#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

#include "stock.h"
#include "Pkt.h"

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

	return eip;
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
    char	   clean_string[EXPIMG100_DESCRIPTION_SIZE];

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

    HI2NS (cp, &pkt->version, 1);
    cp += 2 * 1;

    strncpy( clean_string, pkt->string, EXPIMG100_DESCRIPTION_SIZE );
    memcpy( cp, clean_string, EXPIMG100_DESCRIPTION_SIZE );
    cp += EXPIMG100_DESCRIPTION_SIZE;

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
    NS2HI (&pkt->version, cp, 1);
    cp += 2 * 1;

    reallot( char *, pkt->string, EXPIMG100_DESCRIPTION_SIZE );
    memcpy( pkt->string, cp, EXPIMG100_DESCRIPTION_SIZE );
    memset( (char *) pkt->string + EXPIMG100_DESCRIPTION_SIZE - 1, '\0', 1 );
    cp += EXPIMG100_DESCRIPTION_SIZE;

    strtrim( (char *) pkt->string );

    pkt->string_size = strlen( pkt->string ) + 1;

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
