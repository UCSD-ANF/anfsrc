#ifndef __orbprot__
#define __orbprot__

#include "bns.h"
#define ORBMAGIC             0x6d62726f /* 'orbm' */
#define ORBSRCNAME_SIZE 64
#define ORBWHO_SIZE 24
#define ORBWHAT_SIZE 128
#define ORBHOST_SIZE 128
#define ORBVERSION_SIZE 128
#define ORBSYNC "orbm"
#define NORBSYNC 4  /* = strlen(ORBSYNC) */
#define ORBPUT               1
#define ORBGET               2
#define ORBREAP              3
#define ORBSTAT              4
#define ORBCLIENTS	     5
#define ORBSOURCES	     6
#define ORBSEEK              7
#define ORBTELL              8
#define ORBSELECT            9
#define ORBREJECT	     10
#define ORBCLOSE             11
#define ORBAFTER             12
#define ORBBEFORE            13
#define ORBPING              14
#define ORBHDR               15
#define ORBSETPRI	     16 
#define ORBHALT              17
#define ORBSETLOGGING	     18
#define ORBERROR  	     19
#define ORBOPEN 	     20
#define ORBKILL 	     21
#define ORBID		     23
#define ORBRUP		     24
#define ORBPUTL              25
#define ORBGETL              26
#define ORBREAPL             27
#define ORBSTASHSELECT	     28
#define ORBGETSTASH	     29
#define ORB_ENDREAP	    -32
#define SELECTMAX 96

#define STASH_ALL		0
#define STASH_ONLY		1
#define NO_STASH		2

typedef struct Pktpkg {
    double          time;		/* time of packet */
    char            *packet;
    int             sZpacket;		/* malloc size of packet */
    int             pktid;		/* packet id */
    int		    packetsize;		/* packet size */
    unsigned short  srcnamesize;	/* length of source name */
    char            srcname[ORBSRCNAME_SIZE];	/* source name */
} Pktpkg ; 

typedef struct Orbsrc {
    double          slatest_time;	/* time of latest packet on orb */
    double          soldest_time;	/* time of oldest packet on orb */
    int             nbytes;		/* # of bytes on orb */
    int             npkts;		/* # of packets on orb */
    int             slatest;		/* pktid of latest packet on orb */
    int             soldest;		/* pktid of oldest packet on orb */
    int             active;		/* data originating now on this port */
    char            srcname[ORBSRCNAME_SIZE];	/* = "" source name */
} Orbsrc ; 

typedef struct Orbclient {
    double          lastpkt;	/* time of latest packet to/from client */
    double          started;	/* time client was connected */
    unsigned int    read;	/* #bytes read */
    int             pid;	/* pid of client */
    unsigned int    bytes;	/* packet bytes to/from this client */
    unsigned int    packets;	/* number of packets to/from this client */
    int             pktid;	/* current packet id */
    int             port;	/* client port on client machine */
    char            address[4];	/* ip address of client machine */
    int             thread;	/* thread to which client is connected */
    int             fd;	/* port to which client is connected */
    int             nreject;	/* number of characters in reject */
    int             nselect;	/* number of characters in select */
    int             errors;	/* # errors from this client */
    int             priority;	/* priority for client */
    int             lastrequest;	/* # last request from client */
    int             mymessages;	/* thread flag to print messages if != 0 */
    unsigned int    nrequests;	/* # requests from client */
    unsigned int    nwrites;	/* #write calls */
    unsigned int    nreads;	/* #read calls */
    unsigned int    written;	/* #bytes written */
    char            perm;	/* permission (r or w) */
    char            what[ORBWHAT_SIZE];	/* command line for client machine */
    char            host[ORBHOST_SIZE];	/* hostname of client machine */
    char            who[ORBWHO_SIZE];	/* user running client */
    char            select[SELECTMAX];	/* current selection expression */
    char            reject[SELECTMAX];	/* current rejection expression */
} Orbclient ; 

typedef struct OrbOpenString {
    int             pid;	/* pid of client */
    int             handshake;	/* another sanity check */
    char            perm;	/* permission (r or w) */
    char            what[ORBWHAT_SIZE];	/* command line for client machine */
    char            who[ORBWHO_SIZE];	/* user running client */
} OrbOpenString ; 

typedef struct Orbstat {
    double          when;	/* time when this status was taken */
    double          started;	/* start time of orb server */
    double          orb_start;	/* last time buffer was initialized */
    int             connections;	/* global flag to print all connection open and closes if != 0 */
    int             messages;	/* global flag to print all messages if != 0 */
    unsigned int    maxdata;	/* max data bytes */
    int             errors;	/* number of threads exiting with errors */
    int             rejected;	/* number of failed opens */
    int             closes;	/* number of closes */
    int             opens;	/* number of opens */
    int             port;	/* port number for server requests */
    char            address[4];	/* ip address */
    int             pid;	/* pid for orbserver */
    int             nsources;	/* number of sources */
    int             nclients;	/* number of clients */
    int             maxsrc;	/* maximum number of sources */
    int             maxpkts;	/* max #packets */
    char            version[ORBVERSION_SIZE];	/* version code */
    char            who[ORBWHO_SIZE];	/* who ran the orbserver */
    char            host[ORBHOST_SIZE];	/* hostname on which orbserver runs */
} Orbstat ; 

