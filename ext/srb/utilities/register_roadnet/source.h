#ifndef _SOURCE_H_
#define _SOURCE_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <time.h>
#include <errno.h>

#define SIZEOF_SRCNAME       64 /* from css registry1.2*/
#define SIZEOF_SERVERADDRESS 30 /* from css registry1.2*/
#define SIZEOF_SERVERPORT    10 /* from css registry1.2*/
#define SIZEOF_ORBSTARTDATE  50
#define SIZEOF_REGDATE       50 
#define SIZEOF_DATATYPE      64
#define SIZEOF_SRBNAME       SIZEOF_SRCNAME+SIZEOF_SERVERADDRESS+SIZEOF_SERVERPORT+10
#define SIZEOF_PLACE 100
#define SIZEOF_OWNER 100
#define SIZEOF_ELEVATION 100
#define SIZEOF_LAT       100
#define SIZEOF_LON       100
#define SIZEOF_DESC      200
#define SIZEOF_SRBPATH   SIZEOF_OWNER+10+SIZEOF_SERVERADDRESS+sizeof("::")+SIZEOF_SERVERPORT+sizeof("<ORBSELECT>")+SIZEOF_SRCNAME+sizeof("</ORBSELECT><ORBTIMEOUT>")+10+sizeof("</ORBTIMEOUT><ORBNUMOFPKTS>")+10+sizeof("</ORBNUMOFPKTS>?SHADOW")+10

//#define SIZEOF_SRATE     100
//#define SIZEOF_BAND      100
//#define SIZEOF_CALIB     100
//#define SIZEOF_LDDATE    100   /*time of last update */

typedef struct Source
{
  char srcname[SIZEOF_SRCNAME];
  char serveraddress[SIZEOF_SERVERADDRESS];
  char serverport[SIZEOF_SERVERPORT];
  char orb_start[SIZEOF_ORBSTARTDATE]; /*orb start date*/
  char datatype[SIZEOF_DATATYPE];
  char srbname[SIZEOF_SRBNAME];       /*srb name for this obj*/
  char regdate[SIZEOF_REGDATE];       /*srb object registered date*/
  char place[SIZEOF_PLACE];
  char owner[SIZEOF_OWNER];
  char desc[SIZEOF_DESC];
  
  //char srate[SIZEOF_SRATE];  /* sampling rate */
  //char srate_lddate[SIZEOF_LDDATE]; /* last updated date for srate */
  //char band[SIZEOF_BAND];
  //char band_lddate[SIZEOF_LDDATE]; /* last updated date for band */
  //char calib[SIZEOF_CALIB];
  //char calib_lddate[SIZEOF_LDDATE]; /* last updated date for calib */  
  
} Source;

// in-line functions
#define  DEBUGON
#ifdef   DEBUGON

#ifndef  DEBUG
#define  DEBUG( ... ) { fprintf(stderr, ">>>>\"%s:%u\" %s: ",__FILE__,__LINE__, __FUNCTION__); fprintf(stderr, __VA_ARGS__); fprintf( stderr, "\n"); }
#endif

#else

#ifndef  DEBUG
#define  DEBUG( ... ) 
#endif 

#endif

#ifndef FREEIF
#define FREEIF(pi)		{ if (pi) { free((void *)pi); (pi)=0; }}
#endif


void printSource(Source *s);
void clearSource(Source *s);
void setSrcname(Source *s, char *srcname);
void setServeraddress(Source *s, char *serveraddress);
void setServerport(Source *s, char *serverport);
void setOrbStart(Source *s, char *orb_start);
void setDatatype(Source *s, char *datatype);
void setRegdate(Source *s, char *regdate);
void setSrbname(Source *s, char *srbname);
void setOwner(Source *s, char *owner);
void setDatatypeAuto(Source *s);
void setRegdateAuto(Source *s);
void setSrbnameAuto(Source *s);
void setSourceBasic(Source *s, char *srcname, char *serveraddress, char *serverport,
                char *orb_start, char *owner);
void resetSource(Source *s);                
char* constructSRBPath(Source *s);
int isSameSource(Source *s1, Source *s2);
int isSourceUpdateNeeded (Source *s1, Source *s2);
#endif
