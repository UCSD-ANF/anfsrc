/*
 Copyright (c) 2003 - 2006 The Regents of the University of California
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

   This code is designed to interface with the ICE-9 Strain Meter Data logger

   Written By: Todd Hansen 1/3/2003
   Last Updated By: Geoff Davis 1/04/2012
*/

#define VERSION "Revision: 1.20"

#define KEEPALIVE_TIMEOUT 120
#define KEEPALIVE_DELAY_PKTS 8  
#define KEEPALIVE_DELAY_NOPKTS 50

#undef DEBUG

struct rcvd 
{
  short int msgID; /* 2 */
  short int msgSize; /* 8 */
  int seq_num;
} strt;

struct PFOpkt_lnk
{
  short int msgID; /* 1 */
  short int msgSize;
  int seq_num;
  double timestamp; /* timestamp in unix format */
  double samp_rate; /* number of samples per second */
  char net_name[2]; /* network name */
  char sta_name[5]; /* station name */
  char pad; /* padding for alignment on solaris */
  short int num_chan; /* number of channels in the data */
  short int num_samp; /* number of samples */
  unsigned short int chksum; /* 30 bytes to here */
  /* char chan_id[][6];*/ /* channel_id letters (first 3 are channel, next */
                          /*   2 are location code, last char is a pad for */
                          /*   solaris alignment) */
  /* short int sample[][]; */
} pkt;

struct local_data_type
{
  double last_timestamp;
  int last_seqnum;
  int ipaddr;
  int filedes;
  char connected;
  char used;
} local_data;

unsigned short sumit(char *buf, int size, char *buf2, int size2);
int traffic_data(struct PFOpkt_lnk *inpkt, char *buf, int bufsize, int orbfd, char *configfile);
void send_keepalive(struct local_data_type *lc);
int read_reliable(int sock, char *buf, int size);
double get_calib(char *configfile, char *net, char *sta, char *chan);
char get_segtype(char *configfile, char *net, char *sta, char *chan);

void mort(void);

void usage(void);

int main(int argc, char *argv[]);
