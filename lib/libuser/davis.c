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

/*
 * ALERT: This code is not neccesary for the most recent davis2orb system.
 * davis2orb 1.x is the only version requiring this unstuff code, newer versions use
 * the MGENC format.
 *
 *    -Todd
 */

int
stuff_davis (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
  fprintf(stderr, "can't stuffpkt_davis(not implemented) packe from %s\n", srcname );
  complain(0, "can't stuff davis packet,sorry\n");
  return -1;
}

int
unstuff_davis (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
  unsigned char c;
  PktChannel *channel;
  Srcname srcparts;
  Tbl *splits;
  int repeat;
  double samrate;
  char *i;

  clrPkt(pkt);
  freetbl(pkt->channels,freePktChannel);
  pkt->channels=newtbl(0);

  pkt->version=ntohs(*((short int*)(packet+4)));

  if (pkt->version!=100)
  {
      complain(0,"unstuff_davis, version mismatch, expected 100, got %d\n",pkt->version);
      return(-1);
  }

  if (nbytes != 105)
  {
      complain(0,"unstuff_davis, packet size mismatch, expected 105, got %d\n",nbytes);
      return(-1);      
  }

  repeat=ntohl(*(long int*)(packet));
  samrate=1.0/repeat;

  pkt->nchannels=0;
  pkt->pkttype=suffix2pkttype("MGENC");

  if (strncmp("LOO",packet+6,3))
    {
      complain(0,"unstuff_davis, header mismatch, expected LOO, got %c%c%c\n",packet[7],packet[8],packet[9]);
      return(-1);
    }

  i = packet+6;
  pkt->time=ipkttime;

  split_srcname(srcname,&srcparts);

  strcpy(pkt->parts.src_net,srcparts.src_net);
  strcpy(pkt->parts.src_sta,srcparts.src_sta);
  *(pkt->parts.src_chan)='\0';
  *(pkt->parts.src_loc)='\0';
  strcpy(pkt->parts.src_suffix,"MGENC");
  *(pkt->parts.src_subcode)='\0';

  
  if (i[3] != 'P')
  {
      /* bar trend */
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=*((signed char*)i+3);
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=1;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"Bar-trend");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"c");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
  }
  
  /* pkt type */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[4];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"pktver");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"c");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;
      
  /* barometer */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[8]*256+(unsigned char)i[7];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=0.001/0.02953;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"Bar");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"P");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* inside temp */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[10]*256+(unsigned char)i[9]-320;
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=0.1*5.0/9.0;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"Temp-in");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"t");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* inside hum */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[11];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"Hum-in");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"p");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* outside temp */
  if (i[13]*256+(unsigned char)i[12]!=32767)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=i[13]*256+(unsigned char)i[12]-320;
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=0.1*5.0/9.0;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"Temp-out");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"t");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* wind speed */
  if ((unsigned char)i[14]!=255)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[14];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=0.447;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"wind");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"s");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* 10min avg wind speed */
  if ((unsigned char)i[15]!=255)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[15];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=0.447;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"wind-avg10");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"s");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* wind dir */
  if ((unsigned char)i[17]*256+(unsigned char)i[16]!=32767)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[17]*256+(unsigned char)i[16];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=1;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"wdir");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"a");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* ignoring extra temps, as I don't know the format bytes 18 - 24 */

  /* ignoring soil temps, as I don't have an instrument to test with  bytes 25-28 */

  /* ignoring leaf temps, as I don't have an instrument to test with  bytes 29-32 */
  

  /* outside hum */
  if ((unsigned char)i[33]!=255)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[33];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=1;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"Hum-out");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"p");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* ignoring extra hum, as I don't have an instrument to test with  bytes 34-40 */

  /* rain rate */
  if (((unsigned char)i[42]*256+(unsigned char)i[41])!=65535)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[42]*256+(unsigned char)i[41];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=0.01;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"RainRate");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"c");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* UV */
  if ((unsigned char)i[43]!=255)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[43];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=0.1;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"UV");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"B");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* Solar Radiation */
  if ((unsigned char)i[45]*256+(unsigned char)i[44]!=32767)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      *(channel->data)=(unsigned char)i[45]*256+(unsigned char)i[44];
      channel->time=ipkttime;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->calib=1;
      channel->nsamp=1;
      channel->datasz=1;
      split_srcname(srcname,&srcparts);
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strcpy(channel->chan,"solar");
      strcpy(channel->loc,"");
      strcpy(channel->segtype,"W");
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;
    }

  /* Storm Rain */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[47]*256+(unsigned char)i[46];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=0.01;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"rain-storm");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"r");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* Storm Start */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[49]*256+(unsigned char)i[48];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"stormdate");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"r");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* Rain Day */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[51]*256+(unsigned char)i[50];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=0.01;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"rainday");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"r");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* Rain Month */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[53]*256+(unsigned char)i[52];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=0.01;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"rainmon");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"r");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* Rain Year */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[55]*256+(unsigned char)i[54];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=0.01;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"rainyr");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"r");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;
 
  /* not sure what Day ET and Month ET and Year ET are, 56,58,60 */

  /* not sure how to read soil mostures and leaf wetness or alarms 62-82 */

  /* Transmitter Bat Status */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[86];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"tranbat");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"c");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++; 

  /* Console Battery Voltage */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=(unsigned char)i[87];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=(300/512.0)/100.0;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"batt");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"v");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++; 

  /* not sure what forecast icons and forecast rule number mean */

  /* time of sunrise time of sunset depends on time setting in davis, which we don't check */

  return Pkt_wf;
}

void showPkt_davis( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
    complain(0,"can't show davis paket\n");
}
