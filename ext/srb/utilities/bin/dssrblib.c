#include "dssrb.h"

srbConn *conn;
int  nbytes,  in_fd, out_fd;
char inbuf[BUFSIZE];
char outbuf[BUFSIZE];
int i,j,k;

int connectFlag = 0;

static int
is_srb_database( Dbptr dbexternal, Dbptr *dbinternal )
{
	*dbinternal = dbexternal;

	if( dbexternal.database >= SRB_DATABASES ) {
		
		dbinternal->database = dbexternal.database - SRB_DATABASES;

		return 1;

	} else {

		return 0;
	}
}

static Dbptr
cast_srb_dbptr_to_external( Dbptr dbinternal ) 
{
	Dbptr	dbexternal;
	
	dbexternal = dbinternal;

	if( dbinternal.database >= 0 ) {

		dbexternal.database = dbinternal.database + SRB_DATABASES;
	}

	return dbexternal;
}

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

		printf( "SCAFFOLD: opening a SRB Datascope database\n" );

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

        	i = srbObjProc( conn, in_fd ,"get_dbptr","", 0,outbuf, BUFSIZE );

		str2dbPtr( outbuf, db );

		*db = cast_srb_dbptr_to_external( *db );
	
	} else {

		printf( "SCAFFOLD: opening a native Datascope database\n" );

		rc = dbopen( path, permissions, db ); 
	}

	return rc;
}

Dbptr
srb_dblookup( Dbptr db, char *database_name, char *table_name, 
			char *field_name, char *record_name )
{
	char	*command;
	int	i;

	/* SCAFFOLD need to look up the SRB connection in a hash of some sort
	   (now supports one connection only) */

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 5, "dblookup",
					   database_name,
					   table_name, 
					   field_name,
					   record_name );

		i = srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		str2dbPtr( outbuf, &db );

		db = cast_srb_dbptr_to_external( db );
	
	} else {
		
		db = dblookup( db, database_name, table_name, field_name, record_name );
	}

	return db;
}

int
srb_dbfind( Dbptr db, char *string, int flags, Hook **hook )
{
	char	flag_string[STRSZ];
	char	*command;
	int	rc;
	int	i;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		sprintf( flag_string, "%i", flags );

		command = putArgsToString( DSDELIM, DSESC, 3, "dbfind", string, flag_string );

		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		rc = atoi( outbuf );

	} else {
		
		rc = dbfind( db, string, flags, hook );
	}

	return rc;
}

int
srb_dbclose( Dbptr db )
{
	char	*command;
	int	rc;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 1, "dbclose" );

		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		rc = atoi( outbuf );

		srbObjClose( conn, in_fd );

		clFinish( conn );

	} else {
		
		rc = dbclose( db );
	}

	return rc;
}

int
srb_dbfilename( Dbptr db, char *filename )
{
	char	*command;
	char	*results[MAX_PROC_ARGS_FOR_DS];
	int	rc;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 1, "dbfilename" );

		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		if( getArgsFromString( outbuf, results, DSDELIM, DSESC ) != 2 ) {

			register_error( 0, "Problems parsing result in srb_dbfilename\n" );

			strcpy( filename, "" );

			rc = -2;

		} else {

			rc = atoi( results[0] );

			strcpy( filename, results[1] );
		}

	} else {
		
		rc = dbfilename( db, filename );
	}

	return rc;
}

int
srb_dbextfile( Dbptr db, char *tablename, char *filename )
{
	char	*command;
	char	*results[MAX_PROC_ARGS_FOR_DS];
	int	rc;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 2, "dbextfile", tablename );
		
		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		if( getArgsFromString( outbuf, results, DSDELIM, DSESC ) != 2 ) {

			register_error( 0, "Problems parsing result in srb_dbextfile\n" );

			strcpy( filename, "" );

			rc = -2;

		} else {

			rc = atoi( results[0] );

			strcpy( filename, results[1] );
		}

	} else {
		
		rc = dbextfile( db, tablename, filename );
	}

	return rc;
}

