#include "SRB_synch_orbregistries.h"

char inStr[HUGE_STRING], smallbuf[HUGE_STRING];
int Dorebuild=0, Dotest=0, Num_testcase=0;

int reigisterOrbsFromDS(srbConn *srb_conn,  int srb_obj_fd, char * dbPtr_str, 
  char *srb_collection_registered_orbs, char *srb_orb_rsrc, char *owner)
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
        if (findSourceInSRB(srb_conn, srb_collection_registered_orbs, &src_new, &src_old))
        {
          if (isSourceUpdateNeeded(&src_old, &src_new))
          {
            unRegisterSource(srb_conn,srb_collection_registered_orbs,&src_old);
            registerSource(srb_conn, srb_orb_rsrc, srb_collection_registered_orbs, &src_new);
          }
          else
          {
            /* item alreay exists and no update needed, leave it alone! */
          }
        }
        else
        {
          /* register new item */
          registerSource(srb_conn, srb_orb_rsrc, srb_collection_registered_orbs, &src_new);
        } 
      }
      
    }
    return num_row;
}

void parseOwnerNameFromRegistryName(char registry_name[MAX_DATA_SIZE], 
  char owner_name[MAX_DATA_SIZE])
{
  char *temp;
  memset(owner_name,0,sizeof(owner_name));
  temp=strstr(registry_name,"_orbregistry");
  if (NULL==temp)
  {
    strncpy(owner_name,registry_name,sizeof(owner_name));
    owner_name[sizeof(owner_name)-1]=0;
  }
  else
  {
    strncpy(owner_name,registry_name,temp-registry_name);
    owner_name[temp-registry_name]=0;
  }
}   

int reigisterAllOrbs(srbConn *srb_conn, char *registry_db_coll, 
  char *srb_collection_registered_orbs, char *srb_orb_rsrc)
{
  int i, num_registry, srb_obj_fd, status, num_examed;
  size_t cpy_len;
  char *registry_names=NULL, registry_name[MAX_DATA_SIZE], owner_name[MAX_DATA_SIZE];
  char dbprtstr[MAX_DBPTR_STRLEN]={0};
  time_t t1,t2;
  
  registry_names=getDataNamesInColl(srb_conn,registry_db_coll,&num_registry);
  
  for(i=0;i<num_registry;i++)
  {
    strncpy(registry_name,registry_names+(i*MAX_DATA_SIZE),MAX_DATA_SIZE);
    registry_name[MAX_DATA_SIZE-1]=0;
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
    strncpy(dbprtstr,smallbuf,sizeof(dbprtstr));
    dbprtstr[sizeof(dbprtstr)-1]=0;
    memset(smallbuf, 0, sizeof(smallbuf));
    setDBTable(dbprtstr, -501);
    
    (void)time(&t1);
    num_examed=reigisterOrbsFromDS(srb_conn,  srb_obj_fd, dbprtstr,
      srb_collection_registered_orbs, srb_orb_rsrc, owner_name);
    (void)time(&t2);
    printf("%s: %d orb sources examed and attempted to register/synch in %d second(s) \n",
      registry_name, num_examed, (int)t2-t1);
    
    srbObjClose (srb_conn,srb_obj_fd);
    
  }
  
  FREEIF(registry_names);
  return 0;

}    

/* function: parseConfigFileLine 
 *
 * Parse a line of Config File, into UserConfigParam struct, 
 * which stores all user config parameters
 *
 * Input   - line: a line of config file
 *         - prefix: the prefix of the parameter
 *                   for example: "SRB_HOST mercali.ucsd.edu"
 *         
 * Output  NONE.
 *
 */
void 
parseConfigFileLine(char *_line, UserConfigParam *param)
{
  int i;
  char *line, *temp, *temp_val;
  
  line=strtrim(_line);
  
  if ((strlen(line)<=1)||('#'==line[0]))
    return;
  
  if (0==strncmp("SRB_HOST",line,strlen("SRB_HOST")))
  {
    temp=line+strlen("SRB_HOST");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_host,temp_val,sizeof(param->srb_host));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_PORT",line,strlen("SRB_PORT")))
  {
    temp=line+strlen("SRB_PORT");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_port,temp_val,sizeof(param->srb_port));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_PASSWORD",line,strlen("SRB_PASSWORD")))
  {
    temp=line+strlen("SRB_PASSWORD");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_password,temp_val,sizeof(param->srb_password));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_USERNAME",line,strlen("SRB_USERNAME")))
  {
    temp=line+strlen("SRB_USERNAME");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_username,temp_val,sizeof(param->srb_username));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_DOMAIN",line,strlen("SRB_DOMAIN")))
  {
    temp=line+strlen("SRB_DOMAIN");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_domain,temp_val,sizeof(param->srb_domain));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_ZONE",line,strlen("SRB_ZONE")))
  {
    temp=line+strlen("SRB_ZONE");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_zone,temp_val,sizeof(param->srb_zone));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_COLLECTION_REGISTRIES",line,strlen("SRB_COLLECTION_REGISTRIES")))
  {
    temp=line+strlen("SRB_COLLECTION_REGISTRIES");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_collection_registries,temp_val,sizeof(param->srb_collection_registries));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_COLLECTION_REGISTERED_ORBS",line,strlen("SRB_COLLECTION_REGISTERED_ORBS")))
  {
    temp=line+strlen("SRB_COLLECTION_REGISTERED_ORBS");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_collection_registered_orbs,temp_val,sizeof(param->srb_collection_registered_orbs));
    FREEIF(temp_val);
  }
  
  else
  if (0==strncmp("SRB_ORB_RSRC",line,strlen("SRB_ORB_RSRC")))
  {
    temp=line+strlen("SRB_ORB_RSRC");
    temp_val=strtrim(temp);
    STRNCPY(param->srb_orb_rsrc,temp_val,sizeof(param->srb_orb_rsrc));
    FREEIF(temp_val);
  }
  
  FREEIF(line);
}
  
  

