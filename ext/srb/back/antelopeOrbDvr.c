/*
 * orbDvr.c - Routines to handle Unix type orb storage
 */

/****/
#define ANTELOPEDEBUGON 1
/****/
#include "antelopeOrbMDriver.h" 

/* antelopeOrbOpen - Handles the open call.
 *
 * Input : MDriverDesc *mdDesc - The orb descriptor handle
 *         char *orbDataDesc - The orb path name to be opened
 *         int orbFlags - The open flag
 *         int orbMode - The orb mode
 *
 * Output : Returns the orb descriptor of the opened orb.
 */

/*
int
antelopeOrbOpen(MDriverDesc *mdDesc, mdasGetInfoOut *dataInfo, 
	 char *orbDataDesc, int orbFlags, int orbMode, char *userName)
*/
antelopeOrbOpen(MDriverDesc *mdDesc, char *rsrcInfo,
         char *orbDataDesc, int orbFlags, int orbMode, char *userName)
{

  orbStateInfo *orbSI;
  char orbInMode[4];
  char *tmpPtr;
  int i, orb;

  if((orbSI =  malloc(sizeof (orbStateInfo))) == NULL) {
    fprintf(stdout, "antelopeOrbOpen:  Malloc error");
    return MEMORY_ALLOCATION_ERROR;
  }
  if ((i = getOrbStateInfo( orbSI, rsrcInfo, orbDataDesc, orbFlags, 
			orbMode, userName)) <0 ) {
    fprintf(stdout, "antelopeOrbOpen:  getStateInfo error:%i",i);
    freeOrbStateInfo(orbSI);
    return i;
  }

  if (orbSI->orbMode == O_RDONLY)
    strcpy(orbInMode,"r&");
  else
    strcpy(orbInMode,"w&");
  strcpy(orbInMode,"r&");


#ifdef ANTELOPEDEBUGON
  fprintf(stdout,"antelopeOrbOpen: Start orbopen: orbDataDesc=%s.\n",orbDataDesc);
  fflush(stdout);
#endif /* ANTELOPEDEBUGON */
  orb = orbopen(orbDataDesc, orbInMode);
  if (orb < 0) {
    fprintf(stdout, "antelopeOrbOpen: orbopen error. orbDataDesc=%s. errorCode=%d",
	    orbDataDesc, orb);fflush(stdout);
    freeOrbStateInfo(orbSI);
    return(MD_CONNECT_ERROR);
  }
  if (orbSI->select != NULL) {
#ifdef ANTELOPEDEBUGON
  fprintf(stdout,"antelopeOrbOpen: Start  orbselect =%s.\n",orbSI->select);
  fflush(stdout);
#endif /* ANTELOPEDEBUGON */
    if ((i = orbselect ( orb, orbSI->select )) < 0 ) {
      fprintf(stdout, "antelopeOrbOpen: orbselect error. %s %i",orbSI->select,i);
      freeOrbStateInfo(orbSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }

  if (orbSI->reject != NULL) {
#ifdef ANTELOPEDEBUGON
  fprintf(stdout,"antelopeOrbOpen: Start  orbreject =%s.\n",orbSI->reject);
  fflush(stdout);
#endif /* ANTELOPEDEBUGON */
    if ((i = orbreject ( orb, orbSI->reject )) < 0 ) {
      fprintf(stdout, "antelopeOrbOpen: orbreject error. %s %i",orbSI->reject,i);
      freeOrbStateInfo(orbSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }
  if (orbSI->after != NULL) {
#ifdef ANTELOPEDEBUGON
  fprintf(stdout,"antelopeOrbOpen: Start  orbafter =%s.\n",orbSI->after);
  fflush(stdout);
#endif /* ANTELOPEDEBUGON */
    if ((i = orbafter ( orb, strtod(orbSI->after,NULL) )) < 0 ) {
      fprintf(stdout, "antelopeOrbOpen: orbafter error. %s %i",i,orbSI->after);
      fflush(stdout); freeOrbStateInfo(orbSI);
      return(MD_SET_ERROR);
    }
  }
  if (orbSI->position != NULL) {
#ifdef ANTELOPEDEBUGON
  fprintf(stdout,"antelopeOrbOpen: Start  orbposition =%s.\n",orbSI->position);
  fflush(stdout);
#endif /* ANTELOPEDEBUGON */
    if ((i = orbposition ( orb, orbSI->position )) < 0 ) {
      fprintf(stdout,"antelopeOrbOpen: orbposition error. %s %i",i,orbSI->position);
      freeOrbStateInfo(orbSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }
  orbSI->fd = orb;


  orbSI->firstRead = 1;
  mdDesc->driverSpecificInfo = (char *) orbSI;
#ifdef ANTELOPEDEBUGON
  fprintf(stdout,"antelopeOrbOpen: Finish.\n");
  fflush(stdout);
#endif /* ANTELOPEDEBUGON */

  return MDAS_SUCCESS;

}

/* antelopeOrbCreate - Handles the create call.
 *
 * Input :  MDriverDesc *mdDesc - The orb descriptor handle
 *         char *orbDataDesc - The orb path name to be opened
 *         int orbMode - The orb mode
 *
 * Output : Returns the orb descriptor of the new orb.
 */

/*
int
antelopeOrbCreate(MDriverDesc *mdDesc, mdasResInfo *rsrcInfo, char *orbDataDesc, int orbMode, , char *userName)
*/
int
antelopeOrbCreate(MDriverDesc *mdDesc, char *rsrcInfo, char *orbDataDesc, int orbMode, char *userName)
{
  int status;

  return(FUNCTION_NOT_SUPPORTED);

}

/* antelopeOrbClose - Handles the close call.
 *
 * Input : MDriverDesc *mdDesc - The orb descriptor to be closed
 *
 * Output : Return status of close
 */

int
antelopeOrbClose(MDriverDesc *mdDesc)
{
  int status;
  orbStateInfo *orbSI;
  
  orbSI = (orbStateInfo *) mdDesc->driverSpecificInfo;
  
  status = orbclose(orbSI->fd);
  freeOrbStateInfo(orbSI);
  if (status < 0) {
    fprintf(stdout, "antelopeOrbClose: orbclose error. errorCode = %d", status);
    return(MD_CLOSE_ERROR);
  } 
  return (MDAS_SUCCESS);
}

/* antelopeOrbRead - Handles the read call.
 *
 * Input : MDriverDesc *mdDesc - The orb descriptor to read
 *	   char *buffer - The input buffer
 *	   int amount - The amount to read
 *
 * Output : Returns to number of bytes read
 */

int
antelopeOrbRead(MDriverDesc *mdDesc, char *buffer, int length)
{
  int	status;
    int             orb ,i ;
    int             pktid ; 
    char            srcname[ORBSRCNAME_SIZE] ;
    double          vorbtime ;
    char           *vorbpacket=0 ; 
    int             nbytes = 0 ;
    int             bufsize=0 ;
    orbStateInfo   *orbSI;
    int first;
    char *mybuffer;
    int mylength;
    int mysize = 0;
    int packcount;
    orbSI = (orbStateInfo *) mdDesc->driverSpecificInfo;

    if (length < VORBPKTHEADER)
      return (MD_BUF_LENGTH_INSUFFICIENT);
    orb = orbSI->fd;
    mybuffer = buffer;
    mylength = length;
    mysize = 0;
  *buffer = '\0';
  first = orbSI->firstRead;
  packcount = orbSI->numbulkreads;
    if (orbSI->numofpkts == 0) {
      return(MD_READ_ERROR);
    }
    if (orbSI->firstRead) {
      i = getAntelopeWhich(orbSI->which);
      status = orbseek(orb, i);
      if (status < 0) {
        fprintf(stdout,"antelopeOrbRead: seek error for %i. errorCode = %d",i,status);
	return(MD_SEEK_ERROR);
      }
      orbSI->firstRead = 0;
    }

  while (packcount > 0) {

    if (orbSI->numofpkts == 0) {
      return(mysize);
    }
    else if (orbSI->numofpkts > 0)
      orbSI->numofpkts--;
    packcount--;
    vorbpacket = mybuffer+VORBPKTHEADER;
    bufsize = mylength - VORBPKTHEADER;
    if (bufsize < MIN_ORB_BUF_SIZE)
      return(mysize);
    
    if (orbSI->timeout >= 0)
      status = orbreap_timeout(orb, orbSI->timeout,
	    &pktid, srcname, &vorbtime, &vorbpacket, &nbytes, &bufsize ) ;
    else
      status = orbreap(orb,
	    &pktid, srcname, &vorbtime, &vorbpacket, &nbytes, &bufsize ) ;
    if (status < 0) {
      if (status == ORB_INCOMPLETE || status == ORB_EOF) {
	orbSI->numofpkts = 0;
	nbytes = 0;
	vorbpacket =srcname;
      }
      else {
	fprintf(stdout, "antelopeOrbRead: read error. errorCode= %d\n",status);
	return(MD_READ_ERROR);
      }
    }
    status =  orbSpres(first,orbSI,srcname,vorbtime,pktid,
		       nbytes,vorbpacket,mybuffer);
    if (status < 0) {
      fprintf(stdout, "antelopeOrbRead: presentation error. errorCode =%d\n",status);
      return(MD_READ_ERROR);
    }
    mylength = mylength - strlen(mybuffer);
    mysize =  mysize + strlen(mybuffer);
    mybuffer = mybuffer + strlen(mybuffer);
    first = 0;
  }
  return (mysize);
}

/* antelopeOrbWrite - Handles the write call.
 *
 * Input : MDriverDesc *mdDesc - The orb descriptor to write
 *         char *buffer - The output buffer
 *         int amount - The amount to write
 *
 * Output : Returns to number of bytes written
 */

int
antelopeOrbWrite(MDriverDesc *mdDesc, char *buffer, int length)
{
    int	status;
    return(FUNCTION_NOT_SUPPORTED);

}

/* antelopeOrbSeek - Handles the seek call.
 *
 * Input : MDriverDesc *mdDesc - The orb descriptor to seek
 *         int offset - The position of the next operation
 *         int whence - Same definition as in Orb.
 *              SEEK_SET - pointer is set to the value of the Offset parameter.
 *              SEEK_CUR - pointer is set to its current location plus the
 *                      value of the Offset parameter.
 *              SEEK_END - pointer is set to the size of the orb plus the
 *                      value of the Offset parameter.
 *
 * Output : Returns the status of seek
 */

srb_long_t
antelopeOrbSeek(MDriverDesc *mdDesc, srb_long_t offset, int whence)
{
    srb_long_t	status;
    srb_long_t seekPos;
    return(FUNCTION_NOT_SUPPORTED);

}

/* orbUnlink - Handles the unlink call.
 *
 * Input : char *orbDesc - The orb path name to unlink
 *
 * Output : Returns the status of unlink
 */

int
antelopeOrbUnlink(char *rsrcAddress, char *orbDataDesc)
{
    int status;
 
        return(FUNCTION_NOT_SUPPORTED);
}

int 
antelopeOrbProc(MDriverDesc *mdDesc, char *procName,
              char *inBuf, int inLen, 
              char *outBuf, int outLen )
{
  int status = 0;
  return(FUNCTION_NOT_SUPPORTED);
}


antelopeOrbSync(MDriverDesc *mdDesc)
{
    int status;
 
        return(FUNCTION_NOT_SUPPORTED);
}


/***** antelope ORB utilities ***/

int
getAntelopeWhich(char *orbDwhich)
{
  int i;
  if (orbDwhich != NULL) {
    if (!strcmp(orbDwhich,"ORBCURRENT"))
      i = ORBCURRENT;
    else if (!strcmp(orbDwhich,"ORBNEXT"))
      i = ORBNEXT;
    else if (!strcmp(orbDwhich,"ORBPREV"))
      i = ORBPREV;
    else if (!strcmp(orbDwhich,"ORBOLDEST"))
      i = ORBOLDEST;
    else if (!strcmp(orbDwhich,"ORBNEWEST"))
      i = ORBNEWEST;
    else if (!strcmp(orbDwhich,"ORBNEXT_WAIT"))
      i = ORBNEXT_WAIT;
    else if (!strcmp(orbDwhich,"ORBNEXTT"))
      i = ORBNEXTT;
    else if (!strcmp(orbDwhich,"ORBPREVT"))
      i = ORBPREVT;
    else 
      i = atoi(orbDwhich);
  }
  else 
    i  = ORBCURRENT;
  return(i);
}
