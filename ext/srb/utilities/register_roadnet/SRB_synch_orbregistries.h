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
#include "misc_helper.h"
#include "ds_helper.h"
#include "srb_helper.h"
#include "source.h"

#define DEFAULT_CONFIG_FILE "config.sample" 

typedef struct UserConfigParam
{
  char srb_host[200];
  char srb_port[100];
  char srb_password[100];
  char srb_username[100]; 
  char srb_domain[100];
  char srb_zone[100];     
  char srb_collection_registries[MAX_DATA_SIZE];       
  char srb_collection_registered_orbs[MAX_DATA_SIZE];
  char srb_orb_rsrc[MAX_DATA_SIZE];
} UserConfigParam;

#endif

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/ext/srb/utilities/register_roadnet/Attic/SRB_synch_orbregistries.h,v $
 * $Revision: 1.2 $
 * $Author: sifang $
 * $Date: 2005/01/08 04:10:57 $
 *
 * $Log: SRB_synch_orbregistries.h,v $
 * Revision 1.2  2005/01/08 04:10:57  sifang
 *
 * Add a config file feature, "-r", into the program. So the user could not load his/her own costumized config file with ease. Also added a sample config file with instructions.
 *
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
