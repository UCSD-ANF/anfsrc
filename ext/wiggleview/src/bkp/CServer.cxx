/* 
   a C++ socket server class

   Keith Vertanen 11/98   
*/

#include "CServer.hxx"

#define BACKLOG 10      // how many pending connections queue will hold 
#define VERBOSE 1       // turn on or off debugging output

Server::Server(int p, int datap)
{
	port = p;
	dataport = datap;

#ifdef WIN32
	WSADATA info;
	if (WSAStartup(MAKEWORD(1,1), &info) != 0)
		cout<<" Cannot initialize Winsock"<<endl;
#endif
	
        if (VERBOSE) printf("Server: opening socket on port = %d, datagrams on port = %d\n", 
				port, dataport);

        if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
            perror("socket");
            exit(1);
        }

        if ((datasockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
            perror("datagram socket");
            exit(1);
        }

        if ((senddatasockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
            perror("datagram send socket");
            exit(1);
        }

        my_addr.sin_family = AF_INET;         /* host byte order */
        my_addr.sin_port = htons(port);       /* short, network byte order */
        my_addr.sin_addr.s_addr = INADDR_ANY; /* auto-fill with my IP */
#ifdef WIN32
		memset(&(my_addr.sin_zero), 0, sizeof(struct sockaddr_in));
#else
        bzero(&(my_addr.sin_zero), 8);        /* zero the rest of the struct */
#endif

        if (bind(sockfd, (struct sockaddr *)&my_addr, sizeof(struct
		sockaddr)) == -1) {
            exit(1);
        }

	my_addr.sin_port = htons(dataport);
        if (bind(datasockfd, (struct sockaddr *)&my_addr, sizeof(struct
		sockaddr)) == -1) {
            exit(1);
        }

        if (listen(sockfd, BACKLOG) == -1) {
            exit(1);
        }
};

// wait for somebody to connect to us on our port
void Server::connect()
{
	struct hostent *he;
	char hostname[80];
	int len;

        sin_size = sizeof(struct sockaddr_in);
#ifdef WIN32
	if ((new_fd = accept(sockfd, (struct sockaddr *)&their_addr,
                  &sin_size)) == -1) {
           perror("accept");
        }
#else
        if ((new_fd = accept(sockfd, (struct sockaddr *)&their_addr,
                  (socklen_t*)&sin_size)) == -1) {
           perror("accept");
        }
#endif
        if (VERBOSE) 
		printf("Server: got connection from %s\n",
                    	inet_ntoa(their_addr.sin_addr));

	// the dest_addr is used by the send_datagram method
	// their_addr seems about the same, but it doesn't work
	// and when I put this in, it started working, hmmmm
	
	dest_addr.sin_family = AF_INET;
	dest_addr.sin_port = htons(dataport);
	dest_addr.sin_addr = their_addr.sin_addr;
#ifdef WIN32
	memset(&(my_addr.sin_zero), 0, 8);
#else
	bzero(&(dest_addr.sin_zero), 8);
#endif

	// the client sends us an int to indicate if we should
        // be reversing byte order on this connection
	
	// the client is sending 0 or 1, so a reversed 0 still looks
	// like a 0, no worries mate!

	char temp[1];
	int total = 0;

	while (total<1)
	   total += recv(new_fd, temp, 1, 0);	
	
	int val = temp[0];
	
	if (val==0) REVERSE = 0;	
		else REVERSE = 1;

	if (VERBOSE) 
		if (val==0)
		{
			printf("Client requested normal byte order.\n");
		}
		else
		{
			printf("Client requested reversed byte order.\n");
		}
};

// send a string to the socket
void Server::send_string(char *str)
{
        if (send(new_fd, (char *) str, strlen(str), 0) == -1)
            perror("send");              

	if (VERBOSE) printf("Server: sending string '%s'\n", str);                       

	recv_ack();
	send_ack();
};

// send some bytes over the wire
void Server::send_bytes(char *val, int len)
{
	int i;

        if (send(new_fd, (char *) val, len, 0) == -1)
            		perror("send bytes");              

	if (VERBOSE)
	{ 
		printf("Server: sending %d bytes - ", len);                       
		for (i=0; i<len; i++)
			printf("%d ", val[i]);
		printf("\n");
	}

	// don't continue until we receive an ack from client

	recv_ack();
	send_ack();
};

// send some integers over the wire
void Server::send_ints(int *val, int len)
{
	int *buff;
	char *ptr, *valptr;
	int i,j;

	// we may need to reverse the byte order, oh joy

	if (REVERSE)
	{
		// set the buff pointer to our previously allocated spot
		buff = (int *) buffer;

		ptr = (char *) buff;
		valptr = (char *) val;

		// we need to reverse the order of each set of bytes
		for (i = 0; i < len; i++)
		{
			for (j=0; j<sizeof(int); j++)
				ptr[i*sizeof(int)+j] = (char)
					valptr[(i+1)*sizeof(int)-j-1];
		}
        	if (send(new_fd, (char *) buff, sizeof(int)*len, 0) == -1)
            		perror("send ints");              		
	}
	else
        	if (send(new_fd, (char *) val, sizeof(int)*len, 0) == -1)
            		perror("send ints");              

	if (VERBOSE)
	{ 
		printf("Server: sending %d ints - ", len);                       
		for (i=0; i<len; i++)
			printf("%d ", val[i]);
		printf("\n");
	}

	// don't continue until we receive an ack from client

	recv_ack();
	send_ack();
};

// send some floats over the wire
void Server::send_floats(float *val, int len)
{
	float *buff;
	char *ptr, *valptr;
	int i,j;

	// we may need to reverse the byte order, oh joy

	if (REVERSE)
	{
		buff = (float *) buffer;

		ptr = (char *) buff;
		valptr = (char *) val;

		// we need to reverse the order of each set of bytes
		for (i = 0; i < len; i++)
		{
			for (j=0; j<sizeof(float); j++)
				ptr[i*sizeof(float)+j] = (char)
					valptr[(i+1)*sizeof(float)-j-1];
		}
        	if (send(new_fd, (char *) buff, sizeof(float)*len, 0) == -1)
            		perror("send floats");              		
	}
	else
        	if (send(new_fd, (char *) val, sizeof(float)*len, 0) == -1)
            		perror("send floats");              

	if (VERBOSE)
	{ 
		printf("Server: sending %d floats - ", len);                       
		for (i=0; i<len; i++)
			printf("%0.3f ", val[i]);
		printf("\n");
	}

	recv_ack();
	send_ack();
};

// send some doubles over the wire
void Server::send_doubles(double *val, int len)
{
	double *buff;
	char *ptr, *valptr;
	int i,j;

	// we may need to reverse the byte order, oh joy

	if (REVERSE)
	{
		// allocate a temporary array to hold the reversed bytes
		buff = (double *) buffer;

		ptr = (char *) buff;
		valptr = (char *) val;

		// we need to reverse the order of each set of bytes
		for (i = 0; i < len; i++)
		{
			for (j=0; j<sizeof(double); j++)
				ptr[i*sizeof(double)+j] = (char)
					valptr[(i+1)*sizeof(double)-j-1];
		}
        	if (send(new_fd, (char *) buff, sizeof(double)*len, 0) == -1)
            		perror("send doubles");              		
	}
	else
        	if (send(new_fd, (char *) val, sizeof(double)*len, 0) == -1)
            		perror("send doubles");              

	if (VERBOSE)
	{ 
		printf("Server: sending %d doubles - ", len);                       
		for (i=0; i<len; i++)
			printf("%0.3f ", val[i]);
		printf("\n");
	}

	recv_ack();
	send_ack();
};

// send a packet of bytes using a datagram
void Server::send_datagram(char *val, int len)
{
	int i, numbytes;

        if ((numbytes=sendto(senddatasockfd, val, len, 0, 
		(struct sockaddr *) &dest_addr, sizeof(struct sockaddr)))== -1)
            		perror("send datagram bytes");              

	if (VERBOSE)
	{ 
		printf("Server: sending datagram of %d bytes - ", len);
		for (i=0; i<len; i++)
			printf("%d ", val[i]);
		printf("\n");
	}

};

// receive a string, returns num of bytes received
int Server::recv_string(char *str, int maxlen, char terminal)
//int Server::recv_string(char *str, int maxlen)
{
	int numbytes = 0;
	int end = 0;
	int i, j;
	char *temp;

	// set the temp buffer to our already allocated spot
	temp = (char *) buffer;

	j = 0;

	// this is annoying, but the java end is sending a char
	// at a time, so we recv some chars (probably 1), append
	// it to our str string, then carry on until we see
	// the terminal character
	while (!end)
	{
		if ((numbytes=recv(new_fd, temp, BUFFSIZE, 0))==-1)
			perror("recv");
		for (i=0; i<numbytes; i++)
		{
			str[j] = temp[i];	
			j++;
			cout<<j<<endl;
		}
		//if ((temp[i-1]==terminal) || (j==maxlen-1))
		if ((temp[i-1]==terminal) || (j==maxlen))
			end = 1;
	}


	str[j] = '\0';

	if (VERBOSE) printf("Server: received '%s'\n", str);                       	

	send_ack();
	recv_ack();
	
	return numbytes;
};

// receive some ints, returns num of ints received
int Server::recv_bytes(char *val, int maxlen)
{
	int numbytes = 0;
	int i, j;
	char *temp;
	int end = 0;
	int total_bytes = 0;

	temp = (char *) buffer;

	j = 0;

	// we receiving the incoming ints one byte at a time
	// oh cross language sockets are so much fun...

	while (!end)
	{
		if ((numbytes=recv(new_fd, temp, BUFFSIZE, 0))==-1)
			perror("recv");

		for (i=0; i<numbytes; i++)
		{
			val[j] = temp[i];	
			j++;
		}

		total_bytes = total_bytes + numbytes;
		if (total_bytes==maxlen)
			end = 1;

	}

	if (VERBOSE) 
	{
		printf("Server: received %d bytes - ", maxlen);             	
		for (i=0; i<maxlen; i++)
			printf("%d ", val[i]);
		printf("\n");
	}

	send_ack();
	recv_ack();

	return maxlen;
};

// receive some ints, returns num of ints received
int Server::recv_ints(int *val, int maxlen)
{
	int numbytes = 0;
	int i, j;
	char *temp;
        char *result;
	int end = 0;
	int total_bytes = 0;

	temp = (char *) buffer;
	result = (char *) buffer2;

	j = 0;

	// we receiving the incoming ints one byte at a time
	// oh cross language sockets are so much fun...

	while (!end)
	{
		if ((numbytes=recv(new_fd, temp, BUFFSIZE, 0))==-1)
			perror("recv");
		for (i=0; i<numbytes; i++)
		{
			result[j] = temp[i];	
			j++;
		}

		total_bytes = total_bytes + numbytes;
		if (total_bytes==maxlen*sizeof(int))
			end = 1;

	}

	// now we need to put the array of bytes into the array of ints

	char *ptr;
	int num = j/sizeof(int);

	ptr = (char *) val;

	// the significance order depends on the platform

	if (REVERSE)
	{
		// we need to reverse the order of each set of bytes
		for (i = 0; i < num; i++)
		{
			for (j=0; j<sizeof(int); j++)
				ptr[i*sizeof(int)+j] = (char)
					result[(i+1)*sizeof(int)-j-1];
		}
	}
	else
	{
		// leave the byte order as is
		for (i = 0; i < j; i++)
		{
			ptr[i] = result[i];
		}
	}

	if (VERBOSE) 
	{
		printf("Server: received %d ints - ", num);             	
		for (i=0; i<num; i++)
			printf("%d ", val[i]);
		printf("\n");
	}

	send_ack();
	recv_ack();

	return num;
};

// receive some floats, returns num of floats received
int Server::recv_floats(float *val, int maxlen)
{
	int numbytes = 0;
	int i, j;
	char *temp;
        char *result;
	int end = 0;
	int total_bytes = 0;

	temp = (char *) buffer;
	result = (char *) buffer2;

	j = 0;

	// we receiving the incoming ints one byte at a time
	// oh cross language sockets are so much fun...

	while (!end)
	{
		if ((numbytes=recv(new_fd, temp, BUFFSIZE, 0))==-1)
			perror("recv");
		for (i=0; i<numbytes; i++)
		{
			result[j] = temp[i];	
			j++;
		}

		total_bytes = total_bytes + numbytes;
		if (total_bytes==maxlen*sizeof(float))
			end = 1;

	}

	// now we need to put the array of bytes into the array of floats

	char *ptr;
	int num = j/sizeof(float);

	ptr = (char *) val;

	// the significance order depends on the platform

	if (REVERSE)
	{
		// we need to reverse the order of each set of bytes
		for (i = 0; i < num; i++)
		{
			for (j=0; j<sizeof(float); j++)
				ptr[i*sizeof(float)+j] = (char)
					result[(i+1)*sizeof(float)-j-1];
		}
	}
	else
	{
		// leave the byte order as is
		for (i = 0; i < j; i++)
		{
			ptr[i] = result[i];
		}
	}

	if (VERBOSE) 
	{
		printf("Server: received %d floats - ", num);             	
		for (i=0; i<num; i++)
			printf("%f ", val[i]);
		printf("\n");
	}

	send_ack();
	recv_ack();

	return num;

};

// receive some doubles, returns num of doubles received
int Server::recv_doubles(double *val, int maxlen)
{
	int numbytes = 0;
	int i, j;
	char *temp;
        char *result;
	int end = 0;
	int total_bytes = 0;

	temp = (char *) buffer;
	result = (char *) buffer2;

	j = 0;

	// we receiving the incoming ints one byte at a time
	// oh cross language sockets are so much fun...

	while (!end)
	{
		if ((numbytes=recv(new_fd, temp, BUFFSIZE, 0))==-1)
			perror("recv");
		for (i=0; i<numbytes; i++)
		{
			result[j] = temp[i];	
			j++;
		}

		total_bytes = total_bytes + numbytes;
		if (total_bytes==maxlen*sizeof(double))
			end = 1;

	}

	// now we need to put the array of bytes into the array of floats

	char *ptr;
	int num = j/sizeof(double);

	ptr = (char *) val;

	// the significance order depends on the platform

	if (REVERSE)
	{
		// we need to reverse the order of each set of bytes
		for (i = 0; i < num; i++)
		{
			for (j=0; j<sizeof(double); j++)
				ptr[i*sizeof(double)+j] = (char)
					result[(i+1)*sizeof(double)-j-1];
		}
	}
	else
	{
		// leave the byte order as is
		for (i = 0; i < j; i++)
		{
			ptr[i] = result[i];
		}
	}

	if (VERBOSE) 
	{
		printf("Server: received %d doubles - ", num);             	
		for (i=0; i<num; i++)
			printf("%e ", val[i]);
		printf("\n");
	}

	send_ack();
	recv_ack();

	return num;
};

// receive a datagram
int Server::recv_datagram(char *val, int maxlen)
{
	int numbytes = 0;
	int addr_len, i;

	addr_len = sizeof(struct sockaddr);

#ifdef WIN32
	if ((numbytes=recvfrom(datasockfd, val, maxlen, 0,
		(struct sockaddr *) &their_addr, &addr_len)) == -1)
#else
	if ((numbytes=recvfrom(datasockfd, val, maxlen, 0,
		(struct sockaddr *) &their_addr, (socklen_t*)&addr_len)) == -1)
#endif
	{
		perror("recvfrom datagram");
	}

	if (VERBOSE) 
	{
		printf("Server: received datagram of %d bytes - ", numbytes);             	
		for (i=0; i<numbytes; i++)
			printf("%d ", val[i]);
		printf("\n");
	}

	return numbytes;
};

// shut down the socket
void Server::closeSocket()
{
#ifdef WIN32
	closesocket(new_fd);
#else
	close(new_fd);
#endif

};

// recv a short ack from the client 
void Server::recv_ack()
{
	char temp[1];
	int total = 0;

	if (VERBOSE)
		printf("Waiting for ack...\n");

	while (total<1)
	   total += recv(new_fd, temp, 1, 0);	

	if (VERBOSE)
		printf("Ack recieved.\n");

};

// send a short ack to the client 
void Server::send_ack()
{
	char temp[1];
	temp[0] = 42;

	if (VERBOSE)
		printf("Sending ack...\n");
      
	send(new_fd, temp, 1, 0);
};
