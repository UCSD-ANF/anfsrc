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

#define NETNAME "HM"
#define WAITTIMEOUT 20
#define PKTSIZE 32
#define STX 0x02
#define DLE 0x10
#define DEFAULTSAMPRATE 0.0011111111
#define STATSAMPRATE 0.0002777777

#define VERSION "$Revision: 1.1 $"

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
   Updated By: Todd Hansen 6//2003
*/


void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios);
/* call to reset serial port when we are done */

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd);
/* initalize the serial port for our use */

int processpacket(unsigned char *buf,int size, int orbfd);
void sendack(int fd);
void sendnack(int fd);
void start2orb(int orbfd, unsigned char *buf);
void data2orb(int orbfd, unsigned char *buf);
void pressure(struct Packet *orbpkt, char *staid, unsigned char *buf);
void nwind0(struct Packet *orbpkt, char *staid, unsigned char *buf);
void ewind0(struct Packet *orbpkt, char *staid, unsigned char *buf);
void windgust0(struct Packet *orbpkt, char *staid, unsigned char *buf);
void dgust0(struct Packet *orbpkt, char *staid, unsigned char *buf);
void nwind1(struct Packet *orbpkt, char *staid, unsigned char *buf);
void ewind1(struct Packet *orbpkt, char *staid, unsigned char *buf);
void windgust1(struct Packet *orbpkt, char *staid, unsigned char *buf);
void dgust1(struct Packet *orbpkt, char *staid, unsigned char *buf);
void temp0(struct Packet *orbpkt, char *staid, unsigned char *buf);
void temp1(struct Packet *orbpkt, char *staid, unsigned char *buf);
void humidity(struct Packet *orbpkt, char *staid, unsigned char *buf);
void rain(struct Packet *orbpkt, char *staid, unsigned char *buf);
void solar(struct Packet *orbpkt, char *staid, unsigned char *buf);
void voltage(struct Packet *orbpkt, char *staid, unsigned char *buf);
void numframes(struct Packet *orbpkt, char *staid, unsigned char *buf);

unsigned char goodframenum=0;
double starttime=0;
double DATASAMPRATE=DEFAULTSAMPRATE;
int verbose=0;

