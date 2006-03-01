
/*
 *   Copyright (c) 2005 Lindquist Consulting, Inc.
 *   All rights reserved. 
 *                                                                     
 *   Written by Dr. Kent Lindquist, Lindquist Consulting, Inc. 
 * 
 *   This software may be used freely in any way as long as 
 *   the copyright statement above is not removed. 
 *
 */

#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <errno.h>

#include "Pkt.h"
#include "orb.h"
#include "forb.h"
#include "coords.h"
#include "stock.h"
#include "tr.h"
#include "libuser.h"

#define VERY_LARGE_NUMBER   1e36
#define IMG_SCHEMA "Images1.0"

typedef struct Flags {
	unsigned int    verbose:2;
	unsigned int    cleanup:2;
	unsigned int    thumbnails:2;
	unsigned int    videoframes:2;
	unsigned int    autosite:2;
}               Flags;

typedef struct EipBlock {
	int	nparts;
	Bitvector *current;
	Bitvector *final; 
	Tbl	*parts;
} EipBlock;

static void
usage ()
{
	fprintf (stderr, "\nUsage: %s [-p pfname] [-m match] [-r reject] [-n maxpkts] "
		"[-S statefile] [-v] [-t] [-f] [-c] [-s] "
		"orb db [start-time [period|end-time]]\n", Program_Name);
	exit (1);
}

static void
cleanup_database( Dbptr db, int interval_sec, Arr *expressions, int verbose )
{
	static double last_cleanup = 0;
	Expression *ex = 0;
	Tbl	*keys;
	char	*atable;
	char	*anexpr;
	char	filename[FILENAME_MAX];
	int	itable;
	int	matches_remove_expr;
	int	nrecs; 
	int	nremoved;
	int	nerrors;
	int	rc;

	if( now() - last_cleanup < (double) interval_sec ) {

		return;
	}

	keys = keysarr( expressions );
	
	for( itable = 0; itable < maxtbl( keys ); itable++ ) {
		
		atable = gettbl( keys, itable );

		anexpr = getarr( expressions, atable );

		if( verbose ) {
			elog_notify( 0, "Using expression '%s' to clean up table %s\n", anexpr, atable );
		}

		db = dblookup( db, "", atable, "", "" );

		if( db.table < 0 ) {
			elog_complain( 0, "Failed to lookup table '%s' for cleanup in database\n", atable );
			continue;
		}

		dbex_compile( db, anexpr, &ex, dbBOOLEAN );

		dbquery( db, dbRECORD_COUNT, &nrecs );

		nremoved = 0;
		nerrors = 0;

		for( db.record = 0; db.record < nrecs; db.record++ ) {

			dbex_eval( db, ex, 0, &matches_remove_expr );

			if( matches_remove_expr ) {

				dbfilename( db, filename );
				dbmark( db ); 

				rc = unlink( filename );

				if( rc ) {

					elog_complain( 1, "Failed to remove extfile '%s' (removing record from table %s anyway)\n", filename, atable );
					nerrors++;

				} else {

					if( verbose ) {

						elog_notify( 0, "Removed extfile '%s' (table %s)\n", filename, atable );
					}

					nremoved++;
				}
			}
		}

		dbcrunch( db );

		if( verbose ) {

			elog_notify( 0, "Removed %d files and %d rows for table '%s' with %d errors\n",
					nremoved, nremoved + nerrors, atable, nerrors );
		}

		dbex_free( ex );
		ex = (Expression *) NULL;
	}

	last_cleanup = now();

	return;
}

