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
#include <sys/time.h>
#include <syslog.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <strings.h>
#include <termios.h>
#include <libgen.h>
#include <orb.h>
#include <coords.h>
#include <stock.h>
#include <Pkt.h>
#include "solinst2orb.h"

#define BACKLOG 1

int Stop=0;
static int debugPkts=0;

int main(int argc, char *argv[])
{
  int ch,
    connect_flag,
    err_flag,
    status,
    orbfd,
    fd;

  char *srcname,
    *address,
    *port,
    *statefile,
    *orb=":";

  Relic relic;

  int lastMemPtr=0;

  ch=0;
  connect_flag=-1;
  err_flag=0;

  srcname=NULL;
  address=NULL;
  port=NULL;
  statefile=NULL;

  elog_init(argc,argv);

  while((ch=getopt(argc,argv,"vs:a:l:c:S:O:d"))!=-1)
    {
      switch(ch)
	{
	case 'v':
	  usage();
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
	case 'c':
	  if(connect_flag==0)
	    {
	      usage();
	    }
	  connect_flag=1;
	  port=optarg;
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
	  
      relic.sp=&srcname;
      if(resurrect("srcname",relic,STRING_RELIC)==0)
	{
	  fprintf(stderr,"resurrected sourcename %s\n",srcname);
	}

      relic.ip=&connect_flag;
      if(resurrect("connect_flag",relic,INT_RELIC)==0)
	{
	  fprintf(stderr,"resurrected connect_flag %i\n",connect_flag);
	}

      if(connect_flag==1)
	{
	  relic.sp=&address;
	  if(resurrect("address",relic,STRING_RELIC)==0)
	    {
	      fprintf(stderr,"resurrected address %s\n",address);
	    }
	}

      relic.sp=&port;
      if(resurrect("port",relic,STRING_RELIC)==0)
	{
	  fprintf(stderr,"resurrected port %s\n",port);
	}

      relic.ip=&lastMemPtr;
      if(resurrect("lastMemPtr",relic,INT_RELIC)==0)
	{
	  fprintf(stderr,"resurrected lastMemPtr %i\n",lastMemPtr);
	}
    }

  orbfd=orbopen(orb,"w&");

  while(1)
    {
      /*
      fd=open("/dev/cuaa0",O_RDWR);
      set(fd,"\001S3\002M01\003");
      resetLogger(fd);
      */

      if(connect_flag)
	fd=initConnection(address,port);
      else
	fd=acceptConnection(address,port);

      status=verifySetupGetData(fd,orbfd,srcname,&lastMemPtr);

      shutdown(fd,SHUT_RDWR);
      close(fd);
      fprintf(stderr,"%s status %i\n",srcname,status);
      sleep(status);
    }

  return 0;
}

void usage()
{
  printf("Usage: solinst2orb [-v] -s sourcename -a address -c connectport [-S statefile] [-O orb] [-d]\n");
  printf("Usage: solinst2orb [-v] -s sourcename -l listenport [-S statefile] [-O orb] [-d]\n");
  exit(0);
}

void resetLogger(fd)
{
  char timeStr[17],
    setStr[11+17+4];
  time_t calptr;
  struct tm *brokenDownTime;

  time(&calptr);
  /*calptr=(long)calptr+24*60*60;*/
  brokenDownTime=gmtime(&calptr);

  sprintf(timeStr,"%.2d/%.2d/%.2d %.2d:%.2d:%.2d",brokenDownTime->tm_year-100,brokenDownTime->tm_mon+1,brokenDownTime->tm_mday,brokenDownTime->tm_hour,brokenDownTime->tm_min,brokenDownTime->tm_sec);

  /*fprintf(stderr,"timeStr %s\n",timeStr);*/

  sprintf(setStr,"%s%s%s",setDateTimeHdr,timeStr,genericFtr);

  set(fd,setStr);
  set(fd,setDirectStopMeasurementRegistration);
  set(fd,setDirectStartCalibration);
  set(fd,setDirectStartRegistration);

  exit(0);
}

int verifySetupGetData(int fd,int orbfd,char *srcname,int *lastMemPtr)
{
  struct dataFrame 
    a128ByteDumpDF,
    idOneDF,
    refOneDF,
    rangeOneDF,
    idTwoDF,
    refTwoDF,
    rangeTwoDF,
    masterDF,
    altitudeDF,
    sampleRateDF,
    sampleModeDF,
    dateTimeDF,
    ch1DF,
    ch2DF,
    statusDF;

  struct Packet *orbpkt=newPkt();
  struct PktChannel *pressure=newPktChannel();
  struct PktChannel *temperature=newPktChannel();

  struct Srcname parts;

  char generatedSrcname[ORBSRCNAME_SIZE];
  int packetsz=0,nbytes;
  double t;
  char *packet;

  char
    refOneStr[10]="\0",
    rangeOneStr[10]="\0",
    refTwoStr[10]="\0",
    rangeTwoStr[10]="\0",
    masterStr[10]="\0",
    altitudeStr[10]="\0",
    startTimeStr[18]="\0",
    stopTimeStr[18]="\0";

  unsigned char
    byte1='\0',
    byte2='\0',
    byte3='\0',
    byte4='\0';

  int value1=0,
    value2=0,
    done=0,
    loop=0,
    loop2=0,
    doOrbput=0,
    retry=0,
    store1,
    store2;

  double 
    ref1=0,
    range1=0,
    ref2=0,
    range2=0,
    masterOffset=0,
    altitudeOffset=0,
    sampleRate=0,
    startTime=0,
    stopTime=0,
    result1=0,
    result2=0,
    packetTimestamp=0,
    sampleTimestamp=0,
    calib1,
    calib2;

  /*
  FILE *output=fopen("/export/spare/home/ryuen/solinst/dev01/output","a");
  FILE *debug=fopen("/export/spare/home/ryuen/solinst/dev01/debug","a");
  */

  initDataFrame(&a128ByteDumpDF);
  initDataFrame(&idOneDF);
  initDataFrame(&refOneDF);
  initDataFrame(&rangeOneDF);
  initDataFrame(&idTwoDF);
  initDataFrame(&refTwoDF);
  initDataFrame(&rangeTwoDF);
  initDataFrame(&masterDF);
  initDataFrame(&altitudeDF);
  initDataFrame(&sampleRateDF);
  initDataFrame(&sampleModeDF);
  initDataFrame(&dateTimeDF);
  initDataFrame(&ch1DF);
  initDataFrame(&ch2DF);
  initDataFrame(&statusDF);

  bzero(refOneStr,10);
  bzero(rangeOneStr,10);
  bzero(refTwoStr,10);
  bzero(rangeTwoStr,10);
  bzero(masterStr,10);
  bzero(altitudeStr,10);
  bzero(startTimeStr,18);
  bzero(stopTimeStr,18);

  query(fd,queryIdCodeCh1,&idOneDF);
  query(fd,queryRefUnitCh1,&refOneDF);
  query(fd,queryRangeUnitCh1,&rangeOneDF);

  query(fd,queryIdCodeCh2,&idTwoDF);
  query(fd,queryRefUnitCh2,&refTwoDF);
  query(fd,queryRangeUnitCh2,&rangeTwoDF);

  query(fd,queryMasterUnit,&masterDF);
  query(fd,queryAltitudeUnit,&altitudeDF);
  query(fd,querySampleRate,&sampleRateDF);
  query(fd,querySampleMode,&sampleModeDF);

  query(fd,queryDateTime,&dateTimeDF);
  query(fd,queryCh1,&ch1DF);
  query(fd,queryCh2,&ch2DF);

  issueDumpCmd(fd,244,&a128ByteDumpDF);
  
  strncpy(refOneStr,refOneDF.buf,10);
  strncpy(rangeOneStr,rangeOneDF.buf,10);
  strncpy(refTwoStr,refTwoDF.buf,10);
  strncpy(rangeTwoStr,rangeTwoDF.buf,10);
  strncpy(masterStr,masterDF.buf,10);
  strncpy(altitudeStr,altitudeDF.buf,10);
  strncpy(startTimeStr,a128ByteDumpDF.buf,17);
  strncpy(stopTimeStr,a128ByteDumpDF.buf+19,17);

  startTimeStr[17]='\0';
  stopTimeStr[17]='\0';

  ref1=strtod(refOneStr,NULL);
  range1=strtod(rangeOneStr,NULL);
  ref2=strtod(refTwoStr,NULL);
  range2=strtod(rangeTwoStr,NULL);
  masterOffset=strtod(masterStr,NULL);
  altitudeOffset=strtod(altitudeStr,NULL);

  /*
  printf("a128ByteDumpDF.buf %s\n",a128ByteDumpDF.buf);
  printf("dateTime %s\nstart %s\nstop %s\n",dateTimeDF.buf,startTimeStr,stopTimeStr);
  */

  startTime=generateEpoch(startTimeStr);
  stopTime=generateEpoch(stopTimeStr);
  sampleRate=generateRate(&sampleRateDF,&sampleModeDF);

  /*
  printf("idOne %s\nidTwo %s\n",idOneDF.buf,idTwoDF.buf);
  printf("ref1 %f\nrange1 %f\nref2 %f\nrange2 %f\n",ref1,range1,ref2,range2);
  printf("lastMemPtr %i\n",*lastMemPtr);
  */

  pressure->data=malloc(sizeof(int)*MAX_SAMPLES_PKT);
  temperature->data=malloc(sizeof(int)*MAX_SAMPLES_PKT);

  split_srcname(srcname,&parts);

  done=0;

  while(done!=1)
  {
    if(retry++>=3)
      {
	elog_complain(0,"Could not retrieve data\n");
	/* fclose(output); */

	freePkt(orbpkt);
	freePktChannel(pressure);
	freePktChannel(temperature);

	if(sampleRate<60)
	  return 60;
	else
	  return sampleRate;
      }

    /* 8 get 128 byte frame containing 32 samples */
    initDataFrame(&a128ByteDumpDF);
    /* issueDumpCmd(fd,280+(*lastMemPtr)*4,&a128ByteDumpDF); */

    if(issueDumpCmd(fd,280+(*lastMemPtr)*4,&a128ByteDumpDF)==UNSUCCESSFUL)
      {
	sleep(1);
	continue;
      }

    /* decide how many packets in 32 samples */
    for(loop=0;loop<(int)(32/MAX_SAMPLES_PKT);loop++)
      {
	orbpkt->pkttype=suffix2pkttype("MGENC");
	orbpkt->nchannels=2;

	packetTimestamp=(*lastMemPtr)*sampleRate+startTime;
	doOrbput=0;

	/* construct one packet */
	for(loop2=0;loop2<MAX_SAMPLES_PKT;loop2++)
	  {
	    /* printf("loop %d loop2 %d\n",loop,loop2); */
	    sampleTimestamp=(*lastMemPtr)*sampleRate+startTime;

	    /* printf("sampleTimestamp %f stopTime %f\n",sampleTimestamp,stopTime); */

	    if(sampleTimestamp>stopTime)
	      {
		done=1;
		break;
	      }

	    byte1=a128ByteDumpDF.buf[loop*MAX_SAMPLES_PKT*4+loop2*4+0];
	    byte2=a128ByteDumpDF.buf[loop*MAX_SAMPLES_PKT*4+loop2*4+1];
	    byte3=a128ByteDumpDF.buf[loop*MAX_SAMPLES_PKT*4+loop2*4+2];
	    byte4=a128ByteDumpDF.buf[loop*MAX_SAMPLES_PKT*4+loop2*4+3];

	    if(byte1==0xFD&&sampleTimestamp<=stopTime)
	      break;

	    value1=byte1+250*byte2;
	    value2=byte3+250*byte4;

	    result1=((double)value1/30000.0)*range1+ref1;
	    result2=((double)value2/30000.0)*range2+ref2;

	    store1=(int)(value1+30000*ref1/range1);
	    store2=(int)(value2+30000*ref2/range2);

	    calib1=range1/30000;
	    calib2=range2/30000;

	    /*
	    printf("byte1 %x %d\nbyte2 %x %d\nbyte3 %x %d\nbyte4 %x %d\nvalue1 %d\nvalue2 %d\nresult1 %f\nresult2 %f\nsampleTimestamp %f\nepoch2str %s\n",byte1,byte1,byte2,byte2,byte3,byte3,byte4,byte4,value1,value2,result1,result2,sampleTimestamp,epoch2str(sampleTimestamp,"%D %T"));

	    fprintf(output,"%f %f %s\n\n",result1,result2,epoch2str(sampleTimestamp,"%D %T"));
	    */
	    
	    *(pressure->data)=store1;
	    *(temperature->data)=store2;

	    (*lastMemPtr)++;
	    doOrbput=1;

	    bury();
	  }

	if(byte1==0xFD&&sampleTimestamp<=stopTime)
	  {
	    done=0;
	    sleep(1);
	    break;
	  }

	if(doOrbput==1)
	  {
	    retry=0;

	    pressure->time=sampleTimestamp;
	    temperature->time=sampleTimestamp;
	    pressure->samprate=1.0/sampleRate;
	    temperature->samprate=1.0/sampleRate;
	    pressure->calib=calib1;
	    temperature->calib=calib2;
	    pressure->calper=-1;
	    temperature->calper=-1;
	    pressure->nsamp=1;
	    temperature->nsamp=1;
	    strcpy(pressure->net,parts.src_net);
	    strcpy(temperature->net,parts.src_net);
	    strcpy(pressure->sta,parts.src_sta);
	    strcpy(temperature->sta,parts.src_sta);
	    strcpy(pressure->chan,"PRESSURE");
	    strcpy(temperature->chan,"TEMPERATURE");
	    strcpy(pressure->segtype,"P");
	    strcpy(temperature->segtype,"C");

	    pushtbl(orbpkt->channels,pressure);
	    pushtbl(orbpkt->channels,temperature);

	    stuffPkt(orbpkt,generatedSrcname,&t,&packet,&nbytes,&packetsz);
	    orbput(orbfd,generatedSrcname,t,packet,nbytes);

	    if(debugPkts==1)
	      {
		showPkt(loop,generatedSrcname,t,packet,nbytes,stderr,PKT_UNSTUFF);		/*showPkt(loop,generatedSrcname,t,packet,nbytes,debug,PKT_UNSTUFF);*/
	      }
	  }

	if(done==1)
	  break;
      }
  }

  /*
  fclose(output);
  fclose(debug);
  */

  freePkt(orbpkt);
  freePktChannel(pressure);
  freePktChannel(temperature);
  free(packet);

  return (int)sampleRate;
}

double generateRate(struct dataFrame *rate,struct dataFrame *mode)
{
	double unit,scalar;
	char scalarStr[2];

	if(mode->buf[0]!='T')
		return -1;
	else
	{
		strncpy(scalarStr,rate->buf+1,2);
		scalar=strtod(scalarStr,NULL);

		if(rate->buf[0]=='T')
			unit=1/10;
		else if(rate->buf[0]=='S')
			unit=1;
		else if(rate->buf[0]=='M')
			unit=60;
		else if(rate->buf[0]=='H')
			unit=3600;
	}

	return unit*scalar;
}

double generateEpoch(char *str)
{

  /* 7:08:11 17/10/02 ss:mm:hh dd/mm/yy */

  char timestamp[18];

  double epoch;

  timestamp[0]=str[12];
  timestamp[1]=str[13];
  timestamp[2]='/';
  timestamp[3]=str[9];
  timestamp[4]=str[10];
  timestamp[5]='/';
  timestamp[6]=str[15];
  timestamp[7]=str[16];
  timestamp[8]=' ';
  timestamp[9]=str[6];
  timestamp[10]=str[7];
  timestamp[11]=':';
  timestamp[12]=str[3];
  timestamp[13]=str[4];
  timestamp[14]=':';
  timestamp[15]=str[0];
  timestamp[16]=str[1];
  timestamp[17]='\0';

  /* printf("timestamp %s\n",timestamp); */

  if(zstr2epoch(timestamp,&epoch)!=0)
  	return -1;
  else
  	return epoch;
}

int issueDumpCmd(int fd,int index,struct dataFrame *result)
{
  char a128ByteDumpCmd[11];

  bzero(a128ByteDumpCmd,11);
  sprintf(a128ByteDumpCmd,"%s%5.5X%s",query128ByteDumpHdr,index,genericFtr);
  /* printf("dumpcmd %s\n",a128ByteDumpCmd); */

  return query(fd,a128ByteDumpCmd,result);
}

void initDataFrame(struct dataFrame *frame)
{
  bzero(frame->buf,128);
}

int initConnection(char *host, char *port)
{
  int fd;
  unsigned long ina;
  struct hostent *host_ent;
  struct sockaddr_in addr;
  struct timeval tv;
  struct linger l;

  if (-1 != (ina=inet_addr(host)))
    {
      memcpy(&addr.sin_addr,&ina,min(sizeof(ina), sizeof(addr.sin_addr)));
  }
  else 
    {
      host_ent = gethostbyname(host);
   
      if ( host_ent == NULL )
	{
	  perror("Could not resolve address host");
	  return -1;
	}

      memcpy(&addr.sin_addr, host_ent->h_addr,min(host_ent->h_length, sizeof(addr.sin_addr)));
    }

  /*make socket*/
  fd = socket(AF_INET, SOCK_STREAM, 0);

  tv.tv_sec=10;
  tv.tv_usec=0;
  setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
  setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&tv,sizeof(tv));

  l.l_onoff=0;
  setsockopt(fd,SOL_SOCKET,SO_LINGER,&l,sizeof(l));

  /*create address from host ent*/
  addr.sin_family = AF_INET;
  addr.sin_port = htons(atoi(port));

  if (0 > connect(fd, (struct sockaddr *) &addr, sizeof(addr))) 
    {
      perror("connect failed");
      close(fd);
      return -1;
    }

  return fd;
}