/* function: parseConfigFile 
 *
 * Parse Config File, into UserConfigParam struct, 
 * which stores all user config parameters
 *
 * Input   - filename: config file name
 *         
 * Output  NONE.
 *
 */
void
parseConfigFile(char *filename, UserConfigParam *param)
{
  FILE *fp;
  char *templine, *temp, *temp_val;
  
  if ((fp = fopen(filename, "r")) == NULL)
  {  
    fprintf(stderr, "Can't open %s! Please check the path and permission of this file \n", 
      filename);
    exit(1);
  }
  
  memset(param,0,sizeof(*param));
  
  while (!feof(fp))
  {
    fgets(smallbuf, sizeof(smallbuf), fp);
    parseConfigFileLine(smallbuf, param);
  }
  
  printf("param->srb_host=%s, param->srb_port=%s\n",param->srb_host, param->srb_port);
  
  if (strlen(param->srb_host)<=0)
  {
    DIE("srb_host not set in config file: %s!",filename);
  }
  if (strlen(param->srb_port)<=0)
  {
    DIE("srb_port not set in config file: %s!",filename);
  }
  if (strlen(param->srb_password)<=0)
  {
    DIE("srb_password not set in config file: %s!",filename);
  }
  if (strlen(param->srb_username)<=0)
  {
    DIE("srb_username not set in config file: %s!",filename);
  }
  if (strlen(param->srb_domain)<=0)
  {
    DIE("srb_domain not set in config file: %s!",filename);
  }
  if (strlen(param->srb_zone)<=0)
  {
    DIE("srb_zone not set in config file: %s!",filename);
  }
  if (strlen(param->srb_collection_registries)<=0)
  {
    DIE("srb_collection_registries not set in config file: %s!",filename);
  }
  if (strlen(param->srb_collection_registered_orbs)<=0)
  {
    DIE("srb_collection_registered_orbs not set in config file: %s!",filename);
  }
  if (strlen(param->srb_orb_rsrc)<=0)
  {
    DIE("srb_orb_rsrc not set in config file: %s!",filename);
  }
}

void
usage (char *prog)
{
  fprintf(stderr,"Usage  :%s [-hr] [-f config file] [-t num_testcase] \n", prog);
} 

int main(int argc, char * argv[])
{
    srbConn *srb_conn;
    Source temp;
    
    int i, c, srb_obj_fd, nbytes, status;
    char dbprtstr[MAX_DBPTR_STRLEN]={0}, conf_filename[HUGE_STRING]={0};
    UserConfigParam userConfigParam;
    
    while ((c=getopt(argc, argv,"f:hrt:")) != EOF) 
    {
      switch (c) 
      {
        case 'h':
          usage (argv[0]);
          exit (0);
        case 'f':
          STRNCPY(conf_filename,optarg,sizeof(conf_filename));
          break;
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
    
    if (strlen(conf_filename)<=1)
      strcpy(conf_filename,DEFAULT_CONFIG_FILE);
    parseConfigFile(conf_filename,&userConfigParam);
    
    /* connect to srb server */
    srb_conn = srbConnect (userConfigParam.srb_host, userConfigParam.srb_port, 
      userConfigParam.srb_password, userConfigParam.srb_username, 
      userConfigParam.srb_domain, NULL, NULL);
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
      unregisterAllSources(srb_conn, userConfigParam.srb_collection_registered_orbs);
      fprintf(stderr, "Done! \n");
    } 
    
    
    reigisterAllOrbs(srb_conn, userConfigParam.srb_collection_registries, 
      userConfigParam.srb_collection_registered_orbs, userConfigParam.srb_orb_rsrc);
    
    clFinish (srb_conn);
    
    printf("End of Program!\n");
    return(0); 
}

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/SRB_synch_orbregistries.c,v $
 * $Revision: 1.1 $
 * $Author: sifang $
 * $Date: 2005/01/11 03:38:10 $
 *
 * $Log: SRB_synch_orbregistries.c,v $
 * Revision 1.1  2005/01/11 03:38:10  sifang
 *
 * rewrote SRB style makefile to Antelope style makefile. Also changed its position from Vorb/ext/srb/utilities to here.
 *
 * Revision 1.3  2005/01/08 04:10:56  sifang
 *
 * Add a config file feature, "-r", into the program. So the user could not load his/her own costumized config file with ease. Also added a sample config file with instructions.
 *
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */
