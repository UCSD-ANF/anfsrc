#include <unistd.h>
#include <sys/types.h>
#include <limits.h>
#include "stock.h"
#include "tr.h"
#include "db.h"
#include "libuser.h"

/* inline functions */
#ifndef FREEIF
#define FREEIF(pi)		{ if (pi) { free((void *)pi); (pi)=0; }}
#endif

#ifndef STRNCPY
#define STRNCPY(dest, src, n)	{ strncpy(dest,src,n); dest[n-1]=0; }
#endif

#ifndef MALLOC_SAFE
#define MALLOC_SAFE(dest,size) { dest=malloc(size); if(NULL==dest) {fprintf(stderr,"Error: out of memory at %s:%s\n",__FILE__,__LINE__); exit(-1);} else memset(dest,0,size); }
#endif

#ifndef STRDUP_SAFE
#define STRDUP_SAFE(newstr,oldstr) { newstr=strdup(oldstr); if(NULL==newstr) {fprintf(stderr,"Error: out of memory at %s:%s\n",__FILE__,__LINE__); exit(-1);} }
#endif

#ifndef STRNDUP_SAFE
#define STRNDUP_SAFE(newstr,oldstr,size) { MALLOC_SAFE(newstr,size+sizeof(char)*2); STRNCPY(newstr, oldstr, size+sizeof(char)); }
#endif

#ifndef  DIE
#define  DIE( ... ) fprintf(stderr, "ERROR:\"%s:%u\" %s: ",__FILE__,__LINE__, "Unknown Function" ); fprintf( stderr, __VA_ARGS__ ); exit(-1);
#endif

#ifndef  WARNING
#define  WARNING( ... ) fprintf(stderr, "WARNING:\"%s:%u\" %s: ",__FILE__,__LINE__, __FUNCTION__); fprintf( stderr, __VA_ARGS__ ); 
#endif

#ifndef  DEBUG
#define  DEBUG( ... ) fprintf(stderr, "DEBUG:\"%s:%u\" %s: ",__FILE__,__LINE__, __FUNCTION__); fprintf( stderr, __VA_ARGS__ ); 
#endif

/* constants specific for this function */
#define  MAX_PROC_ARGS_FOR_DS 100
#define  MAX_DBPTR_STRLEN 100   /* max strlen of dbptr */
#define  DS_DESC_TABLE    "DS_DESC_" /* descriptor table for all datascope tables in SQL db */

typedef struct DSSchemaField
{
    char *name;
    Dbptr dsptr;
    int  type;
    char format[100];
    int  size;
}              DSSchemaField;

typedef struct DSSchemaTable
{
    char *name;
    Dbptr dsptr;
    int numrecord;
    int numfield;
    DSSchemaField *fields;
}              DSSchemaTable;

typedef struct DSSchemaDatabase
{
    char *path;           /* full path of the DS descriptor */
    char *name_prefix;    /* table name prefix */
    char *field_prefix;   /* field name prefix */
    Dbptr dsptr;
    int numtable;
    DSSchemaTable *tables;
}              DSSchemaDatabase;

typedef enum  
{
  DBTYPE_ORACLE,
  DBTYPE_MYSQL,
  DBTYPE_POSTGRES,
  DBTYPE_DB2
} SQLDBType;  

int strTokenize(const char *instring, char delim, char ***outstring);
char* getHostURL();
char* getAbsolutePath(char *userpath);
char *strTrim(const char *instring);
int validDbptr(Dbptr db);
int dumpDbptr(Dbptr db);
void dsPtr2str(Dbptr* datascopedbPtr,  char *outBuf);
int str2dsPtr(char *inBuf, Dbptr* datascopedbPtr);
Dbptr DSopen(char *datascope_object_path);
DSSchemaDatabase *readDSSchema (Dbptr *dsptr, char *table_prefix, char *field_prefix);
void freeDSSchemaDatabase(DSSchemaDatabase *ds);
char *genNamePrefix(void);
void dumpDSDescTableSchema(DSSchemaDatabase *ds,SQLDBType sqldbtype,FILE *fp);
void dumpDSDescTableData(DSSchemaDatabase *ds_db, char *local_path, FILE *fp);
void dumpDSSchemaField2SQL(DSSchemaField *field, char *field_prefix, FILE *fp);
void dumpDSSchema2SQL(DSSchemaDatabase *ds_db, int drop_table_needed, FILE *fp);
void dumpDSDataRecord2SQL(DSSchemaField *ds_field, int index, FILE *fp);
void dumpDSData2SQL(DSSchemaDatabase *ds_db, int _max_row_dump, FILE *fp);
void dumpDSQuit(FILE *fp);
void usage (char *prog);

