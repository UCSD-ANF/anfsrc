#include <unistd.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <termios.h>
#include <sys/time.h>
#include <fcntl.h>
#include <coords.h>
#include <netdb.h>
#include <stdio.h>
#include <stock.h>
#include <Pkt.h>
#include <orb.h>
#include "proto1.h"
#include "cayan2orb.h"

#define VERSION "$Revision: 1.3 $"

/*
 Copyright (c) 2003 The Regents of the University of California
 All Rights Reserved
 
 Permission to use, copy, modify and distribute any part of this software for
 educational, research and non-profit purposes, without fee, and without a
 written agreement is hereby granted, provided that the above copyright
 notice, this paragraph and the following three paragraphs appear in all
 copies.
 
 Those desiring to incorporate this software into commercial products or use
 for commercial purposes should contact the Technology Transfer Office,
 University of California, San Diego, 9500 Gilman Drive, La Jolla, CA
 92093-0910, Ph: (858) 534-5815.
 
 IN NO EVENT SHALL THE UNIVESITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
 DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
 LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF THE UNIVERSITY
 OF CALIFORNIA HAS BEEN ADIVSED OF THE POSSIBILITY OF SUCH DAMAGE.
 
 THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
 CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
 ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF CALIFORNIA MAKES NO
 REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EITHER IMPLIED OR
 EXPRESS, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT THE USE OF THE
 SOFTWARE WILL NOT INFRINGE ANY PATENT, TRADEMARK OR OTHER RIGHTS.

   This code was created as part of the ROADNet project.
   See http://roadnet.ucsd.edu/ 

   Written By: Todd Hansen 1/3/2003
   Updated By: Todd Hansen 9/30/2003

   The data loggers this code communicates with were created by Douglas
   Alden, using a protocol he specified.
*/

extern unsigned char goodframenum;
extern double starttime;
extern double DATASAMPRATE;
extern double STATSAMPRATE;
extern int verbose;

void p1_start2orb(int orbfd, unsigned char *buf)
{
  struct Packet *orbpkt;
  char srcname_full[116];
  double newtimestamp;
  static char *newpkt = NULL;
  int newpkt_size;
  static int newpkt_alloc_size=0;
  char epochstr[100];
  
  orbpkt =  newPkt() ;
  orbpkt->pkttype = suffix2pkttype("MGENC");

  sprintf(epochstr,"%x%02x/%x/%x %x:%x:%x",buf[8],buf[9],buf[10],buf[11],buf[12],buf[13],buf[14]);
  orbpkt->time=str2epoch(epochstr);
  if (verbose)
    fprintf(stderr,"pkttime=%f (%s)\n",orbpkt->time,epochstr);

  sprintf(epochstr,"%x%02x/%x/%x 0:0:0",buf[8],buf[9],buf[10],buf[11]);
  starttime=str2epoch(epochstr);

  orbpkt->nchannels=2;
  strncpy(orbpkt->parts.src_net,NETNAME,2);
  sprintf(epochstr,"%0x%x",buf[5],buf[6]);
  strncpy(orbpkt->parts.src_sta,epochstr,5);
  *(orbpkt->parts.src_chan)=0;
  *(orbpkt->parts.src_loc)=0;
  strncpy(orbpkt->parts.src_subcode,"stat",4);
  
  p1_numframes(orbpkt, epochstr, buf);
  p1_voltage(orbpkt, epochstr, buf);

  if (verbose)
    fprintf(stderr,"transfering stat pkt\n");

  if (stuffPkt(orbpkt, srcname_full, &newtimestamp, &newpkt, &newpkt_size, &newpkt_alloc_size)<0)
    {
      fprintf(stderr,"stuff failed\n");
      complain ( 0, "stuffPkt routine failed for pkt\n") ;
   }
  else if (orbput(orbfd, srcname_full, newtimestamp, newpkt, newpkt_size) < 0)
    {
      fprintf(stderr,"put failed\n");
      complain ( 0, "orbput fails %s\n",srcname_full );
    }  
  
  if (verbose)
    {
      fprintf(stderr,"put %s\n",srcname_full);
      showPkt(0,srcname_full,newtimestamp,newpkt,newpkt_size,stdout,PKT_UNSTUFF);
    }
  freePkt(orbpkt);
}

