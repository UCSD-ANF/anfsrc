/**************************************************************************
Copyright Notice
All Rights Reserved
Please refer to files in COPYRIGHT directory under the SRB software directory
for copyright, usage, liability and license information.
Please read these files before using,modifying or distributing SRB software.
**************************************************************************/

#include <stdio.h>
#ifndef _WIN32
#include <unistd.h>
#include <sys/file.h>
#include <sys/stat.h>
#endif
#include "scommands.h"

// in-line functions
#define  DEBUGON
#ifdef   DEBUGON

#ifndef  DEBUG
#define  DEBUG( ... ) { fprintf(stderr, ">>>>\"%s:%u\" %s: ",__FILE__,__LINE__, __FUNCTION__); fprintf(stderr, __VA_ARGS__); fprintf( stderr, "\n"); }
#endif

#else

#ifndef  DEBUG
#define  DEBUG( ... ) 
#endif 

#endif

#ifndef FREEIF
#define FREEIF(pi)		{ if (pi) { free((void *)pi); (pi)=0; }}
#endif


extern char mdasCollectionName[];
extern char mdasCollectionHome[];
extern char srbAuth[];
extern char srbHost[];
extern char inCondition[];
int c_value = 0;


int srbObjInsertUserMetadata(srbConn *conn, char *parColl, char *dataObj,
                char *mdAttName, char *mdAttValue, char *mdAttUnit);
int srbCollectionInsertUserMetadata(srbConn *conn,
                char *collName,char *mdAttName,char *mdAttValue, char *mdAttUnit);
int
getMetaForObj(srbConn *conn, char *objName);
int
extractMetaDataUsingStyleSheet(srbConn *conn,int argc, char **argv);
int
doMetaCopy(srbConn *conn,int C_value, int argc, char **argv);
int
bulkLoadMetaDataClient(srbConn *conn,
                       int c_value,
                       int r_value,
                       int u_value,
                       int D_value,
                       char *metaFile,
                       char *separator,
                       char *trgName);
int
getMetaForRsrc(srbConn *conn, char *objName);
int
getMetaForUser(srbConn *conn, char *objName);
int srbUserInsertUserMetadata(srbConn *conn,
                                  char *userNameDomainName,
                                  char *mdAttName,
                                  char *mdAttValue,
                                  char *mdAttUnit);
int srbResourceInsertUserMetadata(srbConn *conn,
                                  char *rsrcName,
                                  char *mdAttName,
                                  char *mdAttValue,
                                  char *mdAttUnit);
int
doMetaQueryForCollection(srbConn *conn,int argc, char **inargv);
int
doMetaQueryForResource(srbConn *conn,int argc, char **inargv);
int
doMetaQueryForUser(srbConn *conn,int argc, char **inargv);
int
doMetaQueryForDataset(srbConn *conn,int argc, char **inargv);
int
doMetaRemoveForCollection(srbConn *conn,int argc, char **argv);
int
doMetaRemoveForResource(srbConn *conn,int argc, char **argv);
int
doMetaRemoveForUser(srbConn *conn,int argc, char **argv);
int
doMetaRemoveForDataset(srbConn *conn,int argc, char **argv);
int
doMetaQuery (srbConn *conn,
             int c_value,
             int r_value,
             int u_value,
             int argc,
             char **argv);
int
doMetaRemove (srbConn *conn,
             int c_value,
             int r_value,
             int u_value,
             int argc,
             char **argv);