/** 
 * see if any dbptr is valid, if all valid, return 1, else 0 
 * 
 * @param dsptr datascope pointer
 * @return 1,0
 */
int 
validDbptr(Dbptr db)
{
  return ((dbINVALID!=db.database)&&(0==db.database)&&(dbINVALID!=db.table)&&(dbINVALID!=db.field)&&
         (dbINVALID!=db.record));
}    

/** 
 * see if any dbptr is valid, if all valid, return 1, else 0 
 * 
 * @param dsptr datascope pointer
 * @return 1,0
 */
int 
dumpDbptr(Dbptr db)
{
  fprintf(stderr,"%d|%d|%d|%d\n",db.database,db.table,db.field,db.record);
}    

/** 
 * get current host url, like mercali.ucsd.edu
 * 
 * @return full url, must be deallocated by caller.
 */
char* getHostURL()
{
  char _hostname[100]={0}, *trimed_hostname, _domainname[100]={0}, *trimed_domainname, *fullurl;
  
  if(0!=gethostname(_hostname,sizeof(_hostname)))
  {
    sprintf(_hostname,"unknownhost");
  }
  STRDUP_SAFE(trimed_hostname,_hostname);
  if(0==strlen(trimed_hostname))
  {
    sprintf(_hostname,"unknownhost");
  }
  
  if(0!=getdomainname(_domainname,sizeof(_domainname)))
  {
    sprintf(_domainname,"unknowndomain");
  }
  STRDUP_SAFE(trimed_domainname,_domainname);
  if(0==strlen(trimed_domainname))
  {
    sprintf(_domainname,"unknowndomain");
  }
  
  MALLOC_SAFE(fullurl,strlen(_hostname)+strlen(_domainname)+10);
  sprintf(fullurl,"%s.%s",_hostname,_domainname);
  FREEIF(trimed_hostname);
  FREEIF(trimed_domainname);
  
  return fullurl;
} 


/** 
 * translate a user input file path to a absolute path
 * 
 * @param userpath path input by user
 * @return full path, must be deallocated by caller.
 */
char* getAbsolutePath(char *userpath)
{
  char *userpath_trimed, *fullpath, cwd[1000];
  
  if (NULL==userpath)
  {
    WARNING("Null passed in!");
    return NULL;
  }
  
  userpath_trimed=strTrim(userpath);
  if ('/'==userpath_trimed[0])
    return userpath_trimed;
  else
  {
    getcwd(cwd,sizeof(cwd));
    cwd[sizeof(cwd)-1]='\0';  
    if('/'==cwd[strlen(cwd)-1])
    {
      cwd[strlen(cwd)-1]='\0';
    }
    MALLOC_SAFE(fullpath,strlen(cwd)+strlen(userpath_trimed)+5);
    sprintf(fullpath,"%s/%s",cwd,userpath_trimed);
    FREEIF(userpath_trimed)
    return fullpath;
  }
} 

/** 
 * split a string by delim and put into a newly allocated string array
 * 
 * @param instring input string
 * @param delim delimiter
 * @param outstring output, (pointer to) an array of strings.
 * @return number of token.
 */
int 
strTokenize(const char *instring, char delim, char ***outstring)
{
  int i=0, num_tok=0, tok_len;
  char *start, *end;
  
  /* count how many tokens are there */
  start=(char *)instring;
  while(NULL!=(end=strchr(start, delim))) 
  {
    num_tok++;
    start=end+sizeof(delim);
  }
  num_tok++;
  
  if(0>=num_tok) return 0;
  
  /* allocate memory to store array of char * */
  MALLOC_SAFE(*outstring, num_tok*sizeof(void *));
  
  /* allocate and assign each char * within the array */
  start=(char *)instring;
  while(end=strchr(start, delim))
  {
    tok_len=end-start;
    STRNDUP_SAFE((*outstring)[i],start,tok_len);
    start=end+sizeof(delim);
    i++;
  }
  
  /* get the last token */
  STRDUP_SAFE((*outstring)[i],start);
  
  return num_tok;
}

