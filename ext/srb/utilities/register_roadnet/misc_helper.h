#ifndef _MISC_HELPER_H_
#define _MISC_HELPER_H_

#include <stdio.h>
#include <stdlib.h>
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


int isIpAddrRoutable(char *ip);
void setTM (struct tm* time, int year, int mon, int mday, int hour, int min, int sec);
void sortTM(struct tm* start_time, struct tm* end_time);
void swapInt(int *i1, int *i2);


#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/ext/srb/utilities/register_roadnet/Attic/misc_helper.h,v $
 * $Revision: 1.2 $
 * $Author: sifang $
 * $Date: 2005/01/07 03:01:17 $
 *
 * $Log: misc_helper.h,v $
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */
