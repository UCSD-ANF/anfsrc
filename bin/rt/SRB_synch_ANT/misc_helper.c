#include "misc_helper.h"


void swapInt(int *i1, int *i2)
{
   int temp;
   temp=*i1;
   *i1=*i2;
   *i2=temp;
}

/*
 * Check if an IP address is valid          
 *
 * Input: ip address in string
 *
 * Output: 0 if not valid, 1 if valid
 */
int validateIPAddr(char *ip)
{
  const char validChars[] = "0123456789."; 
  /* check the total length */
  return ( (strlen(ip) >= 7)&&         /* Minimum IP address size */ 
           (strspn(ip, ".") != 1)       /* Leading char should not be '.' */
         );
}

/*
 * Check if an IP address is routable (internet ip)     
 *
 * Input: ip address in string
 *
 * Output: 0 if not routable or operation failed, 1 if otherwise
 *
 * The following address are not routable:
 * Class A 10.0.0.0
 * Class B 172.16.0.0
 * Class C 192.168.0.0 
 */
int isIpAddrRoutable(char *ip)
{
  char *start, *end, *temp;
  int ip_sub1, ip_sub2;
  size_t str_len;
  
  if (!validateIPAddr(ip))
    return 0;
  
  start=ip;
  end=strchr(start,'.');
  str_len=(unsigned int)end-(unsigned int)start;
  if (str_len<1)
    return 0;
  temp=malloc((str_len+1)*sizeof(char));
  strncpy(temp,start,str_len);
  temp[str_len-1]=0;
  ip_sub1=atoi(temp);
  FREEIF(temp);
  if ((ip_sub1==0)||(ip_sub1==10)) /* 0 is not valid, 10 is not routable */
    return 0; 
  
  start=end+1;
  if (strlen(start)<5) 
    return 0;
  end=strchr(start,'.');
  str_len=(unsigned int)end-(unsigned int)start;
  if (str_len<1)
    return 0;
  temp=malloc((str_len+1)*sizeof(char));
  strncpy(temp,start,str_len);
  temp[str_len-1]=0;
  ip_sub2=atoi(temp);
  if ((ip_sub1==172)&&(ip_sub2==16)) /* 172.16.*.* is not routable */
    return 0;
  if ((ip_sub1==192)&&(ip_sub2==168)) /* 192.168.*.* is not routable */
    return 0;
  
  return 1;
}

/* function: setTM 
 *
 * fill structure
 *
 * Input   - time: preallocated tm structure
 *         - rest is selfexplaintary
 *
 * Output  None.          
 */
void setTM (struct tm* time, int year, int mon, int mday, int hour, int min, int sec)
{
  int real_year=year;
  if (real_year>1900) real_year=real_year-1900;
  time->tm_year=real_year;
  time->tm_mon=mon;
  time->tm_mday=mday;
  time->tm_hour=hour;
  time->tm_min=min;
  time->tm_sec=sec;
  time->tm_isdst=-1;
  (void)mktime(time);
}

/* function: sortTM 
 *
 * sort 2 time tm structure
 *
 * Input   - start_time: start time
 *         - end_time: end
 *
 * Output  None.          
 */
void sortTM(struct tm* start_time, struct tm* end_time)
{
    struct tm temp;
    (void)mktime(start_time);(void)mktime(end_time);
    if (mktime(start_time)>mktime(end_time))
    {
      memcpy(&temp, start_time, sizeof(struct tm));
      memcpy(start_time, end_time, sizeof(struct tm));
      memcpy(end_time, &temp, sizeof(struct tm));
    }  
}

/* function: strtrim 
 *
 * trim a string
 *
 * Input   - s: string to be trimmed
 *         
 * Output  start point of trimmed string.
 *
 * NOTE: You must free the result string yourself
 */
char* 
strtrim(char *s)
{
	char *result_start, *result_end;
	int result_buff_len;
	if (!s) 
	{
		DEBUG("NULL string!\n");
	  return NULL;
	}
	/* find start of the string */
	while(*s)
	{
		if (isspace(*s))
			s++;
		else
		  break;
	}
	
	/* create result string */
	result_buff_len=strlen(s)+1;
	result_start=malloc(result_buff_len);
	strcpy(result_start,s);
	
	/* trim the ending white space */
	result_end=result_start+result_buff_len-2;
	while( isspace(*result_end)&&(result_end>=result_start) )
	{
		*result_end='\0';
		result_end--;
  }
  
  return result_start;
}

/*
 * $Source: /opt/antelope/vorb_cvs/vorb/bin/rt/SRB_synch_ANT/misc_helper.c,v $
 * $Revision: 1.1 $
 * $Author: sifang $
 * $Date: 2005/01/11 03:38:10 $
 *
 * $Log: misc_helper.c,v $
 * Revision 1.1  2005/01/11 03:38:10  sifang
 *
 * rewrote SRB style makefile to Antelope style makefile. Also changed its position from Vorb/ext/srb/utilities to here.
 *
 * Revision 1.3  2005/01/08 04:10:57  sifang
 *
 * Add a config file feature, "-r", into the program. So the user could not load his/her own costumized config file with ease. Also added a sample config file with instructions.
 *
 * Revision 1.2  2005/01/07 03:01:17  sifang
 *
 *
 * fixed a bug caused by strncpy. remove the dependency of this program and css.
 *
 *
 */
