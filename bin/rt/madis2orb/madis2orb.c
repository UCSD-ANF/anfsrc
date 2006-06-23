/*
* Copyright (c) 2006 The Regents of the University of California
* All Rights Reserved
* 
* Permission to use, copy, modify and distribute any part of this software for
* educational, research and non-profit purposes, without fee, and without a
* written agreement is hereby granted, provided that the above copyright
* notice, this paragraph and the following three paragraphs appear in all
* copies.
* 
* Those desiring to incorporate this software into commercial products or use
* for commercial purposes should contact the Technology Transfer Office,
* University of California, San Diego, 9500 Gilman Drive, La Jolla, CA
* 92093-0910, Ph: (858) 534-5815.
* 
* IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
* DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
* LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF THE UNIVERSITY
* OF CALIFORNIA HAS BEEN ADIVSED OF THE POSSIBILITY OF SUCH DAMAGE.
*
* THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
* CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
* ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF CALIFORNIA MAKES NO
* REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EITHER IMPLIED OR
* EXPRESS, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
* MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT THE USE OF THE
* SOFTWARE WILL NOT INFRINGE ANY PATENT, TRADEMARK OR OTHER RIGHTS.
* 
*  This code was created as part of the ROADNet project.
*  See http://roadnet.ucsd.edu/
* 
*  This code is designed to download data from the MADIS web services portal
*  http://www.madis-fsl.org/madisPublic/cgi-bin/madisXmlPublicDir
* 
*    Code By : Todd Hansen    7-Jun-2006
*    Last Updated By: Todd Hansen 21-Jun-2006 
*
*/

#include <stdio.h>
#include <orb.h>
#include <coords.h>
#include <stock.h>
#include <Pkt.h>

#define VERSION  "madis2orb $Revision: 1.2 $"


/* global variables (config settings) */

char *orbname = ":";
char *netname = "MD"; /* MD for madis? */
char *php_path = "php";
char *madis_grab_pf = "madis2orb.pf";
int repeatinterval=900; /* in seconds */
int verbose=0;

char tfile[5000]; /* temporary file name */
char pffile[5000]; /* temporary file name */
char *pfpkt = NULL;

void showCommandlineUsage (void);
int parseCommandLineOptions (int iArgCount, char *aArgList []);
int cmp_string( char **a, char **b, void *private );
PktChannel* buildChannel(char *sNetname, char *sStaname, char *sChan_Name, int *data, int numsamp, double samprate, double firstsampletime);

