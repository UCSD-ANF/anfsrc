#ifndef _ORBCONST_H_
#define _ORBCONST_H_

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
#define MIN_REOPEN_TIME 10  /* minimum allowed time in seconds between reopen attempts */
#define ORB_BUF_SIZE 8192   /* initial size allocated to bns buffers */

#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/Attic/orb_const.h,v $
 * $Revision: 1.1 $
 * $Author: sifang $
 * $Date: 2005/01/11 03:38:10 $
 *
 * $Log: orb_const.h,v $
 * Revision 1.1  2005/01/11 03:38:10  sifang
 *
 * rewrote SRB style makefile to Antelope style makefile. Also changed its position from Vorb/ext/srb/utilities to here.
 *
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */