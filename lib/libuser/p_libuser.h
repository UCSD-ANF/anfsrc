#ifndef _p_libuser_
#define _p_libuser_

#define NMEA_CURRENT_VERSION 100
#define IMG_CURRENT_VERSION 100

#ifdef  __cplusplus
extern "C" {
#endif

extern int unstuff_NMEA ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_NMEA ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int stuff_VORB ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
extern int unstuff_VORB ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int unstuff_IMG ( char *srcname, double time, char *packet, int nbytes, Packet *pkt );
extern int stuff_IMG ( Packet *pkt, char *srcname, double *time, char **packet, int *nbytes, int *packetsz );
void showPkt_IMG( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_NMEA( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );
void showPkt_VORB( int pktid, char *srcname, double pkttime, char *pkt, int nbytes, FILE *file, int mode );

#ifdef  __cplusplus
}
#endif

#endif
