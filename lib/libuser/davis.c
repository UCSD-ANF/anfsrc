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
  *(channel->data)=i[7]*256+i[8];
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
  *(channel->data)=i[9]*256+i[10]-32;
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
  *(channel->data)=i[11];
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
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[12]*256+i[13]-32;
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

  /* wind speed */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[14];
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

  /* 10min avg wind speed */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[15];
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

  /* wind dir */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[16]*256+i[17];
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

  /* ignoring extra temps, as I don't know the format bytes 18 - 24 */

  /* ignoring soil temps, as I don't have an instrument to test with  bytes 25-28 */

  /* ignoring leaf temps, as I don't have an instrument to test with  bytes 29-32 */
  

  /* outside hum */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[33];
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

  /* ignoring extra hum, as I don't have an instrument to test with  bytes 34-40 */

  /* rain rate */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[41]*256+i[42];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
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

  /* UV */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[43];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
  channel->nsamp=1;
  channel->datasz=1;
  split_srcname(srcname,&srcparts);
  strcpy(channel->net,srcparts.src_net);
  strcpy(channel->sta,srcparts.src_sta);
  strcpy(channel->chan,"UV");
  strcpy(channel->loc,"");
  strcpy(channel->segtype,"c");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* Solar Radiation */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[44]*256+i[45];
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
  strcpy(channel->segtype,"c");
  pushtbl(pkt->channels,channel);
  pkt->nchannels++;

  /* Storm Rain */
  channel=newPktChannel();
  channel->data=malloc(sizeof(int));
  *(channel->data)=i[46]*256+i[47];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
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
  *(channel->data)=i[48]*256+i[49];
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
  *(channel->data)=i[50]*256+i[51];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
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
  *(channel->data)=i[52]*256+i[53];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
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
  *(channel->data)=i[54]*256+i[55];
  channel->time=ipkttime;
  channel->samprate=samrate;
  channel->calper=-1;
  channel->calib=1;
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
  *(channel->data)=i[86];
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
  *(channel->data)=i[86];
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
