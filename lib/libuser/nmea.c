#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <signal.h>

#include "stock.h"
#include "Pkt.h"

#include "p_libuser.h"
#include "libuser.h"

static char *Pfname = "nmea_defs";
static Pf *Pfnmea_defs = 0;

unsigned int
compute_nmea_checksum( char *string )
{
	int	length;
	int 	i;
	unsigned int checksum = 0;

	length = strlen( string );

	/* string fed to compute_nmea_checksum should not include the 
   	   leading '$' or trailing '*' */

	for( i = 0; i < length; i++ ) {
		checksum ^= string[i];
	}

	return checksum;
}

int
stuff_NMEA (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
    char           *pp,
                   *cp;
   /* Must return the packet-type ourselves since the pkt->pkttype structure
      is not defined */
    int             retcode = Pkt_tp;

    pp = cp = *ppp;

   split_srcname( srcname, &(pkt->parts) );
   strcpy( pkt->parts.src_suffix, "EXP" );
   strcpy( pkt->parts.src_subcode, "NMEA" );

    if( ( pkt->string == NULL && pkt->pf == NULL ) ) {

	complain( 0, "Can't stuff null NMEA packet\n" );
	return -1;
   
    } else if( pkt->pf == NULL && 
	       ( pkt->string_size == 0 || strlen( pkt->string ) == 0 ) ) {

	complain( 0, "Can't stuff empty NMEA packet\n" );
	return -1;
   
    } else if( pkt->pf != NULL ) {

	complain( 0, "SCAFFOLD: Not ready for pffile entries yet\n" );
	return -1;
    } 

    /* SCAFFOLD: need to:
	check for leading $ sign
	check for checksum at the end, recompute and verify
	add checksum if necessary
    */

    join_srcname( &pkt->parts, srcname );

    RESIZE_BUFFER( char *, *ppp, *ppsz, pkt->string_size + 2 );

    cp = *ppp + (cp - pp);
    pp = *ppp;

    pkt->version == NMEA_CURRENT_VERSION;

    HI2NS (cp, &pkt->version, 1);
    cp += 2 * 1;

    memcpy( cp, pkt->string, pkt->string_size );
    cp += pkt->string_size;

    *nbytes = cp - pp;

    *opkttime = pkt->time;

    insist (*nbytes < 1000000);
	
    return retcode;
}