int 
deduce_magic_format( ExpImgPacket *eip, char *format )
{

	if( ! strncmp( eip->blob, "\377\330", 2 ) ) {

		strcpy( format, "jpeg" );
		return 0;

	} else if( ! strncmp( eip->blob, "GIF", 3 ) ) {

		strcpy( format, "gif" );
		return 0;

	} else if( ! strncmp( eip->blob, "\115\115", 2 ) ) {

		strcpy( format, "tiff" ); /* Big-endian */
		return 0;

	} else if( ! strncmp( eip->blob, "\111\111", 2 ) ) {

		strcpy( format, "tiff" ); /* Little-endian */
		return 0;

	} else if( ! strncmp( eip->blob, "\211PNG\r\n\032\n", 8 ) ) {

		strcpy( format, "png" ); 
		return 0;

	} else if( ! strncmp( eip->blob, "P4", 2 ) ) {

		strcpy( format, "pbm" ); 
		return 0;

	} else if( ! strncmp( eip->blob, "P5", 2 ) ) {

		strcpy( format, "pgm" ); 
		return 0;

	} else if( ! strncmp( eip->blob, "P6", 2 ) ) {

		strcpy( format, "ppm" ); 
		return 0;

	} else {

		strcpy( format, "UNKNOWN" );

		return -1;
	}
}

EipBlock *
new_eipblock()
{
	EipBlock *eb;
	int	ibit;

	allot( EipBlock *, eb, 1 );

	eb->nparts = 0;

	eb->current = bitnew();

	for( ibit = 0; ibit < bitmax( eb->current ); ibit++ ) {

		bitclr( eb->current, ibit );
	}

	eb->final = bitnew();

	for( ibit = 0; ibit < bitmax( eb->final ); ibit++ ) {

		bitclr( eb->final, ibit );
	}

	eb->parts = newtbl( 0 );

	return eb;
}

void
free_eipblock( EipBlock *eb )
{
	if( eb->current != (Bitvector *) NULL ) {

		bitfree( eb->current );
	}
	
	if( eb->final != (Bitvector *) NULL ) {

		bitfree( eb->final );
	}
	
	if( eb->parts != (Bitvector *) NULL ) {

		freetbl( eb->parts, (void (*)(void *)) free_expimgpacket );
	}
}

ExpImgPacket *
cache_multipart_eip( char *srcname, double time, ExpImgPacket *eip )
{
	char	key[STRSZ];
	static Arr *blocks = 0;
	EipBlock *eb;
	ExpImgPacket *part = 0;
	ExpImgPacket *finished = 0;
	int	ifragment;

	if( blocks == (Arr *) NULL ) {
		
		blocks = newarr( 0 );
	}

	sprintf( key, "%s:%17.5lf", srcname, time );

	if( ( eb = getarr( blocks, key ) ) == (EipBlock *) NULL ) {

		eb = new_eipblock();

		eb->nparts = eip->nfragments;

		for( ifragment = 0; ifragment < eip->nfragments; ifragment++ ) {
			
			bitset( eb->final, ifragment );
		}

		setarr( blocks, key, (void *) eb );
	}

	settbl( eb->parts, eip->ifragment - 1,  dup_expimgpacket( eip ) );

	bitset( eb->current, eip->ifragment - 1 );

	if( bitcmp( eb->current, eb->final ) == 0 ) {

		finished = new_expimgpacket();

		for( ifragment = 0; ifragment < eb->nparts; ifragment++ ) {

			part = gettbl( eb->parts, ifragment );

			if( ifragment == 0 ) {

				strcpy( finished->format, part->format );
				strcpy( finished->description, part->description );
			}

			finished->blob_size += part->blob_size;
		}

		finished->blob_bufsz = finished->blob_size;

		allot( char *, finished->blob, finished->blob_bufsz );

		for( ifragment = 0; ifragment < eb->nparts; ifragment++ ) {
			
			part = gettbl( eb->parts, ifragment );

			memcpy( finished->blob + part->blob_offset, 
				part->blob, 
				part->blob_size );
		}

		finished->ifragment = 1;
		finished->nfragments = 1;

		return finished;

	} else {

		return (ExpImgPacket *) NULL; 
	}
}

