#include <unistd.h>
#include <Pkt.h>
#include <orb.h>
#include "packets.h"
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <sys/file.h>
#include <fcntl.h>

#define min(a,b)  (a<b?a:b)

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

   Written By: Todd Hansen 10/3/2003
   Updated By: Todd Hansen 10/29/2003

*/

#define VERSION "$Revision: 1.3 $"

void usage(void)
{
  cbanner(VERSION,"[-v] [-V] [-u UUID] [-l] [-n neighborip] [-p port] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

void snarf(int orbfd_main, int orbfd_aux, int orbfd_ctl, int listen);

int listen_forremote(int PORT);
int connect_toremote(char *ip, int PORT);
void sendping(void); /* dude, where is my neighbor */
int grabneigh(int waitack); /* when we receive from our neighbor */
int barf(int orbfd_ctl); /* spew these packts */
int findandroute(int orbfd_main); /* route normal packets */
void denied_packet(int pktid, int destUUID);

int UUID=4;
int nUUID=-1;
int neighfd=-1;
int listenfd=-1;
int verbose=0;
char *Neighip=NULL;
int orbfd_out;
int awaitack=0;
int port=14442;
Pf *ctlpf=NULL;

int main (int argc, char *argv[])
{
  char ch, *c;
  int listen=0;
  char *ORBname=":";
  int orbfd_main, orbfd_aux, orbfd_ctl;

  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVlp:o:n:u:")) != -1)
   switch (ch) 
     {
     case 'V':
       usage();
       exit(-1);
     case 'v':
       verbose=1;
       break;
     case 'l':
       listen=1;
       break;
     case 'o':
       ORBname=optarg;
       break;
     case 'n':
       Neighip=optarg;
       break;
     case 'u':
       UUID=atoi(optarg);
       break;
     case 'p':
       port=atoi(optarg);
       break;
     default:
       fprintf(stderr,"Unknown Argument.\n\n");
       usage();
       exit(-1);
     }

  if (verbose)
    {
      printf("VORBrouter version %s, UUID=%d -> nUUID=%d\n",VERSION,UUID,nUUID);
    }

  if (Neighip==NULL && !listen)
    {
      fprintf(stderr,"No Neighbor, I can\'t deal with you anymore.\nLeave me alone.\n");
      exit(-1);
    }

  orbfd_main=orbopen(ORBname,"r&");
  orbfd_aux=orbopen(ORBname,"r&");
  orbfd_ctl=orbopen(ORBname,"r&");
  orbfd_out=orbopen(ORBname,"w&");

  if (orbfd_main<0 || orbfd_aux<0 || orbfd_ctl<0)
    {
      perror("connect to bossy orb failed!");
      exit(-1);
    }

  orbselect(orbfd_ctl,"/pf/VORBrouter");
  orbselect(orbfd_main,".*/VORB.*");
  orbreject(orbfd_main,"/pf/VORBrouter");

  if (listen)
    listenfd=listen_forremote(port);

  while (1)
    {
      snarf(orbfd_main, orbfd_aux, orbfd_ctl, listen);
    }
}

void snarf(int orbfd_main, int orbfd_aux, int orbfd_ctl, int listen)
{
  fd_set readfds;
  fd_set exceptfds;
  int maxfd;
  struct timeval waiter;
  int ret=0;
  struct sockaddr_in cliaddr;
  int clilen;
  struct keepalive ka;
  int val;
  maxfd=orbfd_main;
  if (orbfd_ctl > maxfd)
    maxfd=orbfd_ctl;

  FD_ZERO(&readfds);
  FD_SET(orbfd_main,&readfds);
  FD_SET(orbfd_ctl,&readfds);

  FD_ZERO(&exceptfds);
  FD_SET(orbfd_main,&exceptfds);
  FD_SET(orbfd_ctl,&exceptfds);

  if (listen && neighfd<0)
    {
      if (listenfd > maxfd)
	maxfd=listenfd;
      FD_SET(listenfd,&readfds);
      FD_SET(listenfd,&exceptfds);
    }
  else if (neighfd >= 0)
    {
      if (neighfd > maxfd)
	maxfd=neighfd;
      FD_SET(neighfd,&readfds);
      FD_SET(neighfd,&exceptfds);
    }

  maxfd++;
  waiter.tv_sec=60;
  waiter.tv_usec=0;
  
  ret=select(maxfd,&readfds,NULL,NULL,&waiter);

  if (ret<0)
    {
      perror("select");
      exit(-1);
    }
  
  if (ret==0)
    {
      if (neighfd>=0)
	{
	  sendping();
	  if (verbose)
	    fprintf(stderr,"sending ping to neighbor (%d @ %d)\n",nUUID,time(NULL));
	}
      else if (verbose)
	fprintf(stderr,"timed out, no connection to ping (@ %d)\n",time(NULL));
    }
  else
    {
      if (listen && (FD_ISSET(listenfd,&readfds) || FD_ISSET(listenfd,&exceptfds)))
	{
	  neighfd=accept(listenfd,(struct sockaddr*)&cliaddr,&clilen);
	  if (neighfd<0)
	    perror("accept");
	  else
	    {
	      if (verbose)
		fprintf(stderr,"new connection received %s:%d\n",inet_ntoa(cliaddr.sin_addr),ntohs(cliaddr.sin_port));

	      if (Neighip==NULL)
		{
		  Neighip=malloc(80);
		}

	      sprintf(Neighip,"%s",inet_ntoa(cliaddr.sin_addr));

	      val=1;
	      if (setsockopt(neighfd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
		{
		  perror("setsockopt(SO_KEEPALIVE)");
		  exit(-1);
		}

	      ka.version=htonl(PKTVERSION);
	      ka.type=htonl(5);
	      ka.UUID=htonl(UUID);
	      
	      if (write(neighfd,&ka,sizeof(ka))<sizeof(ka))
		{
		  perror("write inital packet");
		  close(neighfd);
		  neighfd=-1;
		}	      
	    }
	}

      /* always check for ctl packet, if we don't we might not 
	 recover a busted orb connection */
      for (;barf(orbfd_ctl)||ctlpf==NULL;)
	if (ctlpf==NULL)
	  sleep(3);


      /* always check for data packet, second */
      findandroute(orbfd_main);
      
      if (neighfd>=0 && FD_ISSET(neighfd,&readfds))
	grabneigh(0);
    }

  if (neighfd<0 && !listen)
    {
      neighfd=connect_toremote(Neighip, port);
    }
}

void sendping(void)
{
  struct keepalive ka;

  ka.version=htonl(0);
  ka.type=htonl(5);
  ka.UUID=htonl(UUID);
  if (write(neighfd,&ka,sizeof(ka))<sizeof(ka))
    {
      perror("write keep alive (sendping)");
      close(neighfd);
      neighfd=-1;
    }	      
  if (verbose)
    fprintf(stderr,"keep alive sent\n");
}

int grabneigh(int waitack)
{
  char buf[80];
  char *pktbuf=NULL;
  struct keepalive ka;
  int pktsize;
  double pkttime;
  char SRCNAME[ORBSRCNAME_SIZE];
  char SRCNAME_CUR[ORBSRCNAME_SIZE];
  int destcnt;
  int retval=0;
  struct head header;
  struct ack ackpkt;
  
  if (read(neighfd,&header,sizeof(header))<sizeof(header))
    {
      perror("read primary header");
      close(neighfd);
      neighfd=-1;
      return;
    }

  if (ntohl(header.version) != PKTVERSION)
    {
      fprintf(stderr,"Consistency missing, check version match (local %d != remote %d)\n",PKTVERSION,ntohl(header.version));
      exit(-1);
    }

  switch (ntohl(header.type))
    {
    case 4: /* ack packet */
      /* wait for ack */
      if (ntohl(header.id)!=waitack)
	{
	  fprintf(stderr,"failed ack packet, sync lost\n");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}
      retval=1;
      break;

   case 5: /* keep alive */
      read(neighfd,&nUUID,sizeof(nUUID));
      nUUID=ntohl(nUUID);
      ka.version=htonl(0);
      ka.id=header.id; /* replies use the same header id */
      ka.type=htonl(6);
      ka.UUID=htonl(UUID);
      if (write(neighfd,&ka,sizeof(ka))<sizeof(ka))
	{
	  perror("write keep alive reply");
	  close(neighfd);
	  neighfd=-1;
	}	      
      if (verbose)
	fprintf(stderr,"keep alive received, reply sent\n");
      break;

    case 6: /* keep alive reply */
      if (read(neighfd,&nUUID,sizeof(nUUID))<sizeof(nUUID))
	{
	  perror("read");
	  close(neighfd);
	  neighfd=-1;
	}
      nUUID=ntohl(nUUID);
      if (verbose)
	fprintf(stderr,"keep alive reply received\n");
      break;

    case 7: /* data pkt recv */
      if (read(neighfd,&pktsize,sizeof(pktsize))<sizeof(pktsize))
	{
	  perror("read data pkt header");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}

      if (read(neighfd,&destcnt,sizeof(destcnt))<sizeof(destcnt))
	{
	  perror("read data pkt header (destcnt)");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}      

      if (read(neighfd,&SRCNAME_CUR,ORBSRCNAME_SIZE)<ORBSRCNAME_SIZE)
	{
	  perror("read data pkt header (srcname_cur)");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}      

      if (read(neighfd,&SRCNAME,ORBSRCNAME_SIZE)<ORBSRCNAME_SIZE)
	{
	  perror("read data pkt header (srcname)");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}      

      pktbuf=malloc(ntohl(pktsize)+sizeof(struct datapkt)+sizeof(int)*ntohl(destcnt));

      bcopy(&header,pktbuf,sizeof(header));
      bcopy(&pktsize,pktbuf+sizeof(header),sizeof(pktsize));
      bcopy(&destcnt,pktbuf+sizeof(header)+sizeof(pktsize),sizeof(destcnt));
      bcopy(SRCNAME_CUR,pktbuf+sizeof(header)+sizeof(destcnt)+sizeof(pktsize),ORBSRCNAME_SIZE);
      bcopy(SRCNAME,pktbuf+sizeof(header)+sizeof(destcnt)+sizeof(pktsize)+ORBSRCNAME_SIZE,ORBSRCNAME_SIZE);

      if (read(neighfd,pktbuf+sizeof(struct datapkt),ntohl(pktsize)+sizeof(int)*ntohl(destcnt))<ntohl(pktsize)+sizeof(int)*ntohl(destcnt))
	{
	  perror("read data pkt body");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}      

      if (orbput(orbfd_out,SRCNAME_CUR,pkttime,pktbuf,ntohl(pktsize)+sizeof(struct datapkt)+sizeof(int)*ntohl(destcnt)))
	{
	  perror("orbput data pkt failed");
	}

      if (verbose)
	fprintf(stderr,"data packet read (from %d @ %.1f\n",nUUID,now());

      free(pktbuf);

      ackpkt.version=htonl(PKTVERSION);
      ackpkt.type=htonl(4);
      ackpkt.id=header.id;
      if (write(neighfd,&ackpkt,sizeof(ackpkt))<sizeof(ackpkt))
	{

	  perror("sending ack pkt for data");
	  close(neighfd);
	  neighfd=-1;
	}
      break;

    case 8: /* ctl packet */
      if (read(neighfd,&pktsize,sizeof(pktsize))<sizeof(pktsize))
	{
	  perror("read ctl pkt header");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}

      pktsize=ntohl(pktsize);
      pktbuf=malloc(pktsize);
      if (read(neighfd,pktbuf,pktsize)<pktsize)
	{
	  perror("read ctl pkt data");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}

      if (orbput(orbfd_out,"/pf/VORBrouter",now(),pktbuf,pktsize))
	{
	  perror("orbput ctl pkt failed");
	}

      if (verbose)
	fprintf(stderr,"ctl packet read (from %d @ %.1f)\n",nUUID,now());

      free(pktbuf);

      ackpkt.version=htonl(PKTVERSION);
      ackpkt.type=htonl(4);
      ackpkt.id=header.id;
      if (write(neighfd,&ackpkt,sizeof(ackpkt))<sizeof(ackpkt))
	{
	  perror("sending ack pkt for ctl");
	  close(neighfd);
	  neighfd=-1;
	  break;
	}
      break;

    default:
      fprintf(stderr,"Unknown packet type dude\n");
      exit(-1);
    }

  if (neighfd>=0)
    {
      sprintf(buf,"echo %s:%d > connection/%d",Neighip,port,nUUID);
      system(buf);
    }

  return(retval);
}

int barf(int orbfd_ctl)
{
  int pktid;
  char srcname[ORBSRCNAME_SIZE+1];
  double pkttime;
  int nbytes, nbytes2;
  static char *pkt=NULL, *pkt2=NULL;
  static int bufsize=0, bufsize2=0;
  static Packet *unstuffd=NULL;
  int pktUUID;
  double pktcreationtime;
  static Arr *ctlarr=NULL;
  char *ch, *ch2, *ch3;
  struct ctlpkt ctlheader;
  int ret;
  struct ack ackpkt;

  if (ctlarr == NULL)
    {
      ctlarr=newarr(0);
    }

  if ((ret=orbreap_nd(orbfd_ctl,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize))==ORB_INCOMPLETE)
    return 0;
  else if (ret<0)
    {
      perror("orbreap");
      exit(-1);
    }

  switch (unstuffPkt(srcname,pkttime,pkt,nbytes,&unstuffd))
    {
    case Pkt_pf:
      if (pfget_int(unstuffd->pf,"Version")==PKTVERSION)
	{
	  if (pfget_int(unstuffd->pf,"Type")==9)
	    {
	      if (pfget_int(unstuffd->pf,"UUID")==UUID)
		{
		  if (ctlpf==NULL || pfget_double(unstuffd->pf,"Creation")>pfget_double(ctlpf,"Creation"))
		    {
		      if (ctlpf==NULL || pfget_int(unstuffd->pf,"ChangeNumber")!=pfget_int(ctlpf,"ChangeNumber"))
			{
			  pffree(ctlpf);
			  ctlpf=NULL;
			  pfcompile(pf2string(unstuffd->pf),&ctlpf);
			  
			  if (verbose)
			    {
			      fprintf(stderr,"new route table loaded %d\n",time(NULL));
			    }
			}
		    }
		}
	    }
	}

      if (pfget_int(unstuffd->pf,"lastUUID")!=nUUID)
	{
	  pktUUID=pfget_int(unstuffd->pf,"UUID");
	  pktcreationtime=pfget_double(unstuffd->pf,"Creation");
	  if (pktcreationtime<=time(NULL)+20*60)
	    {
	      ch=malloc(20);
	      ch2=malloc(50);
	      sprintf(ch,"%d",pktUUID);
	      sprintf(ch2,"%lf",pktcreationtime);
	      if ((ch3=getarr(ctlarr,ch))==NULL || atof(ch3) < pktcreationtime)
		{
		  free(ch3);
		  setarr(ctlarr,ch,ch2);
		  pfput_int(unstuffd->pf,"lastUUID",UUID);
		  ch=pf2string(unstuffd->pf);

		  stuffPkt(unstuffd,srcname,&pkttime,&pkt2,&nbytes2,&bufsize2);
		  ctlheader.version=htonl(PKTVERSION);
		  ctlheader.type=htonl(8);
		  ctlheader.id=htonl(pktid);
		  ctlheader.dsize=htonl(nbytes);
		  if (write(neighfd,&ctlheader,sizeof(ctlheader))<sizeof(ctlheader))
		    {
		      perror("write(ctlheader to neigh)");
		      close(neighfd);
		      neighfd=-1;
		    }

		  if (write(neighfd,pkt,nbytes)<nbytes)
		    {
		      perror("write(ctlpkt to neigh)");
		      close(neighfd);
		      neighfd=-1;
		    }

		  /* wait for ack */
		  while(!grabneigh(pktid) && neighfd>=0)
		    /* nop */ ;

		  if (neighfd<0)
		    {
		      fprintf(stderr,"ctl packet unacked!\n");
		    }
		  else if (verbose)
		    fprintf(stderr,"ctl packet sent & acked (to %d @ %.1f)\n",nUUID,now());
		}
	      else
		{
		  free(ch);
		  free(ch2);
		}
	    }
	  else
	    fprintf(stderr,"ctl packet creation time greater than 20 min in future, ignoring\n");
	}
      break;
    default:
      fprintf(stderr,"a non-pf packet in control stream, bailing\n");
      exit(-1);
    }  

  return 1;
}

int listen_forremote(int PORT)
{
  struct sockaddr_in serv_addr;
  int sockfd;
  int val;

  if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
      perror("VORBrouter: can't open stream socket");
      exit(-1);
    }

  val=1;
  if (setsockopt(sockfd,SOL_SOCKET,SO_REUSEADDR,&val,sizeof(int))<0)
    {
      perror("setsockopt(SO_REUSEADDR)");
      exit(-1);
    }
  
  bzero((char *) &serv_addr, sizeof(serv_addr));
  serv_addr.sin_family      = AF_INET;
  serv_addr.sin_addr.s_addr  = htonl(INADDR_ANY);
  serv_addr.sin_port        = htons(PORT);
  
  if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
    {
      perror("VORBrouter: can't bind local address");
      exit(-1);
    }
  
  if (listen(sockfd, 0))
    {
      perror("listen");
      exit(-1);
    }

  if (sockfd<0)
    {
      fprintf(stderr,"failed opening server for listening\n");
      exit(-1);
    }

  return(sockfd);
}

int connect_toremote(char *ip, int PORT)
{
  unsigned long lna;
  struct sockaddr_in addr;
  int sockfd;
  int val;
  struct hostent *host_ent;

  if (verbose)
    fprintf(stderr,"attempting to connect!\n");

  if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
      perror("VORBrouter: can't open stream socket");
      exit(-1);
    }

  bzero((char *) &addr, sizeof(addr));
  addr.sin_family      = AF_INET;
  addr.sin_addr.s_addr  = htonl(INADDR_ANY);
  addr.sin_port        = htons(PORT);

  if (-1 != (lna=inet_addr(ip)))
    memcpy(&addr.sin_addr, &lna, 
           min(sizeof(addr.sin_addr), sizeof(lna)));
  else 
    {
      host_ent = gethostbyname(ip);
      if (host_ent == NULL)
        {
	  perror("gethostbyname");
          fprintf(stderr,"can't resolve %s\n",ip);
          exit(-1);
        }
      memcpy(&addr.sin_addr, host_ent->h_addr, 
             min(host_ent->h_length, sizeof(addr.sin_addr)));
    }

  if (connect(sockfd,(struct sockaddr *)&addr,sizeof(addr)))
    {
      perror("connect neighbor");
      return -1;
    }

  val=1;
  if (setsockopt(sockfd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
    {
      perror("setsockopt(SO_KEEPALIVE)");
      exit(-1);
    }

  return(sockfd);
}

int findandroute(int orbfd_main) /* route normal packets */
{
  int lcv;
  int ret;
  int nexthop;
  int numhops_orig;
  int *nexthop2;
  char buf[80];
  Tbl *dest;
  static Pf *routes=NULL;
  void *val=NULL;
  static char *pkt=NULL;
  static int bufsize;
  int nbytes;
  double pkttime;
  char srcname[ORBSRCNAME_SIZE];
  int pktid;  
  int fd;

  if ((ret=orbreap_nd(orbfd_main,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize))==ORB_INCOMPLETE)
    return 0;
  else if (ret<0)
    {
      perror("orbreap");
      exit(-1);
    }

  if (ntohl(((struct datapkt *)pkt)->version)!=PKTVERSION)
    {
      elog_complain(ELOG_COMPLAIN,"mismatched packet version in VORB packet retrieved from orb. ignoring packet (it will not be routed)%d\n",ntohl(((struct datapkt *)pkt)->version));
      return 0;
    }

  if (pfget(ctlpf,"routes",(void **)&routes)!=PFARR)
    {
      perror("bogus pf format");
      exit(-1);
    }

  numhops_orig=ntohl(((struct datapkt *)pkt)->destcnt);
  dest=newtbl(0);
  if (verbose && numhops_orig)
    fprintf(stderr,"dests=%d\n",numhops_orig);
  for (lcv=0;lcv < numhops_orig;lcv++)
    {
      ret=ntohl(*(int*)(pkt+sizeof(struct datapkt)+lcv*sizeof(int)));
      if (ret != UUID)
	{
	  fprintf(stderr,"dst=%d\n",ret);
	  sprintf(buf,"%d",ret);
	  if (pfget(routes,buf,&val)==PFINVALID)
	    {
	      denied_packet(pktid,ret);
	    }
	  else
	    {
	      nexthop=pfget_int(routes,buf);
	      if (nexthop==nUUID)
		{
		  nexthop2=malloc(sizeof(int));
		  *nexthop2=htonl(nexthop);
		  pushtbl(dest,nexthop2);
		}
	    }
	}
    }

  if (maxtbl(dest)==0)
    return(0);
    
  ((struct datapkt *)pkt)->destcnt=htonl(maxtbl(dest));

  if (write(neighfd,pkt,sizeof(struct datapkt))<sizeof(struct datapkt))
    {
      perror("write data pkt header");
      close(neighfd);
      neighfd=-1;
      orbseek(orbfd_main,ORBPREV);
      freetbl(dest,free);
      return(0);
    }

  while(nexthop2=poptbl(dest))
    {
      if (write(neighfd,nexthop2,sizeof(int))<sizeof(int))
	{
	  perror("write data pkt header");
	  close(neighfd);
	  neighfd=-1;
	  orbseek(orbfd_main,ORBPREV);
	  free(nexthop2);
	  return(0);
	}
      free(nexthop2);
    }

  freetbl(dest,free);

  if (write(neighfd,pkt+sizeof(struct datapkt)+sizeof(int)*numhops_orig,ntohl(((struct datapkt *)pkt)->dsize))<ntohl(((struct datapkt *)pkt)->dsize))
    {
      perror("write data pkt header");
      close(neighfd);
      neighfd=-1;
      orbseek(orbfd_main,ORBPREV);
      return(0);
    }

  /* wait for ack */
  while(!grabneigh(ntohl(((struct datapkt *)pkt)->id)) && neighfd>=0)
    /* nop */ ;
  
  if (neighfd<0)
    {
      fprintf(stderr,"data packet unacked!");
    }
  else if (verbose)
    fprintf(stderr,"data packet sent & acked (to %d @ %.1f), %d dests\n",nUUID,now(),((struct datapkt *)pkt)->destcnt);
}

void denied_packet(int pktid, int destUUID)
{
  /* write pktid to pffile and dest ids for pkt */
  fprintf(stderr,"no route for packet %d to %d, discarding because I am dumb.\n",pktid,destUUID);
}
