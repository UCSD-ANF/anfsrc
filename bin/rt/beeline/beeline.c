#include <unistd.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <termios.h>
#include <sys/time.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/utsname.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <regex.h>
#include <syslog.h>

#define MINSAT 4

unsigned char sumit(char *buf);
int get_pkt_NEMA(FILE *fil, char *buf, int buf_size);
FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd);
double str2num(char *n, double val, int decimal);

main(int argc, char *argv[])
{
 int sockfd, newsockfd, clilen, childpid;
 int fd;
 FILE *logfd;
 struct termios termios;
 char *PORT;
 int con, c;
 int lcv;
 double cur_time;
 char buffer[10002];
 char utc[120];
 char *tbuf;
 char *val;
 FILE *fil;
 char strbuf[200];
 int sol_status=-99;
 int numsat=0;
 int oldsol_status=-99;
 int oldnumsat=0;
 int stime;
 int gpstimestat=0;
 int azimuthstat=0;
 int satastat=0;
 int latstat=0;
 int day=0, month=0, year=0;
 char latitude[80], longitude[80], height[80];
 char latstd[80], longstd[80], hgtstd[80];
 char azimuth[80],pitch[80],azstd[80],pitchstd[80];
 int attype=0, oldattype=0;
 int verbose=0;
 int updatedisplay=0;

 *latitude='\0';
 *longitude='\0';
 *height='\0';
 *latstd='\0';
 *longstd='\0';
 *hgtstd='\0';
 *azimuth='\0';
 *pitch='\0';
 *azstd='\0';
 *pitchstd='\0';


 if (argc < 3 || argc > 4) {
   fprintf(stderr, "usage: %s port logfilename [verbose]\n", argv[0]);
   exit(1);
 }

 if (argc == 4)
     verbose=1;

 PORT=argv[1];

 printf("logfile: %s\nport: %s\n",argv[2],PORT);

 logfd=fopen(argv[2],"w");
 if (logfd == NULL)
 {
     perror("fopen(logfile,\"w\")");
     exit(-1);
 }

 fil=init_serial(PORT,&termios,&newsockfd);

 if (fil == NULL)
 {
     fprintf(stderr,"open %s failed\n",PORT);
     sleep(300);
     exit(-1);
 }    
 
 fflush(fil);
 while ((c=fgetc(fil))!='\n' && c >=0)
     ;
 while ((c=fgetc(fil))!='\n' && c >=0)
     ;
 while ((c=fgetc(fil))!='\n' && c >=0)
     ;
  
 if (c < 0)
 {
     perror("fgetc(serial port)");     
     exit(-1);
 } 

 printf("Waiting for satellites to be acquired.\n");

 /* wait for sync */
 while((c=get_pkt_NEMA(fil,buffer,10000))>0 && (sol_status!=0 || numsat<MINSAT || attype<3))
 {
     /* do something*/
     buffer[c]='\n';
     buffer[c+1]='0';
     if (!strncmp(buffer,"$SATA",5))
     {
	 tbuf=buffer;
	 for (lcv=0;lcv<3 && *tbuf!='\0'; lcv++)
	     val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $SATA from GPS (%s)",buffer);
	     exit(-1);
	 }

	 oldsol_status=sol_status;
	 oldnumsat=numsat;
	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $SATA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 sol_status=atoi(val);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $SATA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 numsat=atoi(val);
	 
	 if (numsat!=oldnumsat)
	     printf("num sats = %d\n",numsat);
	 if (oldsol_status!=sol_status)
	     printf("Solution Status = %d (0= sol computed, 1 = insufficent observations, 2 = no convergence, 3 = Singular A^T PA matrix, 4 = Covariance trace exceeds maximum (trace > 1000m), 5 = Test distance exceeded (maximum of 3 rejectors if distance > 10 km), 6 = Not yet converged from cold start, 7 = height or velocity limit exceeded.)\n",sol_status);
     }
     else if (!strncmp(buffer,"$ATTA",5))
     {
	 tbuf=buffer;
	 for (lcv=0;lcv<6 && *tbuf!='\0'; lcv++)
	     val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA2-6 from GPS (%s)",buffer);
	     exit(-1);
	 }

 	 azimuthstat=time(NULL);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA7 from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(azimuth,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA8 from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(pitch,val,80);

         /* ignore reserved field */	 
	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA9 from GPS (%s)",buffer);
	     exit(-1);
	 }

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA10 from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(azstd,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA11 from GPS (%s) %f",buffer,azstd);
	     exit(-1);
	 }
	 strncpy(pitchstd,val,80);

	 /* ignore reserved field */
	 val=strsep(&tbuf,",");
	 if (tbuf==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA12 from GPS (%s)",buffer);
	     exit(-1);
	 }

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA13 from GPS (%s)",buffer);
	     exit(-1);
	 }

	 oldattype=attype;
	 attype=atoi(val);
	 if (attype!=oldattype)
	 {
	     printf("Atitude Solution Type: %d was %d (0 = no attitude, 1 = good 2D floating attitude solution, 2 = good 2D integer attitude solution, 3= floating ambiguity attiude solution with line bias known, 4 = fixed ambiguity attitude solution with line bias known.)\n",attype,oldattype);
	 }
     }
 }

 printf("Gathering history data! 3min\n");
 stime=time(NULL);
 while((c=get_pkt_NEMA(fil,buffer,10000))>0 && time(NULL)-stime < 180)
 {
     /* do something*/
     buffer[c]='\n';
     buffer[c+1]='\0';
     fprintf(logfd,"%s",buffer);
     updatedisplay=1;

     if (!strncmp(buffer,"$GPZDA",6))
     {
 	 gpstimestat=time(NULL);
	 tbuf=buffer;
	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $GPZDA from GPS (%s)",buffer);
	     exit(-1);
	 }

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $GPZDA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strcpy(utc,val);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $GPZDA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 day=atoi(val);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $GPZDA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 month=atoi(val);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $GPZDA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 year=atoi(val);
     }
     else if (!strncmp(buffer,"$ATTA",5))
     {
	 tbuf=buffer;
	 for (lcv=0;lcv<6 && *tbuf!='\0'; lcv++)
	     val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA2-6 from GPS (%s)",buffer);
	     exit(-1);
	 }

 	 azimuthstat=time(NULL);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA7 from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(azimuth,val,80);
	 printf("az=%s , val=\"%s\" %d %lf\n",azimuth,val,azimuthstat,str2num(azimuth,0,0));

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA8 from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(pitch,val,80);

         /* ignore reserved field */	 
	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA9 from GPS (%s)",buffer);
	     exit(-1);
	 }

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA10 from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(azstd,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA11 from GPS (%s) %f",buffer,azstd);
	     exit(-1);
	 }
	 strncpy(pitchstd,val,80);

	 /* ignore reserved field */
	 val=strsep(&tbuf,",");
	 if (tbuf==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA12 from GPS (%s)",buffer);
	     exit(-1);
	 }

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $ATTA13 from GPS (%s)",buffer);
	     exit(-1);
	 }

	 oldattype=attype;
	 attype=atoi(val);
	 if (attype!=oldattype)
	 {
	     printf("Atitude Solution Type: %d (0 = no attitude, 1 = good 2D floating attitude solution, 2 = good 2D integer attitude solution, 3= floating ambiguity attiude solution with line bias known, 4 = fixed ambiguity attitude solution with line bias known.)\n",attype);
	 }
     }
     else if (!strncmp(buffer,"$POSA",5))
     {
	 tbuf=buffer;
	 for (lcv=0;lcv<3 && *tbuf!='\0'; lcv++)
	     val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }

 	 latstat=time(NULL);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(latitude,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(longitude,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(height,val,80);

	 for (lcv=0;lcv<2 && *tbuf!='\0'; lcv++)
	     val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 
	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(latstd,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(longstd,val,80);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $POSA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 strncpy(hgtstd,val,80);
     }
     else if (!strncmp(buffer,"$SATA",5))
     {
	 satastat=time(NULL);
	 tbuf=buffer;
	 for (lcv=0;lcv<3 && *tbuf!='\0'; lcv++)
	     val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $SATA from GPS (%s)",buffer);
	     exit(-1);
	 }

	 oldsol_status=sol_status;
	 oldnumsat=numsat;
	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $SATA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 sol_status=atoi(val);

	 val=strsep(&tbuf,",");
	 if (val==NULL)
	 {
	     fprintf(stderr,"failed to parse $SATA from GPS (%s)",buffer);
	     exit(-1);
	 }
	 numsat=atoi(val);
	 
	 if (numsat!=oldnumsat)
	     printf("num sats = %d\n",numsat);
	 if (oldsol_status!=sol_status)
	     printf("Solution Status = %d (0= sol computed, 1 = insufficent observations, 2 = no convergence, 3 = Singular A^T PA matrix, 4 = Covariance trace exceeds maximum (trace > 1000m), 5 = Test distance exceeded (maximum of 3 rejectors if distance > 10 km), 6 = Not yet converged from cold start, 7 = height or velocity limit exceeded.)\n",sol_status);

	 if (sol_status!=0 || numsat<4)
	 {
	     if (numsat<4)
		 fprintf(stderr,"Number of sats below 4, not finishing\n");
	     
	     if (sol_status!=0)
		 fprintf(stderr,"Solution Status!=0, not finishing\n");

	     exit(-1);
	 }
     }
     else
	 updatedisplay=0;

     buffer[6]='\0';
     if (verbose && updatedisplay)
	 printf("lat: %s (dev: %s) long %s (dev: %s) height: %s (dev %s) az: %s (dev %s) pitch %s (dev %s) str=%s\n",latitude,latstd,longitude,longstd,height,hgtstd,azimuth,azstd,pitch,pitchstd,buffer); 

 }
 if (gpstimestat==0)
 {
     fprintf(stderr,"did not get $GPZDA string, failing\n");
     exit(-1);
 }
 if (azimuthstat==0)
 {
     fprintf(stderr,"did not get $ATTA string, failing\n");
     exit(-1);
 }
 if (satastat==0)
 {
     fprintf(stderr,"did not get $SATA string, failing\n");
     exit(-1);
 }
 if (latstat==0)
 {
     fprintf(stderr,"did not get $POSA string, failing\n");
     exit(-1);
 }

 /* print summary */

 sprintf(strbuf,"*************************************************************************************\n");
 printf("%s",strbuf);
 fprintf(logfd,"%s",strbuf);

 sprintf(strbuf,"DATE: GPS=%c%c:%c%c:%c%c.%c%c %d/%d/%d UTC (M/D/Y)  -> CPU=%d seconds since epoch\n",utc[0],utc[1],utc[2],utc[3],utc[4],utc[5],utc[7],utc[8],month,day,year,gpstimestat);
 printf("%s",strbuf);
 fprintf(logfd,"%s",strbuf);

 sprintf(strbuf,"LAT: %s (+-%s) LONG: %s (+-%s) HGT: %s m (+-%s)\n",latitude,latstd,longitude,longstd,height,hgtstd);
 printf("%s",strbuf);
 fprintf(logfd,"%s",strbuf);

 sprintf(strbuf,"Azimuth: %s (+-%s) Pitch: %s (+-%s)\n",azimuth,azstd,pitch,pitchstd);
 printf("%s",strbuf);
 fprintf(logfd,"%s",strbuf);

 sprintf(strbuf,"Azimuth Fix: %d Num Sats: %d Solution Status: %d\n",attype,numsat,sol_status);
 printf("%s",strbuf);
 fprintf(logfd,"%s",strbuf);

 if (attype != 4)
 {
     sprintf(strbuf,"Atittude Fix may be sub-optimal: %d (0 = no attitude, 1 = good 2D floating attitude solution, 2 = good 2D integer attitude solution, 3= floating ambiguity attiude solution with line bias known, 4 = fixed ambiguity attitude solution with line bias known.)\n");
     printf("%s",strbuf);
     fprintf(logfd,"%s",strbuf);
 }

 if (numsat<MINSAT)
 {
     sprintf(strbuf,"Number of Satellites sub-optimal: %d (we suggest at least %d)\n",numsat,MINSAT);
     printf("%s",strbuf);
     fprintf(logfd,"%s",strbuf);
 }

 if (sol_status != 0)
 {
     sprintf(strbuf,"Solution Status sub-optimal = %d (0= sol computed, 1 = insufficent observations, 2 = no convergence, 3 = Singular A^T PA matrix, 4 = Covariance trace exceeds maximum (trace > 1000m), 5 = Test distance exceeded (maximum of 3 rejectors if distance > 10 km), 6 = Not yet converged from cold start, 7 = height or velocity limit exceeded.)\n",sol_status);
     printf("%s",strbuf);
     fprintf(logfd,"%s",strbuf);
 }
 
 fclose(logfd);
 fclose(fil);
 close(newsockfd);
}

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd)
{
  FILE *fil;
  struct termios tmp_termios;

  *fd=open(file_name,O_RDWR);
  if (*fd<0)
    {
      perror("open serial port");
      return(NULL);
    }

  if (tcgetattr(*fd,&tmp_termios)<0)
    {
      perror("get serial attributes");
      return(NULL);
    }
  
  *orig_termios=tmp_termios;
             
  cfsetispeed(&tmp_termios,B9600);
  cfsetospeed(&tmp_termios,B9600);
  tmp_termios.c_lflag &= ~(ECHO|ICANON|IEXTEN|ISIG);
  tmp_termios.c_iflag &= ~(BRKINT|ICRNL|INPCK|ISTRIP|IXON);
  tmp_termios.c_cflag &= ~(CSIZE|PARENB);
  tmp_termios.c_cflag |= CS8;
  tmp_termios.c_oflag &= ~OPOST;

  tmp_termios.c_cc[VMIN]=1;
  tmp_termios.c_cc[VTIME]=0;
  if (tcsetattr(*fd,TCSANOW,&tmp_termios)<0)
    {
      perror("get serial attributes");
      return(NULL);
    }

  fil=fdopen(*fd,"r+");
  
  if (fil==NULL)
    {
      perror("opening serial port");
      return(NULL);
    }

  if (setvbuf(fil,NULL,_IONBF,0)!=0)
    {
      perror("setting ANSI buffering.");
      return(NULL);
    }

  return(fil);
}

