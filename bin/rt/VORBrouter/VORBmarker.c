#include <unistd.h>
#include <Pkt.h>
#include <orb.h>
#include <sys/file.h>
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

   Written By: Todd Hansen 10/14/2003
   Updated By: Todd Hansen 10/24/2003

*/

#define VERSION "$Revision: 1.1 $"

void usage(void)
{
  cbanner(VERSION,"[-v] [-V] [-t routetable] [-u UUID] [-o $ORB]","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int UUID=4;
int verbose=0;
int orbfd_out;
int orbfd_in;
char *VORBcomm="VORB_routetable.pf";

Tbl* checksrcname(char *srcname);

int main (int argc, char *argv[])
{
  char ch, *c;
  char *ORBname=":";
  int pktid; 
  char srcname[ORBSRCNAME_SIZE+1];
  double pkttime;
  char *pkt=NULL, *pkt2=NULL, *id;
  char *state=NULL;
  int nbytes;
  int ret;
  int lcv;
  int bufsize=0;
  Srcname parts;
  Tbl *dsttbl;

  elog_init(argc,argv);

  while ((ch = getopt(argc, argv, "vVo:t:s:u:")) != -1)
   switch (ch) 
     {
     case 'V':
       usage();
       exit(-1);
     case 'v':
       verbose=1;
       break;
     case 't':
       VORBcomm=optarg;
       break;
     case 'o':
       ORBname=optarg;
       break;
     case 's':
       state=optarg;
       break;
     case 'u':
       UUID=atoi(optarg);
       break;
     default:
       fprintf(stderr,"Unknown Argument.\n\n");
       usage();
       exit(-1);
     }

  if (verbose)
    {
      fprintf(stderr,"VORBmarker version %s, UUID=%d\n",VERSION,UUID);
    }

  orbfd_in=orbopen(ORBname,"r&");
  orbfd_out=orbopen(ORBname,"w&");

  if (state)
    {
      ret=exhume(state,NULL,0,NULL);
      if (ret==0)
	{
	  fprintf(stderr,"no state file, resurrection unsuccessful\n");
	}
      else if (ret==1)
	{
	  fprintf(stderr,"resurrection successful\n");
	}
      else
	{
	  fprintf(stderr,"resurrection problematic, exhume returned %d\n",ret);
	}
      
      if (orbresurrect(orbfd_in,&pktid,&pkttime))
	fprintf(stderr,"orb repositioning failed, variable not found\n");
      else
	fprintf(stderr,"orb repositioned %d @ %.2f\n",pktid,pkttime);
    }

  if (orbfd_in<0 || orbfd_out<0)
    {
      perror("connect to orb failed!");
      exit(-1);
    }

  orbreject(orbfd_in,"(/pf/VORBrouter|.*/VORB.*)");

  ch=0;
  while(1)
    {
      if (orbreap(orbfd_in,&pktid,srcname,&pkttime,&pkt,&nbytes,&bufsize))
	{
	  perror("orbreap");
	  exit(-1);
	}
      srcname[ORBSRCNAME_SIZE]=0;
      dsttbl=checksrcname(srcname);
      
      pkt2=malloc(nbytes+maxtbl(dsttbl)*sizeof(int)+sizeof(struct datapkt));
      ((struct datapkt*)pkt2)->version=htonl(PKTVERSION);
      ((struct datapkt*)pkt2)->type=htonl(7);
      ((struct datapkt*)pkt2)->id=htonl(pktid);
      ((struct datapkt*)pkt2)->dsize=htonl(nbytes);
      ((struct datapkt*)pkt2)->pkttime=pkttime;
      strncpy(((struct datapkt*)pkt2)->srcname,srcname,ORBSRCNAME_SIZE);
      fprintf(stderr,"psrc=%s\n",srcname);
      split_srcname(srcname,&parts);
      if (parts.src_subcode[0]=='\0')
	{
	  strncpy(parts.src_subcode,parts.src_suffix,PKT_TYPESIZE);
	}
      strncpy(parts.src_suffix,"VORB",PKT_TYPESIZE);
      join_srcname(&parts,srcname);
      strncpy(((struct datapkt*)pkt2)->srcname_cur,srcname,ORBSRCNAME_SIZE);
      ((struct datapkt*)pkt2)->destcnt=htonl(maxtbl(dsttbl));
      ((struct datapkt*)pkt2)->pkttime=pkttime;
      for (lcv=0;lcv<maxtbl(dsttbl);lcv++)
	{
	  id=gettbl(dsttbl,lcv);
	  *(int*)(pkt2+sizeof(struct datapkt)+lcv*sizeof(int))=htonl(atoi(id));
	}

      bcopy(pkt,pkt2+sizeof(struct datapkt)+lcv*sizeof(int),nbytes);

      if (orbput(orbfd_out,srcname,pkttime,pkt2,nbytes+lcv*sizeof(int)+sizeof(struct datapkt)))
	{
	  perror("orbput");
	  exit(-1);
	}
      free(pkt2);
      fprintf(stderr,"src=%s\n",srcname);

      ch++;
      if (ch%5==0)
	bury();
    }
}

void freet(Tbl *t)
{
  freetbl(t,free);
}

Tbl* checksrcname(char *srcname)
{
  static Arr *quickarr=NULL;
  static Pf *pf=NULL;
  Tbl *buf=NULL;
  int fd, ret;
  int regmatch;
  Arr *arrs;
  Tbl *orbtbl;
  char *id=NULL, *regex, *ch;
  Tbl *retbl=NULL;
  void *req=NULL;
  void *regtbl=NULL;
  regex_t re;

  fd=open(VORBcomm,O_RDONLY);
  if (fd<0)
    {
      perror("open(route table for locking)");
      exit(-1);
    }

  if (flock(fd,LOCK_SH)<0)
    {
      perror("flock(fd,LOCK_SH)");
      exit(-1);
    }
  
  if ((ret=pfupdate(VORBcomm,&pf))>0)
    {
      if (verbose)
	{
	  fprintf(stderr,"new route table loaded %d\n",time(NULL));
	}
      
      if (flock(fd,LOCK_UN)<0)
	{
	  perror("flock(fd,LOCK_UN)");
	  exit(-1);
	}
      
      if (quickarr!=NULL)
	freearr(quickarr,freet);
      quickarr=newarr(0);
    }
  else if (flock(fd,LOCK_UN)<0)
    {
      perror("flock(fd,LOCK_UN)");
      exit(-1);
    }
  else if (ret<0)
    {
      perror("pfupdate()");
      exit(-1);
    }
  close(fd);

  if ((buf=getarr(quickarr,srcname))==NULL)
    {
      buf=newtbl(0);
      if (pfget(pf,"requests",&req)!=PFARR)
	{
	  perror("bogus pf format");
	  exit(-1);
	}

      orbtbl=pfkeys(req);
      if (orbtbl==NULL)
	{
	  perror("pfkeys");
	  exit(-1);
	}

      while(id=poptbl(orbtbl))
	{
	  if (pfget(req,id,&regtbl)!=PFARR)
	    {
	      perror("pfget(orbtbl), misformated");
	      exit(-1);
	    }

	  retbl=pfget_tbl(regtbl,"regex");
	  regmatch=0;
	  while((regex=poptbl(retbl))  && regmatch==0)
	    {
	      /*fprintf(stderr,"regex=%s\n",regex);*/
	      if (regcomp(&re,regex,REG_EXTENDED|REG_NOSUB)!=0)
		{
		  perror("regcomp");
		  fprintf(stderr,"compilation error on regex %s, ignoring\n",regex);
		}
	      else
		{
		  if (regexec(&re,srcname,0,NULL,0)==0)
		    {
		      fprintf(stderr,"matched (%s==%s)\n",srcname,regex);
		      regmatch=1;
		    }
		  regfree(&re);
		}
	    }
	  
	  if (regmatch==1)
	    {
	      ch=malloc(strlen(id)+1);
	      strcpy(ch,id);
	      pushtbl(buf,ch);
	      fprintf(stderr,"%s adding dst %s\n",srcname,id);
	    }
	}
      setarr(quickarr,srcname,buf);
      freetbl(orbtbl,0);
      freetbl(retbl,0);
    }
  else if (verbose)
    fprintf(stderr,"short-circuit lookup success, %d table size\n",cntarr(quickarr));

  return(buf);
}
