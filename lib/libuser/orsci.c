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
stuff_orsci (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
  fprintf(stderr, "can't stuffpkt_orsci(not implemented) packet %d from %s\n", srcname );
  complain(0, "can't stuff orsci packet,sorry\n");
  return -1;
}

int
unstuff_orsci (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
  unsigned char *cp;
  PktChannel *channel;
  Srcname srcparts;
  double samprate=1.0/300;

  clrPkt(pkt);
  freetbl(pkt->channels,freePktChannel);
  pkt->channels=newtbl(0);

  pkt->version=ntohs(*(short int*)packet);
  if (pkt->version!=100 && pkt->version!=101)
    {
      complain(0,"unstuff_orsci, version mismatch, expected 100 or 101, got %d\n",pkt->version);
      return(-1);
    }
  if (pkt->version==101)
    samprate=1.0/ntohs(*((short int*)(packet+2)));

  pkt->pkttype=suffix2pkttype("MGENC");

  pkt->time=ipkttime;
  pkt->nchannels=0;

  cp=(unsigned char*)packet+2;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[8]/16)*10+cp[8]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[9]/16*10+cp[9]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHhiin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[14]/16*10+cp[13]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHloin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[20]/16*10+cp[20]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[21]/16*10+cp[21]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHhiout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[26]/16*10+cp[25]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHloout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;
  
  cp=(unsigned char*)packet+37;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[2]&0x07)*100+(cp[1]/16)*10+cp[1]%16;
  if ((cp[2]>>3)&0x01)
    *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tmpin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* dont bother 
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[3]>>4)&0x07*100+cp[3]%16*10+cp[2]/16;
  if ((cp[3]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1; 
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tmphin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;*/  

  /* dont bother
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[8]>>4)&0x07*100+cp[8]%16*10+cp[7]/16;
  if ((cp[8]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tmplin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++; */

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[17]&0x07)*100+(cp[16]/16)*10+cp[16]%16;
  if ((cp[17]>>3)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tmpout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  /* dont bother
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[18]>>4)&0x07*100+cp[18]%16*10+cp[17]/16;
  if ((cp[18]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tmpho");
  strcpy(channel->loc,""); 
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++; */

  /* dont bother
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[23]>>4)&0x07*100+cp[23]%16*10+cp[22]/16;
  if ((cp[23]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tmplo");
  strcpy(channel->loc,""); 
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++; */ 

  cp=(unsigned char*)packet+71;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[2]/16*1000+cp[2]%16*100+cp[1]/16*10+cp[1]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"pres");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[5]%16*10000+cp[4]/16*1000+cp[4]%16*100+cp[3]/16*10+cp[3]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"pressea");
  strcpy(channel->loc,""); /* sea level */
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[6]>>4)&0x07; /* 1 = rising 2 = steady 4 = falling */
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"prestre"); 
  strcpy(channel->loc,""); /* trend */
  strcpy(channel->segtype,"m");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[7]/16*10+cp[7]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[8]/16*10+cp[8]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewhin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[13]%16*10+cp[12]/16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewlin");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[18]/16*10+cp[18]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[19]/16*10+cp[19]%16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewhout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[24]%16*10+cp[23]/16;
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewlout");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  cp=(unsigned char*)packet+102;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[6]/16)*1000+(cp[6]%16)*100+(cp[5]/16)*10+(cp[5]%16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.001;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"rain");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"d");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
  
  cp=(unsigned char*)packet+116;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[2]%16)*100+(cp[1]/16)*10+(cp[1]%16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windgust");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"s");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
  
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[3]/16)*100+(cp[3]%16)*10+(cp[2]/16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dgust");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"a");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
   
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[5]%16)*100+(cp[4]/16)*10+(cp[4]%16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windavg");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"s");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[6]/16)*100+(cp[6]%16)*10+(cp[5]/16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"davg");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"a");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[8]%16)*100+(cp[7]/16)*10+(cp[7]%16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windhigh");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"s");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[9]/16)*100+(cp[9]%16)*10+(cp[8]/16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dhigh");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"a");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[16]/16)*10+(cp[16]%16);
  channel->time=ipkttime;
  channel->samprate=samprate;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windchil");
  channel->loc[0]='\0';
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
   
  return Pkt_wf;
}

void showPkt_orsci( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
	printf( "can't showpkt(not implemented) packet %d from %s\n", pktid, srcname );

	printf( "\n" );
}
