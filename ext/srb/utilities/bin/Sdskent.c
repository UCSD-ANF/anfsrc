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
    
	srb_dbopen( argv[1], "r", &db );

	db = srb_dblookup( db, "", "images", "", "" );

	if( 0 ) { 

		int 	myrec;
		char	filename[FILENAME_MAX];

		myrec = srb_dbfind( db, "imagename == \"2002_07_20_frieder_gps\"", 0, 0 );
		db.record = myrec;
		srb_dbfilename( db, filename );
		rc = srb_dbextfile( db, "images", filename );
		DBPTR_PRINT( db, "after_extfile" );

	} else if( 1 ) {

		FILE 	*myfile;
		int 	myrec;

		myrec = srb_dbfind( db, "imagename == \"2002_07_20_frieder_gps\"", 0, 0 );
		db.record = myrec;
		myfile = fopen( "mess.jpg", "w+" );
		srb_dbfilename_retrieve( db, myfile );
		fclose( myfile );
	}

	srb_dbclose( db );

	clear_register( 1 );

    	exit(0);
}
