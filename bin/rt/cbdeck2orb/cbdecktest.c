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

#define min(a,b) (a<b?a:b)
#define NUM_CHANNELS 16
#define CHANNEL_SIZE 14
#define TIMESTAMP_SIZE 24
#define ORB "132.249.32.201"

/*
   This code was written at UCSD under the standard UCSD license. Look it up 
   if you copy this code this code was created as part of the ROADNet project.
   See http://roadnet.ucsd.edu/ 

   Written By: Steve Foley 6/16/2004
*/

main(int argc, char *argv[])
{
 int sockfd;
 struct sockaddr_in cli_addr, serv_addr;
 int PORT, bad_data_test;
 int lcv=0;
 in_addr_t lna;
 struct timeval timeout;
 int max_buffer=(NUM_CHANNELS*CHANNEL_SIZE)+TIMESTAMP_SIZE+1;
 char buffer[(NUM_CHANNELS*CHANNEL_SIZE)+TIMESTAMP_SIZE+1];
 int string_index=0;
 int i;
 float chan_val;
 int string_len;

 bad_data_test = 0;

 if (argc != 2) {
   fprintf(stderr, "usage: %s port [1 for bad_data]\n", argv[0]);
   exit(1);
 }

 PORT=atoi(argv[1]);
 if (argc == 3)
   {
     bad_data_test = 1;
   }

 printf("args: %s %s, port: %d, bad data: %d\n",argv[1], argv[2], PORT, bad_data_test);

 *((short int *)buffer)=htons(100);

 /* setup the socket */
 if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
   {
     perror("tcpcsvtest: can't open stream socket");
     exit(-1);
   }

 bzero((char *) &serv_addr, sizeof(serv_addr));
 serv_addr.sin_family      = AF_INET;
 serv_addr.sin_port        = htons(PORT);
 
 if (-1 != (lna=inet_addr(ORB)))
   memcpy(&(serv_addr.sin_addr), &lna, 
	  min(sizeof(serv_addr.sin_addr), sizeof(lna)));
 else
   {
     perror("host lookup failed");
     exit(-1);
   }

 if (connect(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr))<0)
   {
     perror("connect failed!");
     exit(-1);
   }

 /* Done setting up the socket, do work here */
 while(1)
   {
     memset(buffer, '\0', max_buffer);
     if (bad_data_test)
       {
	 strncpy(buffer, "<AUTHENTICATION>\n", 17);
	 string_index = 17;
       }
     else
       {
	 /* print out a time stamp */
	 strncpy(buffer, "2004-06-11 11:09:59.0099", TIMESTAMP_SIZE);
	 string_index = TIMESTAMP_SIZE;
	 
	 chan_val = 0.0001;
	 for (i=0;i < NUM_CHANNELS;i++)
	   {
	     /* Print out a not-so-random channel value */
	     sprintf(((char *)(buffer+string_index)),",%1.10f",chan_val);
	     string_index += CHANNEL_SIZE;
	     if (chan_val >= 0) string_index--; /* remove room for the neg */
	     chan_val += .0000001;
	   }
	 sprintf(((char *)(buffer+string_index)),"\r");
       }
     printf("sending data [%s]...",buffer);
     
     string_len = strlen(buffer);

     if (write(sockfd,buffer,string_len) != string_len)
       {
	 printf("write issued!\n");
       }

     /* sleep for a second */
     /* sleep(1);*/
   }
 
}