void p1_data2orb(int orbfd, unsigned char *buf)
{
  struct Packet *orbpkt;
  char srcname_full[116];
  double newtimestamp, pkttime;
  static char *newpkt = NULL;
  int newpkt_size;
  static int newpkt_alloc_size=0;
  char epochstr[100];

  sprintf(epochstr,"%x",buf[6]);
  pkttime=starttime+(atoi(epochstr)*60);
  sprintf(epochstr,"%x",buf[5]);
  pkttime+=atoi(epochstr)*60*60;
  if (verbose)
    fprintf(stderr,"pkttime=%f\n",pkttime);

  sprintf(epochstr,"%x%x",buf[2],buf[3]);
  if (!queue_test(epochstr,buf[4],pkttime))
    {
      if (verbose)
	fprintf(stderr,"duplicate packet, skipping\n");
      return;
    }

  orbpkt =  newPkt();
  orbpkt->pkttype = suffix2pkttype("MGENC");
  orbpkt->time=pkttime;
  orbpkt->nchannels=14;
  strncpy(orbpkt->parts.src_net,NETNAME,2);
  sprintf(epochstr,"%0x%x",buf[2],buf[3]);
  strncpy(orbpkt->parts.src_sta,epochstr,5);
  *(orbpkt->parts.src_chan)=0;
  *(orbpkt->parts.src_loc)=0;
  
  p1_pressure(orbpkt, epochstr, buf);
  p1_nwind0(orbpkt, epochstr, buf);
  p1_ewind0(orbpkt, epochstr, buf);
  p1_ngust0(orbpkt, epochstr, buf);
  p1_egust0(orbpkt, epochstr, buf);
  p1_nwind1(orbpkt, epochstr, buf);
  p1_ewind1(orbpkt, epochstr, buf);
  p1_ngust1(orbpkt, epochstr, buf);
  p1_egust1(orbpkt, epochstr, buf);
  p1_temp0(orbpkt, epochstr, buf);
  p1_temp1(orbpkt, epochstr, buf);
  p1_humidity(orbpkt, epochstr, buf);
  p1_rain(orbpkt, epochstr, buf);
  p1_solar(orbpkt, epochstr, buf);

  if (verbose)
    fprintf(stderr,"transfering pkt\n");

  if (stuffPkt(orbpkt, srcname_full, &newtimestamp, &newpkt, &newpkt_size, &newpkt_alloc_size)<0)
    {
      fprintf(stderr,"stuff failed\n");
      complain ( 0, "stuffPkt routine failed for pkt\n") ;
    }
  else if (orbput(orbfd, srcname_full, newtimestamp, newpkt, newpkt_size) < 0)
    {
      fprintf(stderr,"put failed\n");
      complain ( 0, "orbput fails %s\n",srcname_full );
    }  
  
  if (verbose)
    {
      fprintf(stderr,"put %s\n",srcname_full);
      showPkt(0,srcname_full,newtimestamp,newpkt,newpkt_size,stdout,PKT_UNSTUFF);
    }
  freePkt(orbpkt);
}