int
unstuff_NMEA (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
    char           *pp,
                   *cp;
    char	   *checksum_string = 0;
    unsigned int    checksum = 0;
    unsigned int    recomputed_checksum = 0;
    char	    asterisk = '*';
    char	    stripped_string[STRSZ];
    int             retcode = Pkt_tp;
    int		    nchars;
    int		    i;
    int		    rc;
    Tbl            *tokens;
    char           *s;
    char	   *sentence_type;
    Pf		   *parse_recipe;
    Tbl		   *fields;
    char	   *atoken;
    char	   *afield;
    int		    ifield;

    if( Pfnmea_defs == 0 ) {

	rc = pfread( Pfname, &Pfnmea_defs );

	if( rc == -1 ) {
		complain( 0, "unstuff: couldn't find nmea_defs.pf\n" );
		if( Pfnmea_defs ) pffree( Pfnmea_defs );
		Pfnmea_defs = 0;
	} else if( rc < -1 ) {
		complain( 0, "unstuff: error parsing nmea_defs.pf\n" );
		if( Pfnmea_defs ) pffree( Pfnmea_defs );
		Pfnmea_defs = 0;
	}

    } else {
	
	rc = pfupdate( Pfname, &Pfnmea_defs );

	if( rc < 0 ) {
		complain( 0, "unstuff: error rereading nmea_defs.pf\n" );
		if( Pfnmea_defs ) pffree( Pfnmea_defs );
		Pfnmea_defs = 0;
	}
    }

    pp = cp = packet;
    NS2HI (&pkt->version, cp, 1);
    cp += 2 * 1;

    nchars = nbytes - ( cp - pp );
    reallot( char *, pkt->string, nchars );
    memcpy( pkt->string, cp, nchars );
    cp += nchars;

    if( pkt->pf ) { 
	pffree( pkt->pf );
	pkt->pf = 0;
    }

    if( pkt->string[0] != '$' ) {
	complain( 0, 
	  "Invalid NMEA packet from %s at %f: no leading '$', %s, %f\n",
	  srcname, ipkttime );
	memset( pkt->string, '\0', nchars );
	return -1;
    }

    i = nchars - 1;
    while( i >= 0 &&
	   ( pkt->string[i] == '\015' || pkt->string[i] == '\012' ) ) {

 	pkt->string[i] = 0;
	i--;

    }

    pkt->string_size = strlen( pkt->string ) + 1;
   
    strncpy( stripped_string, &(pkt->string[1]), strlen( pkt->string ) );
    strtok_r( stripped_string, &asterisk, &checksum_string );

    if( checksum_string == 0 || ! strcmp( checksum_string, "" ) ) {

	complain( 0, 
	  "No checksum in NMEA packet from %s at %f\n",
	  srcname, ipkttime );

	memset( pkt->string, '\0', nchars );

	return -1;

    } else if( sscanf( checksum_string, "%x", &checksum ) < 1 ) {

	complain( 0, 
	  "Failed to read checksum in NMEA packet from %s at %f\n",
	  srcname, ipkttime );

	memset( pkt->string, '\0', nchars );

	return -1;
    }

    recomputed_checksum = compute_nmea_checksum( stripped_string );

    if( recomputed_checksum != checksum ) {
	complain( 0, 
	  "NMEA packet from %s at %f doesn't match checksum\n",
	  srcname, ipkttime );
	memset( pkt->string, '\0', nchars );
	return -1;
    }

    tokens = newtbl( 5 );
    /* Can't use standard split because it clumps repeated split chars */
    s = &(stripped_string[0]);
    pushtbl( tokens, s++ );
    while ( *s != 0 ) {
	if( *s == ',' ) {
		*s = '\0';
		pushtbl( tokens, ++s );
	} else {
		s++;
	}
    }

    sentence_type = shifttbl( tokens );
    if( Pfnmea_defs != 0 && 
	pfget( Pfnmea_defs, sentence_type, (void **) &parse_recipe ) >= 0 &&
	parse_recipe != 0 ) {

	fields = (Tbl *) pfget_tbl( parse_recipe, "fields" );
	if( fields == NULL ) {
		complain( 0,
		  "unstuff: no fields in parse recipe for $%s\n",
		  sentence_type );
	} else {


		pkt->pf = pfnew( PFARR );
		
		ifield = 0;
		while( ( atoken = shifttbl( tokens ) ) && 
		       ( ifield < maxtbl( fields ) ) ) {
			afield = gettbl( fields, ifield++ );
			pfput_string( pkt->pf, afield, atoken );
		}

		if( maxtbl( tokens ) > 0 ) {
			complain( 0, 
			  "unstuff: unparsed entries in $%s\n",
			  sentence_type );
		} 
		if( ifield < maxtbl( fields ) ) {
			complain( 0, 
			  "unstuff: all expected fields not found in $%s\n",
			  sentence_type );
		}
	}

    } else {

	complain( 0, 
	  "unstuff: no parse recipe for $%s in nmea_defs.pf\n", 
	  sentence_type );
    }

    freetbl( tokens, 0 );

    return retcode;
}

void showPkt_NMEA( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
	Packet	*unstuffed=0;

	unstuffPkt( srcname, pkttime, pkt, nbytes, &unstuffed );

	printf( "Showing packet %d from %s\n", pktid, srcname );

	if( unstuffed->string ) {
		printf( "\t%s\n", unstuffed->string );
	} else {
		printf( "Empty string\n", unstuffed->string );
	}
	
	if( unstuffed->pf ) {
		printf( "Parsed parameter-file equivalent:\n" );
		pfout( stdout, unstuffed->pf );
	} else {
		printf( "Parameter-file equivalent not present\n" );
	}

	printf( "\n" );
}
