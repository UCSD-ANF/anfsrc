#include <unistd.h>
#include "queue.h"

struct qtype
{
  char srcname[500];
  double pkt_time;
  char originhost[500];
  double timepassed;
  struct qtype *next;
  struct qtype *back;
} *head, *foot;

int num_elems=0;
int MAX_ELEMS;

void qinit(int maxsize)
{
  head=NULL;
  foot=NULL;
  num_elems=0;
  MAX_ELEMS=maxsize;
}

void qfree()
{
  while (head!=NULL)
    {
      foot=head->next;
      free(head);
      head=foot;
    }
  
  num_elems=0;
}

int verify_newpacket(char *srcname, double pkt_time, char *originhost)
{
  struct qtype *tmp;

  tmp=head;
  while (tmp!=NULL)
    {
      if (tmp->pkt_time == pkt_time)
	{
	  if (!strcmp(srcname,tmp->srcname))
	    {
	      return(0);
	    }
	}
      
      tmp=tmp->next;      
    }

  /* dude, we failed to find our pkt. */

  if (num_elems == MAX_ELEMS)
    {
      tmp=foot->back;
      foot->back->next=NULL;
      foot->next=head;
      foot->back=NULL;
      head->back=foot;
      head=foot;
      foot=tmp;
    }
  else
    {
      num_elems++;
      tmp=(void *)malloc(sizeof(struct qtype));
      if (tmp==NULL)
	{
	  perror("malloc");
	  exit (-1);
	}

      if (head==NULL)
	{
	  head=tmp;
	  foot=head;
	  head->back=NULL;
	  head->next=NULL;	  
	}
      else
	{
	  tmp->next=head;
	  tmp->back=NULL;
	  head->back=tmp;
	  head=tmp;
	}
    }


  /* populate */
  strcpy(head->srcname,srcname);
  head->pkt_time=pkt_time;
  strcpy(head->originhost,originhost);
  head->timepassed=time(NULL);

  return(1); /* pass this guy */
}