void p1_pressure(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* barometric pressure */
  if (verbose)
    fprintf(stderr,"adding channel pressure\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[7]*256+buf[8];
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"Pre",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"P",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end barometric pressure */
}

void p1_nwind0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* north wind */
  if (verbose)
    fprintf(stderr,"adding channel north wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
 
  pktchan->data[0]=buf[9]*16+(buf[10]/16); 
  if (pktchan->data[0] & 0x800)
  {
    pktchan->data[0] = -1 * (0xFFF - pktchan->data[0]); 
  }
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"NWD0",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0.1;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end north wind */
}

void p1_ewind0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* east wind */
  if (verbose)
    fprintf(stderr,"adding channel east wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[10]%16)*256+buf[11]; 
  if (pktchan->data[0] & 0x800)
  {
    pktchan->data[0] = -1 * (0xFFF - pktchan->data[0]);       
  }
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"EWD0",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0.1;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end east wind */
}

void p1_ngust0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* north gust */
  if (verbose)
    fprintf(stderr,"adding channel north gust\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[12]*16+(buf[13]/16);  
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"Ngst0",5);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end north gust */
}

void p1_egust0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* east gust */
  if (verbose)
    fprintf(stderr,"adding channel east gust\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[13]%16)*256+buf[14]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"Egst0",5);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"a",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end east gust */
}

void p1_nwind1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* north wind */
  if (verbose)
    fprintf(stderr,"adding channel north wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[15]*16+(buf[16]/16); 
  if (pktchan->data[0] & 0x800)
  {
    pktchan->data[0] = -1 * (0xFFF - pktchan->data[0]);       
  }
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"NWD1",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0.1;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end north wind */
}

void p1_ewind1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* east wind */
  if (verbose)
    fprintf(stderr,"adding channel east wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[16]%16)*256+buf[17]; 
  if (pktchan->data[0] & 0x800)
  {
    pktchan->data[0] = -1 * (0xFFF - pktchan->data[0]);       
  }
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"EWD1",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0.1;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end east wind */
}

void p1_ngust1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* north gust */
  if (verbose)
    fprintf(stderr,"adding channel north gust\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[18]*16+(buf[19]/16); 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"Ngst1",5);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end north gust */
}

void p1_egust1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* east gust */
  if (verbose)
    fprintf(stderr,"adding channel east gust\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[19]%16)*256+buf[20]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"Egst1",5);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"a",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end east gust */
}

void p1_temp0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* temp 0 */
  if (verbose)
    fprintf(stderr,"adding channel temp 0\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[21]*16+buf[22]/16; 
  pktchan->data[0]=(((pktchan->data[0]/4095.0) - 0.65107) / -0.0067966) * 10000;
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"T0",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"t",4);
  pktchan->nsamp=1;
  pktchan->calib=0.0001;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end temp 0 */
}

void p1_temp1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* temp 1 */
  if (verbose)
    fprintf(stderr,"adding channel temp 1\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[22]%16)*256+buf[23]; 
  pktchan->data[0]=(((pktchan->data[0]/4095.0) - 0.65107) / -0.0067966) * 10000;
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"T1",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"t",4);
  pktchan->nsamp=1;
  pktchan->calib=0.0001;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end temp 1 */
}

void p1_humidity(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* humidity */
  if (verbose)
    fprintf(stderr,"adding channel humidity\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[24]*256+buf[25]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"RH",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"p",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end humidity */
}

void p1_rain(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* rain */
  if (verbose)
    fprintf(stderr,"adding channel rain\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[26]*256+buf[27]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"RN",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"d",4);
  pktchan->nsamp=1;
  pktchan->calib=0.0001;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end rain */
}

void p1_solar(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* solar radiation  */
  if (verbose)
    fprintf(stderr,"adding channel solar radiation\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[28]*256+buf[29]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"SOL",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"W",4);
  pktchan->nsamp=1;
  pktchan->calib=0.6229598;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end solar radiation */
}

void p1_voltage(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* voltage */
  if (verbose)
    fprintf(stderr,"adding channel battery voltage\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[15]*256+buf[16]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"BAT",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"v",4);
  pktchan->nsamp=1;
  pktchan->calib=0.00437738;
  pktchan->calper=-1;
  pktchan->samprate=STATSAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end voltage */
}

void p1_numframes(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* num frames */
  if (verbose)
    fprintf(stderr,"adding channel num frames\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[7]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"num",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"c",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=STATSAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end num frames */
}