int 
srb_dbfilename_retrieve( Dbptr db, FILE *fp )
{
	FILE	*fp_native;
	char	filename[FILENAME_MAX];
	char	*command;
	size_t 	count;
	int	rc;

	if( is_srb_database( db, &db ) ) {

		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 1, "dbfilename_retrieve" );

		count = srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		if( count > 0 ) {

			fwrite( outbuf, 1, count, fp );

			if( count == BUFSIZE ) {

				while( ( count = srbObjRead( conn, in_fd, outbuf, BUFSIZE ) ) > 0 ) {
					
					fwrite( outbuf, 1, count, fp );
				}
			}

		} else {

			register_error( 0, "srb_dbfilename_retrieve: no data returned\n" );
			return -1;
		}

	} else {

		rc = dbfilename( db, filename );

		if( rc < 0 ) {
			
			register_error( 0, 
				"srb_dbfilename_retrieve: file does not exist\n" );
			return -1;
		}

		fp_native = fopen( filename, "r" );
		
		while( ! feof( fp_native ) && ! ferror( fp_native ) ) {
			
			count = fread( outbuf, 1, 1, fp_native );
			fwrite( (const char *) outbuf, 1, count, fp );
			
			if( ferror( fp ) ) {
				register_error( 0, 
				"srb_dbfilename_retrieve: error writing to output file\n" );
				fclose( fp_native );
				return -1;
			}
		}

		if( ferror( fp_native ) ) {
			register_error( 0, 
				"srb_dbfilename_retrieve: error reading from input file\n" );
			fclose( fp_native );
			return -1;
		}

		fclose( fp_native );
	}

	return 0;
}

int 
srb_dbextfile_retrieve( Dbptr db, char *tablename, FILE *fp )
{
	FILE	*fp_native;
	char	filename[FILENAME_MAX];
	char	*command;
	size_t 	count;
	int	rc;

	if( is_srb_database( db, &db ) ) {

		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 2, "dbextfile_retrieve", tablename );

		count = srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		if( count > 0 ) {

			fwrite( outbuf, 1, count, fp );

			if( count == BUFSIZE ) {

				while( ( count = srbObjRead( conn, in_fd, outbuf, BUFSIZE ) ) > 0 ) {
					
					fwrite( outbuf, 1, count, fp );
				}
			}

		} else {

			register_error( 0, "srb_dbextfile_retrieve: no data returned\n" );
			return -1;
		}

	} else {

		rc = dbextfile( db, tablename, filename );

		if( rc < 0 ) {
			
			register_error( 0, 
				"srb_dbextfile_retrieve: file does not exist\n" );
			return -1;
		}

		fp_native = fopen( filename, "r" );
		
		while( ! feof( fp_native ) && ! ferror( fp_native ) ) {
			
			count = fread( outbuf, 1, 1, fp_native );
			fwrite( (const char *) outbuf, 1, count, fp );
			
			if( ferror( fp ) ) {
				register_error( 0, 
				"srb_dbextfile_retrieve: error writing to output file\n" );
				fclose( fp_native );
				return -1;
			}
		}

		if( ferror( fp_native ) ) {
			register_error( 0, 
				"srb_dbextfile_retrieve: error reading from input file\n" );
			fclose( fp_native );
			return -1;
		}

		fclose( fp_native );
	}

	return 0;
}

int
srb_dbnrecs( Dbptr db )
{
	char	*command;
	int	nrecs;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, 2, "dbquery", "dbRECORD_COUNT" );

		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		nrecs = atoi( outbuf );

	} else {
		
		dbquery( db, dbRECORD_COUNT, &nrecs );
	}

	return nrecs;
}

