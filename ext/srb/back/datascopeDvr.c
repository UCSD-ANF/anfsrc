/*
 * datascopeDvr.c - Routines to handle  datascope database storage
 */

/*******/
#define DATASCOPEDEBUGON 1
/****/

#ifdef DATASCOPEDEBUGON 
#define DATASCOPE_DEBUG( ... ) fprintf( stdout, __VA_ARGS__ ); fflush( stdout ); clear_register( 1 );
#else
#define DATASCOPE_DEBUG( ... ) 
#endif

#define DBPTR_PRINT( DB, WHERE ) fprintf( stderr, "SCAFFOLD: dbptr at '%s' is %d %d %d %d\n", WHERE, (DB).database, (DB).table, (DB).field, (DB).record );

#include "datascopeSrbTools.h"
#include "datascopeMDriver.h"
#include "tr.h"
#include "dbptolemy.h"
#include <errno.h>
extern int errno;

int
mapStringWithEqualString(char *inStr, char *str1, char *str2)
{
    int i,l;
    char *tmpPtr,  *tmpPtr1, *tmpPtr2;
    char a;
    l = strlen(str1);    
    if (strlen(str2) != l)
	return(-1);
    tmpPtr = inStr;
    while ( (tmpPtr1 =  strstr(tmpPtr,str1)) != NULL) {
	a = *(tmpPtr1 + l);
	strcpy(tmpPtr1,str2);
	*(tmpPtr1 + l) = a;
	tmpPtr = tmpPtr1 + l;
    }
    return(0);
}

