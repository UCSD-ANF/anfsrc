
 
/*
 * datascopeDvr.c - Routines to handle  datascope database storage
 */

/*******/
#define DATASCOPEDEBUGON 1
/****/
#include "datascopeMDriver.h"


int
getArgsFromString(char *inStr, char *argv[], char del)
{
    int i;

    char *tmpPtr, *tmpPtr1;
    
    tmpPtr = inStr;
    for (i  = 0; i < MAX_PROC_ARGS_FOR_DS ; i++) {
	argv[i] = tmpPtr;
	if ((tmpPtr1 = strchr(tmpPtr,del)) != NULL){
	    *tmpPtr1 =  '\0';
	    tmpPtr = tmpPtr1 + 1;
	}
	else 
	    break;
    }
    return(i+1);

}

/* datascopeOpen - Handles the open call.
 *
 * Input : MDriverDesc *mdDesc - The datascope descriptor handle
 *         char *datascopePathDesc - The datascope path name to be opened
 *         int datascopeFlags - The open flag
 *         int datascopeMode - The datascope mode
 *
 * Output : Returns the datascope descriptor of the opened datascope.
 */
int
datascopeOpen(MDriverDesc *mdDesc, char *rsrcInfo,
         char *datascopePathDesc, int datascopeFlags, int datascopeMode, char *userName)
{

  datascopeStateInfo *datascopeSI;
  char datascopeInMode[4];
  char *tmpPtr;
  int i;
  Dbptr *datascopedb;
  Hook *hook = 0;

  Dbptr   dbtemp;
  Tbl     *tablenames;
  Tbl     *table_fieldnames;
  Tbl     *request_fieldnames;
  char    *tablename;
  char    fieldname[STRSZ];
  int     is_view;
  int     itable;
  int     ifield;

  if((datascopeSI =  malloc(sizeof (datascopeStateInfo))) == NULL) {
    fprintf(stdout, "datascopeOpen:  Malloc error");
    return MEMORY_ALLOCATION_ERROR;
  }
 if((datascopedb =  malloc(sizeof (Dbptr))) == NULL) {
    fprintf(stdout, "datascopeOpen:  Malloc error");
    return MEMORY_ALLOCATION_ERROR;
  }

  if ((i = getDatascopeStateInfo( datascopeSI, rsrcInfo, datascopePathDesc, datascopeFlags, 
			datascopeMode, userName)) <0 ) {
    fprintf(stdout, "datascopeOpen:  getStateInfo error:%i",i);
    freeDatascopeStateInfo(datascopeSI);
    free(datascopedb);
    return i;
  }


    strcpy(datascopeInMode,"r+");

#ifdef DATASCOPEDEBUGON
  fprintf(stdout,"datascopeOpen: Start datascopeopen: datascopePathDesc=%s.\n",datascopePathDesc);
  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
  i = dbopen_database(datascopePathDesc, datascopeInMode, datascopedb);
  if (i < 0) {
    fprintf(stdout, "datascopeOpen: datascopeopen error. datascopePathDesc=%s. errorCode=%d",
	    datascopePathDesc, i);fflush(stdout);
    free(datascopedb);
    return(MD_CONNECT_ERROR);
  }
   datascopeSI->dbPtrPtr = datascopedb;
  if (datascopeSI->dstable != NULL) {
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: Start  dstable =%s\n",datascopeSI->dstable);
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */
    if ((i = dbopen_table ( datascopeSI->dstable, datascopeInMode, datascopedb )) < 0 ) {
      fprintf(stdout, "datascopeOpen: dstable error. %s %i",datascopeSI->dstable,i);
      freeDatascopeStateInfo(datascopeSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }
  
  if (datascopeSI->dsfind != NULL) {
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: Start  dsfind =%s\n",datascopeSI->dsfind);
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */
    if ((i = dbfind (*datascopedb, datascopeSI->dsfind, 0 , &hook )) < 0 ) {
      fprintf(stdout, "datascopeOpen: dsfind error. %s %i",datascopeSI->dsfind,i);
      freeDatascopeStateInfo(datascopeSI);fflush(stdout);
      if (i == -1) 
	return(DATASCOPE_COMPILATION_ERROR);
      else if (i == -2) 
	return(DATASCOPE_END_OF_DATA_FOUND);
      else if (i == -3) 
	return(DATASCOPE_BEGIN_OF_DATA_FOUND);
      else
	return(MD_SET_ERROR);
    }
  }
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: Start  dsfindStatus =%i.\n",i);
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */
  
  if (datascopeSI->dsprocessStmt  != NULL) {
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: Start  dbprocessStmt.\n");
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */
    *datascopedb = dbprocess(*datascopedb, datascopeSI->dsprocessStmt, dbinvalid);
    if (datascopedb->database < 0) {
       i = datascopedb->database;
       fprintf(stdout, "datascopeOpen: dsprocess error. %i",i);fflush(stdout);
       freeDatascopeStateInfo(datascopeSI);
       return(i);
    } 
  }
  
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: After  dbprocessStmt: datascopedb->database = %i.\n",datascopedb->database);
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */

  if (datascopeSI->dsprocessStmt  != NULL || datascopeSI->dsfind != NULL) {
    i = dbquery( *datascopedb, dbTABLE_IS_VIEW, &is_view );
    if (i < 0) {
      fprintf(stdout, "datascopeOpen: dbquery1 Error: %i\n",i);
      freeDatascopeStateInfo(datascopeSI);
      return(i);
    }	   
    if( is_view ) {
      i =dbquery( *datascopedb, dbVIEW_TABLES, &tablenames );
      if (i < 0) {
         fprintf(stdout, "datascopeOpen: dbquery2 Error: %i\n",i);
         freeDatascopeStateInfo(datascopeSI);
         return(i);
      }
    } else {
	i = dbquery( *datascopedb, dbTABLE_NAME, &tablename );
      if (i < 0) {
         fprintf(stdout, "datascopeOpen: dbquery3 Error: %i\n",i);
         freeDatascopeStateInfo(datascopeSI);
         return(i);
      }
      tablenames = strtbl( tablename, 0 );
    }

#ifdef DATASCOPEDEBUGON
    fprintf(stdout, "Getting Records\n"); fflush(stdout);
#endif /* DATASCOPEDEBUGON */


    
    request_fieldnames = newtbl( 0 );
    
    for( itable = 0; itable < maxtbl( tablenames ); itable++ ) {
      
      tablename = gettbl( tablenames, itable );
     if (tablename == NULL) {
         fprintf(stdout, "datascopeOpen: gettable Error fo itable=%i and maxtabl=%i\n",itable,maxtbl(tablenames));
         freeDatascopeStateInfo(datascopeSI);
         return(MDAS_FAILURE);
      }
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: TableName =%s\n",tablename) ;
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */

      dbtemp = dblookup( *datascopedb, 0, tablename, 0, 0 );
fprintf(stdout,"datascopeOpen: TableId=%i\n",dbtemp.table);fflush(stdout);
      if (dbtemp.table < 0) {
                 fprintf(stdout, "datascopeOpen: dblookup Error db.table=%i\n",dbtemp.table);
         i=dbtemp.table;
         freeDatascopeStateInfo(datascopeSI);
         return(i);
      }

      i = dbquery( dbtemp, dbTABLE_FIELDS, 
	       &table_fieldnames );
     if (i < 0) {
         fprintf(stdout, "datascopeOpen: dbquery4 Error: %i\n",i);
         freeDatascopeStateInfo(datascopeSI);
         return(i);
      }

#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: DbQuery Result =%i and maxtbl(table_fieldnames)=%i\n",
	i,maxtbl(table_fieldnames)) ;
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */


      for( ifield = 0;
	   ifield < maxtbl( table_fieldnames );
	   ifield++ ) {
	sprintf( fieldname, "%s.%s",
		 tablename,
		 gettbl( table_fieldnames, ifield ) );
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeOpen: TableFieldName[%i] =%s\n",ifield,fieldname) ;
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */

	pushtbl( request_fieldnames, strdup( fieldname ) );
      }
    }
    datascopeSI->requestFieldNames = request_fieldnames;
  }

  
  datascopeSI->dbPtrPtr = datascopedb;

  if (is_view != 0)
     datascopeSI->isView = 1;
  else
     datascopeSI->isView = 0;
  datascopeSI->tmpFileName = NULL;
  datascopeSI->xml_bns = NULL;
  datascopeSI->firstRead = 1;
  mdDesc->driverSpecificInfo = (char *) datascopeSI;
#ifdef DATASCOPEDEBUGON
  fprintf(stdout,"datascopeOpen: Finish.\n");
  fflush(stdout);
#endif /* DATASCOPEDEBUGON */


  return MDAS_SUCCESS;

}

/* datascopeCreate - Handles the create call.
 *
 * Input :  MDriverDesc *mdDesc - The datascope descriptor handle
 *         char *datascopePathDesc - The datascope path name to be opened
 *         int datascopeMode - The datascope mode
 *
 * Output : Returns the datascope descriptor of the new datascope.
 */

/*
int
datascopeCreate(MDriverDesc *mdDesc, mdasResInfo *rsrcInfo, char *datascopePathDesc, int datascopeMode, , char *userName)
*/
int
datascopeCreate(MDriverDesc *mdDesc, char *rsrcInfo, char *datascopePathDesc, int datascopeMode, char *userName)
{
  int status;

  return(FUNCTION_NOT_SUPPORTED);

}

/* datascopeClose - Handles the close call.
 *
 * Input : MDriverDesc *mdDesc - The datascope descriptor to be closed
 *
 * Output : Return status of close
 */

int
datascopeClose(MDriverDesc *mdDesc)
{
  int status;
  datascopeStateInfo *datascopeSI;

#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeClose: Begin\n");
 fflush(stdout);
#endif /* DATASCOPEDEBUGON */

  datascopeSI = (datascopeStateInfo *) mdDesc->driverSpecificInfo;
  if (datascopeSI->isView) {
      if (datascopeSI->firstRead >= 0)
	  fclose( (FILE *) datascopeSI->firstRead);
  }
  if (datascopeSI->tmpFileName != NULL){
	unlink(datascopeSI->tmpFileName);
	free(datascopeSI->tmpFileName);
  } 
  if (datascopeSI->xml_bns  != NULL)
     free(datascopeSI->xml_bns);
  freeDatascopeStateInfo(datascopeSI);
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeClose: End\n");
 fflush(stdout);
#endif /* DATASCOPEDEBUGON */
  return (MDAS_SUCCESS);
}

/* datascopeRead - Handles the read call.
 *
 * Input : MDriverDesc *mdDesc - The datascope descriptor to read
 *	   char *buffer - The input buffer
 *	   int amount - The amount to read
 *
 * Output : Returns to number of bytes read
 */

int
datascopeRead(MDriverDesc *mdDesc, char *buffer, int length)
{
  int	status;
  int             datascope ,i ,ii;
    int             pktid ; 
    char            srcname[MAX_TOKEN] ;
    double          vdatascopetime ;
    char           *vdatascopepacket=0 ; 
    int             nbytes = 0 ;
    int             bufsize=0 ;
    datascopeStateInfo   *datascopeSI;
    Dbptr *datascopedbPtr;
    Bns     *xml_bns;	
    int first;
    FILE *tmpFileFd;
    char tmpFileName[400];
    char *mybuffer;
    int mylength;
    int mysize = 0;
    int packcount;
    char *xmlStrPtr;
    datascopeSI = (datascopeStateInfo *) mdDesc->driverSpecificInfo;
    datascopedbPtr = datascopeSI->dbPtrPtr;

    mylength = length;
    mybuffer = buffer;
    first = datascopeSI->firstRead;
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeRead: Start Reading: isView=%i and firstRead=%i\n",
	datascopeSI->isView,datascopeSI->firstRead);
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */

   if (datascopeSI->isView) {
    if (datascopeSI->presentation != NULL && !strcmp(datascopeSI->presentation,"db2xml")) {
      if (datascopeSI->firstRead == 1) {
	  datascopeSI->firstRead = -1;
#ifdef DATASCOPEDEBUGON
        fprintf(stdout,"datascopeRead: Performing db2xml\n");
        fflush(stdout);
#endif /* DATASCOPEDEBUGON */
	i = db2xml( *datascopedbPtr,  "VORBVIEW", "VORBROW",
              datascopeSI->requestFieldNames, 0,(void **) &xml_bns, DBXML_BNS ); 
#ifdef DATASCOPEDEBUGON
        fprintf(stdout,"datascopeRead: After db2xml:%i \n",i);
        fflush(stdout);
#endif /* DATASCOPEDEBUGON */
        if (i < 0 || bnscnt( xml_bns ) <= 0 ) {
          fprintf(stdout,"datascopeRead: Error in  db2xml: error=%i, bnscnt=%i\n",
		bnserrno(xml_bns),bnscnt( xml_bns ));
        }
       	datascopeSI->xml_bns = xml_bns;
      } 
      else {
        xml_bns = datascopeSI->xml_bns;
      }      
      i = bns2buf( xml_bns, (void *) buffer,  length );
#ifdef DATASCOPEDEBUGON
      fprintf(stdout,"datascopeRead: BufferLength= %i \n",i);
      fflush(stdout);
#endif /* DATASCOPEDEBUGON */
      return(i);
    }
    else {
#ifdef DATASCOPEDEBUGON
       fprintf(stdout,"datascopeRead: performing dbselect\n") ;
       fflush(stdout);
#endif /* DATASCOPEDEBUGON */
      if (datascopeSI->firstRead == 1) {
        sprintf(tmpFileName,"../data/dataScopeViewSelect.%i",getpid());
        tmpFileFd = fopen(tmpFileName,"w");
        if (tmpFileFd == NULL) {
           fprintf(stdout, "datascopeRead:  Unable to open temp file:%s\n",tmpFileName);        
          return(DB_TAB_OPEN_ENV_ERROR);
       }
#ifdef DATASCOPEDEBUGON
       fprintf(stdout,"datascopeRead: performing dbselect\n") ;
       fflush(stdout);
#endif /* DATASCOPEDEBUGON */
       dbselect (*datascopedbPtr, datascopeSI->requestFieldNames, tmpFileFd ) ;
#ifdef DATASCOPEDEBUGON
       fprintf(stdout,"datascopeRead: tmpFile position = %d\n",ftell(tmpFileFd )) ;
       fflush(stdout);
#endif /* DATASCOPEDEBUGON */
       fclose(tmpFileFd ) ;
       tmpFileFd = fopen(tmpFileName,"r");
       datascopeSI->tmpFileName = strdup(tmpFileName);   
       datascopeSI->firstRead = tmpFileFd;
     }
     else {
       tmpFileFd = (FILE *)  datascopeSI->firstRead;
     }
     i = fread(buffer,1,length,tmpFileFd);
#ifdef DATASCOPEDEBUGON
     fprintf(stdout,"datascopeRead: BufferLength= %i \n",i);
     fflush(stdout);
#endif /* DATASCOPEDEBUGON */
     return(i);
    }

   }
   else {
    status = dbget(*datascopedbPtr,buffer);
    if (status < 0)
      return(status);
    return (strlen(buffer));

   }

}