/** 
 * trim a string and put into a newly allocated string array
 * 
 * @param instring input string
 * @return new string, that's trimed on both way.
 */
char * 
strTrim(const char *instring)
{
  char *start, *end, *temp, *retval;
  start=(char *)instring;
  
  while(isspace(*start))
  {
    start++;
  }
  STRDUP_SAFE(temp,start);
  end=temp+strlen(temp)-1;
  while(isspace(*end))
  {
    *end='\0';
    end--;
  }
  STRDUP_SAFE(retval,temp);
  FREEIF(temp);
  return retval;
}


/** 
 * open a datascope object 
 * 
 * @param datascope_object_path path of the object
 * @return file descriptor.
 */
Dbptr 
DSopen(char *datascope_object_path)
{
  Dbptr dsptr;
  if(dbINVALID==dbopen_database(datascope_object_path,"r",&dsptr))
  {
    DIE("Could not open \"%s\" as a DS database\n",datascope_object_path);
  }
  return dsptr;
}    

/** 
 * read the datascope object, and convert into table structure (DSSchemaTable)
 * 
 * @param srb_conn srb connection
 * @param srb_obj_fd path descriptor
 * @param name_prefix prefix for all tables.
 * @param field_prefix prefix for all fields.
 * @return database structure, must be freed by caller!
 */  
DSSchemaDatabase *
readDSSchema (Dbptr *dsptr, char *name_prefix, char *field_prefix)
{
    int i,j,status;
    char *tablename, *fieldname;
    
    DSSchemaDatabase *database;     
    Dbvalue dbval, dbval_tablenames, dbval_fieldnames;
    
    /* assign returning values */
    MALLOC_SAFE(database,sizeof(*database));
    STRDUP_SAFE(database->name_prefix, name_prefix);
    STRDUP_SAFE(database->field_prefix, field_prefix);
    database->dsptr=*dsptr;
    
    /* all possible table names: schema+addon */
    if (0>dbquery(database->dsptr,dbSCHEMA_TABLES,&dbval_tablenames))
    {
      DIE("dbquery failed!\n");
    }
    
    /* numtable */
    database->numtable=maxtbl(dbval_tablenames.tbl);
    
    /* allocate space for tables*/
		MALLOC_SAFE(database->tables,database->numtable*sizeof(*database->tables));

    for(i=0;i<database->numtable;i++)
    {
    	/* assign table names */
    	STRDUP_SAFE(database->tables[i].name,gettbl(dbval_tablenames.tbl,i));
    	
      /* assign table dsptrs */	
    	database->tables[i].dsptr=dblookup(database->dsptr,0,database->tables[i].name,0,0);
    	if(!validDbptr(database->tables[i].dsptr))
    	{
    	  dumpDbptr(database->tables[i].dsptr);
    	  DIE("invalid dbptr when dblookup in table [%s]\n",database->tables[i].name);
    	}
    	
    	/* assign numrecord */
    	if (0>dbquery(database->tables[i].dsptr,dbRECORD_COUNT,&dbval))
      {
        DIE("dbquery failed! database->tables[i].name=%s\n",database->tables[i].name);
      }
      database->tables[i].numrecord=dbval.i;
      
      /* get all field names */
    	if (0>dbquery(database->tables[i].dsptr,dbTABLE_FIELDS,&dbval_fieldnames))
      {
        DIE("dbquery failed!\n");
      }
      
      /* assign numfield */
      database->tables[i].numfield=maxtbl(dbval_fieldnames.tbl);
    	
    	/* allocate space for fileds */
    	MALLOC_SAFE(database->tables[i].fields, 
    	  database->tables[i].numfield*sizeof(*database->tables[i].fields));
    	
    	for(j=0;j<database->tables[i].numfield;j++)
      {
        /* assign field name */
      	STRDUP_SAFE(database->tables[i].fields[j].name,gettbl(dbval_fieldnames.tbl,j));
      	
      	/* assign field dsptr */	
      	database->tables[i].fields[j].dsptr=
      	  dblookup(database->tables[i].dsptr,0,database->tables[i].name,
      	    database->tables[i].fields[j].name,0);
      	if(!validDbptr(database->tables[i].fields[j].dsptr))
      	{
      	  dumpDbptr(database->tables[i].fields[j].dsptr);
      	  DIE("invalid dbptr i=%d, j=%d\n",i,j);
      	}
      	
      	/* assign field type */
      	if (0>dbquery(database->tables[i].fields[j].dsptr,dbFIELD_TYPE,&dbval))
        {
          DIE("dbquery failed!\n");
        }
        database->tables[i].fields[j].type=dbval.i;
        
        /* assign field size */
      	if (0>dbquery(database->tables[i].fields[j].dsptr,dbFIELD_SIZE,&dbval))
        {
          DIE("dbquery failed!\n");
        }
        database->tables[i].fields[j].size=dbval.i;
        
        /* assign field format */
      	if (0>dbquery(database->tables[i].fields[j].dsptr,dbFIELD_FORMAT,&dbval))
        {
          DIE("dbquery failed!\n");
        }
        STRNCPY(database->tables[i].fields[j].format,dbval.t,sizeof(database->tables[i].fields[j].format));
      }
    }
    
    return database;
}

