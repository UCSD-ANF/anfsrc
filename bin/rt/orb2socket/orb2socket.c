#include <unistd.h>
#include <strings.h>
#include <string.h>
#include <signal.h>
#include <orb.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <Pkt.h>

#define VERSION "$Revision: 1.2 $"

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

   Written By: Todd Hansen 4/1/2004
   Updated By: Todd Hansen 4/14/2004
*/
int verbose=0;
int unstuff=0;

void usage(void)
{            
  cbanner(VERSION,"[-v] [-V] [-u] [-p tcpport] [-m matchstring ] [-w tcpwindow] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}            


int main (int argc, char *argv[])
{
  int orbfd, fd;
  FILE *sock, *sock2;
  int tcp_send_buf;
  char fifo[60], *pkt=NULL;
  char srcname[60], buf[1024];
  double pkttime, lastpkttime=0;
  int pktid, ch;
  int con=0, val, lcv, lcv2, lcv3, first, ret, off=0;
  int sockfd, newsockfd, clilen;
  struct sockaddr_in cli_addr, serv_addr;
  int nbytes, bufsize=0;
  int PORT=4773, win=0;
  char *ORBname=":";
  fd_set exceptfds;
  fd_set readfds;
  Packet *upacket=NULL;
  struct timeval timeout;
  double ptime;
  char psrcname[ORBSRCNAME_SIZE] ;
  PktChannel *pc=NULL;
  char outbuf[5000];

  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVup:o:m:w:")) != -1)
    switch (ch) {
    case 'V': 
      usage();
      exit(-1);
    case 'v': 
      verbose=1;
      break;  
    case 'u': 
      unstuff=1;
      break;  
    case 'p': 
      PORT=atoi(optarg);
      break;  
    case 'o': 
      ORBname=optarg;
      break;  
    case 'm': 
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

  if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
      perror("can't open stream socket");
      exit(-1);
    }
  
  bzero((char *) &serv_addr, sizeof(serv_addr));
  serv_addr.sin_family      = AF_INET;
  serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  serv_addr.sin_port        = htons(PORT);
  
  if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
    {
      perror("revelle_data: can't bind local address");
      exit(-1);
    }

  listen(sockfd, 1);
  if (verbose)
    {
      elog_notify(0,"selecting on: \"%s\"",SRCNAME);
    }
  if (orbselect(orbfd,SRCNAME)<0)
    {
      elog_complain(1,"orbselect");
      exit(-1);
    }
  
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

      sock2=fdopen(newsockfd,"r");
      if (sock2==NULL)
	{
	  elog_complain(1,"fdopen(fd)");
	  exit(-1);
	}


      if (fscanf(sock2,"%d",&pktid)<1)
	{
	  pktid=-1;
	  elog_complain(0,"failed to read pktid, using -1 for pktid\n",psrcname+1);
	}

      sock=fdopen(newsockfd,"w");
      if (sock==NULL)
	{
	  elog_complain(1,"fdopen(newsockfd)");
	  exit(-1);
	}


      if (pktid>=0)
	{
	  if (orbseek(orbfd,pktid)<0)
	    {
	      elog_complain(1,"orbseek to a location");
	      if (orbseek(orbfd,ORBOLDEST)<0)
		{
		  elog_complain(1,"orbseek oldest (recover)");
		  exit(-1);
		}
	    }

	  if (verbose)
	    elog_notify(0,"going to pktid=%d, per request\n",pktid);
	}
      else
	{
	  if (orbseek(orbfd,ORBOLDEST)<0)
	    {
	      elog_complain(1,"orbseek oldest");
	      exit(-1);
	    }

	  if (verbose)
	    elog_notify(0,"going to beginning of buffer, per request\n");
	}

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
	    
	    if ((ret=orbreap_timeout(orbfd,10,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize))==-1)
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
		
		if (unstuff)
		  {
		    strcpy(psrcname,srcname);
		    if ((ret=unstuffPkt(psrcname,ptime,pkt,nbytes,&upacket))!=Pkt_wf)
		      {
			complain(1,"unstuffPkt (ret=%d on %s):",ret,srcname);
			exit(-1);
		      }

		    for (lcv3=0;lcv3<upacket->nchannels && lcv;lcv3++)
		      {
			pc=gettbl(upacket->channels,lcv3);
			sprintf(outbuf,"****\n\r");
			if (write(fd,outbuf,strlen(outbuf))<strlen(outbuf))
			  {
			    elog_complain(1,"write(fd delimiter)");
			    close(fd);
			    fclose(sock);
			    lcv=0;
			  }

			fprintf(sock,"%s_%s_%s",pc->net,pc->sta,pc->chan);
			if (pc->loc[0]!='\0')
			  fprintf(sock,"_%s",pc->loc);
			fprintf(sock,"\n\r");
			fprintf(sock,"timestamp: %.3f (%s)\n\r",pc->time,strtime(pc->time));
			fprintf(sock,"samprate: %.3f\n\r",pc->samprate);
			fprintf(sock,"calib: %.3f\n\r",pc->calib);
			if (pc->calib==0)
			  pc->calib=1;
			fprintf(sock,"segtype: %c\n\r",pc->segtype[0]);
			fprintf(sock,"pktid: %d\n\r",pktid);

			if (fprintf(sock,"number of samples: %d\n\r",ntohl(pc->nsamp))<0)
			  {
			    elog_complain(1,"fprintf(sock)");
			    close(fd);
			    fclose(sock);
			    fclose(sock2);
			    lcv=0;
			  }

			for (lcv2=0;lcv2<ntohl(pc->nsamp);lcv2++)
			  {
			    fprintf(sock,"samp %d: %f @ %.3f for %s_%s_%s pktid %d",lcv2,ntohl(pc->data[lcv2])*pc->calib,pc->time+(lcv2*1.0/(pc->samprate)),pc->net,pc->sta,pc->chan,pktid);
			    if (pc->loc[0]!='\0')
			      fprintf(sock,"_%s",pc->loc);
			    fprintf(sock,"\n\r");
			  }

			fflush(sock);
		      }
		    
		    freePkt(upacket);
		    upacket=NULL;
}
		else if (write(fd,pkt,nbytes)<0)
		  {
		    perror("write pkt to socket");
		    fclose(sock);
		    fclose(sock2);
		    close(fd);
		    lcv=0;
		  }
	    }
	    else 
	      {
		timeout.tv_sec=5;
		timeout.tv_usec=0;
		
		FD_ZERO(&exceptfds);
		FD_SET(fd,&exceptfds);
		FD_ZERO(&readfds);
		FD_SET(fd,&readfds);
		if (select(fd+1,&readfds,NULL,&exceptfds,&timeout)>0)
		  {
		    if (read(fd,outbuf,1)<1)
		      {
			perror("read test from socket (connection probably closed)\n");
			fclose(sock);
			fclose(sock2);
			close(fd);
			lcv=0;
		      }
		  }
	      }
	      

	}
      
      fclose(sock);
      fclose(sock2);
      close(fd);
      lcv=0;
    }
}

