#include <unistd.h>
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

#define min(a,b)  (a<b?a:b)

/*
 Copyright (c) 2004 The Regents of the University of California
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

   Based on code written by: Rock Yuen-Wong 6/2/2003
   This code by: Todd Hansen 12/18/2003
   Last Updated By: Todd Hansen 6/2/2004
*/

#define VERSION "$Revision: 1.17 $"
#define UNSUCCESSFUL -9999

#define MAXCHANNELS 300
#define MAXRESP 5000

int verbose=0, printprog=0;
double starttime=-1, endtime=-1;
char *ipaddress=NULL;
char *serialport=NULL;
char *port="4000";
char *statefile=NULL;
char *configfile=NULL;
char *orbname=":";
char *srcname="test_sta1";
char *camtimezone="";
int orbfd;
int interval=0;
int OldMemPtr=-1;
int NextMemPtr=1;  /* state pointers */
double previoustimestamp=-1; /* state pointers */
int previousyearstamp=0;
int previousdaystamp=0;
int previoushrstamp=0;
int previoussecstamp=0;
int force=0;
int secondsfield=0;
int slop;
int checktime=0;
int kickstatefile=0;
int versioncheck=-1;
int jitterenable=0;
int skewlog=-1;
int skewlogvalid=0;
double samintlog=-1;
int samintlogvalid=0;

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int pseed);
int getAttention(int *fd);
void flushOut(int *fd);
int flushUntil(int *fd,char c);
void printProgram(int *fd);
int setMemPtr(int *fd, int location);
int readline(int *fd, char *rebuf);
int initConnection(char *host, char *port);
int dataIntegrityCheck(char *completeResponse);
int stuffline(Tbl *r);
void getTime(int *fd);