/* datascopeWrite - Handles the write call.
 *
 * Input : MDriverDesc *mdDesc - The datascope descriptor to write
 *         char *buffer - The output buffer
 *         int amount - The amount to write
 *
 * Output : Returns to number of bytes written
 */

int
datascopeWrite(MDriverDesc *mdDesc, char *buffer, int length)
{
    int	status;
    datascopeStateInfo   *datascopeSI;
    Dbptr *datascopedbPtr;
    char *mybuffer, *tmpPtr;
    int mylength;
    int i,ii;
    char *tableName;
    char *attrName[MAX_TABLE_COLS];
    char *attrVal[MAX_TABLE_COLS];
    datascopeSI = (datascopeStateInfo *) mdDesc->driverSpecificInfo;
    datascopedbPtr = datascopeSI->dbPtrPtr;
    mylength = length;
    mybuffer = buffer;
#ifdef DATASCOPEDEBUGON
    fprintf(stdout,"datascopeWrite: Start Writing\n");
    fflush(stdout);
#endif /* DATASCOPEDEBUGON */
    if (datascopeSI->presentation != NULL && 
	!strcmp(datascopeSI->presentation,"xml2db")) {
      while (mybuffer) {
	i = getDatascopeTableRowFromXML(tableName,attrName,attrVal, 
			       &mybuffer,mylength, "vorb.schema");
	if (i < 0) {
	  if (i != DATASCOPE_ROW_INCOMPLETE)
	    return(i);
#ifdef DATASCOPEDEBUGON
	  fprintf(stdout, "Row:%s\n",tmpPtr);
	  fflush(stdout);
#endif /* DATASCOPEDEBUGON */  
	  return(i);
	}
      }
    }
    else {
      while (mybuffer && mylength > 0) {
	tmpPtr = mybuffer;
	i = getDatascopeTableRowFromTxt(tableName, 
			       &mybuffer,mylength);
	if (i < 0) {
	  if (i != DATASCOPE_ROW_INCOMPLETE)
	    return(i);
#ifdef DATASCOPEDEBUGON
	  fprintf(stdout, "Row:%s\n",tmpPtr);
	  fflush(stdout);
#endif /* DATASCOPEDEBUGON */  
	   return(i);
	}
	/*
	i = dbput (*datascopedbPtr, tmpPtr);
	*/
#ifdef DATASCOPEDEBUGON
	fprintf(stdout, "Row:%s\n",tmpPtr);
	fflush(stdout);
#endif /* DATASCOPEDEBUGON */  
	if (i < 0)
	  return (i);
	mylength = mylength - (int) (tmpPtr - mybuffer);
      }
    }
    return (length);
}

