/* 
 * orb3d 
 *
 * Kent Lindquist, Lindquist Consulting, Inc.
 * Atul Nayak, Institute of Geophysics and Planetary Physics, UCSD 
 *
 */


#pragma warning(disable:4275)
#pragma warning(disable:4251)

#include <stdio.h>
#include "db.h"
#include "stock.h"
#include "brttpkt.h"
#include "brttutil.h"
#include "tr.h"
#include "pf.h"
#include "Pkt.h"
#include "wv_connect_utils.h"

#ifdef NOGRAPHICS
void * nographics_start(void*);
#else
#include "wv_graphics_start.h"
#endif

PktChannelCalib *Pcc;
Arr *Filter_hooks;      

static Wv_stachaninfo *
new_wv_stachaninfo()
{
	Wv_stachaninfo *new_wv_sci;

	allot( Wv_stachaninfo *, new_wv_sci, 1 );

	return new_wv_sci;
}

static int
fill_wv_stachaninfo( Wv_stachaninfo *wv_sci, Dbptr db, char *netstachanloc, double amin, double amax, double twin_sec )
{
	Srcname parts;
	char	expr[STRSZ];
	int 	nrecs;

	split_srcname( netstachanloc, &parts );

	strcpy( wv_sci->sta, parts.src_sta );
	strcpy( wv_sci->chan, parts.src_chan );

	sprintf( expr, "sta == \"%s\" && offdate == NULL", wv_sci->sta );

	db = dblookup( db, "", "site", "", "" );
	db = dbsubset( db, expr, 0 );

	dbquery( db, dbRECORD_COUNT, &nrecs );
	
	if( nrecs <= 0 ) {

		elog_complain( 0, "Couldn't find %s in database!\n", wv_sci->sta ); 

		return -1;

	}  else {
	
		db.record = 0;
		dbgetv( db, 0, 
			"lat", &wv_sci->lat, 
			"lon", &wv_sci->lon, 
			"elev", &wv_sci->elev_meters, 
			0 );
	}

	wv_sci->amplitude_min = amin;
	wv_sci->amplitude_max = amax;
	wv_sci->twin_sec = twin_sec;

	return 0;
}

static void
free_wv_stachaninfo( Wv_stachaninfo **wv_sci ) 
{
	free( *wv_sci );

	return;
}


static Wv_wfstruct *
new_wv_wfstruct( PktChannel *pktchan )
{
        Wv_wfstruct *new_wv_wf;
 
        allot( Wv_wfstruct *, new_wv_wf, 1 );

        new_wv_wf->pktchan = pktchan;

        sprintf( new_wv_wf->netstachanloc, "%s_%s_%s",
                        pktchan->net,
                        pktchan->sta,
                        pktchan->chan );
        
        if( strcmp( pktchan->loc, "" ) ) {
        
                strcat( new_wv_wf->netstachanloc, "_" );
                strcat( new_wv_wf->netstachanloc, pktchan->loc );
        }

        allot( float *, new_wv_wf->cdata, pktchan->nsamp );
        allot( float *, new_wv_wf->fdata, pktchan->nsamp );

        memset( new_wv_wf->cdata, 0, pktchan->nsamp * sizeof( float ) );
        memset( new_wv_wf->fdata, 0, pktchan->nsamp * sizeof( float ) );

        strcpy( new_wv_wf->sta, "-" );
        strcpy( new_wv_wf->chan, "-" );
        strcpy( new_wv_wf->segtype, "-" );
        strcpy( new_wv_wf->filter, "" );
        new_wv_wf->lat = -999.0;
        new_wv_wf->lon = -999.0;
        new_wv_wf->elev_meters = -999.0;
        new_wv_wf->calib = 0;
        new_wv_wf->calper = -1;
        new_wv_wf->dt = -1;
        new_wv_wf->response = 0;
	
        return new_wv_wf;
}

