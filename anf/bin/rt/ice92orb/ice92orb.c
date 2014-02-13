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
#include "ice92orb.h"

/*
 Copyright (c) 2003 - 2006 The Regents of the University of California
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
   Last Updated By: Geoff Davis 1/04/2012
*/

#if defined (BIG_ENDIAN) || defined (_BIG_ENDIAN) || defined (__BIG_ENDIAN)
# ifndef _BIG_ENDIAN
#  define _BIG_ENDIAN
# endif
#endif

#if defined (LITTLE_ENDIAN) || defined (_LITTLE_ENDIAN) || defined(__LITTLE_ENDIAN)
# ifndef _LITTLE_ENDIAN
#  define _LITTLE_ENDIAN
# endif
#endif

#ifdef _LITTLE_ENDIAN

/* Convert NRTS network format double to host format.
 * This makes the very lazy assumption that the current host is using
 * IEEE 754 floating point (which coincidentally Intel, SPARC, and PPC
 * all do). Doubles coming off the wire are SPARC format */
double nrts_to_hd(double data) {
  char temp;

  union {
    char c[8];
  } dat;

  memcpy( &dat, &data, sizeof(double) );
  temp     = dat.c[0];
  dat.c[0] = dat.c[7];
  dat.c[7] = temp;

  temp     = dat.c[1];
  dat.c[1] = dat.c[6];
  dat.c[6] = temp;

  temp     = dat.c[2];
  dat.c[2] = dat.c[5];
  dat.c[5] = temp;

  temp     = dat.c[3];
  dat.c[3] = dat.c[4];
  dat.c[4] = temp;
  memcpy( &data, &dat, sizeof(double) );
  return(data);
}

int16_t readint16(int16_t data) {
  return ((data >> 8) & 0x0ff) | ((data & 0x00ff) << 8);
}

#else /* BIG_ENDIAN */
double nrts_to_hd(double nrts_double) {
  return(nrts_double);
}

int16_t readint16(int16_t data) {
  return data;
}
#endif

/*
 * Globals
 */

int Stop=0;
int verbose=0;
char ip_address[50];
char *ipptr;
static Pf *pf=NULL;

void usage(void) {
  cbanner(VERSION,
      "ice92orb [-V] [-v] [-p listenport] [-c configfile] [-S state/file] -o $ORB",
      "Todd Hansen and Geoff Davis",
      "UCSD ROADNet Project","anf-admins@ucsd.edu");
}

