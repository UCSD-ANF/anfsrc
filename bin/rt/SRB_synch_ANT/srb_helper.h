#ifndef _SRB_HELPER_H_
#define _SRB_HELPER_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <time.h>
#include <errno.h>
#include "scommands.h"
#include "ds_helper.h"
#include "source.h"

int findSourceInSRB (srbConn *srb_conn, char* srb_col, Source *src_new, Source *src_old);
void unregisterDataWithInResult(srbConn *srb_conn, char* srb_col, 
																mdasC_sql_result_struct *myresult);
void unregisterAllSources(srbConn *srb_conn, char* srb_col);
char *getDataNamesInColl (srbConn *conn, char *parColl, int *num_data_result);
void addSRBMetaData(srbConn *srb_conn, char* srb_rsrc, char* srb_col, Source *src);
void makeSourceFromSRB(srbConn *srb_conn, char* srb_col, char* srb_dataname, Source *src);
int registerSource(srbConn *srb_conn, char* srb_rsrc, char* srb_col, Source *src);
int unRegisterSource(srbConn *srb_conn, char* srb_col, Source *src);
int unRegisterData(srbConn *srb_conn, char* srb_col, char *dataname);
int parseSRBDSStringToSource(srbConn *srb_conn,int srb_obj_fd,char * dbPtr_str,char *owner,
                             Source *src);
int getRowCount(srbConn *srb_conn,int srb_obj_fd,char * dbPtr_str,size_t size_dbPtr);
void dbJoinTable( srbConn *srb_conn,int srb_obj_fd,char * dbPtr_str,
                  char *dbprtstr_result, size_t result_len);
void dbAddvSourceToDS(srbConn *srb_conn,int srb_obj_fd,char *dbPtr_str);

#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/srb_helper.h,v $
 * $Revision: 1.1 $
 * $Author: sifang $
 * $Date: 2005/01/11 03:38:10 $
 *
 * $Log: srb_helper.h,v $
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
