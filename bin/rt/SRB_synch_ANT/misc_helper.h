#ifndef _MISC_HELPER_H_
#define _MISC_HELPER_H_

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <malloc.h>
#include <time.h>

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

#ifndef STRNCPY
#define STRNCPY(dest, src, n)	{ strncpy(dest,src,n); dest[n-1]=0; }
#endif

#ifndef  DIE
#define  DIE( ... ) { printf("Program cannot continue because: "); printf(__VA_ARGS__); printf("\n"); exit(1); }
#endif


int isIpAddrRoutable(char *ip);
void setTM (struct tm* time, int year, int mon, int mday, int hour, int min, int sec);
void sortTM(struct tm* start_time, struct tm* end_time);
void swapInt(int *i1, int *i2);
char* strtrim(char *s);

#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/misc_helper.h,v $
 * $Revision: 1.1 $
 * $Author: sifang $
 * $Date: 2005/01/11 03:38:10 $
 *
 * $Log: misc_helper.h,v $
 * Revision 1.1  2005/01/11 03:38:10  sifang
 *
 * rewrote SRB style makefile to Antelope style makefile. Also changed its position from Vorb/ext/srb/utilities to here.
 *
 * Revision 1.3  2005/01/08 04:10:57  sifang
 *
 * Add a config file feature, "-r", into the program. So the user could not load his/her own costumized config file with ease. Also added a sample config file with instructions.
 *
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */
