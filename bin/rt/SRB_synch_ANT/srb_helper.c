#include "srb_helper.h"

char inStr[HUGE_STRING], smallbuf[HUGE_STRING];

// read more on getMetaForObj() in Sufmeta.c!!!!!
int findSourceInSRB (srbConn *srb_conn, char* srb_col, Source *src_new, Source *src_old)
{
	int status, i;
  mdasC_sql_result_struct myresult;
  char * tmp_dataname=NULL;
  
  sprintf(smallbuf,"%s/%s",srb_col, src_new->srbname);
  
  status = queryData (srb_conn, MDAS_CATALOG, smallbuf, l_FLAG, MAX_GET_RESULTS, &myresult);
  /* if status < 0, record doesn't exist! */
  if (status < 0)
  {
  	return 0;
  }
  
  tmp_dataname = (char *) getFromResultStruct(&myresult,
        dcs_tname[DATA_NAME], dcs_aname[DATA_NAME]);
  
  /* if they have same srbname, then same source */
  if (0==strncmp(src_new->srbname,tmp_dataname,sizeof(src_new->srbname)))
  {
  		makeSourceFromSRB(srb_conn,srb_col,src_new->srbname, src_old);
  		return 1;
  }
  else
  	return 0;
}    
	
	

/*
 * unregister data within myresult, need this because one collection may 
 * contain more data that one result can hold
 */
void unregisterDataWithInResult(srbConn *srb_conn, char* srb_col, 
																mdasC_sql_result_struct *myresult)
{
	int i;
	char * dataname=NULL, * tmp_dataname=NULL;
	dataname = (char *) getFromResultStruct(myresult,
        dcs_tname[DATA_NAME], dcs_aname[DATA_NAME]);
  tmp_dataname=dataname;      
  for (i = 0; i < myresult->row_count; i++) 
  {
  	unRegisterData(srb_conn, srb_col, tmp_dataname);
  	/* increment string pointer to next chunk (a row in db) */
  	tmp_dataname += MAX_DATA_SIZE;
  } 	
  
}

//read src/client/clAuth.c about more on this... also use Sls.c as reference.
void unregisterAllSources(srbConn *srb_conn, char* srb_col)
{
  int status, i;
  mdasC_sql_result_struct myresult;
  
  status = queryDataInColl (srb_conn, MDAS_CATALOG, srb_col, l_FLAG, MAX_GET_RESULTS, 
      &myresult);
  if (status<0)
    return;
  
  unregisterDataWithInResult(srb_conn, srb_col, &myresult);
  
  /* loop until no more answer */
  while (myresult.continuation_index >= 0) 
  {
        clearSqlResult (&myresult);
        /* getting next set of rows */
        status = srbGetMoreRows(srb_conn, MDAS_CATALOG,myresult.continuation_index,
          &myresult, MAX_GET_RESULTS);
        if (myresult.result_count == 0  || status != 0)
            return;
	      
	      //not sure if filter is needed for this program...
	      //filterDeleted (&myresult);
	      
	      unregisterDataWithInResult(srb_conn, srb_col, &myresult);
  }
}

char *
getDataNamesInColl (srbConn *conn, char *parColl, int *num_data_result)
{
    mdasC_sql_result_struct  myresult;
    int i, status, num_data;
    char *datanames, *tmpList;

    status = queryDataInColl (conn, MDAS_CATALOG, parColl, l_FLAG, MAX_GET_RESULTS, 
      &myresult);

    if (status < 0)
    {
    	DEBUG("Error occured when query data from \"%s\"\n",parColl);
    	exit(-1);
    }
    
    tmpList = (char *) getFromResultStruct(
      (mdasC_sql_result_struct *) &myresult,
        dcs_tname[DATA_NAME], dcs_aname[DATA_NAME]);
    num_data=myresult.row_count;
    datanames=(char *)malloc(num_data*MAX_DATA_SIZE);
    memcpy(datanames, tmpList, num_data*MAX_DATA_SIZE);
		
		/* loop until no more answer */
    while (myresult.continuation_index >= 0) {
        clearSqlResult (&myresult);
        /* getting next set of rows */
        status = srbGetMoreRows(conn, MDAS_CATALOG,myresult.continuation_index,
          &myresult, MAX_GET_RESULTS);
        if (myresult.result_count == 0  || status != 0)
            break;
        
        tmpList = (char *) getFromResultStruct(
		      (mdasC_sql_result_struct *) &myresult,
		        dcs_tname[DATA_NAME], dcs_aname[DATA_NAME]);
		    num_data=num_data+myresult.row_count;
		    datanames=(char *)realloc(datanames, num_data*MAX_DATA_SIZE);
		    memcpy(datanames+(num_data-myresult.row_count)*MAX_DATA_SIZE, 
		    	tmpList, myresult.row_count*MAX_DATA_SIZE);
    }
    clearSqlResult (&myresult);
    
    *num_data_result=num_data;
    return datanames;
}
	

