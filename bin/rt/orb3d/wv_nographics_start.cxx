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
