
 



#ifndef DATASCOPE_MDRIVER_EXTERN_H
#define DATASCOPE_MDRIVER_EXTERN_H

#ifdef DATASCOPE_MD

#include "MDriverExtern.h"
#include "c.h"
#include "srb.h"
#include "db.h"
#include "stock.h"
#include "bns.h"
#include "dbxml.h"
#define VDATASCOPEPKTHEADER 256
#define MAX_HTML_ROW_SIZE 2048
#define TMP_STRING_SIZE 256
#define MIN_datascope_BUF_SIZE 1000
#define MAX_CURVE_SIZE 8000
typedef struct {
  void   *dbPtrPtr;
  int   firstRead;
  int   timeout;
  int   numofpkts;
  int   numbulkreads;
  int   datascopeFlags;
  int   datascopeMode;
  int   isView;
  char *which;
  char *presentation;
  char *select;
  char *reject;
  char *after;
  char *position;
  char *rsrcInfo;
  char *userName;
  char *dstable;
  char *dsfind;
  char *dsfindRev;
  char *tmpFileName;
  Tbl  *dsprocessStmt;
  Tbl  *requestFieldNames;
  Bns  *xml_bns;
  char *db2xmlOrigStr;
  char * db2xmlRemStr;
  FILE *dbfilefd;
  Arr  *exprArray;
}datascopeStateInfo;

extern int freeDatascopeStateInfo(datascopeStateInfo *datascopeSI);
extern int getDatascopeStateInfo(datascopeStateInfo *datascopeSI, char *rsrcInfo,
           char *datascopePathDesc, int datascopeFlags, int datascopeMode, char *userName);

extern int datascopeOpen(MDriverDesc *mdDesc, char *dataInfo, 
                   char *datascopePathDesc, 
                   int datascopeFlags, int datascopeMode, char *userName);
extern int datascopeCreate(MDriverDesc *mdDesc, char *rsrcInfo, 
                     char *datascopePathDesc, 
                     int datascopeMode, char *userName);
extern int datascopeClose(MDriverDesc *mdDesc);
extern int datascopeRead(MDriverDesc *mdDesc, char *buffer, int length);
extern int datascopeWrite(MDriverDesc *mdDesc, char *buffer, int length);
extern srb_long_t datascopeSeek(MDriverDesc *mdDesc, srb_long_t offset, int whence);
extern int datascopeUnlink(char *rsrcAddress, char *datascopePathDesc);
extern int datascopeSync(MDriverDesc *mdDesc);
extern int datascopeProc(MDriverDesc *mdDesc, char *procName, 
              char *inBuf, int inLen,
              char *outBuf, int outLen );

#endif /* DATASCOPE_MD */
 
#endif  /* DATASCOPE_MDRIVER_EXTERN_H */