static void usage(char *prog)
{
   fprintf(stderr,"Usage: %s AttName AttValue [AttUnit] datasetName\n",prog);

   fprintf(stderr,"Usage: %s -c AttName AttValue [AttUnit] collectionName\n",prog);
   fprintf(stderr,"Usage: %s -u AttName AttValue [AttUnit] userName@Domain\n",prog);
   fprintf(stderr,"Usage: %s -r AttName AttValue [AttUnit] resourceName\n",prog);
   fprintf(stderr,"Usage: %s [-d] -f metadataFileName separator datasetName\n",prog);
   fprintf(stderr,"Usage: %s -c -f metadataFileName separator collectionName\n",prog);   
   fprintf(stderr,"Usage: %s -r -f metadataFileName separator resourceName\n",prog);   
   fprintf(stderr,"Usage: %s -u -f metadataFileName separator\n",prog);   
   fprintf(stderr,"Usage: %s -D -f metadataFileName separator\n",prog);
   fprintf(stderr,"Usage: %s [-d] -Q AttName Op AttValue [AttName Op AttValue] ... (upto 5) \n",prog);
   fprintf(stderr,"Usage: %s -Q -c AttName Op AttValue [AttName Op AttValue] ... (upto 5)\n",prog);
   fprintf(stderr,"Usage: %s -Q -u AttName Op AttValue [AttName Op AttValue] ... (upto 4)\n",prog);
   fprintf(stderr,"Usage: %s -Q -r AttName Op AttValue [AttName Op AttValue] ... (upto 4)\n",prog);
   fprintf(stderr,"Usage: %s datasetName|collName\n",prog);
   fprintf(stderr,"Usage: %s -u userName@domainName\n",prog);
   fprintf(stderr,"Usage: %s -r resourceName\n",prog);
   fprintf(stderr,"Usage: %s -R -d AttName AttValue datasetName\n",prog);
   fprintf(stderr,"Usage: %s -R -c AttName AttValue collectionName\n",prog);
   fprintf(stderr,"Usage: %s -R -u AttName AttValue userName@Domain\n",prog);
   fprintf(stderr,"Usage: %s -R -r AttName AttValue resourceName\n",prog);
   fprintf(stderr,"Usage: %s -e [inSRBMetadataFileName] inSRBExtractorStyleSheet datasetName\n",prog);
   fprintf(stderr,"Usage: %s -C 1 sourceCollectionName targetDataName\n",prog);
   fprintf(stderr,"Usage: %s -C 2 sourceCollectionName targetCollectionName\n",prog);
   fprintf(stderr,"Usage: %s -C 3 sourceDataName targetDataName\n",prog);
   fprintf(stderr,"Usage: %s -C 4 sourceDataName targetCollectionName\n",prog);


   fprintf(stderr,"The first four  synopses are used to ingest metadata\n   for srbData, srbCollections,  srbUsers and srbResources  respectively.\n");
   fprintf(stderr,"The next four synopses [-dcru -f] are used to ingest bulk metadata\n   for single  objects such as srbData, srbCollections, srbUsers and srbResources respectively.\n");
   fprintf(stderr,"The next  synopsis [-D -f]are used to ingest bulk metadata\n   for srbData for many data .\n");

   fprintf(stderr,"The next four synopses [-Q] are used to query metadata\n   for srbData and srbCollections respectively.\n");
   fprintf(stderr,"The next three synopses are used to get all metadata values\n for srbData, srbCollections, srbUsers and srbResources.\n");
   fprintf(stderr,"The next four synopses (-R option) are used to  delete metadata identified by AttNAme-AttValue pairs \n for srbData, srbCollections, srbUsers and srbResources.\n");
   fprintf(stderr,"Use '*' and '?' for wildcards; assumes an 'and' between conditions\n");
   fprintf(stderr,"The next synopsis (-e option) allows for (remote) extracting of metadata \n using a T-language template stored in the SRB by extracting the metadata  either from\n the dataset itself or from another metadata file which is also stored in the SRB.\n");
   fprintf(stderr,"The next four synopses (-C option) are used to copy metadata from one SRB object/collection to another SRB object/collection.\n");
   fprintf(stderr,"Sample Usage:\n");
   fprintf(stderr,"   Sufmeta alpha 200 foo.dat\n");
   fprintf(stderr,"   Sufmeta -c alpha 200 myColl\n");
   fprintf(stderr,"   Sufmeta -c beta bar myColl\n");
   fprintf(stderr,"   Sufmeta -c beta 200 myColl\n");
   fprintf(stderr,"   Sufmeta -Q  alpha = 200\n");
   fprintf(stderr,"   Sufmeta -Q  -c alpha = 200 beta = bar\n");
   fprintf(stderr,"   Sufmeta -Q  -c alpha = 200 beta like '*a*' \n");
   fprintf(stderr,"   Sufmeta -Q  -c alpha '>' 100 beta like '*a*' \n");
   fprintf(stderr,"   Sufmeta foo.dat\n");
   fprintf(stderr,"   Sufmeta -f mdFile '|' ticket123.dat\n");
   fprintf(stderr,"   Sufmeta -c -f mdFile '|' ticket123.dat\n");
   fprintf(stderr,"   where mdFile maybe of the form:\n");
   fprintf(stderr,"ticketnum|es2345\n");
   fprintf(stderr,"car name|ford escort\n");
   fprintf(stderr,"driver name|john q. public\n");
   fprintf(stderr,"numplate|123455\n");
   fprintf(stderr,"speed|89|kmph|overspeed\n");
   fprintf(stderr,"fine|55|dollars\n");
   fprintf(stderr,"Note that blanks before and after '|' will be taken to be part of the metadata being ingested\n");

}


int main(int argc, char **argv)
{
  char temp[MAX_TOKEN], temp1[MAX_TOKEN];
  char metaFile[MAX_TOKEN];
  int i, nArgv;
  int c;
  int u_value, r_value, Q_value, D_value, R_value, e_value, C_value;
  srbConn *conn;
  int status;

  char iName[MAX_TOKEN], iVal[MAX_TOKEN],iUnit[MAX_TOKEN];

  char targColl[MAX_TOKEN], targObj[MAX_TOKEN];

   metaFile[0] = '\0';
   i = initSrbClientEnv();
    if (i < 0)
      {printf("Smeta Initialization Error:%i\n",i); exit(1);}
 
    c_value = 0;
    e_value = 0;
    r_value = 0;
    u_value = 0;
    Q_value = 0;
    D_value =  0;
    R_value =  0;
    C_value = 0;
    conn = srbConnect (srbHost, NULL, srbAuth, 
     NULL, NULL, NULL, NULL);
    if (clStatus(conn) != CLI_CONNECTION_OK) {
      fprintf(stderr,"Connection to srbMaster failed.\n");
      fprintf(stderr,"%s",clErrorMessage(conn));
      srb_perror (2, clStatus(conn), "", SRB_RCMD_ACTION|SRB_LONG_MSG);
      clFinish(conn); exit(3);
    }

  if (argc == 2 && strcmp(argv[1],"-h") ) {
    i = getMetaForObj(conn,argv[1]);
    if (i < 0) 
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }
    

  if (argc < 3) {
    usage(argv[0]);
    clFinish(conn);
    exit(1);
  }

    

  strcpy(inCondition , "");

  /* Removed -L option, no longer in use 2-7-01 Roman */
  while ((c=getopt(argc, argv,"QurhRDecC:f:")) != EOF) {
        switch (c) {
            case 'h':
		usage (argv[0]);
		clFinish(conn);
                exit(1);
                break;
	    case 'c':
	      c_value = 1;
		break;
	    case 'C':
	      C_value = atoi(optarg);
		break;
	    case 'e':
	      e_value = 1;
		break;
	    case 'u':
	      u_value = 1;
		break;
	    case 'r':
	      r_value = 1;
		break;
	    case 'D':
	      D_value = 1;
		break;
	    case 'R':
	      R_value = 1;
		break;
	    case 'Q':
	      Q_value = 1;
		break;
	    case 'f':
	      strcpy (metaFile, optarg);
	      break;
            default:
                usage (argv[0]);
		clFinish(conn);
                exit(1);
        }
  }

  if (e_value == 1) {
    i = extractMetaDataUsingStyleSheet(conn,argc,argv);
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }
  if (C_value > 0) {
    if (argc != 5) {
      usage (argv[0]);
      clFinish(conn);
      exit(1);
    }
    i = doMetaCopy(conn, C_value,argc,argv);
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }
  if (Q_value == 1) {
    i = doMetaQuery(conn,c_value,r_value,u_value,argc,argv);
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }
  if (R_value == 1) {
    if (argc != 6 ) {
      usage (argv[0]);
      clFinish(conn);
      exit(1);
    }
    i = doMetaRemove(conn,c_value,r_value,u_value,argc,argv);
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }

  if (metaFile[0] != '\0') {
    i = bulkLoadMetaDataClient(conn, 
			       c_value,r_value,u_value,D_value,
			       metaFile,argv[argc-2],argv[argc-1]);
    if (i < 0) 
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }
  else if (r_value == 1 && argc == 3) {
    i = getMetaForRsrc(conn, argv[2]);
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);
  }
  else if (u_value == 1 && argc == 3) {
    i = getMetaForUser(conn,argv[2]);
    clFinish(conn);
    if (i < 0) {
      fprintf(stderr,"Error: %i\n",i);
      exit(1);
    }
    else 
      exit(0);

  }

  nArgv = argc - optind;

  if(nArgv == 3)
  {
     strcpy(iName,argv[argc-3]);
     strcpy(iVal, argv[argc-2]);
     iUnit[0] = '\0';
  }
  else if(nArgv == 4)
  {
     strcpy(iName,argv[argc-4]);
     strcpy(iVal, argv[argc-3]);
     strcpy(iUnit,argv[argc-2]);
  }
  else
  {
     usage(argv[0]);
     clFinish(conn);
     exit(1);
  }



  if (c_value == 1) /* for a collection */
  {
    sprintf(temp,"%s/alpha",argv[argc-1]);
    splitpath(temp,targColl, temp1);
    status =  srbCollectionInsertUserMetadata(conn,targColl,
			iName, iVal, iUnit);
  }
  else if(u_value == 1) /* for a user */
  {
     status = srbUserInsertUserMetadata(conn,argv[argc-1],
			iName, iVal, iUnit);
  }
  else if(r_value == 1) /* for a resource */
  {
     status = srbResourceInsertUserMetadata(conn,argv[argc-1],
			iName, iVal, iUnit);
  }
  else   /* for a dataset */
  {
     splitpath(argv[argc-1],targColl,targObj);
     status = srbObjInsertUserMetadata(conn,targColl,targObj,
			iName, iVal, iUnit);
  }

  if(status < 0)
  {
     srb_perror (2, status, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
  }

  return status;
}