void addSRBMetaData(srbConn *srb_conn, char* srb_rsrc, char* srb_col, Source *src)
{
  int which;
  char index[80]={0};
  char *srb_path=constructSRBPath(src);
  
  // add metadata for srcname
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","srcname",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".0 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->srcname,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA);
  
  // add metadata for server address
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","serveraddress",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".1 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->serveraddress,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA);
  
  // add metadata for server port
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","serverport",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".2 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->serverport,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA);
  
  // add metadata for datatype 
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","datatype",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".3 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->datatype,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA); 
                                                     
  // add metadata for orb_start (orb started date)
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","orb_start",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".4 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->orb_start,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA); 
                            
  // add metadata for regdate (srb obj registered date)
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","regdate",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".5 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->regdate,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA); 
 
  // add metadata for owner 
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            "0","owner",
                            D_INSERT_USER_DEFINED_STRING_META_DATA);
  if (which < 0)
  {
    DEBUG(".6 cannot modify metadata for SRB obj '%s':%i\n",
      src->srbname, which);
    return;
  }
  sprintf(index, "%d@%d",1,which);
  which=srbModifyDataset(srb_conn, MDAS_CATALOG, src->srbname, srb_col,
                            srb_rsrc,srb_path,
                            index,src->owner,
                            D_CHANGE_USER_DEFINED_STRING_META_DATA);                          
                            
  FREEIF(srb_path);  
}  

/*
 * make a source obj from SRB obj. src must be pre-allocated
 */ 
void makeSourceFromSRB(srbConn *srb_conn, char* srb_col, char* srb_dataname, Source *src)
{
	int status;
	int i,j;
	
	/* it's 7 here because addSRBMetaData() add 7 meta data */
	/* change it if number of metadata changed!             */
	int expected_num_meta=7; 
	
	char *attrName, *attrValue, *metaNum;
	//char srb_col[MAX_TOKEN], srb_dataname[MAX_TOKEN];
	char qval[MAX_DCS_NUM][MAX_TOKEN]={0};
  int  selval[MAX_DCS_NUM]={0};
	mdasC_sql_result_struct myresult;
	
	if (!src)
	{
		DEBUG("null not allowed.");
		exit (-1);
  }
  
  for (i = 0; i < MAX_DCS_NUM; i++) 
  {
    sprintf(qval[i],"");
    selval[i] = 0;
  }
  
  /* tell srb to select UDSMD0 (attrName) and UDSMD1 (attrValue) */
  /* please read getMetaForObj() in Sufmeta.c for more infor on how to get metadata */
  selval[METADATA_NUM] = 1;
  selval[UDSMD0] = 1;
  selval[UDSMD1] = 1;
  
  /* tell srb what collection and dataname are */
  sprintf(qval[DATA_GRP_NAME]," = '%s'",srb_col);
  sprintf(qval[DATA_NAME]," = '%s'",srb_dataname);
  status = srbGetDataDirInfo(srb_conn, 0 , qval, selval, &myresult,
			       DEFAULT_ROW_COUNT);
	
	if (expected_num_meta!=myresult.row_count)
	{
		DEBUG("row_count %d not expected %d.",myresult.row_count,expected_num_meta);
		exit (-1);
  }
  
  metaNum =  (char *) getFromResultStruct(
		&myresult,dcs_tname[METADATA_NUM], dcs_aname[METADATA_NUM]);
  attrName = (char *) getFromResultStruct(
		&myresult,dcs_tname[UDSMD0], dcs_aname[UDSMD0]);
	attrValue =  (char *) getFromResultStruct(
	  &myresult,dcs_tname[UDSMD1], dcs_aname[UDSMD1]);
	
	if (strncmp(attrName,"srcname",sizeof("srcname")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"srcname");
  	exit(-1);
  }
  setSrcname(src,attrValue);
  
  /* retrieve serveraddress */
  attrName += MAX_DATA_SIZE;
  attrValue += MAX_DATA_SIZE;
  if (strncmp(attrName,"serveraddress",sizeof("serveraddress")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"serveraddress");
  	exit(-1);
  }	
	setServeraddress(src,attrValue);	
	
	/* retrieve serverport */
	attrName += MAX_DATA_SIZE;
  attrValue += MAX_DATA_SIZE;
  if (strncmp(attrName,"serverport",sizeof("serverport")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"serverport");
  	exit(-1);
  }	
	setServerport(src,attrValue);
	
	/* retrieve datatype */
	attrName += MAX_DATA_SIZE;
  attrValue += MAX_DATA_SIZE;
  if (strncmp(attrName,"datatype",sizeof("datatype")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"datatype");
  	exit(-1);
  }	
	setDatatype(src,attrValue);
	
	/* retrieve orb_start */
	attrName += MAX_DATA_SIZE;
  attrValue += MAX_DATA_SIZE;
  if (strncmp(attrName,"orb_start",sizeof("orb_start")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"orb_start");
  	exit(-1);
  }	
	setOrbStart(src,attrValue);
	
	/* retrieve regdate */
	attrName += MAX_DATA_SIZE;
  attrValue += MAX_DATA_SIZE;
  if (strncmp(attrName,"regdate",sizeof("regdate")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"regdate");
  	exit(-1);
  }	
	setRegdate(src,attrValue);
	
	/* retrieve owner */
	attrName += MAX_DATA_SIZE;
  attrValue += MAX_DATA_SIZE;
  if (strncmp(attrName,"owner",sizeof("owner")))
  {
  	DEBUG("invalid attrName from SRB server detected:'%s', '%s' is expected",attrName,"owner");
  	exit(-1);
  }	
	setOwner(src,attrValue);
	
	/* set srbname */
	setSrbname(src, srb_dataname);
	
	free_result_struct(selval, &myresult);
}	
		       

