#include "scommands.h"
#include "datascopeSrbTools.h"

#define BUFSIZE         2097152

extern char srbAuth[];
extern char srbHost[];
extern char mdasCollectionName[];
extern char mdasCollectionHome[];
extern char inCondition[];

extern int srb_dbopen( char *path, char *permissions, Dbptr *db );
extern Dbptr srb_dblookup( Dbptr db, char *database_name, char *table_name, char *field_name, char *record_name );