int main(int argc, char *argv[]) {
 int sockfd, newsockfd;
 socklen_t clilen;
 struct sockaddr_in cli_addr, serv_addr;
 int orbfd;
 int PORT=14028;
 int con;
 int val, lcv, high_fd;
 Relic relic;
 struct timeval timeout;
 char buffer[10002], *statefile=NULL, *orbname=NULL, *configfile=NULL, ch;
 fd_set read_fds, except_fds;
 short int msgSize =0; /* pkt.msgSize in host byte order */
 unsigned short int chksum; /* pkt.chksum in host byte order */

 elog_init(argc,argv);

 while ((ch = getopt(argc, argv, "Vvp:S:o:c:")) != -1) {
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
 }

 if (orbname == NULL) {
     elog_complain(0, "-o $ORB option required!\n\n");
     usage();
     exit(-1);
   }

 local_data.connected=local_data.ipaddr=local_data.used=0;

 strt.msgID = htons(NRTD_STATUS_PACKET);
 strt.msgSize = htons(NRTD_STATUS_PACKET_SIZE);

 elog_notify(0, "ice92orb started. port: %d orb: %s",PORT,orbname);
 if (statefile != NULL) {
   elog_notify(0, " statefile: %s",statefile);
 }
 if (configfile != NULL) {
   elog_notify(0, " configfile: %s",configfile);
 }

 *((short int *)buffer)=htons(100);

 if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
   elog_complain(1, "ice92orb: can't open stream socket");
   exit(-1);
 }

 bzero((char *) &serv_addr, sizeof(serv_addr));
 serv_addr.sin_family      = AF_INET;
 serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
 serv_addr.sin_port        = htons(PORT);

 if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr))
     < 0) {
   elog_complain(1, "ice92orb: can't bind local address");
   exit(-1);
 }

 listen(sockfd, 0);

 if ((orbfd=orbopen(orbname,"w&"))<0) {
   elog_complain(1, "orbopen failed");
   exit(-1);
 }

 if (statefile!=NULL) {
   exhume (statefile, &Stop, 0, &mort);
   relic.ip=(int *)&(local_data.last_seqnum);
   if (resurrect ("last_seqnum", relic, INT_RELIC) == 0 ) {
     elog_notify(0, "%s resurrected last sequence number=%d\n",
         VERSION, local_data.last_seqnum);
   }

   relic.dp=&(local_data.last_timestamp);
   if (resurrect ("last_timestamp", relic, DOUBLE_RELIC) == 0 ) {
     elog_notify(0, "%s resurrected last timestamp=%ld\n", VERSION,
         (long)local_data.last_timestamp);
   }

   relic.sp=&ipptr;
   ipptr=ip_address;
   if (resurrect ("ip_address", relic, STRING_RELIC) == 0) {
     char *s;
     s=strtime(time(NULL));
     elog_notify(0,"%s resurrection successful\n",VERSION);
     elog_notify(0,"initialization completed %s\n",s);
     free(s);
     local_data.used=1;
     local_data.ipaddr=(int)inet_addr(ipptr);
     free(ipptr);
     ipptr=ip_address;
   } else {
     char *s;
     s=strtime(time(NULL));
     local_data.ipaddr=0;
     elog_complain(0,"%s resurrection unsuccessful\n",VERSION);
     elog_notify(0,"initialization completed %s\n",s);
     free(s);
   }
 }

 con=0;

 while(1) {
   FD_ZERO(&except_fds);
   FD_SET(sockfd,&except_fds);
   FD_ZERO(&read_fds);
   FD_SET(sockfd,&read_fds);
   high_fd=sockfd+1;

   if (local_data.connected) {
     FD_SET(local_data.filedes,&read_fds);
     if (local_data.filedes>=high_fd) {
       high_fd=local_data.filedes+1;
     }
   }

   timeout.tv_sec=KEEPALIVE_TIMEOUT;
   timeout.tv_usec=0;

   if (Stop) {
     elog_notify(0, "program exiting before select\n");
     bury();
     exit(0);
   }

   lcv=select(high_fd,&read_fds,0,&except_fds,&timeout);

   if (Stop) {
     elog_notify(0, "program exiting after select\n");
     bury();
     exit(0);
   }

   if (lcv<0) {
     elog_complain(0, "select");
     if (statefile != NULL) {
       bury();
     }
     exit(-1);
   }
   else if (lcv==0) {
     send_keepalive(&local_data);
     if (statefile != NULL) {
       bury();
     }
   }
   else if (FD_ISSET(sockfd,&read_fds) || FD_ISSET(sockfd,&except_fds))
   {
     clilen = sizeof(cli_addr);
     newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr,
         &clilen);
     if (newsockfd < 0) {
       elog_complain(1,"accept error");
       exit(-1);
     }

     val=1;
     if (setsockopt(newsockfd, SOL_SOCKET, SO_KEEPALIVE, &val,
           sizeof(int))) {
       elog_complain(1,"setsockopt(SO_KEEPALIVE)");
       exit(-1);
     }

     con++;

     if (cli_addr.sin_addr.s_addr!=local_data.ipaddr || verbose) {

       if (local_data.ipaddr==0 ||
           cli_addr.sin_addr.s_addr==local_data.ipaddr) {
         elog_notify(0,"connection from %d %d.%d.%d.%d:%d\n",
             con,
             (ntohl(cli_addr.sin_addr.s_addr)>>24)&255,
             (ntohl(cli_addr.sin_addr.s_addr)>>16)&255,
             (ntohl(cli_addr.sin_addr.s_addr)>>8)&255,
             ntohl(cli_addr.sin_addr.s_addr)&255,
             ntohs(cli_addr.sin_port));
       } else
         elog_complain(1,
             "connection from %d %d.%d.%d.%d:%d when connection was previously from %d.%d.%d.%d (using same state for data retrieval)\n",
             con,
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

     if (local_data.used == 0) {
       local_data.used=1;
       local_data.ipaddr=cli_addr.sin_addr.s_addr;
       local_data.last_timestamp=0;
       local_data.last_seqnum=-2;
       local_data.connected=1;
       local_data.filedes=newsockfd;

       strt.seq_num=htonl(local_data.last_seqnum+1);

       write(newsockfd,&strt,ntohs(strt.msgSize));
     } else if (local_data.connected==1) {
       elog_complain(1,"already connected to a host! Disconnecting new connection.\n");
       close(newsockfd);
     } else {
       local_data.connected=1;
       local_data.filedes=newsockfd;
       local_data.ipaddr=cli_addr.sin_addr.s_addr;

       strt.seq_num=htonl(local_data.last_seqnum+1);

       write(newsockfd,&strt,ntohs(strt.msgSize));
     }
   } else {
     if (local_data.connected && FD_ISSET(local_data.filedes,
           &read_fds)) {
       if (read_reliable(local_data.filedes, (char*)&pkt,
             NRTD_DATA_HEADER_LEN) > 0)
       {
         msgSize = ntohs(pkt.msgSize);
         chksum  = ntohs(pkt.chksum);
         if (read_reliable(
               local_data.filedes, (char*)&buffer,
               msgSize - NRTD_DATA_HEADER_LEN
               ) > 0) {
           val=sumit((char*)&pkt,
               NRTD_DATA_HEADER_LEN - 2, /* skip checksum and pad */
               (char*)buffer,
               msgSize - NRTD_DATA_HEADER_LEN);

           if (val!=chksum) {
             elog_complain(1,
                 "checksum mismatch! Disconnecting client. (%d = client id, local=%d, received=%d)\n",
                 lcv, val, chksum);
             local_data.connected=0;
             close(local_data.filedes);
             if (statefile != NULL) {
               bury();
             }
           } else {
             local_data.last_timestamp=nrts_to_hd(pkt.timestamp);
             local_data.last_seqnum=ntohl(pkt.seq_num);

             traffic_data(&pkt, buffer,
                 msgSize - NRTD_DATA_HEADER_LEN,
                 orbfd, configfile);
           }
         } else {
           elog_complain(1, "client disconnected");
           close(local_data.filedes);
           local_data.connected=0;
           if (statefile != NULL) {
             bury();
           }
         }
       } else {
         close(local_data.filedes);
         local_data.connected=0;
         if (statefile != NULL) {
           bury();
         }
       }
     }
   }
 }

 orbclose(orbfd);
 return(0);
}

