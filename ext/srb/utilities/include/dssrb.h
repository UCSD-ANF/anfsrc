#ifndef DSSRB_H
#define DSSRB_H

#include "scommands.h"
#include "datascopeSrbTools.h"

#define BUFSIZE         2097152
#define SRB_DATABASES	1000000

extern char srbAuth[];
extern char srbHost[];
extern char mdasCollectionName[];
extern char mdasCollectionHome[];
extern char inCondition[];

extern int srb_dbopen( char *path, char *permissions, Dbptr *db );
extern int srb_dbclose( Dbptr db );
extern Dbptr srb_dblookup( Dbptr db, char *database_name, char *table_name, char *field_name, char *record_name );
extern int srb_dbfind( Dbptr db, char *string, int flags, Hook **hook );
extern int srb_dbfilename( Dbptr db, char *filename );
extern int srb_dbfilename_retrieve( Dbptr db, FILE *fp );
extern int srb_dbextfile_retrieve( Dbptr db, char *tablename, FILE *fp );
extern int srb_dbnrecs( Dbptr db );
extern Dbptr srb_dbprocess( Dbptr db, Tbl *list, Dbptr (*unknown)() );

#endif /* DSSRB_H */
