#include "dssrb.h"

void
usage()
{
	fprintf(stderr, "Usage: Sdskent srbDatascopeObj\n");
}

int
main(int argc, char **argv)
{
	FILE 	*infile_fd;
	FILE	 *fd;
	int 	myrec;
	Dbptr 	db;
	char	filename[FILENAME_MAX];

    	if( argc != 2 ) {

		usage();
      		exit(1);
      	}
    
	srb_dbopen( argv[1], "r", &db );
	db = srb_dblookup( db, "", "images", "", "" );

	myrec = srb_dbfind( db, "imagename == \"2002_07_20_frieder_gps\"", 0, 0 );

	db.record = myrec;

	srb_dbfilename( db, filename );

	printf( "SCAFFOLD: Got to mark with db.database = %d table = %d field = %d record = %d; record is %d, filename %s\n", 
		db.database, db.table, db.field, db.record, myrec, filename );

	srb_dbclose( db );

/* SCAFFOLD 
	printf( "We got record %i\n", myrec ); fflush(stdout);
	db.record = myrec;
	dbPtr2str(&db,buf);
        i = srbObjProc(conn, in_fd ,"dbfilename_retrieve",buf, strlen(buf)+1,buf, BUFSIZE);
        printf("afterproc dbfilename_retrieve:i=%i\n",i); fflush( stdout );
	{
	FILE *myfile;
	myfile = fopen( "mess", "w+" );
	printf( "myfile is %x with %d\n", myfile, errno ); fflush( stdout );
	fwrite(buf, 1,i,myfile);
	fclose(myfile);
	}
	srbObjClose (conn, in_fd);
    	clFinish(conn);
*/
    	exit(0);
}
