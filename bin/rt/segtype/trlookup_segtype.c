#include <strings.h>
#include "tr.h"
#include <unistd.h>

#define VERSION "$Revision: 1.1 $"

void usage(void)
{
  cbanner(VERSION,"[-V] [-u] [-d] char","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char **argv)
{
	char *s2=NULL,*s3=NULL;
	char ch;
	char desc=0, unit=0;
	char *segtype_val;

	while ((ch = getopt(argc, argv, "Vud")) != -1)
	  switch (ch) {
	  case 'd':
	    desc=1;
	    break;
	  case 'u':
	    unit=1;
	    break;
	  case 'V':
	    usage();
	    exit(0);
	    break;
	  default:
	    usage();
	    exit(-1);
	  }

	argc -= optind;
	argv += optind;

	if (argc!=1)
	  {
	    usage();
	    exit(-1);
	  }

	segtype_val=argv[0];

	if (trlookup_segtype(segtype_val,&s2,&s3)<0)
			exit(-1);
	if (!unit && !desc)
	  printf("%s (%s)\n",s3,s2);
	else
	  {
	    if (unit)
	      printf("%s\n",s2);
	    if (desc)
	      printf("%s\n",s3);
	  }
}