int srbResourceInsertUserMetadata(srbConn *conn,
				  char *rsrcName,
				  char *mdAttName,
				  char *mdAttValue, 
				  char *mdAttUnit)
{
   char AttName[MAX_TOKEN], AttVal[MAX_TOKEN],AttUnit[MAX_TOKEN], NewVal[MAX_TOKEN];
   int  LocalStatus;
   int  MdIdx;

   if((mdAttName == NULL) || (strlen(mdAttName) == 0))
     return -1;

   if((mdAttValue == NULL) || (strlen(mdAttValue) == 0))
     return -1;

   strcpy(AttName,mdAttName);
   strcpy(AttVal,mdAttValue);
   MdIdx = srbModifyResource(conn, MDAS_CATALOG, rsrcName,
                           "0",AttName,"","",
                           R_INSERT_USER_DEFINED_STRING_META_DATA);
   if(MdIdx < 0)
     return MdIdx;

   sprintf(NewVal,"1@%i",MdIdx);
   LocalStatus = srbModifyResource(conn, MDAS_CATALOG, rsrcName,
                   NewVal,AttVal,"","",
                   R_CHANGE_USER_DEFINED_STRING_META_DATA);

   if(LocalStatus < 0)
     return LocalStatus;

   if((mdAttUnit != NULL) && (strlen(mdAttUnit) > 0))
   {
      strcpy(AttUnit,mdAttUnit);
      sprintf(NewVal,"2@%i",MdIdx);
      LocalStatus = srbModifyResource(conn, MDAS_CATALOG, rsrcName,
                             NewVal,AttUnit,"","",
                             R_CHANGE_USER_DEFINED_STRING_META_DATA);

      if(LocalStatus < 0)
        return LocalStatus;
   }

   return 0;

}

int srbUserInsertUserMetadata(srbConn *conn,
				  char *userNameDomainName,
				  char *mdAttName,
				  char *mdAttValue, 
				  char *mdAttUnit)
{

   char AttName[MAX_TOKEN], AttVal[MAX_TOKEN],AttUnit[MAX_TOKEN], NewVal[MAX_TOKEN];
   int  LocalStatus;
   int  MdIdx;

   if((mdAttName == NULL) || (strlen(mdAttName) == 0))
     return -1;

   if((mdAttValue == NULL) || (strlen(mdAttValue) == 0))
     return -1;

   strcpy(AttName,mdAttName);
   strcpy(AttVal,mdAttValue);
   MdIdx = srbModifyUserNonPriv(conn, MDAS_CATALOG, userNameDomainName,
                           "0",AttName,"","","",
                           U_INSERT_USER_DEFINED_STRING_META_DATA);
   if(MdIdx < 0)
     return MdIdx;

   sprintf(NewVal,"1@%i",MdIdx);
   LocalStatus = srbModifyUserNonPriv(conn, MDAS_CATALOG, userNameDomainName,
                   NewVal,AttVal,"","","",
                   U_CHANGE_USER_DEFINED_STRING_META_DATA);

   if(LocalStatus < 0)
     return LocalStatus;

   if((mdAttUnit != NULL) && (strlen(mdAttUnit) > 0))
   {
      strcpy(AttUnit,mdAttUnit);
      sprintf(NewVal,"2@%i",MdIdx);
      LocalStatus = srbModifyUserNonPriv(conn, MDAS_CATALOG, userNameDomainName,
                             NewVal,AttUnit,"","","",
                             U_CHANGE_USER_DEFINED_STRING_META_DATA);

      if(LocalStatus < 0)
        return LocalStatus;
   }

   return 0;
}

