#ifndef _p_libuser_
#define _p_libuser_

#define NMEA_CURRENT_VERSION 100
#define IMG_CURRENT_VERSION 110

#ifdef  __cplusplus
extern "C" {
#endif

extern int stuff_ORACLEpf (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz);
extern int unstuff_ORACLEpf (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt);
extern void showPkt_ORACLEpf( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
extern int unstuff_NMEA ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_NMEA ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int stuff_VORB ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int unstuff_VORB ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_orsci ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int unstuff_orsci ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_wicor ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int unstuff_wicor ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_davis ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int unstuff_davis ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_sbe39 ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int unstuff_sbe39 ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int unstuff_IMG ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_IMG ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
void showPkt_IMG( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_NMEA( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_VORB( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_orsci( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_wicor( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_davis( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_sbe39( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );

#ifdef  __cplusplus
}
#endif

#endif
