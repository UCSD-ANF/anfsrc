#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

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

  clrPkt(pkt);
  freetbl(pkt->channels,freePktChannel);
  pkt->channels=newtbl(0);

  pkt->version=ntohs(*(short int*)packet);
  if (pkt->version!=100)
    {
      complain(0,"unstuff_orsci, version mismatch, expected 100, got %d\n",pkt->version);
      return(-1);
    }
  pkt->pkttype=suffix2pkttype("MGENC");

  pkt->time=ipkttime;
  pkt->nchannels=0;

  cp=(unsigned char*)packet+2;

  fprintf(stderr,"boo= %x",*(cp+2));
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[8]/16)*10+cp[8]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RH");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[9]/16*10+cp[9]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHhi");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[14]/16*10+cp[13]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHlo");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[20]/16*10+cp[20]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RH");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[21]/16*10+cp[21]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHhi");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[26]/16*10+cp[25]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->datasz=1;
  channel->nsamp=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"RHlo");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;
  
  cp=(unsigned char*)packet+37;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[2]&0x07*100+cp[1]/16*10+cp[1]%16;
  if ((cp[2]>>3)&0x01)
    *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"temp");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[3]>>4)&0x07*100+cp[3]%16*10+cp[2]/16;
  if ((cp[3]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1; 
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"temph");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[8]>>4)&0x07*100+cp[8]%16*10+cp[7]/16;
  if ((cp[8]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"templ");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[17]&0x07*100+cp[16]/16*10+cp[16]%16;
  if ((cp[17]>>3)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"temp");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[18]>>4)&0x07*100+cp[18]%16*10+cp[17]/16;
  if ((cp[18]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"temph");
  strcpy(channel->loc,"ou"); /* out */
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[23]>>4)&0x07*100+cp[23]%16*10+cp[22]/16;
  if ((cp[23]>>7)&0x01)
     *(channel->data)*=-1;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"templ");
  strcpy(channel->loc,"ou"); /* out */
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  cp=(unsigned char*)packet+71;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[2]/16*1000+cp[2]%16*100+cp[1]/16*10+cp[1]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"pres");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[5]%16*10000+cp[4]/16*1000+cp[4]%16*100+cp[3]/16*10+cp[3]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"pres");
  strcpy(channel->loc,"sea"); /* sea level */
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[6]>>4)&0x07; /* 1 = rising 2 = steady 4 = falling */
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"pres"); 
  strcpy(channel->loc,"tre"); /* trend */
  strcpy(channel->segtype,"m");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[7]/16*10+cp[7]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dew");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[8]/16*10+cp[8]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewhi");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[13]%16*10+cp[12]/16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewlo");
  strcpy(channel->loc,"in");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[18]/16*10+cp[18]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dew");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[19]/16*10+cp[19]%16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewh");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=cp[24]%16*10+cp[23]/16;
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dewl");
  strcpy(channel->loc,"out");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  cp=(unsigned char*)packet+102;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[6]/16)*1000+(cp[6]%16)*100+(cp[5]/16)*10+(cp[5]%16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.001;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"rain");
  strcpy(channel->segtype,"d");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
  
  cp=(unsigned char*)packet+116;

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[2]%16)*100+(cp[1]/16)*10+(cp[1]%16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windgust");
  strcpy(channel->segtype,"s");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
  
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[3]/16)*100+(cp[3]%16)*10+(cp[2]/16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dgust");
  strcpy(channel->segtype,"a");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  
   
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[5]%16)*100+(cp[4]/16)*10+(cp[4]%16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windavg");
  strcpy(channel->segtype,"s");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[6]/16)*100+(cp[6]%16)*10+(cp[5]/16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"davg");
  strcpy(channel->segtype,"a");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[8]%16)*100+(cp[7]/16)*10+(cp[7]%16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windhigh");
  strcpy(channel->segtype,"s");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[9]/16)*100+(cp[9]%16)*10+(cp[8]/16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"dhigh");
  strcpy(channel->segtype,"a");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;  

  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(cp[17]/16)*10+(cp[17]%16);
  channel->time=ipkttime;
  channel->samprate=0.0033333333;
  channel->calper=-1;
  channel->calib=0.1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"windchil");
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