int srbCollectionInsertUserMetadata(srbConn *conn,
			char *collName,char *mdAttName,char *mdAttValue, char *mdAttUnit)
{
   char AttName[MAX_TOKEN], AttVal[MAX_TOKEN],AttUnit[MAX_TOKEN], NewVal[MAX_TOKEN];
   int  LocalStatus;
   int  MdIdx;

   if((mdAttName == NULL) || (strlen(mdAttName) == 0))
     return -1;

   if((mdAttValue == NULL) || (strlen(mdAttValue) == 0))
     return -1;

   strcpy(AttName,mdAttName);
   strcpy(AttVal,mdAttValue);
   MdIdx = srbModifyCollect(conn, MDAS_CATALOG,
                           collName,
                           "0",AttName,"",
                           C_INSERT_USER_DEFINED_COLL_STRING_META_DATA);
   if(MdIdx < 0)
     return MdIdx;

   sprintf(NewVal,"1@%i",MdIdx);
   LocalStatus = srbModifyCollect(conn, MDAS_CATALOG,
                   collName,
                   NewVal,AttVal, "",
                   C_CHANGE_USER_DEFINED_COLL_STRING_META_DATA);

   if(LocalStatus < 0)
     return LocalStatus;

   if((mdAttUnit != NULL) && (strlen(mdAttUnit) > 0))
   {
      strcpy(AttUnit,mdAttUnit);
      sprintf(NewVal,"2@%i",MdIdx);
      LocalStatus = srbModifyCollect(conn, MDAS_CATALOG,
                             collName,
                             NewVal,AttUnit,"",
                             C_CHANGE_USER_DEFINED_COLL_STRING_META_DATA);

      if(LocalStatus < 0)
        return LocalStatus;
   }

   return 0;
}

int srbObjInsertUserMetadata(srbConn *conn, char *parColl, char *dataObj,
                char *mdAttName, char *mdAttValue, char *mdAttUnit)
{
   char AttName[MAX_TOKEN], AttVal[MAX_TOKEN],AttUnit[MAX_TOKEN], NewVal[MAX_TOKEN];
   int  LocalStatus;
   int  MdIdx;

   if((mdAttName == NULL) || (strlen(mdAttName) == 0))
     return -1;

   if((mdAttValue == NULL) || (strlen(mdAttValue) == 0))
     return -1;

   strcpy(AttName,mdAttName);
   strcpy(AttVal,mdAttValue);
   MdIdx = srbModifyDataset(conn, MDAS_CATALOG, dataObj,parColl, "","",
                           "0",AttName,
                           D_INSERT_USER_DEFINED_STRING_META_DATA);
   if(MdIdx < 0)
     return MdIdx;

   sprintf(NewVal,"1@%i",MdIdx);
   LocalStatus = srbModifyDataset(conn, MDAS_CATALOG, dataObj,parColl, "","",
                   NewVal,AttVal,
                   D_CHANGE_USER_DEFINED_STRING_META_DATA);

   if(LocalStatus < 0)
     return LocalStatus;

   if((mdAttUnit != NULL) && (strlen(mdAttUnit) > 0))
   {
      strcpy(AttUnit,mdAttUnit);
      sprintf(NewVal,"2@%i",MdIdx);
      LocalStatus = srbModifyDataset(conn, MDAS_CATALOG, dataObj,parColl, "","",
                             NewVal,AttUnit,
                             D_CHANGE_USER_DEFINED_STRING_META_DATA);

      if(LocalStatus < 0)
        return LocalStatus;
   }

   return 0;
}

int
doMetaQuery (srbConn *conn, 
	     int c_value,
	     int r_value, 
	     int u_value,
	     int argc, 
	     char **argv)
{
  int i;
  if (c_value == 1) 
    i = doMetaQueryForCollection(conn,argc,argv);
  else if (r_value == 1) 
    i = doMetaQueryForResource(conn,argc,argv);
  else if (u_value == 1) 
    i = doMetaQueryForUser(conn,argc,argv);
  else 
    i = doMetaQueryForDataset(conn,argc,argv);
   return(i);

}

int
doMetaRemove (srbConn *conn, 
	     int c_value,
	     int r_value, 
	     int u_value,
	     int argc, 
	     char **argv)
{
  int i;
  if (c_value == 1) 
    i = doMetaRemoveForCollection(conn,argc,argv);
  else if (r_value == 1) 
    i = doMetaRemoveForResource(conn,argc,argv);
  else if (u_value == 1) 
    i = doMetaRemoveForUser(conn,argc,argv);
  else 
    i = doMetaRemoveForDataset(conn,argc,argv);
   return(i);

}

int
doMetaRemoveForCollection(srbConn *conn,int argc, char **argv)
{
  
  int i;
  i = srbModifyCollect(conn, MDAS_CATALOG,
                           argv[argc-1],
                           argv[3],argv[4],"",
                           C_DELETE_USER_DEFINED_ATTR_VAL_META_DATA);
  return(i);
}

int
doMetaRemoveForDataset(srbConn *conn,int argc, char **argv)
{
  
  int i;
  char  targColl[MAX_TOKEN], targObj[MAX_TOKEN];

  splitpath(argv[argc-1],targColl,targObj);
  i = srbModifyDataset(conn, MDAS_CATALOG,targObj,targColl,"","",
		       argv[3],argv[4],
		       D_DELETE_USER_DEFINED_ATTR_VAL_META_DATA);
  return(i);
}

int
doMetaRemoveForResource(srbConn *conn,int argc, char **argv)
{
  
  int i;

  i = srbModifyResource(conn, MDAS_CATALOG,argv[argc-1],
                           argv[3],argv[4],"","",
		       R_DELETE_USER_DEFINED_ATTR_VAL_META_DATA);
  return(i);
}

int
doMetaRemoveForUser(srbConn *conn,int argc, char **argv)
{
  
  int i;

  i = srbModifyUserNonPriv(conn, MDAS_CATALOG, argv[argc-1],
			   argv[3],argv[4],"","","",
                           U_DELETE_USER_DEFINED_ATTR_VAL_META_DATA);
  return(i);
}




