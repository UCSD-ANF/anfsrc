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

    	if( argc != 2 ) {

		usage();
      		exit(1);
      	}
    
	srb_dbopen( argv[1], "r", &db );

	printf( "SCAFFOLD: Got to mark with db.database = %d table = %d field = %d record = %d\n", 
		db.database, db.table, db.field, db.record );

/* SCAFFOLD 
        i = srbObjProc(conn, in_fd ,"dblookup||images||","", 0,buf, BUFSIZE);
        printf("afterproc dblookup:i=%i\n",i);
        i = srbObjProc(conn, in_fd ,"dbfind|imagename == \"2004_02_02_IQEye3\"|0","", 0,buf, BUFSIZE);
        printf("afterproc dbfind:i=%i\n",i);
        printf("afterproc dbfind returned buffer is %s\n",buf);
	sscanf( buf, "%i|%i|%i|%i|%i", &myrec, &db.database, &db.table, &db.field, &db.record );
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