int
srb_dbquery( Dbptr db, int code, Dbvalue *value )
{
	char	*command;
	char	*code_string;
	int	rc;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );

		code_string = xlatnum( code, Dbxlat, NDbxlat );
	
		command = putArgsToString( DSDELIM, DSESC, 2, "dbquery", code_string );

		rc = srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		if( rc >= 0 ) {
			
			switch( code ) {
			case dbDATABASE_COUNT:
			case dbTABLE_COUNT:
			case dbFIELD_COUNT:
			case dbRECORD_COUNT:
			case dbTABLE_SIZE:
			case dbFIELD_SIZE:
			case dbRECORD_SIZE:
			case dbFIELD_TYPE:
			case dbFIELD_INDEX:
			case dbVIEW_TABLE_COUNT:
			case dbTABLE_IS_VIEW:
			case dbTABLE_IS_WRITABLE:
			case dbTABLE_IS_ADDABLE:
			case dbDATABASE_IS_WRITABLE:
			case dbTABLE_ADDRESS:
			case dbTABLE_IS_TRANSIENT:
			case dbLOCKS:
				value->i = atoi( outbuf );
				break;
			case dbSCHEMA_DESCRIPTION:
			case dbDATABASE_DESCRIPTION:
			case dbTABLE_DESCRIPTION:
			case dbFIELD_DESCRIPTION:
			case dbSCHEMA_DETAIL:
			case dbDATABASE_DETAIL:
			case dbTABLE_DETAIL:
			case dbFIELD_DETAIL:
			case dbSCHEMA_NAME:
			case dbDATABASE_NAME:
			case dbTABLE_NAME:
			case dbFIELD_NAME:
			case dbFIELD_FORMAT:
			case dbFIELD_UNITS:
			case dbNULL:
			case dbFIELD_RANGE:
			case dbDATABASE_FILENAME:
			case dbTABLE_FILENAME:
			case dbTABLE_DIRNAME:
			case dbDBPATH:
			case dbFORMAT:
			case dbUNIQUE_ID_NAME:
			case dbFIELD_BASE_TABLE:
			case dbTIMEDATE_NAME:
			case dbIDSERVER:
				value->t = strdup( outbuf );
				break;
			case dbVIEW_TABLES:
			case dbPRIMARY_KEY:
			case dbALTERNATE_KEY:
			case dbFOREIGN_KEYS:
			case dbTABLE_FIELDS:
			case dbFIELD_TABLES:
			case dbSCHEMA_FIELDS:
			case dbSCHEMA_TABLES:
				value->tbl = str2dbTable( outbuf );
				break;
			case dbLINK_FIELDS:
			case dbLASTIDS:
				value->arr = str2dbArray( outbuf );
				break;
			default:
				register_error( 0,
						"srb_dbquery: code %d not understood\n",
						code );
				break;
			 }

		} else {

			value = (Dbvalue *) NULL;
		}

	} else {
		
		rc = dbquery( db, code, value );
	}

	return rc;
}

Dbptr
srb_dbprocess( Dbptr db, Tbl *list, Dbptr (*unknown)() )
{
	char	*command;
	char	*statements;
	void	*vstack = 0;
	int	i;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );

		for( i = 0; i < maxtbl( list ); i++ ) {

			pushstr( &vstack, gettbl( list, i ) );

			if( i < maxtbl( list ) - 1 ) {

				pushstr( &vstack, ";;" );
			}
		}

		statements = popstr( &vstack, 1 );
	
		command = putArgsToString( DSDELIM, DSESC, 2, "dbprocess", statements );

		free( statements );

		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

		str2dbPtr( outbuf, &db );

		db = cast_srb_dbptr_to_external( db );
	
	} else {
		
		db = dbprocess( db, list, unknown );
	}

	return db;
}

/* 
int
srb_TEMPLATE( Dbptr db, TEMPLATE )
{
	char	*command;
	int	rc;

	if( is_srb_database( db, &db ) ) {
		
		dbPtr2str( &db, inbuf );
	
		command = putArgsToString( DSDELIM, DSESC, TEMPLATE_N, "TEMPLATE", TEMPLATE );

		srbObjProc( conn, in_fd, command, inbuf, strlen( inbuf ) + 1, outbuf, BUFSIZE );

	} else {
		
		rc = TEMPLATE( db, TEMPLATE );
	}

	return rc;
}
*/