/** 
 * free a DSSchemaDatabase (dynamically allocated)
 * 
 * @param ds DSSchemaDatabase struct pointer
 * @return none
 */  
void
freeDSSchemaDatabase(DSSchemaDatabase *ds)
{
  if (NULL==ds) return;
  
  int i,j, numtable,numfield;
  
  for(i=0;i<ds->numtable;i++)
  {
    for(j=0;j<ds->tables[i].numfield;j++)
    {
    	FREEIF(ds->tables[i].fields[j].name);
    }
    FREEIF(ds->tables[i].fields);
    
    FREEIF(ds->tables[i].name);
  }
  
  FREEIF(ds->tables);
  FREEIF(ds->name_prefix);
  FREEIF(ds->field_prefix);
  FREEIF(ds);
}

/** 
 * Generate a prefix for database tables:
 * "username+yyyymmddhhmmss"
 * 
 * @return name prefix string. must be freed by caller!
 */  
char * 
genNamePrefix()
{
  char *name_prefix, *cur_username;
  struct tm tm;
  time_t timep;
  struct passwd *passwd;
  
  /* get current username */
  /*
  passwd=getpwuid(geteuid());
  if (NULL==passwd)
  {
    DIE("could not retreive username\n");
  }
  STRDUP_SAFE(cur_username,passwd->pw_name);
  */
  
  
  /* get current GMT time */
  /*
  time(&timep);
  gmtime_r(&timep, &tm);
  */
  
  /* allocate space for returned string. note that 14 is length for yyyymmddhhmmss */
  /*
  MALLOC_SAFE(name_prefix,
    strlen(cur_username)+14*sizeof(char)+sizeof('\0'));
  
  sprintf(name_prefix,"%s%.4d%.2d%.2d%.2d%.2d%.2d", 
    cur_username,
    tm.tm_year+1900,tm.tm_mon+1,tm.tm_mday,tm.tm_hour,tm.tm_min,tm.tm_sec);
  
  FREEIF(cur_username);
  return name_prefix;
  */
  
  STRDUP_SAFE(name_prefix,"\0");
  return name_prefix;
}

/** 
 * Dump SQL to create a descriptor table for all datascope databases
 * 
 * @param ds DSSchemaDatabase 
 * @param sqldbtype type of the sql database
 * @param fp output file pointer
 * @return none
 */

