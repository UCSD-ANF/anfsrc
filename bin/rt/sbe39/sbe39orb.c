#include <unistd.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <time.h>
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

   This code by: Todd Hansen 4/1/2004
   Last Updated By: Todd Hansen 4/1/2004
*/

#define VERSION "$Revision: 1.1 $"

int verbose=0;
char *ipaddress=NULL;
char *port="4000";
char *orbname=":";
char *srcname="test_sta1";
int orbfd;
int interval=0;

#define UNSUCCESSFUL -9999

int getAttention(int *fd);
void flushOut(int *fd);
int flushUntil(int *fd,char c);
void printProgram(int *fd);
int setMemPtr(int *fd, int location);
int readline(int *fd, char *rebuf);
int initConnection(char *host, char *port);
int dataIntegrityCheck(char *completeResponse);
int stuffline(Tbl *r);
void getTime(int *fd);

void usage (void)
{
  cbanner(VERSION,"[-v] [-V] [-n portnumber] [-c net_sta] [-i interval] [-o $ORB] -a ipaddress ","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main(int argc,char *argv[])
{
  char ch;
  int fd=0;
  int speed=B9600;
  FILE *fil;
  char rebuf[5005];

  elog_init(argc,argv);

  while((ch=getopt(argc,argv,"Vva:n:i:c:"))!=-1)
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

  elog_notify(0,"sbe39orb %s\n",VERSION);

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
	  if (write(fd,"TS\n",3)<2)
	    {
	      elog_complain(1,"write(\"TS\\n\") failed");
	      close(fd);
	      fd=-1;
	    }
	  else
	    {
	      if (readline(&fd,rebuf+4)>0)
		{
		  *((short*)rebuf)=htons(100); /* set version */
		  *((short*)(rebuf+2))=htons(interval); /* set sample interval */
		  orbput(orbfd,srcname,now(),rebuf,strlen(rebuf)+5);
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
  int loop=0,
    val;
  int ret;
  char prompt[4];

  bzero(prompt,4);
  flushOut(fd);

  write(*fd,"\n",1);      
  sleep(2);
  while ((ret=read(*fd,prompt,1))>0 && prompt[0]!='>')
    /* nop */;

  if (ret<=0)
    {
      perror("getAttention(read)");
      close(*fd);
      *fd=-1;
      return(UNSUCCESSFUL);
    }

  /* fprintf(stderr,"got attention\n"); */
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
          perror("flushUntil(read())");
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

int readline(int *fd, char *rebuf)
{
  int loop=0;

  while(loop++<5000)
    {
      if (read(*fd,&(rebuf[loop-1]),1)<1)
        {
          perror("read()");
          close(*fd);
          *fd=-1;
          return UNSUCCESSFUL;
        }
      
      if(rebuf[loop-1]=='>')
	{
	  rebuf[loop]='\0';
	  if (verbose)
	    elog_notify(0,"SBE 39 resp: %s\n",rebuf);
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

