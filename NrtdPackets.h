/* ICE-9 version of packet definitions, here for reference only */

#ifndef NRTDPACKETS_H
#define NRTDPACKETS_H

#define NRTD_DATA_PACKET	1
#define NRTD_STATUS_PACKET	2

#define NETWORK_NAME_LEN	2
#define STATION_NAME_LEN	5
#define CHANNEL_NAME_LEN	3
#define LOCATION_CODE_LEN	2
#define CHANNEL_ID_LEN		(CHANNEL_NAME_LEN + LOCATION_CODE_LEN + 1)	/* extra 1 for byte alignment */

#define NRTD_DATA_PACKET_SIZE(packet)	\
	(sizeof(packet) + \
	 packet.num_chan * CHANNEL_ID_LEN + \
	 packet.num_chan * packet.num_samp * sizeof(short))

#pragma pack(1)
typedef struct
{
	short int msgID;					/* NRTD_DATA_PACKET */
	short int msgSize;					/* NRTD_DATA_PACKET_SIZE */
	long seq_num;						/* packet sequence number */
	double timestamp;					/* timestamp in unix format */
	double samp_rate;					/* number of samples per second */
	char net_name[NETWORK_NAME_LEN];	/* network name */
	char sta_name[STATION_NAME_LEN];	/* station name */
	char pad;							/* padding for alignment on solaris */
	short int num_chan;					/* number of channels in the data */
	short int num_samp;					/* number of samples */
	unsigned short int chksum;			/* 30 bytes to here */
/*	char chan_id[num_chan][CHANNEL_ID_LEN];	*/
/*	short int sample[num_samp][num_chan];	*/
} NrtdDataPacket_t;

typedef struct
{
  short int msgID;		/* NRTD_STATUS_PACKET */
  short int msgSize;	/* 8 */
  long int seq_num;		/* next data packet sequence number */
} NrtdStatusPacket_t;

#pragma pack()


#endif
