#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <unistd.h>
#include <errno.h>

#include "Pkt.h"
#include "orb.h"
#include "forb.h"
#include "coords.h"
#include "stock.h"

#include "libuser.h"
#include "magick/api.h"
#include "magick/magick.h"

typedef struct Flags {
    unsigned int    verbose:4;
}               Flags;

static void
usage ()
{
    fprintf (stderr, "\nUsage: %s [-m match] [-r reject] [-S statefile] [-v] "
	     "orb db [start-time [period|end-time]]\n", Program_Name);
    exit (1);
}

#define VERY_LARGE_NUMBER   1e36
#define IMG_SCHEMA "Images0.2"

static char *
get_imageblob_format( ExpImgPacket *eip )
{
    Image 	*im;
    ImageInfo	*iminfo;
    ExceptionInfo exinfo;
    int		retcode = 0;
    char	*format = 0;

    /* There's some bug in GetImageInfo which makes it write past the 
	end of the iminfo structure. I haven't found the bug yet. 
	Switch to dynamic memory allocation for this structure, and 
	allocate two structures instead of one to give the errant 
	routine some room to scribble irresponsibly. */
      
    allot( ImageInfo *, iminfo, 2 );

    GetImageInfo( iminfo );
    GetExceptionInfo( &exinfo );
    /* im = PingBlob( iminfo, (void *) eip->blob, eip->blob_size, &exinfo ); */
    im = BlobToImage( iminfo, (void *) eip->blob, eip->blob_size, &exinfo );

    if( im == NULL ) {

	complain( 0, "get_imageblob_format: PingBlob failed\n" );
	format = NULL;

    } else {

	format = strdup( im->magick );
	DestroyImage( im );
    	str2lower( format );
    }

    return format;
}