int main (int iArgCount, char *aArgList []) 
{
    int ret, s, e, data;
    int orbfd;
    double last=0;
    char buf[5000], *tmpptr;
    char *phpscript=NULL;
    FILE *FOO, *PF;
    Tbl *tbl=NULL;
    Tbl *hittbl=NULL;
    Packet *orbpkt;
    char generatedSourceName[500];
    PktChannel *pktchan=NULL;
    double samprate;
    double timestamp;
    static char *packet=NULL;
    static int packetsz=0;
    int nbytes;
    int first=1;
    Pf *configpf=NULL;

    elog_init(iArgCount, aArgList);

    if (parseCommandLineOptions(iArgCount,aArgList))
	exit(-2);

    /* Output a log header for our program */
    elog_notify (0, "%s\n", VERSION);  

    if (repeatinterval>0)
      samprate=1.0/repeatinterval;
    else if (repeatinterval<0)
      {
	elog_complain(0,"repeat interval < 0 (%d). Invalid parameter.\n\n",repeatinterval);
	showCommandlineUsage();
	exit(-1);
      }
    else
      samprate=0;

    if ((ret=pfupdate(madis_grab_pf,&configpf))<0)
      {
	complain(0,"pfupdate(\"%s\",configpf): failed to open config file.\n",madis_grab_pf);
	exit(-1);
      } 
    else if (ret==1)
      {
	if (first)
	  elog_notify(0,"config file loaded %s\n",madis_grab_pf);
	else
	  elog_notify(0,"updated config file loaded %s\n",madis_grab_pf);
	
	first=0;
	phpscript=pfget_string(configpf,"madis_grab_script");
	if (phpscript == NULL)
	  {
	    elog_complain(0,"failed to read variable madis_grab_script from parameter file %s\n",madis_grab_pf);
	  }
      }

    if (tmpnam(tfile)==NULL)
    {
	elog_complain(0,"tmpnam: failed to create temporary file name\n");
	exit(-1);
    }

    if (tmpnam(pffile)==NULL)
    {
	elog_complain(0,"tmpnam: failed to create temporary file name for pffile\n");
	exit(-1);
    }
    strncat(pffile,".pf",5000);

    if (verbose)
    {
	elog_notify(0,"using %s for temp file.\n",tfile);
	elog_notify(0,"using %s for parameter file.\n",pffile);
	elog_notify(0,"using %s for orb.\n",orbname);
	elog_notify(0,"using %s for network name.\n",netname);
	elog_notify(0,"using %0.1f mins for repeat interval.\n",repeatinterval/60.0);
	elog_notify(0,"using %s for php path executable.\n",php_path);
	elog_notify(0,"using %s for madis2orb parameter file.\n",madis_grab_pf);
    }

    orbfd=orbopen(orbname,"w&");

    do {
	if (last>0 && now()>=last+repeatinterval*2)
	    elog_complain(0,"missing samples. Apparently, we missed at least one complete sample (last sample at %d, current time %d, sample interval %d)\n",last,now(),repeatinterval);

	last=now();

	if (repeatinterval>0 && ((int)now())%repeatinterval>0)
	    {
		if (verbose)
		    elog_notify(0,"sleeping %d seconds (in order to align with repeat interval)",repeatinterval-((int)now())%repeatinterval);
		sleep(repeatinterval-((int)now())%repeatinterval);
	    }

	timestamp=now();
	if (verbose)
	  elog_notify(0,"executing php to grab data\n");
	
	sprintf(buf,"pfecho -q %s madis_grab_script | %s -q > %s",madis_grab_pf,php_path,tfile);
	ret=system(buf);
	if (ret)
	  {
	    elog_complain(0,"calling \"%s\" application failed. system call returned %d\n",buf,ret);
	    return -1;
	  }

	if (verbose)
	  elog_notify(0,"finished executing php\n");

	if ((FOO=fopen(tfile,"r+"))==NULL)
	  {
	    elog_complain(1,"unable to open temporary file (%s):",tfile);
	    return -1;
	  }

	if ((PF=fopen(pffile,"w"))==NULL)
	  {
	    elog_complain(1,"unable to open temporary parameter file (%s):",pffile);
	    return -1;
	  }

	if (unlink(tfile))
	  {
	    elog_complain(1,"can't unlink temp file %s:",tfile);
	    return -1;
	  }

	fprintf(PF,"dls\t&Arr{\n");
	hittbl=newtbl(0);
	if (hittbl==NULL)
	  {
	    elog_complain(1,"newtbl(0) failed\n");
	    exit(-1);
	  }

	orbpkt=newPkt();
	if (orbpkt==NULL)
	  {
	    elog_complain(1,"creating newPkt:");
	    exit(-1);
	  }

	orbpkt->nchannels=0;
	orbpkt->pkttype=suffix2pkttype("MGENC");

	while (fgets(buf,5000,FOO)!=NULL)
	  {
	    tbl=split(buf,'\t');
	    if (maxtbl(tbl)!=11 && maxtbl(tbl)>1)
	      {
		elog_complain(0,"madis response mis-formatted. I expected 11 fields seperated by \\t, but I got %d.\nmadis response=\"%s\"",maxtbl(tbl),buf);
		exit(-1);
	      }
	    else if (maxtbl(tbl)==11)
	      {
		data=atof(gettbl(tbl,7))*1000;
		
		pktchan=buildChannel(netname,gettbl(tbl,1),gettbl(tbl,0),&data,1,samprate,timestamp);
		if (pktchan != NULL)
		  {
		    pushtbl(orbpkt->channels,pktchan);
		    orbpkt->nchannels++;
		  }
		
		tmpptr=gettbl(tbl,1);
		if (!searchtbl(&tmpptr,hittbl,cmp_string,NULL,&s,&e))
		  {
		    /* don't use netname until orbpf2db can split it off */
		    fprintf(PF,"\t%s\t&Arr{\n",gettbl(tbl,1));
		    /*fprintf(PF,"\t%s_%s\t&Arr{\n",netname,gettbl(tbl,1));*/
		    fprintf(PF,"\t\tlat\t%s\n",gettbl(tbl,3));
		    fprintf(PF,"\t\tlon\t%s\n",gettbl(tbl,4));
		    fprintf(PF,"\t\tmadis_source\t%s\n",gettbl(tbl,6));
		    fprintf(PF,"\t}\n");
		    if ((tmpptr=malloc(7))==NULL)
		      {
			elog_complain(1,"malloc failed:");
			exit(-1);
		      }
		    
		    strncpy(tmpptr,gettbl(tbl,1),7);
		    tmpptr[6]='\0';
		    pushtbl(hittbl,tmpptr);
		    sorttbl(hittbl,cmp_string,NULL);
		  }
	      }
	    freetbl(tbl,NULL);
	  }
	
	if (ferror(FOO))
	  {
	    elog_complain(1,"fgets failed on %s:",tfile);
	    return -1;
	  }
	
	freetbl(hittbl,free);
	fprintf(PF,"}\n\n");
	if (gethostname(buf,5000))
	  {
	    elog_complain(1,"gethostname() failed:");
	    exit(-1);
	  }
	fprintf(PF,"hostname\t%s\n",buf);
	
	fclose(PF);
	fclose(FOO);
	
	sprintf(buf,"pf2orb -s %s -p stat %s %s",netname,pffile,orbname);
	ret=system(buf);
	if (ret)
	  {
	    elog_complain(0,"calling %s application failed. system call returned %d\n",buf,ret);
	    return -1;
	  }
	
	if (orbpkt->nchannels>0)
	  {
	    if (stuffPkt(orbpkt,generatedSourceName,&timestamp,&packet,&nbytes,&packetsz)<0)
	      {
		elog_complain(0,"stuffPKt() failed in sendPkt\n");
		exit(-1);
	      }
	    
	    sprintf(buf,"%s/MGENC",netname);
	    if (verbose)
	      showPkt(0,buf,timestamp,packet,nbytes,stderr,PKT_UNSTUFF);
	    
	    if (orbput(orbfd,buf,timestamp,packet,nbytes))
	      {
		elog_complain(0,"orbput() failed in sendPkt\n");
		exit(-1);
	      }
	  }
	
	freePkt(orbpkt);	
    } while (repeatinterval>0);
    
    elog_notify(0, "exiting since repeat interval was %d seconds\n",repeatinterval);
    unlink(tfile);
    unlink(pffile);
    orbclose(orbfd);
    return 0;
}