int registerSource(srbConn *srb_conn, char* srb_rsrc, char* srb_col, Source *src)
{
  int status;
  char *srb_path=constructSRBPath(src);
  status=srbRegisterDataset (srb_conn, MDAS_CATALOG, src->srbname, 
                      "orb data", srb_rsrc, srb_col, srb_path, 0);
  if (status < 0)
  {
    fprintf(stderr,
      "Sregister: cannot register SRB obj '%s':%i\n",
      src->srbname, status);
    srb_perror (2, status, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
    exit(-1);
  }
  FREEIF(srb_path);
  
  addSRBMetaData (srb_conn, srb_rsrc, srb_col,src);                   
  return status;
}

int unRegisterSource(srbConn *srb_conn, char* srb_col, Source *src)
{
  int status;
  status=srbUnregisterDataset (srb_conn, src->srbname, srb_col);
  if (status < 0)
  {
    fprintf(stderr,
      "srbUnregisterDataset: cannot unregister SRB obj '%s':%i\n",
      src->srbname, status);
    srb_perror (2, status, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
  }
  return status;
}

int unRegisterData(srbConn *srb_conn, char* srb_col, char *dataname)
{
  int status;
  status=srbUnregisterDataset (srb_conn, dataname, srb_col);
  if (status < 0)
  {
    fprintf(stderr,
      "srbUnregisterDataset: cannot unregister SRB obj '%s':%i\n",
      dataname, status);
    srb_perror (2, status, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
  }
  return status;
}

/*
 * use dbPtr_str (must be pointing to specific row), and dbgetv, get result string
 * and parse it into a source obj.
 *
 * Input   - srb_conn: srb connection
 *         - srb_obj_fd: srb obj file pointer
 *         - dbPtr_str: dbptr pointing to the table, dbjoin'ed by sources and servers.
 *         - src: preallocated Source obj
 *         
 * Output  - OKAY: 0
 *         - ERROR: return value of dbgetv, if dbgetv fails, it will give an negative number.        
 */
int parseSRBDSStringToSource(srbConn *srb_conn,  
                int srb_obj_fd,
                char * dbPtr_str,
                char * owner,
                Source *src)
{
  char *start, *end;
  int status;
  
  char srcname[sizeof(src->srcname)];
  char serveraddress[sizeof(src->serveraddress)];
  char serverport[sizeof(src->serverport)];
  char orb_start[sizeof(src->orb_start)]; 
  
  int serverport_int;     
  double orb_start_t;
  time_t orb_start_timet;
  
  struct tm orb_start_tm;
  
  sprintf(inStr, "dbgetv||srcname|serveraddress|serverport|orb_start");
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbPtr_str,strlen(dbPtr_str)+1,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
    DEBUG(">>>> srbObjProc failed ret_val=%d\n",status);
    return status;
  }
  
  // get srcname
  start=smallbuf;
  if (NULL==(end=strstr(start, "|")))
  {
     DEBUG(">>>> returned buff contains no expected delimiter '|'. returned buff=%s\n",smallbuf);
     return -1;
  }
  if (!parseDBString(start,end, srcname, sizeof(srcname))) 
  {
     DEBUG(">>>> parseDBString failed. returned buff=%s\n",smallbuf);
     return -1;
  }
  
  // get serveraddress
  start=end+1;;
  if (NULL==(end=strstr(start, "|")))
  {
     DEBUG(">>>> returned buff contains no expected delimiter '|'. returned buff=%s\n",smallbuf);
     return -1;
  }
  if (!parseDBString(start,end, serveraddress, sizeof(serveraddress)))
  { 
     DEBUG(">>>> parseDBString failed. returned buff=%s\n",smallbuf);
     return -1;
  }
  
  
  //get serverport
  start=end+1;
  if (NULL==(end=strstr(start, "|")))
  {
     DEBUG(">>>> returned buff contains no expected delimiter '|'. returned buff=%s\n",smallbuf);
     return -1;
  }
  if (!parseDBInteger(start,end, &(serverport_int))) 
  {
    DEBUG(">>>> parseDBInteger failed. returned buff=%s\n",smallbuf);
    return -1;
  }
  snprintf(serverport, sizeof(serverport)-1,"%d",serverport_int);
  
  //get orb_start
  start=end+1;
  end=start+strlen(start);
  if (!parseDBReal(start,end, &(orb_start_t))) 
  {
    DEBUG(">>>> parseDBReal failed. returned buff=%s\n",smallbuf);
    return -1;
  }
  orb_start_timet=(const time_t)orb_start_t;
  (void)gmtime_r( &orb_start_timet, &orb_start_tm);
  strftime(orb_start, sizeof(orb_start)-1, "%Y%m%d",
    &orb_start_tm);
    
  setSourceBasic(src, srcname, serveraddress, serverport, orb_start, owner);
}

/*
 * get Row Count of input table 
 *
 * Input   - srb_conn: srb connection
 *         - srb_obj_fd: srb obj file pointer
 *         - dbPtr_str: dbptr pointing to the table.
 *         - size_dbPtr: size of dbPtr_str
 *         
 * Output  - row count. (if negative, then error occured!)          
 */
int getRowCount(srbConn *srb_conn,  
                int srb_obj_fd,
                char * dbPtr_str, 
                size_t size_dbPtr)
{
  int status, num_row;
  sprintf(inStr, "dbquery|%d",dbRECORD_COUNT);
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbPtr_str,size_dbPtr,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
    DEBUG(">>>> srbObjProc failed. ret_val=%d, dbPtr_str=%s\n",status,dbPtr_str);
    num_row=status;
  }
  else
  {
    num_row=atoi(smallbuf);
    memset(smallbuf, 0, sizeof(smallbuf));
  }
  return num_row;
}

/*
 * dbjoin table (1)sources and (2)server
 *
 * Input   - srb_conn: srb connection
 *         - srb_obj_fd: srb obj file pointer
 *         - dbptr_str: original dbptr pointing to the database.
 *         - dbprtstr_result (pre-allocated): result dbptr pointing to the transiant db.
 *         - size_result: sizeof dbprtstr_result
 *         
 * Output  - none.          
 */
void dbJoinTable( srbConn *srb_conn,  
                  int srb_obj_fd,
                  char * dbPtr_str, 
                  char *dbprtstr_result, 
                  size_t result_len)
{
  int status;
  char dbprtstr_sources[MAX_DBPTR_STRLEN]={0}, 
       dbprtstr_server[MAX_DBPTR_STRLEN]={0},
       dbprtstr_src_svr[MAX_DBPTR_STRLEN]={0};
  
  // open table sources 
  sprintf(inStr,"dbopen_table|sources|r");
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbPtr_str,strlen(dbPtr_str)+1,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
      DEBUG("srbObjProc failed.1 ret_val=%d\n",status);
      return;
  }
  strncpy(dbprtstr_sources,smallbuf,sizeof(dbprtstr_sources));
  dbprtstr_sources[sizeof(dbprtstr_sources)-1]=0;
  memset(smallbuf, 0, sizeof(smallbuf));  
  
  // open table servers
  sprintf(inStr,"dbopen_table|servers|r");
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbPtr_str,strlen(dbPtr_str)+1,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
      DEBUG("srbObjProc failed.2 ret_val=%d\n",status);
      return;
  }
  strncpy(dbprtstr_server,smallbuf,sizeof(dbprtstr_server));
  dbprtstr_server[sizeof(dbprtstr_server)-1]=0;
  memset(smallbuf, 0, sizeof(smallbuf)); 
  
  // join the two tables
  sprintf(inStr,"dbjoin|%s||serveraddress|0||",dbprtstr_server);
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbprtstr_sources,strlen(dbprtstr_sources)+1,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
      DEBUG("srbObjProc failed.3 ret_val=%d\n",status);
      return;
  }
  strncpy(dbprtstr_src_svr,smallbuf,sizeof(dbprtstr_src_svr));
  dbprtstr_src_svr[sizeof(dbprtstr_src_svr)-1]=0;
  memset(smallbuf, 0, sizeof(smallbuf)); 
  
  strncpy(dbprtstr_result, dbprtstr_src_svr, result_len);
  dbprtstr_result[result_len-1]=0;
}

