#ifndef _libuser_
#define _libuser_

#define EXPIMG100_DESCRIPTION_SIZE 64

typedef struct ExpImgPacket {

	/* Packet version is in Packet struct */
	/* "description" field is in Packet ->string element */

#if 0
	/* This should have been in the packet format. Putting it in the 
	   unstuff structure forces unfortunate dependencies, such as using
	   ImageMagick in the unstuff routines. Leave this out for now.
	*/
	char	format[LIBUSER_FORMAT_SIZE];  /* e.g. GIF, JPEG etc */
#endif
	char	*blob;			      /* binary block with image */
	int	blob_size;		      /* size of binary block */
	int	blob_bufsz;		      /* size of allocated buffer */

} ExpImgPacket;

#ifdef  __cplusplus
extern "C" {
#endif

extern ExpImgPacket *new_expimgpacket ( void );
extern void free_expimgpacket ( ExpImgPacket *eip );

#ifdef  __cplusplus
}
#endif

#endif