int get_pkt_NEMA(FILE *fil, char *buf, int buf_size)
{
  char linebuf[4096];
  char sum[3];

  *buf=0;

  while(*buf==0)
    {
      if (fgets(linebuf,4096,fil)==NULL)
	{
	  return(-1);
	}
      
      sprintf(sum,"%X",sumit(linebuf));
      
      if (strncmp(sum,linebuf+strlen(linebuf)-4,2))
	{
	  printf("bad checksum (%s != %s)(%s)\n",sum,linebuf+strlen(linebuf)-4,linebuf);
	}
      else
	{
	  strcpy(buf,linebuf);
	}
    }

  buf[strlen(buf)-2]='\0';
  return(strlen(buf));
}

unsigned char sumit(char *buf)
{
  int lcv, lcv2;
  unsigned char sum;

  lcv=1;
  sum=0;
  lcv2=strlen(buf);
  while(buf[lcv]!='\0' && buf[lcv]!='*')
    {
      sum^=buf[lcv];
      lcv++;
    }
	
  return(sum);
}

double str2num(char *n, double val, int decimal)
{
    if (*n=='\0')
	return(val);
    else if (*n=='.')
	return (str2num(n+1,val,1));
    else
    {	
	val=str2num(n+1,val*10.0+((*n)-48),decimal);
	if (decimal)
	    return(val/10.0);
	else
	    return(val);
		
    }
}
