/*
 Copyright (c) 2003 The Regents of the University of California
 All Rights Reserved

 Permission to use, copy, modify and distribute any part of this software for
 educational, research and non-profit purposes, without fee, and without a
 written agreement is hereby granted, provided that the above copyright
 notice, this paragraph and the following three paragraphs appear in all
 copies.

 Those desiring to incorporate this software into commercial products or use
 for commercial purposes should contact the Technology Transfer Office,
 University of California, San Diego, 9500 Gilman Drive, La Jolla, CA
 92093-0910, Ph: (858) 534-5815.

 IN NO EVENT SHALL THE UNIVESITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
 DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
 LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF THE UNIVERSITY
 OF CALIFORNIA HAS BEEN ADIVSED OF THE POSSIBILITY OF SUCH DAMAGE.

 THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
 CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
 ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF CALIFORNIA MAKES NO
 REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EITHER IMPLIED OR
 EXPRESS, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT THE USE OF THE
 SOFTWARE WILL NOT INFRINGE ANY PATENT, TRADEMARK OR OTHER RIGHTS.

   This code was created as part of the ROADNet project.
   See http://roadnet.ucsd.edu/

   Written By: Rock Yuen-Wong 6/2/2003
   Last Updated By: Todd Hansen 12/15/2003
*/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <time.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <strings.h>
#include <termios.h>
#include <time.h>
#include <orb.h>
#include <coords.h>
#include <stock.h>
#include <Pkt.h>
#include "campbell2orb.h"

int Stop=0;
static int debugPkts=0;
int version_limit=0;
int version_actual=0;
int version_required=-1;
int version_showerr=0;
int running_instance=0;
int printprog=0;

int main(int argc,char *argv[])
{
  int ch,
    connect_flag,
    reset_flag,
    err_flag,
    status,
    orbfd;

  /* never saved into statefile */
  char *version,
    *srcname,
    *address,
    *port,
    *statefile,
    *orb=":";

  Relic relic;

  /* retrieve these from statefile */
  double previousTimestamp;
  int stepSize,
    lastMemPtr,
    channels;

  srcname=NULL;
  address=NULL;
  port=NULL;
  statefile=NULL;

  ch=0;
  connect_flag=-1;
  reset_flag=0;
  err_flag=0;

  previousTimestamp=0;
  stepSize=60;
  lastMemPtr=1;
  channels=0;

  elog_init(argc,argv);
  elog_notify(0,"WARNING: this program is no longer maintained, please see csi2orb(1) for a newer implementation.\n\n");

  while((ch=getopt(argc,argv,"vpn:s:a:l:c:rS:O:di:"))!=-1)
    {
      switch(ch)
	{
	case 'v':
	  usage();
	  break;
	case 'n':
	  version=optarg;
	  if(atoi(version)==0)
	    {
	      usage();
	    }
	  else
	    {
	      version_limit=atoi(version);
	    }
	  break;
	case 's':
	  srcname=optarg;
	  break;
	case 'a':
	  address=optarg;
	  break;
	case 'l':
	  if(connect_flag==1)
	    {
	      usage();
	    }
	  connect_flag=0;
	  port=optarg;
	  break;
	case 'p':
	  printprog=1;
	  break;
	case 'c':
	  if(connect_flag==0)
	    {
	      usage();
	    }
	  connect_flag=1;
	  port=optarg;
	  break;
	case 'r':
	  reset_flag=1;
	  break;
	case 'i':
	  version_required=atoi(optarg);
	  break;
	case 'S':
	  statefile=optarg;
	  break;
	case 'O':
	  orb=optarg;
	  break;
	case 'd':
	  debugPkts=1;
	  break;
	default:
	  usage();
	}
    }

  /* no srcname */
  if(srcname==NULL)
    usage();
  /* no address to connect to */
  else if(connect_flag==1&&address==NULL)
    usage();
  /* no port to connect/listen */
  else if(port==NULL)
    usage();

  if(statefile==NULL)
    {
      statefile=strcat(strdup(srcname),".state");
    }

  if(statefile!=NULL)
    {
      exhume(statefile,NULL,0,0);

      relic.dp=&previousTimestamp;
      if(resurrect("previousTimestamp",relic,DOUBLE_RELIC)==0)
	{
	  fprintf(stderr,"resurrected previousTimestamp %f\n",previousTimestamp);
	}

      relic.ip=&stepSize;
      if(resurrect("stepSize",relic,INT_RELIC)==0)
	{
	  fprintf(stderr,"resurrected stepSize %d\n",stepSize);
	}

      relic.ip=&lastMemPtr;
      if(resurrect("lastMemPtr",relic,INT_RELIC)==0)
	{
	  fprintf(stderr,"resurrected lastMemPtr %d\n",lastMemPtr);
	}

      relic.ip=&channels;
      if(resurrect("channels",relic,INT_RELIC)==0)
	{
	  fprintf(stderr,"resurrected channels %d\n",channels);
	}
    }

  orbfd=orbopen(orb,"w&");

  while(1)
    {
      status=readCampbell(address,connect_flag,port,reset_flag,srcname,&orbfd,&previousTimestamp,&stepSize,&lastMemPtr,&channels);
      fprintf(stderr,"%s status %d\n",srcname,status);

      if(status==UNSUCCESSFUL)
	sleep(300);
      else
	sleep(status);

      running_instance++;
    }

  return 0;
}

