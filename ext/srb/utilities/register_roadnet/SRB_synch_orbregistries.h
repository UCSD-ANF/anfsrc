/*
 * Description: Please read SETUP and man page before configure/build/run this program
 */
 
#ifndef _REGISTER_ORB_H_
#define _REGISTER_ORB_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <sys/types.h>
#include <time.h>
#include <errno.h>
#include "scommands.h"
#include "ds_helper.h"
#include "srb_helper.h"
#include "source.h"

/* The srb server connection requirments to be used.                            */
/* This srb server should also contain the following:                           */
/*     1. SRB_COLLECTION_REGISTRIES: orb registry databases (as SRB objects)    */
/*        Note: - this collection should contain only registry dbs              */
/*              - you will need to register all database as SRB objects 1st     */
/*     2. SRB_COLLECTION_REGISTERED_ORBS: where orbs should be registered       */
/*     3. SRB_RSRC_MERCALI_ORB: SRB resource to be used for registering orbs    */ 
#define  SRB_HOST "mercali.ucsd.edu"
#define  SRB_PORT "8829"
#define  SRB_PASSWORD "SIOSRB"
#define  SRB_USERNAME "siosrb"
#define  SRB_DOMAIN "sio"
#define  SRB_ZONE "sdscdlib" 
 
#define  SRB_COLLECTION_REGISTRIES "/home/siosrb.sio/Datascope Registries"
#define  SRB_COLLECTION_REGISTERED_ORBS "/home/siosrb.sio/Registered ORBs"

#define  SRB_RSRC_MERCALI_ORB "mercali-orb-1"

/* when "-t" (test mode is picked), up to how many orbs should the program exam */
/* and attempt to synch. You will not need to reconfigure this in most cases    */
/* for instance, if it's 3, then program will attempt to exam up to 3 orb       */
/* sources in the database                                                      */
#define  NUM_TESTCASE          10

#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/ext/srb/utilities/register_roadnet/Attic/SRB_synch_orbregistries.h,v $
 * $Revision: 1.1 $
 * $Author: sifang $
 * $Date: 2005/01/06 04:38:30 $
 *
 * $Log: SRB_synch_orbregistries.h,v $
 * Revision 1.1  2005/01/06 04:38:30  sifang
 *
 * initial checking for SRB_synch_orbregistries.
 *
 * This
 * utility reads in orb information from Datascope (Antelope) registry
 * databases, which are pre-registered as SRB objects, and attempt to
 * build/synchronize a collection of all ORB data sources stored across all
 * databases. Each Orb source is registered as a SRB object, and can be
 * queried though SRB. SRB_synch_orbregistries also insert metadata for each SRB-ORB. It is very
 * useful if you want to query the ORBs based on this metadata.
 *
 * Please read file "SETUP" to learn how to configure this program, and read the man file SRB_synch_orbregistries.1 to learn how to run the program.
 *
 *
 *
 * -
 *
 *
 */
