#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <regex.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <syslog.h>
#include <fcntl.h>
#include <netdb.h>
#include <stdio.h>

#define min(a,b)  (a<b?a:b)
#define NUM_CLIENTS 10

/*
   This code was written at UCSD under the standard UCSD license. Look it up 
   if you copy this code this code was created as part of the ROADNet project.
   See http://roadnet.ucsd.edu/ 

   Written By: Todd Hansen 1/3/2003
*/

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

struct local_data
{
  double last_timestamps[NUM_CLIENTS];
  long last_seqnum[NUM_CLIENTS];
  int filedes[NUM_CLIENTS];
  char connected[NUM_CLIENTS];
  char used[NUM_CLIENTS];
  char waitcycle[NUM_CLIENTS];
  long ipaddr[NUM_CLIENTS];
} local_data;

unsigned short sumit(char *buf, int size, char *buf2, int size2);

void send_keepalive(int type);

main(int argc, char *argv[])
{
 int sockfd, newsockfd, clilen, childpid;
 struct sockaddr_in cli_addr, serv_addr;
 int fd, orbfd;
 time_t cur_time;
 int PORT;
 int con, c;
 in_addr_t lna;
 int val, lcv, lcv2, lcv3=0, high_fd;
 struct timeval timeout;
 char buffer[10002];
 fd_set read_fds, except_fds;

 for (lcv=0;lcv<NUM_CLIENTS;lcv++)
   local_data.connected[lcv]=local_data.ipaddr[lcv]=local_data.used[lcv]=0;

  strt.msgID = 2;
  strt.msgSize = 8;

 if (argc != 3) {
   fprintf(stderr, "usage: %s port sourcename\n", argv[0]);
   exit(1);
 }

 PORT=atoi(argv[1]);

 printf("source name: %s\nport: %d\n",argv[2],PORT);

 *((short int *)buffer)=htons(100);

 if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
   {
     perror("revelle_data: can't open stream socket");
     exit(-1);
   }

 bzero((char *) &serv_addr, sizeof(serv_addr));

 if (-1 != (lna=inet_addr("198.202.124.8")))
   memcpy(&(serv_addr.sin_addr), &lna, 
	  min(sizeof(serv_addr.sin_addr), sizeof(lna)));
 else
   {
     perror("host lookup failed");
     exit(-1);
   }

 serv_addr.sin_family      = AF_INET;
 serv_addr.sin_port        = htons(PORT);

 if (connect(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr))<0)
   {
     perror("connect failed!");
     exit(-1);
   }

 while(1)
   {
     FD_ZERO(&read_fds);
     FD_SET(sockfd,&read_fds);
     high_fd=sockfd+1;

     timeout.tv_sec=10;
     timeout.tv_usec=0;
     lcv=select(high_fd,&read_fds,0,0,&timeout);
     if (lcv<0)
       {
	 perror("select");
	 exit(-1);
       }
     else if (FD_ISSET(sockfd,&read_fds))
       {
	
	 if (read(sockfd,buffer,2)<=0)
	   {
	     perror("read");
	     exit(-1);
	   }
	
	 printf(" * %d\n",*((short int*)buffer));
       }
     else
       {
	 pkt.msgID=htons(1);
	 pkt.msgSize=htons(58);
	 pkt.seq_num=htonl(lcv3++);
	 pkt.timestamp=time(NULL);
	 pkt.num_chan=htons(2);
	 pkt.num_samp=htons(2);
	 pkt.samp_rate=1.0;
	 strncpy(pkt.sta_name,"PFO",5);
	 strncpy(pkt.net_name,"SM",2);
	 pkt.pad=0;

	 strncpy(buffer,"dus",3); /* channel */
	 strncpy(buffer+3,"N",2); /* location code */
	 *(buffer+4)=0; /* pad */
	 strncpy(buffer+6,"lon",3); /* channel */
	 strncpy(buffer+9,"S",2); /* location code */
	 *(buffer+11)=0; /* pad */
	 *((short int*)(buffer+12))=htons(1000);
	 *((short int*)(buffer+14))=htons(-1000);
	 *((short int*)(buffer+16))=htons(3);
	 *((short int*)(buffer+18))=htons(4);

	 /*pkt.chksum=htons(0);*/ /* use this to send invalid pkts */
	 pkt.chksum=htons(sumit((char*)&pkt,36,buffer,20));
	 printf("sent data checksum=%d, size of header=%d\n",ntohs(pkt.chksum),sizeof(pkt));


	 if (write(sockfd,&pkt,38)!=38)
	   {
	     printf("write issue!\n");
	   }
	 if (write(sockfd,buffer,20)!=20)
	   {
	     printf("write issue!2\n");
	   }
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




