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
   Updated By: Todd Hansen 10/29/2003

*/

#define PKTVERSION 0

struct keepalive
{
  int version; /* 0 */
  int type; /* 5 */ /* 6 = reply */
  int id;
  int UUID;
};

struct rmod
{
  int version; /* 0 */
  int type; /* 1 = complete, 2 = add, 3 = delete */
  unsigned int checksum;
  int UUID;
  double createtime;
  int lastUUID;
  int neighcnt;
  int requestcnt;
  /*struct requests *req;*/
  /*struct neighbors *neigh;*/
};

struct ack
{
  int version; /* 0 */
  int type; /* 4 */
  int id;
};

struct datapkt
{
  int version; /* 0 */
  int type; /* 7 */
  int id;
  int dsize;
  int destcnt;
  char srcname_cur[ORBSRCNAME_SIZE];
  char srcname[ORBSRCNAME_SIZE];
  /*  int *destUUID;*/
  /* in between vorbrouter double pkttime is here */
  /*  char *pkt;*/
};

struct ctlpkt
{
  int version; /* 0 */
  int type; /* 8 */
  int id;
  int dsize;
  /*char *pkt;*/
};

struct routepkt
{
  int version; /* 0 */
  int type; /* 9 */
  int UUID; 
  int lastUUID;
  int creation;
  int changenum;
  /* array of selects */
  /* array of routes */
  /* more verbose hops */
};

struct head
{
  int version;
  int type;
  int id;
};

