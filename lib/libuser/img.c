#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <signal.h>

#include "stock.h"
#include "Pkt.h"
#include "swapbytes.h"

#include "p_libuser.h"
#include "libuser.h"

ExpImgPacket *
new_expimgpacket( void ) 
{
	ExpImgPacket	*eip;

	allot( ExpImgPacket *, eip, 1 );

	eip->blob = 0;
	eip->blob_size = 0;
	eip->blob_bufsz = 0;
	eip->blob_offset = 0;
	eip->ifragment = 0;
	eip->nfragments = 0;

	strcpy( eip->description, "" );
	strcpy( eip->format, "" );

	return eip;
}

ExpImgPacket *
dup_expimgpacket( ExpImgPacket *eip ) 
{
	ExpImgPacket	*new;

	new = new_expimgpacket();

	allot( char *, new->blob, eip->blob_bufsz );

	memcpy( new->blob, eip->blob, eip->blob_size );

	new->blob_size = eip->blob_size;
	new->blob_bufsz = eip->blob_bufsz;
	new->blob_offset = eip->blob_offset;
	new->ifragment = eip->ifragment;
	new->nfragments = eip->nfragments;

	strcpy( new->description, eip->description );
	strcpy( new->format, eip->format );

	return new;
}

void
free_expimgpacket( ExpImgPacket *eip )
{
	if( eip == (ExpImgPacket *) NULL ) {
		return;
	}

	if( eip->blob != (char *) NULL ) {
		free( eip->blob );
	}

	free( eip );

	return;
}

int
stuff_IMG (Packet * pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
    char           *pp,
                   *cp;
    /* Must set the retcode by hand since pkt->pkttype structure isn't defined */
    int             retcode = Pkt_tp;
    ExpImgPacket  *eip = 0;
    char	   clean_string[EXPIMG_DESCRIPTION_SIZE];

    pp = cp = *ppp;

    if( ( eip = (ExpImgPacket *) pkt->pkthook->p ) == NULL ||
	  eip->blob == NULL || 
	  eip->blob_size == 0 ) {

	complain( 0, "Can't stuff null image\n" );
	return -1;
    }

    RESIZE_BUFFER( char *, *ppp, *ppsz, eip->blob_size + 66 );

    cp = *ppp + (cp - pp);
    pp = *ppp;

    pkt->version = IMG_CURRENT_VERSION;

    hi2ms (&pkt->version, &cp, 1);

    hi2ms (&eip->ifragment, &cp, 1);

    hi2ms (&eip->nfragments, &cp, 1);

    hi2mi (&eip->blob_offset, &cp, 1);

    strncpy( clean_string, eip->format, EXPIMG_FORMAT_SIZE );
    memcpy( cp, clean_string, EXPIMG_FORMAT_SIZE );
    cp += EXPIMG_FORMAT_SIZE;

    strncpy( clean_string, eip->description, EXPIMG_DESCRIPTION_SIZE );
    memcpy( cp, clean_string, EXPIMG_DESCRIPTION_SIZE );
    cp += EXPIMG_DESCRIPTION_SIZE;

    memcpy ( cp, eip->blob, eip->blob_size );
    cp += eip->blob_size;

    *nbytes = cp - pp;

    insist (*nbytes < 1000000);

    return retcode;
}

int
unstuff_IMG (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
    char           *pp,
                   *cp;
    int             retcode = Pkt_tp;
    size_t 	imgsize;
    size_t 	bloblength = 0;
    ExpImgPacket  *eip = 0;

    pp = cp = packet;
    ms2hi (&cp, &pkt->version, 1);

    if( pkt->pkthook == NULL ) {

    	pkt->pkthook = new_hook( (void (*)()) free_expimgpacket );
	eip = pkt->pkthook->p = new_expimgpacket();

    } else if( pkt->pkthook && pkt->pkthook->free != free_expimgpacket ) {

	free_hook( &pkt->pkthook );
    	pkt->pkthook = new_hook( (void (*)()) free_expimgpacket );
	eip = pkt->pkthook->p = new_expimgpacket();

    } else {

    	eip = (ExpImgPacket *) pkt->pkthook->p;
    }

    if( pkt->version == 110 ) {
		
	ms2hi (&cp, &eip->ifragment, 1);

	ms2hi (&cp, &eip->nfragments, 1);

	mi2hi (&cp, &eip->blob_offset, 1);

	memcpy( eip->format, cp, EXPIMG_FORMAT_SIZE );
	memset( (char *) eip->format + EXPIMG_FORMAT_SIZE - 1, '\0', 1 );
	cp += EXPIMG_FORMAT_SIZE;

    	strtrim( (char *) eip->format );

    } else if( pkt->version == 100 ) {

	eip->ifragment = 1;
	eip->nfragments = 1;
	eip->blob_offset = 0;

	strcpy( eip->format, "" );

    } else {
	
	complain (0, "Unrecognized packet version %d in unstuff_IMG\n", pkt->version );

	return -1;
    }

    memcpy( eip->description, cp, EXPIMG_DESCRIPTION_SIZE );
    memset( (char *) eip->description + EXPIMG_DESCRIPTION_SIZE - 1, '\0', 1 );
    cp += EXPIMG_DESCRIPTION_SIZE;

    strtrim( (char *) eip->description );

    imgsize = nbytes - (cp - pp);

    RESIZE_BUFFER( char *, eip->blob, eip->blob_bufsz, imgsize );

    memcpy ( eip->blob, cp, imgsize );
    cp += imgsize;

    if (nbytes < cp - pp) {
	complain (0, "nbytes=%d < cp-pp=%d\n", nbytes, cp - pp);
	retcode = -1;
    };

    eip->blob_size = imgsize;

    return retcode;
}

void showPkt_IMG( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{

	printf( "showPkt_IMG: packet %d from %s has %d bytes\n", pktid, srcname, nbytes );
}