void
print_wv_wfstruct( FILE *stream, Wv_wfstruct *wvwf )
{
        char    *s;
        int     i;
        int     nprint = 5;

        fprintf( stream, "\nPacket:\n" );
        fprintf( stream, "\tsta\t%s\n", wvwf->sta );
        fprintf( stream, "\tchan\t%s\n", wvwf->chan );

        fprintf( stream, "\tstart time\t%s\n",
                 s = strtime( wvwf->pktchan->time ) );
        free( s );

        fprintf( stream, "\tnsamp %d calib %f calper %f\n",
                        wvwf->pktchan->nsamp, wvwf->calib, wvwf->calper );

        if( wvwf->pktchan->nsamp >= nprint ) {
                fprintf( stream, "\traw: " );
                for( i = 0; i < nprint; i++ ) {
                        fprintf( stream, "%d\t", wvwf->pktchan->data[i] );
                }
                fprintf( stream, "\n" );

                fprintf( stream, "\tcal: " );
                for( i = 0; i < nprint; i++ ) {
                        fprintf( stream, "%.1f\t", wvwf->cdata[i] );
                }
                fprintf( stream, "\n" );

                fprintf( stream, "\tfil: " );
                for( i = 0; i < nprint; i++ ) {
                        fprintf( stream, "%.1f\t", wvwf->fdata[i] );
                }
                fprintf( stream, "\n" );
        }
       fprintf( stream, "\n" );

        return;
}

void
free_wv_wfstruct( Wv_wfstruct **wvwf )
{
        freePktChannel( (*wvwf)->pktchan );

        if( (*wvwf)->fdata ) {

                free( (*wvwf)->fdata );
        }

        if( (*wvwf)->cdata ) {

                free( (*wvwf)->cdata );
        }

        if( (*wvwf)->response ) {

                free_response( (*wvwf)->response );
        }

        free( *wvwf );

        *wvwf = 0;

        return;
}

static int
pipecallback( void *dlp, PktChannel *pktchan,
              int queue_code, double gaptime )
{
        Wv_datalink *dl = (Wv_datalink *) dlp;
        Wv_wfstruct *wvwf;
        char    *dbname;
        static char *filter = 0;
        int     need_calib = 1;
        int     need_response = 0;
        int     need_site = 1;
        int     check = 0;
        int     i;
        Hook    *hook = 0;

        if( Pcc == (PktChannelCalib *) NULL ) {

                dbname = pfget_string( dl->pf, "dbname" );

                Pcc = pktchannelcalib_new( dbname, need_calib,
                                need_response, need_site );
        }

        if( Filter_hooks == (Arr *) NULL ) {

                Filter_hooks = newarr( 0 );
        }

        if( queue_code == PKTCHANNELPIPE_DUP ) {
                elog_notify( 0, "duplicate packet\n" );
                freePktChannel( pktchan );
                return 0;
        }

        wvwf = new_wv_wfstruct( pktchan );

        pktchannelcalib_get( Pcc, pktchan->net, pktchan->sta, pktchan->chan,
                          pktchan->loc, pktchan->time, check,
                             wvwf->sta, wvwf->chan, &wvwf->lat, &wvwf->lon,
                             &wvwf->elev_meters, &wvwf->calib, &wvwf->calper,
                             wvwf->segtype, &wvwf->response );

        if( wvwf->calib == 0 ) {
                wvwf->calib = 1.0;
        }

        wvwf->dt = 1. / pktchan->samprate;

        for( i = 0; i < wvwf->pktchan->nsamp; i++ ) {

                wvwf->cdata[i] = wvwf->calib * wvwf->pktchan->data[i];
                wvwf->fdata[i] = wvwf->calib * wvwf->pktchan->data[i];
        }

        if( filter == 0 ) {

                filter = pfget_string( dl->pf, "filter" );
        }

        strcpy( wvwf->filter, filter );

        /* SCAFFOLD need to handle filter resetting (fancier hook mgmt) */

        hook = (Hook*)getarr( Filter_hooks, wvwf->netstachanloc );

        trfilter_pkt( wvwf->pktchan->nsamp, wvwf->dt, wvwf->fdata,
                      wvwf->filter, &hook );

        if( hook ) {

                setarr( Filter_hooks, wvwf->netstachanloc, hook );
        }
      if( pmtfifo_push( dl->fifo, (void *) wvwf ) < 0 ) {

                elog_complain( 1, "pmtfifo_push error\n" );
        }

        return 0;
}