int
doMetaQueryForDataset(srbConn *conn,int argc, char **inargv)
{


    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    int i, jj;
    int status;
    char argv[SMALL_TOKEN][MAX_TOKEN];

    for (i = 0; i < argc; i++)
      strcpy(argv[i], inargv[i]);

    for (i = 0; i < MAX_DCS_NUM; i++) {
        sprintf(qval[i],"");
        selval[i] = 0;
    }
    for (jj =  0,i =  2; i < argc && jj < 5 ; i =  i+3, jj++) {
      if (i +2 >= argc) {
	printf("Error in number of arguments expected\n");
	return(-1);
      }
      if (!strcmp(argv[i+1],"like") || !strcmp(argv[i+1],"LIKE") ) {
	make_like_for_mdas(argv[i+2]);
#ifdef MCAT_VERSION_10
	strcat (argv[i+2], " %%' ESCAPE '\\");
#else
	strcat (argv[i+2], "' ESCAPE '\\");
#endif
      }
      if (jj == 0) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD0]," like  '%s  %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD0]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD0]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 1) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD0_1]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD0_1]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD0_1]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD1_1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 2) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD0_2]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD0_2]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD0_2]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD1_2]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 3) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD0_3]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD0_3]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD0_3]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD1_3]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 4) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD0_4]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD0_4]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD0_4]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD1_4]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }

    }
    selval[DATA_GRP_NAME] = 1;
    selval[DATA_NAME] = 1;
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    if (status < 0)     {
	if (status == MCAT_INQUIRE_ERROR)
	  printf("No Answer found for the Query\n");
	return(1);
    }
    else {
      show_results(conn, qval, selval, &myresult, DEFAULT_FIELD_WIDTH,
		   DEFAULT_ROW_COUNT);
    }
    return(0);

}


int
doMetaQueryForCollection(srbConn *conn,int argc, char **inargv)
{

    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    int i, jj;
    int status;
    char argv[SMALL_TOKEN][MAX_TOKEN];

    for (i = 0; i < argc; i++)
      strcpy(argv[i], inargv[i]);

    for (i = 0; i < MAX_DCS_NUM; i++) {
        sprintf(qval[i],"");
        selval[i] = 0;
    }
    for (jj =  0,i =  3; i < argc && jj < 5 ; i =  i+3, jj++) {
      if (i +2 >= argc) {
	printf("Error in number of arguments expected\n");
	return(-1);
      }
      if (!strcmp(argv[i+1],"like") || !strcmp(argv[i+1],"LIKE") ) {
	make_like_for_mdas(argv[i+2]);
#ifdef MCAT_VERSION_10
	strcat (argv[i+2], " %%' ESCAPE '\\");
#else
	strcat (argv[i+2], "' ESCAPE '\\");
#endif
      }
      if (jj == 0) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_COLL0]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_COLL0]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_COLL0]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_COLL1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 1) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_COLL0_1]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_COLL0_1]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_COLL0_1]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_COLL1_1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 2) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_COLL0_2]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_COLL0_2]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_COLL0_2]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_COLL1_2]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 3) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_COLL0_3]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_COLL0_3]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_COLL0_3]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_COLL1_3]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 4) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_COLL0_4]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_COLL0_4]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_COLL0_4]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_COLL1_4]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }

    }
    selval[DATA_GRP_NAME] = 1;
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    if (status < 0)     {
	if (status == MCAT_INQUIRE_ERROR)
	  printf("No Answer found for the Query\n");
	return(1);
    }
    else {
      show_results(conn, qval, selval, &myresult, DEFAULT_FIELD_WIDTH,
		   DEFAULT_ROW_COUNT);
    }
    return(0);

}


int
doMetaQueryForResource(srbConn *conn,int argc, char **inargv)
{

    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    int i, jj;
    int status;
    char argv[SMALL_TOKEN][MAX_TOKEN];

    for (i = 0; i < argc; i++)
      strcpy(argv[i], inargv[i]);

    for (i = 0; i < MAX_DCS_NUM; i++) {
        sprintf(qval[i],"");
        selval[i] = 0;
    }
    for (jj =  0,i =  3; i < argc && jj < 3 ; i =  i+3, jj++) {
      if (i +2 >= argc) {
	printf("Error in number of arguments expected\n");
	return(-1);
      }
      if (!strcmp(argv[i+1],"like") || !strcmp(argv[i+1],"LIKE") ) {
	make_like_for_mdas(argv[i+2]);
#ifdef MCAT_VERSION_10
	strcat (argv[i+2], " %%' ESCAPE '\\");
#else
	strcat (argv[i+2], "' ESCAPE '\\");
#endif
      }
      if (jj == 0) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_RSRC0]," like  '%s  %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_RSRC0]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_RSRC0]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_RSRC1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 1) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_RSRC0_1]," like  '%s  %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_RSRC0_1]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_RSRC0_1]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_RSRC1_1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 2) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_RSRC0_2]," like  '%s  %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_RSRC0_2]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_RSRC0_2]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_RSRC1_2]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 3) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_RSRC0_3]," like  '%s  %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_RSRC0_3]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_RSRC0_3]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_RSRC1_3]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
    }
    selval[RSRC_NAME] = 1;
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    if (status < 0)     {
	if (status == MCAT_INQUIRE_ERROR)
	  printf("No Answer found for the Query\n");
	return(1);
    }
    else {
      show_results(conn, qval, selval, &myresult, DEFAULT_FIELD_WIDTH,
		   DEFAULT_ROW_COUNT);
    }
    return(0);

}


