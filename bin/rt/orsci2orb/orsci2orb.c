#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <stdlib.h>
#include <orb.h>
#include <coords.h>
#include <netdb.h>
#include <stdio.h>
#include <stock.h>

#define VERSION "$Revision: 1.8 $"

/**************************************************************************
 * this can read the data from a Wavelan/EC-S connected to a radio shack  *
 * WX-200 weather sensor.                                                 *
 *                                                                        *
 * By: Todd Hansen (NLANR/MOAT, ROADNet) tshansen@nlanr.net    (c) 8/9/01 *
 **************************************************************************/

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

    This code was created as part of the ROADNet, NLANR, and HPWREN projects.
    See http://roadnet.ucsd.edu/ 
        http://www.nlanr.net/
	http://hpwren.ucsd.edu/

    Original Version Written By: Todd Hansen 8/9/2001
    Updated By: Todd Hansen 12/29/2004

 */

#define SLEEP 60

char DATA_DIR[80];

#define min(a,b)  (a<b?a:b)

struct out_frame
{
  long time;
  char buf[35];
};


FILE* init_connection(char *host, char *port, int *fd);
/* setup the connection the wavelan/EC-S serial port */

unsigned char read_frame(int fd, unsigned char *buf);
 /* buf must be at a minimum 35 bytes */
/* returns type or 0x00 if no valid packet recieved */

int verfy_chksum(unsigned char *buf, int size, unsigned char cksum);
/* just check the cksum of the frame, if it matches return 0 */

void write_results(char *name,char *date,struct out_frame *data,int size);

int main(int argc, char **argv)
{
  FILE *fil;
  int fd, orbfd;
  unsigned char buf[35];
  unsigned char outbuf[145];
  char srcname[255];
  struct out_frame data_8F, data_9F, data_AF, data_BF, data_CF;

  elog_init(argc,argv);

  if (argc!=5)
    {
      fprintf(stderr,"Usage:\n\torsci2orb ipaddress port net_sta_chan orb\n\n\taddress - the address of the host or the domain name (should match the\n\t\tdirectory created in /var/Web/Weather to store the data\n\tport - the port to which to connect\n\tnet_sta - the net_sta to use for sending data to the orb\n\torb - the orb to connect to send data\n");
      exit(-1);
    }

  elog_notify(0,"orsci2orb started. %s\n",VERSION);
     
  sprintf(srcname,"%s/EXP/ORsci",argv[3]);

  if ((orbfd=orbopen(argv[4],"w&"))<0)
    {
      elog_complain(1,"orbopen failed");
      exit(-1);
    }

  while (1)
    {
      data_8F.time=0;
      data_9F.time=0;
      data_AF.time=0;
      data_BF.time=0;
      data_CF.time=0;
      
      /* connect to remote wavelan/EC-S */
      fil=init_connection(argv[1],argv[2],&fd);
      if (fil==NULL)
	return(-1);
      
      while(data_8F.time==0 || data_9F.time==0 || data_AF.time==0 || data_BF.time==0 || data_CF.time==0)
	{
	  switch(read_frame(fd,buf))
	    {
	    case 0x8F: bcopy(buf,data_8F.buf,35); data_8F.time=time(NULL);break;
	    case 0x9F: bcopy(buf,data_9F.buf,35); data_9F.time=time(NULL);break;
	    case 0xAF: bcopy(buf,data_AF.buf,35); data_AF.time=time(NULL);break;
	    case 0xBF: bcopy(buf,data_BF.buf,35); data_BF.time=time(NULL);break;
	    case 0xCF: bcopy(buf,data_CF.buf,35); data_CF.time=time(NULL);break;
	    }
	}
      
      /* close the wavelan connection */
      fclose(fil);
      close(fd);
      
      *((short int *)outbuf)=htons(101);
      *((short int *)(outbuf+2))=htons(SLEEP);
      
      bcopy(data_8F.buf,outbuf+4,35);
      bcopy(data_9F.buf,outbuf+39,34);
      bcopy(data_AF.buf,outbuf+73,31);
      bcopy(data_BF.buf,outbuf+104,14);
      bcopy(data_CF.buf,outbuf+118,27);
      
      if (orbput(orbfd,srcname,now(),(char *)outbuf,145))
	{
	  complain ( 0, "orbput failed");
	  exit(-1);
	}

      sleep(SLEEP);
    }

  orbclose(orbfd);
}