int
dbxml2html(char *buffer, int stringlength, int MaxBufSize )
{
    char *buf;
    char *tmpPtr,*tmpPtr0,  *tmpPtr1, *tmpPtr2, *tmpPtr3, *tmpPtr4, *tmpPtr5, *tmpPtr6;
    int i,j,k;
    char selBuf[HUGE_STRING];
    int firstSel;
    int selBufFlag;
    int cnt = 0;
    DATASCOPE_DEBUG( "Entering dbxml2html with buffer=%.200s\n", buffer );

    buf = malloc(1.5 * MaxBufSize);
    strcpy(selBuf,"<DSFILENAME></DSFILENAME><DSPRESENTATION>dbfilename</DSPRESENTATION><DSFIND>");
    firstSel = 1;
    selBufFlag = 0;
    memcpy(buf, buffer,stringlength + 2);
    buf[stringlength] = '\0';
    
    tmpPtr = strstr(buf,"<VORBROW>");
    if (tmpPtr == NULL)
	return(-1);
    tmpPtr6 = strstr(buf,"</VORBROW>");
    if (tmpPtr6 != NULL)
	*tmpPtr6 = '\0';
    tmpPtr ++;
    tmpPtr0 = tmpPtr;
/*    sprintf(buffer, "<HTML><BODY><TABLE BGCOLOR=\"#EEFFFF\" BORDER=\"1\" BORDERCOLOR=\"blue\"><COLGROUP SPAN=%i ALIGN=\"right\"><TR>",MAX_TABLE_COLS * 6); */
    sprintf(buffer, "<TABLE BGCOLOR=\"#EEFFFF\" BORDER=\"1\" BORDERCOLOR=\"blue\"><COLGROUP SPAN=%i ALIGN=\"right\"><TR>",MAX_TABLE_COLS * 6);
    while (tmpPtr != NULL) {
	tmpPtr2 = strchr(tmpPtr,'<');
	if (tmpPtr2 == NULL)
	    break;
	tmpPtr3 = strchr(tmpPtr2,'>');
	if (tmpPtr3 != NULL)
	    *tmpPtr3 = '\0';
	strcat(buffer,"<TH>");
	strcat(buffer,tmpPtr2+1);
        if (strstr(tmpPtr2,".dir") || strstr(tmpPtr2,".dfile"))
	    selBufFlag++;
	strcat(buffer,"</TH>");
	*tmpPtr3 = '>';
	tmpPtr2 = strstr (tmpPtr3,"</");
	if (tmpPtr2 == NULL)
	    break;
	tmpPtr = tmpPtr2 + 1;
    }
    if (selBufFlag >= 2)
	strcat(buffer,"<TH>Select</TH>");
    strcat(buffer,"</TR>\n");
    tmpPtr = tmpPtr0;
    while (tmpPtr != NULL) {
	strcat(buffer,"<TR>");
	tmpPtr2 =  strchr(tmpPtr,'<');
	while (tmpPtr2  != NULL) {
	    tmpPtr3 = strchr(tmpPtr2,'>');
	    if (tmpPtr3 != NULL) {
		*tmpPtr3 = '\0';
		tmpPtr3 += 1;
		tmpPtr4 = strchr(tmpPtr3,'<');
		if (tmpPtr4 != NULL)
		    *tmpPtr4 = '\0';
		strcat(buffer,"<TD>");
		strcat(buffer,tmpPtr3);
		strcat(buffer,"</TD>");
		if (selBufFlag >= 2 && (strstr(tmpPtr2,".dir")||strstr(tmpPtr2,".dfile"))){
		    if (firstSel == 0)
			strcat(selBuf," AND ");
		    firstSel = 0;
		    strcat(selBuf,tmpPtr2 + 1);
		    strcat(selBuf,"==&#34;");
		    strcat(selBuf,tmpPtr3);
		    strcat(selBuf,"&#34;");
		}
                if (tmpPtr4 != NULL) {
		    *tmpPtr4 = '<';
		    tmpPtr4++;
		    tmpPtr2 = strchr(tmpPtr4,'<');
		}
		else
		    tmpPtr2 = NULL;
		*(tmpPtr3 - 1) = '>';

	    }
	    else {
		tmpPtr2 = NULL;
		strcat(buffer,"<TD>");
		strcat(buffer,tmpPtr3+1);
                strcat(buffer,"</TD>");
	    }
	}
	*tmpPtr6 = '<';
	if (selBufFlag >= 2) {
	    strcat(buffer,"<TD><input type=\"radio\" name =\"gg\" value =\"");
	    strcat(buffer,selBuf);
	    strcpy(selBuf,"<DSFILENAME></DSFILENAME><DSPRESENTATION>dbfilename</DSPRESENTATION><DSFIND>");
	    firstSel = 1;
	    strcat(buffer,"\"></TD>");
	}
	strcat(buffer,"</TR>\n");
	tmpPtr = strstr(tmpPtr6,"<VORBROW>");
	if (tmpPtr == NULL)
	    break;
	tmpPtr6 = strstr(tmpPtr,"</VORBROW>");
	if (tmpPtr6 != NULL)
	    *tmpPtr6 = '\0';
	else
	    break;
	tmpPtr ++;
	if ((cnt % 200) == 0)
            DATASCOPE_DEBUG( "Row's Processed = %i processed length = %i\n",cnt, 
			     (int) (tmpPtr - buf));
	cnt++;
    }
/* RAJA removed  for datascopeimages stuff
    strcat(buffer,"</BODY></HTML>\n");
    RAJA removed  for datascopeimages stuff */
    strcat(buffer,"</TABLE>\n");
    return(0);
}
int
makeDbgetvCall (Dbptr *datascopedbPtr, char *tableName,
		int numArgs, char *argv[], Dbvalue dbValueArr[])
{
 
    int i,j,k;

    DATASCOPE_DEBUG( "tableName is %s\n", tableName );
    for (i = 0; i < numArgs ; i++) {
        DATASCOPE_DEBUG( "makeDbgetvCall handling %s into %x\n", argv[i], &dbValueArr[i] );
	j =  dbgetv(*datascopedbPtr,tableName, argv[i], &dbValueArr[i], 0);
	if (j < 0) {
	    DBPTR_PRINT( *datascopedbPtr, "in makeDbgetvCall" );
	    clear_register( 1 );
	    return(j);
	}
    }
    return(j);
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
         char *datascopePathDescIn, int datascopeFlags, int datascopeInMode, char *userName)
{

  datascopeStateInfo *datascopeSI;
  char datascopeMode[4];
  char *tmpPtr;
  int i;
  Dbptr *datascopedb;
  Hook *hook = 0;

  Dbptr   dbtemp;
  Tbl     *tablenames;
  Tbl     *table_fieldnames;
  Tbl     *request_fieldnames;
  char    *tablename;
  char *datascopePathDesc;
  char    fieldname[STRSZ];
  int     is_view;
  int nrec;
  int     itable;
  int     ifield;
  char fileName[FILENAME_MAX];
  char fileName2[FILENAME_MAX];

  if((datascopeSI =  malloc(sizeof (datascopeStateInfo))) == NULL) {
    fprintf(stdout, "datascopeOpen:  Malloc error");
    return MEMORY_ALLOCATION_ERROR;
  }
 if((datascopedb =  malloc(sizeof (Dbptr))) == NULL) {
    fprintf(stdout, "datascopeOpen:  Malloc error");
    return MEMORY_ALLOCATION_ERROR;
  }
 datascopePathDesc = datascopePathDescIn;
 while (*datascopePathDesc == ' ')
     datascopePathDesc++;
 if ((tmpPtr = strstr(datascopePathDesc,"?SHADOW")) != NULL) 
     *tmpPtr = '\0';

 datascopeSI->dbPtrPtr = datascopedb;
 mdDesc->driverSpecificInfo = (char *) datascopeSI;
 if (strlen(datascopePathDesc) == 0)
     return(MDAS_SUCCESS);

  if (datascopeFlags == 0)
      strcpy(datascopeMode,"r");
  else
      strcpy(datascopeMode,"r+");

  DATASCOPE_DEBUG("datascopeOpen: Start datascopeopen: datascopePathDesc=%s; datascopeMode=%s.\n",datascopePathDesc,datascopeMode);

  unuralize(datascopePathDesc);
  unuralize(datascopePathDesc);
  if ((i = getDatascopeStateInfo( datascopeSI, rsrcInfo, datascopePathDesc, datascopeFlags, 
			datascopeInMode, userName)) <0 ) {
    fprintf(stdout, "datascopeOpen:  getStateInfo error:%i",i);
    freeDatascopeStateInfo(datascopeSI);
    free(datascopedb);
    return i;
  }
 
  datascopeSI->dbfilefd= NULL;
  datascopeSI->exprArray = NULL;
  DATASCOPE_DEBUG("datascopeOpen: Opening database\n");

  i = dbopen_database(datascopePathDesc, datascopeMode, datascopedb);
  if (i < 0) {
      fprintf(stdout, "datascopeOpen: datascopeopen error. datascopePathDesc=%s. errorCode=%d",
	      datascopePathDesc, i);fflush(stdout);
      free(datascopedb);
      
      return(MD_CONNECT_ERROR);
  }
  if (datascopeSI->dstable != NULL) {
    DATASCOPE_DEBUG("datascopeOpen: Start  dstable =%s\n",datascopeSI->dstable);
    if ((i = dbopen_table ( datascopeSI->dstable, datascopeMode, datascopedb )) < 0 ) {
      fprintf(stdout, "datascopeOpen: dstable error. %s %i",datascopeSI->dstable,i);
      freeDatascopeStateInfo(datascopeSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }
  datascopeSI->dbPtrPtr = datascopedb;

  if (datascopeSI->dsprocessStmt  != NULL) {
    DATASCOPE_DEBUG("datascopeOpen: Start  dbprocessStmt.\n");
    *datascopedb = dbprocess(*datascopedb, datascopeSI->dsprocessStmt, dbinvalid);
    if (datascopedb->database < 0) {
       i = datascopedb->database;
       fprintf(stdout, "datascopeOpen: dsprocess error. %i",i);fflush(stdout);
       freeDatascopeStateInfo(datascopeSI);
       DATASCOPE_DEBUG("datascopeOpen: After  dbprocessStmt: FAILED:  status=%i.\n",i);
       return(i);
    } 
    DATASCOPE_DEBUG("datascopeOpen: After  dbprocessStmt: datascopedb->database = %i.\n",datascopedb->database);
  }
  
  if (datascopeSI->dsfind != NULL || datascopeSI->dsfindRev != NULL ) {
    if (datascopeSI->dsfind != NULL) {
        DATASCOPE_DEBUG("datascopeOpen: Start  dsfind =%s\n",datascopeSI->dsfind);
	datascopedb->record =-1;
	i = dbfind (*datascopedb, datascopeSI->dsfind, 0 , &hook );
    }
    else {
        DATASCOPE_DEBUG("datascopeOpen: Start  dsfindRev =%s\n",datascopeSI->dsfindRev);
	i = dbquery( *datascopedb, dbRECORD_COUNT, &nrec );
	if (i < 0) {
	    fprintf(stdout, "datascopeOpen: dbquery1 for nrec Error: %i\n",i);
	    freeDatascopeStateInfo(datascopeSI);
	    return(i);
	}
        DATASCOPE_DEBUG("datascopeOpen: Start  dsfindRev Nrec =%i\n",nrec);

	datascopedb->record = nrec;
	i = dbfind (*datascopedb, datascopeSI->dsfindRev, 1, &hook );
    }
    if (i  < 0 ) {
      fprintf(stdout, "datascopeOpen: dsfind error. %s %i",datascopeSI->dsfind,i);
      freeDatascopeStateInfo(datascopeSI);
      DATASCOPE_DEBUG("datascopeOpen: After dsfind: FAILED: status=%i.\n",i);

      if (i == -1) 
	return(DATASCOPE_COMPILATION_ERROR);
      else if (i == -2) 
	return(DATASCOPE_END_OF_DATA_FOUND);
      else if (i == -3) 
	return(DATASCOPE_BEGIN_OF_DATA_FOUND);
      else
	return(MD_SET_ERROR);
    }
    datascopedb->record = i;
    
    DATASCOPE_DEBUG("datascopeOpen: Start  dsfindStatus =%i.\n",i);
  }


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

    DATASCOPE_DEBUG("Getting Records\n"); 
    
    request_fieldnames = newtbl( 0 );
    
    for( itable = 0; itable < maxtbl( tablenames ); itable++ ) {
      
      tablename = gettbl( tablenames, itable );
     if (tablename == NULL) {
         fprintf(stdout, "datascopeOpen: gettable Error fo itable=%i and maxtabl=%i\n",itable,maxtbl(tablenames));
         freeDatascopeStateInfo(datascopeSI);
         return(MDAS_FAILURE);
      }
      DATASCOPE_DEBUG("datascopeOpen: TableName =%s\n",tablename) ;

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

      DATASCOPE_DEBUG("datascopeOpen: DbQuery Result =%i and maxtbl(table_fieldnames)=%i\n",
	i,maxtbl(table_fieldnames)) ;

      for( ifield = 0;
	   ifield < maxtbl( table_fieldnames );
	   ifield++ ) {
	sprintf( fieldname, "%s.%s",
		 tablename,
		 gettbl( table_fieldnames, ifield ) );
      DATASCOPE_DEBUG("datascopeOpen: TableFieldName[%i] =%s\n",ifield,fieldname) ;

	pushtbl( request_fieldnames, strdup( fieldname ) );
      }
    }
    datascopeSI->requestFieldNames = request_fieldnames;
  }
  
  if (datascopeSI->tmpFileName  != NULL) {
      /* we are doing an extfile if string > 0 length */
      DATASCOPE_DEBUG("datascopeOpen: dbfile/dbextfile for '%s'\n",datascopeSI->tmpFileName);
      strcpy(fileName,"");
      if (strlen(datascopeSI->tmpFileName) > 0) 
	  i =  dbextfile( *datascopedb, datascopeSI->tmpFileName,
			  fileName);
      else
	  i =  dbfilename(*datascopedb, fileName);
      DATASCOPE_DEBUG("datascopeOpen: dbfile/dbextfile Result= %i\n",i);
      DATASCOPE_DEBUG("datascopeOpen: dbfile/dbextfile path= %s\n",fileName);
      if (i < 0){
	  fprintf(stdout,"datascopeOpen: dbfile/dbextfile path= %s\n",fileName);
	  fflush(stdout);
	  return(MDAS_FAILURE);
      }
      abspath(fileName,fileName2);
      free(datascopeSI->tmpFileName);
      datascopeSI->tmpFileName = NULL;
      DATASCOPE_DEBUG("datascopeOpen: dbfile/dbextfile absolute path= %s\n",fileName2);
      is_view = 1;
      datascopeSI->dbfilefd = fopen(fileName2,"r");
      if (datascopeSI->dbfilefd == NULL) {
	  fprintf(stdout,"datascopeOpen: dbfile/dbextfile  unable to open local file: %s\n",fileName2);
	  fflush(stdout);
      }
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
  DATASCOPE_DEBUG("datascopeOpen: Finish.\n");

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

  DATASCOPE_DEBUG("datascopeClose: Begin\n");

  datascopeSI = (datascopeStateInfo *) mdDesc->driverSpecificInfo;
  if (datascopeSI->isView) {
      if (datascopeSI->firstRead > 1)
	  fclose( (FILE *) datascopeSI->firstRead);
  }
  if (datascopeSI->dbfilefd !=NULL)
      fclose( (FILE *) datascopeSI->dbfilefd);
  if (datascopeSI->tmpFileName != NULL){
	unlink(datascopeSI->tmpFileName);
	free(datascopeSI->tmpFileName);
  } 
  if (datascopeSI->xml_bns  != NULL)
     free(datascopeSI->xml_bns);
  freeDatascopeStateInfo(datascopeSI);
  DATASCOPE_DEBUG("datascopeClose: End\n");
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
  DATASCOPE_DEBUG("datascopeRead: Start Reading: isView=%i and firstRead=%i,buffer length = %i\n",
	datascopeSI->isView,datascopeSI->firstRead,length);

    if ( datascopeSI->dbfilefd != NULL && datascopeSI->firstRead != 1) {
	i = fread(buffer,1,length,datascopeSI->dbfilefd);
	return(i);
    }

/*   if (datascopeSI->isView) {*/
    if ( 1 == 1) {
    if (datascopeSI->presentation != NULL && (!strcmp(datascopeSI->presentation,"db2xml") || !strcmp(datascopeSI->presentation,"db2html"))) {
      if (datascopeSI->firstRead == 1) {
	  datascopeSI->firstRead = -1;
  DATASCOPE_DEBUG("datascopeRead: Performing db2xml\n");
  DATASCOPE_DEBUG("datascopeRead: Before db2xml:%i \n",i);
	i = db2xml( *datascopedbPtr,  "VORBVIEW", "VORBROW",
              datascopeSI->requestFieldNames, 0,(void **) &xml_bns, DBXML_BNS ); 
  DATASCOPE_DEBUG("datascopeRead: After db2xml:%i \n",i);
        if (i < 0 || bnscnt( xml_bns ) <= 0 ) {
          fprintf(stdout,"datascopeRead: Error in  db2xml: error=%i, bnscnt=%i\n",
		bnserrno(xml_bns),bnscnt( xml_bns ));
        }
       	datascopeSI->xml_bns = xml_bns;
      } 
      else {
        xml_bns = datascopeSI->xml_bns;
      }      
      if (datascopeSI->xml_bns == NULL)
	  return(0);
#ifdef DATASCOPEDEBUGON
      fprintf(stdout,"datascopeRead: Before bns2buf  \n");
      fflush(stdout);
#endif /* DATASCOPEDEBUGON */

      i = bns2buf( xml_bns, (void *) buffer,  length );
#ifdef DATASCOPEDEBUGON
        fprintf(stdout,"datascopeRead: After bns2buf:%i Length=%i \n",i,length);
        fflush(stdout);
#endif /* DATASCOPEDEBUGON */
/*	i =  bnsget(xml_bns,(void *) buffer, BYTES, length );  */
      if (i  < length) {
	  bnsclose( xml_bns);
	  datascopeSI->xml_bns = NULL;
      }
      if (!strcmp(datascopeSI->presentation,"db2html")) {
#ifdef DATASCOPEDEBUGON
	  fprintf(stdout,"datascopeRead: Before db2html  \n");
	  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
	  dbxml2html(buffer, i, length );
#ifdef DATASCOPEDEBUGON
	  fprintf(stdout,"datascopeRead: After dbxml2html :%i \n",i);
	  fflush(stdout);
#endif /* DATASCOPEDEBUGON */
	  i = strlen(buffer);
      }
  DATASCOPE_DEBUG("datascopeRead: BufferLength= %i \n",i);
      return(i);
    }
    else if (datascopeSI->presentation != NULL && !strcmp(datascopeSI->presentation,"dbfilename")) {
	tmpFileFd = (FILE *)  datascopeSI->dbfilefd;
	datascopeSI->firstRead = -1;
	i = fread(buffer,1,length,tmpFileFd);
  DATASCOPE_DEBUG("datascopeRead: BufferLength= %i \n",i);
	return(i);
    }
    else {
  DATASCOPE_DEBUG("datascopeRead: performing dbselect\n") ;
      if (datascopeSI->firstRead == 1) {
        sprintf(tmpFileName,"../data/dataScopeViewSelect.%i",getpid());
        tmpFileFd = fopen(tmpFileName,"w");
        if (tmpFileFd == NULL) {
           fprintf(stdout, "datascopeRead:  Unable to open temp file:%s\n",tmpFileName);        
          return(DB_TAB_OPEN_ENV_ERROR);
       }
  DATASCOPE_DEBUG("datascopeRead: performing dbselect\n") ;
       dbselect (*datascopedbPtr, datascopeSI->requestFieldNames, tmpFileFd ) ;
  DATASCOPE_DEBUG("datascopeRead: tmpFile position = %d\n",ftell(tmpFileFd )) ;
       fclose(tmpFileFd ) ;
       tmpFileFd = fopen(tmpFileName,"r");
       datascopeSI->tmpFileName = strdup(tmpFileName);   
       datascopeSI->firstRead = (int) tmpFileFd;
     }
     else {
       tmpFileFd = (FILE *)  datascopeSI->firstRead;
     }
     i = fread(buffer,1,length,tmpFileFd);
  DATASCOPE_DEBUG("datascopeRead: BufferLength= %i \n",i);
     return(i);
    }

   }
   else {
       DATASCOPE_DEBUG("datascopeRead: performing dbget\n") ;
       status = dbget(*datascopedbPtr,buffer);
       if (status < 0) {
	   DATASCOPE_DEBUG("datascopeRead: Error status = %d\n", status);
	   return(status);
       }
       DATASCOPE_DEBUG("datascopeRead: buf length=%d\n",strlen(buffer));
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
  DATASCOPE_DEBUG("datascopeWrite: Start Writing\n");

  if ( datascopeSI->dbfilefd != NULL) {
      i = fwrite(buffer,1,length,datascopeSI->dbfilefd);
      return(i);
  }

    if (datascopeSI->presentation != NULL && 
	!strcmp(datascopeSI->presentation,"xml2db")) {
      while (mybuffer) {
	i = getDatascopeTableRowFromXML(tableName,attrName,attrVal, 
			       &mybuffer,mylength, "vorb.schema");
	if (i < 0) {
	  if (i != DATASCOPE_ROW_INCOMPLETE)
	    return(i);
  DATASCOPE_DEBUG("Row:%s\n",tmpPtr);
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
  DATASCOPE_DEBUG("Row:%s\n",tmpPtr);
	   return(i);
	}
	/*
	i = dbput (*datascopedbPtr, tmpPtr);
	*/
  DATASCOPE_DEBUG("Row:%s\n",tmpPtr);
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
  int             datascope ,i ,ii,j,k,l, numArgs, jj;
  datascopeStateInfo   *datascopeSI;
  Dbptr *datascopedbPtr;
  Tbl  *processTable = NULL;
  Tbl  *exprTable = NULL;
  Tbl  *nojoinTable = NULL;
  Hook *hook = NULL;
  Arr  *exprArray = NULL;
  char *tmpPtr, *tmpPtr1, *retStr;
  Dbptr *datascopedbPtr2;
  Dbptr  dbPtr1;
  int  outBufStrLen;
  Bns     *xml_bns;
  char fileNameString[FILENAME_MAX];
  char fileNameString2[FILENAME_MAX];
  int fldType,nrec;
  char *fldFormat;
  char *tableName;  
  Dbvalue tmpDbValue;
  FILE *tmpfd;
  Expression *exprPtr;
  double t0, t1;
  char tmpBuf[STRSZ * 2];


  datascopeSI = (datascopeStateInfo *) mdDesc->driverSpecificInfo;
  datascopedbPtr = datascopeSI->dbPtrPtr;
  outBufStrLen =  0;
  outBuf[0] = '\0';
  DATASCOPE_DEBUG("datascopeProc: Begin Proc inLen=%i,outLen=%i \n",inLen,outLen);
  DATASCOPE_DEBUG("datascopeProc: procName=$$%s$$\n",procName);
  DATASCOPE_DEBUG("datascopeProc: inBuf=$$%.80s$$\n",inBuf);
  
  if (isalnum(procName[0]) == 0)
      i = getArgsFromString(procName +1 ,argv,procName[0],DSESC);
  else
      i = getArgsFromString(procName,argv,DSDELIM,DSESC);
  DATASCOPE_DEBUG("datascopeProc: i=%i, actualprocName=$$%s$$\n",i,procName);
  if(i == 0 )
      return(FUNCTION_NOT_SUPPORTED);
  if (i < 0) 
      return(i);
  numArgs = i;
  i = 0;
  if (!strcmp(argv[0],"get_dbptr")) {
      /* Returns outBuf = datascopedbPtr String */
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"put_dbptr")) {
      /* inBuf = datascopedbPtr String */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      return(i);
  }
  else if (!strcmp(argv[0],"close_extfile")) {
      /* outBuf returns fclose return value */
      if (datascopeSI->dbfilefd != NULL) {
	  i = fclose(datascopeSI->dbfilefd);
	  datascopeSI->dbfilefd = NULL;
	  return(i);
      }
      return(i);
  }
  else if (!strcmp(argv[0],"dbopen_table")) {
      /* argv[1] = table_name 
         argv[2] = mode */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (numArgs != 3) {
          fprintf(stdout, "datascopeproc: in dbopen_table arguments insufficient:%i\n",numArgs);
          return(MDAS_FAILURE);
      }
      if (inLen > 0) 
	  str2dbPtr(inBuf,datascopedbPtr);
      i = dbopen_table (argv[1], argv[2], datascopedbPtr);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbopen")) {
      /* argv[1] = database_name
         argv[2] = mode */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (numArgs != 3) {
          fprintf(stdout, "datascopeproc: in dbopen arguments insufficient:%i\n",numArgs);
          return(MDAS_FAILURE);
      }
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbopen (argv[1], argv[2], datascopedbPtr);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbopen_database")) {
      /* argv[1] = database_name
         argv[2] = mode */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (numArgs != 3) {
          fprintf(stdout, "datascopeproc: in dbopen_database arguments insufficient:%i\n",numArgs);
          return(MDAS_FAILURE);
      }
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbopen_database (argv[1], argv[2], datascopedbPtr);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbfind")) {
      /* argv[1] = searchstring
         argv[2] = flag (int) */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = status */
      if (inLen > 0) 
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbfind( *datascopedbPtr, argv[1], atoi(argv[2]), NULL);
      sprintf(outBuf,"%i",i);
      outBufStrLen = strlen(outBuf)+1;
      DATASCOPE_DEBUG("outBuf in dbfind proc call is <%s>\n", outBuf)
  }  
  else if (!strcmp(argv[0],"dbfindrev")) {
      /* argv[1] = searchstring
         argv[2] = flag (int) */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = status|datascopedbPtr String */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbquery( *datascopedbPtr, dbRECORD_COUNT, &nrec );
      if (i < 0)
	  return(i);
      datascopedbPtr->record = nrec;
      i = dbfind( *datascopedbPtr, argv[1], atoi(argv[2]), NULL);
      sprintf(outBuf,"%i|%i|%i|%i|%i",i,
	      datascopedbPtr->database,
	      datascopedbPtr->table,
	      datascopedbPtr->field,
	      datascopedbPtr->record);
      /* outBufStrLen = dbPtr2str(datascopedbPtr, &outBuf[strlen(outBuf)]);*/
         fprintf(stdout, "outBuf in dbfindrev proc call is <%s>\n", outBuf);fflush(stdout);
      outBufStrLen = strlen(outBuf)+1;
  }

  else if (!strcmp(argv[0],"dblookup")) {
      /* argv[1] = database_name
	 argv[2] = table_name 
	 argv[3] = field_name 
	 argv[4] = record_name */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      *datascopedbPtr = dblookup(*datascopedbPtr, argv[1],argv[2],argv[3],argv[4]);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"db2xml")) {
      /* argv[1] = rootnode
	 argv[2] = rownode
	 argv[3] = flag (int)
	 argv[4] = fields separated by ;;
	 argv[5] = expressions separated by ;; */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = if flag= 0 returns xml string
                          if flag=DBXML_BNS return (BNS *) */
      /* return status for the function gives size of the outBuf fille */
      /* if return status = outLen-1
             when flag = 0 use dbReadString to get rest of string
	     when flag =DBXML_BNS use dbReadBns to get rest of string
	        one can use dbRead* as many times as wanted until
		the return status is 0 or negative */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[4]) == 0)
	  processTable = NULL;
      else {
	  processTable =  newtbl( 0 );
	  tmpPtr1 = argv[4];
	  while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
	      *tmpPtr = '\0';
	      strtrim(tmpPtr1);
	      pushtbl( processTable,strdup(tmpPtr1) );
	      tmpPtr1 = tmpPtr + 2;
	  }
	  strtrim(tmpPtr1);
	  pushtbl( processTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[5]) == 0)
          exprTable = NULL;
      else {
          exprTable =  newtbl( 0 );
          tmpPtr1 = argv[5];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( exprTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( exprTable,strdup(tmpPtr1) );
      }
      if (atoi(argv[3]) == DBXML_BNS) {
	  i = db2xml(*datascopedbPtr,argv[1],argv[2],
                     processTable, exprTable,
		     (void **) &xml_bns, DBXML_BNS );
  	  DATASCOPE_DEBUG("datascopeProc: db2xml-bns:status= %i,bnscnt=%i\n",
		  i,bnscnt(xml_bns));
	  if (i < 0 || bnscnt( xml_bns ) <= 0) {
	      fprintf(stdout,"datascopeRead: Error in  db2xml: error=%i, bnscnt=\%i\n",
		      bnserrno(xml_bns),bnscnt( xml_bns ));
	      return(i);
	  }
	  sprintf(outBuf,"%i",xml_bns );
	  return(strlen(outBuf));
      }
      else {
	  i = db2xml(*datascopedbPtr,argv[1],argv[2], 
		     processTable, exprTable, (void **) &retStr, 0);
	  if (i < 0)
	      return(i);
	  if ((i = strlen(retStr)) <= (outLen - 1)) {
	      strcpy(outBuf,retStr);
	      datascopeSI->db2xmlOrigStr = NULL;
	      datascopeSI->db2xmlRemStr =  NULL;
	      return(i);
	  }
	  else {
	      strncpy(outBuf,retStr,outLen);
	      datascopeSI->db2xmlOrigStr = retStr;
	      datascopeSI->db2xmlRemStr = retStr + outLen;
	      return(outLen);
	  }
      }
  }
  else if (!strcmp(argv[0],"db2ptolemy")) {
      /* argv[1] = flag (int)
         argv[2] = fields separated by ;;
         argv[3] = expressions separated by ;; */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = if flag= 0 returns  string
	 if flag=DBXML_BNS return (BNS *) */
      /* return status for the function gives size of the outBuf fille */
      /* if return status = outLen-1
             when flag = 0 use dbReadString to get rest of string
             when flag =DBXML_BNS use dbReadBns to get rest of string
                one can use dbRead* as many times as wanted until
                the return status is 0 or negative */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[2]) == 0)
          processTable = NULL;
      else {
          processTable =  newtbl( 0 );
          tmpPtr1 = argv[2];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( processTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( processTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[3]) == 0)
          exprTable = NULL;
      else {
          exprTable =  newtbl( 0 );
          tmpPtr1 = argv[3];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( exprTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( exprTable,strdup(tmpPtr1) );
      }
      if (atoi(argv[1]) == DBXML_BNS) {
          i = db2ptolemy(*datascopedbPtr,
                     processTable, exprTable,
                     (void **) &xml_bns, DBXML_BNS );
          DATASCOPE_DEBUG("datascopeProc: db2ptolemy-bns:status= %i,bnscnt=%i\n",
			  i,bnscnt(xml_bns));
          if (i < 0 || bnscnt( xml_bns ) <= 0) {
              fprintf(stdout,"datascopeRead: Error in  db2xml: error=%i, bnscnt=\%i\n",
                      bnserrno(xml_bns),bnscnt( xml_bns ));
              return(i);
          }
          sprintf(outBuf,"%i",xml_bns );
          return(strlen(outBuf));
      }
      else {
	  i = db2ptolemy(*datascopedbPtr,
		     processTable, exprTable, (void **) &retStr, atoi(argv[1]));
	  if (i < 0)
	      return(i);
	  if ((i = strlen(retStr)) <= (outLen - 1)) {
	      strcpy(outBuf,retStr);
	      datascopeSI->db2xmlOrigStr = NULL;
	      datascopeSI->db2xmlRemStr =  NULL;
	      return(i);
	  }
	  else {
	      strncpy(outBuf,retStr,outLen);
	      datascopeSI->db2xmlOrigStr = retStr;
	      
	      return(outLen);
	  }
      }
  }
  else if (!strcmp(argv[0],"dbReadString")) {
      /* return outBuf with the string (as much as possible  */
      /* return status of function is the length of used outBuf */ 
      if (datascopeSI->db2xmlRemStr == NULL)
	  return(0);
      retStr = datascopeSI->db2xmlRemStr;
      if ((i = strlen(retStr)) <= (outLen-1)) {
	  strcpy(outBuf,retStr);
	  free(datascopeSI->db2xmlOrigStr);
	  datascopeSI->db2xmlOrigStr = NULL;
	  datascopeSI->db2xmlRemStr =  NULL;
	  return(i);
      }
      else {
	  strncpy(outBuf,retStr,outLen);
	  datascopeSI->db2xmlRemStr = retStr + outLen;
	  return(outLen);
      }
  }
  else if (!strcmp(argv[0],"dbReadBns")) {
      /* return outBuf with the string (as much as possible  */
      /* return status of function is the length of used outBuf */
      xml_bns = (Bns *) atoi(argv[1]);
      i = bns2buf( xml_bns, (void *) outBuf,  outLen - 1 );
      return(i);
  }
  else if (!strcmp(argv[0],"dbprocess")) {
      /* argv[1] = statements separated by ;; */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      processTable =  newtbl( 0 );
      tmpPtr1 = argv[1];
      while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
	  *tmpPtr = '\0';
	  strtrim(tmpPtr1);
  	  DATASCOPE_DEBUG("datascopeProc: process Stmt=%s\n",tmpPtr1);
	  pushtbl( processTable,strdup(tmpPtr1) );
	  tmpPtr1 = tmpPtr + 2;
      }
      strtrim(tmpPtr1);
      DATASCOPE_DEBUG("datascopeProc: process Stmt=%s\n",tmpPtr1);
      pushtbl( processTable,strdup(tmpPtr1) );
      *datascopedbPtr = dbprocess(*datascopedbPtr,processTable,dbinvalid);

      if (datascopedbPtr->database < 0) {
	  return(datascopedbPtr->database);
      }
      datascopeSI->dbPtrPtr = datascopedbPtr;
      datascopeSI->requestFieldNames = 0;
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbfilename")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  a pair separated by | :          	 status|fileName  */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbfilename(*datascopedbPtr, fileNameString);
      DATASCOPE_DEBUG("dbfilename returns %s\n", fileNameString );
      abspath(fileNameString,fileNameString2);
      sprintf(tmpBuf,"%i",i);
      strcpy( outBuf, putArgsToString( DSDELIM, DSESC, 2, tmpBuf, fileNameString2 ) );
      DATASCOPE_DEBUG("dbfilename: ready to return %s\n", outBuf ); 
      return(strlen(outBuf)+1);
  }
  else if (!strcmp(argv[0],"dbextfile")) {
      /* argv[1] = tablename */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  a pair separated by | :   status|fileName  */
      /* if you need the dbPtr info you need to make another call after this */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      DATASCOPE_DEBUG("dbextfile gets dbptr as inbuf %s, as vals %d %d %d %d\n", inBuf, 
				datascopedbPtr->database,
				datascopedbPtr->table,
				datascopedbPtr->field,
				datascopedbPtr->record )
      i = dbextfile(*datascopedbPtr,argv[1], fileNameString);
      DATASCOPE_DEBUG("dbextfile returns '%s' from table %s\n", fileNameString, argv[1] );
      abspath(fileNameString,fileNameString2);
      sprintf(tmpBuf,"%i",i);
      strcpy( outBuf, putArgsToString( DSDELIM, DSESC, 2, tmpBuf, fileNameString2 ) );
      DATASCOPE_DEBUG("dbextfile: ready to return %s\n", outBuf ); 
      return(strlen(outBuf)+1);
  }
  else if (!strcmp(argv[0],"dbget")) {
      /* argv[1] = flag: 0-> get into scratch record; 1-> return record in outBuf */
      /* inBuf = datascopedbPtr String */
      /* returns the return code (and possibly the dbget result string) in outBuf  */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      if( atoi( argv[1] ) ) {
      	i = dbget(*datascopedbPtr,outBuf);
        sprintf(tmpBuf,"%i",i);
        strcpy( outBuf, putArgsToString( DSDELIM, DSESC, 2, tmpBuf, outBuf ) );
      } else {
      	i = dbget(*datascopedbPtr,0);
        sprintf(outBuf,"%i",i);
      }
      i = 0;
      return(strlen(outBuf));
  }
  else if (!strcmp(argv[0],"dbgetv")) {
      /* argv[1] = tablename zerolength string if not given */
      /* argv[2] thru argv[numArgs-1]  fieldNames */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = contains v0|v1|...|v[numArgs-2]  where
         v[i] is the value being returned \| is used escape any | inside the string values*/

      Dbvalue dbValueArr[numArgs];
      if (numArgs == 2) {
	  fprintf(stdout, "datascopeproc: in dbgetv  number of fields is zero:\n");
	  return(MDAS_FAILURE);
      }
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[1]) > 0)
	  tableName = argv[1];
      else
	  tableName = NULL;
      
      for (i = 0; i < numArgs -2; i++)
	  argv[i] = argv[i+2];
      numArgs  = numArgs - 2;

      i  =  makeDbgetvCall (datascopedbPtr, tableName, numArgs, argv, dbValueArr);
      if (i < 0) {
	  fprintf(stdout, "datascopeproc: in dbgetv makeDbgetvCall Error : %i\n", i);
	  return(i);
      }
      sprintf( outBuf, "" );
      dbPtr1 = *datascopedbPtr;
      if (tableName != NULL) {
	  dbPtr1 = dblookup( dbPtr1, 0, tableName, 0, 0 );
	  if (dbPtr1.table < 0) {
	      fprintf(stdout, "datascopeproc: in dbgetv  dblookup Error db.table=%i\n",dbPtr1.table);
	      return(dbPtr1.table);
	  }
      }
      for (ii =  0 ; ii < numArgs; ii++) {
	  dbPtr1 = dblookup( dbPtr1, "", "", argv[ii], "" );
	  if (dbPtr1.table < 0) {
	      fprintf(stdout, "datascopeproc: in dbgetv  dblookup for field %s Error db.table=%i\n",
		      argv[ii], dbPtr1.table);
	      return(dbPtr1.table);
	  }
	  i = dbquery( dbPtr1, dbFIELD_TYPE, &fldType);
	  if (i < 0) {
	      fprintf(stdout, "datascopeproc: in dbgetv getting field type using dbquery Error: %i\n",i);
	      return(i);
	  }
	  i = dbquery( dbPtr1, dbFIELD_FORMAT, &fldFormat);
	  if (i < 0) {
	      fprintf(stdout, "datascopeproc: in dbgetv getting field format using dbquery Error: %i\n",i);
	      return(i);
	  }
	  if( strcmp( outBuf, "" ) ) {
		sprintf(outBuf,"%s%c",outBuf,DSDELIM);
	  }
	  switch(fldType) {
	      case dbDBPTR:
		  strcat( outBuf, "dbDBPTR:" );
		  sprintf(tmpBuf, "%d %d %d %d",
			  dbValueArr[ii].db.database,
			  dbValueArr[ii].db.table,
			  dbValueArr[ii].db.field,
			  dbValueArr[ii].db.record );
		  break;
	      case dbSTRING:
		  strcat( outBuf, "dbSTRING:" );
		  l = strlen(dbValueArr[ii].s);
		  for (i = 0, j=0; i <= l ;i++,j++) {
		      if (dbValueArr[ii].s[i] == DSDELIM) {
			  tmpBuf[j] = DSESC;
			  j++;
		      }
		      tmpBuf[j] = dbValueArr[ii].s[i];
		  }
		  
		  break;
	      case dbBOOLEAN:
	      case dbINTEGER:
	      case dbYEARDAY:
		  strcat( outBuf, "dbINTEGER:" );
		  sprintf(tmpBuf, fldFormat, dbValueArr[ii].i );              
		  strtrim( tmpBuf );
		  break;
	      case dbREAL:
	      case dbTIME:
		  strcat( outBuf, "dbREAL:" );
		  sprintf(tmpBuf, fldFormat, dbValueArr[ii].d );
		  strtrim( tmpBuf );
		  break;
	      default: 
		  strcat( outBuf, "dbINVALID:" );
		  sprintf(tmpBuf,"");
		  break;
	  }	  
	  strcat(outBuf,tmpBuf);
      }
      i = 0;
      DATASCOPE_DEBUG("dbgetv: ready to return %s\n", outBuf ); 
      outBufStrLen = strlen(outBuf)+1;
  }
  else if (!strcmp(argv[0],"dbput")) {
      /* argv[1] contains put string */
      /* inBuf = datascopedbPtr String */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[1]) > 0)
	  i = dbput(*datascopedbPtr,argv[1]);
      else
	  i = dbput(*datascopedbPtr, 0);
      sprintf(outBuf,"%i",i);
      DATASCOPE_DEBUG( "dbput will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbputv") || !strcmp(argv[0],"dbaddv") ||
      !strcmp(argv[0],"dbaddv_extfile") ||
      !strcmp(argv[0],"dbaddv_extfile_all")) {
      /* argv[1] = tablename */
      /* argv[2] = pattern in case of dbaddv_extfile  or dbaddv_extfile_all*/
      /* for i = 2,5,8,11,...   for dbputv/dbaddv and
             i = 3,6,9,12,...   for dbaddv_extfile or dbaddv_extfile_all
         argv[i]   = fieldName
	 argv[i+1] = fieldType (integer :dbREAL,dbINTEGER, etc)
         argv[i+2] = field Value */
      /* inBuf = datascopedbPtr String  except in case of
              dbaddv_extfile or dbaddv_extfile_all  when it contains file-content*/

      if (!strcmp(argv[0],"dbaddv_extfile") || !strcmp(argv[0],"dbaddv_extfile_all"))
	  jj = 3;
      else
	  jj = 2;
      if (numArgs == jj) {
	  fprintf(stdout, "datascopeproc: in dbputv/dbaddv/dbaddv_extfile  number of fields is zero:\n");
	  return(MDAS_FAILURE);
      }
      if ((numArgs -jj) % 3 != 0){
	  fprintf(stdout, "datascopeproc: in dbputv/dbaddv/dbaddv_extfile <name|type|value> triplets required\n");
	  return(MDAS_FAILURE);
      }
      if ( !strcmp(argv[0],"dbaddv_extfile") ||
	   !strcmp(argv[0],"dbaddv_extfile_all"))
	  if (inLen > 0)
	      str2dbPtr(inBuf,datascopedbPtr);

      if (strlen(argv[1]) > 0)
          tableName = argv[1];
      else
          tableName = NULL;
      if (!strcmp(argv[0],"dbaddv") || !strcmp(argv[0],"dbaddv_extfile") ||
	  !strcmp(argv[0],"dbaddv_extfile_all")) 
	  *datascopedbPtr = dblookup(*datascopedbPtr,"", "", "", "dbSCRATCH" );
      for ( i = jj; i  < numArgs; i + 3) {
	  if (!strcmp(argv[0],"dbaddv_extfile") || 
	      !strcmp(argv[0],"dbaddv_extfile_all")) {
	      if (!strcmp(argv[i],"dir" ) || !strcmp(argv[i],"dfile" ) )
		  continue;
	  }
	  tmpDbValue.t = NULL;
	  switch(atoi(argv[i+1])) {
	      case dbDBPTR:
		  l = strlen(argv[i+2]);
		  for (ii = 0; ii < l ; ii++) {
		      if (argv[i+2][ii] == ' ' && argv[i+2][ii+1] != ' ')
			  argv[i+2][ii] = DSDELIM;
		  }
		  str2dbPtr(argv[i+2],&(tmpDbValue.db));
		  break;
	      case dbSTRING:
		  l = strlen(argv[i+2]);
		  for (ii = 0, j=0; ii <= l ;ii++,j++) {
		      if (argv[i+2][ii] == DSESC && argv[i+2][ii+1] == DSDELIM)
			  ii++;
		      tmpDbValue.s[j] == argv[i+2][ii];
		  }
		  break;
	      case dbBOOLEAN:
              case dbINTEGER:
              case dbYEARDAY:
		  tmpDbValue.i = (int) strtol(argv[i+2],(char**)NULL, 10);
                  break;
              case dbREAL:
              case dbTIME:
		  tmpDbValue.d = strtod(argv[i+2],(char**)NULL);
                  break;
              default:
		  fprintf(stdout, "datascopeproc: in dbputv/dbaddv/dbaddv_extfile unknown fieldType:%i\n",atoi(argv[i+1]));
		  return(MDAS_FAILURE);
                  break;
          }
	  ii = dbputv(*datascopedbPtr,tableName,argv[i],tmpDbValue);
	  if (ii < 0) 
	      return(ii);
      }
      if (!strcmp(argv[0],"dbaddv")) 
          i = dbaddchk(*datascopedbPtr,0);
      else if (!strcmp(argv[0],"dbaddv_extfile") ||
	  !strcmp(argv[0],"dbaddv_extfile_all")) {
	  i = trwfname(*datascopedbPtr,argv[2], (char **) &fileNameString);
	  if (i != 0)
	      return(i);
	  datascopeSI->dbfilefd = fopen(fileNameString,"w+");
	  if (datascopeSI->dbfilefd == NULL) {
	      fprintf(stdout,"datascopeProc: dbselect: unable to open local tmp file:%s\n",fileNameString);
              i = -errno;
              return(i);
	  }
	  if (inLen > 0) {
	      i = fwrite(inBuf,1,inLen,datascopeSI->dbfilefd);
	      if (i != inLen) {
		  fclose(datascopeSI->dbfilefd);
		  return(i);
	      }
	      if (!strcmp(argv[0],"dbaddv_extfile_all")) {
		  fclose(datascopeSI->dbfilefd);
		  datascopeSI->dbfilefd = NULL;
		  i = dbaddchk(*datascopedbPtr,0);
	      }
	      else 
		  i  = 0;
	  }
	  outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      }
      else
	  i = 0;
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbquery")) {
      /* argv[1] = code as string e.g. "dbRECORD_COUNT" */
      /* inBuf = datascopedbPtr String */
      /* outBuf depends upon value returned by dbquery */
      char tmpBuf[STRSZ * 2];
      Dbvalue val;
      int code;

      code = xlatname( argv[1], Dbxlat, NDbxlat );
      if (code == -1) 
	  code = atoi(argv[1]);
      DATASCOPE_DEBUG("datascope: dbquery code = %i\n", code);
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      ii =  dbquery(*datascopedbPtr,code, &val);
      if (ii < 0)
          return(ii);
      i = 0;
      switch (code) {
	  case dbDATABASE_COUNT:
	  case dbTABLE_COUNT:
	  case dbFIELD_COUNT:
	  case dbRECORD_COUNT:
	  case dbTABLE_SIZE:
	  case dbFIELD_SIZE:
	  case dbRECORD_SIZE:
	  case dbFIELD_TYPE:
	  case dbFIELD_INDEX:
	  case dbVIEW_TABLE_COUNT:
	  case dbTABLE_IS_VIEW:
	  case dbTABLE_IS_WRITABLE:
	  case dbTABLE_IS_ADDABLE:
	  case dbDATABASE_IS_WRITABLE:
	  case dbTABLE_ADDRESS:
	  case dbTABLE_IS_TRANSIENT:
          case dbLOCKS:
	      sprintf(outBuf,"%i",val.i);
	      DATASCOPE_DEBUG( "dbquery will return val of '%s'\n", outBuf );
	      outBufStrLen = strlen(outBuf)+1;
	      break;
	  case dbSCHEMA_DESCRIPTION:
	  case dbDATABASE_DESCRIPTION:
	  case dbTABLE_DESCRIPTION:
	  case dbFIELD_DESCRIPTION:
	  case dbSCHEMA_DETAIL:
	  case dbDATABASE_DETAIL:
	  case dbTABLE_DETAIL:
	  case dbFIELD_DETAIL:
	  case dbSCHEMA_NAME:
	  case dbDATABASE_NAME:
	  case dbTABLE_NAME:
	  case dbFIELD_NAME:
	  case dbFIELD_FORMAT:
	  case dbFIELD_UNITS:
	  case dbNULL:
              sprintf(outBuf,"%s",val.t);
	      DATASCOPE_DEBUG( "dbquery will return val of '%s'\n", outBuf );
              outBufStrLen = strlen(outBuf)+1;
	      break;
	  case dbFIELD_RANGE:
	  case dbDATABASE_FILENAME:
	  case dbTABLE_FILENAME:
	  case dbTABLE_DIRNAME:
	  case dbDBPATH:
	  case dbFORMAT:
	  case dbUNIQUE_ID_NAME:
          case dbFIELD_BASE_TABLE:
          case dbTIMEDATE_NAME:
          case dbIDSERVER:
              sprintf(outBuf,"%s",val.t);
	      DATASCOPE_DEBUG( "dbquery will return val of '%s'\n", outBuf );
              outBufStrLen = strlen(outBuf)+1;
              break;
	  case dbVIEW_TABLES:
	  case dbPRIMARY_KEY:
	  case dbALTERNATE_KEY:
	  case dbFOREIGN_KEYS:
	  case dbTABLE_FIELDS:
	  case dbFIELD_TABLES:
	  case dbSCHEMA_FIELDS:
	  case dbSCHEMA_TABLES:
	      dbTable2str(val.tbl,outBuf);
	      DATASCOPE_DEBUG( "dbquery will return val of '%s'\n", outBuf );
              outBufStrLen = strlen(outBuf)+1;
	      break;
	  case dbLINK_FIELDS:
	  case dbLASTIDS:
              dbArray2str(val.arr,outBuf);
	      DATASCOPE_DEBUG( "dbquery will return val of '%s'\n", outBuf );
              outBufStrLen = strlen(outBuf)+1;
	      break;
	  default:
	      fprintf(stdout, "datascopeproc: in dbquery unknown code:%i\n",code);
	      return(MDAS_FAILURE);
	      break; 
      }
  }
  else if (!strcmp(argv[0],"dbfilename_retrieve")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  a pair separated by | :            status|fileName  */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      strcat(outBuf,"               ");
      i = dbfilename(*datascopedbPtr, fileNameString);
        fprintf(stdout, "dbfilename returns %s\n", fileNameString ); fflush(stdout);
      abspath(fileNameString,fileNameString2);
      datascopeSI->dbfilefd = fopen(fileNameString2,"r");
      if (datascopeSI->dbfilefd == NULL) {
          fprintf(stdout,"datascopeproc: in dbfilename_retrieve  unable to open local file: %s\n",fileNameString2);
          fflush(stdout);
      }
      datascopeSI->firstRead = -1;
      i = fread(outBuf,1,outLen,datascopeSI->dbfilefd);
      return(i);
  }
  else if (!strcmp(argv[0],"dbextfile_retrieve")) {
      /* argv[1] = tablename */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  data retieved from the file  */
      /* if you need the dbPtr info you need to make another call after this */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      strcat(outBuf,"               ");
      i = dbextfile(*datascopedbPtr,argv[1], fileNameString);
      abspath(fileNameString,fileNameString2);
      datascopeSI->dbfilefd = fopen(fileNameString2,"r");
      if (datascopeSI->dbfilefd == NULL) {
          fprintf(stdout,"datascopeproc: in dbextfile_retrieve  unable to open local file: %s\n",fileNameString2);
          fflush(stdout);
      }
      datascopeSI->firstRead = -1;
      i = fread(outBuf,1,outLen,datascopeSI->dbfilefd);
      return(i);
  }
  else if (!strcmp(argv[0],"dbadd")) {
      /* argv[1] contains add string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the return value  integer*/
      if (inLen > 0)
	  str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[1]) > 0)
	  i = dbadd(*datascopedbPtr,argv[1]);
      else
	  i = dbadd(*datascopedbPtr, 0);
      sprintf(outBuf,"%i",i);
      DATASCOPE_DEBUG( "dbadd will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbadd_remark")) {
      /* inBuf = datascopedbPtr String */
      /* argv[1] contains remark string */
      /* outBuf contains the return value  integer*/
      if (inLen > 0)
	  str2dbPtr(inBuf,datascopedbPtr);
      i = dbadd_remark(*datascopedbPtr,argv[1]);
      sprintf(outBuf,"%i",i);
      DATASCOPE_DEBUG( "dbadd will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbget_remark")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the return value as string */
      if (inLen > 0)
	  str2dbPtr(inBuf,datascopedbPtr);
      i = dbget_remark(*datascopedbPtr, &tmpPtr);
      sprintf(tmpBuf, "%i", i );
      strcpy( outBuf, putArgsToString( DSDELIM, DSESC, 2, tmpBuf, tmpPtr ) );
      free(tmpPtr);
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbaddchk")) {
      /* argv[1] contains add string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the return value  integer*/
      if (inLen > 0)
	  str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[1]) > 0)
	  i = dbaddchk(*datascopedbPtr,argv[1]);
      else
	  i = dbaddchk(*datascopedbPtr, 0);
      sprintf(outBuf,"%i",i);
      DATASCOPE_DEBUG( "dbaddchk will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbaddnull")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the return value  integer*/
      if (inLen > 0)
	  str2dbPtr(inBuf,datascopedbPtr);
      i = dbaddnull(*datascopedbPtr);
      if (i < 0)
	  return(i);
      sprintf(outBuf,"%i",i);
      DATASCOPE_DEBUG( "dbaddnull will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbcompile")) {
      /* argv[1] contains schema  string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the databasepointer */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbcompile(*datascopedbPtr,argv[1]);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbselect")) {
      /* argv[1] contains Table expressions each of which
          is separated  by ;;*/
      /* if you need the dbPtr info you need to make another call after this */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the report string. if string is longer than
	 outBufLen, then the rest can be read through srbObjRead */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      processTable =  newtbl( 0 );
      tmpPtr1 = argv[1];
      while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
          *tmpPtr = '\0';
          strtrim(tmpPtr1);
          pushtbl( processTable,strdup(tmpPtr1) );
          tmpPtr1 = tmpPtr + 2;
      }
      strtrim(tmpPtr1);
      pushtbl( processTable,strdup(tmpPtr1) );
      sprintf(fileNameString,"/tmp/DSdbselect.%i.%i.%ld.%ld,%ld", 
	      datascopedbPtr->database,datascopedbPtr->table,
	      (long) time(NULL),getpid(), (long) random());
      tmpfd = fopen(fileNameString,"w+");
      i  = 0;
      while (tmpfd == NULL && i < 5) {
	  sprintf(fileNameString2,"%ld", (long) random());
	  strcat(fileNameString,fileNameString2);
	  tmpfd = fopen(fileNameString,"w+");
	  i++;
      }
      if (tmpfd == NULL) {
	  fprintf(stdout,"datascopeProc: dbselect: unable to open local tmp file:%s\n",fileNameString);
	      i = -errno;
	      return(i);
      }
      i = dbselect (*datascopedbPtr,processTable, tmpfd);
      if (i < 0) {
	  fclose(tmpfd);
	  tmpfd = NULL;
	  unlink(fileNameString);
	  return(i);
      }
      fseek(tmpfd, SEEK_SET, 0);
      i = fread (outBuf, 1,outLen,tmpfd);
      if (i == outLen) {
	  datascopeSI->firstRead = -1;
	  datascopeSI->dbfilefd = tmpfd;
	  return(i);
      }
      else {
	  fclose(tmpfd);
	  tmpfd = NULL;
          unlink(fileNameString);
	  return(i);
      }
  }
  else if (!strcmp(argv[0],"dbget_range")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  start and end integers  separated by DSDELIM delimiter */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = 0;
      j = 0;
      dbget_range(*datascopedbPtr, &i, &j);
      sprintf(outBuf,"%i%c%i",i,DSDELIM,j);
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbfree")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbfree (*datascopedbPtr);
      sprintf( outBuf, "%i", i );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbclose")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbclose (*datascopedbPtr);
      sprintf(outBuf,"%i",i);
      DATASCOPE_DEBUG( "dbclose will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbmark")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbmark (*datascopedbPtr);
      sprintf( outBuf, "%i", i );
      DATASCOPE_DEBUG( "dbmark will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbdelete")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbdelete (*datascopedbPtr);
      sprintf( outBuf, "%i", i );
      DATASCOPE_DEBUG( "dbdelete will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbcrunch")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbcrunch (*datascopedbPtr);
      sprintf( outBuf, "%i", i );
      DATASCOPE_DEBUG( "dbcrunch will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbdestroy")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbdestroy (*datascopedbPtr);
      sprintf( outBuf, "%i", i );
      DATASCOPE_DEBUG( "dbdelete will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbflush_indexes")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  database pointer */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbflush_indexes (*datascopedbPtr);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbsave_view")) {
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  database poi1ter */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbsave_view (*datascopedbPtr);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbtruncate")) {
      /* argv[1] containts the integer for truncation */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the  return value */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      j = atoi(argv[1]);
      i = dbtruncate (*datascopedbPtr,j);
      sprintf( outBuf, "%i", i );
      DATASCOPE_DEBUG( "dbtruncate will return val of '%s'\n", outBuf );
      outBufStrLen = strlen(outBuf)+1;
      i = 0;
  }
  else if (!strcmp(argv[0],"dbstrtype")) {
      /* argv[1] containts the  string */
      /* inBuf = datascopedbPtr String */
      /* outBuf returns the pair: d|v   
	 where d=dbpointer and v= integer value which is type returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbstrtype(*datascopedbPtr,argv[1]);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      sprintf(tmpBuf,"|%i",i);
      strcat(outBuf,tmpBuf);
      outBufStrLen = strlen(outBuf)+1;
  }
  else if (!strcmp(argv[0],"dbex_evalstr")) {
      /* argv[1] containts string to be evaluated
	 argv[2] has type in integer but currently is ignored!
	    everything is coerced as a string */
      /* inBuf = datascopedbPtr String */
      /* outBuf returns the pair: d|v
         where d=dbpointer and v= integer value which is an expression identifier */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbex_evalstr(*datascopedbPtr,argv[1], dbSTRING, &tmpPtr);
      if (i < 0)
	  return(i);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      strcat(outBuf,"|");
      strcat(outBuf,tmpPtr);
      free(tmpPtr);
      outBufStrLen = strlen(outBuf)+1;
  }
  else if (!strcmp(argv[0],"dbex_compile")) {
      /* argv[1] containts string to be evaluated
         argv[2] has type in integer but currently is ignored! but sent back as part of dbex_eval
	 dbex_compile uses dbSTRING internally */
      /* inBuf = datascopedbPtr String */
      /* outBuf returns the pair: d|v   
	 where d=dbpointer and v= integer value which is an expression identifier */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbex_compile(*datascopedbPtr,argv[1], &exprPtr,dbSTRING);
      if (i != 0)
	  return(i);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      /* 64-BIT PROBLEM NOTICE: Coerce properly the pointer below when using 64-bit */
      sprintf(tmpBuf,"%ld",(long) exprPtr);
      strcat(outBuf,"|");
      strcat(outBuf,tmpPtr);
      outBufStrLen = strlen(outBuf)+1;
      if (datascopeSI->exprArray == NULL) {
	  datascopeSI->exprArray = newarr(0);
      }
      tmpPtr = malloc(10);
      sprintf(tmpPtr,"%i",argv[2]);
      setarr(datascopeSI->exprArray,tmpBuf,tmpPtr);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbex_eval")) {
      /* argv[1] containts expression identifier integer sent by dbex_compile call
         argv[2] has setflag in integer */
      /* if dbex_eval returns dbINVALID the return value is dbINVALID and outBuf is empty */
      /* inBuf = datascopedbPtr String */
      /* outBuf returns in outBuf the 4-tuple: d|i|j|s   where 
	 d=dbpointer 
	 i= type sent for dbex_compile 
	 j=  return  value from dbex_eval and 
	 s= value as a  string */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /* 64-BIT PROBLEM NOTICE: Coerce properly the pointer below when using 64-bit */
      exprPtr = (Expression *) atoi(argv[1]);
      j =  atoi(argv[2]);
      i = dbex_eval(*datascopedbPtr,exprPtr,j, &tmpPtr);
      if (i == dbINVALID)
	  return(i);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      strcat(outBuf,"|");
      strcat(outBuf,tmpPtr);
      free(tmpPtr);
      tmpPtr = getarr(datascopeSI->exprArray, argv[1]);
      sprintf(tmpBuf,"|%s|%i",tmpPtr,i); 
      strcat(outBuf,tmpBuf);
      outBufStrLen = strlen(outBuf)+1;
  }
  else if (!strcmp(argv[0],"dbex_free")) {
      /* argv[1] containts expression identifier integer sent by dbex_compile call */
      /* inBuf = datascopedbPtr String */
      if (inLen > 0)
	  str2dbPtr(inBuf,datascopedbPtr);
      /* 64-BIT PROBLEM NOTICE: Coerce properly the pointer below when using 64-bit */
      exprPtr = (Expression *) atoi(argv[1]);
      tmpPtr = (char *) delarr(datascopeSI->exprArray,argv[1]);
      if (tmpPtr != 0)
	  free(tmpPtr);
      i = dbex_free(exprPtr);
      return(i);
  }
  else if (!strcmp(argv[0],"trloadchan")) {
      /* argv[1] t0 a double given as a string
	 argv[2] t1 a double given as a string
	 argv[3] sta  station name as a string
	 argv[4] chan channel name as  string  */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      t0 = strtod(argv[1],NULL);
      t1 = strtod(argv[2],NULL);
      dbPtr1 = trloadchan(*datascopedbPtr, t0,t1, argv[3], argv[4]);
      DBPTR_PRINT( dbPtr1, "in datastoreObjProc:trloadchan" );
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i = 0;
  }
  else if (!strcmp(argv[0],"trextract_data_all")) {
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = has one line per record separated by \n
          and each line is of form:  nsamp:f,f,f,f,f,f,f 
          where nsamp is number of doubles in the line and f is the
          value as a charter string denoting the double value */
      int     nrecs;
      int     single_row;
      int     nsamp = 0;
      float   *data = NULL;
      double  *doublep;
      int     rc;
      int    first = 1;
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      DATASCOPE_DEBUG( "trextract_data_all callin dbquery for dbRECORD_COUNT\n" );
      DBPTR_PRINT( *datascopedbPtr,"in datastoreObjProc:trextract_data_all");
      rc = dbquery( *datascopedbPtr, dbRECORD_COUNT, &nrecs );
      if (rc == dbINVALID )
	  return(rc);
      strcpy(outBuf,"");
      DATASCOPE_DEBUG( "trextract_data_all: dbRECORD_COUNT=%d\n",nrecs );
      for (datascopedbPtr->record = 0; datascopedbPtr->record < nrecs; 
	   datascopedbPtr->record++) {
	  dbgetv( *datascopedbPtr, 0, "nsamp", &nsamp, "data", &data, 0 );
	  DATASCOPE_DEBUG( "trextract_data_all: dbgetv nsamp=%d\n",nsamp);
	  if (nsamp <= 0 || data == NULL )
	      return(nsamp);
	  if (first)
	      sprintf(&outBuf[strlen(outBuf)],
		      "%i:%f",nsamp,(double) data[0]);
	  else
	      sprintf(&outBuf[strlen(outBuf)],
		      "\n%i:%f",nsamp,(double) data[0]);
	  first = 0;
	  for( i=1; i<nsamp; i++ )
	      sprintf(&outBuf[strlen(outBuf)], ",%f",(double) data[i]);
      }
      outBufStrLen = strlen(outBuf);
      DATASCOPE_DEBUG( "trextract_data_all:  returning buffer of length: %d\n",
		       outBufStrLen);
      return(outBufStrLen);
  }
  else if (!strcmp(argv[0],"dbsort")) {
      /* argv[1] fields separated by ;;
         argv[2] flag  integer 
         argv[3] name of table (need not be given)*/
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String */
      if (numArgs < 3) {
          fprintf(stdout, "datascopeproc: in dbsort  not enough arguments:%i\n",numArgs);
          return(MDAS_FAILURE);
      }
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      exprTable =  newtbl( 0 );
      tmpPtr1 = argv[1];
      while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
	  *tmpPtr = '\0';
	  strtrim(tmpPtr1);
	  pushtbl( exprTable,strdup(tmpPtr1) );
	  tmpPtr1 = tmpPtr + 2;
      }
      strtrim(tmpPtr1);
      pushtbl( exprTable,strdup(tmpPtr1) );
      i = atoi(argv[2]);
      if (numArgs == 4)
	  dbPtr1 = dbsort (*datascopedbPtr,exprTable,i, argv[3]);
      else 
	  dbPtr1 = dbsort (*datascopedbPtr,exprTable,i,0);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i = 0;
  }
  else if (!strcmp(argv[0],"dbtmp")) {
      /* argv[1] schema name */
      /* inBuf = datascopedbPtr String */
      /* Returns outBuf = datascopedbPtr String of the tmp db */
      if (numArgs < 2) {
          fprintf(stdout, "datascopeproc: in dbsort  not enough arguments:%i\n",numArgs);
          return(MDAS_FAILURE);
      }
      dbPtr1 = dbtmp (argv[1]);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i = 0;
  }
  else if (!strcmp(argv[0],"dbsubset")) {
      /* argv[1] = expression string 
         argv[2] = view name; internally generated if empty string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr to the new view created */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      if (strlen(argv[2]) > 0)
	  dbPtr1 = dbsubset (*datascopedbPtr, argv[1],argv[2]);
      else
	  dbPtr1 = dbsubset (*datascopedbPtr, argv[1],0);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbsever")) {
      /* argv[1] = tablename
	 argv[2] = view name */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      dbPtr1 = dbsever (*datascopedbPtr, argv[1],argv[2]);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbseparate")) {
      /* argv[1] = tablename */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      dbPtr1 = dbseparate(*datascopedbPtr, argv[1]);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbungroup")) {
      /* argv[1] = viewname */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      dbPtr1 = dbungroup(*datascopedbPtr, argv[1]);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbunjoin")) {
      /* argv[1] = databasename 
	 argv[2] = rewrite flag integer */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned if successful  or dbINVALID */
      i = dbunjoin ( *datascopedbPtr, argv[1],atoi(argv[2]));
      if (i == 0)
	  outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
  }
  else if (!strcmp(argv[0],"dbtheta")) {
      /* argv[1] - argv[4] = database pointer number2
	 argv[5] = theta expression
	 argv[6] = outer join flag integer
	 argv[7] = view name; internally generated if empty string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /*str2dbPtr(argv[1],&dbPtr1);*/
      dbPtr1.database = atoi(argv[1]);
      dbPtr1.table =  atoi(argv[2]);
      dbPtr1.field =  atoi(argv[3]);
      dbPtr1.record =  atoi(argv[4]);
      if (strlen(argv[7]) > 0)
	  *datascopedbPtr = dbtheta(*datascopedbPtr, dbPtr1, argv[5],
				    atoi(argv[6]),argv[7]);
      else
	  *datascopedbPtr = dbtheta(*datascopedbPtr, dbPtr1, argv[5],
                                    atoi(argv[6]),0);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbgroup")) {
      /* argv[1] = groupFileds separated by ;; 
	 argv[2] = name of generated table; internally generated if empty string 
	 argv[3] = type specified to bundle integer  */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      processTable =  newtbl( 0 );
      tmpPtr1 = argv[1];
      while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
	  *tmpPtr = '\0';
	  strtrim(tmpPtr1);
	  pushtbl( processTable,strdup(tmpPtr1) );
	  tmpPtr1 = tmpPtr + 2;
      }
      strtrim(tmpPtr1);
      pushtbl( processTable,strdup(tmpPtr1) );
      if (strlen(argv[2]) > 0)
          dbPtr1 = dbgroup(*datascopedbPtr, processTable,argv[2], atoi(argv[3]));
      else
	  dbPtr1 = dbgroup(*datascopedbPtr, processTable,0,atoi(argv[3]));
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbnojoin")) {
      /* argv[1] - argv[4] = database pointer number2
	 argv[5] = keys1p  separated by ;;
	 argv[6] = keys2p separated by ;;
	 argv[7] = view name; internally generated if empty string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /*str2dbPtr(argv[1],&dbPtr1);*/
      dbPtr1.database = atoi(argv[1]);
      dbPtr1.table =  atoi(argv[2]);
      dbPtr1.field =  atoi(argv[3]);
      dbPtr1.record =  atoi(argv[4]);
      if (strlen(argv[5]) == 0)
          processTable = NULL;
      else {
          processTable =  newtbl( 0 );
          tmpPtr1 = argv[5];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( processTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( processTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[6]) == 0)
          exprTable = NULL;
      else {
          exprTable =  newtbl( 0 );
          tmpPtr1 = argv[6];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( exprTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( exprTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[7]) > 0)
	  *datascopedbPtr = dbnojoin(*datascopedbPtr,dbPtr1, &processTable, &exprTable,
				    argv[7]);
      else
	  *datascopedbPtr = dbnojoin(*datascopedbPtr,dbPtr1, &processTable, &exprTable, 0);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbjoin")) {
      /* argv[1] - argv[4] = database pointer number2 
         argv[5] = pattern1  separated by ;;
         argv[6] = pattern2  separated by ;;
         argv[7] = outer flag integer
	 argv[8] = nojoin fields separated by ;;
	 argv[9] = view name; internally generated if empty string */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /*str2dbPtr(argv[1],&dbPtr1);*/
      dbPtr1.database = atoi(argv[1]);
      dbPtr1.table =  atoi(argv[2]);
      dbPtr1.field =  atoi(argv[3]);
      dbPtr1.record =  atoi(argv[4]);
      if (strlen(argv[5]) == 0)
          processTable = NULL;
      else {
          processTable =  newtbl( 0 );
          tmpPtr1 = argv[5];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( processTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( processTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[6]) == 0)
          exprTable = NULL;
      else {
          exprTable =  newtbl( 0 );
          tmpPtr1 = argv[6];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( exprTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( exprTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[8]) == 0)
	  nojoinTable = NULL;
      else {
	  nojoinTable =  newtbl( 0 );
	  tmpPtr1 = argv[8];
	  while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
	      *tmpPtr = '\0';
	      strtrim(tmpPtr1);
	      pushtbl( nojoinTable,strdup(tmpPtr1) );
	      tmpPtr1 = tmpPtr + 2;
	  }
	  strtrim(tmpPtr1);
	  pushtbl( nojoinTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[9]) > 0)
          *datascopedbPtr = dbjoin(*datascopedbPtr,dbPtr1, &processTable, &exprTable,
				   atoi(argv[7]), &nojoinTable, argv[9]);
      else
          *datascopedbPtr = dbjoin(*datascopedbPtr,dbPtr1, &processTable, &exprTable,
				   atoi(argv[7]), &nojoinTable, 0);
      outBufStrLen = dbPtr2str(datascopedbPtr,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dblist2subset")) {
      /* argv[1] = list of records separated by ;; */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the dbPtr returned */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      processTable =  newtbl( 0 );
      tmpPtr1 = argv[1];
      while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
          *tmpPtr = '\0';
          strtrim(tmpPtr1);
          pushtbl( processTable,strdup(tmpPtr1) );
          tmpPtr1 = tmpPtr + 2;
      }
      strtrim(tmpPtr1);
      pushtbl( processTable,strdup(tmpPtr1) );
      dbPtr1 = dblist2subset(*datascopedbPtr,processTable);
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbcreate")) {
      /* argv[1] = filename String 
	 argv[2] = schema String
	 argv[3] = name for dbpath String
	 argv[4] = description String
	 argv[5] = detail String */
      /* return value is the value returned by the call */
      i = dbcreate (argv[1],argv[2],argv[3],argv[4],argv[5]);
      return(i);
  }
  else if (!strcmp(argv[0],"dbinvalid")) {
      /* outBuf contains the dbPtr returned */
      dbPtr1 = dbinvalid();
      outBufStrLen = dbPtr2str(&dbPtr1,outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbfind_join_keys")) {
      /* argv[1] - argv[4] = database pointer number2 */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains s1|;|s2  
	 where s1 is keys in table1 and s2 is keys in table2 */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /*str2dbPtr(argv[1],&dbPtr1);*/
      dbPtr1.database = atoi(argv[1]);
      dbPtr1.table =  atoi(argv[2]);
      dbPtr1.field =  atoi(argv[3]);
      dbPtr1.record =  atoi(argv[4]);
      i = dbfind_join_keys(*datascopedbPtr,dbPtr1,&processTable, &exprTable);
      if (i != 0)
	  return(i);
      i = dbTable2str(processTable,outBuf);
      if (i < 0)
	  return(i);
      strcat(outBuf,"|;|");
      i = strlen(outBuf);
      i = dbTable2str(exprTable, (char *) (outBuf + i));
      if (i == 0)
	  outBufStrLen = strlen(outBuf);
  }
  else if (!strcmp(argv[0],"dbis_expression")) {
      /* argv[1] = expression String */
      /* return value is the value from the call */
      i = dbis_expression (argv[1]);
      return(i);
  }
  else if (!strcmp(argv[0],"dbnextid")) {
      /* argv[1] = name string */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      i = dbnextid(*datascopedbPtr,argv[1]);
      return(i);
  }
  else if (!strcmp(argv[0],"dbmatches")) {
      /* argv[1] - argv[4] = database pointer number2
         argv[5] = pattern1  separated by ;;
         argv[6] = pattern2  separated by ;;
	 argv[7] = hook integer; empty string makes the 8hook to be 0 */
      /* inBuf = datascopedbPtr String */
      /* outBuf contains the pair |v
	 where  is the number of records and v is the records separated by DSDELIM */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /*str2dbPtr(argv[1],&dbPtr1);*/
      dbPtr1.database = atoi(argv[1]);
      dbPtr1.table =  atoi(argv[2]);
      dbPtr1.field =  atoi(argv[3]);
      dbPtr1.record =  atoi(argv[4]);
      if (strlen(argv[5]) == 0)
          processTable = NULL;
      else {
          processTable =  newtbl( 0 );
          tmpPtr1 = argv[5];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( processTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( processTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[6]) == 0)
          exprTable = NULL;
      else {
          exprTable =  newtbl( 0 );
          tmpPtr1 = argv[6];
          while ((tmpPtr  =  strstr(tmpPtr1,";;")) != NULL) {
              *tmpPtr = '\0';
              strtrim(tmpPtr1);
              pushtbl( exprTable,strdup(tmpPtr1) );
              tmpPtr1 = tmpPtr + 2;
          }
          strtrim(tmpPtr1);
          pushtbl( exprTable,strdup(tmpPtr1) );
      }
      if (strlen(argv[7]) > 0) 
	  hook = (void *)atoi(argv[7]);
      i = dbmatches(*datascopedbPtr,dbPtr1, &processTable, &exprTable,&hook,
		    &nojoinTable);
      if (i < 0)
	  return(i);
      sprintf(outBuf,"%i|",i);
      j = strlen(outBuf);
      dbTable2str(nojoinTable, (char *) (outBuf + j));
      outBufStrLen = strlen(outBuf);
      i  = 0;
  }
  else if (!strcmp(argv[0],"dbread_view")) {
      /**** - NOTE THE DIFFERENCE IN ARGUMENTATION - ****/
      /* argv[1]-argv[4] contains the datascopedbPtr String values 
	 argv[5] is the name of new table; if empty string then a name is generated */
      /* inBuf = is a buffer containing the contents of the file
	         and is written into a local tmp file before
		 performing the dbread_view operation */
      /* return value is the value returned by the operation */
      if (atoi(argv[1]) != dbINVALID) {
	  datascopedbPtr->database = atoi(argv[1]);
	  datascopedbPtr->table =  atoi(argv[2]);
	  datascopedbPtr->field =  atoi(argv[3]);
	  datascopedbPtr->record =  atoi(argv[4]);
      }
      sprintf(fileNameString,"/tmp/DSread_view.%i.%i.%ld.%ld,%ld",
              datascopedbPtr->database,datascopedbPtr->table,
              (long) time(NULL),getpid(), (long) random());
      tmpfd = fopen(fileNameString,"w+");
      i  = 0;
      while (tmpfd == NULL && i < 5) {
          sprintf(fileNameString2,"%ld", (long) random());
          strcat(fileNameString,fileNameString2);
          tmpfd = fopen(fileNameString,"w+");
          i++;
      }
      if (tmpfd == NULL) {
          fprintf(stdout,"datascopeProc: dbread_view: unable to open local tmp file:%s\n",fileNameString);
	  i = -errno;
	  return(i);
      }
      i = fwrite(inBuf,1,inLen,tmpfd);
      if (i != inLen) {
	  fclose(tmpfd);
	  tmpfd = NULL;
          unlink(fileNameString);
	  return(TMP_FILE_WRITE_ERROR);
      }
      fseek(tmpfd, SEEK_SET, 0);
      if (argv[5] != NULL && strlen(argv[5]) > 0)
	  i = dbread_view (tmpfd, datascopedbPtr,argv[5]);
      else
	  i = dbread_view (tmpfd, datascopedbPtr,0);
      fclose(tmpfd);
      tmpfd = NULL;
      unlink(fileNameString);
      return(i);
  }
  else if (!strcmp(argv[0],"dbread_view_from_server_file")) {
      /* argv[1] contains the file name 
	 argv[2] is the name of new table; if empty string then a name is generated */
      /* inBuf = datascopedbPtr String */
      /* return value is the value returned by the operation */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      tmpfd = fopen(argv[1],"r");
      if (tmpfd == NULL) {
	  fprintf(stdout,"datascopeProc: dbread_view_from_server_file: unable to server file:%s\n",argv[1]);
          i = -errno;
          return(i);
      }
      if (argv[2] != NULL && strlen(argv[2]) > 0)
          i = dbread_view (tmpfd, datascopedbPtr,argv[2]);
      else
          i = dbread_view (tmpfd, datascopedbPtr,0);
      fclose(tmpfd);
      tmpfd = NULL;
      return(i);
  }
  else if (!strcmp(argv[0],"dbwrite_view")) {
      /* outBuf gets the buffer that is the contents of the file. If file contents
	 is longer than outBufLen, then the rest can be read through srbObjRead */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      sprintf(fileNameString,"/tmp/DSdbwrite_view.%i.%i.%ld.%ld,%ld",
              datascopedbPtr->database,datascopedbPtr->table,
              (long) time(NULL),getpid(), (long) random());
      tmpfd = fopen(fileNameString,"w+");
      i  = 0;
      while (tmpfd == NULL && i < 5) {
          sprintf(fileNameString2,"%ld", (long) random());
          strcat(fileNameString,fileNameString2);
          tmpfd = fopen(fileNameString,"w+");
          i++;
      }
      if (tmpfd == NULL) {
          fprintf(stdout,"datascopeProc: dbwrite_view: unable to open local tmp file:%s\n",fileNameString);
	  i = -errno;
	  return(i);
      }
      i = dbwrite_view (*datascopedbPtr, tmpfd);
      if (i < 0) {
          fclose(tmpfd);
	  tmpfd = NULL;
          unlink(fileNameString);
          return(i);
      }
      fseek(tmpfd, SEEK_SET, 0);
      i = fread (outBuf, 1,outLen,tmpfd);
      if (i == outLen) {
          datascopeSI->firstRead = -1;
          datascopeSI->dbfilefd = tmpfd;
          return(i);
      }
      else {
          fclose(tmpfd);
	  tmpfd = NULL;
          unlink(fileNameString);
          return(i);
      }
  }
  else if (!strcmp(argv[0],"dbwrite_view_to_server_file")) {
      /* argv[1] contains the file name */
      /* inBuf = datascopedbPtr String */
      /* return value is the value returned by the operation */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      tmpfd = fopen(argv[1],"w+");
      if (tmpfd == NULL) {
          fprintf(stdout,"datascopeProc: dbread_view_to_server_file: unable to server file:%s\n",argv[1]);
          i = -errno;
          return(i);
      }
      i = dbwrite_view (*datascopedbPtr,tmpfd);
      fclose(tmpfd);
      tmpfd = NULL;
      return(i);
  }
  else if (!strcmp(argv[0],"dbcopy")) {
      /* argv[1] - argv[4] = database pointer number2
	 argv[5] = expressions array String separated by ;; */
      /* inBuf = datascopedbPtr String */
      /* returns the value returned by the operation */
      if (inLen > 0)
          str2dbPtr(inBuf,datascopedbPtr);
      /*str2dbPtr(argv[1],&dbPtr1);*/
      dbPtr1.database = atoi(argv[1]);
      dbPtr1.table =  atoi(argv[2]);
      dbPtr1.field =  atoi(argv[3]);
      dbPtr1.record =  atoi(argv[4]);
      if (strlen(argv[5]) == 0)
	  exprArray = NULL;
      else
	  exprArray =  str2dbArray( argv[5]);
      i = dbcopy(*datascopedbPtr, dbPtr1, exprArray);
      return(i);
  }
  else {
      return(FUNCTION_NOT_SUPPORTED);
  }
  if (processTable != NULL)
      freetbl(processTable,0);
  if (exprTable != NULL)
      freetbl(exprTable,0);
  if (nojoinTable != NULL)
      freetbl(nojoinTable,0);
  if (exprArray != NULL)
      freearr(exprArray,0);
  if (i < 0)
      return(i);
  else
      return(outBufStrLen);
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
  char *dsFindRev;
  char *tmpPtr;
  char *dsposition;
  char *dstimeout;
  char *dsnumofpkts;
  char *dspresentation;
  char *dsnumbulkreads;
  char *dsProcess;
  char *dsfilename;
  dsTable = strstr(datascopeDataDesc,"<DSTABLE>");
  while (dsTable != NULL && ((tmpPtr =  strstr(dsTable+2,"<DSTABLE>")) != NULL))
      dsTable = tmpPtr;
  dsFind  = strstr(datascopeDataDesc,"<DSFIND>");
  while (dsFind != NULL && ((tmpPtr =  strstr(dsFind+2,"<DSFIND>")) != NULL))
      dsFind = tmpPtr;
  dsFindRev = strstr(datascopeDataDesc,"<DSFINDREV>");
  while (dsFindRev != NULL && ((tmpPtr =  strstr(dsFindRev+2,"<DSFINDREV>")) != NULL))
      dsFindRev = tmpPtr;
  dsProcess  = strstr(datascopeDataDesc,"<DSPROCESS>");
  while (dsProcess != NULL && ((tmpPtr =  strstr(dsProcess+2,"<DSPROCESS>")) != NULL))
      dsProcess  = tmpPtr;
  dsposition  = strstr(datascopeDataDesc,"<DSPOSITION>");
  while (dsposition != NULL && ((tmpPtr =  strstr(dsposition+2,"<DSPOSITION>")) != NULL))
      dsposition = tmpPtr;
  dstimeout  = strstr(datascopeDataDesc,"<DSTIMEOUT>");
  while (dstimeout != NULL && ((tmpPtr =  strstr(dstimeout+2,"<DSTIMEOUT>")) != NULL))
      dstimeout = tmpPtr;
  dsnumofpkts  = strstr(datascopeDataDesc,"<DSNUMOFPKTS>");
  while (dsnumofpkts != NULL && ((tmpPtr =  strstr(dsnumofpkts+2,"<DSNUMOFPKTS>")) != NULL))
      dsnumofpkts = tmpPtr;
  dspresentation  = strstr(datascopeDataDesc,"<DSPRESENTATION>");
  while (dspresentation != NULL && ((tmpPtr =  strstr(dspresentation +2,"<DSPRESENTATION>")) != NULL))
    dspresentation = tmpPtr; 
  dsnumbulkreads  = strstr(datascopeDataDesc,"<DSNUMBULKREADS>");
  while (dsnumbulkreads != NULL && ((tmpPtr =  strstr(dsnumbulkreads +2,"<DSNUMBULKREADS>")) != NULL))
      dsnumbulkreads = tmpPtr;
  dsfilename   = strstr(datascopeDataDesc,"<DSFILENAME>");
  while (dsfilename != NULL && ((tmpPtr =  strstr(dsfilename +2 ,"<DSFILENAME>")) != NULL))
    dsfilename = tmpPtr; 


  if (dsTable != NULL) {
    *dsTable = '\0';
    dsTable += 9;
    if ((tmpPtr  =  strstr(dsTable,"</DSTABLE>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsTable: %s\n",dsTable);
/*      return(INP_ERR_RES_FORMAT);*/
    }
    else
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
/*      return(INP_ERR_RES_FORMAT);*/
    }
    else
	*tmpPtr = '\0';
    if ((datascopeSI->dsfind  =strdup(dsFind)) == NULL)
      return MEMORY_ALLOCATION_ERROR;
    mapStringWithEqualString(datascopeSI->dsfind, " AND ", " &&  ");
  }
  else 
    datascopeSI->dsfind = NULL;

  if (dsFindRev != NULL) {
      *dsFindRev = '\0';
      dsFindRev += 11;
      if ((tmpPtr  =  strstr(dsFindRev,"</DSFINDREV>")) == NULL) {
	  fprintf(stdout, "getStateInfo:  Error in dsFindRev: %s\n",dsFindRev);
/*  	  return(INP_ERR_RES_FORMAT);*/
      }
      else
	  *tmpPtr = '\0';
      if ((datascopeSI->dsfindRev  =strdup(dsFindRev)) == NULL)
	  return MEMORY_ALLOCATION_ERROR;
      mapStringWithEqualString(datascopeSI->dsfindRev, " AND ", " &&  ");
  }
  else
      datascopeSI->dsfindRev = NULL;


  if (dsProcess != NULL) {
    *dsProcess = '\0';
    dsProcess += 11;
    if ((tmpPtr  =  strstr(dsProcess,"</DSPROCESS>")) == NULL) {
      fprintf(stdout, "getStateInfo:  Error in dsProcess: %s\n",dsProcess);
/*      return(INP_ERR_RES_FORMAT);*/
    }
    else
	*tmpPtr = '\0';
    mapStringWithEqualString(dsProcess, " AND ", " ;;  ");
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
/*      return(INP_ERR_RES_FORMAT);*/
    }
    else
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
/*      return(INP_ERR_RES_FORMAT); */
    }
    else
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
/*      return(INP_ERR_RES_FORMAT); */
    }
    else
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
/*      return(INP_ERR_RES_FORMAT);*/
    }
    else
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
/*      return(INP_ERR_RES_FORMAT); */
    }
    else
	*tmpPtr = '\0';
    datascopeSI->numbulkreads  = atoi(dsnumbulkreads);
  }
  else 
    datascopeSI->numbulkreads = 1;

  if (dsfilename  != NULL) {
      *dsfilename = '\0';
      dsfilename += 12;
      if ((tmpPtr  =  strstr(dsfilename,"</DSFILENAME>")) == NULL) {
	  fprintf(stdout, "getStateInfo:  Error in dsfilename: %s\n",dsfilename);
/*	  return(INP_ERR_RES_FORMAT); */
      }
      else
	  *tmpPtr = '\0';
    if((datascopeSI->tmpFileName = strdup(dsfilename)) == NULL)
      return MEMORY_ALLOCATION_ERROR;
  }
  else
      datascopeSI->tmpFileName = NULL;

  datascopeSI->firstRead = 1;
  datascopeSI->datascopeFlags = datascopeFlags;
  datascopeSI->datascopeMode = datascopeMode;
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

