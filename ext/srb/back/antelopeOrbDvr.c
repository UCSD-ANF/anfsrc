/*
 * orbDvr.c - Routines to handle Unix type orb storage
 */

/****/
#define ANTELOPEDEBUGON 1
/****/
#include "antelopeOrbMDriver.h" 

#ifdef ANTELOPEDEBUGON 
#define ANTELOPE_DEBUG( ... ) fprintf( stdout, __VA_ARGS__ ); fflush( stdout );
#else
#define ANTELOPE_DEBUG( ... ) 
#endif


int
orbstat2str(Orbstat *orbstat, char *outBuf)
{
    /* returns length of buffer */
    if (orbstat == NULL)
	return(0);
    sprintf(outBuf,
	    "%f|%f|%f|%d|%d|%u|%d|%d|%d|%d|%d|%s|%d|%d|%d|%d|%d|%s|%s|%s",
	    orbstat->when,orbstat->started,orbstat->orb_start,
	    orbstat->connections,orbstat->messages,orbstat->maxdata,
	    orbstat->errors,orbstat->rejected,orbstat->closes,
	    orbstat->opens,orbstat->port,orbstat->address,
	    orbstat->pid,orbstat->nsources,orbstat->nclients,
	    orbstat->maxsrc,orbstat->maxpkts,
	    orbstat->version,orbstat->who,orbstat->host);
    return(strlen(outBuf));
}

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


  ANTELOPE_DEBUG("antelopeOrbOpen: Start orbopen: orbDataDesc=%s.\n",orbDataDesc);
  orb = orbopen(orbDataDesc, orbInMode);
  if (orb < 0) {
    fprintf(stdout, "antelopeOrbOpen: orbopen error. orbDataDesc=%s. errorCode=%d",
	    orbDataDesc, orb);fflush(stdout);
    freeOrbStateInfo(orbSI);
    return(MD_CONNECT_ERROR);
  }
  if (orbSI->select != NULL) {
    ANTELOPE_DEBUG("antelopeOrbOpen: Start  orbselect =%s.\n",orbSI->select);
    if ((i = orbselect ( orb, orbSI->select )) < 0 ) {
      fprintf(stdout, "antelopeOrbOpen: orbselect error. %s %i",orbSI->select,i);
      freeOrbStateInfo(orbSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }

  if (orbSI->reject != NULL) {
    ANTELOPE_DEBUG("antelopeOrbOpen: Start  orbreject =%s.\n",orbSI->reject);
    if ((i = orbreject ( orb, orbSI->reject )) < 0 ) {
      fprintf(stdout, "antelopeOrbOpen: orbreject error. %s %i",orbSI->reject,i);
      freeOrbStateInfo(orbSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }
  if (orbSI->after != NULL) {
    ANTELOPE_DEBUG("antelopeOrbOpen: Start  orbafter =%s.\n",orbSI->after);
    if ((i = orbafter ( orb, strtod(orbSI->after,NULL) )) < 0 ) {
      fprintf(stdout, "antelopeOrbOpen: orbafter error. %s %i",i,orbSI->after);
      fflush(stdout); freeOrbStateInfo(orbSI);
      return(MD_SET_ERROR);
    }
  }
  if (orbSI->position != NULL) {
    ANTELOPE_DEBUG("antelopeOrbOpen: Start  orbposition =%s.\n",orbSI->position);
    if ((i = orbposition ( orb, orbSI->position )) < 0 ) {
      fprintf(stdout,"antelopeOrbOpen: orbposition error. %s %i",i,orbSI->position);
      freeOrbStateInfo(orbSI);fflush(stdout);
      return(MD_SET_ERROR);
    }
  }
  orbSI->fd = orb;

  orbSI->reapMemRemSize = 0;
  orbSI->reapMemBegPtr = NULL;
  orbSI->firstRead = 1;
  mdDesc->driverSpecificInfo = (char *) orbSI;
  ANTELOPE_DEBUG("antelopeOrbOpen: Finish.\n");

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
    fprintf(stdout,"antelopeOrbRead: reaped one packet:pktid=%i,status=%i\n",
	    pktid,status); fflush(stdout);
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
  char *argv[MAX_PROC_ARGS_FOR_ANT_ORB];
  int  outBufStrLen;
  int          i ,ii,j,k,l,p,q,r,s, numArgs;
  orbStateInfo   *orbSI;
  int orb, orbfd,  orb1,orb2;
  char            srcname[ORBSRCNAME_SIZE] ;
  char *tmpPtr;
  char *outBufPtr;
  double dtime;
  Orbstat *orbstatPtr;
  Orbsrc *orbsourcePtr;
  Orbclient *orbclientPtr;
  Packet *pktPtr;

  orbSI = (orbStateInfo *) mdDesc->driverSpecificInfo;
  orb = orbSI->fd;
  outBufStrLen =  0;
  outBuf[0] = '\0';
  outBufPtr = outBuf;


  ANTELOPE_DEBUG("antelopeOrbProc: Begin Proc inLen=%i,outLen=%i \n",inLen,outLen);
  ANTELOPE_DEBUG("antelopeOrbProc: procName=$$%s$$\n",procName);
  ANTELOPE_DEBUG("antelopeOrbProc: inBuf=$$%.80s$$\n",inBuf);
  if (isalnum(procName[0]) == 0)
      i = getArgsFromString(procName +1 ,argv,procName[0],'\\');
  else
      i = getArgsFromString(procName,argv,'|','\\');
  ANTELOPE_DEBUG("antelopeOrbProc: i=%i, actualprocName=$$%s$$\n",i,procName);
  if(i == 0 )
      return(FUNCTION_NOT_SUPPORTED);
  if (i < 0)
      return(i);
  numArgs = i;
  i = 0;

  if (!strcmp(argv[0],"orbopen")) {
      /* argv[1] = orbhost
	 argv[2] = perm */
      /* return value is the orb connection descriptor (int) */
      i = orbopen(argv[1],argv[2]);
      return(i);
  }
  else if (!strcmp(argv[0],"orbclose")) {
      /* argv[1] = orbfd (int) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
	  orb = orbfd;
      i = orbclose(orb);
      return(i);
  }
  else if (!strcmp(argv[0],"orbput")) {
      /* argv[1] = orbfd (int)
	 argv[2] = srcname
	 argv[3] = pkttime (double)
	 inBuf = pkt
	 inLen = nbytes  */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
	  orb = orbfd;
      dtime = atof(argv[3]);
      i = orbput(orb, argv[2], dtime, inBuf, inLen);
      return(i);
      
  }
  else if (!strcmp(argv[0],"orbget") ||
           !strcmp(argv[0],"orbreap") ||
           !strcmp(argv[0],"orbreap_nd") ||
           !strcmp(argv[0],"orbreap_timeout") ||
           !strcmp(argv[0],"orbgetstash") ||
           !strcmp(argv[0],"orbget_unstuffed") ||
           !strcmp(argv[0],"orbreap_unstuffed") ||
           !strcmp(argv[0],"orbreap_nd_unstuffed") ||
           !strcmp(argv[0],"orbreap_timeout_unstuffed") ||
           !strcmp(argv[0],"orbgetstash_unstuffed")) {
      /* argv[1] = orbfd (int)
	 argv[2] = whichpkt (int) for orbget
                   maxseconds (int) for orb_timeout*/
      /* outBuf  = rv|pid|pt|n|b|sn|pkt 
	 where rv = function return value  (int)
	       pid = pktid (int)   set to -1 for orbgetstash  
	       pt  = pkttime (double)
	       n   = nbytes (int)
	       b   = bufSize 
	       sn = source name padded with blanks
	       pkt = packet  if there is overflow 
	             call antelopeOrbProc with"orbgetmore" */
      /* return value = function return value if negative 
	 otherwise length of used outBuf */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      if (!strcmp(argv[0],"orbget") || !strcmp(argv[0],"orbreap_timeout") ||
	  !strcmp(argv[0],"orbget_unstuffed") || 
	  !strcmp(argv[0],"orbreap_timeout_unstuffed") )
	  k = atoi(argv[2]);
      ii = 4 + 19 + 20 + 20 + ORBSRCNAME_SIZE + 1 ; /* 128 */
      for (i =  0 ; i < ii ; i++)
	  outBuf[i] = ' ';
      outBuf[i-1] = '|';
      outBuf[i] = '\0';
      outBufPtr +=  ii;
      j = outLen - ii;
      q = outLen -  ii;
      if (!strcmp(argv[0],"orbget") || !strcmp(argv[0],"orbget_unstuffed"))
	  i = orbget ( orb, k, &p, srcname, &dtime, &outBufPtr, &j, &q);
      else if (!strcmp(argv[0],"orbreap")|| !strcmp(argv[0],"orbreap_unstuffed"))
          i = orbreap ( orb,  &p, srcname, &dtime, &outBufPtr, &j, &q);
      else if (!strcmp(argv[0],"orbreap_nd") || !strcmp(argv[0],"orbreap_nd_unstuffed"))
          i = orbreap_nd ( orb,  &p, srcname, &dtime, &outBufPtr, &j, &q);
      else if (!strcmp(argv[0],"orbreap_timeout") || !strcmp(argv[0],"orbreap_timeout_unstuffed") )
          i = orbreap_timeout ( orb, k, &p, srcname, &dtime, &outBufPtr, &j, &q);
      else if (!strcmp(argv[0],"orbgetstash") || !strcmp(argv[0],"orbgetstash_unstuffed")) {
	  p = -1;
	  i = orbgetstash(orb,srcname, &dtime, &outBufPtr, &j, &q);
      }
	  
      if (i == -1)
	  return(i);
      sprintf(outBuf,"%i|%i|%d|%i|%i|%s",i,p,dtime,j,q,srcname);
      if (strstr(argv[0],"_unstuffed") == NULL) {
	  if (outBufPtr != outBuf + ii) {
	      memcpy((void *)(outBuf + ii), outBufPtr, outLen - ii);
	      orbSI->reapMemBegPtr = outBufPtr;
	      orbSI->reapMemCurPtr = outBufPtr + outLen - ii;
	      orbSI->reapMemRemSize = q - outLen - ii;
	      return(outLen);
	  }
	  else {
	      return(j + ii);
	  }
      }
      else {
	  r = unstuffPkt(srcname, dtime, outBufPtr, j, &pktPtr );
	  if (outBufPtr != outBuf + ii) 
	      free(outBufPtr);
	  switch (r) {
	      case Pkt_db:
		  i = db2xml(pktPtr->db,  0, 0, 0, 0, (void **) &tmpPtr, 0 );
		  if (i < 0) 
		      return(i);
		  q = strlen(tmpPtr);
		  if ( q < (outLen - ii)) {
		      strcpy((char *) (outBuf + ii), tmpPtr);
		      free (tmpPtr);
		      return(q + ii);
		  }
		  else {
		      memcpy((void *)(outBuf + ii),tmpPtr, outLen - ii);
		      orbSI->reapMemBegPtr = tmpPtr;
		      orbSI->reapMemCurPtr = tmpPtr + outLen - ii;
		      orbSI->reapMemRemSize = q - outLen - ii;
		      return(outLen);
		  }
		  break;
	      case Pkt_pf:
		  tmpPtr = pf2xml(pktPtr->pf, 0,0,0);
		  if (tmpPtr == NULL)
		      return(-10);
		  q = strlen(tmpPtr);
                  if ( q < (outLen - ii)) {
                      strcpy((char *) (outBuf + ii), tmpPtr);
                      free (tmpPtr);
                      return(q + ii);
                  }
                  else {
                      memcpy((void *)(outBuf + ii),tmpPtr, outLen - ii);
                      orbSI->reapMemBegPtr = tmpPtr;
                      orbSI->reapMemCurPtr = tmpPtr + outLen - ii;
                      orbSI->reapMemRemSize = q - outLen - ii;
                      return(outLen);
                  }
		  break;
	      default:
		  return (FUNCTION_NOT_SUPPORTED);
		  break;
	  }

      }
      
  }
  else if (!strcmp(argv[0],"orbgetmore")) {
      /* outBuf contains the remaining packet if overflow call again*/
      if (orbSI->reapMemBegPtr == NULL || orbSI->reapMemRemSize == 0)
	  return(0);
      if (outLen < orbSI->reapMemRemSize) {
	  memcpy(outBuf, orbSI->reapMemCurPtr, outLen);
	  orbSI->reapMemCurPtr += outLen;
	  orbSI->reapMemRemSize -= outLen;
	  return(outLen);
      }
      else {
	  memcpy(outBuf, orbSI->reapMemCurPtr,orbSI->reapMemRemSize);
	  free(orbSI->reapMemBegPtr);
	  orbSI->reapMemRemSize = 0;
	  orbSI->reapMemBegPtr = NULL;
	  return(orbSI->reapMemRemSize);
      }
  }
  else if (!strcmp(argv[0],"orbseek")) {
      /* argv[1] = orbfd (int)
         argv[2] = whichpkt (int) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      j = atoi(argv[2]);
      i = orbseek(orb,j);
      return(i);
  }
  else if (!strcmp(argv[0],"orbtell")) {
      /* argv[1] = orbfd (int) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      i = orbtell(orb);
      return(i);
  }
  else if (!strcmp(argv[0],"orbposition")) {
      /* argv[1] = orbfd (int)
         argv[2] = orbwhere */
      /* return value = function return value */
      orbfd = atoi(argv[1]); 
      if (orbfd != -1 )
	  orb = orbfd;
      i = orbposition(orb,argv[2]);
      return(i);
  }
  else if (!strcmp(argv[0],"orbafter")) {
      /* argv[1] = orbfd (int)
         argv[2] = atime  (double) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      dtime = atof(argv[2]);
      i = orbafter(orb,dtime);
      return(i);
  }
  else if (!strcmp(argv[0],"orbselect")) {
      /* argv[1] = orbfd (int)
         argv[2] = regex */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      i = orbselect(orb,argv[2]);
      return(i);
  }
  else if (!strcmp(argv[0],"orbreject")) {
      /* argv[1] = orbfd (int)
         argv[2] = regex */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      i = orbreject(orb,argv[2]);
      return(i);
  }
  else if (!strcmp(argv[0],"orbping")) {
      /* argv[1] = orbfd (int) */
      /* return value = function return value if less than zero
              otherwise return the orbversion*/
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      i = orbping (orb, &j);
      if (i < 0)
	  return(i);
      return(j);
  }
  else if (!strcmp(argv[0],"orbset_logging")) {
      /* argv[1] = orbfd (int)
         argv[2] = level (int) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      j =  atoi(argv[2]);
      i = orbset_logging(orb,j);
      return(i);
  }
  else if (!strcmp(argv[0],"orbstashselect")) {
      /* argv[1] = orbfd (int)
         argv[2] = stashflag (int) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      j =  atoi(argv[2]);
      i = orbset_logging(orb,j);
      return(i);
  }
  else if (!strcmp(argv[0],"orbstat")) {
      /* argv[1] = orbfd (int) */
      /* return value = function return value */
      orbfd = atoi(argv[1]);
      if (orbfd != -1 )
          orb = orbfd;
      i = orbstat(orb, &orbstatPtr);
      if (i < 0)
	  return(i);
      i = orbstat2str(orbstatPtr, outBuf);
      return(i);
  }
  else if (!strcmp(argv[0],"orbsources")) {
      return(FUNCTION_NOT_SUPPORTED);
  }
  else if (!strcmp(argv[0],"orbclients")) {
      return(FUNCTION_NOT_SUPPORTED);
  }
  else {
      return(FUNCTION_NOT_SUPPORTED);
  }
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
