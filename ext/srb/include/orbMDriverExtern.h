

#ifndef ORB_MDRIVER_EXTERN_H
#define ORB_MDRIVER_EXTERN_H

#ifdef ORB_MD
#include "MDriverExtern.h"

#include"c.h"
#include"srb.h"





#define VORBPKTHEADER 256
#define MAX_HTML_ROW_SIZE 2048
#define TMP_STRING_SIZE 256
#define MIN_ORB_BUF_SIZE 1000
#define MAX_CURVE_SIZE 8000

#include <fcntl.h>      /* most O_ */
#ifndef O_RDONLY
#include <sys/file.h>   /* The rest of O_ */
#endif /* O_RDONLY */

typedef struct {
  int   fd;
  int   firstRead;
  int   timeout;
  int   numofpkts;
  int   numbulkreads;
  int   orbFlags;
  int   orbMode;
  char *which;
  char *presentation;
  char *select;
  char *reject;
  char *after;
  char *position;
  char *rsrcInfo;
  char *userName;
  char *reapMemBegPtr; 
  char *reapMemCurPtr;
  int  reapMemRemSize;
}orbStateInfo;

extern int freeOrbStateInfo(orbStateInfo *orbSI);
extern int getOrbStateInfo(orbStateInfo *orbSI, char *rsrcInfo,
	   char *orbDataDesc, int orbFlags, int orbMode, char *userName);
extern int orbSpres(int first, orbStateInfo *orbSI, char *srcname,
       double vorbtime, int pktid, int nbytes, char *vorbpacket, char *buffer);
extern int orbSpresGPSHTML(int first, int last,char *srcname,double vorbtime, 
	  int pktid, int nbytes, char *vorbpacket, char *inbuffer);

extern int orbSpresGPSXML(int first, int last, char *srcname,double vorbtime, 
	  int pktid, int nbytes, char *vorbpacket, char *inbuffer);
extern int orbSpresWAVJAV1(int first, int last, char *srcname,double vorbtime,
	  int pktid, int nbytes, char *vorbpacket, char *inbuffer, char *pres);

#endif /* ORB_MD */
 
#endif  /* ORB_MDRIVER_EXTERN_H */

