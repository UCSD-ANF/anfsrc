#include <unistd.h>
#include <stdio.h>
#include <strings.h>
#include <ctype.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <termios.h>
#include <sys/time.h>
#include <fcntl.h>
#include <stdio.h>
#include <errno.h>


/* from BRTT Antelope's 4.6 coords.h */
#ifndef M_PI
#define M_PI          3.14159265358979323846
#endif

/* from BRTT Antelope's 4.6 coords.h */
#define deg(r)    ((r) * 180.0/M_PI)
#define rad(d)    ((d) * M_PI/180.0)

#define VERSION "$Revision: 1.3 $"
#define CLOCKTICK 0.79

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

   Written By: Todd Hansen 7/19/2004
   Updated By: Todd Hansen 7/30/2004
*/

double currentyaw=0;
double currentroll=0;
double currentpitch=0;

double ncurrentyaw=0;
double ncurrentroll=0;
double ncurrentpitch=0;

void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios);
/* call to reset serial port when we are done */

FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed);
/* initalize the serial port for our use */

unsigned short checksum(unsigned char *buf, int size);
int find_speed(char *val);
void flushOut(int *fd);
void dr3mxv(double a[], double b[], double c[]);
      
void usage(void)
{            
  fprintf(stderr,"\nVG700CA [-v] [-z] [-w] [-V] [-p serialport] [-d serialspeed] [-l logfile]\n\n%s\n\n\tTodd Hansen\n\tUCSD ROADNet Project\n\ttshansen@ucsd.edu\n\n",VERSION);
}            
       
