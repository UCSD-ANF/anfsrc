#include <unistd.h>
#include <stdio.h>
#include <strings.h>
#include <ctype.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <termios.h>
#include <sys/time.h>
#include <fcntl.h>
#include <orb.h>
#include <coords.h>
#include <netdb.h>
#include <stdio.h>
#include <stock.h>
#include <Pkt.h>

#define WAITTIMEOUT 20
char *SRCNAME="CSRC_IGPP_TEST";

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


void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios);
/* call to reset serial port when we are done */

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd);
/* initalize the serial port for our use */

int processpacket(char *buf,int size, int orbfd);
int checksum(unsigned char *buf, int size);
             
void usage(void)
{            
  cbanner(VERSION,"[-V] [-p serialport] [-s net_sta_cha_loc] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}            
       
int main (int argc, char *argv[])
{
  struct termios orig_termios;
  int fd, orbfd, orbinfd, highfd;
  FILE *fil;
  char buf[250], fifo[50];
  int lcv, pktsize, verbose=0;
  fd_set readfds, exceptfds;
  struct timeval timeout;
  int ch, ret, pktid, nbytes=0, bufsize=0;
  char srcname[50];
  double pkttime;
  char *pkt=NULL;
  char *port="/dev/ttyS3";
  char *ORBname=":";

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
      SRCNAME=optarg;
      break;  
    default:  
      fprintf(stderr,"Unknown Argument.\n\n");
      usage();
      exit(-1);
    }         


  fil=init_serial(port, &orig_termios, &fd);

  if (fil==NULL)
   {
	perror("serial port open");
	exit(-1);
   }

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

  if ((orbinfd=orbopen(ORBname,"r&"))<0)
    {
      perror("orbopen failed (orbinfd)");
      return(-1);
    }

  sprintf(fifo,"%s/EXP/MBEN_CMD",SRCNAME);
  if (orbselect(orbinfd,fifo)<0)
    {
      perror("orbselect");
    }

  lcv=0;
  pktsize=12;
  while (1) 
    {      
      FD_ZERO(&readfds);
      FD_SET(fd,&readfds);
      FD_SET(orbinfd,&readfds);
      
      FD_ZERO(&exceptfds);
      FD_SET(fd,&exceptfds);
      FD_SET(orbinfd,&readfds);

      timeout.tv_sec=WAITTIMEOUT;
      timeout.tv_usec=0;

      if (fd>orbinfd)
	  highfd=fd+1;
      else
	highfd=orbinfd+1;

      if (select(highfd,&readfds,NULL,&exceptfds,&timeout)<0)
	{
	  perror("select");
	  return(-1);
	}
      
	if (FD_ISSET(fd, &readfds) || FD_ISSET(fd, &exceptfds))
	{
	  ret=read(fd,buf+lcv,1);
	  
	  if (ret!=1)
	    {
	      perror("read");
	      return(-1);
	    }
	  /*else if (lcv==0 && buf[0]!='$')
	    {
	    lcv=0; *//* discard input not matching start character *//*
	    }
	else*/
	    lcv++;

	    /* if (lcv==11)
	    {
	      if (strncmp(buf,"$PASHR,MCA,",11)==0)
		{
		  pktsize=50;
		}
	      else if (strncmp(buf,"$PASHR,MPC,",11) == 0)
		{
		  pktsize=108;
		}
	      else if (strncmp(buf,"$PASHR,PBN,",11) == 0)
		{
		  pktsize=69;
		}
	      else if (strncmp(buf,"$PASHR,SNV,",11) == 0)
		{
		  pktsize=145;
		}
	      else
		{
		  buf[11]='\0';
		  pktsize=248;
		}
		}*/

	  if (lcv==pktsize || buf[lcv-1]=='\n')
	    {
	      if (processpacket(buf,lcv, orbfd) != 0)
		{
		  if (lcv>11)
		    buf[11]='\0';		     
		  else
		    buf[lcv]='\0';
		  fprintf(stderr,"invalid checksum! (%s)\n",buf);
		}

	      lcv=0;
	      pktsize=248;
	    }
	  
	  if (FD_ISSET(fd, &exceptfds))
	    {
	      fprintf(stderr,"serial exception! recovered?\n");
	    }
	}
	
	ret=orbreap_nd(orbinfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize);
	if (ret==-1)
	  {
	    perror("orbreap_nd failed");
	    exit(-1);
	  }
	
	if (ret != ORB_INCOMPLETE)
	  {
	    fprintf(stderr,"%s command recieved through orb\n",strtime(now()));
	    if (ntohs(*((short*)pkt))!=100)
	      {
		fprintf(stderr,"command packet version mismatch!");
		exit(-1);
	      }
	    
	    if (write(fd,pkt+2,nbytes-2)!=(nbytes-2))
	      {
		perror("write short");
		exit(-1);
	      }
	  }
    }

  destroy_serial_programmer(fil,fd,&orig_termios);
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

  cfsetispeed(&tmp_termios,B115200);
  cfsetospeed(&tmp_termios,B115200);
  tmp_termios.c_lflag &= ~(ECHO|ICANON|IEXTEN|ISIG);
  tmp_termios.c_iflag &= ~(BRKINT|ICRNL|INPCK|ISTRIP|IXON);
  tmp_termios.c_cflag &= ~(CSIZE|PARENB);
  tmp_termios.c_cflag |= CS8;
  tmp_termios.c_oflag &= ~OPOST;

  tmp_termios.c_cc[VMIN]=1;
  tmp_termios.c_cc[VTIME]=0;
  if (tcsetattr(*fd,TCSANOW,&tmp_termios)<0)
    {
      perror("set serial attributes");
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

int processpacket(char *buf, int size, int orbfd)
{
  char lbuf[252];
  char srcname[48];

  /*if (strncmp(buf,"$PASHR,PBN,",11)==0||strncmp(buf,"$PASHR,SNV,",11)==0||strncmp(buf,"$PASHR,MPC,",11)==0||strncmp(buf,"$PASHR,MCA,",11)==0)
    if (checksum(buf,size))
    return (-1);*/

  *(short*)lbuf=htons(100);
  bcopy(buf,lbuf+2,size);
  sprintf(srcname,"%s/EXP/MBEN",SRCNAME);
  orbput(orbfd,srcname,now(),lbuf,size+2);
  return(0);
}

int checksum(unsigned char *buf, int size)
{
  unsigned char sum;
  unsigned short sum2;
  int lcv;

  if (strncmp((char*)buf,"$PASHR,PBN,",11)==0 || strncmp((char*)buf,"$PASHR,SNV,",11)==0)
    {
      sum2=0;
      for (lcv=11;lcv<size-4;lcv+=2)
	{
	  sum2+=buf[lcv]*256+buf[lcv+1];
	}

      if (buf[size-4]*256+buf[size-3]==sum2)
	return 0;
      else
	{ 
	  fprintf(stderr,"checksum=0x%x, calculated=0x%x\n",buf[size-4]*256+buf[size-3],sum2);
	  return -1;
	}
    }
  else
    {
      sum=0;
      for (lcv=11;lcv<size-3;lcv++)
	{
	  sum^=buf[lcv];
	}
      
      if (buf[size-3]==sum)
	return 0;
      else
	{
	  fprintf(stderr,"checksum=0x%x, calculated=0x%x\n",buf[size-3],sum);
	  return -1;
	}
    }
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
