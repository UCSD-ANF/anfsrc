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


int stuff_ORACLEpf (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
  fprintf(stderr, "can't stuffpkt_ORACLEpf(not implemented) packet %d from %s\n", srcname );
  complain(0, "can't stuff ORACLEpf packet,sorry\n");
  return -1;
}

int unstuff_ORACLEpf (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
  PktChannel *channel;
  Srcname srcparts;
  double samrate;
  double timestamp;
  Pf *pf=NULL;
  Arr *channels;
  Arr *chan_pf_arr;
  Tbl *chan_pf_keys;
  Tbl *chan_split_tbl;
  char *buf;
  int lcv;
  float val;

  clrPkt(pkt);
  freetbl(pkt->channels,freePktChannel);
  pkt->channels=newtbl(0);
  buf=malloc(nbytes+1);
  strncpy(buf,packet,nbytes);
  buf[nbytes]=0;

  if (pfcompile(buf,&pf))
    return -1;

  if (pfget_int(pf,"Version")!=100)
    {
      complain(0,"unstuff_ORACLEpf, version mismatch, expected 100, got %d\n",pfget_int(pf,"Version"));
      free(buf);
      return(-1);
    }

  samrate=pfget_double(pf,"SampleRate");
  timestamp=pfget_double(pf,"Timestamp");

  chan_pf_arr=pfget_arr(pf,"Channels");
  chan_pf_keys=keysarr(chan_pf_arr);

  pkt->nchannels=0;
  pkt->pkttype=suffix2pkttype("MGENC");

  pkt->time=timestamp;

  split_srcname(srcname,&srcparts);

  strcpy(pkt->parts.src_net,srcparts.src_net);
  strcpy(pkt->parts.src_sta,srcparts.src_sta);
  *(pkt->parts.src_chan)='\0';
  *(pkt->parts.src_loc)='\0';
  strcpy(pkt->parts.src_suffix,"MGENC");
  *(pkt->parts.src_subcode)='\0';

  if (maxtbl(chan_pf_keys)<1)
    {
      printf("the ORACLEpf packet did not contain any data.\npf=\"%s\"\n",buf);
      free(buf);
      freearr(chan_pf_arr,NULL);
      freetbl(chan_pf_keys,NULL);
      return -1;
    }
  for (lcv=0;lcv<maxtbl(chan_pf_keys);lcv++)
    {
      channel=newPktChannel();
      channel->data=malloc(sizeof(int));
      channel->time=pkt->time;
      channel->samprate=samrate;
      channel->calper=-1;
      channel->nsamp=1;
      channel->datasz=1;
      strncpy(channel->net,srcparts.src_net,PKT_TYPESIZE);
      strncpy(channel->sta,srcparts.src_sta,PKT_TYPESIZE);
      strncpy(channel->chan,gettbl(chan_pf_keys,lcv),PKT_TYPESIZE);
      *(channel->loc)='\0';

      chan_split_tbl=split(getarr(chan_pf_arr,channel->chan),' ');
      if (maxtbl(chan_split_tbl)!=4)
	{
	  printf("ORACLEpf: internal packet format error. Expected parameter file entry of format: chan_name\tsegtype\tcalib\tmultiplier\tval\n for channel %s but there are %d elements in pkt: \"%s\"\n",channel->chan,maxtbl(chan_split_tbl)+1,buf);
	  free(buf);
	  freePktChannel(channel);
	  freearr(chan_pf_arr,NULL);
	  freetbl(chan_pf_keys,NULL);
	  return -1;
	}
      
      sscanf(gettbl(chan_split_tbl,3),"%f",&val);
      *(channel->data)=val*atof(gettbl(chan_split_tbl,1));
      strncpy(channel->segtype,gettbl(chan_split_tbl,0),1);
      channel->calib=atof(gettbl(chan_split_tbl,2));
      
      pushtbl(pkt->channels,channel);
      pkt->nchannels++;

      freetbl(chan_split_tbl,NULL);
    }

  free(buf);
  freearr(chan_pf_arr,NULL);
  freetbl(chan_pf_keys,NULL);
  return Pkt_wf;
}

void showPkt_ORACLEpf( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
  write(0,"ORACLEpf packet:\n",17);
  write(0,pkt,strlen(pkt));
  write(0,"\n",1);
}
