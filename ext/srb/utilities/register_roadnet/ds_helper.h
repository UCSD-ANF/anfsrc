#ifndef _DS_HELPER_H_
#define _DS_HELPER_H_

#define  MAX_PROC_ARGS_FOR_DS 100

#define  MAX_DBPTR_STRLEN 100   //max strlen of dbptr
#define  DS_PREFIX_DBSTRING "dbSTRING:" //dbgetv returns data with perfix
#define  DS_PREFIX_DBREAL   "dbREAL:"
#define  DS_PREFIX_DBINTEGER   "dbINTEGER:"

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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include "ds_const.h"

typedef struct Dbptr
{
    int             database,
	table,
	field,
	record;
}              Dbptr;


int getArgsFromString(char *inStr, char *argv[], char del);
int dbPtr2str(Dbptr* datascopedbPtr,  char *outBuf);
int str2dbPtr(char * inBuf, Dbptr*   datascopedbPtr);
void incDBRecord(char* dbptr_str);
void setDBRecord(char* dbptr_str, int record_index);
void setDBTable(char* dbptr_str, int table_value);
void clearDBRecord(char* dbptr_str);
void clearDBFieldRecord(char* dbptr_str);
int parseDBString(char *start, char *end, char *out, int out_len);
int parseDBReal(char *start, char *end, double *out);
int parseDBInteger(char *start, char *end, int *out);
        
        
#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/ext/srb/utilities/register_roadnet/Attic/ds_helper.h,v $
 * $Revision: 1.2 $
 * $Author: sifang $
 * $Date: 2005/01/07 03:01:17 $
 *
 * $Log: ds_helper.h,v $
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */
