#include <unistd.h>
#include <stdio.h>
#include <orb.h>
#include <Pkt.h>

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

   Written By: Todd Hansen 5/24/2004
   Updated By: Todd Hansen 10/19/2004

*/

#define min(a,b)  (a<b?a:b)

void usage(void)
{
  cbanner(VERSION,"[-v] [-V] [-m matchname] [-r rejectname] [-a destaddr] [-p destport] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char *argv[])
{
  char *matchname=NULL;
  char *rejectname=NULL;
  char *ORBname=":";
  char srcname[60];
  int ch;
  int pktid;
  int lcv, lcv2, lcv3;
  int sock_fd;
  double pkttime;
  char *pkt=NULL;
  char buf[5000];
  int nbytes;
  int bufsize=0;
  int orbfd;
  int verbose=0;
  int ret;
  unsigned char MTTL=255;
  struct Packet *Upkt=NULL;
  struct PktChannel *dp;
  char *maddr="233.7.117.79";
  int mport=4000;
  struct sockaddr_in cli_addr;
  struct sockaddr_in serv_addr;
  unsigned long lna;
  struct hostent *host_ent;
  struct sockaddr_in multi_addr;

  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVm:r:o:a:p:")) != -1)
   switch (ch) 
     {
     case 'V':
       usage();
       exit(-1);
     case 'v':
       verbose=1;
       break;
     case 'a':
       maddr=optarg;
       break;
     case 'p':
       mport=atoi(optarg);
       break;
     case 'o':
       ORBname=optarg;
       break;
     case 'm':
       matchname=optarg;
       break;
     case 'r':
	rejectname=optarg;
	break;
     default:
       fprintf(stderr,"Unknown Argument.\n\n");
       usage();
       exit(-1);
     }

  if (-1 != (lna=inet_addr(maddr)))
    memcpy(&multi_addr.sin_addr, &lna, 
	   min(sizeof(multi_addr.sin_addr), sizeof(lna)));
  else 
    {
      host_ent = gethostbyname(maddr);
      if (host_ent == NULL)
	{
	  elog_complain(0,"can't resolve %s!\n",maddr);
	  exit(-1);
	}

      memcpy(&multi_addr.sin_addr, host_ent->h_addr, 
             min(host_ent->h_length, sizeof(multi_addr.sin_addr)));
    }
       

  /*make socket*/
  sock_fd = socket(AF_INET, SOCK_DGRAM, 0);
  
  bzero((char *) &serv_addr, sizeof(serv_addr));
  serv_addr.sin_family      = AF_INET;
  serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  serv_addr.sin_port        = 0;
  
  if (bind(sock_fd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
    {
      perror("bind");
      exit(-1);
    }

  if (verbose)
    elog_notify(0,"setting Mcast TTL (%d)\n",MTTL);
  
  if (setsockopt(sock_fd, IPPROTO_IP, IP_MULTICAST_TTL,(char *)&MTTL, sizeof(MTTL)) < 0) 
    {
      perror("IP_MULTICAST_TTL");
      exit(1);
    }

  if ((orbfd=orbopen(ORBname,"r&"))<0)
    {
      perror("orbopen failed");
      return(-1);
    }
    
    if (matchname)
      if (orbselect(orbfd,matchname)<0)
	{
	  perror("orbselect");
	}
 
    if (rejectname)
      if (orbreject(orbfd,rejectname)<0)
      {
	perror("orbreject");
      }
	 
    while (1)
      {
	if (orbreap(orbfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize)<0)
	  {
	    perror("orbreap");
	    exit(-1);
	  }

	if ((ret=unstuffPkt(srcname,pkttime,pkt,nbytes,&Upkt)) != Pkt_wf)
	  {
	    fprintf(stderr,"unkown packet type, unstuff returned %d for %s\n",ret,srcname);
	  }
	else
	  {
	    if (verbose)
	      printf("got pkt, channels = %d & srcname = %s\n",Upkt->nchannels,srcname);

	    for (lcv=0;lcv<Upkt->nchannels;lcv++)
	      {
		dp=poptbl(Upkt->channels);

		if (dp->segtype[0]==0)
		  dp->segtype[0]='c';

		sprintf(buf,"%s:%s:%s:1:0\t%s\t%f\t%f\t%c\t%f\t%d\t%f\n",dp->net,dp->sta,dp->chan,dp->loc,dp->time+dp->samprate*(dp->nsamp),dp->calib,dp->segtype[0],dp->samprate,dp->data[dp->nsamp-1],dp->calib*dp->data[dp->nsamp-1]);

		cli_addr.sin_family      = AF_INET;
		cli_addr.sin_addr.s_addr = multi_addr.sin_addr.s_addr;
		cli_addr.sin_port        = htons(mport);
		lcv2=sizeof(cli_addr);
		if ((lcv3=sendto(sock_fd,buf,strlen(buf),0,(struct sockaddr*)&cli_addr,lcv2))<0)
		  {
		    perror("sendto");
		    return(-1);
		  }

		if (verbose)
		  elog_notify(0,"sent: %d bytes to %s:%p\n",lcv3,maddr,mport);
		
		freePktChannel(dp);
		dp=NULL;
	      }
	  }

	freePkt(Upkt);
	Upkt=NULL;
      }

}