int
doMetaQueryForUser(srbConn *conn,int argc, char **inargv)
{


    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    int i, jj;
    int status;
    char argv[SMALL_TOKEN][MAX_TOKEN];

    for (i = 0; i < argc; i++)
      strcpy(argv[i], inargv[i]);

    for (i = 0; i < MAX_DCS_NUM; i++) {
        sprintf(qval[i],"");
        selval[i] = 0;
    }
    for (jj =  0,i =  3; i < argc && jj < 3 ; i =  i+3, jj++) {
      if (i +2 >= argc) {
	printf("Error in number of arguments expected\n");
	return(-1);
      }
      if (!strcmp(argv[i+1],"like") || !strcmp(argv[i+1],"LIKE") ) {
	make_like_for_mdas(argv[i+2]);
#ifdef MCAT_VERSION_10
	strcat (argv[i+2], " %%' ESCAPE '\\");
#else
	strcat (argv[i+2], "' ESCAPE '\\");
#endif
      }
      if (jj == 0) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_USER0]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_USER0]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_USER0]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_USER1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 1) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_USER0_1]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_USER0_1]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_USER0_1]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_USER1_1]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 2) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_USER0_2]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_USER0_2]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_USER0_2]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_USER1_2]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
      else if (jj == 3) {
	if (make_like_for_mdas(argv[i]) == 1)
#ifdef MCAT_VERSION_10
	  sprintf(qval[UDSMD_USER0_3]," like  '%s %%' ESCAPE '\\'",argv[i]); 
#else
	  sprintf(qval[UDSMD_USER0_3]," like  '%s' ESCAPE '\\'",argv[i]); 
#endif
	else
	  sprintf(qval[UDSMD_USER0_3]," = '%s'",argv[i]); 
	if (strlen(argv[i+2]) > 0) 
	  sprintf(qval[UDSMD_USER1_3]," %s '%s'", 
		    argv[i+1],argv[i+2]); 
      }
    }
    selval[USER_NAME] = 1;
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    if (status < 0)     {
	if (status == MCAT_INQUIRE_ERROR)
	  printf("No Answer found for the Query\n");
	return(1);
    }
    else {
      show_results(conn, qval, selval, &myresult, DEFAULT_FIELD_WIDTH,
		   DEFAULT_ROW_COUNT);
    }
    return(0);

}



int
getMetaForRsrc(srbConn *conn, char *objName)
{


    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    char *attrName;
    char *attrValue;
    char *attrUnit;
    char *metaNum;
    int status;

    for (i = 0; i < MAX_DCS_NUM; i++) {
      sprintf(qval[i],"");
      selval[i] = 0;
    }

    selval[METADATA_NUM_RSRC] = 1;
    selval[UDSMD_RSRC0] = 1;
    selval[UDSMD_RSRC1] = 1;
    selval[UDSMD_RSRC2] = 1;
    sprintf(qval[RSRC_NAME]," =  '%s'",objName);


    
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    while(status == 0) {
     if (status == 0) {
      metaNum =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[METADATA_NUM_RSRC], 
	      dcs_aname[METADATA_NUM_RSRC]);
      attrName = (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD_RSRC0], dcs_aname[UDSMD_RSRC0]);
      attrValue =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD_RSRC1], dcs_aname[UDSMD_RSRC1]);
      attrUnit =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD_RSRC2], dcs_aname[UDSMD_RSRC2]);
      while ( j < myresult.row_count) {
       printf("%s %s = %s %s\n",metaNum, attrName, attrValue, attrUnit);
       attrName += MAX_DATA_SIZE;
       attrValue += MAX_DATA_SIZE;
       attrUnit += MAX_DATA_SIZE;
       metaNum += MAX_DATA_SIZE;
       j++;
      }
     }
if (myresult.continuation_index >= 0) {
      free_result_struct(selval, &myresult);
      status = srbGetMoreRows(conn, MDAS_CATALOG,myresult.continuation_index,
			      &myresult,DEFAULT_ROW_COUNT);
     }
     else {
       status = -1;
     }
    }
    free_result_struct(selval, &myresult);
      return(0);
}


int
getMetaForUser(srbConn *conn, char *objName)
{

    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    char targColl[MAX_TOKEN], targObj[MAX_TOKEN];
    char *attrName;
    char *attrValue;
    char *attrUnit;
    char *metaNum;
    int status;

    for (i = 0; i < MAX_DCS_NUM; i++) {
      sprintf(qval[i],"");
      selval[i] = 0;
    }
    splitbychar(objName,targColl,targObj, '@');
    selval[METADATA_NUM_USER] = 1;
    selval[UDSMD_USER0] = 1;
    selval[UDSMD_USER1] = 1;
    selval[UDSMD_USER2] = 1;
    sprintf(qval[USER_NAME]," =  '%s'",targColl); 
    sprintf(qval[DOMAIN_DESC]," = '%s'",targObj);

    
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    while(status == 0) {
     if (status == 0) {
      metaNum =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[METADATA_NUM_USER], 
	      dcs_aname[METADATA_NUM_USER]);
      attrName = (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD_USER0], dcs_aname[UDSMD_USER0]);
      attrValue =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD_USER1], dcs_aname[UDSMD_USER1]);
      attrUnit = (char *) getFromResultStruct(
             &myresult,dcs_tname[UDSMD_USER2], dcs_aname[UDSMD_USER2]);
      while ( j < myresult.row_count) {
       printf("%s %s = %s %s\n",metaNum, attrName, attrValue, attrUnit);
       attrName += MAX_DATA_SIZE;
       attrValue += MAX_DATA_SIZE;
       attrUnit += MAX_DATA_SIZE;
       metaNum += MAX_DATA_SIZE;
       j++;
      }
     
     }
if (myresult.continuation_index >= 0) {
      free_result_struct(selval, &myresult);
      status = srbGetMoreRows(conn, MDAS_CATALOG,myresult.continuation_index,
			      &myresult,DEFAULT_ROW_COUNT);
     }
     else {
       status = -1;
     }
    }
    free_result_struct(selval,&myresult);
      return(0);
}