void usage()
{
  printf("Usage: campbell2orb [-v] [-p] [-i prog_vs] [-n version] -s sourcename -a address -c connectport [-S statefile] [-O orb] [-d]\n");
  exit(0);
}

int readCampbell(char *wavelanAddress,int connect_flag,char *wavelanPort,int reset_flag,char *sourceName,int *orbfd,double *previousTimestamp,int *stepSize,int *lastMemPtr,int *channels)
{
  int fd,
    status;

  /* fprintf(stderr,"wavelanAddress %s wavelanPort %s sourceName %s\n",wavelanAddress,wavelanPort,sourceName); */

  if((fd=initConnection(wavelanAddress,connect_flag,wavelanPort))==UNSUCCESSFUL)
    {
      elog_complain(0,"readCampbell(%d) = Could not initiate connection\n",running_instance);
      return UNSUCCESSFUL;
    }

  /* fprintf(stderr,"after initConnection\n"); */

  if(reset_flag)
    setTime(&fd);

  if (printprog)
    printProgram(&fd);

  status=interrogate(&fd,orbfd,sourceName,previousTimestamp,stepSize,lastMemPtr,channels);

  /* fprintf(stderr,"after interrogate\n"); */

  close(fd);

  return status;
}

int initConnection(char *host,int connect_flag,char *port)
{
  int fd,
    cxnAttempts=0;
  unsigned long ina;
  int nconnected=1;
  struct hostent *host_ent;
  struct sockaddr_in addr;
  int val;

  /* fprintf(stderr,"in initConnection host ^%s^ port ^%s^\n",host,port); */

  while( nconnected)
    {
      
      if ( (ina=inet_addr(host)) != -1 )
	{
	  memcpy(&addr.sin_addr, &ina,min(sizeof(ina), sizeof(addr.sin_addr)));
	}
      else
	{
	  host_ent = gethostbyname(host);
	  
	  if ( host_ent == NULL )
	    {
	      elog_complain(0,"initConnection(%d) = Could not resolve address (host=%s)\n",running_instance,host);
	      return UNSUCCESSFUL;
	    }

	  memcpy(&addr.sin_addr, host_ent->h_addr,min(host_ent->h_length, sizeof(addr.sin_addr)));
	}

      /* make socket */
      if( (fd=socket(AF_INET, SOCK_STREAM, 0)) == -1 )
	{
	  elog_complain(0,"initConnection(%d) = Could not make socket\n",running_instance);
	  return UNSUCCESSFUL;
	}
      
      /* create address from host ent */
      addr.sin_family = AF_INET;
      addr.sin_port = htons(atoi(port));
      
      nconnected=connect(fd, (struct sockaddr *) &addr, sizeof(addr));
      
      if (nconnected)
	{
	  elog_complain(0,"initConnection(%d) = connect failed\n",running_instance);
	  close(fd);
	  sleep(30);
	  
	  if((cxnAttempts++)>=CXN_RETRY)
	    {
	      elog_complain(0,"initConnection(%d) = Could not connect after %d retries\n",running_instance,cxnAttempts);
	      return UNSUCCESSFUL;
	    }
	}
    }

  val=1;
  if (setsockopt(fd,SOL_SOCKET,SO_KEEPALIVE,&val,sizeof(int)))
    {
      perror("setsockopt(SO_KEEPALIVE)");
      exit(-1);
    }

  return fd;
}

