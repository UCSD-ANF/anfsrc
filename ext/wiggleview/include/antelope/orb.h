#ifndef _orb_
#define _orb_

#include "db.h"
#include "stock.h"
#include "orbprot.h"

#define ORB_TCP_PORT 6510

#define ORB_EOF		-9
#define ORB_INCOMPLETE	-2

#define ORBCURRENT 	-10
#define ORBNEXT    	-11
#define ORBPREV	   	-12
#define ORBOLDEST  	-13
#define ORBNEWEST  	-14
#define ORBNEXT_WAIT	-15
#define ORBNEXTT	-16
#define ORBPREVT	-17
#define ORBSTASH	-18
#define ORBPREVSTASH	-19

#define ALL_MSGS	1
#define MY_MSGS		2
#define CONNECTIONS	3

#define ORB_MAX_DATA_BYTES 1000000

#define ORB_TEPSILON 1.0e-5 /* dt used in orbreopen to back off lastpkttime */
#define MIN_REOPEN_TIME 1  /* minimum allowed time in seconds between reopen attempts */
#define ORB_BUF_SIZE 8192   /* initial size allocated to bns buffers */

extern Xlat Orbxlat[], Orbconst[] ;
extern int Orbxlatn, Orbconstn ;

#define orbflush(ORB)

#ifdef  __cplusplus
extern "C" {
#endif

extern Pktpkg * newPktpkg ( void );
extern Orbsrc * newOrbsrc ( void );
extern void initOrbsrc ( Orbsrc *s );
extern void freeOrbsrc ( Orbsrc *s );
extern void dbgOrbsrc ( Orbsrc *s, FILE *file, int flag );
extern void askOrbsrc ( Orbsrc *s );
extern int gbnsOrbsrc ( Bns *bns, Orbsrc *s );
extern int pbnsOrbsrc ( Bns *bns, Orbsrc *s );
extern Orbclient * newOrbclient ( void );
extern void initOrbclient ( Orbclient *s );
extern void freeOrbclient ( Orbclient *s );
extern void dbgOrbclient ( Orbclient *s, FILE *file, int flag );
extern void askOrbclient ( Orbclient *s );
extern int gbnsOrbclient ( Bns *bns, Orbclient *s );
extern int pbnsOrbclient ( Bns *bns, Orbclient *s );
extern OrbOpenString * newOrbOpenString ( void );
extern void initOrbOpenString ( OrbOpenString *s );
extern void freeOrbOpenString ( OrbOpenString *s );
extern void dbgOrbOpenString ( OrbOpenString *s, FILE *file, int flag );
extern void askOrbOpenString ( OrbOpenString *s );
extern int gbnsOrbOpenString ( Bns *bns, OrbOpenString *s );
extern int pbnsOrbOpenString ( Bns *bns, OrbOpenString *s );
extern Orbstat * newOrbstat ( void );
extern void initOrbstat ( Orbstat *s );
extern void freeOrbstat ( Orbstat *s );
extern void dbgOrbstat ( Orbstat *s, FILE *file, int flag );
extern void askOrbstat ( Orbstat *s );
extern int gbnsOrbstat ( Bns *bns, Orbstat *s );
extern int pbnsOrbstat ( Bns *bns, Orbstat *s );
extern Orbrequest * newOrbrequest ( void );
extern void initOrbrequest ( Orbrequest *s );
extern void freeOrbrequest ( Orbrequest *s );
extern void dbgOrbrequest ( Orbrequest *s, FILE *file, int flag );
extern void askOrbrequest ( Orbrequest *s );
extern int gbnsOrbrequest ( Bns *bns, Orbrequest *s );
extern int pbnsOrbrequest ( Bns *bns, Orbrequest *s );
extern Orbresponse * newOrbresponse ( void );
extern void initOrbresponse ( Orbresponse *s );
extern void freeOrbresponse ( Orbresponse *s );
extern void dbgOrbresponse ( Orbresponse *s, FILE *file, int flag );
extern void askOrbresponse ( Orbresponse *s );
extern int gbnsOrbresponse ( Bns *bns, Orbresponse *s );
extern int pbnsOrbresponse ( Bns *bns, Orbresponse *s );
extern int orbid ( int orb, int *mythread );
extern int orbopen ( char *name, char *perm );
extern int orbrup ( char *name, int athread, double *orb_start, double *server_start, int *latest_pktid );
extern int orbclose ( int orb );
extern int orbput ( int orb, char *srcname, double time, char *packet, int nbytes );
extern int orbget ( int orb, int which, int *pktid, char *srcname, double *time, char **packet, int *nbytes, int *bufsize );
extern int orbgetstash (int orb, char *srcname, double *time, char **packet, int *nbytes, int *bufsize);
extern int orbreap ( int orb, int *pktid, char *srcname, double *time, char **packet, int *nbytes, int *bufsize );
extern int orbreap_timeout ( int orb, int maxseconds, int *pktid, char *srcname, double *time, char **packet, int *nbytes, int *bufsize );
extern int orbreap_nd ( int orb, int *pktid, char *srcname, double *time, char **packet, int *nbytes, int *bufsize );
extern int orbreapt ( int orb, double maxtime, int *pktid, char *srcname, double *time, char **packet, int *nbytes, int *bufsize );
extern int orbreaphdr ( int orb, int *pktid, char *srcname, double *time );
extern int orbreapn ( int orb, int maxpkts, int *pktid, char *srcname, double *time, char **packet, int *nbytes, int *bufsize );
extern int orbseek ( int orb, int which );
extern int orbset_logging ( int orb, int which );
extern int orbtell ( int orb );
extern int orbping ( int orb, int *version );
extern int orbselect ( int orb, char *select );
extern int orbreject ( int orb, char *reject );
extern int orbafter ( int orb, double time );
extern int orbstat ( int orb, Orbstat **orbstat );
extern int orbsources ( int orb, double *when, Orbsrc **source, int *nsource );
extern int orbclients ( int orb, double *when, Orbclient **client, int *nclient );
extern int orbhalt ( int orb );
extern int orbkill ( int orb, int thread );
extern int orbsetpri ( int orb, int thread, int newpri );
extern int orbresurrect ( int orb, int *last_pktid, double *last_pkttime );
extern int pf2orbpkt ( Pf *pf, char *name, int orb );
extern int orbpkt2pf ( char *packet, int packet_size, Pf **pf );
extern int setsocksize ( int fd, int sendsize, int recvsize );
extern int orbdelta ( int orb, char *re_string, int *ndelta );
extern int orbwait ( int orb, char *re_string, double mintime, double timeout );
extern int orbposition ( int orb, char *from );
extern int orbstashselect ( int orb, int stashflag ) ;

#ifdef  __cplusplus
}
#endif

#endif 