int
getMetaForObj(srbConn *conn, char *objName)
{


    mdasC_sql_result_struct myresult;
    char qval[MAX_DCS_NUM][MAX_TOKEN];
    int  selval[MAX_DCS_NUM];
    char targColl[MAX_TOKEN], targObj[MAX_TOKEN];
    char *attrName;
    char *attrValue;
    char *attrUnit;
    char *metaNum;
    char temp[MAX_TOKEN];
    int status;

    for (i = 0; i < MAX_DCS_NUM; i++) {
      sprintf(qval[i],"");
      selval[i] = 0;
    }
    splitpath(objName,targColl,targObj);
    selval[METADATA_NUM] = 1;
    selval[UDSMD0] = 1;
    selval[UDSMD1] = 1;
    selval[UDSMD2] = 1;
    if (make_like_for_mdas(targColl) == 1)
#ifdef MCAT_VERSION_10
      sprintf(qval[DATA_GRP_NAME]," like  '%s %%' ESCAPE '\\'",targColl); 
#else
      sprintf(qval[DATA_GRP_NAME]," like  '%s' ESCAPE '\\'",targColl); 
#endif
    else
      sprintf(qval[DATA_GRP_NAME]," = '%s'",targColl);
    if (make_like_for_mdas(targObj) == 1)
#ifdef MCAT_VERSION_10
      sprintf(qval[DATA_NAME]," like  '%s %%' ESCAPE '\\'",targObj); 
#else
      sprintf(qval[DATA_NAME]," like  '%s' ESCAPE '\\'",targObj); 
#endif
    else
      sprintf(qval[DATA_NAME]," = '%s'",targObj);
    
    DEBUG("qval[DATA_GRP_NAME]=%s, qval[DATA_NAME]=%s\n",qval[DATA_GRP_NAME],qval[DATA_NAME]);
    
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
			  
			       
				metaNum =  (char *) getFromResultStruct(
	      			&myresult,dcs_tname[METADATA_NUM], dcs_aname[METADATA_NUM]);
			  attrName = (char *) getFromResultStruct(
				      &myresult,dcs_tname[UDSMD0], dcs_aname[UDSMD0]);
			  attrValue =  (char *) getFromResultStruct(
				      &myresult,dcs_tname[UDSMD1], dcs_aname[UDSMD1]);
				attrUnit = (char *) getFromResultStruct(
             &myresult,dcs_tname[UDSMD2], dcs_aname[UDSMD2]);
				printf("%s %s = %s \n",metaNum, attrName, attrValue);
				j=0;
				while ( j < myresult.row_count) {
			       printf("%s %s = %s \n",metaNum, attrName, attrValue);
			       attrName += MAX_DATA_SIZE;
			       attrValue += MAX_DATA_SIZE;
			       metaNum += MAX_DATA_SIZE;
			       j++;
			      }      
				      
				exit(0);	       
				
			       
    while(status == 0) {
     if (status == 0) {
      j =  0;
      metaNum =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[METADATA_NUM], dcs_aname[METADATA_NUM]);
      attrName = (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD0], dcs_aname[UDSMD0]);
      attrValue =  (char *) getFromResultStruct(
	      &myresult,dcs_tname[UDSMD1], dcs_aname[UDSMD1]);
      attrUnit = (char *) getFromResultStruct(
             &myresult,dcs_tname[UDSMD2], dcs_aname[UDSMD2]);
      while ( j < myresult.row_count) {
       printf("%s %s = %s %s\n",metaNum, attrName, attrValue, attrUnit);
       attrName += MAX_DATA_SIZE;
       attrValue += MAX_DATA_SIZE;
       attrUnit += MAX_DATA_SIZE;
       metaNum += MAX_DATA_SIZE;
       j++;
      }
     
     }
     if (myresult.continuation_index >= 0) {
      free_result_struct(selval, &myresult);
      status = srbGetMoreRows(conn, MDAS_CATALOG,myresult.continuation_index,
			      &myresult,DEFAULT_ROW_COUNT);
     }
     else {
       status = -1;
     }
    }
    free_result_struct(selval, &myresult);
    for (i = 0; i < MAX_DCS_NUM; i++) {
      sprintf(qval[i],"");
      selval[i] = 0;
    }
    j = 0;
    sprintf(temp,"%s/uuu",objName);
    splitpath(temp,targColl,targObj);
    selval[METADATA_NUM_COLL] = 1;
    selval[UDSMD_COLL0] = 1;
    selval[UDSMD_COLL1] = 1;
    selval[UDSMD_COLL2] = 1;
    if (make_like_for_mdas(targColl) == 1)
#ifdef MCAT_VERSION_10
      sprintf(qval[DATA_GRP_NAME]," like  '%s %%' ESCAPE '\\'",targColl); 
#else
      sprintf(qval[DATA_GRP_NAME]," like  '%s' ESCAPE '\\'",targColl); 
#endif
    else
      sprintf(qval[DATA_GRP_NAME]," = '%s'",targColl);
    status = srbGetDataDirInfo(conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
    while(status == 0) {
     if (status == 0) {
      metaNum =  (char *) getFromResultStruct(
	 &myresult,dcs_tname[METADATA_NUM_COLL], dcs_aname[METADATA_NUM_COLL]);
      attrName = 	 (char *) getFromResultStruct(
	 &myresult,dcs_tname[UDSMD_COLL0], dcs_aname[UDSMD_COLL0]);
      attrValue =  (char *) getFromResultStruct(
         &myresult,dcs_tname[UDSMD_COLL1], dcs_aname[UDSMD_COLL1]);
      attrUnit = 	 (char *) getFromResultStruct(
         &myresult,dcs_tname[UDSMD_COLL2], dcs_aname[UDSMD_COLL2]);
      while ( j < myresult.row_count) {
	printf("%s %s = %s %s\n", metaNum, attrName, attrValue, attrUnit);
	attrName += MAX_DATA_SIZE;
	attrValue += MAX_DATA_SIZE;
	attrUnit += MAX_DATA_SIZE;
	metaNum += MAX_DATA_SIZE;
	j++;
      }
     }
     if (myresult.continuation_index >= 0) {
      free_result_struct(selval, &myresult);
      status = srbGetMoreRows(conn, MDAS_CATALOG,myresult.continuation_index,
			      &myresult,DEFAULT_ROW_COUNT);
     }
     else {
       status = -1;
     }
    }
    free_result_struct(selval, &myresult);
    return(0);
 
}