void setTime(int *fd)
{
  char year[4],
    dayOfYear[4],
    hhmm[4],
    sec[2];
  time_t calptr;
  struct tm *brokenDownTime;

  time(&calptr);
  calptr+=24.0*60.0*60.0;
  brokenDownTime=gmtime(&calptr);

  sprintf(year,"%.4d",1900+brokenDownTime->tm_year);
  sprintf(dayOfYear,"%.4d",brokenDownTime->tm_yday);
  sprintf(hhmm,"%.2d%.2d",brokenDownTime->tm_hour,brokenDownTime->tm_min);
  sprintf(sec,"%.2d",brokenDownTime->tm_sec);
  getAttention(fd);
  /* fprintf(stderr,"%s %s %s %s\n",year,dayOfYear,hhmm,sec); */

  write(*fd,"7H\r",3);
  flushUntil(fd,'>');
  write(*fd,"*5",2);
  write(*fd,"A",1);
  write(*fd,year,4);
  write(*fd,"A",1);
  write(*fd,dayOfYear,4);
  write(*fd,"A",1);
  write(*fd,hhmm,4);
  write(*fd,"A",1);
  write(*fd,sec,2);
  write(*fd,"A",1);
  write(*fd,"*0",2);
  write(*fd,"E\r",2);
  flushOut(fd);
  close(*fd);

  fprintf(stderr,"time reset to UTC\n");

  exit(0);
}

void printProgram(int *fd)
{
  char program[10000];

  bzero(program,10000);
  getAttention(fd);
  write(*fd,"7H\r",3);
  flushUntil(fd,'>');
  write(*fd,"*D\r",3);
  sleep(3);
  write(*fd,"1A\r",3);
  sleep(5);
  read(*fd,program,10000);
  fprintf(stderr,"%s\n",program);
  write(*fd,"*0",2);
  write(*fd,"E\r",2);
  flushOut(fd);
  close(*fd);

  exit(0);
}

void flushOut(int *fd)
{
  char c;
  int val;

  val=fcntl(*fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  sleep(3);

  while(read(*fd,&c,1)!=-1)
    {
      /* fprintf(stderr,"%c\n",c); */
    }

  val&=~O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);
}

int interrogate(int *fd,int *orbfd,char *sourceName,double *previousTimestamp,int *stepSize,int *lastMemPtr,int *channels)
{
  int dataAttempts=0,
    status;

  while(dataAttempts++<=DATA_RETRY)
    {
      if(getAttention(fd)==UNSUCCESSFUL)
	{
	  elog_complain(0,"interrogate(%d) = Could not get attention\n",running_instance);
	  if (*fd<0)
	    return UNSUCCESSFUL;
	  continue;
	}

      if((status=harvest(fd,orbfd,sourceName,previousTimestamp,stepSize,lastMemPtr,channels))==UNSUCCESSFUL)
	{
	  if (*fd<0)
	    return UNSUCCESSFUL;

	  elog_complain(0,"interrogate(%d) = Could not harvest\n",running_instance);
	  continue;
	}

      if (write(*fd,"\r\r\r\rE\r",6)<6)
	{
	  perror("write(445)");
	  *fd=-1;
	  return (UNSUCCESSFUL);
	}

      flushOut(fd);
      return status;
    }

  elog_complain(0,"interrogate(%d) = Data retrieval failed after %d retries\n",running_instance,dataAttempts);
  write(*fd,"\r\r\r\rE\r",6);

  return UNSUCCESSFUL;
}

