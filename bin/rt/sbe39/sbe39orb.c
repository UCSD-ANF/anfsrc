#include <unistd.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <time.h>
#include <signal.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <strings.h>
#include <termios.h>
#include <time.h>
#include <orb.h>
#include <coords.h>
#include <stock.h>
#include <Pkt.h>

#define min(a,b)  (a<b?a:b)

/*
 Copyright (c) 2004, 2006 The Regents of the University of California
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

   This code by: Todd Hansen 4/1/2004
   Last Updated By: Todd Hansen 1/18/2006
*/

#define VERSION "$Revision: 1.5 $"

#define PKTVERSION 100
#define CMDRESPONSE_DELAY 5

int verbose=0;
char *ipaddress=NULL;
char *port="4000";
char *orbname=":";
char *srcname="test_sta1";
char psrcname[501];
int orbfd;
int interval=0;

#define UNSUCCESSFUL -9999

int getAttention(int *fd);
void flushOut(int *fd);
int flushUntil(int *fd,char c);
void printProgram(int *fd);
int setMemPtr(int *fd, int location);
int readline_nb(int *fd, char *rebuf);
int initConnection(char *host, char *port);
int dataIntegrityCheck(char *completeResponse);
int stuffline(Tbl *r);
void getTime(int *fd);
int test_sbe39_pkt(char *packet);