int main(int argc, char* argv[])
{	
	Pf      *pf;
	Dbptr	db;
        Wv_wfstruct *wvwf;
        Wv_stachaninfo *wvsci;
        PktChannelPipe *pcp;
        int     rc;
        char    *pfname = "orb3d";
        char    *dbname;
        char    *orbname;
        char    *select;
        Tbl     *channels_select;
        Tbl     *display_channels;
        char    srcname[ORBSRCNAME_SIZE];
        int     loop = 1;
        int     max_pktpipe_packets;
        int     orbfd;
        int     pktid;
        double  pkttime;
        char    *pkt = 0;
        int     nbytes = 0;
        int     bufsize = 0;
        Wv_datalink *dl;
	FILE	*fp;
	char	*stereocameras_file_contents;
	int	ichannel;
	char	channelline[STRSZ];
	Tbl	*pieces;
	char	*whitespace_chars = "\t\n\r";
	char	*whitespace_spaces = "   ";
	char	*netstachanloc;
	double	twin_sec;
	double	amin;
	double	amax;

	elog_init( argc, argv );

	#ifndef NOGRAPHICS
	
		glutInit(&argc, argv);
	#endif

       if( argc != 1 ) {

                die( 0, "usage: orb3d\n" );
        }

	allot( Wv_datalink *, dl, 1 );

        if( pfread( pfname, &pf ) < 0 ) {

                die( 1, "Failed to read parameter file '%s.pf'. Bye.\n", pfname );

        } else {

		dbname = pfget_string( pf, "dbname" );
		orbname = pfget_string( pf, "orbname" );
		select = pfget_string( pf, "select" );

		dl->tripod_filename = pfget_string( pf, "tripod_filename" );
		dl->grid_filename = pfget_string( pf, "grid_filename" );

		max_pktpipe_packets = pfget_int( pf, "max_pktpipe_packets" );

		display_channels = pfget_tbl( pf, "display_channels" );

		stereocameras_file_contents = pfget_string( pf, "StereoCameras_file" );
	}

	if( dbopen( dbname, "r", &db ) < 0 ) {
		
		elog_die( 0, "Failed to open database '%s'. Bye!\n", dbname );
	} 

	channels_select = newtbl( 0 );
	dl->display_channels = newarr( 0 );

	for( ichannel = 0; ichannel < maxtbl( display_channels ); ichannel++ ) {

		strcpy( channelline, (char *) gettbl( display_channels, ichannel ) );

		strtr( channelline, whitespace_chars, whitespace_spaces ); 
		pieces = split( channelline, ' ' );

		netstachanloc = (char *) gettbl( pieces, 0 );
		twin_sec = atof( (char *) gettbl( pieces, 1 ) );
		amin = atof( (char *) gettbl( pieces, 2 ) );
		amax = atof( (char *) gettbl( pieces, 3 ) );

		wvsci = new_wv_stachaninfo();

		rc = fill_wv_stachaninfo( wvsci, db, netstachanloc, amin, amax, twin_sec );

		if( rc < 0 ) {

			elog_complain( 0, "failed to set up info for display_station '%s'; skipping!\n",
				netstachanloc );

			free_wv_stachaninfo( &wvsci );

		} else {
	
			pushtbl( channels_select, strdup( netstachanloc ) );

			setarr( dl->display_channels, netstachanloc, (void *) wvsci );
		}

		freetbl( pieces, 0 );
	}
	
	sprintf( dl->stereocameras_filename, "/tmp/StereoCameras_%d_%d.iv", getuid(), getpid() );

	fp = fopen( dl->stereocameras_filename, "w" );
	fprintf( fp, "%s\n", stereocameras_file_contents );
	fclose( fp );

	dl->pf = pf;
	dl->fifo = pmtfifo_create( 0, 0, 0 );

	#ifdef NOGRAPHICS

        	rc = pthread_create( &(dl->tid), 0, nographics_start, (void *) dl );

	#else

        	rc = pthread_create( &(dl->tid), 0, graphics_start, (void *) dl );

	#endif

        if( rc != 0 ) {

                elog_die( 1, "failed to create graphics thread: pthread create error\n" );

        }

        if( ( orbfd = orbopen( orbname, "r&" ) ) < 0 ) {

                die( 1, "Failed to open orb '%s' for reading. Bye.\n",
                        orbname );
        }

        orbselect( orbfd, select );

	pcp = pktchannelpipe_new( channels_select,
                                  0, max_pktpipe_packets,
                                  pipecallback, (void *) dl );

        for(;;) {

                orbreap( orbfd, &pktid, srcname, &pkttime, &pkt,
                        &nbytes, &bufsize );

                fprintf( stderr, "\n\t\t\tacquisition: orbreap got a packet from %s at %s!\n",
                                 srcname, strtime( pkttime ) );

                pktchannelpipe_push( pcp, srcname, pkttime, pkt, nbytes );
        }	

	unlink( dl->stereocameras_filename );

    	return( 0 ); // exit without error
}