int
main (int argc, char **argv)
{
	int	c;
	int	errflg = 0;
	char	*orbname;
	char	*dbname;
	int	orbfd;
	Dbptr	db;
	Dbptr	dbt;
	Dbptr	dbsite;
	Arr	*sites = 0;
	int	nsites;
	double	*timep;
	Pf	*pf;
	char	*pfname = "orbimg2db";
	double	maxpkts = VERY_LARGE_NUMBER ;
	int	quit = 0;
	char	*match = 0;
	char	*reject = 0;
	int	nmatch = 0;
	int	specified_after = 0;
	double	after = 0.0;
	double	until = VERY_LARGE_NUMBER;
	double	start_time;
	double	end_time;
	double	delta_t;
	double	totpkts = 0;
	double	totbytes = 0;
	Flags	flags;
	static int last_pktid = -1;
	static double last_pkttime = 0.0;
	char	*statefile = 0;
	double	last_burial = 0.0;
	double	decent_interval = 300.0;
	int	mode = PKT_NOSAMPLES;
	int	rcode;
	int	cleanup_interval_sec;
	Srcname default_src;
	Arr	*cleanup_expressions;
	char	srcname[ORBSRCNAME_SIZE];
	char	*nocode_srcname;
	char	*sp;
	char	image_format[STRSZ];
	char	*default_suffix;
	char	*image_filenames;
	char	*thumbnail_filenames;
	char	*thumbnail_size;
	char	*thumbnail_command;
	char	*videoframe_filenames;
	char	*videoframe_size;
	char	*videoframe_format;
	char	*videoframe_command;
	char	filename_formatstr[STRSZ];
	char	*imgfilepath = 0;
	char	*thumbfilepath = 0;
	char	*framefilepath = 0;
	double	pkttime = 0.0 ;
	int	pktid;
	int	nbytes;
	char	*packet = 0;
	int	packetsz = 0;
	Packet	*unstuffed = 0;
	Tbl	*mytbl;
	FILE	*fp;
	char	*schema_name;
	ExpImgPacket *eip;
	int	alloted_joined_image = 0;
	char	cmd[STRSZ];
	char	*s;
	char	*hex;
	int 	rc;

	memset (&flags, 0, sizeof (flags));
	elog_init (argc, argv);

	elog_notify (0, "%s $Revision: 1.15 $ $Date: 2006/03/01 06:16:12 $\n",
		 Program_Name);

	while ((c = getopt (argc, argv, "p:m:n:r:S:ctfvs")) != -1) {
		switch (c) {
		case 'c':
			flags.cleanup++;
			break;

		case 'f':
			flags.videoframes++;
			break;

		case 'm':
			match = optarg;
			break;

		case 'n':
			maxpkts = atoi (optarg);
			break;

		case 'p': 
			pfname = optarg;
			break;

		case 'r':
			reject = optarg;
			break;

		case 's':
			flags.autosite++;
			break;

		case 'S':
			statefile = optarg;
			break;

		case 't':
			flags.thumbnails++;
			break;

		case 'v':
			flags.verbose++;
			break;

		case 'V':
	    		usage ();
			break;

		case '?':
			errflg++;
		}
	}

	if (errflg || argc - optind < 2 || argc - optind > 4)
	usage ();

	orbname = argv[optind++];
	dbname = argv[optind++];

	if (argc > optind) {
		after = str2epoch (argv[optind++]);
		specified_after = 1;
		if (argc > optind) {
			until = str2epoch (argv[optind++]);
			if (until < after) {
			until += after ;
			}
		}
	}
	if ((orbfd = orbopen (orbname, "r&")) < 0)
	die (0, "Can't open input '%s'\n", orbname);

	if (statefile != 0) {
		if (exhume (statefile, &quit, RT_MAX_DIE_SECS, 0) != 0) {
	    		if( flags.verbose ) {
				elog_notify (0, "read old state file\n");
			}
		}
		if (orbresurrect (orbfd, &last_pktid, &last_pkttime) == 0) {
			if( flags.verbose ) {
	    			elog_notify (0, "resurrection successful: repositioned to pktid #%d @ %s\n",
			 	last_pktid, s = strtime (last_pkttime));
			}
	    	free (s);
		} else {
	    		elog_complain (0, "resurrection unsuccessful\n");
		}
	}

	if( pfread( pfname, &pf ) < 0 ) {
		die( 1, "Error reading parameter-file '%s'\n", pfname );
	}

	if( ( default_suffix = pfget_string( pf, "default_suffix" ) ) == 0 ) {
		die( 0, "Missing 'default_suffix' parameter\n" );
	}

	split_srcname( default_suffix, &default_src );

	if( ( image_filenames = pfget_string( pf, "image_filenames" ) ) == 0 ) {
		die( 0, "Missing 'image_filenames' parameter\n" );
	}

	if( flags.cleanup ) {
		cleanup_interval_sec = pfget_int( pf, "cleanup_interval_sec" );

		cleanup_expressions = pfget_arr( pf, "cleanup_expressions" );
	}

	if( flags.thumbnails ) {

		if( (thumbnail_filenames = pfget_string( pf, "thumbnail_filenames" )) == 0 ) {
			die( 0, "-t option requires 'thumbnail_filenames' parameter\n" );
		}
		if( (thumbnail_size = pfget_string( pf, "thumbnail_size" )) == 0 ) {
			die( 0, "-t option requires 'thumbnail_size' parameter\n" );
		}
		if( (thumbnail_command = pfget_string( pf, "thumbnail_command" )) == 0 ) {
			die( 0, "-t option requires 'thumbnail_command' parameter\n" );
		}
	}

	if( flags.videoframes ) {

		if( (videoframe_filenames = pfget_string( pf, "videoframe_filenames" )) == 0 ) {
			die( 0, "-f option requires 'videoframe_filenames' parameter\n" );
		}
		if( (videoframe_size = pfget_string( pf, "videoframe_size" )) == 0 ) {
			die( 0, "-f option requires 'videoframe_size' parameter\n" );
		}
		if( (videoframe_format = pfget_string( pf, "videoframe_format" )) == 0 ) {
			die( 0, "-f option requires 'videoframe_format' parameter\n" );
		}
		if( (videoframe_command = pfget_string( pf, "videoframe_command" )) == 0 ) {
			die( 0, "-f option requires 'videoframe_command' parameter\n" );
		}
	}

	if( dbcreate( dbname, IMG_SCHEMA, 0, 0, 0 ) != 0 ) {

		die( 1, "Failed to create new database %s in schema %s\n", dbname, IMG_SCHEMA );
	}

	if ((dbopen (dbname, "r+", &db)) < 0) {
		die (1, "Can't open output '%s'\n", dbname);
	}

	dbquery( db, dbSCHEMA_NAME, &schema_name );
	if( strcmp( schema_name, IMG_SCHEMA ) != 0 ) {
		die( 1, "%s is not in %s schema\n", dbname, IMG_SCHEMA );
	} 
	db = dblookup( db, 0, "images", 0, 0 );

	if( flags.autosite ) {
		
		sites = newarr( 0 );

		dbsite = dblookup( db, 0, "site", 0, 0 );
		
		dbquery( dbsite, dbRECORD_COUNT, &nsites );
		
		for( dbsite.record = 0; dbsite.record < nsites; dbsite.record++ ) {
			
			allot( double *, timep, 1 );
			
			dbgetv( dbsite, 0, "imagename", srcname, 
					   "time", timep, 0 );

			setarr( sites, srcname, timep );
		}
	}

	if( flags.cleanup ) {
		cleanup_database( db, cleanup_interval_sec, 
				  cleanup_expressions, flags.verbose );
	}

	if (match) {
		nmatch = orbselect (orbfd, match);
	}
	if (nmatch < 0) {
		die (1, "select '%s' returned %d\n", match, nmatch);
	}
	if (reject) {
		nmatch = orbreject (orbfd, reject);
	}
	if (nmatch < 0) {
		die (1, "reject '%s' returned %d\n", reject, nmatch);
	} 
	if( match || reject ) {
		if( flags.verbose ) {
			elog_notify ( 0, "%d sources selected\n", nmatch);
		}
	}

	if( match == NULL && default_suffix != NULL ) {
		sprintf( srcname, ".*%s", default_suffix );

		nmatch = orbselect( orbfd, srcname );
		if( flags.verbose ) {
			elog_notify( 0, "%d sources selected of type %s\n", nmatch, default_suffix );
		}
	}

	if (specified_after) {
		pktid = orbafter (orbfd, after);
		if (pktid < 0) {
	    		elog_complain (1, "seek to %s failed\n", s = strtime (after));
	    		free (s);
	    		pktid = forbtell (orbfd);
	    		if( flags.verbose ) {
				elog_notify( 0,"pktid is still #%d\n", pktid);
			}
		} else {
			if( flags.verbose ) {
	    			elog_notify( 0, "new starting pktid is #%d\n", pktid);
			}
		}
	}
	start_time = now ();
	while (!quit && pkttime < until && totpkts < maxpkts) {
		rcode = orbreap (orbfd,
		    	&pktid, srcname, &pkttime, &packet, &nbytes, &packetsz);

		switch (rcode) {
	  	case 0:
			totpkts++;
			totbytes += nbytes;

			if (statefile != 0
		    		&& last_pkttime - last_burial > decent_interval) {
				bury ();
				last_burial = pkttime;
	    		}
	    		switch (unstuffPkt (srcname, pkttime, packet, nbytes, &unstuffed)) {
			case -1:
				complain( 1, "Packet-unstuff failed for %s, %s\n", srcname, s = strtime( pkttime ) );
				free( s );
				continue;
	      		case Pkt_wf:
	      		case Pkt_db:
	      		case Pkt_pf:
	      		case Pkt_ch:
	      		case Pkt_tp:
	      		default:
				break;
	    		}

	        	if( strcmp( unstuffed->parts.src_suffix, default_src.src_suffix ) || 
			    strcmp( unstuffed->parts.src_subcode, default_src.src_subcode ) ) {

				continue;
	    		}

	    		if (flags.verbose) {
				showPkt (pktid, srcname, pkttime, packet, nbytes, stdout, mode);
	    		}

	    		nocode_srcname = strdup( srcname );
	    		mytbl = split( nocode_srcname, '/' );
	    		freetbl( mytbl, 0 );

	    		eip = unstuffed->pkthook->p;

			if( eip->blob_size <= 0 ) {
				
				complain( 0, "Received zero-length image %s timestamped %s ; skipping\n", srcname, s = strtime( pkttime ) );
				free( nocode_srcname );
				free( s );
				continue;
			}

			alloted_joined_image = 0;

			if( eip->nfragments != 1 ) {

				if( flags.verbose ) {
					
					elog_notify( 0, "Received multipart "
					  "image segment %s timestamped %s, "
					  "fragment %d of %d); caching\n", 
					  srcname, 
					  s = strtime( pkttime ), 
					  eip->ifragment, 
					  eip->nfragments );
					free( s );
				}

				eip = cache_multipart_eip( srcname, pkttime, eip );

				if( eip == (ExpImgPacket *) NULL ) {

					free( nocode_srcname );
					continue;

				}  else {

					if( flags.verbose ) {
						elog_notify( 0, "Finished "
						"assembling image %s "
						"timestamped %s\n", 
						srcname, 
						s = strtime( pkttime ) );
						free( s );
					}

					alloted_joined_image = 1;
				}
			}

			if( ! strcmp( eip->format, "" ) ) {

				if( deduce_magic_format( eip, image_format ) != 0 ) {
					
					complain( 0, "Failed to deduce format of image %s timestamped %s, "
						     "starting with\n%s\n", 
						     srcname, s = strtime( pkttime ), 
						     hex = hexdump_string( 0, eip->blob, 8 ) );
					free( s );
					free( hex );
					free( nocode_srcname );
				}

			} else { 
				
				strcpy( image_format, eip->format );
			}

	    		db = dblookup( db, "", "", "", "dbSCRATCH" );

	    		dbputv( db, 0, "imagename", nocode_srcname, 
		       		"time", pkttime, 
		       		"format", image_format,
		       		"description", eip->description,
		       		0 );

	    		strcpy( filename_formatstr, image_filenames );
	    		trwfname( db, filename_formatstr, &imgfilepath );

	    		fp = fopen( imgfilepath, "w" );

	    		if( fp == (FILE *) NULL ) {

				complain( 1, "Failed to open %s for writing\n", imgfilepath );
				free( imgfilepath );
				imgfilepath = 0;

				free( nocode_srcname );

				if( alloted_joined_image ) {
					
					free_expimgpacket( eip );
				}

				continue;

	    		} else {

	    			fwrite( eip->blob, sizeof( char ), eip->blob_size, fp );
	    			fclose( fp );
	    		}

			if( alloted_joined_image ) {
				
				free_expimgpacket( eip );
			}

	    		dbadd( db, 0 );

			if( flags.autosite ) {

				if( getarr( sites, nocode_srcname ) == NULL ) {

					rc = dbaddv( dbsite, 0, 
						"imagename", nocode_srcname,
						"time", pkttime, 0 );

					if( rc < 0 ) {
						
						elog_complain( 0, "Failed to add site '%s' to "
							"site table!\n", nocode_srcname );

					} else {

						allot( double *, timep, 1 );

						*timep = pkttime;

						setarr( sites, nocode_srcname, timep );

						if( flags.verbose ) {
							
							elog_notify( 0, "Added imagename '%s' "
							"starting at %s UTC to site table\n",
							nocode_srcname, s = strtime( *timep ) );

							free( s );
						}
					}
				}
			}

			if( flags.thumbnails ) {

				dbt = dblookup( db, "", "thumbnails", "", "dbSCRATCH" );

	    			dbputv( dbt, 0, "imagename", nocode_srcname, 
		       			"time", pkttime, 
					"imagesize", thumbnail_size,
		       			"format", image_format,
		       			0 );

		    		strcpy( filename_formatstr, thumbnail_filenames );
		    		trwfname( dbt, filename_formatstr, &thumbfilepath );

				sprintf( cmd, "%s %s %s", thumbnail_command, 
						imgfilepath, thumbfilepath );
				
				free( thumbfilepath );
				thumbfilepath = 0;

				if( flags.verbose ) {
					elog_notify( 0, "Executing '%s'\n", cmd );
				}

				rcode = system( cmd );
				
				if( rcode ) {
					complain( 1, "Failed to create thumbnail with command '%s'\n", cmd );
				} else {

					dbadd( dbt, 0 );
				}
			}

			if( flags.videoframes ) {

				dbt = dblookup( db, "", "frames", "", "dbSCRATCH" );

	    			dbputv( dbt, 0, "imagename", nocode_srcname, 
		       			"time", pkttime, 
					"imagesize", videoframe_size,
		       			"format", videoframe_format,
		       			0 );

		    		strcpy( filename_formatstr, videoframe_filenames );
		    		trwfname( dbt, filename_formatstr, &framefilepath );

				sprintf( cmd, "%s %s %s", videoframe_command, 
						imgfilepath, framefilepath );
				
				free( framefilepath );
				framefilepath = 0;

				if( flags.verbose ) {
					elog_notify( 0, "Executing '%s'\n", cmd );
				}

				rcode = system( cmd );
				
				if( rcode ) {
					complain( 1, "Failed to create videoframe with command '%s'\n", cmd );
				} else {

					dbadd( dbt, 0 );
				}
			}

			if( imgfilepath != NULL ) {

				free( imgfilepath );
				imgfilepath = 0;
			}

			free( nocode_srcname );

	    		last_pktid = pktid;
	    		last_pkttime = pkttime;
	    		break;

	  	default:
	    		break;
		}

		if( flags.cleanup ) {
			cleanup_database( db, cleanup_interval_sec, 
				  	cleanup_expressions, flags.verbose );
		}
	}

	if (statefile != 0) {
		bury ();
	}

	end_time = now ();
	delta_t = end_time - start_time;
	if (totpkts > 0) {
		if( flags.verbose ) {
			elog_notify ( 0, "\n%.0f %.2f byte packets (%.1f kbytes) in %.3f seconds\n\t%10.3f kbytes/s\n\t%10.3f kbaud\n\t%10.3f pkts/s\n",
				totpkts, totbytes / totpkts, totbytes / 1024,
				delta_t,
				totbytes / delta_t / 1024,
				totbytes / delta_t / 1024 * 8,
				totpkts / delta_t);
		}

	} else {

		if( flags.verbose ) {
			elog_notify ( 0, "\nno packets saved\n");
		}
	}

	if (orbclose (orbfd)) {
		elog_complain (1, "error closing read orb\n");
	}
	if( dbclose( db ) < 0 ) {
		elog_complain (1, "error closing output db\n");
	}
	exit( 0 );
}
