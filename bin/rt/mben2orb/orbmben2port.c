#include <unistd.h>
#include <signal.h>
#include <orb.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

#define VERSION "$Revision: 1.2 $"

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

   Written By: Todd Hansen 3/4/2003
   Updated By: Todd Hansen 8/5/2003
*/

#define SRCNAME "CSRC_PFO_PIN1"

int main (void)
{
  int orbfd, fd;
  char fifo[60], *pkt=NULL;
  char srcname[60];
  double pkttime;
  int pktid;
  int nbytes, bufsize=0;
  int ret;

  orbfd=orbopen("/export/rt/pin1_lockup_040312/pin1.t@f","r&");
  if (orbfd<0)
    {
      perror("orbopen");
      exit(-1);
    }
  
  sprintf(fifo,"/tmp/buf_lu.%s",SRCNAME);
/*  if (mkfifo(fifo,0644))
    {
      perror("mkfifo");
      exit(-1);
      }*/
  
  fprintf(stderr,"mben data accessible through: %s\n",fifo);
  fd=open(fifo,O_WRONLY|O_CREAT);
  if (fd<0)
    {
      perror("open fifo");
      exit(-1);
    }

  sprintf(fifo,"%s.*",SRCNAME);
  if (orbselect(orbfd,fifo)!=0)
    {
      perror("orbselect");
    }

  if (orbseek(orbfd,ORBOLDEST)<0)
    {
      perror("orbseek");
    }

  while(1)
    {
	if ((ret=orbreap(orbfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize))==-1)
	{
	    complain(1,"orbreap");
	    perror("orbreap");
	}

	if (ret==ORB_INCOMPLETE)
	{
	    fprintf(stderr,"done?\n");
	    exit(0);
	}
	
      if (ntohs(*(short int*)pkt)!=100)
	{
	  fprintf(stderr,"version mismatch, expected 100, got %d\n",ntohs(*(short int*)pkt));
	}
      else
	{
	  write(fd,pkt+2,nbytes-2);
	}
    }

  orbclose(orbfd);
  close(fd);
}
