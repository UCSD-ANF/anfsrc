
#include <unistd.h>
#include <stdio.h>
#include <orb.h>
#include <Pkt.h>

#include <sys/types.h>
//#include <time.h>
#include <sys/timeb.h>


#define VERSION "$Revision: 1.12 $"
#define PRINT_TIMEOUT   500         // time out for print queue, in milliseconds
#define PRINT_MAXPACKETS    100     // max number of packets to be processed before print out  


//function prototypes
int chan_equals(PktChannel *dp1, PktChannel *dp2);
int update_stored_channels(Tbl *stored_channels, PktChannel *dp_fresh);
void print_channels(Tbl *stored_channels, char *filename);

//global variable


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
   Updated By: Sifang Lu   8/17/2004

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
  Tbl * stored_channels;     // a table of stored channels
  struct timeb *tp;
  //time_t last_print_time, current_time;    // last time print output 
  struct timeb last_print_time, current_time;
  int    time_diff;          // time difference between the two above, in millisecond
  int    packet_counter=0;     // variable tracking how many times a channel data is processed/stored
  int    orbreap_status;     // status returned by orbreap_nd
    
  elog_init(argc,argv);
  
  ftime(&last_print_time);   // init the last print_time
  
  // Process command line parameters
  while ((ch = getopt(argc, argv, "vVm:o:f:")) != -1)
  {
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
    
    stored_channels=newtbl(500);
    
    while (1)
    {
        // read in next packet, and get need packet information for later usage.
        orbreap_status=orbreap_nd(orbfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize);
        
        if (orbreap_status>=0) {}
        else
        if (orbreap_status==-1)
        {
            perror("orbreap_nd");
            exit(-1);
        }
        else
        if (orbreap_status==ORB_INCOMPLETE) 
        {
            if (verbose)
                printf(">>>>> Output to file! orbreap_status=%d\n",orbreap_status);
            if (statusfile)
                print_channels(stored_channels, statusfile);
            
            // reset timer and packet counter
            ftime(&last_print_time);
            packet_counter=0;
            
            if(orbreap(orbfd,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize)<0)
            {
                perror("orbreap");
                exit(-1);
            }
        }
                
        else
        {
            fprintf(stderr,"ERROR: unkown orbreap_nd return value!\n");
            exit(-1);
        }
        
        // filter out non-wave-from packets
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
                for (lcv=0;lcv<Upkt->nchannels;lcv++)
                {
                    dp=poptbl(Upkt->channels);
                    if (dp->data[dp->nsamp-1]!=TRGAP_VALUE)
                    {
                        if (dp->segtype[0]==0)            
                          dp->segtype[0]='c';
                          
                        update_stored_channels(stored_channels, dp);
                        freePktChannel(dp);
                        dp=NULL;
                        
                    }
                 }
            }
            else
            {
                printf("# net\tsta\tchan\tloc\ttime\tcalib\tsegtype\tsamprate\tvalue\tcalib*value\n");
                for (lcv=0;lcv<Upkt->nchannels;lcv++)
                {
                    dp=poptbl(Upkt->channels);
                    if (dp->segtype[0]==0)
                      dp->segtype[0]='c';
                    printf("%s\t%s\t%s\t%s\t%f\t%f\t%c\t%f\t%d\t%f\n",
                        dp->net,dp->sta,dp->chan,dp->loc,
                        dp->time+dp->samprate*(dp->nsamp),dp->calib,
                        dp->segtype[0],dp->samprate,dp->data[dp->nsamp-1],
                        dp->calib*dp->data[dp->nsamp-1]);
                    freePktChannel(dp);
                    dp=NULL;
                }
            }
        }
    
        freePkt(Upkt);
        Upkt=NULL;
        
        ftime(&current_time);
        time_diff=1000.0*(current_time.time-last_print_time.time)+
                    current_time.millitm-last_print_time.millitm;
        if ( (time_diff>=PRINT_TIMEOUT)||(packet_counter>=PRINT_MAXPACKETS) )
        {
            if (verbose)
                printf(">>>>> Output to file! orbreap_status=%d, time_interval=%d millisecond(s), "
                       "packet_counter=%d\n",
                    orbreap_status, time_diff, packet_counter);
            if (statusfile)
                print_channels(stored_channels, statusfile);
            
            ftime(&last_print_time);
            packet_counter=0;
        }
        packet_counter++;
        
    } // end of while

} // end of main

// check if two channel equals
int chan_equals(PktChannel *dp1, PktChannel *dp2)
{
    return ( 
        (strcmp(dp1->net, dp2->net)==0)&&
        (strcmp(dp1->sta, dp2->sta)==0)&&
        (strcmp(dp1->chan, dp2->chan)==0)&&
        (strcmp(dp1->loc, dp2->loc)==0)
           );
}

// update channel list with a fresh channel.  
int update_stored_channels(Tbl *stored_channels, PktChannel *dp_fresh)
{
     int i;
     PktChannel *dp_old;
     for(i=0; i<maxtbl(stored_channels); i++)
     {
        dp_old=(PktChannel *) gettbl(stored_channels,i);
        if ( chan_equals(dp_old, dp_fresh) )
        {
            memcpy(dp_old, dp_fresh, sizeof(PktChannel));
            return 1;      
        }
     }
     dp_old=malloc(sizeof(PktChannel));
     memcpy(dp_old, dp_fresh, sizeof(PktChannel));
     return pushtbl(stored_channels,(char *)dp_old);
}

// print all stored channel data to the file, if filename is null, then it outputs to stdout
void print_channels(Tbl *stored_channels, char *filename)
{
    int i;
    FILE *fp;
    PktChannel *dp;
    
    if (!filename)
    {
        fp=stdout;
    }
    else
    {
        if (NULL==(fp=fopen(filename,"w")))
        {
            fprintf(stderr,"fail to open output file: = %s\n",filename);
            exit(-1);
        }
    }
    // print headers
    fprintf(fp,"# net\tsta\tchan\tloc\ttime\t\t\tcalib\t\tsegtype\tsamprate\tvalue\tcalib*value\n");
    for(i=0; i<maxtbl(stored_channels); i++)
    {
        dp=(PktChannel *) gettbl(stored_channels,i);
        fprintf(fp,"%s\t%s\t%s\t%s\t%f\t%f\t%c\t%f\t%d\t%f\n",
                    dp->net,dp->sta,dp->chan,dp->loc,
                    dp->time+dp->samprate*(dp->nsamp),
                    dp->calib,dp->segtype[0],
                    dp->samprate,dp->data[dp->nsamp-1],
                    dp->calib*dp->data[dp->nsamp-1]
               );
    }
    
    if (filename)
    {
        fclose(fp);
    }
}











                                     