void showCommandlineUsage (void) 
{
    cbanner (VERSION,"[-V] [-v] [-r interval] [-c netname] [-p madis2orb.pf] [-x pathtophp] [-o orbname]","Todd Hansen", "UCSD ROADNet Project", "tshansen@ucsd.edu");
}

int parseCommandLineOptions (int iArgCount, char *aArgList []) 
{
    int iOption = '\0';

    while ((iOption = getopt (iArgCount, aArgList,"Vvr:c:o:p:x:")) != -1) 
    {    
	switch (iOption)
	{
	    case 'V':
		showCommandlineUsage();
		return -1;
		break;
	    case 'v':
		verbose=1;
		break;
	    case 'r':
		repeatinterval=atoi(optarg);
		break;
	    case 'c':
		netname=optarg;
		break;
	    case 'o':
		orbname = optarg;
		break;
	    case 'p':
		madis_grab_pf = optarg;
		break;
	    case 'x':
		php_path = optarg;
		break;
	    /* Handle invalid arguments */
	    default:
		elog_complain (0, "parseCommandLineOptions(): Invalid commandline argument\n\n");
		showCommandlineUsage ();
		return -1;
	}
    }

    return 0;
 
}

/* from newtbl(3) man page by dan quinlan */
int cmp_string( char **a, char **b, void *private )
{
  return strncmp( *a, *b, 5);
}

