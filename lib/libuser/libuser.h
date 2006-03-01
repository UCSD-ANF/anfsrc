#ifndef _libuser_
#define _libuser_

#define EXPIMG_DESCRIPTION_SIZE 64
#define EXPIMG_FORMAT_SIZE 25

typedef struct ExpImgPacket {

	char	format[EXPIMG_FORMAT_SIZE];  
	char	description[EXPIMG_DESCRIPTION_SIZE]; /* Image description */
	char	*blob;			      /* binary block with image */
	int	blob_size;		      /* size of binary block */
	int	blob_bufsz;		      /* size of allocated buffer */
	int	blob_offset;		      /* byte offset of this block in final image */
	int	ifragment;		      /* part number of this image fragment in image */
	int	nfragments;		      /* number of fragments (orb packets) for this image */

} ExpImgPacket;

#ifdef  __cplusplus
extern "C" {
#endif

extern ExpImgPacket *new_expimgpacket ( void );
extern ExpImgPacket *dup_expimgpacket ( ExpImgPacket *eip );
extern void free_expimgpacket ( ExpImgPacket *eip );

#ifdef  __cplusplus
}
#endif

#endif