int
bulkLoadMetaDataClient(srbConn *conn,
		       int c_value,
		       int r_value,
		       int u_value,
		       int D_value,
		       char *metaFile,
		       char *separator,
		       char *trgName)
{

 int i;
 FILE *fd;
 char *buf;
 struct stat statbuf;
 char targColl[MAX_TOKEN], targObj[MAX_TOKEN], tempObj[MAX_TOKEN];

#ifdef _WIN32
 if (stat_file(metaFile, &statbuf) != 0)
#else
   if (stat(metaFile, &statbuf) != 0)
#endif
     {
       fprintf(stderr, "unable to stat metadata file %s\n",
	      metaFile);
       return (-1);
     }
    fd = fopen(metaFile,"r");
    if (fd == NULL) {
      fprintf(stderr, "can't open metadata file %s, errno = %d\n",
	      metaFile,errno);
      return(-1);
    }
    buf = malloc( statbuf.st_size + 20);
    i = fread(buf,1,statbuf.st_size+19, fd);
    fclose(fd);
    if (i <= 0) {
      fprintf(stderr, "error reading metadata file %s = %i\n", metaFile,i);
      return(-1);
    }

    buf[i] = '\0';
    buf[i+1] = '\0';


    if (u_value == 1) {
      i = srbModifyUser(conn, MDAS_CATALOG,
			buf,trgName, /* trgName gets the separator */
			U_BULK_INSERT_UDEF_META_DATA_FOR_USER);
      return(i);
    }
    else if (r_value == 1) {
      i = srbModifyRescInfo(conn, MDAS_CATALOG,trgName,
			    R_BULK_INSERT_UDEF_META_DATA_FOR_RSRC,
			    buf,separator,"","");
      return(i);
    }
    else if (c_value == 1) {
      sprintf(tempObj,"%s/aaaa",trgName);
      splitpath(tempObj,targColl,targObj);
      i = srbModifyCollect(conn, MDAS_CATALOG,targColl,
                           buf,separator,"",
                           C_BULK_INSERT_UDEF_META_DATA_FOR_COLL);
      return(i);
    }
    else if (D_value == 1) {
      
      i = srbModifyDataset(conn, MDAS_CATALOG, "","", "","",
		      buf,trgName, /* trgName gets the separator */
		      D_BULK_INSERT_UDEF_META_DATA_FOR_MANY_DATA);
      return(i);
    }
    else {
      splitpath(trgName,targColl,targObj);
      i = srbModifyDataset(conn, MDAS_CATALOG, targObj,targColl, "","",
                             buf,separator,
                             D_BULK_INSERT_UDEF_META_DATA_FOR_DATA);
      
      return(i);
    }
    
}

int
extractMetaDataUsingStyleSheet(srbConn *conn,int argc, char **argv)
{
  int status;
  char targColl[MAX_TOKEN], targObj[MAX_TOKEN];
  char metaColl[MAX_TOKEN], metaObj[MAX_TOKEN];
  char stylColl[MAX_TOKEN], stylObj[MAX_TOKEN];
  char execString[MAX_TOKEN *8];
  char buf[MAX_TOKEN];

  if (argc != 4 && argc != 5 ) {
    usage(argv[0]);
    return -100;
  }
  
  if (argc == 4) {
    splitpath(argv[3],targColl,targObj);
    splitpath(argv[2],stylColl,stylObj);
    sprintf(execString,"%s/%s|%s/%s",stylColl,stylObj,targColl,targObj);
  }
  else {
    splitpath(argv[4],targColl,targObj);
    splitpath(argv[3],stylColl,stylObj);
    splitpath(argv[2],metaColl,metaObj);
    sprintf(execString,"%s/%s|%s/%s|%s/%s",stylColl,stylObj,targColl,targObj,
	    metaColl,metaObj);
  }
    status = srbExecFunction (conn, "extractMetadata", execString, NULL,
                            PORTAL_STD_IN_OUT);
  if (status < 0) {
    printf("Error in srbExecFunction: %i\n",status);
    while ((status = read (status, buf, sizeof (buf) -1 )) > 0) {
      buf[status] = '\0';
      printf ("%s", buf);
    }
    return(-200);
  }
  return(0);
}

int
doMetaCopy(srbConn *conn,int C_value, int argc, char **argv)
{
  int i;
  char trgColl[MAX_TOKEN], trgObj[MAX_TOKEN];
  char srcColl[MAX_TOKEN], srcObj[MAX_TOKEN];
  char tempColl[MAX_TOKEN];

  if (C_value == 1) { /*sourceCollectionName targetDataName */
    sprintf(tempColl,"%s/temp", argv[3]);
    splitpath(tempColl, srcColl, srcObj);
    splitpath(argv[4], trgColl, trgObj);
    strcpy(srcObj,"");
    i = srbModifyDataset(conn, MDAS_CATALOG, 
			 trgObj, trgColl,
			 "","", srcColl,srcObj,
			 D_COPY_META_DATA_FROM_COLL_TO_DATA);
    
  }
  else if (C_value == 2) { /* sourceCollectionName targetCollectionName */
    sprintf(tempColl,"%s/temp", argv[3]);
    splitpath(tempColl, srcColl, srcObj);
    sprintf(tempColl,"%s/temp", argv[4]);
    splitpath(tempColl, trgColl, trgObj);
    strcpy(srcObj,"");
    strcpy(trgObj,"");
    i = srbModifyCollect(conn, MDAS_CATALOG, 
			 trgColl,
			 srcColl,srcObj,"",
			 C_COPY_META_DATA_FROM_COLL_TO_COLL);
  }
  else if (C_value == 3) { /* sourceDataName targetDataName */
    splitpath(argv[3], srcColl, srcObj);
    splitpath(argv[4], trgColl, trgObj);
    i = srbModifyDataset(conn, MDAS_CATALOG, 
			 trgObj, trgColl,
			 "","", srcColl,srcObj,
			 D_COPY_META_DATA_FROM_DATA_TO_DATA);
  }
  else if (C_value == 4) { /* sourceDataName targetCollectionName */
    splitpath(argv[3], srcColl, srcObj);
    sprintf(tempColl,"%s/temp", argv[4]);
    splitpath(tempColl, trgColl, trgObj);
    strcpy(trgObj,"");
    i = srbModifyCollect(conn, MDAS_CATALOG, 
			   trgColl,
			   srcColl,srcObj,"",
			     C_COPY_META_DATA_FROM_DATA_TO_COLL);
  }
  else {
    usage (argv[0]);
    i = -100;
  }
  return(i);
}
