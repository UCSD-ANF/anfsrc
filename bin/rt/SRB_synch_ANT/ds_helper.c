#include "ds_helper.h"

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


int 
dbPtr2str(Dbptr* datascopedbPtr,  char *outBuf)
{
    sprintf(outBuf, "%i|%i|%i|%i", 
            datascopedbPtr->database,
            datascopedbPtr->table,
            datascopedbPtr->field,
            datascopedbPtr->record);

    return(0);

}

int
str2dbPtr(char * inBuf, Dbptr*   datascopedbPtr) 
{

    char *argv[10];
    int i;

    i = getArgsFromString (inBuf,argv,'|');
    if (i < 4) {
        datascopedbPtr->database = 0 ;
        datascopedbPtr->table =  0;
        datascopedbPtr->field =  0;
        datascopedbPtr->record =  0;
        return(i);
    }
    datascopedbPtr->database = atoi(argv[0]);
    datascopedbPtr->table =  atoi(argv[1]);
    datascopedbPtr->field =  atoi(argv[2]);
    datascopedbPtr->record =  atoi(argv[3]);
    return(0);

}

/*
 * increment record index of a dbptr, in string format. 
 *
 * Input   - dbptr_str: dbptr in string format.
 *         
 * Output  None.          
 */
void 
incDBRecord(char* dbptr_str)
{
    Dbptr dbptr;
    str2dbPtr(dbptr_str, &dbptr);
    if (dbptr.record<0)
      dbptr.record=0;
    dbptr.record++;
    dbPtr2str(&dbptr, dbptr_str);
}

/*
 * set record index of a dbptr, as the value of record_index, in string format. 
 *
 * Input   - dbptr_str: dbptr in string format.
 *         
 * Output  None.          
 */
void 
setDBRecord(char* dbptr_str, int record_index)
{
    Dbptr dbptr;
    str2dbPtr(dbptr_str, &dbptr);
    if (dbptr.record<0)
      dbptr.record=0;
    dbptr.record=record_index;
    dbPtr2str(&dbptr, dbptr_str);
}

/*
 * set table value of a dbptr, in string format. 
 *
 * Input   - dbptr_str: dbptr in string format.
 *         
 * Output  None.          
 */
void 
setDBTable(char* dbptr_str, int table_value)
{
    Dbptr dbptr;
    str2dbPtr(dbptr_str, &dbptr);
    dbptr.table=table_value;
    dbPtr2str(&dbptr, dbptr_str);
}

/*
 * clear field and record index of a dbptr, in string format. 
 *
 * Input   - dbptr_str: dbptr in string format.
 *         
 * Output  None.          
 */
void 
clearDBFieldRecord(char* dbptr_str)
{
    Dbptr dbptr;
    str2dbPtr(dbptr_str, &dbptr);
    dbptr.field=0;
    dbptr.record=0;
    dbPtr2str(&dbptr, dbptr_str);
}

/*
 * parse a dbSTRING  
 *
 * Input   - start: start ptr of target string
 *         - end: end ptr of target string
 *         - out: caller's storage, need to be pre-allocated.
 *         - outlen: length of out
 *         
 * Output  - OKAY: 1
 *         - ERROR: 0
 */
int 
parseDBString(char *start, char *end, char *out, int out_len)
{
  int token_len;
  size_t cpy_len;
  memset(out,0,out_len);
  if (strstr(start, DS_PREFIX_DBSTRING)) 
      start=start+sizeof(DS_PREFIX_DBSTRING)-1;
  else
  {
      DEBUG(">>>> input buff contains no dbstring prefix. input buff=%s\n",start);
      return 0;
  }
  token_len=end-start;
  cpy_len=(token_len<out_len-1)?token_len:out_len-1;
  strncpy(out, start, cpy_len);
  out[cpy_len]=0;
  return 1;
}

/*
 * parse a dbREAL  
 *
 * Input   - start: start ptr of target string
 *         - end: end ptr of target string
 *         - out: caller's float holder, need to be pre-allocated.
 *        
 * Output  - OKAY: 1
 *         - ERROR: 0
 */
int 
parseDBReal(char *start, char *end, double *out)
{
  int token_len;
  size_t cpy_len;
  char temp_buff[100]={0};
  if (strstr(start, DS_PREFIX_DBREAL)) 
      start=start+sizeof(DS_PREFIX_DBREAL)-1;
  else
  {
      DEBUG(">>>> input buff contains no dbreal prefix. input buff=%s\n",start);
      return 0;
  }
  token_len=end-start;
  cpy_len=(token_len<sizeof(temp_buff)-1)?token_len:sizeof(temp_buff)-1;
  strncpy(temp_buff, start, cpy_len);
  temp_buff[cpy_len]=0;
  *out=atof(temp_buff);
  return 1;
}

/*
 * parse a dbINTEGER  
 *
 * Input   - start: start ptr of target string
 *         - end: end ptr of target string
 *         - out: caller's integer holder, need to be pre-allocated.
 *        
 * Output  - OKAY: 1
 *         - ERROR: 0
 */
int 
parseDBInteger(char *start, char *end, int *out)
{
  int token_len;
  size_t cpy_len;
  char temp_buff[100]={0};
  if (strstr(start, DS_PREFIX_DBINTEGER)) 
      start=start+sizeof(DS_PREFIX_DBINTEGER)-1;
  else
  {
      DEBUG(">>>> input buff contains no dbreal prefix. input buff=%s\n",start);
      return 0;
  }
  token_len=end-start;
  cpy_len=(token_len<sizeof(temp_buff)-1)?token_len:sizeof(temp_buff)-1;
  strncpy(temp_buff, start, cpy_len);
  temp_buff[cpy_len]=0;
  *out=atoi(temp_buff);
  return 1;
}

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/ds_helper.c,v $
 * $Revision: 1.2 $
 * $Author: sifang $
 * $Date: 2005/05/06 03:07:39 $
 *
 * $Log: ds_helper.c,v $
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
