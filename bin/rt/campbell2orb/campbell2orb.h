#define MAX_SAMPLES_PKT 1
#define VS  100
#define CXN_RETRY 1
#define DATA_RETRY 1
#define SUCCESSFUL 1
#define UNSUCCESSFUL -9999

/***
  CAMPBELL2ORB FUNCTIONS AND PROCEDURES
***/

#define min(a,b)        (a<b?a:b)

int readCampbell(char *wavelanAddress,int connect_flag,char *wavelanPort,int reset_flag,char *sourceName,int *orbfd,double *previousTimestamp,int *stepSize,int *lastMemPtr,int *channels);

void usage();

int initConnection(char *host,int connect_flag,char *port);

void setTime(int *fd);

void printProgram(int *fd);

void flushOut(int *fd);

int interrogate(int *fd,int *orbfd,char *sourceName,double *previousTimestamp,int *stepSize,int *lastMemPtr,int *channels);

int getAttention(int *fd);

int harvest(int *fd,int *orbfd,char *sourceName,double *previousTimestamp,int *stepSize,int *lastMemPtr,int *channel);

int setMemPtr(int *fd,int location);

int flushUntil(int *fd,char c);

int determineChannels(int *fd);

double constructPacket(int *fd,struct Packet *orbpkt,int *pktChannels,double previousTimestamp,char *currentMemPtr,int lastMemPtr,char
*sourceName,Tbl *tbl);

int dataIntegrityCheck(char *completeResponse);

int determineRecords(char *completeResponse,int channels);

char *tokenizer(char *s,char *d,int *position);

double generateTimestamp(char *sample);

void extractTimestamp(char *sample,char *timestamp);
