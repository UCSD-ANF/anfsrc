#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <signal.h>

#include "stock.h"
#include "Pkt.h"

#include "p_libuser.h"
#include "libuser.h"


int
stuff_sbe39 (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
  fprintf(stderr, "can't stuffpkt_sbe39(not implemented) packet %d from %s\n", srcname );
  complain(0, "can't stuff sbe39 packet,sorry\n");
  return -1;
}

int
unstuff_sbe39 (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
  unsigned char c;
  PktChannel *channel;
  Srcname srcparts;
  Tbl *splits;
  char i;
  char epochstr[150];
  double samrate;
  float val;
  char timestr[500];
  char timestr2[500];
  int day, year,hr,min,sec;

  clrPkt(pkt);
  freetbl(pkt->channels,freePktChannel);
  pkt->channels=newtbl(0);

  if (ntohs(*(short int*)packet)!=100)
    {
      complain(0,"unstuff_sbe39, version mismatch, expected 100, got %d\n",pkt->version);
      return(-1);
    }

  samrate=ntohs(*(short int*)(packet+2));
  if (samrate>0)
    {
      samrate=1.0/samrate;
    }
  else
    samrate=0;

  pkt->nchannels=0;
  pkt->pkttype=suffix2pkttype("MGENC");

  i=4;
  if (*(packet+i)=='T')
      while(*(packet+i)!='\0' && *(packet+i)!='\r')
	i++;

  if (*(packet+i)=='\r')
    i++;

  if (sscanf(packet+i," %f, %d %s %d, %d:%d:%d\r",&val,&day,timestr,&year,&hr,&min,&sec)!=7)
    {
      elog_complain(1,"can't parse SBE39 format (%s)",packet+i);
      return(-1);
    }

  sprintf(timestr2,"%02d %s %04d %02d:%02d:%02d US/Pacific",day,timestr,year,hr,min,sec);

  pkt->time=str2epoch(timestr2);

  split_srcname(srcname,&srcparts);

  strcpy(pkt->parts.src_net,srcparts.src_net);
  strcpy(pkt->parts.src_sta,srcparts.src_sta);
  *(pkt->parts.src_chan)='\0';
  *(pkt->parts.src_loc)='\0';
  strcpy(pkt->parts.src_suffix,"MGENC");
  *(pkt->parts.src_subcode)='\0';

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  channel->time=pkt->time;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->nsamp=1;
  channel->datasz=1;
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"watertemp");
  *(channel->loc)='\0';
      
  *(channel->data)=val*10000;
  strcpy(channel->segtype,"t");
  channel->calib=0.0001;

  pushtbl(pkt->channels,channel);
  pkt->nchannels++;
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  channel->time=pkt->time;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->nsamp=1;
  channel->datasz=1;
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"timeskew");
  *(channel->loc)='\0';
      
  *(channel->data)=pkt->time-ipkttime;
  strcpy(channel->segtype,"T");
  channel->calib=1;

  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  return Pkt_wf;
}

void showPkt_sbe39( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
  write(0,"sbe39 packet:\n",13);
  write(0,pkt+5,strlen(pkt+5));
  write(0,"\n",1);
}
