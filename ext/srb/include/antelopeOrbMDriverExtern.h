 



#ifndef ANT_ORB_MDRIVER_EXTERN_H
#define ANT_ORB_MDRIVER_EXTERN_H

#ifdef ANT_ORB_MD

#define MAX_PROC_ARGS_FOR_ANT_ORB 100

/*
extern int antelopeOrbOpen(MDriverDesc *mdDesc, mdasGetInfoOut *dataInfo,
                   char *orbDataDesc,
                   int orbFlags, int orbMode, char *userName);
extern int antelopeOrbCreate(MDriverDesc *mdDesc, mdasResInfo *rsrcInfo,
                     char *orbDataDesc,
                     int orbMode, char *userName);
*/
extern int antelopeOrbOpen(MDriverDesc *mdDesc, char *dataInfo, 
		   char *orbDataDesc, 
		   int orbFlags, int orbMode, char *userName);
extern int antelopeOrbCreate(MDriverDesc *mdDesc, char *rsrcInfo, 
		     char *orbDataDesc, 
		     int orbMode, char *userName);
extern int antelopeOrbClose(MDriverDesc *mdDesc);
extern int antelopeOrbRead(MDriverDesc *mdDesc, char *buffer, int length);
extern int antelopeOrbWrite(MDriverDesc *mdDesc, char *buffer, int length);
extern srb_long_t antelopeOrbSeek(MDriverDesc *mdDesc, srb_long_t offset, int whence);
extern int antelopeOrbUnlink(char *rsrcAddress, char *orbDataDesc);
extern int antelopeOrbSync(MDriverDesc *mdDesc);
extern int antelopeOrbProc(MDriverDesc *mdDesc, char *procName, 
              char *inBuf, int inLen,
              char *outBuf, int outLen );


#endif /* ANT_ORB_MD */
 
#endif  /* ANT_ORB_MDRIVER_EXTERN_H */
