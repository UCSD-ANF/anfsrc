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
#include <pthread.h>

#define WAITTIMEOUT 2
char *SRCNAME="CSRC_IGPP_TEST";

#define VERSION "$Revision: 1.19 $"

z_stream compstream;
int verbose;

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

    Written By: Todd Hansen 3/4/2003
    Updated By: Todd Hansen 10/4/2004

    1.7 was the first revision to include zlib compression
 */

int orbinfd;
FILE *fil;
int fd;

void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios);
 /* call to reset serial port when we are done */

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed);
 /* initalize the serial port for our use */

int processpacket(unsigned char *buf,int size, int orbfd, int compressOn);
int checksum(unsigned char *buf, int size);
int find_speed(char *val);
void* cmdthread(void* args);

 void usage(void)
 {            
   cbanner(VERSION,"[-v] [-j] [-V] [-g] [-c] [-p serialport] [-d serialspeed] [-s net_sta_cha_loc] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
 }            

 int main (int argc, char *argv[])
 {
   struct termios orig_termios;
   int orbfd;
   char buf[250], fifo[50], *tbuf;
   char jumbo[500000];
   int jumbo_cnt=0;
   int jumbo_str=0;
   int jumbomode=0;
   int lcv, pktsize, val;
   fd_set readfds, exceptfds;
   struct timeval timeout;
   int ch, ret, pktid, nbytes=0, bufsize=0;
   char srcname[50];
   double pkttime;
   char *pkt=NULL;
   char *port="/dev/ttyS3";
   char *ORBname=":";
   int serial_speed = B115200;
   int selectret=0;
   int compressOn=0;
   int glob=0;
   int lcv2;
   struct timeval tw;
   struct timeval tw2;
   double twdiff;
   pthread_t cmdthr;
   int cmdpid;

   elog_init(argc,argv);

   while ((ch = getopt(argc, argv, "vjcgVp:o:s:d:")) != -1)
     switch (ch) {
     case 'V': 
       usage();
       exit(-1);
     case 'v': 
       verbose=1;
       break;  
     case 'g': 
       glob=1;
       break;  
     case 'c': 
       compressOn=1;
       break;  
     case 'j': 
       jumbomode=1;
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

   elog_notify(0,"mben2orb started. %s\n",VERSION);
   if (jumbomode && glob)
   {
       elog_complain(0,"you can't specify both jumbo (-j) and glob (-g) modes\n");
       usage();
       exit(-1);
   }
   if (jumbomode)
       elog_notify(0,"jumbo mode (MBEN Specific grouping algorithm)\n");
   if (glob)
       elog_notify(0,"glob mode (time-dependent grouping algorithm)\n");
   if (compressOn)
     elog_notify(0,"compressing data with: zlib %s\n",zlibVersion());

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

   /*if ((orbinfd=orbopen(ORBname,"r&"))<0)
     {
       perror("orbopen failed (orbinfd)");
       return(-1);
     }

   sprintf(fifo,"%s/EXP/MBEN_CMD",SRCNAME);
   if (orbselect(orbinfd,fifo)<0)
     {
       perror("orbselect");
     }

   if ((cmdpid=fork())<0)
   {
       perror("fork failed!\n");
       exit(-1);
   }

   if (cmdpid==0)
   {
       cmdthread(NULL);
       exit(0);
       }*/

   /*elog_notify(0,"bef spawned cmdthread\n");
   pthread_create(&cmdthr,NULL,cmdthread,NULL);
   pthread_create(&cmdthr,NULL,cmdthread,NULL);
   elog_notify(0,"spawned cmdthread\n");*/

   lcv=0;
   while (1) 
     {      
	 if (glob)
	 {
	     if (gettimeofday(&tw,NULL))
	     {
		 elog_complain(1,"gettimeofday(&tw,NULL)");
		 exit(-1);
	     }
	     twdiff=0;
	     
	     while (twdiff < 0.5 && jumbo_cnt<4000)
	     {
		 memset(buf,1,250);

		 if (fgets(buf,250,fil)==NULL)
		 {
		     if (errno != EAGAIN)
		     {
			 elog_complain(1,"fgets(fil,buf,250) failed");
			 exit(-1);
		     }

		     if (verbose)
			 elog_notify(0,"fgets exited, waiting for serial data\n");
		 }
		 else
		 {
		     ret=250;
		     while (ret>0 && buf[ret]!='\0')
			 ret--;

		     memcpy(jumbo+jumbo_cnt,buf,ret);

		     if (ret==4096)
			 elog_notify(0,"possible lost data (rec'd 4096 bytes, uart max)\n");
		    
		     if (ret>0)
			 jumbo_cnt+=ret;
		     else
			 elog_complain(0,"fgets returned but without data and without error\n");
		 }

		 if (gettimeofday(&tw2,NULL))
		 {
		     elog_complain(1,"gettimeofday(&tw2,NULL)");
		     exit(-1);
		 }
		 twdiff=tw2.tv_sec+tw2.tv_usec/1000000.0;
		 twdiff-=tw.tv_sec+tw.tv_usec/1000000.0;
	     }
     	 }
	 else
	 {
	     memset(buf+lcv,1,250-lcv);
	     
	     if (fgets(buf+lcv,250-lcv,fil)==NULL)
	     {
		 if (verbose)
		     elog_notify(0,"fgets() exited, waiting for serial data feof=%d ferror=%d\n",feof(fil),ferror(fil));

		 if (read(fd,buf+lcv,1)<0 && errno!=EAGAIN)
		 {
		     perror("read()");
		     elog_complain(1,"fgets(fil,buf,250) failed ferror=%d",ferror(fil));
		     exit(-1);
		 }
	     }
	     else
	     {
		 ret=250;
		 while (ret>0 && buf[ret]!='\0')
		     ret--;
		 
		 if (ret>0)
		     lcv+=ret;
	     }
	 }

	 if (glob)
	 {
	     processpacket((unsigned char*)jumbo,jumbo_cnt, orbfd, compressOn);
	     jumbo_cnt=0;
	     jumbo_str=0;
	 }
	 else
	 {
	     if (!jumbomode)
		 processpacket((unsigned char*)buf,lcv, orbfd, compressOn);
	     else 
	     {
		 bcopy(buf,jumbo+jumbo_cnt,lcv);
		 jumbo_cnt+=lcv;
		 jumbo_str++;
			 
		 if (strncmp(buf,"$PASHR,PBN,",11) == 0 || jumbo_cnt>40000)
/*		 if (strncmp(buf,"$PASHR,PBN,",11) == 0 || (selectret==0 && lcv>0) || jumbo_cnt>40000)*/
		 {
		     if (verbose)
		     {
			 if (selectret)
			     elog_notify(0,"accumulated enough strings (%d), sending packet (size %d)\n",jumbo_str,jumbo_cnt);
			 else
			     elog_notify(0,"select timeout, sending strings (%d), packet size %d\n",jumbo_str,jumbo_cnt);
			 
		     }
			     
		     processpacket((unsigned char*)jumbo,jumbo_cnt,orbfd,compressOn);
		     jumbo_cnt=0;
		     jumbo_str=0;
		 }

		 lcv=0;
	     }
	 }
     }

   destroy_serial_programmer(fil,fd,&orig_termios);
   orbclose(orbfd);
   return(0);
 }

 FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed)
 {
   FILE *fil;
   struct termios tmp_termios;

   *fd=open(file_name,O_RDONLY);
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

   fil=fdopen(*fd,"r");

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

 int processpacket(unsigned char *buf, int size, int orbfd, int compressOn)
 {
   unsigned char lbuf[60010];
   char srcname[48];
   int ret;

   /*if (strncmp(buf,"$PASHR,PBN,",11)==0||strncmp(buf,"$PASHR,SNV,",11)==0||strncmp(buf,"$PASHR,MPC,",11)==0||strncmp(buf,"$PASHR,MCA,",11)==0)
     if (checksum(buf,size))
     return (-1);*/

   sprintf(srcname,"%s/EXP/MBEN",SRCNAME);
      
   if (compressOn)
   {
     compstream.next_in=Z_NULL;
     compstream.next_out=Z_NULL;
     compstream.msg=Z_NULL;
     compstream.zalloc=Z_NULL;
     compstream.zfree=Z_NULL;
     compstream.opaque=Z_NULL;
     ret=deflateInit(&compstream,Z_BEST_COMPRESSION);
     
     if (ret!=Z_OK)
       {
	 elog_complain(0,"zlib deflateInit() failed %d\n",ret);
	 
	 if (ret==Z_MEM_ERROR)
	   elog_complain(0,"deflateInit: Memory Allocation error\n");
	 
	 if (ret==Z_VERSION_ERROR)
	   elog_complain(0,"deflateInit: libz Version mismatch Error (compile=%s, runtime=%s\n",ZLIB_VERSION,zlibVersion());
	 
	 if (ret==Z_STREAM_ERROR)
	   elog_complain(0,"deflateInit: Invalid compression level\n");
	 
	 if (compstream.msg!=NULL)
	   elog_complain(0,"deflauteInit: error message=\"%s\"",compstream.msg);
	 exit(-1);
       }
     
     /*
       gencompress demo for kent
       compstream.avail_out=60000;
       compstream.avail_in=size;
       ret=gencompress(&lbuf,&compstream.avail_out,&compstream.avail_in,(int*)buf,size/4+1,0);
       elog_notify(0,"gencompress in=%d out=%d ret=%d\n",size,compstream.avail_in,ret);
     */

       *(short*)lbuf=htons(101);
       compstream.next_in=buf;
       compstream.avail_in=size;
       compstream.total_in=0;
       compstream.total_out=0;
       compstream.next_out=lbuf+2;
       compstream.avail_out=60000;
       ret=deflate(&compstream,Z_FINISH);

       if (ret==Z_STREAM_END)
       {
	   if (compstream.avail_out==0 || compstream.total_out>size)
	   {
	       if (compstream.avail_out==0)
		   elog_complain(0,"zlib compression output exceeded 60k bytes with input of %d bytes (msg=%s), sending uncompressed version\n",size,compstream.msg);
	       else
		   elog_complain(0,"zlib compression inefficent, sending uncompressed. (in bytes=%d, out bytes=%d)",size,compstream.total_out);

	       *(short*)lbuf=htons(100);
	       bcopy(buf,lbuf+2,size);
	       orbput(orbfd,srcname,now(),(char*)lbuf,size+2);
	   }
	   else
	   {
	       if (verbose)
	       {
		   elog_notify(0,"zlib compressed %d bytes to %d bytes (message=%s) (%.1f%%)\n",size,compstream.total_out,compstream.msg,(size-compstream.total_out)*100.0/size);
	       }
	       orbput(orbfd,srcname,now(),(char*)lbuf,compstream.total_out+2);
	   }

	   deflateEnd(&compstream);
       }
       else
       {
	   elog_complain(0,"deflate failed. msg=\"%s\" ret=%d\n",compstream.msg,ret);
	   exit(-1);
       }
  }
  else
  {
      *(short*)lbuf=htons(100);
      bcopy(buf,lbuf+2,size);
      orbput(orbfd,srcname,now(),(char*)lbuf,size+2);
  }
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

void* cmdthread(void* args)
{
    int ret;
    int pktid;
    char srcname[300];
    double pkttime;
    char *pkt=NULL;
    int nbytes=0;
    int bufsize=0;

    elog_notify(0,"inside cmdthread\n");

    while (1)
    {
	ret=orbreap(orbinfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize);
	if (ret==-1)
	{
	    perror("orbreap failed");
	    exit(-1);
	}
	
	elog_notify(0,"%s command recieved through orb\n");
	if (ntohs(*((short*)pkt))!=100)
	{
	    elog_complain(0,"command packet version mismatch!");
	    exit(-1);
	}
	
	if (fwrite(pkt+2,nbytes-2,1,fil)!=(nbytes-2))
	{
	    elog_complain(1,"write short");
	    exit(-1);
	}

	/* 
	   if (write(fd,pkt+2,nbytes-2)!=(nbytes-2))
	   {
	   elog_complain(1,"write short");
	   exit(-1);
	   }
	*/
    }
}
