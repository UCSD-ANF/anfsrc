#define VERSION "$Revision: 1.1 $"

#include <unistd.h>
#include <Pkt.h>
#include <orb.h>
#include <stdio.h>
#include "packets.h"

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
   Updated By: Todd Hansen 10/24/2003

*/

char *regex = "(VORBrouter|VORBcomm|VORBmapper|VORBmarker|pforbstat|orbstat)";
regex_t preg;

void query_requests(int orbfd, FILE *fil);

void usage(void)
{
  cbanner(VERSION,"[-v] [-V] [-p parameterfile] [-u UUID] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char *argv[])
{
  char ch;
  int verbose=0;
  char *clientpf="VORBrouter.pf";
  char *ORBname=":";
  int orbfd;
  int UUID=4;
  char buf[80];
  FILE *fil;
  
  elog_init(argc,argv);

  if (regcomp(&preg,regex,REG_NOSUB|REG_EXTENDED))
    {
      perror("regcomp!");
      exit(-1);
    }

  while ((ch = getopt(argc, argv, "vVp:o:u:")) != -1)
   switch (ch) 
     {
     case 'V':
       usage();
       exit(-1);
     case 'v':
       verbose=1;
       break;
     case 'p':
       clientpf=optarg;
       break;
     case 'o':
       ORBname=optarg;
       break;
     case 'u':
       UUID=atoi(optarg);
       break;
     default:
       fprintf(stderr,"Unknown Argument.\n\n");
       usage();
       exit(-1);
     }
  
  orbfd=orbopen(ORBname,"r&");
  while(1)
    {
      if ((fil=fopen(clientpf,"w"))==NULL)
	{
	  perror("open pf");
	  exit(-1);
	}
      
      fprintf(fil,"Version\t%d\n",PKTVERSION);
      fprintf(fil,"Type\t%d\n",8); /* complete description */
      fprintf(fil,"Creation\t%d\n",time(NULL));
      /*      fprintf(fil,"Creation\t%f\n",now());*/
      fprintf(fil,"UUID\t%d\n",UUID);
      fprintf(fil,"lastUUID\t%d\n",UUID);
      
      query_requests(orbfd, fil);
      fprintf(fil,"\n");
      fclose(fil);
      
      sprintf(buf,"./query_neighbors.pl >> %s",clientpf);
      system(buf);
      sprintf(buf,"pf2orb VORBrouter %s",ORBname);
      system(buf);

      sleep(30);
    }
}

void query_requests(int orbfd, FILE *fil)
{
  Orbclient *clients=NULL;
  int nclient=0;
  double time;
  int lcv, cnt;
  Tbl *stbl;
  Tbl *rtbl;
  struct requests *p;
  char *tmp;
  char *tmp2;

  if (orbclients(orbfd,&time,&clients,&nclient)<0)
    {
      perror("orbclients failed");
      exit(-1);
    }
  
  stbl=newtbl(0);
  rtbl=newtbl(0);
  cnt=0;
  for (lcv=0;lcv<nclient;lcv++)
    {
      if (clients[lcv].perm == 'r' && regexec(&preg,clients[lcv].what,0,NULL,0))
	{
	  printf("what %s = %s %s\n",clients[lcv].what,clients[lcv].select,clients[lcv].reject);
	  cnt++;
	  pushtbl(stbl,clients[lcv].select);
	  pushtbl(rtbl,clients[lcv].reject);
	}
      else if (clients[lcv].perm == 'r')
	fprintf(stderr,"rejected %s\n",clients[lcv].what);
    }

  fprintf(fil,"request_cnt\t%d\n",cnt);
  fprintf(fil,"selects\t&Tbl{\n");
  while(tmp=poptbl(stbl))
    {
      if (!strcmp(tmp,""))
	fprintf(fil,"\t(.*");
      else
	fprintf(fil,"\t(%s",tmp);

      tmp2=poptbl(rtbl);
      if (!strcmp(tmp2,""))
	fprintf(fil,")\n");
      else
	fprintf(fil,"&!%s)\n",tmp2);
    }
  fprintf(fil,"}\n");
}