int
main (int argc, char **argv)
{

    int             c,
                    errflg = 0;

    char           *orbname,
                   *dbname;
    int             orbfd;
    Dbptr	    db;
    double          maxpkts = VERY_LARGE_NUMBER ;
    int             quit = 0;
    char           *match = 0,
                   *reject = 0;
    int             nmatch;
    int             specified_after = 0;
    double          after = 0.0,
                    until = VERY_LARGE_NUMBER ;
    double          start_time,
                    end_time,
                    delta_t ;
    double          totpkts = 0,
                    totbytes = 0;
    Flags           flags;
    static int      last_pktid = -1;
    static double   last_pkttime = 0.0;
    char           *statefile = 0;
    double          last_burial = 0.0;
    double          decent_interval = 300.0;
    int             mode = PKT_NOSAMPLES;
    int             rcode;
    char            srcname[ORBSRCNAME_SIZE];
    char	    *nocode_srcname, *sp;
    char	    *image_format;
    char	    filename_formatstr[STRSZ];
    char	    *imgfilepath = 0;
    double          pkttime = 0.0 ;
    int             pktid;
    int             nbytes;
    char           *packet = 0;
    int             packetsz = 0;
    Packet         *unstuffed = 0;
    Tbl		   *mytbl;
    FILE	   *fp;
    struct stat	    statbuf;
    char	    *schema_name;
    ExpImgPacket    *eip;

    memset (&flags, 0, sizeof (flags));
    elog_init (argc, argv);
    elog_notify (0, "%s $Revision: 1.2 $ $Date: 2003/06/02 21:30:42 $\n",
		 Program_Name);

    while ((c = getopt (argc, argv, "m:n:r:S:v")) != -1) {
	switch (c) {
	  case 'm':
	    match = optarg;
	    break;

	  case 'n':
	    maxpkts = atoi (optarg);
	    break;

	  case 'r':
	    reject = optarg;
	    break;

	  case 'S':
	    statefile = optarg;
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
	char           *s;

	if (exhume (statefile, &quit, RT_MAX_DIE_SECS, 0) != 0) {
	    elog_notify (0, "read old state file\n");
	}
	if (orbresurrect (orbfd, &last_pktid, &last_pkttime) == 0) {
	    elog_notify (0, "resurrection successful: repositioned to pktid #%d @ %s\n",
			 last_pktid, s = strtime (last_pkttime));
	    free (s);
	} else {
	    complain (0, "resurrection unsuccessful\n");
	}
    }

    if( stat( dbname, &statbuf ) < 0 && errno == ENOENT ) {
	fp = fopen( dbname, "w" );
	if( fp == NULL ) {
		die( 1, "Failed to create descriptor file %s\n", dbname );
	}
	fprintf( fp, "#\nschema %s\n", IMG_SCHEMA );
	fclose( fp );
    }

    if ((dbopen (dbname, "r+", &db)) < 0) {
	die (1, "Can't open output '%s'\n", dbname);
    }

    dbquery( db, dbSCHEMA_NAME, &schema_name );
    if( strcmp( schema_name, IMG_SCHEMA ) != 0 ) {
	die( 1, "%s is not in %s schema\n", dbname, IMG_SCHEMA );
    } 
    db = dblookup( db, 0, "images", 0, 0 );

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
	printf ("%d sources selected\n", nmatch);
    }

    if (specified_after) {
	pktid = orbafter (orbfd, after);
	if (pktid < 0) {
	    char           *s;
	    complain (1, "seek to %s failed\n", s = strtime (after));
	    free (s);
	    pktid = forbtell (orbfd);
	    printf ("pktid is still #%d\n", pktid);
	} else {
	    printf ("new starting pktid is #%d\n", pktid);
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
		complain( 1, "Packet-unstuff failed for %s, %s\n", srcname, strtime( pkttime ) );
		continue;
	      case Pkt_wf:
	      case Pkt_db:
	      case Pkt_pf:
	      case Pkt_ch:
	      case Pkt_tp:
	      default:
		break;
	    }

            if( strcmp( unstuffed->parts.src_suffix, "EXP" ) || 
		strcmp( unstuffed->parts.src_subcode, "IMG" ) ) {

		continue;
	    }

	    if (flags.verbose) {
		showPkt (pktid, srcname, pkttime, packet, nbytes, stdout, mode);
	    }

	    nocode_srcname = strdup( srcname );
	    mytbl = split( nocode_srcname, '/' );
	    free( mytbl );

	    eip = unstuffed->pkthook->p;

	    if( ( image_format = get_imageblob_format( eip ) ) == NULL ) {

		continue;
	    }

	    db = dblookup( db, "", "", "", "dbSCRATCH" );

    	    dbputv( db, 0, "srcname", nocode_srcname, 
		       "time", pkttime, 
		       "format", image_format,
		       "description", unstuffed->string,
		       0 );

	    free( nocode_srcname );

	    strcpy( filename_formatstr, "%Y/%j/%{srcname}.%H:%M:%S." );
	    strcat( filename_formatstr, image_format );
	    trwfname( db, filename_formatstr, &imgfilepath );

	    free( image_format );

	    fp = fopen( imgfilepath, "w" );

	    if( fp == (FILE *) NULL ) {

		complain( 1, "Failed to open %s for writing\n", imgfilepath );
		continue;

	    } else {

	    	fwrite( eip->blob, sizeof( char ), eip->blob_size, fp );
	    	fclose( fp );
	    }

	    dbadd( db, 0 );

	    last_pktid = pktid;
	    last_pkttime = pkttime;
	    break;

	  default:
	    break;
	}

    }

    if (statefile != 0)
	bury ();

    end_time = now ();
    delta_t = end_time - start_time;
    if (totpkts > 0) {
	printf ("\n%.0f %.2f byte packets (%.1f kbytes) in %.3f seconds\n\t%10.3f kbytes/s\n\t%10.3f kbaud\n\t%10.3f pkts/s\n",
		totpkts, totbytes / totpkts, totbytes / 1024,
		delta_t,
		totbytes / delta_t / 1024,
		totbytes / delta_t / 1024 * 8,
		totpkts / delta_t);
    } else {

	printf ("\nno packets saved\n");
    }

    if (orbclose (orbfd)) {
	complain (1, "error closing read orb\n");
    }
    if( dbclose( db ) < 0 ) {
	complain (1, "error closing output db\n");
    }
    return 0;
}
