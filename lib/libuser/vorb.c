#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

#include "stock.h"
#include "Pkt.h"

#include "p_libuser.h"
#include "libuser.h"

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
  /*  char *pkt;*/
};

int stuff_VORB (Packet *pkt, char *srcname, double *opkttime, char **ppp, int *nbytes, int *ppsz)
{
  complain( 0, "Can't stuff VORB packet today\n" );
  return -1;
}

int unstuff_VORB (char *srcname, double ipkttime, char *packet, int nbytes, Packet * pkt)
{
  if (ntohl(((struct datapkt*)packet)->version)!=0)
    {
      complain( 0, "unstuff: version number mismatch in VORB packet\n" );
      return -1;
    }
  if (ntohl(((struct datapkt*)packet)->type)!=7)
    {
      complain( 0, "unstuff: not a VORB data packet\n" );
      return -1;
    }

  return unstuffPkt(((struct datapkt*)packet)->srcname,ipkttime,packet+sizeof(struct datapkt)+sizeof(int)*ntohl(((struct datapkt*)packet)->destcnt),nbytes-sizeof(struct datapkt)+sizeof(int)*ntohl(((struct datapkt*)packet)->destcnt),&pkt);
}

void showPkt_VORB( int pktid, char *srcname, double pkttime, 
		   char *pkt, int nbytes, FILE *file, int mode )
{
  int lcv;

  if (ntohl(((struct datapkt*)pkt)->version)!=0)
    {
      complain( 0, "showPkt: version number mismatch in VORB packet\n" );
      return;
    }
  if (ntohl(((struct datapkt*)pkt)->type)!=7)
    {
      complain( 0, "showPkt: not a VORB data packet\n" );
      return;
    }

  printf("VORB dests (%d): ",ntohl(((struct datapkt*)pkt)->destcnt));
  for (lcv=0;lcv<ntohl(((struct datapkt*)pkt)->destcnt);lcv++)
    {
      printf("%d ",ntohl(*((int*)(pkt+sizeof(struct datapkt)+sizeof(int)*lcv))));
    }
  printf("\nData Pkt:\n");

  showPkt(pktid,((struct datapkt*)pkt)->srcname,pkttime,pkt+sizeof(struct datapkt)+sizeof(int)*((struct datapkt*)pkt)->destcnt,nbytes,file,mode);
}