typedef struct Orbrequest {
    double          time;
    double          reap_maxtime;
    char            srcname[ORBSRCNAME_SIZE];	/* = "" source name */
    char            *reject;
    Pktpkg          *pkg;
    char            *select;
    OrbOpenString   *hello;
    int             thread;
    int		    stashflag ;
    int             newpri;
    int             sZpkg; /* malloc size of pkg */
    int             logflag;
    int             sZreject; /* malloc size of reject */
    int             pktcode;
    int             nreject;	/* # of characters in reject + 1 */
    int             sZselect; /* malloc size of select */
    int             reap_maxpkts;
    int             nselect;	/* # of characters in select + 1 */
    int             sZhello; /* malloc size of hello */
    int             reap_maxbytes;
    int             athread;
    int             what;	/* request code */
} Orbrequest ; 

typedef struct Orbresponse {
    double          source_when;
    double          client_when;
    double          server_start;	/* when orbserver was started */
    double          orb_start;	/* when orb ring buffer was last reset */
    Orbsrc          *source;
    Pktpkg          *pkg;
    Orbclient       *client;
    Orbstat         orbstat;
    int             nsource;
    int             sZclient; /* malloc size of client */
    int             nclient;
    int             pktid;
    int             sZpkg; /* malloc size of pkg */
    int             nselections;
    int             version;
    int             thread;
    int		    stashflag ;
    int             latest_pktid;	/* latest packet id */
    int             nerr;
    int             sZsource; /* malloc size of source */
    int             active;	/* 1 if thread is active, 0 otherwise */
    int             result;	/* result code */
    int             what;	/* echo request */
    char            errmsg[512];
} Orbresponse ; 

#ifdef  __cplusplus
extern "C" {
#endif

extern Pktpkg * newPktpkg () ;
extern int gbnsPktpkg (Bns *bns, int what, Pktpkg *s ) ;
extern int pbnsPktpkg (Bns *bns, int what, Pktpkg *s ) ;
extern void dbgPktpkg (Pktpkg *s, FILE *file, int flag) ;
extern void initPktpkg (Pktpkg *s) ;
extern void askPktpkg (Pktpkg *s ) ;
extern void freePktpkg (Pktpkg *s) ;

extern Orbsrc * newOrbsrc () ;
extern int gbnsOrbsrc (Bns *bns, Orbsrc *s ) ;
extern int pbnsOrbsrc (Bns *bns, Orbsrc *s ) ;
extern void dbgOrbsrc (Orbsrc *s, FILE *file, int flag) ;
extern void initOrbsrc (Orbsrc *s) ;
extern void askOrbsrc (Orbsrc *s ) ;
extern void freeOrbsrc (Orbsrc *s) ;

extern Orbclient * newOrbclient () ;
extern int gbnsOrbclient (Bns *bns, Orbclient *s ) ;
extern int pbnsOrbclient (Bns *bns, Orbclient *s ) ;
extern void dbgOrbclient (Orbclient *s, FILE *file, int flag) ;
extern void initOrbclient (Orbclient *s) ;
extern void askOrbclient (Orbclient *s ) ;
extern void freeOrbclient (Orbclient *s) ;

extern OrbOpenString * newOrbOpenString () ;
extern int gbnsOrbOpenString (Bns *bns, OrbOpenString *s ) ;
extern int pbnsOrbOpenString (Bns *bns, OrbOpenString *s ) ;
extern void dbgOrbOpenString (OrbOpenString *s, FILE *file, int flag) ;
extern void initOrbOpenString (OrbOpenString *s) ;
extern void askOrbOpenString (OrbOpenString *s ) ;
extern void freeOrbOpenString (OrbOpenString *s) ;

extern Orbstat * newOrbstat () ;
extern int gbnsOrbstat (Bns *bns, Orbstat *s ) ;
extern int pbnsOrbstat (Bns *bns, Orbstat *s ) ;
extern void dbgOrbstat (Orbstat *s, FILE *file, int flag) ;
extern void initOrbstat (Orbstat *s) ;
extern void askOrbstat (Orbstat *s ) ;
extern void freeOrbstat (Orbstat *s) ;

extern Orbrequest * newOrbrequest () ;
extern int gbnsOrbrequest (Bns *bns, Orbrequest *s ) ;
extern int pbnsOrbrequest (Bns *bns, Orbrequest *s ) ;
extern void dbgOrbrequest (Orbrequest *s, FILE *file, int flag) ;
extern void initOrbrequest (Orbrequest *s) ;
extern void askOrbrequest (Orbrequest *s ) ;
extern void freeOrbrequest (Orbrequest *s) ;

extern Orbresponse * newOrbresponse () ;
extern int gbnsOrbresponse (Bns *bns, Orbresponse *s ) ;
extern int pbnsOrbresponse (Bns *bns, Orbresponse *s ) ;
extern void dbgOrbresponse (Orbresponse *s, FILE *file, int flag) ;
extern void initOrbresponse (Orbresponse *s) ;
extern void askOrbresponse (Orbresponse *s ) ;
extern void freeOrbresponse (Orbresponse *s) ;

#ifdef  __cplusplus
}
#endif

#endif
