#include <wv_graphics_start.h>

void *
nographics_start(void *dlp) {

	Wv_datalink *dl = (Wv_datalink *) dlp;
	Wv_wfstruct *wvwf;
	Wv_stachaninfo *wvsci;
	int	rc;
	int	loop = 1;
	Tbl	*keys;
	int	ikey; 
	char	*key;

	keys = keysarr( dl->display_channels );

	fprintf( stderr, "\n\nnographics_start: Initial display_channels setup information:\n" );

	for( ikey = 0; ikey < maxtbl( keys ); ikey++ ) {

		key = (char *) gettbl( keys, ikey );

		wvsci = (Wv_stachaninfo *) getarr( dl->display_channels, key );
		
		fprintf( stderr, "\nDisplaying station %s channel %s\n"
				 "\tlat %f, lon %f, elev %f meters\n"
				 "\ttimespan %f seconds, amplitude scale %f to %f\n",
				wvsci->sta, 
				wvsci->chan, 
				wvsci->lat, 
				wvsci->lon, 
				wvsci->elev_meters, 
				wvsci->twin_sec, 
				wvsci->amplitude_min, 
				wvsci->amplitude_max );
	}

	fprintf( stderr, "\n\nnographics_start: Initial ground_surface setup information:\n" );
	fprintf( stderr, "\n\t\ttopography_pixfile_filename\t%s\n", dl->topography_pixfile_filename );
	fprintf( stderr, "\n\t\ttopography_grid\t%s\n", dl->topography_grid );
	fprintf( stderr, "\n\t\ttopography_gmtgrid\t%s\n", dl->topography_gmtgrid );
	fprintf( stderr, "\n\t\ttopography_gmtcolormap\t%s\n", dl->topography_gmtcolormap );
	fprintf( stderr, "\n\t\ttopography_lonmin\t%f\n", dl->topography_lonmin );
	fprintf( stderr, "\n\t\ttopography_lonmax\t%f\n", dl->topography_lonmax );
	fprintf( stderr, "\n\t\ttopography_loninc\t%f\n", dl->topography_loninc );
	fprintf( stderr, "\n\t\ttopography_latmin\t%f\n", dl->topography_latmin );
	fprintf( stderr, "\n\t\ttopography_latmax\t%f\n", dl->topography_latmax );
	fprintf( stderr, "\n\t\ttopography_latinc\t%f\n", dl->topography_latinc );
	fprintf( stderr, "\n\t\ttopography_zmin\t%f\n", dl->topography_zmin );
	fprintf( stderr, "\n\t\ttopography_zmax\t%f\n", dl->topography_zmax );
	
	fprintf( stderr, "\n\nnographics_start: starting data-display loop:\n" );

	while( loop ) {

		if( ( rc = pmtfifo_pop( dl->fifo, (void **) &wvwf ) ) == PMTFIFO_OK ) {

                        fprintf( stderr, "\n\t\t\tnographics_start: packet acquired!:\n" );

                        print_wv_wfstruct( stderr, wvwf );

		} else if( rc == PMTFIFO_NODATA ) {

                        fprintf( stderr, "\n\t\t\tnographics_start: no data, sleeping\n" );

			sleep( 1 );
	
		} else {

                        fprintf( stderr, "\n\t\t\tnographics_start: ERROR! going to sleep for 1 sec\n" );

			sleep( 1 );
		}
	}
}