int acceptConnection(char *host,char *port)
{
  int fd,
    fd2;
  int bool;
  struct sockaddr_in server, client;
  int sin_size;
  struct timeval tv;
  struct linger l;

  if((fd=socket(AF_INET,SOCK_STREAM,0))==-1)
    {
      perror("socket() error");
      exit(1);
    }

  bool=1;
  if(setsockopt(fd,SOL_SOCKET,SO_REUSEADDR,&bool,sizeof(bool))==-1)
    {
      perror("setsockopt");
      exit(1);
    }

  l.l_onoff=0;
  l.l_linger=0;
  if(setsockopt(fd,SOL_SOCKET,SO_LINGER,&l,sizeof(l))==-1)
    {
      perror("setsockopt");
      exit(1);
    }

  server.sin_family=AF_INET;
  server.sin_port=htons(atoi(port));
  server.sin_addr.s_addr=INADDR_ANY;
  bzero(&(server.sin_zero),8);

  if(bind(fd,(struct sockaddr*)&server,sizeof(struct sockaddr))==-1)
    {
      perror("bind() error");
      exit(1);
    }

  if(listen(fd,BACKLOG)==-1)
    {
      perror("listen() error");
      exit(1);
    }

  sin_size=sizeof(struct sockaddr_in);

  if((fd2=accept(fd,(struct sockaddr*)&client,&sin_size))==-1)
    {
      perror("accept() error");
      exit(1);
    }

  tv.tv_sec=10;
  tv.tv_usec=0;
  setsockopt(fd2,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
  setsockopt(fd2,SOL_SOCKET,SO_SNDTIMEO,&tv,sizeof(tv));

  /* printf("connection from %s\n",inet_ntoa(client.sin_addr)); */
  host=strdup(inet_ntoa(client.sin_addr));
  shutdown(fd,SHUT_RDWR);
  close(fd);

  return fd2;
}

void set(int fd, char *cmd)
{
  query(fd,cmd,NULL);
}

int query(int fd, char *query, struct dataFrame *result)
{
  int val;
  char checksum, buf[200];
  char cmd[50];
  int cmdSize,responseSize;
  int loop;

  cmdSize=0;
  responseSize=0;
  responseSize=0;
  bzero(buf,200);
  bzero(cmd,50);

  checksum=createChecksum(query,0);
  cmdSize=sprintf(cmd,"W%s%c",query,checksum);
  write(fd,cmd,cmdSize);

  val=fcntl(fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(fd,F_SETFL,val);

  /* sleep 300 ms */
  sleep(1);
  responseSize=read(fd,buf,200);

  val&=~O_NONBLOCK;
  fcntl(fd,F_SETFL,val);

  fprintf(stderr,"responeSize %i\n",responseSize);

  errno=0;

  if(responseSize==-1||errno==EAGAIN||errno==EWOULDBLOCK)
    {
      elog_complain(0,"socket timed out\n");
      return UNSUCCESSFUL;
    }

  checksum=createChecksum(buf,responseSize);

  /* printf("responseSize %i\nbuf checksum %i\n",responseSize,buf[responseSize-1]); */

  if(buf[responseSize-1]!=checksum)
    {
      elog_complain(0,"checksum error\n");
      return UNSUCCESSFUL;
    }
  else if(result==NULL)
    {
      return 0;
    }

  loop=0;
  while(buf[loop++]!='\002');
  memcpy(result->buf,buf+loop,responseSize);

  return 0;
}

unsigned char createChecksum(char *buf, int bufSize)
{
  int loop=0;
  unsigned char sum;

  sum=0;
  loop=0;

  /* printf("bufSize %i\n",bufSize); */

  /* simple algorithm */
  if(bufSize==0)
    {
      while(buf[loop]!='\003')
	{
	  /* printf("%i %c %i\n",(unsigned char)buf[loop],buf[loop],sum); */

	  sum+=(unsigned char)buf[loop];
	  loop++;
	}

      sum+='\003';
    }
  /* handle complex query */
  else
    {
      while(loop<bufSize-1)
	{
	  /*printf("%i %c %i\n",(unsigned char)buf[loop],buf[loop],sum);*/

	  sum+=(unsigned char)buf[loop];
	  loop++;
	}
    }

  /*printf("calc checksum %i\n",sum);*/

  return sum;
}