int traffic_data(struct PFOpkt_lnk *inpkt, char *buf, int bufsize,
    int orbfd, char *configfile) {
 struct Packet *orbpkt;
 struct PktChannel *pktchan;
 int lcv, lcv2;
 char srcname_full[116];
 double newtimestamp;
 static char *newpkt = NULL;
 int newpkt_size;
 static int newpkt_alloc_size=0;
 short int num_chan=0, num_samp=0;
 double timestamp=0.0;
 double samp_rate=0.0;
 int chandata_offset=0;

 num_chan=ntohs(inpkt->num_chan);
 num_samp=ntohs(inpkt->num_samp);
 timestamp=nrts_to_hd(inpkt->timestamp);
 samp_rate=nrts_to_hd(inpkt->samp_rate);


 orbpkt =  newPkt() ;
 orbpkt->pkttype = suffix2pkttype("MGENC");
 orbpkt->time=timestamp;
 orbpkt->nchannels=num_chan;
 strncpy(orbpkt->parts.src_net,inpkt->net_name,NETWORK_NAME_LEN);
 orbpkt->parts.src_net[NETWORK_NAME_LEN]='\0';
 strncpy(orbpkt->parts.src_sta,inpkt->sta_name,STATION_NAME_LEN);
 orbpkt->parts.src_sta[STATION_NAME_LEN]='\0';
 *(orbpkt->parts.src_chan)=0;
 *(orbpkt->parts.src_loc)=0;

 for (lcv=0; lcv < orbpkt->nchannels; lcv++) {

   pktchan = newPktChannel();
   pktchan->nsamp=num_samp;
   SIZE_BUFFER(int32_t *, pktchan->data, pktchan->datasz, pktchan->nsamp);

   chandata_offset = lcv*2 + num_chan*6;

   for (lcv2=0; lcv2 < pktchan->datasz; lcv2++) {
     ((int32_t *)pktchan->data)[lcv2] = readint16(
         *(int16_t*)(
           buf +
           chandata_offset +
           num_chan*lcv2*2 /* sizeof(uint16_t) */
         )
       );
   }

   pktchan->time=timestamp;

   strncpy(pktchan->net, inpkt->net_name, NETWORK_NAME_LEN);
   pktchan->net[NETWORK_NAME_LEN]='\0';

   strncpy(pktchan->sta, inpkt->sta_name, STATION_NAME_LEN);
   pktchan->sta[STATION_NAME_LEN]='\0';

   strncpy(pktchan->chan,
       buf + lcv * (STATION_NAME_LEN + 1),
       CHANNEL_NAME_LEN);
   pktchan->chan[CHANNEL_NAME_LEN]='\0';

   strncpy(pktchan->loc,
       buf + lcv * (STATION_NAME_LEN + 1) + (CHANNEL_NAME_LEN),
       LOCATION_CODE_LEN);
   pktchan->loc[LOCATION_CODE_LEN]='\0';

   pktchan->segtype[0]=get_segtype(configfile, pktchan->net, pktchan->sta,
       pktchan->chan);
   pktchan->segtype[1]='\0';
   /* strncpy(pktchan->segtype,"S",4); */

   pktchan->calib=get_calib(configfile, pktchan->net, pktchan->sta,
       pktchan->chan);
   pktchan->calper=-1;
   pktchan->samprate=samp_rate;
   pushtbl(orbpkt->channels,pktchan);
 }

 if (stuffPkt(orbpkt, srcname_full, &newtimestamp, &newpkt,
       &newpkt_size, &newpkt_alloc_size)<0) {
   elog_complain ( 1, "stuffPkt routine failed\n");
 }
 else if (orbput(orbfd, srcname_full, newtimestamp, newpkt,
       newpkt_size) < 0) {
   elog_complain ( 1, "orbput fails %s\n",srcname_full );
 }

 freePkt(orbpkt);

 if (verbose)
     showPkt(0, srcname_full, newtimestamp, newpkt, newpkt_size,
         stdout, PKT_UNSTUFF);
 return 0;
}