int main (int argc, char *argv[])
{
  struct termios orig_termios;
  int fd;
  FILE *fil;
  char buf[250];
  int lcv, val, verbose=0;
  int repeat=300;
  int ch, ret, redo;
  unsigned char uch;
  int samcnt=0;
  struct timeval t;
  struct timezone tz;
  char *port="/dev/ttyS3";
  char tbuf[250];
  int serial_speed = B38400;
  char *logfile=NULL;
  FILE *logfd;
  double stime;
  double ctime;
  double cumulativetime;
  int warm=0;
  int dontzero=0;
  short int rollrate;
  short int yawrate;
  short int pitchrate;
  double X[9];
  double Y[9];
  double Z[9];
  double V[3];
  double R[3];
  double rollrated;
  double yawrated;
  double pitchrated;
  double temp;
  double tdiff;
  int samtime;
  int oldtime;
  int firstsam=1;

  while ((ch = getopt(argc, argv, "vVp:d:l:zw")) != -1)
    switch (ch) {
    case 'V': 
      usage();
      exit(-1);
    case 'z': 
      dontzero=1;
      break;  
    case 'w': 
      warm=1;
      break;  
    case 'v': 
      verbose=1;
      break;  
    case 'p': 
      port=optarg;
      break;  
    case 'l': 
      logfile=optarg;
      break;  
    case 'd': 
      serial_speed=find_speed(optarg);
      break;  
    default:  
      fprintf(stderr,"Unknown Argument.\n\n");
      usage();
      exit(-1);
    }         

  printf("VG700CA.c: %s\n",VERSION);

  fil=init_serial(port, &orig_termios, &fd, serial_speed);

  if (fil==NULL)
   {
	perror("serial port open");
	exit(-1);
   }

  if (logfile)
  {
      logfd=fopen(logfile,"w");
      if (logfd==NULL)
      {
	  perror("can't open logfile\n");
	  exit(-1);
      }
  }

  /* 
  write(fd,"A",1);
  read(fd,buf,1);
  write(fd,buf,1);
  */

  tz.tz_minuteswest=0;
  tz.tz_dsttime=0;
  if (gettimeofday(&t,&tz))
  {
      perror("gettimeofday");
      exit(-1);
  }
  stime=t.tv_sec+t.tv_usec/1000000.0;

  if (write(fd,"G",1)<1)
  {
      perror("write(ExitContinousMode)");
      exit(-1);
  }
  
  flushOut(&fd);
  
  *buf='\0';
  lcv=0;
  if (verbose)
      fprintf(stderr,"getting attention...");
  do
  {
      if (lcv == 3)
      {
	  fprintf(stderr,"Failed to wake up the VG700CA on port %s after 3 attempts, exiting!\n",port);
	  exit(-1);
      }
      
      if (write(fd,"R",1)<1)
      {
	  perror("write(wakeup)");
	  exit(-1);
      }

      sleep(1);
      
      val=fcntl(fd,F_GETFL,0);
      val|=O_NONBLOCK;
      fcntl(fd,F_SETFL,val);
      
      if (read(fd,buf,1)<0 && errno!=EAGAIN)
      {
	  perror("read reply");
	  exit(-1);
      }
      
      val&=~O_NONBLOCK;
      fcntl(fd,F_SETFL,val);
      lcv++;
  }
  while (*buf != 'H');
  
  if (verbose)
      fprintf(stderr,"got attention\n");
  
  if (write(fd,"v",1)<1)
  {
      perror("write(version)");
      exit(-1);
  }
  
  lcv=0;
  buf[0]='\0';
  while(lcv<250 && (lcv<1 || (buf[lcv-1]!='V' || lcv==10 || lcv==20)))
  {
      ret=read(fd,buf+lcv,1);
      if (ret<0)
      {
	  perror("read(v response");
	  exit(-1);
      }
      lcv++;
  }
  
  
  if (buf[lcv-1]=='V')
  {
      buf[lcv-1]=0;
      printf("Unit Label: %s\n",buf+1);
  }
  else
  {
      fprintf(stderr,"couldn't get v response (lcv=%d)\n",lcv);
      exit(-1);
  }
  
  if (write(fd,"S",1)<1)
  {
      perror("write(SerialNumberRequest)");
      exit(-1);
  }
  
  if (read(fd,&ch,1)<1)
  {
      perror("read(serialnumber_header)");
      exit(-1);
  }
  
  if (*((unsigned char*)&ch) != 0xFF)
  {
      perror("missed serialnumber header\n");
      exit(-1);
  }
  
  if (read(fd,&ch,4)<4)
  {
      perror("read(serialnumber)");
      exit(-1);
  }
  
  uch=0;
  uch+=((unsigned char*)&ch)[0];
  uch+=((unsigned char*)&ch)[1];
  uch+=((unsigned char*)&ch)[2];
  uch+=((unsigned char*)&ch)[3];
  
  if (read(fd,&ret,1)<1)
  {
      perror("read(serialnumber_checksum)");
      exit(-1);
  }   
  
  if (uch != ((unsigned char*)&ret)[0])
  {
      fprintf(stderr,"serialnumber checksum failed!");
      exit(-1);
  }

  printf("SerialNumber: %u\n",(unsigned int)ntohl(ch));
  
  if (logfile)
  {
      fprintf(logfd,"#VG700CA.c %s\tModel: \"%s\", SN: \"%u\"\n#InitTime: %lf\n",VERSION,buf+1,(unsigned int)ntohl(ch),stime);
      fflush(logfd);
  }
  printf("Please align device with true north prior to starting this program!\n");
  printf("Device warm up phase, 5 min\n");
  
  if (!warm)
      sleep(300);
  else
      printf("Skipping warm up, flag (-w) says device is already warm\n");
  
  if (!dontzero)
  {
      
      if (write(fd,"z3",2)<2)
      {
	  perror("write(ZeroRequest)");
	  exit(-1);
      }
      
      if (read(fd,&ch,1)<1)
      {
	  perror("read(ZeroResponse)");
	  exit(-1);
      }
      
      if (*((unsigned char*)&ch)!='Z')
      {
	  fprintf(stderr,"invalid response to zero command (0x%x)\n",*((unsigned char*)&ch));
	  exit(-1);
      }
      
      printf("Device zeroing phase, 3-4 min (don't move the gyro!)\n");
      
      sleep(240); /* 4 min, since zero is approx 3 min */
      printf("Device zeroing phase complete\n");
  }
  else
      printf("Device zeroing phase, skipped (flag -z says don't zero)\n");
  
  if (write(fd,"c",1)<1)
  {
      perror("write(RequestScaledMode)");
      exit(-1);
  }
	  
  if (read(fd,&ch,1)<1)
  {
      perror("read(ScaledModeResponse)");
      exit(-1);
  }     
  
  if (*((unsigned char*)&ch)!='C')
  {
      fprintf(stderr,"invalid response to scaled mode command (0x%x)\n",*((unsigned char*)&ch));
      exit(-1);
  }

  ch=0;
  flushOut(&ch);
  printf("Entering continous mode, press <CR> to exit\n");
  printf("5\n");
  sleep(1);
  printf("4\n");
  sleep(1);
  printf("3\n");
  sleep(1);
  printf("2\n");
  sleep(1);
  printf("1\n");
  sleep(1);
  printf("mark (reading data)\n");
  samcnt=0;

  if (write(fd,"C",1)<1)
  {
      perror("write(ContinousMode)");
      exit(-1);
  }
  
  if (gettimeofday(&t,&tz))
  {
      perror("gettimeofday");
      exit(-1);
  }
  stime=t.tv_sec+t.tv_usec/1000000.0;
  cumulativetime=0;
  if (logfile)
  {
      fprintf(logfd,"#starttime: %lf gyro internal clocktick %f usec\n",stime,CLOCKTICK);
      fprintf(logfd,"#Columns: realtime\tint.clock\troll rate\tpitch rate\tyaw rate\ttemp\n");
      fprintf(logfd,"#Columns: *realtime\tint.clock\tcumul.roll\tcumul.pitch\tcumul.yaw\tdeltaT\n");
      fprintf(logfd,"#Columns: >realtime\tint.clock\trealroll\trealpitch\trealyaw\tdeltaT\n");
  }

  val=fcntl(0,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(0,F_SETFL,val);

  while (read(0,&ch,1)==-1 && errno==EAGAIN)
  {
      if (read(fd,&buf,18)<18)
      {
	  perror("could not read data\n");
	  if (write(fd,"G",1)<2)
	  {
	      perror("write(ExitContinousMode)");
	      exit(-1);
	  }
	  exit(-1);
      }

      uch=0;
      for (lcv=0;lcv<17;lcv++)
	  uch+=buf[lcv];

      if ((unsigned char)buf[0]!=0xFF && buf[17]!=uch)
      {
	  if ((unsigned char)buf[0]!=0xFF)
	      fprintf(stderr,"data pkt header missing\n");
	  else
	      fprintf(stderr,"checksum failed! 0x%x, expected 0x%x\n",uch,buf[17]);
	  
	  if (write(fd,"G",1)<2)
	  {
	      perror("write(ExitContinousMode)");
	      exit(-1);
	  }
	  exit(-1);
      }

      samcnt++;

      rollrate=buf[1]*256+buf[2];
      pitchrate=buf[3]*256+buf[4];
      yawrate=buf[5]*256+buf[6];
      temp=((buf[13]*256+buf[14])*5/4096.0 - 1.375) * 44.4;
      samtime=buf[15]*256+buf[16];

      rollrated=rollrate*200.0*1.5/(double)(2 << 14);
      yawrated=yawrate*200.0*1.5/(double)(2 << 14);
      pitchrated=pitchrate*200.0*1.5/(double)(2 << 14);

      if (firstsam)
	  firstsam=0;
      else
      {
	  tz.tz_minuteswest=0;
	  tz.tz_dsttime=0;
	  if (gettimeofday(&t,&tz))
	  {
	      perror("gettimeofday");
	      exit(-1);
	  }
	  ctime=t.tv_sec+t.tv_usec/1000000.0;
	  
	  sprintf(buf,"%lf\t%d\t%f\t%f\t%f\t%f\n",ctime,samtime,rollrated,pitchrated,yawrated,temp);
	  if (logfile)
	      fprintf(logfd,buf);
	  if (verbose)
	      printf(buf);

	  tdiff=oldtime-samtime;
	  if (tdiff<0)
	  {
	      tdiff=65535-samtime+oldtime+1;
	  }

	  Z[0]=cos(rad(currentyaw));
	  Z[1]=sin(rad(currentyaw));
	  Z[2]=0;
	  Z[3]=-sin(rad(currentyaw));
	  Z[4]=cos(rad(currentyaw));
	  Z[5]=0;
	  Z[6]=0;
	  Z[7]=0;
	  Z[8]=1;
	  
	  X[0]=1;
	  X[1]=0;
	  X[2]=0;
	  X[3]=0;
	  X[4]=cos(rad(currentroll));
	  X[5]=sin(rad(currentroll));
	  X[6]=0;
	  X[7]=-sin(rad(currentroll));
	  X[8]=cos(rad(currentroll));
	  
	  Y[0]=cos(rad(currentpitch));
	  Y[1]=0;
	  Y[2]=-sin(rad(currentpitch));
	  Y[3]=0;
	  Y[4]=1;
	  Y[5]=0;
	  Y[6]=sin(rad(currentpitch));
	  Y[7]=0;
	  Y[8]=cos(rad(currentpitch));

	  V[0]=rollrated*tdiff*CLOCKTICK/1000000.0;
	  V[1]=pitchrated*tdiff*CLOCKTICK/1000000.0;
	  V[2]=yawrated*tdiff*CLOCKTICK/1000000.0;

	  dr3mxv(X,V,R);
	  dr3mxv(Y,R,V);
	  dr3mxv(Z,V,R);

	  currentyaw+=V[2];
	  currentpitch+=V[1];
	  currentroll+=V[0];
	  sprintf(buf,"^%lf\t%d\t%f\t%f\t%f\n",ctime,samtime,currentroll,currentpitch,currentyaw);
	  if (logfile)
	      fprintf(logfd,buf);
	  if (verbose)
	      printf(buf);

	  ncurrentyaw+=yawrated*tdiff*CLOCKTICK/1000000.0;
	  ncurrentroll+=rollrated*tdiff*CLOCKTICK/1000000.0;
	  ncurrentpitch+=pitchrated*tdiff*CLOCKTICK/1000000.0;
	  sprintf(buf,"*%lf\t%d\t%f\t%f\t%f\t%f\n",ctime,samtime,ncurrentroll,ncurrentpitch,ncurrentyaw,tdiff);
	  cumulativetime+=tdiff*CLOCKTICK/1000000.0;
	  if (logfile)
	      fprintf(logfd,buf);
	  if (verbose)
	      printf(buf);
      }

      oldtime=samtime;
  }
  
  if (write(fd,"G",1)<1)
  {
      perror("write(ExitContinousMode)");
      exit(-1);
  }
  
  val&=~O_NONBLOCK;
  fcntl(0,F_SETFL,val);
  
  printf("Shutting Gyro down, exiting\n\n");
  flushOut(&fd);

  printf("*****************************************************************\n");
  sprintf(buf,"#Summary: Clock Duration: %.2f min\tSample Duration: %.2f min\n",(ctime-stime)/60.0,cumulativetime/60.0);
  printf("%s",buf);
  if (logfd)
      fprintf(logfd,"%s",buf);

  sprintf(buf,"#Summary: Total Movement: %.3f yaw, %.3f pitch, %.3f roll\n",currentyaw,currentpitch,currentroll);
  printf("%s",buf);
  if (logfd)
      fprintf(logfd,"%s",buf);

  sprintf(buf,"#Summary: Rate of Movement: %.2f yaw/hr, %.2f pitch/hr, %.2f roll/hr\n",currentyaw/((ctime-stime)/(60.0*60.0)),currentpitch/((ctime-stime)/(60.0*60.0)),currentroll/((ctime-stime)/(60.0*60.0)));
  printf("%s",buf);
  if (logfd)
      fprintf(logfd,"%s",buf);

  sprintf(buf,"#Summary: Number of Samples: %d rate=%.2f/sec\n",samcnt,samcnt/cumulativetime);
  printf("%s",buf);
  if (logfd)
      fprintf(logfd,"%s",buf);

  if (logfile)
      fclose(logfd);
  destroy_serial_programmer(fil,fd,&orig_termios);
  return(0);
}

void flushOut(int *fd)
{
  char c;
  int val;

  val=fcntl(*fd,F_GETFL,0);
  val|=O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);

  sleep(3);

  while(read(*fd,&c,1)!=-1)
    {
      /* fprintf(stderr,"%c\n",c); */
    }

  val&=~O_NONBLOCK;
  fcntl(*fd,F_SETFL,val);
}