void usage(void)
{
  cbanner(VERSION,"cayan2orb [-v] [-V] [-p serialport] [-s datasamplerate] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char *argv[])
{
  struct termios orig_termios;
  int fd, orbfd;
  FILE *fil;
  unsigned char buf[32];
  int lcv, ret;
  char *port="/dev/ttySA1", *ORBname=":";
  signed char ch;
  fd_set readfds, exceptfds;
  struct timeval timeout;

  while ((ch = getopt(argc, argv, "vVp:o:s:")) != -1)
   switch (ch) {
   case 'V':
     usage();
     exit(-1);
   case 'v':
     verbose=1;
     break;
   case 'p':
     port=optarg;
     break;
   case 'o':
     ORBname=optarg;
     break;
   case 's':
     DATASAMPRATE=atof(optarg);
     break;
   default:
     fprintf(stderr,"Unknown Argument.\n\n");
     usage();
     exit(-1);
   }

  fil=init_serial(port, &orig_termios, &fd);

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

	  if (ret!=1)
	    {
	      perror("read");
	      return(-1);
	    }
	  else if (lcv==0 && buf[0]!=DLE)
	    {
	      lcv=0; /* discard input not matching start character */
	    }
	  else if (lcv==1 && (buf[1]!=DLE && buf[1]!=STX))
	    {
		lcv=0; buf[0]=0;
	    }  
	  else
	    lcv++;

	  if (lcv==PKTSIZE)
	    {
	      if (processpacket(buf,lcv, orbfd) == 0)
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

int processpacket(unsigned char *buf, int size, int orbfd)
{
  if (FletcherDecode(buf,size)!=0)
    {
      return(-1);
    }

  if (buf[1]==STX)
    {
      if (verbose) 
	fprintf(stderr,"data packet! local time = %d\n",(int)time(NULL));

      goodframenum=buf[5];
      data2orb(orbfd, buf);

    }
  else if (buf[1]==DLE)
    {
      if (verbose)
	fprintf(stderr,"start packet! local time = %d\n",(int)time(NULL));
      start2orb(orbfd, buf);
    }
  else
    {
      fprintf(stderr,"unknown packet type (0x%X).\n",buf[0]);
      return(-1);
    }

  return(0);
}

void start2orb(int orbfd, unsigned char *buf)
{
  struct Packet *orbpkt;
  char srcname_full[116];
  double newtimestamp;
  static char *newpkt = NULL;
  int newpkt_size;
  static int newpkt_alloc_size=0;
  char epochstr[100];
  
  orbpkt =  newPkt() ;
  orbpkt->pkttype = suffix2pkttype("MGENC");

  sprintf(epochstr,"%x%02x/%x/%x %x:%x:%x",buf[8],buf[9],buf[10],buf[11],buf[12],buf[13],buf[14]);
  orbpkt->time=str2epoch(epochstr);
  if (verbose)
    fprintf(stderr,"pkttime=%f (%s)\n",orbpkt->time,epochstr);

  sprintf(epochstr,"%x%02x/%x/%x 0:0:0",buf[8],buf[9],buf[10],buf[11]);
  starttime=str2epoch(epochstr);

  orbpkt->nchannels=2;
  strncpy(orbpkt->parts.src_net,NETNAME,2);
  sprintf(epochstr,"%0x%x",buf[5],buf[6]);
  strncpy(orbpkt->parts.src_sta,epochstr,5);
  *(orbpkt->parts.src_chan)=0;
  *(orbpkt->parts.src_loc)=0;
  strncpy(orbpkt->parts.src_subcode,"stat",4);
  
  numframes(orbpkt, epochstr, buf);
  voltage(orbpkt, epochstr, buf);

  if (verbose)
    fprintf(stderr,"transfering stat pkt\n");

  if (stuffPkt(orbpkt, srcname_full, &newtimestamp, &newpkt, &newpkt_size, &newpkt_alloc_size)<0)
    {
      fprintf(stderr,"stuff failed\n");
      complain ( 0, "stuffPkt routine failed for pkt\n") ;
   }
  else if (orbput(orbfd, srcname_full, newtimestamp, newpkt, newpkt_size) < 0)
    {
      fprintf(stderr,"put failed\n");
      complain ( 0, "orbput fails %s\n",srcname_full );
    }  
  
  if (verbose)
    {
      fprintf(stderr,"put %s\n",srcname_full);
      showPkt(0,srcname_full,newtimestamp,newpkt,newpkt_size,stdout,PKT_UNSTUFF);
    }
}

void data2orb(int orbfd, unsigned char *buf)
{
  struct Packet *orbpkt;
  char srcname_full[116];
  double newtimestamp, pkttime;
  static char *newpkt = NULL;
  int newpkt_size;
  static int newpkt_alloc_size=0;
  char epochstr[100];

  sprintf(epochstr,"%x",buf[6]);
  pkttime=starttime+(atoi(epochstr)*60);
  sprintf(epochstr,"%x",buf[5]);
  pkttime+=atoi(epochstr)*60*60;
  if (verbose)
    fprintf(stderr,"pkttime=%f\n",pkttime);

  sprintf(epochstr,"%x%x",buf[2],buf[3]);
  if (!queue_test(epochstr,buf[4],pkttime))
    {
      if (verbose)
	fprintf(stderr,"duplicate packet, skipping\n");
      return;
    }

  orbpkt =  newPkt() ;
  orbpkt->pkttype = suffix2pkttype("MGENC");
  orbpkt->time=pkttime;
  orbpkt->nchannels=14;
  strncpy(orbpkt->parts.src_net,NETNAME,2);
  sprintf(epochstr,"%0x%x",buf[2],buf[3]);
  strncpy(orbpkt->parts.src_sta,epochstr,5);
  *(orbpkt->parts.src_chan)=0;
  *(orbpkt->parts.src_loc)=0;
  
  pressure(orbpkt, epochstr, buf);
  nwind0(orbpkt, epochstr, buf);
  ewind0(orbpkt, epochstr, buf);
  windgust0(orbpkt, epochstr, buf);
  dgust0(orbpkt, epochstr, buf);
  nwind1(orbpkt, epochstr, buf);
  ewind1(orbpkt, epochstr, buf);
  windgust1(orbpkt, epochstr, buf);
  dgust1(orbpkt, epochstr, buf);
  temp0(orbpkt, epochstr, buf);
  temp1(orbpkt, epochstr, buf);
  humidity(orbpkt, epochstr, buf);
  rain(orbpkt, epochstr, buf);
  solar(orbpkt, epochstr, buf);

  if (verbose)
    fprintf(stderr,"transfering pkt\n");

  if (stuffPkt(orbpkt, srcname_full, &newtimestamp, &newpkt, &newpkt_size, &newpkt_alloc_size)<0)
    {
      fprintf(stderr,"stuff failed\n");
      complain ( 0, "stuffPkt routine failed for pkt\n") ;
   }
  else if (orbput(orbfd, srcname_full, newtimestamp, newpkt, newpkt_size) < 0)
    {
      fprintf(stderr,"put failed\n");
      complain ( 0, "orbput fails %s\n",srcname_full );
    }  
  
  if (verbose)
    {
      fprintf(stderr,"put %s\n",srcname_full);
      showPkt(0,srcname_full,newtimestamp,newpkt,newpkt_size,stdout,PKT_UNSTUFF);
    }
}

void pressure(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* barometric pressure */
  if (verbose)
    fprintf(stderr,"adding channel pressure\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[7]*256+buf[8];
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"Pre",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"P",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end barometric pressure */
}

void nwind0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* north wind */
  if (verbose)
    fprintf(stderr,"adding channel north wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[9]*16+(buf[10]%16); 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"NWD0",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end north wind */
}

void ewind0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* east wind */
  if (verbose)
    fprintf(stderr,"adding channel east wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[10]/16)*256+buf[11]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"EWD0",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end east wind */
}

void windgust0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* wind gust */
  if (verbose)
    fprintf(stderr,"adding channel wind gust\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[12]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"GST0",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end wind gust */
}

void dgust0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* wind gust dir */
  if (verbose)
    fprintf(stderr,"adding channel wind gust dir\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[13]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"dgt0",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"a",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end wind gust dir */
}

void nwind1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* north wind */
  if (verbose)
    fprintf(stderr,"adding channel north wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[14]*16+(buf[15]%16); 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"NWD1",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end north wind */
}

void ewind1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* east wind */
  if (verbose)
    fprintf(stderr,"adding channel east wind\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[15]/16)*256+buf[16]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"EWD1",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end east wind */
}

void windgust1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* wind gust */
  if (verbose)
    fprintf(stderr,"adding channel wind gust\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[17]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"GST1",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"s",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end wind gust */
}

void dgust1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* wind gust dir */
  if (verbose)
    fprintf(stderr,"adding channel wind gust dir\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[18]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"dgt1",4);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"a",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end wind gust dir */
}

void temp0(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* temp 0 */
  if (verbose)
    fprintf(stderr,"adding channel temp 0\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[19]*16+buf[20]/16; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"T0",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"t",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end temp 0 */
}

void temp1(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* temp 1 */
  if (verbose)
    fprintf(stderr,"adding channel temp 1\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=(buf[20]/16)*256+buf[21]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"T1",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"t",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end temp 1 */
}

void humidity(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* humidity */
  if (verbose)
    fprintf(stderr,"adding channel humidity\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[22]*256+buf[23]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"RH",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"p",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end humidity */
}

void rain(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* rain */
  if (verbose)
    fprintf(stderr,"adding channel rain\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[24]*256+buf[25]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"RN",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"d",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end rain */
}

void solar(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* solar radiation  */
  if (verbose)
    fprintf(stderr,"adding channel solar radiation\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[26]*256+buf[27]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"SOL",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"W",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=DATASAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end solar radiation */
}

void voltage(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* voltage */
  if (verbose)
    fprintf(stderr,"adding channel battery voltage\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[15]*256+buf[16]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"BAT",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"v",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=STATSAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end voltage */
}

void numframes(struct Packet *orbpkt, char *staid, unsigned char *buf)
{
  struct PktChannel *pktchan;
  
  /* num frames */
  if (verbose)
    fprintf(stderr,"adding channel num frames\n");
  pktchan = newPktChannel();
  pktchan -> datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      perror("malloc");
      exit(-1);
    }
  
  pktchan->data[0]=buf[7]; 
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,NETNAME,2);
  strncpy(pktchan->sta,staid,5);
  strncpy(pktchan->chan,"num",3);
  *(pktchan->loc)='\0';
  strncpy(pktchan->segtype,"c",4);
  pktchan->nsamp=1;
  pktchan->calib=0;
  pktchan->calper=-1;
  pktchan->samprate=STATSAMPRATE;
  pushtbl(orbpkt->channels,pktchan);
  /* end num frames */
}

void sendack(int fd)
{
  char ack;
  ack=0x2;
  write(fd,&ack,1);
  write(fd,&goodframenum,1);
}

void sendnack(int fd)
{
  char nack;
  nack=0x1;
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