void usage (void)
{
  cbanner(VERSION,"[-v] [-V] [-d] [-f] [-q] [-x] [-j] {[-p serialport] | [-a ipaddress] [-n portnumber]} [-s statefile [-k]] [-t starttime] [-e endtime] [-c net_sta] [-g configfile] [-i interval] [-r serialspeed] [-m arrayid] [-z timezone] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main(int argc,char *argv[])
{
  char ch;
  int fd=0;
  int speed=B9600;
  int fpass=0;
  FILE *fil;
  struct termios orig_termios;
  char readbuf[MAXRESP];
  double chans[MAXCHANNELS];
  int nchans=0;
  Relic relic;
  int sleeptime;

  elog_init(argc,argv);

  while((ch=getopt(argc,argv,"Vvfjqxkdp:a:n:m:i:s:t:r:e:c:g:o:z:"))!=-1)
    {
      switch(ch)
	{
	case 'V':
	  usage();
	  exit(-1);
	  break;	
	case 'v':
	  verbose=1;
	  break;
	case 'f':
	  force=1;
	  break;
	case 'x':
	  checktime=1;
	  break;
	case 'j':
	  jitterenable=1;
	  break;
	case 'q':
	  secondsfield=1;
	  break;
	case 'k':
	  kickstatefile=1;
	  break;
	case 'p':
	  serialport=optarg;
	  break;
	case 'a':
	  ipaddress=optarg;
	  break;
	case 'i':
	  interval=atoi(optarg);
	  break;
	case 'n':
	  port=optarg;
	  break;
	case 'm':
	  versioncheck=atoi(optarg);
	  elog_notify(0,"runtime restricted looking for campbell program version (%d arrayid)\n",versioncheck);
	  break;
	case 's':
	  statefile=optarg;
	  break;
	case 'r':
	  speed=find_speed(optarg);
	  break;
	case 't':
	  starttime=atoi(optarg);
	  elog_notify(0,"runtime restricted looking for data newer than (%.2f)\n",starttime);
	  break;
	case 'e':
	  endtime=atoi(optarg);
	  elog_notify(0,"runtime restricted looking for data older than (%.2f)\n",versioncheck);
	  break;
	case 'c':
	  srcname=optarg;
	  break;
	case 'd':
	  printprog=1;
	  break;
	case 'g':
	  configfile=optarg;
	  break;
	case 'z':
	  camtimezone=optarg;
	  break;
	case 'o':
	  orbname=optarg;
	  break;
	default:
	  elog_complain(0,"Invalid argument\n");
	  usage();
	  exit(-1);
	}
    }
  elog_notify(0,"csi2orb %s\n",VERSION);
  if (jitterenable && (!checktime || !(interval>0) || !configfile))
    {
      elog_notify(0,"jitter enable (-j) has no effect unless you specify (-x, -g configfile, and  -i maxinterval)\n");
      jitterenable=0;
    }

  if ((serialport==NULL && ipaddress==NULL) || (serialport!=NULL && ipaddress!=NULL))
    {
      elog_complain(0,"missing or vague arguments, please use one argument of either -a or -p\n\n");
      usage();
      exit(-1);
    }

  if(statefile!=NULL)
    {
      ch=exhume(statefile,NULL,0,0);
      if (ch<0)
	{
	  elog_complain(1,"exhume failed, returned %d.\n",ch);
	  exit(-1);
	}
       
      if (ch==0)
	elog_notify(0,"no saved state file found. starting from scratch\n");

      relic.dp=&previoustimestamp;
      if(resurrect("previousTimestamp",relic,DOUBLE_RELIC)==0)
	fprintf(stderr,"resurrected previousTimestamp %f\n",previoustimestamp);
      else
	previoustimestamp=-1;

      /*
    if(resurrect("previousyearstamp",relic,INT_RELIC)==0)
        fprintf(stderr,"resurrected previousyearstamp %d\n",previousyearstamp);
      else
	previousyearstamp=0;

    if(resurrect("previousdaystamp",relic,INT_RELIC)==0)
	fprintf(stderr,"resurrected previousdaystamp %d\n",previousdaystamp);
      else
	previousdaystamp=0;

    if(resurrect("previoushrstamp",relic,INT_RELIC)==0)
	fprintf(stderr,"resurrected previoushrstamp %d\n",previoushrstamp);
      else
	previoushrstamp=0;
      */

      relic.ip=&NextMemPtr;
      if(resurrect("NextMemPtr",relic,INT_RELIC)==0)
	fprintf(stderr,"resurrected NextMemPtr %d\n",NextMemPtr);
      else
	NextMemPtr=1;
    }

  if (kickstatefile>0)
    {
      NextMemPtr=1;
      previoustimestamp=-1;
      if (statefile!=NULL)
	elog_notify(0,"ignoring state file's state since you specified the -k option, we will start at the beginning of the data logger and update the state file as we download new data\n");
    }

  if ((orbfd=orbopen(orbname,"w&"))<0)
    {
      perror("orbopen failed");
      return(-1);
    }
  
  fd=-1;
  while (1)
    {
      if (fd<0)
	{
	  if (verbose)
	    elog_notify(0,"connecting to remote station\n");

	  if (ipaddress)
	    fd=initConnection(ipaddress,port);
	  else
	    {
	      fil=init_serial(serialport, &orig_termios, &fd, speed);
	      fclose(fil);
	    }

	  if (fd>0)
	    {
	      if (getAttention(&fd)==UNSUCCESSFUL)
		{
		  close(fd);
		  fd=-1;
		}
	      else
		fpass=1;
	    }
	}

      slop=1;
      if (fd>=0)
	{
	  if (printprog)
	    {
	      printProgram(&fd);
	      break;
	    }	
	  if (fpass && checktime) 
	    getTime(&fd);
	  
	  if (fpass)
	    fpass=0;
	  
	  if (fd < 0 || setMemPtr(&fd,NextMemPtr)==UNSUCCESSFUL)
	    {
	      elog_complain(0,"setMemPtr(&fd,%d) failed\n",NextMemPtr);
	      close(fd);
	      fd=-1;
	    }
	  else
	    {
	      /*flushOut(&fd);*/
	      if (write(fd,"D\r",2)<2)
		{
		  elog_complain(1,"write(\"D\\r\") failed");
		  close(fd);
		  fd=-1;
		}
	      else
		{
		  if (readline(&fd,readbuf)!=UNSUCCESSFUL)
		    if (dataIntegrityCheck(readbuf)!=UNSUCCESSFUL)
		      slop=stuffline(split(readbuf,' ')); /* update local pointers and bury if applicable */
		    else
		      break;
		}
	    }
	}
      
      /* if slop then we ran out of data to get */
      if (interval>0 && slop)
	{
	  write(fd,"E\r",2);
	  close(fd);
	  fd=-2;
	  if (jitterenable && samintlogvalid && skewlogvalid)
	    {
	      sleeptime=(int)((previoustimestamp+samintlog+skewlog)-now());
	      if (sleeptime>interval || sleeptime<0)
		sleeptime=interval;
	      else if (verbose)
		elog_notify(0,"sleep shorted. (sleeping for %d sec, interval=%d)\n",sleeptime,interval);
	      
	      sleep(sleeptime);
	    }
	  else
	    sleep(interval);
	}
      else if (slop)
	break;
    }
  
  write(fd,"E\r",2);
  close(fd);
  orbclose(orbfd);
}

int stuffline(Tbl *r)
{
  int channels=0;
  char *c;
  Packet *orbpkt;
  PktChannel *pktchan;
  int prog_vs;
  int ret;
  int saminterval;
  static char *packet=NULL;
  static int packetsz=0;
  char pfsearch[255], *channame;
  int nbytes;
  double val, t;
  static Pf *configpf=NULL;
  char generatedSourceName[500];
  char channame_cpy[500];
  Srcname srcparts;
  Tbl *chantab;
  
  if (configfile!=NULL)
    {
      if ((ret=pfupdate(configfile,&configpf))<0)
	{
	  complain(1,"pfupdate(%s,configpf)",configfile);
	  exit(-1);
	} 
      else if (ret==1)
	elog_notify(0,"updated config file loaded %s\n",configfile);
    }

  orbpkt=newPkt();
  orbpkt->pkttype=suffix2pkttype("MGENC");
  orbpkt->nchannels=0;
  split_srcname(srcname,&srcparts);

  while(c=shifttbl(r))
    {
      while(*c!='\0' && !isdigit(*c) && *c != 'A')
	c++;

      if (c[0]=='A')
	{
	  c=shifttbl(r);
	  
	  while(*c!='\0' && !isdigit(*c) && *c != 'L')
	    c++;

	  if (channels<4 || (secondsfield && channels < 5))
	    {
	      complain(0,"this memory location (%d) did not contain enough data elements (%d)\n",OldMemPtr,channels);

	      /* don't do it */
	      freePkt(orbpkt);
	      if (channels==0)
		{
		  elog_notify(0,"are we done yet?\n");
		  return(1);
		}

	      exit(-1);
	    }

	  OldMemPtr=NextMemPtr;
	  NextMemPtr=atoi(c+1);
	  if (verbose)
	    elog_notify(0,"NextMemPtr updated (now=%d verbose=%s)\n",NextMemPtr,c);
	  break;
	}
      else if (c[0]!='\0' && channels==0)
	{
	  prog_vs=atoi(c+2);
	  if (verbose)
	    elog_notify(0,"program version=%d\n",prog_vs);
	}
      else if (c[0]!='\0' && channels==1)
	{
	  previousyearstamp=atoi(c+2);
	}
      else if (c[0]!='\0' && channels==2)
	{
	  previousdaystamp=atoi(c+2);
	}
      else if (c[0]!='\0' && channels==3)
	{
	  previoushrstamp=atoi(c+2);

	  if (secondsfield)
	    {
	      c=shifttbl(r);
	      channels++;

	      while(*c!='\0' && !isdigit(*c) && *c != 'A')
		c++;
	      previoussecstamp=atoi(c+2);
	    }

	  /* check timestamp */
	  if (secondsfield)
	    sprintf(pfsearch,"%d-%03d %d:%02d:%02d %s",previousyearstamp,previousdaystamp,previoushrstamp/100,previoushrstamp%100,previoussecstamp,camtimezone);
	  else
	    sprintf(pfsearch,"%d-%03d %d:%d %s",previousyearstamp,previousdaystamp,previoushrstamp/100,previoushrstamp%100,camtimezone);

	  t=str2epoch(pfsearch);
	  if (verbose)
	    elog_notify(0,"timestamp: %s -> %s\n",pfsearch,strtime(t));

	  sprintf(pfsearch,"%s{%d}{sampleinterval}",srcname,prog_vs);
	  if (configpf != NULL && !(t<starttime) && (versioncheck==-1 || prog_vs == versioncheck))
	    {
	      saminterval=pfget_int(configpf,pfsearch);
	      samintlog=saminterval;
	      samintlogvalid=1;

	      if (previoustimestamp>-0.2)
		{
		  if (t-previoustimestamp>saminterval+saminterval*0.05 || t-previoustimestamp<saminterval-saminterval*0.05)
		    {
		      if (force)
			complain(0,"sample interval out of tolerance, ignoring failure (%f should be %d with a tolerance of %f)\n",previoustimestamp-t,saminterval,saminterval*0.05);
		      else
			{
			  complain(0,"sample interval out of tolerance, failing, using -f to force this to work (%f should be %d with a tolerance of %f)\n",previoustimestamp-t,saminterval,saminterval*0.05);
			  exit(-1);
			}
		    }
		}
	    }
	  else 
	    {
	      saminterval=0;
	      if (verbose)
		{
		  if (versioncheck!=-1 && prog_vs != versioncheck)
		    elog_notify(0,"program version not matched, so I won't check for data gaps\n");
		  else
		    elog_notify(0,"no config file, so I won't check for data gaps\n");
		}
	    }
	  
	  orbpkt->time=t;
	}
      else if (c[0]!='\0')
	{
	  chantab=NULL;
	  pktchan = newPktChannel();
	  
	  if (configpf != NULL)
	    {
	      sprintf(pfsearch,"%s{%d}{ch%d}",srcname,prog_vs,channels+1);
	      channame=pfget_string(configpf,pfsearch);

	      if (channame != NULL)
		{
		  elog_notify(0,"%s\n",channame);
		  strncpy(channame_cpy,channame,499);
		  channame_cpy[499]='\0';
		  
		  chantab=split(channame_cpy,' ');
		  strncpy(pktchan->chan,gettbl(chantab,0),PKT_TYPESIZE);
		}
	      else if (orbpkt->time<starttime || (versioncheck!=-1 && versioncheck!=prog_vs))
		{ /* we aren't going to write it, so lets set a channel name */
		  sprintf(pktchan->chan,"%d",channels+1);
		}
	      else
		{
		  complain(0,"can't add channel %d, no channel name, ignoring packet at postion %d and timestamp %f (verbose=%s)\ncsi2orb is shutting down\n",channels+1,NextMemPtr,orbpkt->time,c);
		  freePktChannel(pktchan);
		  freePkt(orbpkt);
		  if (chantab!=NULL)
		    freetbl(chantab,0);
		  freetbl(r,0);
		  exit(-1);
		}
	    }
	  else
	    sprintf(pktchan->chan,"%d",channels+1);

	  pktchan->datasz = 1;
	  pktchan->data=malloc(4);
	  if (pktchan->data==NULL)
	    {
	      perror("malloc");
	      exit(-1);
	    }
	  
	  if (chantab && maxtbl(chantab)>1)
	    pktchan->data[0]=atof(c+2)*atof(gettbl(chantab,1));
	  else
	    pktchan->data[0]=atof(c+2)*1000;
		
	  pktchan->time=orbpkt->time;
	  strncpy(pktchan->net,srcparts.src_net,PKT_TYPESIZE);
	  strncpy(pktchan->sta,srcparts.src_sta,PKT_TYPESIZE);
	  *(pktchan->loc)='\0';
	  pktchan->nsamp=1;

	  if (chantab && maxtbl(chantab)>2)
	    strncpy(pktchan->segtype,gettbl(chantab,2),4);
	  else
	    strncpy(pktchan->segtype,"c",2);

	  if (chantab && maxtbl(chantab)>1)
	    pktchan->calib=1.0/atof(gettbl(chantab,1));
	  else
	    pktchan->calib=0.001;
	  
	  pktchan->calper=-1;

	  if (saminterval>0)
	    pktchan->samprate=1.0/saminterval;
	  else
	    pktchan->samprate=0;

	  pushtbl(orbpkt->channels,pktchan);
	  orbpkt->nchannels++;

	  if (verbose)
	    fprintf(stderr,"adding channel %s (%d) %f\n",pktchan->chan,channels,pktchan->data[0]*pktchan->calib);
	  
	  if (chantab)
	    {
	      freetbl(chantab,0);
	      chantab=NULL;
	    }
	}
      
      if (c[0]!='\0')
	++channels;
    }

  freetbl(r,0);

  pktchan = newPktChannel();
	  
  sprintf(pktchan->chan,"memloc");

  pktchan->datasz = 1;
  pktchan->data=malloc(4);
  if (pktchan->data==NULL)
    {
      elog_complain(0,"malloc");
      exit(-1);
    }

  pktchan->data[0]=OldMemPtr;
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,srcparts.src_net,PKT_TYPESIZE);
  strncpy(pktchan->sta,srcparts.src_sta,PKT_TYPESIZE);
  *(pktchan->loc)='\0';
  pktchan->nsamp=1;
  strncpy(pktchan->segtype,"c",2);
  pktchan->calib=1;
  pktchan->calper=-1;
  pktchan->samprate=1.0/saminterval;
  pushtbl(orbpkt->channels,pktchan);
  orbpkt->nchannels++;

  previoustimestamp=t;

  if (previoustimestamp>endtime && endtime>-0.2)
    {
      elog_complain(0,"current packet (%d) timestamp %s exceeds the endtime of %s - all data downloaded, exiting without sending current packet\n",NextMemPtr,strtime(orbpkt->time),strtime(endtime));
      freePkt(orbpkt);
      orbclose(orbfd);
      exit(0);
    }

  if (previoustimestamp<starttime)
    {
      if (verbose)
	elog_notify(0,"current packet (%d @ %s) is prior to starttime (%s) - skipping packet\n",NextMemPtr,strtime(orbpkt->time),strtime(starttime));
    }
  else if ((versioncheck!=-1) && (versioncheck!=prog_vs))
    {
      if (verbose)
	elog_notify(0,"current packet (%d @ %s prog_vs=%d) is not the desired program_vs or array ID (%d) - skipping packet\n",NextMemPtr,strtime(orbpkt->time),prog_vs,versioncheck);
    }
  else
    {
      stuffPkt(orbpkt,generatedSourceName,&t,&packet,&nbytes,&packetsz);
      if (verbose)
	showPkt(0,generatedSourceName,t,packet,nbytes,stderr,PKT_UNSTUFF);
      orbput(orbfd,generatedSourceName,t,packet,nbytes);
    }

  bury();

  freePkt(orbpkt);
  return(0);
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
      elog_complain(0,"dataIntegrityCheck = Checksum error (runningChecksum=%i,checksum=%s\n",runningChecksum,checksum);
      return UNSUCCESSFUL;
    }
  else
    return cells;
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

void getTime(int *fd)
{
  char program[10000];
  int lcv=0;
  double samtime;
  double camtime;
  int year;
  int day;
  Packet *orbpkt;
  PktChannel *pktchan;
  static char *packet=NULL;
  static int packetsz=0;
  int nbytes;
  Srcname srcparts;
  int hr;
  int min;
  int sec;
  char pfs[500];
  char generatedSourceName[500];

  bzero(program,10000);
  getAttention(fd);
  if (write(*fd,"C\r",2)<2)
    {
      elog_complain(1,"get_time() write()");
      close(*fd);
      *fd=-1;
      return;
    }
  samtime=now();
  do
    {
      if (read(*fd,program+lcv,1)<1)
	{
	  elog_complain(1,"getTime read");
	  close(*fd);
	  *fd=-1;
	  return;
	}

      if (program[lcv]=='\r' || program[lcv]=='\n')
	program[lcv]='J';

      lcv++;
    }
  while (program[lcv-1]!='*');
  program[lcv-1]='0';
  sscanf(program,"CJJ Y%2d D%4d T%d:%d:%d",&year,&day,&hr,&min,&sec);
  sprintf(pfs,"20%02d-%03d %d:%02d:%02d %s",year,day,hr,min,sec,camtimezone);
  camtime=str2epoch(pfs);

  if (verbose)
    fprintf(stderr,"time check resp=%s\ttimediff=%d seconds\n",pfs,(int)(samtime-camtime));

  orbpkt=newPkt();
  orbpkt->time=samtime;
  orbpkt->pkttype=suffix2pkttype("MGENC");
  orbpkt->nchannels=1;
  split_srcname(srcname,&srcparts);
  pktchan = newPktChannel();
  strncpy(pktchan->chan,"timeskew",PKT_TYPESIZE);
  pktchan->datasz = 1;
  pktchan->data=malloc(4);
  pktchan->data[0]=(int)(samtime-camtime);
  pktchan->time=orbpkt->time;
  strncpy(pktchan->net,srcparts.src_net,PKT_TYPESIZE);
  strncpy(pktchan->sta,srcparts.src_sta,PKT_TYPESIZE);
  *(pktchan->loc)='\0';
  pktchan->nsamp=1;
  strncpy(pktchan->segtype,"T",2);
  pktchan->calib=1.0;
  pktchan->calper=-1;
  if (jitterenable && samintlogvalid)
    pktchan->samprate=1.0/samintlog;
  else if (interval>0)
    pktchan->samprate=1.0/interval;
  else
    pktchan->samprate=1;
  pushtbl(orbpkt->channels,pktchan);

  stuffPkt(orbpkt,generatedSourceName,&samtime,&packet,&nbytes,&packetsz);

  split_srcname(generatedSourceName,&srcparts);
  strncpy(srcparts.src_subcode,"stat",PKT_TYPESIZE);
  join_srcname(&srcparts,generatedSourceName);

  if (verbose)
    showPkt(0,generatedSourceName,samtime,packet,nbytes,stderr,PKT_UNSTUFF);
  orbput(orbfd,generatedSourceName,samtime,packet,nbytes);

  skewlog=(int)(samtime-camtime);
  skewlogvalid=1;
}

int setMemPtr(int *fd,int location)
{
  char moveCmd[50];
  int moveCmdSize=0;

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
      sleep(2);
      while ((ret=read(*fd,prompt,4))>0)
        {
          if(prompt[0]=='*'||prompt[1]=='*'||prompt[2]=='*'||prompt[3]=='*')
            {
              val&=~O_NONBLOCK;
              fcntl(*fd,F_SETFL,val);
	      if (verbose)
		elog_notify(0,"got attention");
              return 0;
            }
        }

      if (ret<0)
	{
	  perror("getAttention(read)");
	  close(*fd);
	  *fd=-1;
	  return(UNSUCCESSFUL);
	}
    }

  val&=~O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  elog_complain(0,"getAttention() = Could not get attention (prompt[0]=%c,prompt[1]=%c,prompt[2]=%c,prompt[3]=%c)\n",prompt[0],prompt[1],prompt[2],prompt[3]);

  close(*fd);
  *fd=-1;

  return UNSUCCESSFUL;
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

int flushUntil(int *fd,char c)
{
  char prompt=0;
  int loop=0;

  while(loop++<3000)
    {
      prompt=0;
      if (read(*fd,&prompt,1)<1)
        {
          perror("flushUntil(read())");
          close(*fd);
          *fd=-1;
          return UNSUCCESSFUL;
        }
      
      /* fprintf(stderr,"read %c\n",prompt); */

      if(prompt==c)
        return loop;
    }

  elog_complain(0,"flushUntil() = overflow in flushUntil (c=%c)\n",c);
  close(*fd);
  *fd=-1;
  return UNSUCCESSFUL;
}

int readline(int *fd, char *rebuf)
{
  int loop=0;

  while(loop++<5000)
    {
      if (read(*fd,&(rebuf[loop-1]),1)<1)
        {
          perror("read()");
          close(*fd);
          *fd=-1;
          return UNSUCCESSFUL;
        }
      
      if(rebuf[loop-1]=='*')
	{
	  rebuf[loop]='\0';
	  if (verbose)
	    elog_notify(0,"campbell resp: %s\n",rebuf);
	  return loop;
	}
    }

  elog_complain(0,"readline() = overflow in readline (c=%c)\n",rebuf[loop-1]);
  close(*fd);
  *fd=-1;
  return UNSUCCESSFUL;
}

int find_speed(char *val)
{
  int l;

  l=atoi(val);
  if (l==50)
    return B50;
  if (l==75)
    return B75;
  if (l==110)
    return B110;
  if (l==134)
    return B134;
  if (l==150)
    return B150;
  if (l==200)
    return B200;
  if (l==300)
    return B300;
  if (l==600)
    return B600;
  if (l==1200)
    return B1200;
  if (l==1800)
    return B1800;
  if (l==2400)
    return B2400;
  if (l==4800)
    return B4800;
  if (l==9600)
    return B9600;
  if (l==19200)
    return B19200;
  if (l==38400)
    return B38400;
  if (l==57600)
    return B57600;
  if (l==115200)
    return B115200;
  if (l==230400)
    return B230400;
  if (l==460800)
    return B460800;

  elog_complain(0,"speed %s is not supported see: /usr/include/sys/termios.h for supported values. Using default: 9600 bps\n",val);
  return B9600;
}


FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int speed)
{
  FILE *fil;
  struct termios tmp_termios;

  *fd=open(file_name,O_RDWR);
  if (*fd<0)
    {
      perror("open serial port");
      return(NULL);
    }

  if (tcgetattr(*fd,&tmp_termios)<0)
    {
      perror("get serial attributes");
      return(NULL);
    }
  
  *orig_termios=tmp_termios;

  cfsetispeed(&tmp_termios,B9600);
  cfsetospeed(&tmp_termios,B9600);
  tmp_termios.c_lflag &= ~(ECHO|ICANON|IEXTEN|ISIG);



  tmp_termios.c_iflag &= ~(BRKINT|ICRNL|INPCK|ISTRIP|IXON);
  tmp_termios.c_cflag &= ~(CSIZE|PARENB);
  tmp_termios.c_cflag |= CS8;
  tmp_termios.c_oflag &= ~OPOST;

  tmp_termios.c_cc[VMIN]=1;
  tmp_termios.c_cc[VTIME]=0;
  if (tcsetattr(*fd,TCSANOW,&tmp_termios)<0)
    {
      perror("set serial attributes");
      return(NULL);
    }

  fil=fdopen(*fd,"r+");
  
  if (fil==NULL)
    {
      perror("opening serial port");
      return(NULL);
    }

  if (setvbuf(fil,NULL,_IONBF,0)!=0)
    {
      perror("setting ANSI buffering.");
      return(NULL);
    }

  return(fil);
}