/* datascopeSeek - Handles the seek call.
 *
 * Input : MDriverDesc *mdDesc - The datascope descriptor to seek
 *         int offset - The position of the next operation
 *         int whence - Same definition as in datascope.
 *              SEEK_SET - pointer is set to the value of the Offset parameter.
 *              SEEK_CUR - pointer is set to its current location plus the
 *                      value of the Offset parameter.
 *              SEEK_END - pointer is set to the size of the datascope plus the
 *                      value of the Offset parameter.
 *
 * Output : Returns the status of seek
 */

srb_long_t
datascopeSeek(MDriverDesc *mdDesc, srb_long_t offset, int whence)
{
    srb_long_t	status;
    srb_long_t seekPos;
    return(FUNCTION_NOT_SUPPORTED);

}

/* datascopeUnlink - Handles the unlink call.
 *
 * Input : char *datascopeDesc - The datascope path name to unlink
 *
 * Output : Returns the status of unlink
 */

int
datascopeUnlink(char *rsrcAddress, char *datascopePathDesc)
{
    int status;
 
        return(FUNCTION_NOT_SUPPORTED);
}

int 
datascopeProc(MDriverDesc *mdDesc, char *procName, 
              char *inBuf, int inLen, 
              char *outBuf, int outLen )
{

  int status = 0;
  char *argv[MAX_PROC_ARGS_FOR_DS];
  int             datascope ,i ,ii,j,k;
  datascopeStateInfo   *datascopeSI;
  Dbptr *datascopedbPtr;
  Tbl  *processTable;
  char *tmpPtr, *tmpPtr1;
  Dbptr *datascopedbPtr2;
 

  datascopeSI = (datascopeStateInfo *) mdDesc->driverSpecificInfo;
  datascopedbPtr = datascopeSI->dbPtrPtr;

#ifdef DATASCOPEDEBUGON
  fprintf(stdout,"datascopeProc: Begin Proc inLen=%i,outLen=%i \n",inLen,outLen);
  fprintf(stdout,"datascopeProc: procName=$$%s$$\n",procName);
  fprintf(stdout,"datascopeProc: inBuf=$$%.80s$$\n",inBuf);
  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
  
  if (isalnum(procName[0]) == 0)
      i = getArgsFromString(procName +1 ,argv,procName[0]);
  else
      i = getArgsFromString(procName,argv,'|');
#ifdef DATASCOPEDEBUGON
  fprintf(stdout,"datascopeProc: i=%i, actualprocName=$$%s$$\n",i,procName);
  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
  if (i < 0)
      return(i);
  if (!strcmp(argv[0],"dbopen_table")) {
      /* argv[1] = table_name 
         argv[2] = mode */
      i = dbopen_table (argv[1], argv[2], datascopedbPtr);
  }
  else if (!strcmp(argv[0],"dbfind")) {
      /* argv[1] = searchstring
         argv[2] = flag (int) */
      i = dbfind( *datascopedbPtr, argv[1], atoi(argv[2]), NULL);
  }  else if (!strcmp(argv[0],"dbprocess")) {
      /* argv[1] = statements separated by ;;
         argv[2] =  */
      processTable =  newtbl( 0 );
      tmpPtr1 = argv[1];
      while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
	  *tmpPtr = '\0';
	  strtrim(tmpPtr1);
#ifdef DATASCOPEDEBUGON
  fprintf(stdout,"datascopeProc: process Stmt=%s\n",tmpPtr1);
  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
	  pushtbl( processTable,strdup(tmpPtr1) );
	  tmpPtr1 = tmpPtr + 2;
      }
      strtrim(tmpPtr1);
#ifdef DATASCOPEDEBUGON
  fprintf(stdout,"datascopeProc: process Stmt=%s\n",tmpPtr1);
  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
      pushtbl( processTable,strdup(tmpPtr1) );
      *datascopedbPtr = dbprocess(*datascopedbPtr,processTable,dbinvalid);

      if (datascopedbPtr->database < 0) {
	  return(datascopedbPtr->database);
      }
      datascopeSI->dbPtrPtr = datascopedbPtr;
      datascopeSI->requestFieldNames = 0;
      return(0);
  }
  else {
      return(FUNCTION_NOT_SUPPORTED);
  }
  return(i);
}