void dumpDSDescTableSchema(DSSchemaDatabase *ds,SQLDBType sqldbtype, FILE *fp)
{
  switch (sqldbtype)
  {
    case DBTYPE_ORACLE:
    {
      fprintf(fp, "-- ===Oracle PL/SQL to create datascope desciptor table if not exits=== --\n");
      fprintf(fp, "DECLARE \n");
      fprintf(fp, "c_table_name varchar(%d) := upper('%s'); \n",strlen(DS_DESC_TABLE)+2,DS_DESC_TABLE);
      fprintf(fp, "cursor c1 is       \n");
      fprintf(fp, "select table_name  \n");
      fprintf(fp, "  from user_tables \n");
      fprintf(fp, "where table_name = c_table_name; \n");
      
      fprintf(fp, "BEGIN               \n");
      fprintf(fp, "open c1;            \n");
      fprintf(fp, "fetch c1 into c_table_name; \n");
      fprintf(fp, "if c1%%NOTFOUND     \n");
      fprintf(fp, "then                \n");
      fprintf(fp, "execute immediate   \n");
      fprintf(fp, "  'create table %s (\n",DS_DESC_TABLE);
      fprintf(fp, "    table_name   VARCHAR(100), \n");
      fprintf(fp, "    dstable_name VARCHAR(100), \n");
      fprintf(fp, "    table_prefix VARCHAR(100), \n");
      fprintf(fp, "    field_prefix VARCHAR(100), \n");
      fprintf(fp, "    local_host   VARCHAR(500), \n");
      fprintf(fp, "    local_path   VARCHAR(500), \n");
      fprintf(fp, "    srb_server   VARCHAR(500), \n");
      fprintf(fp, "    srb_zone     VARCHAR(100), \n");
      fprintf(fp, "    srb_port     VARCHAR(10),  \n");
      fprintf(fp, "    srb_path     VARCHAR(500), \n");
      fprintf(fp, "    comments     VARCHAR(500)  \n");
      fprintf(fp, "   )';    \n");
      fprintf(fp, "end if;   \n");
      fprintf(fp, "close c1; \n");
      fprintf(fp, "END;      \n");
      fprintf(fp, "/         \n");
      fprintf(fp, "-- ===End of PL/SQL=== --\n");
      break;
    }
    case DBTYPE_MYSQL:
    {
      fprintf(fp, "  create table if not exists %s (\n",DS_DESC_TABLE);
      fprintf(fp, "    table_name   VARCHAR(100), \n");
      fprintf(fp, "    dstable_name VARCHAR(100), \n");
      fprintf(fp, "    table_prefix VARCHAR(100), \n");
      fprintf(fp, "    field_prefix VARCHAR(100), \n");
      fprintf(fp, "    local_host   VARCHAR(500), \n");
      fprintf(fp, "    local_path   VARCHAR(500), \n");
      fprintf(fp, "    srb_server   VARCHAR(500), \n");
      fprintf(fp, "    srb_zone     VARCHAR(100), \n");
      fprintf(fp, "    srb_port     VARCHAR(10),  \n");
      fprintf(fp, "    srb_path     VARCHAR(500), \n");
      fprintf(fp, "    comments     VARCHAR(500)  \n");
      fprintf(fp, "   );    \n");
      break;
    }
    case DBTYPE_DB2:
    case DBTYPE_POSTGRES:
    {
      fprintf(fp, "  create table %s (\n",DS_DESC_TABLE);
      fprintf(fp, "    table_name   VARCHAR(100), \n");
      fprintf(fp, "    dstable_name VARCHAR(100), \n");
      fprintf(fp, "    table_prefix VARCHAR(100), \n");
      fprintf(fp, "    field_prefix VARCHAR(100), \n");
      fprintf(fp, "    local_host   VARCHAR(500), \n");
      fprintf(fp, "    local_path   VARCHAR(500), \n");
      fprintf(fp, "    srb_server   VARCHAR(500), \n");
      fprintf(fp, "    srb_zone     VARCHAR(100), \n");
      fprintf(fp, "    srb_port     VARCHAR(10),  \n");
      fprintf(fp, "    srb_path     VARCHAR(500), \n");
      fprintf(fp, "    comments     VARCHAR(500)  \n");
      fprintf(fp, "   );    \n");
      break;
    }
    
    default:
      DIE("wrong sqldbtype: %d!\n",sqldbtype);
  }
}

/** 
 * dump all datascope descriptor data to SQL 
 * 
 * @param ds_db DSSchemaDatabase database
 * @param local_path full path of datascope descriptor
 * @param fp output file pointer
 * @return none
 */
void
dumpDSDescTableData(DSSchemaDatabase *ds_db, char *local_path, FILE *fp)
{
  int i,j,k,status;
  char *url;
  
  url=getHostURL();
  
  for (i=0; i<ds_db->numtable; i++)
  {
    fprintf(fp,"INSERT INTO %s ( ",DS_DESC_TABLE);
    fprintf(fp,"  table_name, ");
    fprintf(fp,"  dstable_name, ");
    fprintf(fp,"  table_prefix, ");
    fprintf(fp,"  field_prefix, ");
    fprintf(fp,"  local_host,   ");
    fprintf(fp,"  local_path    ");
    fprintf(fp,") \n");
    fprintf(fp,"VALUES ");
    fprintf(fp,"('%s%s','%s','%s','%s','%s','%s');\n",
               ds_db->name_prefix,ds_db->tables[i].name,
               ds_db->tables[i].name,
               ds_db->name_prefix,
               ds_db->field_prefix,
               url,
               local_path
           );
  }   
  
  FREEIF(url);
}  

