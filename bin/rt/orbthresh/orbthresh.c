#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <orb.h>
#include "queue.h"

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

   This code is designed to handle two simultaneous download streams

   Written By: Todd Hansen 1/3/2003
   Last Updated By: Todd Hansen 4/1/2003
*/

#define VERSION "$Revision: 1.1 $"

int debug=0;
int pkt_match=0;
int curpktid=0;

#define ORBTIMEOUT 15

void handle_pkt(char *originhost, int orbin, int pktid, char *srcname, double pkttime, char *pkt, int pkt_size, int orbout);

void usage(void)
{
  cbanner(VERSION,"orbthresh [-V] [-p] [-m matchstr] [-S state/file] -f $ORBin -b $ORBin2 -o $ORBout","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char *argv[])
{
  int orb1, orb2, orbout;
  int pktid;
  char srcname[500], ch;
  char *outorbname=NULL;
  char *firstorbname=NULL;
  char *backuporbname=NULL;
  char *selectstr=NULL;
  char *statefile;
  double pkttime;
  char *pkt;
  int pkt_size;
  int buf_size=0;
  int highestfd;
  int time1, time2;
  int maxsize=80000;
  Relic relic;
  struct timeval timeout;
  fd_set readfds, exceptfds;

 while ((ch = getopt(argc, argv, "Vdpm:S:o:f:b:s:")) != -1)
   switch (ch) {
   case 'V':
     usage();
     exit(-1);
   case 'd':
     debug=1;
     break;
   case 'p':
     pkt_match=1;
     break;
   case 'S':
     statefile=optarg;
     fprintf(stderr,"State files are currently ignored, sucker.\n");
     break;
   case 'o':
     outorbname=optarg;
     break;
   case 'f':
     firstorbname=optarg;
     break;
   case 'b':
     backuporbname=optarg;
     break;
   case 'm':
     selectstr=optarg;
     break;
   case 's':
     maxsize=atoi(optarg);
   default:
     fprintf(stderr,"Unknown Argument.\n\n");
     usage();
     exit(-1);
   }

 if (backuporbname == NULL || firstorbname == NULL || outorbname == NULL)
   {
     fprintf(stderr,"Required arguments missing.\n\n");
     usage();
     exit(-1);
   }


  qinit(maxsize);

  if ((orb1=orbopen(firstorbname,"r&"))<0)
    {
      perror("orbopen first/primary orb");
      exit(-1);
    }

  
  if ((orb2=orbopen(backuporbname,"r&"))<0) 
    {
      perror("orbopen backup orb");
      exit(-1);
    }

  if ((orbout=orbopen(outorbname,"w&"))<0)
    {
      perror("orbopen output orb");
      exit(-1);
    }

  if (selectstr)
    {
      orbselect(orb1,selectstr);
      orbselect(orb2,selectstr);
    }
  
  if (orbreap_nd(orb1,&pktid,srcname,&pkttime,&pkt,&pkt_size,&buf_size)!=ORB_INCOMPLETE)
    {
      handle_pkt(firstorbname,orb1,pktid,srcname,pkttime,pkt,pkt_size,orbout);
    }

  if (orbreap_nd(orb2,&pktid,srcname,&pkttime,&pkt,&pkt_size,&buf_size) != ORB_INCOMPLETE)
    {
      handle_pkt(backuporbname,orb2,pktid,srcname,pkttime,pkt,pkt_size,orbout);
    }
      
  if (orb1>orb2)
    highestfd=orb1+1;
  else
    highestfd=orb2+1;

  time1=time(NULL);
  time2=time(NULL);

  while (1)
    {
      FD_ZERO(&readfds);
      FD_SET(orb1,&readfds);
      FD_SET(orb2,&readfds);
 
      FD_ZERO(&exceptfds);
      FD_SET(orb1,&exceptfds);
      FD_SET(orb2,&exceptfds);
      
      timeout.tv_sec=ORBTIMEOUT;
      timeout.tv_usec=0;
      if (select(highestfd,&readfds,NULL,&exceptfds,&timeout)<0)
	{
	  perror("select");
	  exit(-1);
	}

      if (FD_ISSET(orb1, &readfds) || FD_ISSET(orb1, &exceptfds))
	{
	  if (orbreap_nd(orb1,&pktid,srcname,&pkttime,&pkt,&pkt_size,&buf_size)!=ORB_INCOMPLETE)
	    {
	      handle_pkt(firstorbname,orb1,pktid,srcname,pkttime,pkt,pkt_size,orbout);
	    }

	  if (FD_ISSET(orb1, &exceptfds))
	    {
	      fprintf(stderr,"orb1 exception! recovered?\n");
	    }
	  time1=time(NULL);
	}

      if (FD_ISSET(orb2, &readfds) || FD_ISSET(orb2, &exceptfds))
	{

	  if (orbreap_nd(orb2,&pktid,srcname,&pkttime,&pkt,&pkt_size,&buf_size)!=ORB_INCOMPLETE)
	    {
	      handle_pkt(backuporbname,orb2,pktid,srcname,pkttime,pkt,pkt_size,orbout);
	    }

	  if (FD_ISSET(orb2, &exceptfds))
	    {
	      fprintf(stderr,"orb2 exception! recovered?\n");
	    }
	  time2=time(NULL);
	}

      if ((time(NULL) - time1) > ORBTIMEOUT)
	{
	  if (orbreap_nd(orb1,&pktid,srcname,&pkttime,&pkt,&pkt_size,&buf_size)!=ORB_INCOMPLETE)
	    {
	      handle_pkt(firstorbname,orb1,pktid,srcname,pkttime,pkt,pkt_size,orbout);
	    }
	  if (debug)
	    printf("recovered orb1 via timeout\n");
	}

      if ((time(NULL) - time2) > ORBTIMEOUT)
	{
	  if (orbreap_nd(orb2,&pktid,srcname,&pkttime,&pkt,&pkt_size,&buf_size)!=ORB_INCOMPLETE)
	    {
	      handle_pkt(backuporbname,orb2,pktid,srcname,pkttime,pkt,pkt_size,orbout);
	    }

	  if (debug)
	    printf("recovered orb2 via timeout\n");
	}
       
    }

  orbclose(orbout);
  orbclose(orb1);
  orbclose(orb2);
  qfree();
}

void handle_pkt(char *originhost, int orbin, int pktid, char *srcname, double pkttime, char *pkt, int pkt_size, int orbout)
{
  int ret;

  if ((pkt_match && (pktid>curpktid || curpktid-pktid > 500000))|| (!pkt_match && verify_newpacket(srcname, pkttime, originhost)))
    {
      if (pkt_match && curpktid-pktid>500000)
	printf("Orb pktid looped on %s, last pktid: %d, new pktid %d\n",originhost,curpktid,pktid);

      curpktid=pktid;
      if ((ret=orbput(orbout,srcname,pkttime,pkt,pkt_size))<0)
	{
	  printf("%d %s %f 0x%p %d %d\n",orbout,srcname,pkttime,pkt,pkt_size,ret);
	  perror("orbput");
	  exit(-1);
	}

      if (debug)
	printf("pkt received from %s, %s %f %d\n",originhost,srcname,pkttime,pktid);
    }
  else
    {
      if (pkt_match && curpktid-curpktid>500)
	{
	  if ((pktid=orbseek(orbin,curpktid))!=curpktid)
	    {
	      printf("orbseek failed, requested pkt#%d, got pkt#%d\n",curpktid,pktid);
	    }
	}
      if (debug)
	printf("pkt repeated from %s, %s %f %d\n",originhost,srcname,pkttime,pktid);
    }
}
