#include <unistd.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <termios.h>
#include <sys/time.h>
#include <fcntl.h>
#include "FletcherEncode.h"
#include "queue.h"
#include <orb.h>
#include <coords.h>
#include <netdb.h>
#include <stdio.h>
#include <stock.h>
#include <Pkt.h>
#include <sys/utsname.h>
#include "proto0.h"
#include "proto1.h"
#include "proto2.h"
#include "cayan2orb.h"

#define VERSION "$Revision: 1.18 $"

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

   Written By: Todd Hansen 1/3/2003
   Updated By: Todd Hansen 2/17/2004

   The data loggers this code communicates with were created by Douglas
   Alden, using a protocol he specified.
*/


void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios);
/* call to reset serial port when we are done */

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd);
/* initalize the serial port for our use */

int processpacket(unsigned char *buf,int size, int orbfd, int pktver, int *vercnt);
void sendack(int fd);
void sendnack(int fd);

unsigned char goodframenum=0;
double starttime=0;
double DATASAMPRATE=1;
double STATSAMPRATE=1;
char *NETNAME="HM";
int dumbass=0;
int verbose=0;

void usage(void)
{
  cbanner(VERSION,"cayan2orb [-v] [-V] [-d] [-p serialport] [-n netname] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char *argv[])
{
  struct termios orig_termios;
  int fd, orbfd;
  FILE *fil;
  unsigned char buf[MAX_PKTSIZE+2];
  unsigned char serbuf[50];
  char *serpt, *serpt2;
  int sercnt=0;
  char sersrcname[75];
  struct utsname uns;
  
  int lcv, ret;
  char *port="/dev/ttySA1", *ORBname=":";
  signed char ch;
   int pktver, vercnt=0;
  fd_set readfds, exceptfds;
  struct timeval timeout;

  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVdp:o:n:")) != -1)
   switch (ch) {
   case 'V':
     usage();
     exit(-1);
   case 'v':
     verbose=1;
     break;
   case 'd':
     dumbass=1;
     break;
   case 'p':
     port=optarg;
     break;
   case 'o':
     ORBname=optarg;
     break;
   case 'n':
     NETNAME=optarg;
     break;
   default:
     fprintf(stderr,"Unknown Argument.\n\n");
     usage();
     exit(-1);
   }

  fil=init_serial(port, &orig_termios, &fd);

  serpt=port;
  serpt2=port;
  while(*serpt!='\0')
    {
      serpt++;
      if (*serpt=='/')
	{
	  serpt2=serpt+1;
	}
    }

  if (fil==NULL)
    exit(-1);

  /* 
  write(fd,"A",1);
  read(fd,buf,1);
  write(fd,buf,1);
  */ 

  if ((orbfd=orbopen(ORBname,"w&"))<0)
    {
      perror("orbopen failed");
      return(-1);
    }

  lcv=0;
  while (1) 
    {      
      FD_ZERO(&readfds);
      FD_SET(fd,&readfds);
      
      FD_ZERO(&exceptfds);
      FD_SET(fd,&exceptfds);
      
      timeout.tv_sec=WAITTIMEOUT;
      timeout.tv_usec=0;

      if (select(fd+1,&readfds,NULL,&exceptfds,&timeout)<0)
	{
	  perror("select");
	  return(-1);
	}
      
	if (FD_ISSET(fd, &readfds) || FD_ISSET(fd, &exceptfds))
	{
	  ret=read(fd,buf+lcv,1);

	  if (verbose)
	    fprintf(stderr,"got char 0x%x %d\n",*(buf+lcv),lcv);

	  if (dumbass)
	    {
	      serbuf[sercnt]=*(buf+lcv);
	      sercnt++;

	      if (sercnt==50)
		{
		  uname(&uns);
		  sprintf(sersrcname,"%s_%s_%s/EXP/metbarf",NETNAME,uns.nodename,serpt2);
		  orbput(orbfd,sersrcname,time(NULL),(char*)serbuf,50);
		  sercnt=0;
		}
			 
	    }

	  if (ret!=1)
	    {
	      perror("read");
	      return(-1);
	    }
	  else if (lcv==0 && buf[0]!=DLE)
	    lcv=0; /* discard input not matching start character */
	  else if (lcv==1 && buf[1]==STX && vercnt==0)
	    {
	      lcv=0; /* discard possible data headers if we are searching
			for a start header*/
	      buf[0]=0;
	      if (verbose)
		fprintf(stderr,"discarding, possible data header, when waiting for start header.\n");
	    }
	  else if (lcv==1 && (buf[1]!=DLE && buf[1]!=STX))
	    {
		lcv=0; 
		buf[0]=0;
	    } 
	  else 
	    lcv++;

	  if (lcv == 19 && buf[1]==DLE)
	    {
	      pktver=buf[17];
	      vercnt=1; /*pktver only valid for this packet until ok checksum*/
	      switch (buf[18]) {
	      case 0x0:
		DATASAMPRATE=0.0011111111;
		STATSAMPRATE=0.0002777777;
		break;
	      case 0x1:
		DATASAMPRATE=0.016666667;
		STATSAMPRATE=0.016666667;
		break;
	      default:
		fprintf(stderr,"Unknown sample rate id encountered: 0x%x. Ignoring\n",buf[18]);
	      }
	      if (verbose)
		{
		  fprintf(stderr,"data sample rate set to: %f\n",DATASAMPRATE);
		}
	    }

	  if ((vercnt>0) && ((pktver == 0 && lcv == 32) || (pktver == 1 && lcv == 41) || (pktver == 2 && lcv == 41) || lcv > 41))
	    {
	      if (processpacket(buf,lcv, orbfd, pktver, &vercnt) == 0)
		{
		  /* set goodframenum */
		  if (verbose)
		    fprintf(stderr,"valid checksum!\n");
		  sendack(fd);
		}
	      else
		{
		  fprintf(stderr,"invalid checksum!\n");
		  sendnack(fd);
		}
	      lcv=0;
	    }
	  else if (lcv >= MAX_PKTSIZE)
	    lcv=0;
	  
	  if (FD_ISSET(fd, &exceptfds))
	    {
	      fprintf(stderr,"serial exception! recovered?\n");
	    }
	}
    }

  destroy_serial_programmer(fil,fd,&orig_termios);
  queue_clean();
  orbclose(orbfd);
  return(0);
}

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd)
{
  FILE *fil;
  struct termios tmp_termios;

  *fd=open(file_name,O_RDWR);
  if (*fd<0)
    {
      perror("open serial port");
      return(NULL);
    }

  if (tcgetattr(*fd,&tmp_termios)<0)
    {
      perror("get serial attributes");
      return(NULL);
    }
  
  *orig_termios=tmp_termios;

  cfsetispeed(&tmp_termios,B19200);
  cfsetospeed(&tmp_termios,B19200);
  tmp_termios.c_lflag &= ~(ECHO|ICANON|IEXTEN|ISIG);
  tmp_termios.c_iflag &= ~(BRKINT|ICRNL|INPCK|ISTRIP|IXON);
  tmp_termios.c_cflag &= ~(CSIZE|PARENB);
  tmp_termios.c_cflag |= CS8;
  tmp_termios.c_oflag &= ~OPOST;

  tmp_termios.c_cc[VMIN]=1;
  tmp_termios.c_cc[VTIME]=0;
  if (tcsetattr(*fd,TCSANOW,&tmp_termios)<0)
    {
      perror("get serial attributes");
      return(NULL);
    }

  fil=fdopen(*fd,"r+");
  
  if (fil==NULL)
    {
      perror("opening serial port");
      return(NULL);
    }

  if (setvbuf(fil,NULL,_IONBF,0)!=0)
    {
      perror("setting ANSI buffering.");
      return(NULL);
    }

  return(fil);
}

int processpacket(unsigned char *buf, int size, int orbfd, int pktver, int *vercnt)
{
  *vercnt--;

  if (FletcherDecode(buf,size)!=0)
    {
      return(-1);
    }

  if (verbose)
    fprintf(stderr,"packet version: %d\n",pktver);

  if (buf[1]==STX)
    {
      if (verbose) 
	fprintf(stderr,"data packet! local time = %d\n",(int)time(NULL));

      goodframenum=buf[4];
      if (pktver == 0)
	p0_data2orb(orbfd, buf);
      else if (pktver == 1)
	p1_data2orb(orbfd,buf);
      else if (pktver == 2)
	p2_data2orb(orbfd,buf);
      else
	fprintf(stderr,"unknown pkt version %d!\n",pktver);

      if ((*vercnt == 0) && verbose)
	{
	  fprintf(stderr,"final data packet, waiting for new start packet!\n");
	}
    }
  else if (buf[1]==DLE)
    {
      if (verbose)
	fprintf(stderr,"start packet! ver=%d local time = %d\n",pktver,(int)time(NULL));
      *vercnt=buf[7];
      if (verbose)
	fprintf(stderr,"expecting %d data packets\n",*vercnt);

      if (pktver == 0)
	p0_start2orb(orbfd, buf);
      else if (pktver == 1)
	p1_start2orb(orbfd,buf);
      else if (pktver == 2)
	p2_start2orb(orbfd,buf);
      else
	fprintf(stderr,"unknown pkt version %d!\n",pktver);
    }
  else
    {
      fprintf(stderr,"unknown packet type (0x%X).\n",buf[0]);
      return(-1);
    }

  return(0);
}

void sendack(int fd)
{
  char ack;
  ack=0x6;
  write(fd,&ack,1);
  write(fd,&goodframenum,1);
}

void sendnack(int fd)
{
  char nack;
  nack=0x15;
  write(fd,&nack,1);
  write(fd,&goodframenum,1);
}

void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios)
{
  if (tcsetattr(fd,TCSANOW,orig_termios)<0)
    {
      perror("get serial attributes");
      exit(-1);
    }

  fclose(fil);
  close(fd);
}