PktChannel* buildChannel(char *sNetname, char *sStaname, char *sChan_Name, int *data, int numsamp, double samprate, double firstsampletime)
{
  char *tmp, buf[5000], tmp2[5000];
  Tbl *channametbl=NULL;
  PktChannel *pktchan;
  int lcv;

  /* Send the data to the ORB */
  pktchan=newPktChannel();
  if (pktchan==NULL)
    {
      elog_complain(1,"creating newPktChannel in buildChannel:");
      exit(-1);
    }

  pktchan->datasz=numsamp;
  pktchan->nsamp=numsamp;
	  
  pktchan->data=malloc(4*numsamp);
  if (pktchan->data==NULL)
    {
      elog_complain(1,"malloc failed in buildChannel:");
      exit(-1);
    }
	  
  bcopy(data,pktchan->data,4*numsamp);
  pktchan->time=firstsampletime;
	  
  strncpy(pktchan->net,sNetname,PKT_TYPESIZE);
  strncpy(pktchan->sta,sStaname,6);
  pktchan->sta[6]='\0';
  *(pktchan->loc)='\0';

  if (!strcmp(sChan_Name,"V-TD"))
    {
      strncpy(pktchan->chan,"dewout",8);
      strncpy(pktchan->segtype,"t",2);
      pktchan->calib=0.001;
      for (lcv=0;lcv<numsamp;lcv++)
	pktchan->data[lcv]-=(273.15)*1000;
    }
  else if (!strcmp(sChan_Name,"V-RH"))
    {
      strncpy(pktchan->chan,"Hum-out",8);
      strncpy(pktchan->segtype,"p",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-ALTSE"))
    {
      strncpy(pktchan->chan,"Bar-alt",8);
      strncpy(pktchan->segtype,"P",2);
      pktchan->calib=0.001*0.01;
    }
  else if (!strcmp(sChan_Name,"V-SLP"))
    {
      strncpy(pktchan->chan,"Bar-sea",8);
      strncpy(pktchan->segtype,"P",2);
      pktchan->calib=0.001*0.01;
    }
  else if (!strcmp(sChan_Name,"V-P"))
    {
      strncpy(pktchan->chan,"Bar",8);
      strncpy(pktchan->segtype,"P",2);
      pktchan->calib=0.001*0.01;
    }
  else if (!strcmp(sChan_Name,"V-T"))
    {
      strncpy(pktchan->chan,"Temp-out",8);
      strncpy(pktchan->segtype,"t",2);
      pktchan->calib=0.001;
      for (lcv=0;lcv<numsamp;lcv++)
	pktchan->data[lcv]-=(273.15)*1000;
    }
  else if (!strcmp(sChan_Name,"V-DD"))
    {
      strncpy(pktchan->chan,"wdir",8);
      strncpy(pktchan->segtype,"a",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-FF"))
    {
      strncpy(pktchan->chan,"wind",8);
      strncpy(pktchan->segtype,"s",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-T1H"))
    {
      strncpy(pktchan->chan,"tempOAvg",8);
      strncpy(pktchan->segtype,"t",2);
      pktchan->calib=0.001;
      for (lcv=0;lcv<numsamp;lcv++)
	pktchan->data[lcv]-=(273.15)*1000;    
    }
  else if (!strcmp(sChan_Name,"V-RH1H"))
    {
      strncpy(pktchan->chan,"HumOAvg",8);
      strncpy(pktchan->segtype,"p",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-VIS"))
    {
      strncpy(pktchan->chan,"Visibility",8);
      strncpy(pktchan->segtype,"d",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-VERTVIS"))
    {
      strncpy(pktchan->chan,"VertVisibility",8);
      strncpy(pktchan->segtype,"d",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-PCPRATE"))
    {
      strncpy(pktchan->chan,"RainRate",8);
      strncpy(pktchan->segtype,"s",2);
      pktchan->calib=0.001*0.001;
    }
  else if (!strcmp(sChan_Name,"V-DDGUST"))
    {
      strncpy(pktchan->chan,"windgstd",8);
      strncpy(pktchan->segtype,"a",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-PCP24H"))
    {
      strncpy(pktchan->chan,"RainFall",8);
      strncpy(pktchan->segtype,"d",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-DD1H"))
    {
      strncpy(pktchan->chan,"wdir-avg",8);
      strncpy(pktchan->segtype,"a",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-FF1H"))
    {
      strncpy(pktchan->chan,"wind-avg",8);
      strncpy(pktchan->segtype,"s",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-FFGUST"))
    {
      strncpy(pktchan->chan,"windgust",8);
      strncpy(pktchan->segtype,"s",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-SST"))
    {
      strncpy(pktchan->chan,"Temp-sea",8);
      strncpy(pktchan->segtype,"t",2);
      pktchan->calib=0.001;
      for (lcv=0;lcv<numsamp;lcv++)
	pktchan->data[lcv]-=(273.15)*1000;    
    }
  else if (!strcmp(sChan_Name,"V-WAVEHT"))
    {
      strncpy(pktchan->chan,"waveht",8);
      strncpy(pktchan->segtype,"d",2);
      pktchan->calib=0.001;
    }
  else if (!strcmp(sChan_Name,"V-WAVEPER"))
    {
      strncpy(pktchan->chan,"waveper",8);
      strncpy(pktchan->segtype,"T",2);
      pktchan->calib=0.001;
    }  
  else if (!strcmp(sChan_Name,"V-RIVSTG"))
    {
      strncpy(pktchan->chan,"riverstg",8);
      strncpy(pktchan->segtype,"d",2);
      pktchan->calib=0.001;
    }  
  else if (!strcmp(sChan_Name,"V-SOLRAD"))
    {
      strncpy(pktchan->chan,"solar",8);
      strncpy(pktchan->segtype,"W",2);
      pktchan->calib=0.001;
    }  
  else if (!strcmp(sChan_Name,"V-DSRDINS"))
    {
      strncpy(pktchan->chan,"solar",8);
      strncpy(pktchan->segtype,"W",2);
       pktchan->calib=0.001;
    }  
  else if (!strcmp(sChan_Name,"V-FUELM"))
    {
      strncpy(pktchan->chan,"FuelMois",8);
      strncpy(pktchan->segtype,"p",2);
      pktchan->calib=0.001;
    }  
  else if (!strcmp(sChan_Name,"V-FUELT"))
    {
      strncpy(pktchan->chan,"FuelTemp",8);
      strncpy(pktchan->segtype,"t",2);
      pktchan->calib=0.001;
      for (lcv=0;lcv<numsamp;lcv++)
	pktchan->data[lcv]-=(273.15)*1000;  
    }  
  else
    {
      elog_complain(0,"channel name not found: \'%s\' from station %s\n",sChan_Name,sStaname);
      freePktChannel(pktchan);
      return NULL;
    }

  pktchan->chan[8]='\0';
  pktchan->calper=-1;
  pktchan->samprate=samprate;

  if (verbose)
    elog_notify(0,"added channel %s: %d samples\n",sChan_Name,numsamp);

  return pktchan;
}
