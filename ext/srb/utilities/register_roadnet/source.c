#include "source.h"

/*
 * print source obj
 */ 
void printSource(Source *s)
{
  /*
  fprintf(stderr, "srcname=%s; serveraddress=%s; serverport=%s; orb_start=%s;"
                 "datatype=%s; place=%s; owner=%s; desc=%s; srate=%s; srate_lddate=%s;"
                 "band=%s band_lddate=%s calib=%s calib_lddate=%s\n",
    s->srcname, s->serveraddress, s->serverport, s->orb_start, 
    s->datatype, s->place, s->owner, s->desc, s->srate, s->srate_lddate, 
    s->band, s->band_lddate, s->calib, s->calib_lddate);
  */
  fprintf(stderr, "srcname=%s; serveraddress=%s; serverport=%s; orb_start=%s;"
                 "datatype=%s; place=%s; owner=%s; desc=%s; \n",
    s->srcname, s->serveraddress, s->serverport, s->orb_start, 
    s->datatype, s->place, s->owner, s->desc);
}

/* 
 * clear (zero out) source obj
 */
void clearSource(Source *s)
{
  memset(s,0,sizeof(Source));
} 


/*
 * set srcname in source obj s (preallocated)
 */
void setSrcname(Source *s, char *srcname)
{
	strncpy(s->srcname,srcname,sizeof(s->srcname)-1);
}	

/*
 * set serveraddress in source obj s (preallocated)
 */
void setServeraddress(Source *s, char *serveraddress)
{
	strncpy(s->serveraddress,serveraddress,sizeof(s->serveraddress)-1);
}	

/*
 * set serverport in source obj s (preallocated)
 */
void setServerport(Source *s, char *serverport)
{
	strncpy(s->serverport,serverport,sizeof(s->serverport)-1);
}

/*
 * set orb_start in source obj s (preallocated)
 */
void setOrbStart(Source *s, char *orb_start)
{
	strncpy(s->orb_start,orb_start,sizeof(s->orb_start)-1);
}

	
/*
 * set data type field in source obj s (preallocated)
 */
void setDatatype(Source *s, char *datatype)
{
	strncpy(s->datatype,datatype,sizeof(s->datatype)-1);
}

/*
 * set regdate field in source obj s (preallocated)
 */
void setRegdate(Source *s, char *regdate)
{
	strncpy(s->regdate,regdate,sizeof(s->regdate)-1);
}

/*
 * set srbname field in source obj s (preallocated)
 */
void setSrbname(Source *s, char *srbname)
{
	strncpy(s->srbname,srbname,sizeof(s->srbname)-1);
}

/*
 * set owner field in source obj s (preallocated)
 */
void setOwner(Source *s, char *owner)
{
	strncpy(s->owner,owner,sizeof(s->owner)-1);
}

/*
 * set data type field in source obj s (preallocated), based on its srcname
 */
void setDatatypeAuto(Source *s)
{
  char *temp;
  
  if (NULL==s) return;
  if(NULL==(temp=strchr(s->srcname,'/')))
    return;
  setDatatype(s, temp+1);
  
} 

/*
 * set current time as srb registered date
 */
void setRegdateAuto(Source *s)
{
  struct tm now_tm;
  char temp[sizeof(s->regdate)]={0};
  
  time_t now_t=time((time_t *)NULL);
  (void)gmtime_r( &now_t, &now_tm );
  (void)strftime(temp, sizeof(temp)-1, "%Y%m%d", &now_tm);
  setRegdate(s, temp);
} 

/*
 * set srbname field in source obj s (preallocated), based on its:
 * srcname, serveraddress, serverport
 */
void setSrbnameAuto(Source *s)
{
  char *temp, tempbuff[sizeof(s->srbname)]={0};
  snprintf(tempbuff,sizeof(tempbuff),"%s::%s::%s::%s",
    s->owner,s->srcname,s->serveraddress,s->serverport);
  
  /* replace '/' to '_' */
  while(NULL!=(temp=strchr(tempbuff,'/')))
  {
    temp[0]='_';
  }
  setSrbname(s,tempbuff);
} 


/*
 * basic version of the set source obj
 */
void setSourceBasic(Source *s, char *srcname, char *serveraddress, char *serverport,
                char *orb_start, char *owner)
{
  clearSource(s);
  setSrcname(s,srcname);
  setServeraddress(s,serveraddress);
  setServerport(s,serverport);
  setOrbStart(s,orb_start);
  setOwner(s,owner);
  
  /* system time dependent */
  setRegdateAuto(s);
  
  /* the following depending on the previouse set****() */ 
  setDatatypeAuto(s);
  setSrbnameAuto(s);  
}  

/*
 * recalculate the dependent attributes, assuming independent attrbutes are already set
 */
void resetSource(Source *s)
{
  /* system time dependent */
  setRegdateAuto(s);
  
  /* the following depending on the previouse set****() */ 
  setDatatypeAuto(s);
  setSrbnameAuto(s);  
}  

/*
 * construct a SRB path based on source 
 */
char* constructSRBPath(Source *s)
{
  char *path=NULL;
  path=malloc(SIZEOF_SRBPATH);
  
  snprintf(path,SIZEOF_SRBPATH-1,"%s:%s<ORBSELECT>%s</ORBSELECT><ORBWHICH>-13</ORBWHICH>"
          "<ORBTIMEOUT>10</ORBTIMEOUT><ORBNUMOFPKTS>10</ORBNUMOFPKTS>?SHADOW",
          s->serveraddress,s->serverport,s->srcname);
  return path;
}  

/*
 * check if two source objects represent the same source
 * return 1 if same, 0 if not same.
 */
int isSameSource(Source *s1, Source *s2) 
{
  return ( (0==strncmp(s1->srcname,s2->srcname,sizeof(s1->srcname)))&&
           (0==strncmp(s1->serveraddress,s2->serveraddress,sizeof(s1->serveraddress)))&&
           (0==strncmp(s1->serverport,s2->serverport,sizeof(s1->serverport)))&&
           (0==strncmp(s1->datatype,s2->datatype,sizeof(s1->datatype)))
         );
}

/*
 * check if old source object (s1) needed to be updated by new (s2)
 * return 1 if yes, 0 if no.
 */
int isSourceUpdateNeeded (Source *s1, Source *s2)
{
  if (!isSameSource(s1, s2))
  {
    DEBUG("trying to update different source?!");
    exit(-1);
  }
  
  return (!(   (0==strncmp(s1->orb_start,s2->orb_start,sizeof(s1->orb_start)))
             &&(0==strncmp(s1->srbname,s2->srbname,sizeof(s1->srbname)))
             //&&(0==strncmp(s1->owner,s2->owner,sizeof(s1->owner)))
           )
         );
}