void send_keepalive(struct local_data_type *lc)
{
  if (lc->connected) {
    strt.seq_num=htonl(lc->last_seqnum+1);
    if (write(lc->filedes,&strt,ntohs(strt.msgSize))<0) {
      elog_complain(0, "lost connection. (keepalive send)");
      close(lc->filedes);
      lc->connected=0;
    }
  }
}



unsigned short sumit(char *buf, int size, char *buf2, int size2) {
  /* Original checksum was a byte-wise or in SPARC byte order */
  int lcv;
  unsigned short sum;

  sum=0;
  for (lcv=0;lcv<(size/2);lcv++) {
    sum^=ntohs(((unsigned short int *)buf)[lcv]);
  }

  for (lcv=0;lcv<(size2/2);lcv++) {
    sum^=ntohs(((unsigned short int *)buf2)[lcv]);
  }

  return(sum);
}

int read_reliable(int sock, char *buf, int size) {
  int lcv, val;

  lcv=0;
  while(lcv<size) {
    val=read(sock,buf+lcv,size-lcv);
    if (Stop) {
      elog_notify(1, "read_reliable: got Stop on read");
      bury();
      close(sock);
      exit(0);
    }
    if (val>0) {
      lcv+=val;
    }
    else
      return 0;
  }

  return 1;
}

void mort (Pf *pf) {
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
  char str[5000];
  static void *result=NULL;

  if (configfile) {
    lcv=pfupdate(configfile,&pf);
    if (lcv<0) {
      elog_complain(1, "error reading config file %s\n\n",
          configfile);
      exit(-1);
    }

    if (lcv>0) {
      elog_notify(0, "config file updated, rereading it.\n");
    }

    sprintf(str,"calib_%s_%s_%s",net,sta,chan);
    if (pfget(pf,str,&result)!=PFINVALID) {
      calib=pfget_double(pf,str);
      return(calib);
    }
    else {
      sprintf(str,"calib_%s_%s",net,sta);
      if (pfget(pf,str,&result)!=PFINVALID) {
        calib=pfget_double(pf,str);
        return(calib);
      }
      else {
        sprintf(str,"calib_%s",net);
        if (pfget(pf,str,&result)!=PFINVALID) {
          calib=pfget_double(pf,str);
          return(calib);
        }
        else {
          sprintf(str,"calib");
          if (pfget(pf,str,&result)!=PFINVALID) {
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

char get_segtype(char *configfile, char *net, char *sta, char *chan) {
  int lcv;
  char *s;
  char str[5000];

  if (configfile) {
    lcv=pfupdate(configfile,&pf);
    if (lcv<0) {
      elog_complain(1,"error reading config file %s\n\n",configfile);
      exit(-1);
    }

    if (lcv>0)
      elog_notify(0,"config file updated, rereading it.\n");

    sprintf(str,"segtype_%s_%s_%s",net,sta,chan);
    if ((s=pfget_string(pf,str))!=NULL) {
      return(s[0]);
    } else {
      sprintf(str,"segtype_%s_%s",net,sta);
      if ((s=pfget_string(pf,str))!=NULL) {
        return(s[0]);
      } else {
        sprintf(str,"segtype_%s",net);
        if ((s=pfget_string(pf,str))!=NULL) {
          return(s[0]);
        } else {
          sprintf(str,"segtype");
          if ((s=pfget_string(pf,str))!=NULL) {
            return(s[0]);
          }
          else
            return 'S';
        }
      }
    }
  } else
    return(0);
}