int
datascopeSync(MDriverDesc *mdDesc)
{
    int status;
 
        return(FUNCTION_NOT_SUPPORTED);
}


/***** datascope utilities ***/

int
freeDatascopeStateInfo(datascopeStateInfo *datascopeSI)
{
  int i;
  Dbptr *db;
  db = datascopeSI-> dbPtrPtr;
  i = dbclose( *db);
  return(i);
}

int
getDatascopeStateInfo(datascopeStateInfo *datascopeSI, char *rsrcInfo,
         char *datascopeDataDesc, int datascopeFlags,
               int datascopeMode, char *userName)
{

  char *dsTable;
  char *dsFind;
  char *tmpPtr;
  char *dsposition;
  char *dstimeout;
  char *dsnumofpkts;
  char *dspresentation;
  char *dsnumbulkreads;
  char *dsProcess;
  dsTable = strstr(datascopeDataDesc,"<DSTABLE>");
  dsFind  = strstr(datascopeDataDesc,"<DSFIND>");
  dsProcess  = strstr(datascopeDataDesc,"<DSPROCESS>");
  dsposition  = strstr(datascopeDataDesc,"<DSPOSITION>");
  dstimeout  = strstr(datascopeDataDesc,"<DSTIMEOUT>");
  dsnumofpkts  = strstr(datascopeDataDesc,"<DSNUMOFPKTS>");
  dspresentation  = strstr(datascopeDataDesc,"<DSPRESENTATION>");
  dsnumbulkreads  = strstr(datascopeDataDesc,"<DSNUMBULKREADS>");


  if (dsTable != NULL) {
    *dsTable = '\0';
    dsTable += 9;
    if ((tmpPtr  =  strstr(dsTable,"</DSTABLE>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsTable: %s\n",dsTable);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    if ((datascopeSI->dstable  =strdup(dsTable)) == NULL)
      return MEMORY_ALLOCATION_ERROR;
  }
  else 
    datascopeSI->dstable = NULL;

  if (dsFind != NULL) {
    *dsFind = '\0';
    dsFind += 8;
    if ((tmpPtr  =  strstr(dsFind,"</DSFIND>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsFind: %s\n",dsFind);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    if ((datascopeSI->dsfind  =strdup(dsFind)) == NULL)
      return MEMORY_ALLOCATION_ERROR;
  }
  else 
    datascopeSI->dsfind = NULL;

  if (dsProcess != NULL) {
    *dsProcess = '\0';
    dsProcess += 11;
    if ((tmpPtr  =  strstr(dsProcess,"</DSPROCESS>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsProcess: %s\n",dsProcess);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    datascopeSI->dsprocessStmt = newtbl( 0 );
    while ((tmpPtr  =  strstr(dsProcess,";;")) != NULL) {
      *tmpPtr = '\0';
      strtrim(dsProcess);
      pushtbl( datascopeSI->dsprocessStmt,strdup(dsProcess) );
      dsProcess = tmpPtr + 2;
    }
    strtrim(dsProcess);
    pushtbl( datascopeSI->dsprocessStmt,strdup(dsProcess) );
  }
  else 
    datascopeSI->dsprocessStmt = NULL;

  if (dsposition != NULL) {
    *dsposition = '\0';
    dsposition += 12;
    if ((tmpPtr  =  strstr(dsposition,"</DSPOSITION>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsposition: %s\n",dsposition);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    if ((datascopeSI->position  =strdup(dsposition)) == NULL)
      return MEMORY_ALLOCATION_ERROR;
  }
  else 
    datascopeSI->position = NULL;


  if (dstimeout != NULL) {
    *dstimeout = '\0';
    dstimeout += 11;
    if ((tmpPtr  =  strstr(dstimeout,"</DSTIMEOUT>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dstimeout: %s\n",dstimeout);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    datascopeSI->timeout = atoi(dstimeout);
  }
  else 
    datascopeSI->timeout = -1;


  if (dsnumofpkts != NULL) {
    *dsnumofpkts = '\0';
    dsnumofpkts += 13;
    if ((tmpPtr  =  strstr(dsnumofpkts,"</DSNUMOFPKTS>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsnumofpkts: %s\n",dsnumofpkts);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    datascopeSI->numofpkts  =atoi(dsnumofpkts);
  }
  else 
    datascopeSI->numofpkts = -1;


  if (dspresentation != NULL) {
    *dspresentation = '\0';
    dspresentation += 16;
    if ((tmpPtr  =  strstr(dspresentation,"</DSPRESENTATION>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dspresentation: %s\n",dspresentation);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    if ((datascopeSI->presentation  =strdup(dspresentation)) == NULL)
      return MEMORY_ALLOCATION_ERROR;
  }
  else 
    datascopeSI->presentation = NULL;


  if (dsnumbulkreads != NULL) {
    *dsnumbulkreads = '\0';
    dsnumbulkreads += 16;
    if ((tmpPtr  =  strstr(dsnumbulkreads,"</DSNUMBULKREADS>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsnumbulkreads: %s\n",dsnumbulkreads);
      return(INP_ERR_RES_FORMAT);
    }
    *tmpPtr = '\0';
    datascopeSI->numbulkreads  = atoi(dsnumbulkreads);
  }
  else 
    datascopeSI->numbulkreads = 1;

  datascopeSI->firstRead = 1;
  datascopeSI->datascopeFlags = datascopeFlags;
  datascopeSI->datascopeMode = datascopeFlags;
  if ((datascopeSI->userName  = strdup(userName)) == NULL)
    return MEMORY_ALLOCATION_ERROR; 
  if ((datascopeSI->rsrcInfo = strdup(rsrcInfo)) == NULL)
    return MEMORY_ALLOCATION_ERROR; 
  return MDAS_SUCCESS;

}

int
datascopeSpresGeneric(int first, int last,char *srcname,double vorbtime, int pktid,
		int nbytes, char *vorbpacket, char *buffer)
{
  int i;

  if (last == 0) return (last);
  sprintf(buffer,"%s||%s\n",srcname,vorbpacket);
  i = strlen(buffer);
  return (i);
}

int
getDatascopeTableRowFromXML( char *tableName,
			     char *attrName[MAX_TABLE_COLS],
			     char *attrVal[MAX_TABLE_COLS], 
			     char **mybuffer,
			     int  length, 
			     char *schemaName)
{

  return(0);
}

int
getDatascopeTableRowFromTxt(char *tableName, 
			    char **mybuffer,
			    int  length)

{
  int i,j;
  char *tmpPtr, *tmpPtr1;

  tmpPtr = *mybuffer;

  while (*tmpPtr != '\n'  && *tmpPtr != '\f' && *tmpPtr != '\r') {
    tmpPtr++;
    length--;
    if (length == 0) {
      *mybuffer = tmpPtr;
      return (0);
    }
  }

  *tmpPtr == '\0';
  tmpPtr++;
  length--;
  while (*tmpPtr == '\n'  || *tmpPtr == '\f' || *tmpPtr != '\r' ) {
    tmpPtr++;
    length--;
    if (length == 0) {
      *mybuffer = tmpPtr;
      return (0); 
    }   
  }
  *mybuffer = tmpPtr;
  return (0); 
}

