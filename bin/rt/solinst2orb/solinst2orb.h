#define min(a,b)  (a<b?a:b)

#define MAX_RETRY 3
#define MAX_SAMPLES_PKT 1
#define VS 100
#define SRC_NAME "HP_BSMT/MGENC"
#define UNSUCCESSFUL -9999

#define genericFtr "\003"
#define query128ByteDumpHdr "\001M80\002"
#define setDateTimeHdr "\001D11\002"
#define queryDateTime "\001D11\002\003"
#define setInstrHdr "\001N24\002"
#define queryInstr "\001N24\002\003"
#define setSerialInstrHdr "\001F24\002"
#define querySerialInstr "\001F24\002\003"
#define setLocCodeHdr "\001L14\002"
#define queryLocCode "\001L14\002\003"
#define setIdCodeCh1Hdr "\001I14\002"
#define queryIdCodeCh1 "\001I14\002\003"
#define setIdCodeCh2Hdr "\001i14\002"
#define queryIdCodeCh2 "\001i14\002\003"
#define setRefUnitCh1Hdr "\001R10\002"
#define queryRefUnitCh1 "\001R10\002\003"
#define setRefUnitCh2Hdr "\001r10\002"
#define queryRefUnitCh2 "\001r10\002\003"
#define setRangeUnitCh1Hdr "\001T10\002"
#define queryRangeUnitCh1 "\001T10\002\003"
#define setRangeUnitCh2Hdr "\001t10\002"
#define queryRangeUnitCh2 "\001t10\002\003"
#define setMasterUnitHdr "\001W10\002"
#define queryMasterUnit "\001W10\002\003"
#define setAltitudeUnitHdr "\001Q10\002"
#define queryAltitudeUnit "\001Q10\002\003"
#define queryCh1 "\001V10\002\003"
#define queryCh2 "\001v10\002\003"
#define setSampleRateHdr "\001S3\002"
#define querySampleRate "\001S3\002\003"
#define setSampleModeHdr "\001P4\002"
#define querySampleMode "\001P4\002\003"
#define setFutureStartTimeHdr "\001B11\002"
#define setDirectStartRegistration "\001B\002\003"
#define setDirectStartCalibration "\001K\002\003"
#define setDirectStopMeasurementRegistration "\001E\002\003"
#define queryOffsetUnit "\001O10\002\003"
#define setProductIdHdr "\001C14\002"
#define queryProductId "\001C14\002\003"
#define queryStatus "\001#14\002\003"
#define setFillCalibrationTblHdr "\001$2\002"
#define queryFillCallibrationTbl "\001$2\002\003"
#define queryCommErr "\001F\002\003"

struct dataFrame
{
  char buf[128];
};

/* command line */
void usage();

/* restart logging */
void resetLogger(int fd);

/* set and get */
int verifySetupGetData(int fd,int orbfd,char *srcname,int *lastMemPtr);

/* resume from bookmark */
int getLastIndex();

/* bookmark records read */
void saveLastIndex(int index);

/* determine log rate in 1/10 second precision */
double generateRate(struct dataFrame *rate,struct dataFrame *mode);

/* funky format to epoch */
double generateEpoch(char *str);

/* helper function for dump cmd */
int issueDumpCmd(int fd,int index,struct dataFrame *result);

/* initialize the dataFrame */
void initDataFrame(struct dataFrame *frame);

/* setup the connection the wavelan/EC-S serial port */
int initConnection(char *host, char *port);

/* accept incoming connections */
int acceptConnection();

/* send one-way cmd */
void set(int fd, char *cmd);

/* send cmd and retrieve data */
int query(int fd, char *query, struct dataFrame *result);

/* create checksum for cmd to send */
unsigned char createChecksum(char *buf,int bufSize);