/** 
 * translate datascope field schema to ANSI SQL schema
 * 
 * @param field DSSchemaField field
 * @param field_prefix prefix for field names
 * @param fp output file pointer
 * @return none
 */
void
dumpDSSchemaField2SQL(DSSchemaField *field, char *field_prefix, FILE *fp)
{
  fprintf(fp,"%s%s ",field_prefix,field->name);
  switch (field->type)
  {
    case dbBOOLEAN:
    case dbINTEGER:
    case dbYEARDAY:
      fprintf(fp,"INTEGER");
      break;  
    case dbREAL:
    case dbTIME:
      fprintf(fp,"REAL");
      break;
    case dbSTRING:  
    case dbLINK:  
      fprintf(fp,"VARCHAR (%d)",field->size);
      break;
    default: 
      DIE("wrong datatype: %d!\n",field->type);
  }
  
}

/** 
 * dump datascope schema to ANSI SQL schema
 * 
 * @param ds_db DSSchemaDatabase database
 * @param drop_table_needed if "drop table xxx" is needed
 * @param fp output file pointer
 * @return none
 */
void 
dumpDSSchema2SQL(DSSchemaDatabase *ds_db, int drop_table_needed, FILE *fp)
{
  int i,j;
  for (i=0; i<ds_db->numtable; i++)
  {
    if (drop_table_needed)
    {
      fprintf(fp,"DROP TABLE %s%s; \n",
        ds_db->name_prefix,ds_db->tables[i].name);
        
      fprintf(fp,"DELETE FROM %s WHERE table_name='%s%s'; \n",
        DS_DESC_TABLE,ds_db->name_prefix,ds_db->tables[i].name); 
    }
    fprintf(fp,"CREATE TABLE %s%s\n",
      ds_db->name_prefix,ds_db->tables[i].name);
    fprintf(fp,"(\n");
    for (j=0; j<ds_db->tables[i].numfield; j++)
    {
      fprintf(fp,"  ");
      dumpDSSchemaField2SQL(&(ds_db->tables[i].fields[j]),ds_db->field_prefix,fp);
      if (j!=ds_db->tables[i].numfield-1)
        fprintf(fp,",");
      fprintf(fp,"\n");
    }
    fprintf(fp,");\n");
  }
}

/** 
 * translate datascope field/record value to ANSI SQL value (string:)
 * 
 * @param ds_field DSSchemaField
 * @param index index of the record 
 * @param fp output file pointer
 * @return none
 */
void
dumpDSDataRecord2SQL(DSSchemaField *ds_field, int index, FILE *fp)
{
  Dbptr dsptr;
  int i=0, status;
  char *temp1, *temp2;
  Dbvalue dbval;
  
  dsptr=ds_field->dsptr;
  dsptr.record=index;
  
  if(0!=(status=dbgetv(dsptr,0,ds_field->name,&dbval,0)))
  {
    dumpDbptr(dsptr);
    DIE("dbgetv failed! status=%d\n",status);
  }
  
  switch (ds_field->type)
  {
    case dbSTRING:
    case dbLINK:
      fprintf(fp,"'");
      MALLOC_SAFE(temp1,sizeof(char)*ds_field->size+1);
      sprintf(temp1,ds_field->format,dbval.s);
      temp2=strTrim(temp1);
      
      /* escape "'" */
      i=0;
      while('\0'!=temp2[i])
      {
        if ('\''==temp2[i])
          fputc('\'',fp);
        fputc(temp2[i],fp);
        i++;
      }  
        
      fprintf(fp,"'");
      FREEIF(temp1);
      FREEIF(temp2);
      break;
    case dbBOOLEAN:
	  case dbINTEGER:
	  case dbYEARDAY:
	    fprintf(fp,ds_field->format,dbval.i);
	    break;
    case dbREAL:
	  case dbTIME:
	    fprintf(fp,ds_field->format,dbval.d);
	    break;
    default:
      DIE("wrong datatype: %d!\n",ds_field->type);
  }
      
}

/** 
 * dump all datascope data to ANSI SQL 
 * 
 * @param ds_db DSSchemaDatabase database
 * @_max_row_dump max number of rwos to be dumped, if -1, then no limit
 * @param fp output file pointer
 * @return none
 */
