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

   Written By: Todd Hansen 1/3/2003
   Updated By: Todd Hansen 6/3/2003
*/

#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include "queue.h"

struct Qdata
{
  char srcname[256];
  int frame_num;
  double time;
  struct Qdata *next;
} *top=NULL;

void queue_clean(void)
{
  struct Qdata *tmp;

  while (top != NULL)
    {
      tmp=top->next;
      free (top);
      top=tmp;
    }
}

int queue_test(char *srcname, int frame_num, double time)
{
  struct Qdata *tmp;

  tmp=top;
  while (tmp != NULL && !strncmp(tmp->srcname,srcname,255))
    tmp=tmp->next;
	 
  if (tmp == NULL)
    {
      tmp=malloc(sizeof(struct Qdata));
      tmp->next=top;
      top=tmp;
      tmp->frame_num=frame_num;
      tmp->time=time;
      strncpy(tmp->srcname,srcname,255);
      return 1;
    }
  else
    {
      if (time > tmp->time)
	{
	  tmp->frame_num=frame_num;
	  tmp->time=time; 
	  return 1;
	}
      else
	return 0;
    }  
}
