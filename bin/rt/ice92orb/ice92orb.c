#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <regex.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <syslog.h>
#include <fcntl.h>
#include <orb.h>
#include <coords.h>
#include <netdb.h>
#include <stdio.h>
#include <stock.h>
#include <strings.h>
#include <Pkt.h>

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

   This code is designed to interface with the ICE-9 Strain Meter Data logger

   Written By: Todd Hansen 1/3/2003
   Last Updated By: Todd Hansen 5/23/2003
*/

#define VERSION "$Revision: 1.4 $"

#define KEEPALIVE_TIMEOUT 120
#define KEEPALIVE_DELAY_PKTS 8  
#define KEEPALIVE_DELAY_NOPKTS 50

#undef DEBUG

struct rcvd 
{
  short int msgID; /* 2 */
  short int msgSize; /* 8 */
  long int seq_num;
} strt;

struct PFOpkt_lnk
{
  short int msgID; /* 1 */
  short int msgSize;
  long seq_num;
  double timestamp; /* timestamp in unix format */
  double samp_rate; /* number of samples per second */
  char net_name[2]; /* network name */
  char sta_name[5]; /* station name */
  char pad; /* padding for alignment on solaris */
  short int num_chan; /* number of channels in the data */
  short int num_samp; /* number of samples */
  unsigned short int chksum; /* 30 bytes to here */
  /* char chan_id[][6];*/ /* channel_id letters (first 3 are channel, next */
                          /*   2 are location code, last char is a pad for */
                          /*   solaris alignment) */
  /* short int sample[][]; */
} pkt;

struct local_data_type
{
  double last_timestamp;
  long last_seqnum;
  long ipaddr;
  int filedes;
  char connected;
  char used;
} local_data;

int Stop=0;

char ip_address[50];
char *ipptr;

unsigned short sumit(char *buf, int size, char *buf2, int size2);
int traffic_data(struct PFOpkt_lnk *inpkt, char *buf, int bufsize, int orbfd, char *configfile);
void send_keepalive(struct local_data_type *lc);
int read_reliable(int sock, char *buf, int size);
double get_calib(char *configfile, char *net, char *sta, char *chan);

void mort(void);

