#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <thread.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/uio.h>
#include <errno.h>
#include "strings.h"
#include "stock.h"
#include "bns.h"
#include "orb.h"
#include "Pkt.h"
#include "libuser.h"

void
put_packet( int orbfd, char *buffer, char *srcname )
{
	Packet	*pkt = 0;
	char	*orbpkt = 0;	
	int	bufsz = 0;
	int	nbytes = 0;
	double 	pkttime = 0;

	pkt = newPkt();

	pkt->string = strdup( buffer );
	pkt->string_size = strlen( pkt->string );
	pkt->time = now();
	stuffPkt( pkt, srcname, &pkttime, &orbpkt, &nbytes, &bufsz );
	orbput( orbfd, srcname, pkttime, orbpkt, nbytes );
	free( pkt->string );
	pkt->string = 0;
	pkt->string_size = 0;

	freePkt( pkt );
}

int
main( int argc, char **argv ) {
	struct sockaddr_in sin;
	in_port_t port;
	int 	so;
	Bns 	*bns;
	int	synchronizing = 1;
	char	c;
	char	orbname[STRSZ];
	char	srcname[ORBSRCNAME_SIZE];
	char	nmea_source[STRSZ];
	char	buffer[STRSZ];
	int 	orbfd;
	int	isentence;
	
	elog_init( argc, argv );

	if( argc != 5 ) {

		die( 1, "Usage: nmea2orb nmea_source port srcname orbname\n" );

	} else {

		strcpy( nmea_source, argv[1] );	
		port = atoi( argv[2] );
		strcpy( srcname, argv[3] );	
		strcpy( orbname, argv[4] );	
	}

	if( ( orbfd = orbopen( orbname, "w&" ) ) < 0 ) {
		die( 1, "Couldn't open %s\n", orbname );
	} 

	so = socket( PF_INET, SOCK_STREAM, 0 );
	if( so < 0 ) {
		die( 1, "Can't open tcp socket for nmea acquisition\n" );
	}

	sin.sin_family = AF_INET;
	sin.sin_port = htons( 0 );  /* Any port */
	sin.sin_addr.s_addr = htonl( INADDR_ANY );
	
	if( bind( so, (struct sockaddr *) &sin, sizeof( sin ) ) ) {
		die( 1, "Couldn't bind nmea acquisition socket\n" );
	}
		
	sin.sin_port = htons( (in_port_t) port );
	sin.sin_addr.s_addr = inet_addr( nmea_source );
	
	if( connect( so, (struct sockaddr *) &sin, sizeof( sin ) ) ) {
		die( 1, "Couldn't connect nmea acquisition socket\n" );
	}

	bns = bnsnew( so, STRSZ );
	bnsuse_sockio( bns );

	synchronizing = 1;
	isentence = 0;
	memset( buffer, '\0', STRSZ );

	while( bnsget( bns, &c, BYTES, 1 ) == 0 ) {

		if( synchronizing && c != '$' ) {
			continue;
		} else {
			synchronizing = 0;
		}
		
		if( c == '$' && ( strlen( buffer ) > 0 ) ) {

			buffer[isentence] = '\0';

			isentence == 0;

			put_packet( orbfd, buffer, srcname );

			memset( buffer, '\0', STRSZ );

			buffer[isentence++] = c;

		} else if( c == '\n' ) {

			buffer[isentence++] = c;
			buffer[isentence] = '\0';
			isentence = 0;

			put_packet( orbfd, buffer, srcname );

			memset( buffer, '\0', STRSZ );

			synchronizing = 1;
			
		} else {
			buffer[isentence++] = c;
		}
	}

	return 0;
}
