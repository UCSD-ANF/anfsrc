#include <unistd.h>
#include <strings.h>
#include <signal.h>
#include <orb.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include <zlib.h>

#define VERSION "$Revision: 1.8 $"

char *SRCNAME="CSRC_IGPP_TEST";

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
   Updated By: Todd Hansen 4/16/2004

   1.7 was the first revision to include zlib compression

*/

int processpacket(char *buf, int size, int orbfd);

void usage(void)
{            
  cbanner(VERSION,"[-v] [-V] [-p tcpport] [-s net_sta_cha_loc] [-w tcpwindow] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}            


int main (int argc, char *argv[])
{
  int orbfd, fd, orboutfd;
  int tcp_send_buf;
  char fifo[60], *pkt=NULL;
  char srcname[60], buf[1024];
  char inflated[60010];
  double pkttime, lastpkttime=0;
  int pktid, ch;
  int con=0, val, lcv, first, ret, off=0;
  int sockfd, newsockfd, clilen;
  struct sockaddr_in cli_addr, serv_addr;
  int nbytes, bufsize=0;
  fd_set exceptfds, readfds;
  struct timeval timeout;
  int PORT=2772, verbose=0, win=0;
  char *ORBname=":";
  z_stream compstream;
  int inflateOn=1;
  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVp:o:s:w:")) != -1)
    switch (ch) {
    case 'V': 
      usage();
      exit(-1);
    case 'v': 
      verbose=1;
      break;  
    case 'p': 
      PORT=atoi(optarg);
      break;  
    case 'o': 
      ORBname=optarg;
      break;  
    case 's': 
      SRCNAME=optarg;
      break;  
    case 'w':
      win=atoi(optarg);
      break;
    default:  
      fprintf(stderr,"Unknown Argument.\n\n");
      usage();
      exit(-1);
    }         

  orbfd=orbopen(ORBname,"r&");
  if (orbfd<0)
    {
      perror("orbopen");
      exit(-1);
    }

  orboutfd=orbopen(ORBname,"w&");
  if (orboutfd<0)
    {
      perror("orbopen(orboutfd)");
      exit(-1);
    }

  if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
      perror("can't open stream socket");
      exit(-1);
    }
  elog_notify(0,"decompressing data with: zlib %s\n",zlibVersion());
  compstream.next_in=Z_NULL;
  compstream.next_out=Z_NULL;
  compstream.msg=Z_NULL;
  compstream.zalloc=Z_NULL;
  compstream.zfree=Z_NULL;
  compstream.opaque=Z_NULL;
  ret=inflateInit(&compstream);
  
  if (ret!=Z_OK)
  {
      elog_complain(0,"zlib inflateInit() failed %d\n",ret);
      
      if (ret==Z_MEM_ERROR)
	  elog_complain(0,"inflateInit: Memory Allocation error\n");
      
      if (ret==Z_VERSION_ERROR)
	  elog_complain(0,"inflateInit: libz Version mismatch Error (compile=%s, runtime=%s\n",ZLIB_VERSION,zlibVersion());
      
      if (compstream.msg!=NULL)
	  elog_complain(0,"inflauteInit: error message=\"%s\"",compstream.msg);

      inflateOn=0;
      elog_complain(0,"inflateInit: we will not be able to comprehend compressed packets\n");
  }
  
  bzero((char *) &serv_addr, sizeof(serv_addr));
  serv_addr.sin_family      = AF_INET;
  serv_addr.sin_addr.s_addr  = htonl(INADDR_ANY);
  serv_addr.sin_port        = htons(PORT);
  
  if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
    {
      perror("revelle_data: can't bind local address");
      exit(-1);
    }

  listen(sockfd, 1);

  sprintf(fifo,"%s/EXP/MBEN",SRCNAME);
  if (orbselect(orbfd,fifo)<0)
    {
      elog_complain(1,"orbselect");
      exit(-1);
    }
  
  if (orbseek(orbfd,ORBOLDEST)<0)
    {
      elog_complain(1,"orbseek");
      exit(-1);
    }
  
  /*if (orbafter(orbfd,time(NULL)-20*60)<0)
    {
      perror("orbafter");
    }*/

  while (1)
    {
      clilen = sizeof(cli_addr);
      newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
      if (newsockfd < 0)
	{
	  perror("accept error");
	  exit(-1);
	}
      

      if (win > 0)
	{
	  val=sizeof(int);
	  tcp_send_buf=win;
	  if (setsockopt(newsockfd,SOL_SOCKET,SO_SNDBUF,&tcp_send_buf,val))
	    {
	      perror("setsockopt");
	      exit(-1);
	    }
	} 

      if (verbose)
	{
	  val=sizeof(int);
	  if (getsockopt(newsockfd,SOL_SOCKET,SO_SNDBUF,&tcp_send_buf,&val))
	    {
	      perror("getsockopt");
	      exit(-1);
	    }
	  if (win > 0)
	    printf("requested tcpwindow=%d\n",win);
	  printf("tcpwindow=%d\n",tcp_send_buf);
	}      

      val=1;
      if (setsockopt(newsockfd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
	{
	  perror("setsockopt(SO_KEEPALIVE)");
	  exit(-1);
	}
      
      con++;
      
      fprintf(stderr,"connection from %d %d.%d.%d.%d:%d\n",con,
	      (ntohl(cli_addr.sin_addr.s_addr)>>24)&255,
	      (ntohl(cli_addr.sin_addr.s_addr)>>16)&255,
	      (ntohl(cli_addr.sin_addr.s_addr)>>8)&255,
	      ntohl(cli_addr.sin_addr.s_addr)&255,
	      ntohs(cli_addr.sin_port));
  
      fd=newsockfd;

      lcv=1;
      first=1;
      while(lcv)
	{
	    if (orbtell(orbfd)<0)
	    { /* recover if we loose the end of the ring buffer */
		if (verbose)
		    elog_complain(0,"lost the end of the ring buffer, reseeking oldest\n");
		
		if (orbseek(orbfd,ORBOLDEST)<0)
		{
		    elog_complain(1,"orbseek");
		    exit(-1);
		}
	    }
	    
	    if ((ret=orbreap_nd(orbfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize))==-1)
	    {
		elog_complain(1,"orbreap");
		exit(-1);
	    }
	    
	    if (ret != ORB_INCOMPLETE)
	    {
		if (first)
		{
		    first=0;
		    fprintf(stderr,"first packet time=%.2f, previous pkt time=%.2f\n",pkttime,lastpkttime);
		}
		lastpkttime=pkttime;
		
		if (ntohs(*(short int*)pkt)!=100 && (ntohs(*(short int*)pkt)!=101 || !inflateOn))
		{
		    fprintf(stderr,"version mismatch, expected 100 (standard) or 101 (compression), got %d\n",ntohs(*(short int*)pkt));
		}
		else if (ntohs(*(short int*)pkt)==100)
		{
		    if (write(fd,pkt+2,nbytes-2)<0)
		    {
			perror("write pkt to socket");
			close(fd);
			lcv=0;
		    }
		}
		else
		{
		    compstream.next_in=pkt+2;
		    compstream.avail_in=nbytes-2;
		    compstream.total_in=0;
		    compstream.total_out=0;
		    compstream.next_out=inflated;
		    compstream.avail_out=60000;		    
		    ret=inflate(&compstream,Z_FINISH);
		    if (ret==Z_OK)
		    {
			if (compstream.avail_out==0)
			{
			    elog_complain(0,"inflate failed. msg=\"%s\" ret=%d\n avail_out=0, incoming size=%d bytes",compstream.msg,ret,nbytes-2);
			    exit(-1);
			}

			if (write(fd,inflated,compstream.total_out)<0)
			{
			    perror("write inflated pkt to socket");
			    close(fd);
			    lcv=0;
			}
		    }       
		    else
		    {
			elog_complain(0,"inflate failed. msg=\"%s\" ret=%d\n",compstream.msg,ret);
			exit(-1);
		    }

		}
	    }

	    if (lcv)
	    {
	      FD_ZERO(&readfds);
	      FD_ZERO(&exceptfds);
	      FD_SET(fd,&readfds);
	      FD_SET(orbfd,&readfds);
	      FD_SET(fd,&exceptfds);
	      FD_SET(orbfd,&exceptfds);
	      timeout.tv_sec=300;
	      timeout.tv_usec=0;
	      if (orbfd>fd)
		  ret=select(orbfd+1,&readfds,NULL,&exceptfds,&timeout);
	      else
		  ret=select(fd+1,&readfds,NULL,&exceptfds,&timeout);
	      
	      if (ret < 0)
	      {
		  perror("select(fd,orbfd)");
		  exit(-1);
	      }
	      
	      if (FD_ISSET(fd,&readfds) || FD_ISSET(fd,&exceptfds))
	      {
		  if (read(fd,buf+off,1)<=0)
		  {
		      perror("read socket");
		      lcv=0;
		      close(fd);
		  }
		  
		  if (*(buf+off)== '\n')
		  {
		      processpacket(buf,off+1,orboutfd);
		      off=0;
		      if (verbose)
			  fprintf(stderr,"sent command packet!");
		  }
		  else
		      off++;
		  
		  if (off>1024)
		  {
		      fprintf(stderr,"command buff to big, dumping.\n");
		      off=0;
		  }
	      }
	    }
	}
      
      close(fd);
    }
}

int processpacket(char *buf, int size, int orbfd)
{
  char lbuf[1030];
  char srcname[48];

  *(short*)lbuf=htons(100);
  bcopy(buf,lbuf+2,size);
  sprintf(srcname,"%s/EXP/MBEN_CMD",SRCNAME);
  
  if (orbput(orbfd,srcname,now(),lbuf,size+2))
    {
      perror("orbput(orboutfd)");
    }
  return(0);
}

