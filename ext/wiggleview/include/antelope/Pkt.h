#ifndef __pkt__
#define __pkt__

#include "tr.h"
#include "stock.h"
#include "orb.h"

extern Xlat Pktxlat[] ;
extern int Pktxlatn ;

/*  ORB Packet structure/types definitions  */

#define PKT_NAMESIZE 10  /* Don't change!! 
				-- used for field size in several packets */
#define PKT_TYPESIZE 32

typedef struct PktChannel {
    int *data ;			/* Required */
    char *puser1 ;		
    double time ; 		/* Required */
    double samprate ; 		/* Required */
    double calib ; 		/* Required */
    double calper ;		/* Required */
    double duser1 ; 
    double duser2 ;
    int nsamp ; 		/* Required */
    int datasz ;		/* size of data buffer in **samples** */
    int	iuser1 ; 
    int iuser2 ;
    int iuser3 ;
    char net[PKT_TYPESIZE] ;	/* Required */
    char sta[PKT_TYPESIZE] ;	/* Required */
    char chan[PKT_TYPESIZE] ;	/* Required */
    char loc[PKT_TYPESIZE] ;	/* Required */
    char segtype[4];		/* Required */
    char cuser1[64] ; 
    char cuser2[64] ;
    Hook *hook ; 		/* for a program's private use */
} PktChannel ;

typedef struct Srcname {
    char src_net[PKT_TYPESIZE] ;
    char src_sta[PKT_TYPESIZE] ;
    char src_chan[PKT_TYPESIZE] ;
    char src_loc[PKT_TYPESIZE] ;
    char src_suffix[PKT_TYPESIZE] ;
    char src_subcode[PKT_TYPESIZE] ;
} Srcname ; 

typedef struct Packet {
    Srcname parts ;
    double time ;
    struct PacketType *pkttype ;		
    int nchannels ;  		/* Required */
    Tbl *channels ;
    Pf *pf ; 
    char *string ;		/* character string */
    int string_size ;		/* length of string including null byte -- if zero, use strlen(string) */
    Dbptr db ;
    char *dfile ;		/* in case file is included */
    int   dfile_size ; 		/* # bytes in dfile */
    int version ;		/* highly recommended */
    Hook *pkthook ;		/* for a program's private use */
} Packet ;

typedef struct PacketType {
    char *name ; 
    char *suffix ;
    int content ;
    int hdrcode ; 
    int bodycode ;
    char *desc ;
    int (*stuff) (Packet *, char *, double *, char **, int *, int *) ;
    int (*unstuff) (char *, double, char *, int, Packet *) ;
} PacketType ;

#define Pkt_wf	1	/* waveform packet */
#define Pkt_st	2	/* status packet */
#define Pkt_db	3	/* database row */
#define Pkt_pf	4	/* parameter file */
#define Pkt_cn	5	/* control messages */
#define Pkt_rw  6	/* arbitrary binary data, wrapped in orb packet */
#define Pkt_ch  7	/* arbitrary character string */
#define Pkt_tp  8	/* test packet */ 
#define Pkt_stash  9	/* stash packet */ 

/* levels of verbosity for showPkt */
#define PKT_DUMP 	1	/* hex dump */
#define PKT_UNSTUFF 	2	/* unstuff, print all data samples */
#define PKT_NOSAMPLES 	3	/* unstuff, print no data samples */
#define PKT_TERSE	4	/* just show the header information */

extern PacketType PktList[] ;
extern int nPktList ;
extern Arr *PktTypes ;

#ifdef  __cplusplus
extern "C" {
#endif

extern PktChannel * newPktChannel ( void );
extern Packet * newPkt ( void );
extern void clrPktChannel ( PktChannel *achan );
extern void clrPkt ( Packet *pkt );
extern void freePktChannel ( PktChannel *achan );
extern void freePkt ( Packet *Pkt );
extern void join_srcname ( Srcname *parts, char *srcname );
extern void split_srcname ( char *srcname, Srcname *parts );
extern PacketType * header2pkttype ( short hdrcode, short bodycode );
extern PacketType * suffix2pkttype ( char *suffix );
extern int unstuffPkt ( char *srcname, double time, char *packet, int nbytes, Packet **pktp );
extern int stuffPkt ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int stuffStashPkt ( char *stash, int nstash, char **packet, int *nbytes, int *packetsz );

extern int unstuffPkt_User ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuffPkt_User ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );

extern void showPkt ( int pktid, char *srcname, double pkttime, char *packet, int nbytes, FILE *file, int mode );

#ifdef  __cplusplus
}
#endif

#endif
