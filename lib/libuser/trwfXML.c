/* 
 * waveform XML-based time-series reading and writing
 *
 * Kent Lindquist
 * Lindquist Consulting
 * UCSD VORB project
 * 6/2003
 */

#include "tr.h"

#define XML_DATABLOCK_VERSION "0.1"
#define XML_DATABLOCK_TAGNAME "wfdata"
#define XML_DATAPOINT_TAGNAME "wfpt"
#define XML_DATAPOINT_MAXBYTES 45

int 
wfreadXML ( char *input, int nbytes,  int first, int nsamp, float *dest )
{
	int i, retcode ; 
	short x ;

	retcode = -2; /* SCAFFOLD: -2 => 'not implemented' */

	/* SCAFFOLD
	if ( nbytes >= xxHdrSz + (nsamp+first) * sizeof(short)) {
	input += xxHdrSz ; 
	for ( i = 0 ; i<nsamp ; i++ ) { 
		N2H2(&x, input+((i+first)*sizeof(short)), 1 ) ; 
		dest[i] = x ;
	}
	retcode = 0 ; 
	} else { 
		retcode = -6 ; * file too short *
	}
	*/

	return retcode ; 
}

static int
add_attribute( void **vstack, char *attrname, char *attrval )
{
	pushstr( vstack, " " );
	pushstr( vstack, attrname );
	pushstr( vstack, "=\"" );
	pushstr( vstack, attrval );
	pushstr( vstack, "\"" );

	return 0;
}

int
wfhdrXML ( Wfdisc *wfdisc,
	    void *data, 
	    int nsamp, 
	    char **outbuf, 
	    int *nbytes, 
	    int *bufsz )
{

	void 	*vstack = 0;
	char	*s;	
	char	attrval[STRSZ];

	pushstr( &vstack, "<" );
	pushstr( &vstack, XML_DATABLOCK_TAGNAME );
	add_attribute( &vstack, "version", XML_DATABLOCK_VERSION );
	add_attribute( &vstack, "net", wfdisc->net );
	add_attribute( &vstack, "sta", wfdisc->sta );
	add_attribute( &vstack, "chan", wfdisc->chan );
	add_attribute( &vstack, "segtype", wfdisc->segtype );

	sprintf( attrval, "%.9g", wfdisc->time );
	add_attribute( &vstack, "time", attrval );

	sprintf( attrval, "%d", wfdisc->nsamp );
	add_attribute( &vstack, "nsamp", attrval );

	sprintf( attrval, "%.9g", wfdisc->samprate );
	add_attribute( &vstack, "samprate", attrval );

	sprintf( attrval, "%.9g", wfdisc->calib );
	add_attribute( &vstack, "calib", attrval );

	sprintf( attrval, "%.9g", wfdisc->calper );
	add_attribute( &vstack, "calper", attrval );

	pushstr( &vstack, ">\n" );

	s = popstr( &vstack, 1 );
	SIZE_BUFFER( char *, *outbuf, *bufsz, strlen(s)+1 ); 
	strcpy( *outbuf, s );
	free( s );

	*nbytes = strlen( *outbuf ) ; 

	return 0 ; 
}

#define OUTSIDE(X,LOWER,UPPER) ((X) <= LOWER || (X) >= UPPER)

int
wfwriteXML ( Wfdisc *wfdisc, 
	      Trsample *data, 
	      int nsamp, 
	      char **outbuf, 
	      int *nbytes, 
	      int *bufsz )
{
	int	i;
	int	needed;
	int	bps;
	int	flags=0; 
	float	x;
	float	fill; 
	float	MISSING;
	float	lower;
	float	upper;
	Wftype 	*type ;
	char	*s;

	type = trwftype("xm");
	lower = type->lower;
	upper = type->upper;
	bps = type->bytesPerSamp;
	if( bps == 0 ) {
		bps = XML_DATAPOINT_MAXBYTES;
	}
	fill = type->fill;

	needed = bps * nsamp ; 
	SIZE_BUFFER(char *, *outbuf, *bufsz, needed ) ;

	MISSING = trwftype("s4")->fill;

	s = *((char **) outbuf );

	for( i=0; i<nsamp; i++ ) { 
		if (data[i] == MISSING) {
			x = fill;
			flags |= TR_GAPS;
		} else {
			if (OUTSIDE (data[i], lower, upper)) {

				flags |= TR_CLIPPED;

				if ( data[i] <= lower ) { 
		    			x = lower+1; 
				} else { 
		    			x = upper-1; 
				}

			} else {

				x= floor (data[i]);

				if (x != data[i]) {
		    			flags |= TR_TRUNCATED;
				}
			}
		}
		wfdisc->checksum += x ;
		sprintf( s, "<%s>%.9g</%s>\n",
			 XML_DATAPOINT_TAGNAME, x, XML_DATAPOINT_TAGNAME );
		s += strlen( s );
	}
	*nbytes = s - *outbuf;
	return flags ; 
}

int
wftrailerXML ( Wfdisc *wfdisc, void *data, int nsamp, char **outbuf, int *nbytes, int *bufsz )
{
	void 	*vstack = 0;
	char	*s;	

	pushstr( &vstack, "</" );
	pushstr( &vstack, XML_DATABLOCK_TAGNAME );
	pushstr( &vstack, ">\n" );

	s = popstr( &vstack, 1 );
	SIZE_BUFFER( char *, *outbuf, *bufsz, strlen(s) + 1 ); 
	strcpy( *outbuf, s );
	free( s );

	*nbytes = strlen(*outbuf) ; 

	return 0 ; 
}