void usage (void)
{
  cbanner(VERSION,"[-v] [-V] [-n portnumber] [-c net_sta] [-i interval] [-o $ORB] -a ipaddress ","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main(int argc,char *argv[])
{
  char rebuf[5005];
  signed char ch;
  int fd=0;
  int speed=B9600;
  FILE *fil;
  short swap;

  elog_init(argc,argv);

  while((ch=getopt(argc,argv,"Vva:n:i:c:o:"))!=-1)
    {
      switch(ch)
	{
	case 'V':
	  usage();
	  exit(-1);
	  break;	
	case 'v':
	  verbose=1;
	  break;
	case 'a':
	  ipaddress=optarg;
	  break;
	case 'n':
	  port=optarg;
	  break;
	case 'c':
	  srcname=optarg;
	  break;
        case 'i':
          interval=atoi(optarg);
          break;
	case 'o':
	  orbname=optarg;
	  break;
	default:
	  elog_complain(0,"Invalid argument\n");
	  usage();
	  exit(-1);
	}
    }
  
  sprintf(psrcname,"%s/EXP/SBE39",srcname);
  elog_notify(0,"sbe39orb %s output: %s\n",VERSION,psrcname);

  if (ipaddress==NULL)
    {
      elog_complain(0,"you must specify an IP address to connect to\n\n");
      usage();
      exit(-1);
    }

  if ((orbfd=orbopen(orbname,"w&"))<0)
    {
      perror("orbopen failed");
      return(-1);
    }
  
  fd=-1;
  while (1)
    {
      if (verbose)
	elog_notify(0,"connecting to remote station\n");
      
      fd=initConnection(ipaddress,port);
      
      if (fd>0)
	{
	  if (getAttention(&fd)==UNSUCCESSFUL)
	    {
	      close(fd);
	      fd=-1;
	    }
	}
      
      if (fd>=0)
	{
	  if (write(fd,"TS\r",3)<3)
	    {
	      elog_complain(1,"write(\"TS\\r\") failed");
	      close(fd);
	      fd=-1;
	    }
	  else
	    {
	      swap=htons(PKTVERSION); /* set version */
	      bcopy(&swap,rebuf,2);
	      swap=htons(interval); /* set sample interval */
	      bcopy(&swap,rebuf+2,2);
	      if (readline_nb(&fd,rebuf+4)>0)
		{
		    if (!test_sbe39_pkt(rebuf))
			orbput(orbfd,psrcname,now(),rebuf,strlen(rebuf+4)+5);
		}
	    }
	}
      
      close(fd);
      fd=-1;
      if (interval>0)
	sleep(interval);
      else
	{
	  orbclose(orbfd);
	  exit(0);
	}
    }
}

int getAttention(int *fd)
{
  int loop=0, val;
  int ret;
  char prompt[4];

  bzero(prompt,4);
  flushOut(fd);

  if (write(*fd,"\r\r\r",3)<3)
  {
      elog_complain(1,"write failed in getAttention()");
      close(*fd);
      *fd=-1;
      return(UNSUCCESSFUL);
  }

  val=fcntl(*fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  sleep(CMDRESPONSE_DELAY);
  while ((ret=read(*fd,prompt,1))>0 && prompt[0]!='>')
    /* nop */;

  if (ret<=0 && errno!=EAGAIN)
    {
      elog_complain(1,"getattention(read)");
      close(*fd);
      *fd=-1;
      return(UNSUCCESSFUL);
    }

  flushOut(fd);
  if (verbose)
    elog_notify(0,"got attention\n"); 

  val&=~O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  return 0;
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

int flushUntil(int *fd,char c)
{
  char prompt=0;
  int loop=0;

  while(loop++<3000)
    {
      prompt=0;
      if (read(*fd,&prompt,1)<1)
        {
	  elog_complain(1,"flushUntil(read())");
          close(*fd);
          *fd=-1;
          return UNSUCCESSFUL;
        }
      
      /* fprintf(stderr,"read %c\n",prompt); */

      if(prompt==c)
        return loop;
    }

  elog_complain(0,"flushUntil() = overflow in flushUntil (c=%c)\n",c);
  close(*fd);
  *fd=-1;
  return UNSUCCESSFUL;
}

int readline_nb(int *fd, char *rebuf)
{
  int loop=0;
  int ret=0;
  int val;

  sleep(CMDRESPONSE_DELAY);

  val=fcntl(*fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  while(loop++<5000)
    {
      if ((ret=read(*fd,&(rebuf[loop-1]),1))<1 && errno!=EAGAIN)
        {
          elog_complain(1,"readline(): read()");
          close(*fd);
          *fd=-1;
          return UNSUCCESSFUL;
        }
      else if ((ret==-1) && errno==EAGAIN)
      {
	  elog_complain(0,"readline(): read timed out (%d seconds) before receiving terminating character from SBE39 \'>\'.\nDisconnecting\n",CMDRESPONSE_DELAY);
	  close(*fd);
	  *fd=-1;
	  return UNSUCCESSFUL;
      }
      
      if(rebuf[loop-1]=='>')
	{
	  rebuf[loop]='\0';
	  if (verbose)
	    elog_notify(0,"SBE 39 resp: %s\n",rebuf);

	  val&=~O_NONBLOCK;
	  fcntl(*fd,F_SETFL,val);
	  return loop;
	}
    }

  elog_complain(0,"readline() = overflow in readline (c=%c)\n",rebuf[loop-1]);
  close(*fd);
  *fd=-1;
  return UNSUCCESSFUL;
}

int initConnection(char *host, char *port)
{
  int fd;
  unsigned long ina;
  int nconnected=1;
  struct hostent *host_ent;
  struct sockaddr_in addr;
  int val;

  /* fprintf(stderr,"in initConnection host ^%s^ port ^%s^\n",host,port); */

  if ( (ina=inet_addr(host)) != -1 )
    {
      memcpy(&addr.sin_addr, &ina,min(sizeof(ina), sizeof(addr.sin_addr)));
    }
  else
    {
      host_ent = gethostbyname(host);
      
      if ( host_ent == NULL )
	{
	  elog_complain(0,"initConnection = Could not resolve address (host=%s)\n",host);
	  return UNSUCCESSFUL;
	}
      
      memcpy(&addr.sin_addr, host_ent->h_addr,min(host_ent->h_length, sizeof(addr.sin_addr)));
    }
  
  /* make socket */
  if( (fd=socket(AF_INET, SOCK_STREAM, 0)) == -1 )
    {
      elog_complain(0,"initConnection = Could not make socket\n");
      return UNSUCCESSFUL;
    }
  
  /* create address from host ent */
  addr.sin_family = AF_INET;
  addr.sin_port = htons(atoi(port));
  
  nconnected=connect(fd, (struct sockaddr *) &addr, sizeof(addr));
  
  if (nconnected)
    {
      elog_complain(1,"initConnection = connect failed\n");
      close(fd);
      return UNSUCCESSFUL;
    }

  val=1;
  if (setsockopt(fd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
    {
      perror("setsockopt(SO_KEEPALIVE)");
      exit(-1);
    }

  return fd;
}

int test_sbe39_pkt(char *packet)
{
    int i;
    float val;
    double timestamp;
    char timestr[500];
    char timestr2[500];
    int day, year, hr, min, sec;

    i=4;
    if (*(packet+i)=='T')
	while(*(packet+i)!='\0' && *(packet+i)!='\r')
	    i++;
    
    if (*(packet+i)=='\r')
	i++;
    
    if (sscanf(packet+i," %f, %d %s %d, %d:%d:%d\r",&val,&day,timestr,&year,&hr,&min,&sec)!=7)
    {
	elog_complain(1,"can't parse SBE39 format (%s)",packet+i);
	return(-1);
    }

    sprintf(timestr2,"%02d %s %04d %02d:%02d:%02d US/Pacific",day,timestr,year,hr,min,sec);
    
    if (!is_epoch_string(timestr2,&timestamp))
    {
	elog_complain(0,"error parsing time string from packet \'%s\'. Invalid format.\n",timestr2);
	return(-2);
    }

    if (verbose)
	elog_notify(0,"packet parses ok (temp=%d C timestamp=%d)",val,timestamp);

    return(0);
}
