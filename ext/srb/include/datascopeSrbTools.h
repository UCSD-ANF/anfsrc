#ifndef DATASCOPE_SRB_TOOLS_H
#define DATASCOPE_SRB_TOOLS_H

#include "db.h"
#include "stock.h"

#define MAX_PROC_ARGS_FOR_DS 100

extern int getArgsFromString(char *inStr, char *argv[], char del);
extern int str2dbPtr(char * inBuf, Dbptr*   datascopedbPtr);
extern int dbPtr2str(Dbptr* datascopedbPtr,  char *outBuf);
extern int unescapeDelimiter(char *inOutStr, char del, char esc);
extern int escapeDelimiter(char *inStr, char *outStr, char del, char esc);
extern int dbTable2str(Tbl *inTbl, char *outStr);
extern int dbArray2str(Arr *inArr, char *outStr);

#endif /* DATASCOPE_SRB_TOOLS_H */
