#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

#include "stock.h"
#include "Pkt.h"

#include "p_libuser.h"
#include "libuser.h"


int 
stuffPkt_User (Packet *pkt, char *srcname, double *opkttime, 
	       char **ppp, int *nbytes, int *ppsz)
{
	Srcname parts;

	split_srcname( srcname, &parts );

	if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
	    strcmp( parts.src_subcode, "IMG" ) == 0 ) {

		return stuff_IMG( pkt, srcname, opkttime, 
				     ppp, nbytes, ppsz );

	} else if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
	    strcmp( parts.src_subcode, "NMEA" ) == 0 ) {

		return stuff_NMEA( pkt, srcname, opkttime, 
				     ppp, nbytes, ppsz );

	} else if( strcmp( parts.src_suffix, "VORB" ) == 0 ) {

		return stuff_VORB( pkt, srcname, opkttime, 
				     ppp, nbytes, ppsz );

	} else if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
	    strcmp( parts.src_subcode, "ORsci" ) == 0 ) {

		return stuff_orsci( pkt, srcname, opkttime, 
				     ppp, nbytes, ppsz );

	} else {
		return -1;
	}
}

int
unstuffPkt_User (char *srcname, double ipkttime, char *packet, 
		 int nbytes, Packet * pkt)
{
	Srcname parts;

	split_srcname( srcname, &parts );

	if( strcmp( parts.src_suffix, "EXP" ) == 0 &&
	    strcmp( parts.src_subcode, "IMG" ) == 0 ) {

		return unstuff_IMG( srcname, ipkttime, packet, 
				       nbytes, pkt );

	} else if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
	    strcmp( parts.src_subcode, "NMEA" ) == 0 ) {

		return unstuff_NMEA( srcname, ipkttime, packet, 
				       nbytes, pkt );
	} else if( strcmp( parts.src_suffix, "VORB" ) == 0 ) {

		return unstuff_VORB( srcname, ipkttime, packet, 
				       nbytes, pkt );

	} else if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
	    strcmp( parts.src_subcode, "ORsci" ) == 0 ) {

		return unstuff_orsci( srcname, ipkttime, packet, 
				       nbytes, pkt );

	} else {
		return -1;
	}
}

void
showPkt_User( int pktid, char *srcname, double pkttime, char *pkt, 
	      int nbytes, FILE *file, int mode )
{
	Srcname parts;

	split_srcname( srcname, &parts );

	if( strcmp( parts.src_suffix, "EXP" ) == 0 &&
	    strcmp( parts.src_subcode, "IMG" ) == 0 ) {

	  showPkt_IMG( pktid, srcname, pkttime, pkt, nbytes, file, mode );

	} else if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
		   strcmp( parts.src_subcode, "NMEA" ) == 0 ) {
	  
	  showPkt_NMEA( pktid, srcname, pkttime, pkt, nbytes, file, mode );
	} else if( strcmp( parts.src_suffix, "VORB" ) == 0 ) {
	  
	  showPkt_VORB( pktid, srcname, pkttime, pkt, nbytes, file, mode );
	} else if( strcmp( parts.src_suffix, "EXP" ) == 0 && 
		   strcmp( parts.src_subcode, "ORsci" ) == 0 ) {
	  
	  showPkt_orsci( pktid, srcname, pkttime, pkt, nbytes, file, mode );
	}

}