int initConnection(char *host, char *port)
{
  int fd;
  unsigned long ina;
  int nconnected=1;
  struct hostent *host_ent;
  struct sockaddr_in addr;
  int val;

  /* fprintf(stderr,"in initConnection host ^%s^ port ^%s^\n",host,port); */

  if ( (ina=inet_addr(host)) != -1 )
    {
      memcpy(&addr.sin_addr, &ina,min(sizeof(ina), sizeof(addr.sin_addr)));
    }
  else
    {
      host_ent = gethostbyname(host);
      
      if ( host_ent == NULL )
	{
	  elog_complain(0,"initConnection = Could not resolve address (host=%s)\n",host);
	  return UNSUCCESSFUL;
	}
      
      memcpy(&addr.sin_addr, host_ent->h_addr,min(host_ent->h_length, sizeof(addr.sin_addr)));
    }
  
  /* make socket */
  if( (fd=socket(AF_INET, SOCK_STREAM, 0)) == -1 )
    {
      elog_complain(0,"initConnection = Could not make socket\n");
      return UNSUCCESSFUL;
    }
  
  /* create address from host ent */
  addr.sin_family = AF_INET;
  addr.sin_port = htons(atoi(port));
  
  nconnected=connect(fd, (struct sockaddr *) &addr, sizeof(addr));
  
  if (nconnected)
    {
      elog_complain(1,"initConnection = connect failed\n");
      close(fd);
      return UNSUCCESSFUL;
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
{ /* defunct */
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