FILE* init_serial(char *file_name, struct termios *orig_termios, int *fd, int serial_speed)
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

  cfsetispeed(&tmp_termios,serial_speed);
  cfsetospeed(&tmp_termios,serial_speed);
  tmp_termios.c_lflag &= ~(ECHO|ICANON|IEXTEN|ISIG);
  tmp_termios.c_iflag &= ~(BRKINT|ICRNL|INPCK|ISTRIP|IXON);
  tmp_termios.c_cflag &= ~(CSIZE|PARENB);
  tmp_termios.c_cflag |= CS8;
  tmp_termios.c_oflag &= ~OPOST;

  tmp_termios.c_cc[VMIN]=1;
  tmp_termios.c_cc[VTIME]=0;
  if (tcsetattr(*fd,TCSANOW,&tmp_termios)<0)
    {
      perror("set serial attributes");
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

void destroy_serial_programmer(FILE *fil, int fd, const struct termios *orig_termios)
{
  if (tcsetattr(fd,TCSANOW,orig_termios)<0)
    {
      perror("get serial attributes");
      exit(-1);
    }

  fclose(fil);
  close(fd);
}

int find_speed(char *val)
{
  int l;

  l=atoi(val);
  if (l==50)
    return B50;
  if (l==75)
    return B75;
  if (l==110)
    return B110;
  if (l==134)
    return B134;
  if (l==150)
    return B150;
  if (l==200)
    return B200;
  if (l==300)
    return B300;
  if (l==600)
    return B600;
  if (l==1200)
    return B1200;
  if (l==1800)
    return B1800;
  if (l==2400)
    return B2400;
  if (l==4800)
    return B4800;
  if (l==9600)
    return B9600;
  if (l==19200)
    return B19200;
  if (l==38400)
    return B38400;
  if (l==57600)
    return B57600;
  if (l==115200)
    return B115200;
  if (l==230400)
    return B230400;
  if (l==460800)
    return B460800;

  fprintf(stderr,"speed %d is not supported see: /usr/include/sys/termios.h for supported values. Using default: 19.2kbps\n",l);
  return B19200;
}

/* provided by  Frank Vernon */
void dr3mxv(a, b, c)
double  a[9], b[3], c[3];
{
         double d[3];
         int i;

         d[0] = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
         d[1] = a[3] * b[0] + a[4] * b[1] + a[5] * b[2];
         d[2] = a[6] * b[0] + a[7] * b[1] + a[8] * b[2];
         for (i = 0; i < 3; i++)  c[i] = d[i];
}
