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
#include <Pkt.h>
#include <zlib.h>
#include <errno.h>

#define VERSION "$Revision: 1.1 $"
int verbose=0;

char *SRCNAME="CSRC_IGPP_TEST";

 /*
  Copyright (c) 2004 The Regents of the University of California
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

    Written By: Todd Hansen 8/19/2004
    Updated By: Todd Hansen 8/19/2004

 */
int orbinfd;
FILE *fil;
int fd;

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed);
int find_speed(char *val);
void* cmdthread(void* args);

void usage(void)
{            
    cbanner(VERSION,"[-v] [-V] [-p serialport] [-d serialspeed] [-s net_sta_cha_loc] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}            

int main (int argc, char *argv[])
{
    struct termios orig_termios;   
    char *port="/dev/ttyS3";
    char *ORBname=":";
    int serial_speed = B115200;
    int ch;
    char fifo[50];
    int ret;
    int pktid;
    char srcname[300];
    double pkttime;
    char *pkt=NULL;
    int nbytes=0;
    int bufsize=0;

    elog_init(argc,argv);
    
    while ((ch = getopt(argc, argv, "vVp:o:s:d:")) != -1)
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
	    case 'd': 
		serial_speed=find_speed(optarg);
		break;  
	    default:  
		fprintf(stderr,"Unknown Argument.\n\n");
		usage();
		exit(-1);
	}         
    
    elog_notify(0,"mben2orb_cmd started. %s\n",VERSION);

    fil=init_serial(port, &orig_termios, &fd, serial_speed);
    
    if (fil==NULL)
    {
	perror("serial port open");
	exit(-1);
    }

    if ((orbinfd=orbopen(ORBname,"r&"))<0)
    {
	perror("orbopen failed (orbinfd)");
	return(-1);
    }
    
    orbseek(orbinfd,ORBNEWEST);
    sprintf(fifo,"%s/EXP/MBEN_CMD",SRCNAME);
    if (orbselect(orbinfd,fifo)<0)
    {
	perror("orbselect");
    }
    elog_notify(0,"selecting on: \"%s/EXP/MBEN_CMD\"",SRCNAME);    

    while (1)
    {
	elog_notify(0,"waiting for reap\n");
	ret=orbreap(orbinfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize);
	if (ret==-1)
	{
	    perror("orbreap failed");
	    exit(-1);
	}
	
	elog_notify(0,"command received through orb\n");
	if (ntohs(*((short*)pkt))!=100)
	{
	    elog_complain(0,"command packet version mismatch!");
	    exit(-1);
	}
	
        /*
	if (fwrite(pkt+2,nbytes-2,1,fil)!=(nbytes-2))
	{
	elog_complain(1,"write short");
	exit(-1);
	}
	*/

	
	if (write(fd,pkt+2,nbytes-2)!=(nbytes-2))
	{
	    elog_complain(1,"write cmd to ashtech (via serial)");
	    exit(-1);
	}
    }
}

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed)
{
    FILE *fil;
    struct termios tmp_termios;
    
    *fd=open(file_name,O_WRONLY);
    if (*fd<0)
     {
	 elog_complain(1,"open serial port");
	 return(NULL);
     }
    
    if (tcgetattr(*fd,&tmp_termios)<0)
     {
	 elog_complain(1,"get serial attributes");
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
       elog_complain(1,"set serial attributes");
       return(NULL);
   }
   
   fil=fdopen(*fd,"w");
   
   if (fil==NULL)
   {
       elog_complain(1,"opening serial port");
       return(NULL);
   }
   
   if (setvbuf(fil,NULL,_IOLBF,0)!=0)
   {
       elog_complain(1,"setting ANSI buffering.");
       return(NULL);
   }

   return(fil);
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

  elog_complain(0,"speed %d is not supported see: /usr/include/sys/termios.h for supported values. Using default: 115.2kbps\n",l);
  return B115200;
}