/*
 * use dbaddv() to add an source to datascope
 *
 * Input   - srb_conn: srb connection
 *         - srb_obj_fd: srb obj file pointer
 *         - dbptr_str: original dbptr pointing to the database.
 *         
 * Output  - none.          
 */
void
dbAddvSourceToDS( srbConn *srb_conn,  
                  int srb_obj_fd,
                  char * dbPtr_str)
{
	int status;
  char dbprtstr_serversrb[MAX_DBPTR_STRLEN]={0};
       
  // open table sources 
  sprintf(inStr,"dbopen_table|serversrb|r+");
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbPtr_str,strlen(dbPtr_str)+1,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
      DEBUG("srbObjProc failed.1 ret_val=%d\n",status);
      return;
  }
  strncpy(dbprtstr_serversrb,smallbuf,sizeof(dbprtstr_serversrb));
  dbprtstr_serversrb[sizeof(dbprtstr_serversrb)-1]=0;
  memset(smallbuf, 0, sizeof(smallbuf));  
  printf("dbprtstr_serversrb=%s",dbprtstr_serversrb);
  
  //dbSTRING=6, dbINTEGER=2, dbTIME=4
  sprintf(inStr,"dbaddv|"
  							"|serveraddress|6|%s"
  							"|serverport|2|%d"
  							"|Szone|6|%s"
  							"|Scoll|6|%s"
  							"|Sobj|6|%s",
  							//"|lddate|4|%f",
  							"test.srv.addr",1000,"testzone","testcoll","testobj4" //,1055350912.24000
  							);
  status = srbObjProc(srb_conn,srb_obj_fd,inStr,dbprtstr_serversrb,strlen(dbprtstr_serversrb)+1,smallbuf,sizeof(smallbuf));
  if (status<0)
  {
      DEBUG("srbObjProc failed.2 ret_val=%d\n",status);
      return;
  }
  printf("smallbuf=%s",smallbuf);
  
}

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/srb_helper.c,v $
 * $Revision: 1.2 $
 * $Author: sifang $
 * $Date: 2005/05/06 03:07:39 $
 *
 * $Log: srb_helper.c,v $
 * Revision 1.2  2005/05/06 03:07:39  sifang
 *
 * fixed few memory bugs
 *
 * Revision 1.1  2005/01/11 03:38:10  sifang
 *
 * rewrote SRB style makefile to Antelope style makefile. Also changed its position from Vorb/ext/srb/utilities to here.
 *
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */
