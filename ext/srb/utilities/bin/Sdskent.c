#include "dssrb.h"

#define DBPTR_PRINT( DB, WHERE ) fprintf( stderr, "SCAFFOLD: dbptr at '%s' is %d %d %d %d\n", WHERE, (DB).database, (DB).table, (DB).field, (DB).record );
void
usage()
{
	fprintf(stderr, "Usage: Sdskent srbDatascopeObj\n");
}

int
main(int argc, char **argv)
{
	Dbptr 	db;
	int	rc;

    	if( argc != 2 ) {

		usage();
      		exit(1);
      	}
    
	if( 0 ) { 

		int 	arec;
		char	filename[FILENAME_MAX];

		srb_dbopen( argv[1], "r", &db );

		db = srb_dblookup( db, "", "images", "", "" );
		arec = srb_dbfind( db, "imagename == \"2002_07_20_frieder_gps\"", 0, 0 );
		db.record = arec;
		srb_dbfilename( db, filename );
		rc = srb_dbextfile( db, "images", filename );
		DBPTR_PRINT( db, "after extfile" );

	} else if( 0 ) {

		FILE 	*afile;
		int 	arec;

		srb_dbopen( argv[1], "r", &db );

		db = srb_dblookup( db, "", "images", "", "" );
		arec = srb_dbfind( db, "imagename == \"2002_07_20_frieder_gps\"", 0, 0 );
		db.record = arec;
		afile = fopen( "mess.jpg", "w+" );
		srb_dbfilename_retrieve( db, afile );
		fclose( afile );
		afile = fopen( "mess2.jpg", "w+" );
		srb_dbextfile_retrieve( db, "images", afile );
		fclose( afile );

	} else if( 0 ) {
		
		int 	nrecs;
		char	*astring;
		Tbl	*fields;
		Tbl	*link_tables;
		Arr	*links;
		int	i;

		srb_dbopen( argv[1], "r", &db );

		db = srb_dblookup( db, "", "origin", "", "" );
		fprintf( stderr, "Nrecs %d\n", srb_dbnrecs( db ) );
		srb_dbquery( db, dbRECORD_COUNT, &nrecs );
		fprintf( stderr, "Nrecs from direct dbquery: %d\n", nrecs );
		
		srb_dbquery( db, dbTABLE_DETAIL, &astring );
		fprintf( stderr, "table detail from direct dbquery: %s\n", astring );

		srb_dbquery( db, dbTABLE_FIELDS, &fields );
		printf( "Table fields:\n" );
		for( i=0; i<maxtbl( fields ); i++ ) {
			printf( "\t%s\n", gettbl( fields, i ) );
		}

		srb_dbquery( db, dbLINK_FIELDS, &links );
		printf( "Link fields:\n" );
		link_tables = keysarr( links );
		for( i=0; i<maxtbl( link_tables ); i++ ) {
			astring = gettbl( link_tables, i );
			printf( "\t%s\t%s\n", astring, getarr( links, astring ) );
		}

		db = srb_dblookup( db, "", "lastid", "", "" );
		srb_dbquery( db, dbLASTIDS, &links );
		printf( "Last IDs:\n" );
		link_tables = keysarr( links );
		for( i=0; i<maxtbl( link_tables ); i++ ) {
			astring = gettbl( link_tables, i );
			printf( "\t%s\t%s\n", astring, getarr( links, astring ) );
		}
	} else if( 0 ) {
		
		Tbl	*list;

		list = strtbl( "dbopen arrival", 
			       "dbjoin assoc", 
			       "dbjoin arrival",
			       "dbsubset sta == \"KBK\" || sta == \"AAK\"",
			       0 );

		srb_dbopen( argv[1], "r", &db );

		db = srb_dbprocess( db, list, 0 );
		fprintf( stderr, "Nrecs after srb_dbprocess: %d\n", srb_dbnrecs( db ) );

		fprintf( stderr, "Dbfree result is %d\n", srb_dbfree( db ) );

	} else if( 1 ) {

		int	nrecs;
		int 	rc = 0;

		srb_dbopen( argv[1], "r+", &db );

		db = srb_dblookup( db, "", "origin", "", "" );

		nrecs = srb_dbnrecs( db );
		fprintf( stderr, "Nrecs in origin %d\n", nrecs );
		
		db.record = 16;
		rc = srb_dbmark( db );
		fprintf( stderr, "dbmark rc %d\n", rc );
		rc = srb_dbcrunch( db );

		nrecs = srb_dbnrecs( db );
		fprintf( stderr, "Nrecs after mark/crunch %d with rc %d\n", nrecs, rc );
		
		db.record = 20;
		rc = srb_dbdelete( db );

		nrecs = srb_dbnrecs( db );
		fprintf( stderr, "Nrecs after dbdelete %d with rc %d\n", nrecs, rc );

		rc = srb_dbtruncate( db, 916 );
		nrecs = srb_dbnrecs( db );
		fprintf( stderr, "Nrecs after dbtruncate %d with rc %d\n", nrecs, rc );
	}

	srb_dbclose( db );

	clear_register( 1 );

    	exit(0);
}
