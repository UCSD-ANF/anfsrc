#ifndef _WV_CONNECT_UTILS
#define _WV_CONNECT_UTILS

#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include "db.h"
#include "stock.h"
#include "brttpkt.h"
#include "brttutil.h"
#include "tr.h"
#include "Pkt.h"
#include "orb.h"
#include "response.h"

typedef struct wv_wfstruct { 	/* Wiggleview waveform structure */
	PktChannel *pktchan;
	float	*cdata;		/* Calibrated data */
	float	*fdata;		/* Filtered data. ***Normally, use this time-series in potting*** */
	char	netstachanloc[ORBSRCNAME_SIZE];
	char	sta[PKT_TYPESIZE];
	char	chan[PKT_TYPESIZE];
	char	filter[STRSZ];
	double	lat;
	double	lon;
	double	elev_meters;
	double	calib;
	double	calper;
	double	dt;
	char	segtype[PKT_TYPESIZE];
	Response *response; 
} Wv_wfstruct;

typedef struct wv_datalink {
        pthread_t tid;
        Pf      *pf;
        Pmtfifo *fifo;
	char	stereocameras_filename[FILENAME_MAX];
	char	*tripod_filename;
	char	*grid_filename;
	Arr	*display_channels;
} Wv_datalink;

typedef struct wv_stachaninfo {
	char	sta[PKT_TYPESIZE];
	char	chan[PKT_TYPESIZE];
	double	lat;
	double 	lon;
	double 	elev_meters;
	double	amplitude_min;
	double	amplitude_max;
	double	twin_sec;
} Wv_stachaninfo;

extern void free_wv_wfstruct( Wv_wfstruct **wvwf );
extern void print_wv_wfstruct( FILE *stream, Wv_wfstruct *wvwf );
#endif
