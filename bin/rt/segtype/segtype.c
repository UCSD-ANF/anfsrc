#include "tr.h"

#define VERSION "$Revision: 1.1 $"

void usage(void)
{
  cbanner(VERSION,"char","Todd Hansen","UCSD ROADNet Project","tshansen@ucsd.edu");
}

int main (int argc, char **argv)
{
	char *s2=NULL,*s3=NULL;
	if (argc!=2)
	  {
	    usage();
	    exit(-1);
	  }

	if (trlookup_segtype(argv[1],&s2,&s3)<0)
			exit(-1);
	printf("%s (%s)\n",s3,s2);
/*free (s2);
	free (s3);*/
}
