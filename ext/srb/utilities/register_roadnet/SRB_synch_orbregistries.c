#include "SRB_synch_orbregistries.h"

char inStr[HUGE_STRING], smallbuf[HUGE_STRING];
int Dorebuild=0, Dotest=0, Num_testcase=0;

int reigisterOrbsFromDS(srbConn *srb_conn,  int srb_obj_fd, char * dbPtr_str, char *owner)
{
    int i, num_row, status; 
    char dbprtstr_src_svr[MAX_DBPTR_STRLEN]={0};
    Source src_new, src_old;
    
    dbJoinTable(srb_conn,srb_obj_fd,dbPtr_str,dbprtstr_src_svr,sizeof(dbprtstr_src_svr));
    
    num_row=getRowCount(srb_conn,srb_obj_fd,dbprtstr_src_svr,sizeof(dbprtstr_src_svr));
    
    /* need to add this feature when Kent help me resolving the dbaddv() problem */
    /* dbAddvSourceToDS(srb_conn,srb_obj_fd,dbPtr_str); */
    
    /* if do test, then reset the number of row up to the number user specified */
    if (Dotest)
    {
    	num_row=((num_row >= Num_testcase)  ? Num_testcase : num_row); 
    }
    
    for(i=0;i<num_row;i++)
    {
      setDBRecord(dbprtstr_src_svr,i);
      
      parseSRBDSStringToSource(srb_conn,srb_obj_fd,dbprtstr_src_svr,owner,&src_new);
      
      if (isIpAddrRoutable(src_new.serveraddress))
      {
        if (findSourceInSRB(srb_conn, SRB_COLLECTION_REGISTERED_ORBS, &src_new, &src_old))
	      {
	      	if (isSourceUpdateNeeded(&src_old, &src_new))
	      	{
	      		unRegisterSource(srb_conn,SRB_COLLECTION_REGISTERED_ORBS,&src_old);
	      		registerSource(srb_conn, SRB_RSRC_MERCALI_ORB, SRB_COLLECTION_REGISTERED_ORBS, &src_new);
	        }
	        else
	        {
	        	/* item alreay exists and no update needed, leave it alone! */
	        }
	      }
	      else
	      {
	      	/* register new item */
	      	registerSource(srb_conn, SRB_RSRC_MERCALI_ORB, SRB_COLLECTION_REGISTERED_ORBS, &src_new);
	      }	
      }
      
    }
    return num_row;
}

void parseOwnerNameFromRegistryName(char registry_name[MAX_DATA_SIZE], char owner_name[MAX_DATA_SIZE])
{
	char *temp;
	memset(owner_name,0,sizeof(owner_name));
	temp=strstr(registry_name,"_orbregistry");
	if (NULL==temp)
		strncpy(owner_name,registry_name,sizeof(owner_name));
	else
		strncpy(owner_name,registry_name,temp-registry_name);
}		

int reigisterAllOrbs(srbConn *srb_conn, char *registry_db_coll)
{
	int i, num_registry, srb_obj_fd, status, num_examed;
	char *registry_names=NULL, registry_name[MAX_DATA_SIZE], owner_name[MAX_DATA_SIZE];
	char dbprtstr[MAX_DBPTR_STRLEN]={0};
	time_t t1,t2;
	
	registry_names=getDataNamesInColl(srb_conn,registry_db_coll,&num_registry);
	
	for(i=0;i<num_registry;i++)
	{
		strncpy(registry_name,registry_names+(i*MAX_DATA_SIZE),MAX_DATA_SIZE);
		parseOwnerNameFromRegistryName(registry_name, owner_name);
		
		/* open srb object, which is a query in datascope in current case */
		srb_obj_fd = srbObjOpen (srb_conn, registry_name,  O_RDONLY, registry_db_coll);
    if (srb_obj_fd < 0)  {   /* error */
        DEBUG("Cannot Open Object. srb_obj_fd=%d\n", srb_obj_fd);
        DEBUG("srb_obj_fd: %s",clErrorMessage((void *)srb_obj_fd));
        srb_perror (2, srb_obj_fd, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
        clFinish(srb_conn);
        continue;
    }
    
		/* get default dbptr by open table sources 1st, */
    /* then set the table to be null (-501),        */
    /* so dbptr points to the database instead of any table */
    sprintf(inStr,"dbopen_table|sources|r");
    status = srbObjProc(srb_conn,srb_obj_fd,inStr,"",0,smallbuf,sizeof(smallbuf));
    if (status<0)
    {
      DEBUG("srbObjProc failed. Maybe table 'source' doesn't exist in registry %s ?!!"
      	,registry_name);
      srbObjClose (srb_conn,srb_obj_fd);
      continue;
    }
    strncpy(dbprtstr,smallbuf,sizeof(dbprtstr)-1);
    memset(smallbuf, 0, sizeof(smallbuf));
    setDBTable(dbprtstr, -501);
    
    (void)time(&t1);
    num_examed=reigisterOrbsFromDS(srb_conn,  srb_obj_fd, dbprtstr, owner_name);
    (void)time(&t2);
    printf("%s: %d orb sources examed and attempted to register/synch in %d second(s) \n",
    	registry_name, num_examed, (int)t2-t1);
    
    srbObjClose (srb_conn,srb_obj_fd);
    
	}
	
	FREEIF(registry_names);
	return 0;

}    

void
usage (char *prog)
{
	fprintf(stderr,"Usage  :%s [-hr] [-t num_testcase] \n", prog);
}	

int main(int argc, char * argv[])
{
    srbConn *srb_conn;
    Source temp;
    
    int i, c, srb_obj_fd, nbytes, status;
    char dbprtstr[MAX_DBPTR_STRLEN]={0};
    
    while ((c=getopt(argc, argv,"hrt:")) != EOF) 
    {
    	switch (c) 
    	{
    		case 'h':
					usage (argv[0]);
          exit (0);
        case 'r':
          Dorebuild = 1;
          break;  
    		case 't':
    			Dotest = 1;
    			Num_testcase=atoi(optarg);
    			break;
    		default:
          usage (argv[0]);
          exit (1);
      }	
    }
    /* connect to srb server */
    srb_conn = srbConnect (SRB_HOST, SRB_PORT, SRB_PASSWORD, SRB_USERNAME, 
      SRB_DOMAIN, NULL, NULL);
    if (clStatus(srb_conn) != CLI_CONNECTION_OK) {
        DEBUG("Connection to srbMaster failed.\n");
        DEBUG("%s",clErrorMessage(srb_conn));
        srb_perror (2, clStatus(srb_conn), "", SRB_RCMD_ACTION|SRB_LONG_MSG);
        clFinish (srb_conn);
        exit (-1);
    }
    
    /* if do rebuild, then unregister all registered orbs 1st */
    if (Dorebuild)	
    {
    	fprintf(stderr, "Unregistering all registered orbs (SRB objects) ... ");
    	unregisterAllSources(srb_conn, SRB_COLLECTION_REGISTERED_ORBS);
    	fprintf(stderr, "Done! \n");
    }	
    
    reigisterAllOrbs(srb_conn, SRB_COLLECTION_REGISTRIES);
    
    clFinish (srb_conn);
    
    printf("End of Program!\n");
    return(0); 
}