void write_results(char *name,char *date,struct out_frame *data,int size)
{
  char filename[500];
  int lfd;

  sprintf(filename,"%s/%s.%s.wdata",DATA_DIR,name,date);
  lfd=open(filename,O_APPEND|O_CREAT|O_WRONLY);
  if (lfd<0)
    {
      fprintf(stderr,"%s: problem with file\n",filename);
      perror("open");
      exit(-1);
    }

  fchmod(lfd,0644);

  if (write(lfd,data,size)<size)
    {
      fprintf(stderr,"%s: problem with file\n",filename);
      perror("Couldn't write full sample to data file");
      exit(-1);
    }
  close(lfd);
}


FILE* init_connection(char *host, char *port, int *fd)
{
  FILE *fil;
  unsigned long ina;
  struct hostent *host_ent;
  struct sockaddr_in addr;
  int val;

  if (-1 != (ina=inet_addr(host)))
    memcpy(&addr.sin_addr, &ina, 
	   min(sizeof(ina), sizeof(addr.sin_addr)));
  else 
    {
      host_ent = gethostbyname(host);
      if ( host_ent == NULL )
	{
	  perror("Could not resolve address");
	  exit(-1);
	}
      memcpy(&addr.sin_addr, host_ent->h_addr, 
	     min(host_ent->h_length, sizeof(addr.sin_addr)));
      free(host_ent);
    }

  /*make socket*/
  *fd = socket(AF_INET, SOCK_STREAM, 0);

  /*create address from host ent*/
  addr.sin_family = AF_INET;
  addr.sin_port = htons(atoi(port));

  if (0 > connect(*fd, (struct sockaddr *) &addr, sizeof(addr))) 
    {
      perror("connect failed");
      exit(-1);
    }

  val=1;
  if (setsockopt(*fd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
    {
      perror("setsockopt(SO_KEEPALIVE)");
      exit(-1);
    }

  fil=fdopen(*fd,"r");
  
  if (fil==NULL)
    {
      perror("opening wavelan/EC-S connection");
      return(NULL);
    }

  if (setvbuf(fil,NULL,_IONBF,0)!=0)
    {
      perror("setting ANSI buffering.");
      return(NULL);
    }

  return(fil);
}

unsigned char read_frame(int fd, unsigned char *buf)
{
  int tmp, tmp2;
  int length;
  unsigned char calc_cksum;
  
  buf[0]=0;

  /* look for frame header */
  while (buf[0]!=0x8F && buf[0]!=0x9F && buf[0]!=0xAF && buf[0]!=0xBF && buf[0]!=0xCF)
    {
      if (read(fd,buf,1)!=1)
	{
	  perror("read from serial port");
	  return(0);
	}
    }

  switch (buf[0])
    {
    case 0x8F: length=35; break;
    case 0x9F: length=34; break;
    case 0xAF: length=31; break;
    case 0xBF: length=14; break;
    case 0xCF: length=27; break;
    }

  tmp=1;
  while(tmp<length)
    {
      tmp2=read(fd,buf+tmp,length-tmp);
      if (tmp2<1)
	{
	  perror("read from serial port");
	  return(0);
	}
      tmp+=tmp2;
    }

  if ((calc_cksum=verfy_chksum(buf,length,buf[length-1]))!=0)
      {
	fprintf(stderr,"checksum mismatch for frame, int cksum=%x, calc cksum=%x\n",buf[length-1],calc_cksum);
	return(0);
      }
  return(buf[0]);
}


int verfy_chksum(unsigned char *buf, int size, unsigned char cksum)
{
  int lcv=0;
  unsigned char sum;

  sum=0;
  for (lcv=0; lcv<size-1;lcv++)
    sum+=buf[lcv];

  if (sum==cksum)
    return(0);
  
  if (sum!=0)
    return(sum);
  else
    return(-1);
}



