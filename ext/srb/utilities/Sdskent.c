
#include "scommands.h"
#include "datascopeSrbTools.h"

#define BUFSIZE         2097152

extern char srbAuth[];
extern char srbHost[];
extern char mdasCollectionName[];
extern char inCondition[];

srbConn *conn;
int  nbytes,  in_fd, out_fd;
char buf[BUFSIZE];
int i,j,k;

void
usage()
{
  fprintf(stderr, "Usage: Sdskent srbDatascopeObj\n");
}

int
main(int argc, char **argv)
{
    FILE * infile_fd, *fd;
    char targColl[MAX_TOKEN], targObj[MAX_TOKEN];
    int myrec;
    Dbptr db;

    if (argc != 2) 
      {usage();
      exit(1);
      }
    
    i = initSrbClientEnv();
   if (i < 0)
      {printf("Sdskent: Initialization Error:%i\n",i); exit(1);}

    conn = srbConnect (srbHost, NULL, srbAuth, 
     NULL, NULL, NULL, NULL);
    if (clStatus(conn) != CLI_CONNECTION_OK) {
        fprintf(stderr,"Sdskent: Connection to srbMaster failed.\n");
        fprintf(stderr,"Sdskent: %s",clErrorMessage(conn));
	srb_perror (2, clStatus(conn), "", SRB_RCMD_ACTION|SRB_LONG_MSG);
        clFinish(conn);
        exit(1);
    }
    splitpath(argv[1],targColl,targObj, '/');
    in_fd = srbObjOpen (conn, targObj,  O_RDONLY, targColl);
    if (in_fd < 0) {   /* error */
	fprintf(stderr, "Sdskent: can't open SRB obj \"%s/%s:%i\"\n",
		targColl,targObj,in_fd);
	fprintf(stderr,"Sdskent: %s",clErrorMessage(conn));
	srb_perror (2, in_fd, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
	clFinish(conn);
	exit(2);
    }
    else {
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
    }
    clFinish(conn);
    exit(0);
}
