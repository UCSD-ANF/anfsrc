/*
   a C++ socket server class 

   Keith Vertanen 11/98 
*/

#define BUFFSIZE 64000

#ifdef WIN32
#include <windows.h>
#include <winsock.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#else
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/wait.h>
// For linux
#include <unistd.h>
#include <arpa/inet.h>
#endif

#include <iostream>
using namespace std;
class Server
{
  // class attibutes
  public:	
	int port;	// the port I'm listening on
	int dataport;	// the port I'm listening for datagrams on
	int REVERSE;    // should be reverse the incoming/outgoing
			// byte order, 0 is normal, 1 is reversed
	
  protected:		
	int sockfd;	               // listen on sock_fd
	int datasockfd;	               // listen on datagram socket
	int senddatasockfd;	       // datagram send socket
	int new_fd;	               // new connection on new_fd
	struct sockaddr_in my_addr;    // my address information
        struct sockaddr_in their_addr; // connector's address information
        struct sockaddr_in dest_addr;  // used for datagram sending, not
				       // sure why we can't use their_addr, oh well
	int sin_size;
	double buffer[BUFFSIZE];	// reuse the same memory for buffer
	double buffer2[BUFFSIZE];

  // class methods
  public:
	Server(int, int);			// constructor with port #
	void connect();			// accept a new connection
	void closeSocket();		// close the socket

	void send_string(char *str);		// send a string to socket
	void send_bytes(char *vals, int len);	        // send some bytes
	void send_ints(int *vals, int len);	        // send some integers
	void send_floats(float *vals, int len);		// send some floats
	void send_doubles(double *vals, int len);	// send some doubles
	void send_datagram(char *vals, int len);	// send a datagram packet
	int recv_string(char *str, int max, char term); // recv a string
//	int recv_string(char *str, int max); // recv a string
	int recv_bytes(char *vals, int max);  		// recv bytes
	int recv_ints(int *vals, int max);  		// recv ints
	int recv_floats(float *vals, int max);  	// recv floats
	int recv_doubles(double *vals, int max);  	// recv doubles
	int recv_datagram(char *vals, int max);  	// recv datagram
	void recv_ack();
	void send_ack();

};