int getAttention(int *fd)
{
  int loop=0,
    val;
  int ret;
  char prompt[4];

  bzero(prompt,4);
  flushOut(fd);

  val=fcntl(*fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  while(loop++<10)
    {
      write(*fd,"\r",1);
      sleep(1);
      while ((ret=read(*fd,prompt,4))>0)
	{
	  if (ret<0)
	    {
	      perror("getAttention(read)");
	      close(*fd);
	      *fd=-1;
	      return(UNSUCCESSFUL);
	    }

	  /* fprintf(stderr,"%d %d %d %d\n",prompt[0],prompt[1],prompt[2],prompt[3]); */

	  if(prompt[0]=='*'||prompt[1]=='*'||prompt[2]=='*'||prompt[3]=='*')
	    {
	      val&=~O_NONBLOCK;
	      fcntl(*fd,F_SETFL,val);
	      /* fprintf(stderr,"got attention\n"); */
	      return SUCCESSFUL;
	    }
	}
    }

  val&=~O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  elog_complain(0,"getAttention(%d) = Could not get attention (prompt[0]=%c,prompt[1]=%c,prompt[2]=%c,prompt[3]=%c)\n",running_instance,prompt[0],prompt[1],prompt[2],prompt[3]);

  return UNSUCCESSFUL;
}

int harvest(int *fd,int *orbfd,char *sourceName,double *previousTimestamp,int *stepSize,int *lastMemPtr,int *channels)
{
  char currentMemPtr[10];
  char generatedSourceName[ORBSRCNAME_SIZE];

  int deadlock=0;

  double status,
    packetTimestamp=*previousTimestamp;

  struct Packet *orbpkt=newPkt();

  /* stuffPkt vars */
  int packetsz=0,
    nbytes;
  double t;
  char *packet;

  /* parameter file vars */
  Pf *pf;
  Tbl *tbl;

  if(setMemPtr(fd,*lastMemPtr)==UNSUCCESSFUL)
    {
      freePkt(orbpkt);
      elog_complain(0,"harvest(%d) = (1) Could not set memory pointer (lastMemPtr=%d)\n",running_instance,*lastMemPtr);
      return UNSUCCESSFUL;
    }

  /*if(*previousTimestamp==0||*channels==0)*/
    /*{*/
      if((*channels=determineChannels(fd))==UNSUCCESSFUL)
	{
	  freePkt(orbpkt);
	  elog_complain(0,"harvest(%d) = Could not determine channels (channels=%d)\n",running_instance,*channels);
	  return UNSUCCESSFUL;
	}
      fprintf(stderr,"channels=%d\n",*channels);
      /*   }*/

  pfread("/export/spare/home/rt/pf/campbell2orb.pf",&pf);
  tbl=pfget_tbl(pf,sourceName);

  while((status=constructPacket(fd,orbpkt,channels,*previousTimestamp,currentMemPtr,*lastMemPtr,sourceName,tbl))!=-1)
    {
      if(status==UNSUCCESSFUL)
	{
	  elog_complain(0,"harvest(%d) = Could not construct packet\n",running_instance);
	  freePkt(orbpkt);
	  return UNSUCCESSFUL;
	}

      packetTimestamp=status;

      if(packetTimestamp>*previousTimestamp)
	{
	  orbpkt->pkttype=suffix2pkttype("MGENC");
	  orbpkt->nchannels=*channels;
	  stuffPkt(orbpkt,generatedSourceName,&t,&packet,&nbytes,&packetsz);

	  if(version_limit==0 || version_limit==version_actual)
	    {
	      orbput(*orbfd,generatedSourceName,t,packet,nbytes);

	      if(version_showerr==1)
		{
		  elog_complain(0,"harvest(%d) = Specified version and parameter file version numbers match again, resuming processing of packets",running_instance);
		  showPkt(0,generatedSourceName,t,packet,nbytes,stderr,PKT_TERSE);
		  version_showerr=0;
		}

	      if(debugPkts==1)
		showPkt(0,generatedSourceName,t,packet,nbytes,stderr,PKT_UNSTUFF);
	    }
	  else
	    {
	      elog_complain(0,"harvest(%d) = Specified version and parameter file version numbers do not match, will not process packets until version numbers converge again",running_instance);
	      showPkt(0,generatedSourceName,t,packet,nbytes,stderr,PKT_TERSE);
	      version_showerr=1;
	    }

	  freePkt(orbpkt);
	  orbpkt=newPkt();
	  packetsz=0;

	  *stepSize=packetTimestamp-*previousTimestamp;
	  *previousTimestamp=packetTimestamp;
	  *lastMemPtr=atoi(currentMemPtr);

	  bury();
	}
      else if(packetTimestamp<*previousTimestamp)
	{
	  if(setMemPtr(fd,*lastMemPtr)==UNSUCCESSFUL)
	    {
   	      freePkt(orbpkt);
	      elog_complain(0,"harvest(%d) = (2) Could not set memory pointer (lastMemPtr=%d)\n",running_instance,*lastMemPtr);
	      return UNSUCCESSFUL;
	    }

	  if(deadlock++>=DATA_RETRY)
	    {
	      *previousTimestamp=0;
	      deadlock=0;
	    }
	}
    }

  freetbl(tbl,0);
  freePkt(orbpkt);

  if(*stepSize>time(NULL)-packetTimestamp)
    return *stepSize-(time(NULL)-packetTimestamp);
  else if(*stepSize==packetTimestamp)
    return 60;
  else
    return *stepSize;
}

int setMemPtr(int *fd,int location)
{
  char moveCmd[50];
  int moveCmdSize=0;

  bzero(moveCmd,50);

  if(location==-1)
    moveCmdSize=sprintf(moveCmd,"B\r");
  else
    moveCmdSize=sprintf(moveCmd,"%dG\r",location);

  if (write(*fd,moveCmd,moveCmdSize)<moveCmdSize)
    {
      close(*fd);
      *fd=-1;
      return(UNSUCCESSFUL);
    }

  return flushUntil(fd,'*');
}

int flushUntil(int *fd,char c)
{
  char prompt=0;
  int loop=0;

  while(loop++<MAX_SAMPLES_PKT*300+100)
    {
      prompt=0;
      if (read(*fd,&prompt,1)<1)
	{
	  perror("read(662)");
	  close(*fd);
	  *fd=-1;
	  return UNSUCCESSFUL;
	}
      
      /* fprintf(stderr,"read %c\n",prompt); */

      if(prompt==c)
	return loop;
    }

  elog_complain(0,"flushUntil(%d) = overflow in flushUntil (c=%c)\n",running_instance,c);
  return UNSUCCESSFUL;
}

int determineChannels(int *fd)
{
  char response[1000];
  int channels,
    responseSize,
    loop;

  bzero(response,1000);
  channels=0;
  responseSize=0;
  loop=0;

  if (getAttention(fd)==UNSUCCESSFUL)
    return UNSUCCESSFUL;

  write(*fd,"D\r",2);
  sleep(1);
  responseSize=read(*fd,response,1000);
  fprintf(stderr,"determineChannels response %s\n",response); 

  while(loop<responseSize)
    {
      if (response[loop]=='L') /* L = end of output record */
	{
	  responseSize=0;
	}
      else if(response[loop++]=='.')
	channels++;
    }


  if(setMemPtr(fd,-1)==UNSUCCESSFUL)
    {
      elog_complain(0,"determineChannels(%d) = Could not set memory pointer (location=-1)\n",running_instance);
      return UNSUCCESSFUL;
    }

  if (channels == 0)
    {
      write(*fd,"D\r",2);
      sleep(1);
      responseSize=read(*fd,response,1000);
      fprintf(stderr,"determineChannels (take 2) response %s\n",response); 
      
      while(loop<responseSize)
	{
	  if (response[loop]=='L') /* L = end of output record */
	    {
	      responseSize=0;
	    }
	  else if(response[loop++]=='.')
	    channels++;
	}
    }

  return channels;
}

double constructPacket(int *fd,struct Packet *orbpkt,int *pktChannels,double previousTimestamp,char *currentMemPtr,int lastMemPtr,char *sourceName,Tbl *tbl)
{
  char c=0,
    completeResponse[5000],
    dumpCmd[10],
    slice[500],
    dataPoint[7];
  int channels,
    records,
    loop=0,
    loop2=0,
    loop3=0,
    cells,
    cmdSize,
    offset,
    recordAdjustedMemPtr;
  double sampleTimestamp=previousTimestamp,
    previousSampleTimestamp;

  struct PktChannel *genericChannel;
  struct Srcname parts;

  char *string=NULL,
    *chaName=NULL;
  int  chaCalib=1000;
  char *chaSegtype=NULL;

  channels=*pktChannels;

  fprintf(stderr,"ch=%d\n",channels);
  
  do
  {
    loop=0;
    bzero(dumpCmd,10);
    cmdSize=sprintf(dumpCmd,"%dD\r",MAX_SAMPLES_PKT);
    write(*fd,dumpCmd,cmdSize);

    if(flushUntil(fd,dumpCmd[0])==UNSUCCESSFUL)
      return UNSUCCESSFUL;

    bzero(completeResponse,sizeof(completeResponse));
    completeResponse[loop++]=dumpCmd[0];

    while(loop<sizeof(completeResponse))
      {
	read(*fd,&c,1);
	completeResponse[loop++]=c;

	if(c=='*')
	  break;
      }

    completeResponse[loop]='\0';
    fprintf(stderr,"complete response %s\n",completeResponse); 

    cells=dataIntegrityCheck(completeResponse);

    if(cells==UNSUCCESSFUL)
      {
	if(setMemPtr(fd,lastMemPtr)==UNSUCCESSFUL)
	  {
	    elog_complain(0,"constructPacket(%d) = Could not set memory pointer (lastMemPtr=%d)\n",running_instance,lastMemPtr);
	    return UNSUCCESSFUL;
	  }
	else
	  elog_complain(0,"constructPacket(%d) = Checksum error\n",running_instance);

	getAttention(fd);

	if(loop3++>=DATA_RETRY)
	  {
	    elog_complain(0,"constructPacket(%d) = Checksum failed\n",running_instance);
	    return UNSUCCESSFUL;
	  }
      }
    else
      {
	bzero(currentMemPtr,10);
	loop=0;
	loop2=0;
	while(completeResponse[loop++]!='L');
	while(completeResponse[loop++]!=' ')
	  {
	    if(loop2==10)
	      {
		elog_complain(0,"constructPacket(%d) = Overflow in memory pointer (currentMemPtr=%s)\n",running_instance,currentMemPtr);
		return UNSUCCESSFUL;
	      }

	    currentMemPtr[loop2++]=completeResponse[loop];
	  }
	currentMemPtr[loop2]='\0';
      }
  }while(cells==UNSUCCESSFUL);


  if(cells==0)
    return -1;

  records=determineRecords(completeResponse,channels);
  fprintf(stderr,"records %d memPtr %d\n",records,lastMemPtr+records*channels); 
  if (records == 0)
    return (-1);

  recordAdjustedMemPtr=lastMemPtr+records*channels;
  offset=10*channels+channels/8+2;
  split_srcname(sourceName,&parts);

  for(loop=0;loop<records;loop++)
    {
      bzero(slice,500);

      for(loop2=loop*offset,loop3=0;loop2<loop*offset+offset;loop2++)
	{
	  if(completeResponse[cmdSize+1+loop2]==10)
	    slice[loop3++]=' ';
	  else if(completeResponse[cmdSize+1+loop2]==13)
	    continue;
	  else
	    slice[loop3++]=completeResponse[cmdSize+1+loop2];
	}
      /* fprintf(stderr,"%d slice %s^\n",loop2,slice); */

      previousSampleTimestamp=sampleTimestamp;
      if((sampleTimestamp=generateTimestamp(slice))==UNSUCCESSFUL)
	{
	  elog_complain(0,"constructPacket(%d) = Could not generate timestamp (slice=%s)\n",running_instance,slice);
	  return UNSUCCESSFUL;
	}
      /* fprintf(stderr,"sample %f\n",sampleTimestamp);*/

      for(loop2=0;loop2<channels;loop2++)
	{
	  /* default calibration is 1000 */
	  chaCalib=1000;

	  /* default segtype is NULL */
	  chaSegtype=NULL;

	  genericChannel=newPktChannel();
	  genericChannel->data=malloc(sizeof(int)*MAX_SAMPLES_PKT);

	  bzero(dataPoint,7);
	  strncpy(dataPoint,slice+2+loop2*10,6);

	  /* TESTING RESOLUTION PRESERVATION */
	  if(channels==maxtbl(tbl))
	    {
	      string=strdup(gettbl(tbl,loop2));
	      strtok(string,"\t");
	      chaName=strtok(NULL,"\t");
	      chaCalib=atoi(strtok(NULL,"\t"));
	      chaSegtype=strtok(NULL,"\n");
	    }

	  if(strcmp(chaName,"prog_vs"))
	    {
	      version_actual=atoi(dataPoint);
	      printf("version_actual=%d\n",version_actual);
	    }

	  *(genericChannel->data)=(int)(atof(dataPoint)*chaCalib);
	  genericChannel->time=sampleTimestamp;
	  genericChannel->samprate=1.0/(sampleTimestamp-previousSampleTimestamp);
	  genericChannel->calib=1.0/chaCalib;
	  genericChannel->calper=-1;
	  genericChannel->nsamp=1;

	  strcpy(genericChannel->net,parts.src_net);
	  strcpy(genericChannel->sta,parts.src_sta);

	  if(chaName!=NULL)
	    strcpy(genericChannel->chan,chaName);
	  else if(chaName==NULL)
	    sprintf(genericChannel->chan,"%i",loop2);

	  strcpy(genericChannel->loc,parts.src_loc);

	  if(chaSegtype!=NULL)
	    strcpy(genericChannel->segtype,chaSegtype);

	  /* fprintf(stderr,"packing channel %i with %i\n",loop2,atoi(dataPoint)); */
	  pushtbl(orbpkt->channels,genericChannel);

	  free(string);
	}
    }

  if(recordAdjustedMemPtr<atoi(currentMemPtr))
    {
      if(setMemPtr(fd,recordAdjustedMemPtr)==UNSUCCESSFUL)
	{
	    elog_complain(0,"constructPacket(%d) = (2) Could not set memory pointer (recordAdjustedMemPtr=%d)\n",running_instance,recordAdjustedMemPtr);
	    return UNSUCCESSFUL;
	}

      channels=determineChannels(fd);
      *pktChannels=channels;
    }

  return sampleTimestamp;
}

int determineRecords(char *completeResponse,int channels)
{
  char *token;
  int position=0,
    loop,
    columns,
    records=0;

  while((token=tokenizer(completeResponse,"01+",&position))!=NULL)
    {
      /*fprintf(stderr,"token %s\n",token); */
      columns=0;
      for(loop=0;token[loop]!='\0'&&token[loop]!='L';loop++)
	{
	  if(token[loop]=='.')
	    columns++;
	}

      if(channels==columns)
	records++;
      else if(channels!=columns)
	break;
    }

  return records;
}

char *tokenizer(char *s,char *d,int *position)
{
  char *t1,*t2;

  if(*position==-1)
    return NULL;

  t1=strstr(s+*position,d);
  if (t1==NULL)
    return NULL;

  t2=strstr(t1+sizeof(d),d);

  /*if(t2!=NULL)
     fprintf(stderr,"t1 %s t2 %s\n",t1,t2); */

  if(t2!=NULL)
    {
      *(t2-1)='\0';
      *position=t2-s;
    }
  else if(t2==NULL)
    *position=-1;

  /*if(*position==-1)
    return NULL;*/

  return t1;
}

int dataIntegrityCheck(char *completeResponse)
{
  char checksum[5];
  int loop=0,
    runningChecksum=0,
    cells=0;
  int lc;

  lc=0;
  while(completeResponse[loop]!='C')
    {
      if(completeResponse[loop]=='L')
	lc=1;
      if(lc==0 && completeResponse[loop]=='.')
	cells++;

      runningChecksum+=(unsigned int)completeResponse[loop++];
      runningChecksum%=8192;
    }

  runningChecksum+=(int)'C';

  loop++;
  checksum[0]=completeResponse[loop++];
  checksum[1]=completeResponse[loop++];
  checksum[2]=completeResponse[loop++];
  checksum[3]=completeResponse[loop];
  checksum[4]='\0';
  /* fprintf(stderr,"checksum %d\n",atoi(checksum)); */

  if(runningChecksum!=atoi(checksum))
    {
      elog_complain(0,"dataIntegrityCheck(%d) = Checksum error (runningChecksum=%i,checksum=%s\n",running_instance,runningChecksum,checksum);
      return UNSUCCESSFUL;
    }
  else
    return cells;
}

double generateTimestamp(char *sample)
{
  char timestamp[24];
  double epoch;

  extractTimestamp(sample,timestamp);
  /* fprintf(stderr,"timestamp %s\n",timestamp); */

  if(zstr2epoch(timestamp,&epoch)!=0)
    return UNSUCCESSFUL;
  else
    return epoch;
}

void extractTimestamp(char *sample,char *timestamp)
{
  /* year (day) hour:min:sec.subsec */

  timestamp[0]=sample[13];
  timestamp[1]=sample[14];
  timestamp[2]=sample[15];
  timestamp[3]=sample[16];
  timestamp[4]=' ';
  timestamp[5]='(';
  timestamp[6]=sample[23];
  timestamp[7]=sample[24];
  timestamp[8]=sample[25];
  timestamp[9]=sample[26];
  timestamp[10]=')';
  timestamp[11]=' ';
  timestamp[12]=sample[33];
  timestamp[13]=sample[34];
  timestamp[14]=':';
  timestamp[15]=sample[35];
  timestamp[16]=sample[36];

  timestamp[17]='\0';

  /*
  timestamp[17]=':';
  timestamp[18]=sample[43];
  timestamp[19]=sample[44];
  timestamp[20]=sample[45];
  timestamp[21]=sample[46];
  timestamp[22]=sample[47];
  timestamp[23]='\0';
  */
}
