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
stuff_wicor (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
  fprintf(stderr, "can't stuffpkt_wicor(not implemented) packet %d from %s\n", srcname );
  complain(0, "can't stuff orsci packet,sorry\n");
  return -1;
}

int
unstuff_wicor (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
  unsigned char c;
  PktChannel *channel;
  Srcname srcparts;
  Tbl *splits;
  char *i, *i2;
  char epochstr[150];

  clrPkt(pkt);
  freetbl(pkt->channels,freePktChannel);
  pkt->channels=newtbl(0);

  if (ntohs(*(short int*)packet)!=100)
    {
      complain(0,"unstuff_wicor, version mismatch, expected 100, got %d\n",pkt->version);
      return(-1);
    }

  pkt->nchannels=0;
  pkt->pkttype=suffix2pkttype("MGENC");

  splits=split(packet+2,',');
  i=shifttbl(splits);
  if (strcmp("$WICOR",i))
    {
      complain(0,"unstuff_wicor, header mismatch, expected $WICOR, got %s\n",i);
      return(-1);
    }

  /* timestamp */
  i=shifttbl(splits);
  i2=shifttbl(splits);

  sprintf(epochstr,"%c%c/%c%c/20%c%c %c%c:%c%c:%c%c",*(i+2),*(i+3),*i,*(i+1),*(i+4),*(i+5),*i2,*(i2+1),*(i2+2),*(i2+3),*(i2+4),*(i2+5));
  pkt->time=str2epoch(epochstr);

  split_srcname(srcname,&srcparts);

  strcpy(pkt->parts.src_net,srcparts.src_net);
  strcpy(pkt->parts.src_sta,srcparts.src_sta);
  *(pkt->parts.src_chan)='\0';
  *(pkt->parts.src_loc)='\0';
  strcpy(pkt->parts.src_suffix,"MGENC");
  *(pkt->parts.src_subcode)='\0';

  while (i=shifttbl(splits))
    {
      i2=shifttbl(splits);

      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      channel->time=pkt->time;
      channel->samprate=0.06666666667;
      channel->calper=-1;
      channel->nsamp=1;
      channel->datasz=1;
      strcpy(channel->net,srcparts.src_net);
      strcpy(channel->sta,srcparts.src_sta);
      strncpy(channel->chan,i2,2);
      channel->loc[2]=='\0';
      *(channel->loc)='\0';
      
      c=1;

      if (!strcmp(channel->chan,"AT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"BP"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"P");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"BC"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"SW"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"W");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"LW"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"W");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"LD"))
	{
	  *(channel->data)=(atof(i)-273.15)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"LB"))
	{
	  *(channel->data)=(atof(i)-273.15)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"LT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"v");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"PR"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"d");
	  channel->calib=0.000001;
	}
      else if (!strcmp(channel->chan,"PT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"RH"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"p");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"RT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"DP"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"WS"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"s");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"WK"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TW"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"s");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TK"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"WD"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"a");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TI"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"a");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"ST"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TC"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"u");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"SA"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"SD"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"SV"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"s");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"OX"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"OG"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"o");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"OC"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"i");
	  channel->calib=0.000001;
	}
      else if (!strcmp(channel->chan,"OT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"OS"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"PH"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"h");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"FL"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TB"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"TR"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"p");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"BA"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"PA"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"FM"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"FI"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"VT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"v");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"MA"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"i");
	  channel->calib=0.000001;
	}
      else if (!strcmp(channel->chan,"WT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"AX"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"PS"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"XX"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"LA"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"LO"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"CR"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"a");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"SP"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
       else if (!strcmp(channel->chan,"SL"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"GY"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"a");
	  channel->calib=0.001;
	}
      else if (!strcmp(channel->chan,"GT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"GT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"TS"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"ZD"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"SY"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"BT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"d");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"SH"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"a");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"SM"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"SR"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"ZO"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"d");
	  channel->calib=0.001;
	}
    else if (!strcmp(channel->chan,"ZS"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"s");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"ZT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"VP"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"VR"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"VH"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"d");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"VY"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"VX"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"IP"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"d");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"IT"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"t");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"IS"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"IA"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"d");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"IV"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"s");
	  channel->calib=0.001/60;
	}
    else if (!strcmp(channel->chan,"IX"))
	{
	  *(channel->data)=atof(i)*1000;
	  strcpy(channel->segtype,"c");
	  channel->calib=0.001/60;
	}
    else
	{
	  freePktChannel(channel);
	  complain(0,"unknown channel designator (%s)\n",channel->chan);
	  c=0;
	}

      if (*(i2+2)=='7' || *(i2+2)=='9')
	{
	  freePktChannel(channel);
	  c=0;
	}


      if (c)
	{
	  pushtbl(pkt->channels,channel);
	  pkt->nchannels++;
	}
    }

  freetbl(splits,0);
  return Pkt_wf;
}

void showPkt_wicor( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
  write(0,"wicor packet:\n",14);
  write(0,pkt+2,nbytes-1);
  write(0,"\n",1);
}
