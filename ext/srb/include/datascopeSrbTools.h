#ifndef DATASCOPE_SRB_TOOLS_H
#define DATASCOPE_SRB_TOOLS_H

#include <stdarg.h>
#include "db.h"
#include "stock.h"

#define MAX_PROC_ARGS_FOR_DS 100
#define DSDELIM '|'
#define DSESC '\\'

extern char *putArgsToString(char del, char esc, int nargs, ...);
extern void addArgsToString(char **string, char del, char esc, Tbl *args );
extern int getArgsFromString(char *inStr, char *argv[], char del, char esc);
extern int str2dbPtr(char * inBuf, Dbptr*   datascopedbPtr);
extern int dbPtr2str(Dbptr* datascopedbPtr,  char *outBuf);
extern int unescapeDelimiter(char *inOutStr, char del, char esc);
extern int escapeDelimiter(char *inStr, char *outStr, char del, char esc);
extern int dbTable2str(Tbl *inTbl, char *outStr);
extern int dbArray2str(Arr *inArr, char *outStr);
extern Tbl *str2dbTable(char *inStr);
extern Arr *str2dbArray(char *inStr);

#endif /* DATASCOPE_SRB_TOOLS_H */
