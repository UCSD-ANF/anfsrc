#include <unistd.h>
#include <stdio.h>
#include <orb.h>
#include <Pkt.h>

#define VERSION "$Revision: 1.11 $"

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

   Written By: Todd Hansen 10/3/2003
   Updated By: Todd Hansen 5/24/2004

*/

void usage(void)
{
  cbanner(VERSION,"[-v] [-V] [-m matchname] [-f statusfile] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char *argv[])
{
  char *statusfile=NULL;
  char *matchname=NULL;
  char *ORBname=":";
  char srcname[60];
  char ch;
  int pktid;
  int lcv;
  double pkttime;
  char *pkt=NULL;
  char buf[256];
  int nbytes;
  int bufsize=0;
  int orbfd;
  int verbose=0;
  int ret;
  struct Packet *Upkt=NULL;
  struct PktChannel *dp;
  char *tempfile, t1[60];
  char *tempfile2, t2[60];
  char *tempfile_holder;
  FILE *FIL;

  elog_init(argc,argv);

  tempfile=tmpnam(t1);
  tempfile2=tmpnam(t2);
  
  while ((ch = getopt(argc, argv, "vVm:o:f:")) != -1)
   switch (ch) 
     {
     case 'V':
       usage();
       exit(-1);
     case 'v':
       verbose=1;
       break;
     case 'o':
       ORBname=optarg;
       break;
     case 'm':
       matchname=optarg;
       break;
     case 'f':
       statusfile=optarg;
       break;
     default:
       fprintf(stderr,"Unknown Argument.\n\n");
       usage();
       exit(-1);
     }

    if ((orbfd=orbopen(ORBname,"r&"))<0)
    {
      perror("orbopen failed");
      return(-1);
    }

    if (matchname)
      if (orbselect(orbfd,matchname)<0)
	{
	  perror("orbselect");
	}
  
    while (1)
      {
	if (orbreap(orbfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize)<0)
	  {
	    perror("orbreap");
	    exit(-1);
	  }

	if ((ret=unstuffPkt(srcname,pkttime,pkt,nbytes,&Upkt)) != Pkt_wf)
	  {
	    fprintf(stderr,"unkown packet type, unstuff returned %d for %s\n",ret,srcname);
	  }
	else
	  {
	    if (verbose)
	      printf("got pkt, channels = %d & srcname = %s\n",Upkt->nchannels,srcname);

	    if (statusfile)
	      {
		sprintf(buf,"cp %s %s",statusfile,tempfile);
		if (system(buf) < 0)
		  {
		    perror("make backup of statusfile failed!");
		  }
		
		for (lcv=0;lcv<Upkt->nchannels;lcv++)
		  {
		    dp=poptbl(Upkt->channels);
		    if (dp->data[dp->nsamp-1]!=TRGAP_VALUE)
		      {
			FIL=fopen(tempfile2,"w+");
			if (FIL == NULL)
			  {
			    perror("opening temp file");
			    fprintf(stderr,"temp file = %s\n",tempfile2);
			    exit(-1);
			  }
			fprintf(FIL,"# net\tsta\tchan\tloc\ttime\t\t\tcalib\t\tsegtype\tsamprate\tvalue\tcalib*value\n");
			if (dp->segtype[0]==0)		      
			  dp->segtype[0]='c';
			fprintf(FIL,"%s\t%s\t%s\t%s\t%f\t%f\t%c\t%f\t%d\t%f\n",dp->net,dp->sta,dp->chan,dp->loc,dp->time+dp->samprate*(dp->nsamp),dp->calib,dp->segtype[0],dp->samprate,dp->data[dp->nsamp-1],dp->calib*dp->data[dp->nsamp-1]);
			fclose(FIL);
			
			sprintf(buf,"egrep -a -v \"^%s\t%s\t%s\t%s\" %s | egrep -a -v \"^#\" >> %s",dp->net,dp->sta,dp->chan,dp->loc,tempfile,tempfile2);
			if (system(buf) < 0)
			  {
			    perror("remove old record in statusfile failed!");
			    exit(-1);
			  }
			
			freePktChannel(dp);
			dp=NULL;
			unlink(tempfile);
			tempfile_holder=tempfile2;
			tempfile2=tempfile;
			tempfile=tempfile_holder;
		      }
		  }

		sprintf(buf,"cp %s %s",tempfile,statusfile);
		if (system(buf) < 0)
		  {
		    perror("make backup of statusfile failed!");
		    exit(-1);
		  }
		unlink(tempfile);
	      }
	    else
	      {
		printf("# net\tsta\tchan\tloc\ttime\tcalib\tsegtype\tsamprate\tvalue\tcalib*value\n");
		for (lcv=0;lcv<Upkt->nchannels;lcv++)
		  {
		    dp=poptbl(Upkt->channels);
		    if (dp->segtype[0]==0)
		      dp->segtype[0]='c';
		    printf("%s\t%s\t%s\t%s\t%f\t%f\t%c\t%f\t%d\t%f\n",dp->net,dp->sta,dp->chan,dp->loc,dp->time+dp->samprate*(dp->nsamp),dp->calib,dp->segtype[0],dp->samprate,dp->data[dp->nsamp-1],dp->calib*dp->data[dp->nsamp-1]);
		    freePktChannel(dp);
		    dp=NULL;
		  }
	      }
	  }

	freePkt(Upkt);
	Upkt=NULL;
      }

}