void
dumpDSData2SQL(DSSchemaDatabase *ds_db, int _max_row_dump, FILE *fp)
{
  int i,j,k,status;
  
  for (i=0; i<ds_db->numtable; i++)
  {
    if (ds_db->tables[i].numrecord<=0) continue;
    
    for(j=0; j<_max_row_dump&&j<ds_db->tables[i].numrecord; j++)
    {
      fprintf(fp,"INSERT INTO %s%s VALUES (",
        ds_db->name_prefix,ds_db->tables[i].name);
      for(k=0; k<ds_db->tables[i].numfield; k++)
      {
        dumpDSDataRecord2SQL(&ds_db->tables[i].fields[k],j,fp);
        if (k!=ds_db->tables[i].numfield-1)
          fprintf(fp,", ");
      }
      fprintf(fp,");\n");
    }  
  }   
}  

/** 
 * print "quit;" at the end of batch file to close connection 
 * 
 * @param fp output file pointer
 * @return none
 */
void
dumpDSQuit(FILE *fp)
{
  fprintf(fp,"QUIT;\n");   
}  

void
usage (char *prog)
{
    fprintf(stderr,"Usage  :%s [-s] [-h] [-o output_file] [-d sqldatabase_type] [-n max_num_row_dump] [-t table_prefix] [-f field_prefix] datascope_descriptor_file \n",
      prog);
}


int
main(int argc, char **argv)
{
  char c, *DS_path, *DS_fullpath, *name_prefix, *field_prefix;
  int drop_table_needed=0, max_row_dump=INT_MAX;
  FILE *outfp=stdout;
  DSSchemaDatabase *ds_db=NULL;
  Dbptr dsptr;
  SQLDBType sqltype=DBTYPE_ORACLE;

  STRDUP_SAFE(name_prefix,"\0");
  STRDUP_SAFE(field_prefix,"\0");
  while ((c=getopt(argc, argv,"shf:n:o:t:d:")) != EOF)
  {
    switch (c)
    {
      case 's':
        drop_table_needed=1;
        break;
      case 'h':
        usage (argv[0]);
        exit (0);
      case 'o':
        if ((outfp = fopen(optarg, "w")) == NULL)
        {
          fprintf(stderr, "Error: Cannot open %s. Using standard out instead\n", optarg);
          outfp=stdout;
        }
        break;
      case 'n':
        max_row_dump=atoi(optarg);
        break;  
      case 't':
        STRDUP_SAFE(name_prefix,optarg);
        break;
      case 'f':
        STRDUP_SAFE(field_prefix,optarg);
        break;  
      case 'd':
        if ((0==strcmp("oracle",optarg))||(0==strcmp("ORACLE",optarg)))
          sqltype=DBTYPE_ORACLE;
        else
        if ((0==strcmp("mysql",optarg))||(0==strcmp("MYSQL",optarg)))
          sqltype=DBTYPE_MYSQL;
        else
        if ((0==strcmp("postgres",optarg))||(0==strcmp("POSTGRES",optarg)))
          sqltype=DBTYPE_POSTGRES;
        else
        if ((0==strcmp("db2",optarg))||(0==strcmp("DB2",optarg)))
          sqltype=DBTYPE_DB2;   
        else
        {
          fprintf(stderr,"Database type:%s is not supported at this moment!\n",optarg);
          exit(-1);
        }
        break;
      default:
        usage (argv[0]);
        exit (1);
    }
  }
  
  /* srbObj name or full path is required */
  if (argc <= optind)
  {
    usage (argv[0]);
    exit (1);
  }
  DS_path=argv[optind];
  
  DS_fullpath=getAbsolutePath(DS_path);
  
  dsptr=DSopen(DS_fullpath);
  ds_db=readDSSchema (&dsptr,name_prefix, field_prefix);
  dumpDSSchema2SQL(ds_db,drop_table_needed,outfp);
  dumpDSDescTableSchema(ds_db,sqltype,outfp);
  dumpDSDescTableData(ds_db,DS_fullpath,outfp);
  dumpDSData2SQL(ds_db,max_row_dump,outfp);
  if (DBTYPE_ORACLE==sqltype)
    dumpDSQuit(outfp);
  
  dbclose(dsptr);
  FREEIF(name_prefix);
  FREEIF(field_prefix);
  freeDSSchemaDatabase(ds_db);
  FREEIF(DS_fullpath);
  return 0;
}
