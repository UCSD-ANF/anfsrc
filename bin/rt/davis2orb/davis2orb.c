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
#include <errno.h>
#include "CCITT.h"

char *SRCNAME="LG_IGPP";
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

   Written By: Todd Hansen 2/26/2004
   Updated By: Todd Hansen 2/27/2004
*/


void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios);
/* call to reset serial port when we are done */

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed);
/* initalize the serial port for our use */

unsigned short checksum(unsigned char *buf, int size);
int find_speed(char *val);
void flushOut(int *fd);
      
void usage(void)
{            
  cbanner(VERSION,"[-v] [-V] [-r repeat] [-p serialport] [-d serialspeed] [-s net_sta] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}            
       
int main (int argc, char *argv[])
{
  struct termios orig_termios;
  int fd, orbfd;
  FILE *fil;
  char buf[250];
  int lcv, val, verbose=0;
  int repeat=300;
  int ch, ret, redo;
  char srcname[50];
  double t;
  char *port="/dev/ttyS3";
  char *ORBname=":";
  int serial_speed = B19200;

  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVp:o:s:d:r:")) != -1)
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
    case 'r': 
      repeat=atoi(optarg);
      break;  
    case 's': 
      SRCNAME=optarg;
      break;  
    case 'd': 
      serial_speed=find_speed(optarg);
      break;  
    default:  
      fprintf(stderr,"Unknown Argument.\n\n");
      usage();
      exit(-1);
    }         


  fil=init_serial(port, &orig_termios, &fd, serial_speed);

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

  t=now();
  while (1) 
    {      
      flushOut(&fd);
      
      *buf='\0';
      lcv=0;
      if (verbose)
	fprintf(stderr,"getting attention...");
      do
	{
	  if (lcv == 3)
	    {
	      complain(0,"Failed to wake up the Davis on port %s after 3 attempts, exiting!\n",port);
	    }

	  if (write(fd,"\n",1)<1)
	    {
	      perror("write(wakeup)");
	      exit(-1);
	    }

	  sleep(1);

	  val=fcntl(fd,F_GETFL,0);
	  val|=O_NONBLOCK;
	  fcntl(fd,F_SETFL,val);
	  
	  if (read(fd,buf,1)<0 && errno!=EAGAIN)
	    {
	      perror("read reply");
	      exit(-1);
	    }

	  val&=~O_NONBLOCK;
	  fcntl(fd,F_SETFL,val);
	  lcv++;
	}
      while (*buf != '\n');

      if (verbose)
	fprintf(stderr,"got attention\n");
      
      if (write(fd,"LOOP 1\n",7)<1)
	{
	  perror("write(LOOP 1)");
	  exit(-1);
	}
      
      /* wait for ack */
      *buf='\0';
      lcv=0;
      sleep(1);
      while(*buf!=0x6)
	{
	  if (lcv>100)
	    {
	      complain(0,"Command ack not recieved after 100 tries, exiting\n");
	      exit(-1);
	    }

	  if (read(fd,buf,1)<0 && errno!=EAGAIN)
	    {
	      perror("read command ack");
	      exit(-1);
	    }
	  lcv++;
	}

      ch=0;
      if (verbose)
	fprintf(stderr,"reading data\n");
      while(ch<99)
	{
	  if ((ret=read(fd,buf+6+ch,99-ch))<0  && errno!=EAGAIN)
	    {
	      perror("read response");
	      exit(-1);
	    }
	  
	  if (ret>0)
	    ch+=ret;
	  
	  fprintf(stderr,"got %d chars (99 needed) so far\n",ch);
	}
      if (verbose)
	fprintf(stderr,"got a data packet, parsing\n");
      
      if ((ret=checksum((unsigned char*)buf+6,99))!=0 && redo<25)
	{
	  complain(0,"checksum failed for data, retrying\n");
	  redo++;
	}
      else
	{
	  if (redo==25 && ret!=0)
	    complain(0,"checksum failed 25 times, going to sleep for next sample period\n");
	    
	  redo=0;

	  if (ret==0)
	    {
	      *((short int*)buf)=htons(0x100); /* set version */
	      *((long int*)(buf+2))=htonl(repeat); /* set repeat */	      
	      sprintf(srcname,"%s/EXP/DAVIS",SRCNAME);
	      orbput(orbfd,srcname,now(),buf,105);
	    }

	  if (verbose)
	    fprintf(stderr,"sleeping %d sec, %f %f\n",(repeat-(((int)(now()-t))%repeat)),now(),t);

	  if (repeat-(((int)(now()-t))%repeat)>0)
	    sleep(repeat-(((int)(now()-t))%repeat));
	  else
	    {
	      complain(0,"falling behind, I should sleep %d sec, %f %f\n",(int)(repeat-(now()-t)),now(),t);
	    }
	}
    }

  destroy_serial_programmer(fil,fd,&orig_termios);
  orbclose(orbfd);
  return(0);
}

void flushOut(int *fd)
{
  char c;
  int val;

  val=fcntl(*fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  sleep(3);

  while(read(*fd,&c,1)!=-1)
    {
      /* fprintf(stderr,"%c\n",c); */
    }

  val&=~O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);
}


FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed)
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

  cfsetispeed(&tmp_termios,serial_speed);
  cfsetospeed(&tmp_termios,serial_speed);
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

unsigned short checksum(unsigned char *buf, int size)
{
  unsigned short crc;
  int lcv;

  crc=0;
  for (lcv=0;lcv<size;lcv++)
    {
      /* if (lcv!=95 && lcv != 96)*/
	crc=crc_table[(crc>>8) ^ buf[lcv]] ^ (crc << 8);
    }

  return crc;
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

int find_speed(char *val)
{
  int l;

  l=atoi(val);
  if (l==50)
    return B50;
  if (l==75)
    return B75;
  if (l==110)
    return B110;
  if (l==134)
    return B134;
  if (l==150)
    return B150;
  if (l==200)
    return B200;
  if (l==300)
    return B300;
  if (l==600)
    return B600;
  if (l==1200)
    return B1200;
  if (l==1800)
    return B1800;
  if (l==2400)
    return B2400;
  if (l==4800)
    return B4800;
  if (l==9600)
    return B9600;
  if (l==19200)
    return B19200;
  if (l==38400)
    return B38400;
  if (l==57600)
    return B57600;
  if (l==115200)
    return B115200;
  if (l==230400)
    return B230400;
  if (l==460800)
    return B460800;

  fprintf(stderr,"speed %d is not supported see: /usr/include/sys/termios.h for supported values. Using default: 19.2kbps\n",l);
  return B19200;
}
