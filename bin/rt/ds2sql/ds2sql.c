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
#define  DBTABLE_PREFIX_DELIMITER "___" /* delimiter for database table name and prefix   */
                                        /* for eg., if table name is wfdisc in datascope  */
                                        /* and prefix is sdsc, then the acctaul table name*/
                                        /* in database (sql based) will be: sdsc___wfdisc */

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
    char *name_prefix;
    Dbptr dsptr;
    int numtable;
    DSSchemaTable *tables;
}              DSSchemaDatabase;

int strTokenize(const char *instring, char delim, char ***outstring);
char *strTrim(const char *instring);
void dsPtr2str(Dbptr* datascopedbPtr,  char *outBuf);
int str2dsPtr(char *inBuf, Dbptr* datascopedbPtr);
Dbptr DSopen(char *datascope_object_path);
DSSchemaDatabase *readDSSchema (Dbptr *dsptr, char *name_prefix);
void freeDSSchemaDatabase(DSSchemaDatabase *ds);
char *genNamePrefix(void);
void dumpDSSchemaField2SQL(DSSchemaField *field, FILE *fp);
void dumpDSSchema2SQL(DSSchemaDatabase *ds_db, int drop_table_needed, FILE *fp);
void dumpDSDataRecord2SQL(DSSchemaField *ds_field, int index, FILE *fp);
void dumpDSData2SQL(DSSchemaDatabase *ds_db, int _max_row_dump, FILE *fp);
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
 * @return database structure, must be freed by caller!
 */  
DSSchemaDatabase *
readDSSchema (Dbptr *dsptr, char *name_prefix)
{
    int i,j,status;
    char *tablename, *fieldname;
    
    DSSchemaDatabase *database;     
    Dbvalue dbval, dbval_tablenames, dbval_fieldnames;
    
    /* assign returning values */
    MALLOC_SAFE(database,sizeof(*database));
    STRDUP_SAFE(database->name_prefix, name_prefix);
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
 * translate datascope field schema to ANSI SQL schema
 * 
 * @param field DSSchemaField field
 * @param fp output file pointer
 * @return none
 */
void
dumpDSSchemaField2SQL(DSSchemaField *field, FILE *fp)
{
  fprintf(fp,"%s ",field->name);
  switch (field->type)
  {
    case dbBOOLEAN:
      fprintf(fp,"INTEGER");
      break;
    case dbINTEGER:
      fprintf(fp,"INTEGER");
      break;  
    case dbREAL:
      fprintf(fp,"REAL");
      break;  
    case dbTIME:
      fprintf(fp,"REAL");
      break;
    case dbYEARDAY:
      fprintf(fp,"INTEGER");
      break;
    case dbSTRING:  
      fprintf(fp,"CHAR (%d)",field->size);
      break;
    case dbLINK:  
      fprintf(fp,"CHAR (%d)",field->size);
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
    }
    fprintf(fp,"CREATE TABLE %s%s\n",
      ds_db->name_prefix,ds_db->tables[i].name);
    fprintf(fp,"(\n");
    for (j=0; j<ds_db->tables[i].numfield; j++)
    {
      fprintf(fp,"  ");
      dumpDSSchemaField2SQL(&(ds_db->tables[i].fields[j]),fp);
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
  int status;
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
      fprintf(fp,"%s",temp2);
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
    
    for(j=0; j<=_max_row_dump&&j<ds_db->tables[i].numrecord; j++)
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

void
usage (char *prog)
{
    fprintf(stderr,"Usage  :%s [-dnp] [-h] [-f output_file] [datascope_descriptor_file ...]\n",
      prog);
}


int
main(int argc, char **argv)
{
  char c, *DS_path, *name_prefix=NULL;
  int drop_table_needed=0, max_row_dump=INT_MAX;
  FILE *outfp=stdout;
  DSSchemaDatabase *ds_db=NULL;
  Dbptr dsptr;

  while ((c=getopt(argc, argv,"dhf:n:p:")) != EOF)
  {
    switch (c)
    {
      case 'd':
        drop_table_needed=1;
        break;
      case 'h':
        usage (argv[0]);
        exit (0);
      case 'f':
        if ((outfp = fopen(optarg, "w")) == NULL)
        {
          fprintf(stderr, "Error: Cannot open %s. Using standard out instead\n", optarg);
          outfp=stdout;
        }
        break;
      case 'n':
        max_row_dump=atoi(optarg);
        break;  
      case 'p':
        STRDUP_SAFE(name_prefix,optarg);
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
  
  if(NULL==name_prefix)
  {
    name_prefix=genNamePrefix();
  }
  
  dsptr=DSopen(DS_path);
  
  ds_db=readDSSchema (&dsptr,name_prefix);
  dumpDSSchema2SQL(ds_db,drop_table_needed,outfp);
  dumpDSData2SQL(ds_db,max_row_dump,outfp);
  
  dbclose(dsptr);
  FREEIF(name_prefix);
  freeDSSchemaDatabase(ds_db);
  return 0;


}
