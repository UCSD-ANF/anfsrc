#include "scommands.h"
#include "datascopeSrbTools.h"

#define BUFSIZE         2097152

extern char srbAuth[];
extern char srbHost[];
extern char mdasCollectionName[];
extern char mdasCollectionHome[];
extern char inCondition[];

extern int srb_dbopen( char *path, char *permissions, Dbptr *db );
