/***********************************************************
*File Name: FletcherEncode.c
*Description: 
*			 This is Fletcher's checksum which is a variant 
*			 of the 1's complement checksum that is tuned to 
*			 trap bit error patterns similar to those trapped 
*			 by a CRC.  Port 0 will encode the frame and Port
*			 1 will decode the frame to check 
*			  
************************************************************/
#include <stdio.h>
#include "FletcherEncode.h"

extern verbose;

/***********************************************
*Function 
 name: FletcerEncode
*Description: 
* FlecterEncode is an algorithm that encodes the data
* before the data is sent.   
*
* passing parameters: 
*	unsigned char *buffer -> the frame
*	long count -> number of bytes in the frame
************************************************/

long FletcherDecode(unsigned char *buffer, long count )
{
	long result = 0;
	int i;
	unsigned char c0 = 0;
	unsigned char c1 = 0;
	unsigned char temp = 0;
	
	for( i = 0; i < count-2; i++)
	{
		if(i==29)
		{
		    c1 = c0 + *(buffer+i);
			c0 = c0 + *(buffer+i);
		}
		else
		{
			c0 = c0 + *( buffer + i );	
			c1 = c1 + c0;		
		}	
	}

	if (verbose)
	  fprintf(stderr," fletcher result =>  %d\n" , c0 + c1 );
	return( (long)(c0+c1) );
}

/***********************************************
*Function name: FletcerDecode
*Description: 
* Flecterdecode is an algorithm that decodes the data
* after the data has been received	   
*
* passing parameters: 
*	unsigned char *buffer -> the frame
*	long count -> number of bytes in the frame
***********************************************/
void FletcherEncode(unsigned char *buffer, long count )
{
	int i;
	
	unsigned char c0 = 0;
	unsigned char c1 = 0;
    
	/* stored in byte #29 and #30 */
    *( buffer + count - 3 ) = 0;
    *( buffer + count - 4 ) = 0;


	for( i = 0; i < count - 4 ; i++)
	{
		c0 = c0 + *( buffer + i );
		c1 = c1 + c0;
	}	

	*( buffer + count - 4 ) = c0 - c1;
	*( buffer + count - 3 ) = c1 - 2*c0;


	printf(" the buffer is -> %x " , *(buffer+28));
	printf(" the buffer is -> %x " , *(buffer+29));
    
}