void usage(void)
{
  cbanner(VERSION,"ice92orb [-V] [-p listenport] [-c configfile] [-S state/file] -o $ORB","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

main(int argc, char *argv[])
{
 int sockfd, newsockfd, clilen, childpid;
 struct sockaddr_in cli_addr, serv_addr;
 int fd, orbfd;
 time_t cur_time;
 int PORT=14028;
 int con, c;
 int val, lcv, lcv2, lcv3, high_fd;
 Relic relic;
 struct timeval timeout;
 char buffer[10002], *statefile=NULL, *orbname=NULL, *configfile=NULL, ch;
 fd_set read_fds, except_fds;

 while ((ch = getopt(argc, argv, "Vp:S:o:c:")) != -1)
   switch (ch) {
   case 'V':
     usage();
     exit(-1);
   case 'p':
     PORT=atoi(optarg);
     break;
   case 'c':
     configfile=optarg;
     break;
   case 'S':
     statefile=optarg;
     break;
   case 'o':
     orbname=optarg;
     break;
   default:
     printf("\n");
     usage();
     exit(-1);
   }

 if (orbname == NULL)
   {
     printf("-o $ORB option required!\n\n");
     usage();
     exit(-1);
   }

 local_data.connected=local_data.ipaddr=local_data.used=0;

  strt.msgID = htons(2);
  strt.msgSize = htons(8);

  printf("ice92orb started. port: %d orb: %s",PORT,orbname);
  if (statefile != NULL)
    {
      printf(" statefile: %s",statefile);
    }
  if (configfile != NULL)
    {
      printf(" configfile: %s",configfile);
    }
  printf("\n");
 
 *((short int *)buffer)=htons(100);

 if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
   {
     perror("ice92orb: can't open stream socket");
     exit(-1);
   }

 bzero((char *) &serv_addr, sizeof(serv_addr));
 serv_addr.sin_family      = AF_INET;
 serv_addr.sin_addr.s_addr  = htonl(INADDR_ANY);
 serv_addr.sin_port        = htons(PORT);

 if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
   {
     perror("ice92orb: can't bind local address");
     exit(-1);
   }

 listen(sockfd, 0);

 if ((orbfd=orbopen(orbname,"w&"))<0)
   {
     perror("orbopen failed");
     exit(-1);
   }

 if (statefile!=NULL)
   {
     exhume (statefile, &Stop, 0, &mort);
     relic.ip=(int *)&(local_data.last_seqnum);
     if (resurrect ("last_seqnum", relic, INT_RELIC) == 0 )
       {
	 printf("%s resurrected last sequence number=%d\n",VERSION,local_data.last_seqnum);
       }

     relic.dp=&(local_data.last_timestamp);
     if (resurrect ("last_timestamp", relic, DOUBLE_RELIC) == 0 )
       {
	 printf("%s resurrected last timestamp=%d\n",VERSION,local_data.last_timestamp);
       }

     relic.sp=&ipptr;
     ipptr=ip_address;
     if (resurrect ("ip_address", relic, STRING_RELIC) == 0)
       {
	 char *s;
	 printf("%s resurrection successful\n",VERSION);
	 printf("initialization completed %s\n",s=strtime(time(NULL)));
	 free(s);
	 local_data.used=1;
	 local_data.ipaddr=(int)inet_addr(ipptr);
	 free(ipptr);
	 ipptr=ip_address;
       }
     else
       {
	 char *s;
	 local_data.ipaddr=0;
	 printf("%s resurrection unsuccessful\n",VERSION);
	 printf("initialization completed %s\n",s=strtime(time(NULL)));
 	 free(s);
      }
   }

 con=0;

 while(1)
   {
     FD_ZERO(&except_fds);
     FD_SET(sockfd,&except_fds);
     FD_ZERO(&read_fds);
     FD_SET(sockfd,&read_fds);
     high_fd=sockfd+1;

     if (local_data.connected)
       {
	 FD_SET(local_data.filedes,&read_fds);
	 if (local_data.filedes>=high_fd)
	   high_fd=local_data.filedes+1;
       }

     timeout.tv_sec=KEEPALIVE_TIMEOUT;
     timeout.tv_usec=0;

     if (Stop)
       {
	 printf("program exiting before select\n");
	 bury();
	 exit(0);
       }

     lcv=select(high_fd,&read_fds,0,&except_fds,&timeout);

     if (Stop)
       {
	 printf("program exiting after select\n");
	 bury();
	 exit(0);
       }

     if (lcv<0)
       {
	 perror("select");
	 if (statefile != NULL)
	   bury();
	 exit(-1);
       }
     else if (lcv==0)
       {
	 send_keepalive(&local_data);
	 if (statefile != NULL)
	   bury();
       }
     else if (FD_ISSET(sockfd,&read_fds) || FD_ISSET(sockfd,&except_fds))
       {
	 clilen = sizeof(cli_addr);
	 newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
	 if (newsockfd < 0)
	   {
	     perror("accept error");
	     exit(-1);
	   }

	 val=1;
	 if (setsockopt(newsockfd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
	   {
	     perror("setsockopt(SO_KEEPALIVE)");
	     exit(-1);
	   }

	 con++;
	 
	 if (cli_addr.sin_addr.s_addr!=local_data.ipaddr)
	   {

	     if (local_data.ipaddr==0)
	       {
		 fprintf(stderr,"connection from %d %d.%d.%d.%d:%d\n",con,
			 (ntohl(cli_addr.sin_addr.s_addr)>>24)&255,
			 (ntohl(cli_addr.sin_addr.s_addr)>>16)&255,
			 (ntohl(cli_addr.sin_addr.s_addr)>>8)&255,
			 ntohl(cli_addr.sin_addr.s_addr)&255,
			 ntohs(cli_addr.sin_port));
	       }
	     else
	       fprintf(stderr,"WARNING: connection from %d %d.%d.%d.%d:%d when connection was previously from %d.%d.%d.%d (using same state for data retrieval)\n",con,
		       (ntohl(cli_addr.sin_addr.s_addr)>>24)&255,
		       (ntohl(cli_addr.sin_addr.s_addr)>>16)&255,
		       (ntohl(cli_addr.sin_addr.s_addr)>>8)&255,
		       ntohl(cli_addr.sin_addr.s_addr)&255,
		       ntohs(cli_addr.sin_port),
		       (ntohl(local_data.ipaddr)>>24)&255,
		       (ntohl(local_data.ipaddr)>>16)&255,
		       (ntohl(local_data.ipaddr)>>8)&255,
		       ntohl(local_data.ipaddr)&255);
	   }

	 if (local_data.used == 0)
	   {
	     local_data.used=1;
	     local_data.ipaddr=cli_addr.sin_addr.s_addr;
	     local_data.last_timestamp=0;
	     local_data.last_seqnum=-2;
	     local_data.connected=1;
	     local_data.filedes=newsockfd;
	     
	     strt.seq_num=htonl(local_data.last_seqnum+1);
	     
	     write(newsockfd,&strt,strt.msgSize);
	   }
	 else if (local_data.connected==1)
	   {
             fprintf(stderr,"already connected to a host! Disconnecting new connection.\n");
	     close(newsockfd);
	   }
	 else
	   {	     
	     local_data.connected=1;
	     local_data.filedes=newsockfd;
	     local_data.ipaddr=cli_addr.sin_addr.s_addr;
	     
	     strt.seq_num=htonl(local_data.last_seqnum+1);
	     
	     write(newsockfd,&strt,strt.msgSize);
	   }
       }
     else
       {
	 if (local_data.connected && FD_ISSET(local_data.filedes,&read_fds))
	   {	     
	     if (read_reliable(local_data.filedes,(char*)&pkt,38)>0)
	       {
		 if (read_reliable(local_data.filedes,(char*)&buffer,ntohs(pkt.msgSize)-38)>0)
		   {
		     val=sumit((char*)&pkt,36,(char*)buffer,pkt.msgSize-38); /* skip checksum */
		     
		     if (val!=ntohs(pkt.chksum))
		       {
			 fprintf(stderr,"checksum mismatch! (%d = client id, local=%d, received=%d)\n",lcv,val,ntohs(pkt.chksum));
			 local_data.connected=0;
			 close(local_data.filedes);
			 if (statefile != NULL)
			   bury();
		       }
		     else
		       {
			 local_data.last_timestamp=pkt.timestamp;
			 local_data.last_seqnum=ntohl(pkt.seq_num);
			 
			 traffic_data(&pkt, buffer, pkt.msgSize-38, orbfd, configfile);
		       }
		   }
		 else 
		   {
		     close(local_data.filedes);
		     local_data.connected=0;
		     if (statefile != NULL)
		       bury();
		   }
	       }
	     else
	       {
		 close(local_data.filedes);
		 local_data.connected=0;
		 if (statefile != NULL)
		   bury();
	       }
	   }
       }
   }

 orbclose(orbfd);
 return(0);
}

int traffic_data(struct PFOpkt_lnk *inpkt, char *buf, int bufsize, int orbfd, char *configfile)
{
 struct Packet *orbpkt;
 struct PktChannel *pktchan;
 int orbpkt_size, lcv, lcv2;
 char srcname_full[116];
 double newtimestamp;
 static char *newpkt = NULL;
 int newpkt_size;
 static int newpkt_alloc_size=0;
 int *data;

 orbpkt =  newPkt() ;
 orbpkt->pkttype = suffix2pkttype("MGENC");
 orbpkt->time=inpkt->timestamp;
 orbpkt->nchannels=ntohs(inpkt->num_chan);
 strncpy(orbpkt->parts.src_net,inpkt->net_name,2);
 strncpy(orbpkt->parts.src_sta,inpkt->sta_name,5);
 *(orbpkt->parts.src_chan)=0;
 *(orbpkt->parts.src_loc)=0;

 for (lcv=0;lcv<orbpkt->nchannels;lcv++)
   {

     pktchan = newPktChannel();
     pktchan -> datasz = ntohs(inpkt->num_samp);
     pktchan->data=malloc(4*ntohs(inpkt->num_samp));
     if (pktchan->data==NULL)
       {
	 perror("malloc");
	 exit(-1);
       }

     for (lcv2=0;lcv2<pktchan->datasz;lcv2++)
       {
	 pktchan->data[lcv2]=htonl(ntohs(*(short int*)(buf+ntohs(inpkt->num_chan)*lcv2*2+lcv*2+ntohs(inpkt->num_chan)*6)));
       }

     pktchan->time=inpkt->timestamp;
     strncpy(pktchan->net,inpkt->net_name,2);
     strncpy(pktchan->sta,inpkt->sta_name,5);
     strncpy(pktchan->chan,buf+lcv*6,3);
     strncpy(pktchan->loc,buf+lcv*6+3,2);
     strncpy(pktchan->segtype,"S",4);
     pktchan->nsamp=ntohs(inpkt->num_samp);
     pktchan->calib=get_calib(configfile,pktchan->net,pktchan->sta,pktchan->chan);
     pktchan->calper=-1;
     pktchan->samprate=inpkt->samp_rate;
     pushtbl(orbpkt->channels,pktchan);
   }
 
 if (stuffPkt(orbpkt, srcname_full, &newtimestamp, &newpkt, &newpkt_size, &newpkt_alloc_size)<0)
   {
     printf("stuff failed\n");
     complain ( 0, "stuffPkt routine failed\n");
   }
 else if (orbput(orbfd, srcname_full, newtimestamp, newpkt, newpkt_size) < 0)
   {
     printf("put failed\n");
     complain ( 0, "orbput fails %s\n",srcname_full );
   }  

#ifdef DEBUG
 showPkt(0,srcname_full,newtimestamp,newpkt,newpkt_size,stdout,PKT_UNSTUFF);
#endif
 return 0;
}

void send_keepalive(struct local_data_type *lc)
{
  int loop;
  
  if (lc->connected)
    {
      strt.seq_num=htonl(lc->last_seqnum+1);
      if (write(lc->filedes,&strt,strt.msgSize)<0)
	{
	  printf("lost connection. (keepalive send)");
	  close(lc->filedes);
	  lc->connected=0;
	}
    }
}



unsigned short sumit(char *buf, int size, char *buf2, int size2)
{
  int lcv;
  unsigned short sum;

  sum=0;
  for (lcv=0;lcv<(size/2);lcv++)
    {
      sum^=((unsigned short int *)buf)[lcv];
    }

  for (lcv=0;lcv<(size2/2);lcv++)
    {
      sum^=((unsigned short int *)buf2)[lcv];
    }
	
  return(sum);
}

int read_reliable(int sock, char *buf, int size)
{
  int lcv, val;
  
  lcv=0;
  while(lcv<size)
  {
    val=read(sock,buf+lcv,size-lcv);
    if (Stop)
      {
	bury();
	close(sock);
	exit(0);
      }
    if (val>0)
      {
	lcv+=val;
      }
    else
      return 0;
  }
  
  return 1;
}

void mort (void)
{
  sprintf(ip_address,"%d.%d.%d.%d",
	  (ntohl(local_data.ipaddr)>>24)&255,
	  (ntohl(local_data.ipaddr)>>16)&255,
	  (ntohl(local_data.ipaddr)>>8)&255,
	  ntohl(local_data.ipaddr)&255);
}

double get_calib(char *configfile, char *net, char *sta, char *chan)
{
  int lcv;
  double calib;
  static Pf *pf;
  char str[5000];
  void *result=NULL;

  if (configfile)
    {
      lcv=pfupdate(configfile,&pf);
      if (lcv<0)
	{
	  fprintf(stderr,"error reading config file %s\n\n",configfile);
	  exit(-1);
	}
      
      if (lcv>0)
	fprintf(stderr,"config file updated, rereading it.\n");

      sprintf(str,"calib_%s_%s_%s",net,sta,chan);
      if (pfget(pf,str,&result)!=PFINVALID)
	{
	  calib=pfget_double(pf,str);
	  return(calib);
	}
      else
	{
	  sprintf(str,"calib_%s_%s",net,sta);
	  if (pfget(pf,str,&result)!=PFINVALID)
	    {
	      calib=pfget_double(pf,str);
	      return(calib);
	    }
	  else
	    {
	      sprintf(str,"calib_%s",net);
	      if (pfget(pf,str,&result)!=PFINVALID)
		{
		  calib=pfget_double(pf,str);
		  return(calib);
		}
	      else
		{
		  sprintf(str,"calib");
		  if (pfget(pf,str,&result)!=PFINVALID)
		    {
		      calib=pfget_double(pf,str);
		      return(calib);
		    }
		  else
		    return 0;
		}
	    }
	}
    }
  else
    return(0);
}
