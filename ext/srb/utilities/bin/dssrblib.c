#include "dssrb.h"

srbConn *conn;
int  nbytes,  in_fd, out_fd;
char buf[BUFSIZE];
int i,j,k;

int connectFlag = 0;

static int 
srb_init()
{
	int 	i;
	int 	c;
	int 	vFlag = 1;
	char 	svrVersion[MAX_TOKEN];
	char 	dummy1[MAX_TOKEN];
	char	dummy2[MAX_TOKEN];
	char	cliAPIVersion[MAX_TOKEN];
	char	svrAPIVersion[MAX_TOKEN];
   
	if( vFlag > 0 ) {

		dummy1[0] = '\0';

		cliAPIVersion[0] = '\0';

		splitString( SRB_VERSION, dummy1, cliAPIVersion, '&' );

		printf( "Client Release = %s, API version = %s.\n", 
	 		dummy1, cliAPIVersion );
	}

	i = firstInitSrbClientEnv();

	if( i < 0 ) {

		printf( "Error Opening Client Environment File:%i\n",i ); 
		
		return -1;
	}

	i = rewriteSrbClientEnvFile();

	if( i < 0 ) {

		printf( "Error Writing Client Environment File:%i\n",i ); 
		
		return -1;
	}

	i = initSrbClientEnv();

	if( i < 0 ) {

		printf("Error Opening Client Environment File:%i\n",i);
		 
		return -1;
	}

	conn = srbConnect( srbHost, NULL, srbAuth, NULL, NULL, NULL, NULL );

	if( clStatus( conn ) != CLI_CONNECTION_OK ) {

        	fprintf( stderr, "Connection to srbMaster failed.\n" );

        	fprintf( stderr, "%s", clErrorMessage( conn ) );

		srb_perror( 2, clStatus( conn ), "", SRB_RCMD_ACTION|SRB_LONG_MSG );

        	return -1;
	}

	if (vFlag > 0) {

		i = srbGetSvrVersion (conn, &svrVersion);

		if (i == 0) {

            		dummy2[0] = '\0';

            		svrAPIVersion[0] = '\0';

            		splitString (svrVersion, dummy2, svrAPIVersion, '&');

            		printf ("Server Release = %s, API version = %s.\n", 
             			dummy2, svrAPIVersion);

		} else {

	    		fprintf(stderr,"Unable to srbGetSvrVersion.\n");

	    		srb_perror (2, i, "", SRB_RCMD_ACTION|SRB_LONG_MSG);
		}
	}

	clFinish( conn );

	return 0;
}
    
int 
srb_dbopen( char *path, char *permissions, Dbptr *db ) 
{
	char 	targColl[MAX_TOKEN];
	char	targObj[MAX_TOKEN];
	char	*srbpath;
	int	rc;
	int 	i;

	*db = dbinvalid();

	if( ! strncmp( path, "srb:", 4 ) ) {

		srbpath = path + 4;

		printf( "SCAFFOLD: opening a SRB database\n" );

		srb_init();

		splitpath( srbpath,targColl,targObj, '/' );

		i = initSrbClientEnv();

		if( i < 0 ) {

			printf( "srb_dbopen: SRB Initialization Error:%i\n",i ); 

			return dbINVALID;
		}

		conn = srbConnect( srbHost, NULL, srbAuth, NULL, NULL, NULL, NULL );

		if( clStatus( conn ) != CLI_CONNECTION_OK ) {

			fprintf( stderr, "srb_dbopen: Connection to srbMaster failed.\n" );

			fprintf( stderr, "srb_dbopen: %s",clErrorMessage( conn ) );

			srb_perror( 2, clStatus( conn ), "", SRB_RCMD_ACTION|SRB_LONG_MSG );

			clFinish( conn );

			return dbINVALID;

		} else 	{
	
			connectFlag++;
		}	


    		in_fd = srbObjOpen( conn, targObj, O_RDONLY, targColl );

    		if( in_fd < 0 ) {   

			fprintf( stderr, "srb_dbopen: can't open SRB obj \"%s/%s:%i\"\n",
					targColl,targObj,in_fd );

			fprintf( stderr, "srb_dbopen: %s", clErrorMessage( conn ) );

			srb_perror( 2, in_fd, "", SRB_RCMD_ACTION|SRB_LONG_MSG );

			clFinish( conn );

			return dbINVALID;
    		}

        	i = srbObjProc( conn, in_fd ,"get_dbptr","", 0,buf, BUFSIZE );

		str2dbPtr( buf, db );

	} else {

		rc = dbopen( path, permissions, db ); 
	}

	return rc;
}

Dbptr
srb_dblookup( Dbptr db, char *database_name, char *table_name, char *field_name, char *record_name )
{
}

