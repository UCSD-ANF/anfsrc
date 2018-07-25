c hypoDD.inc: Stores parameters that define array dimensions in hypoDD.
c             Modify to fit size of problem and available computer memory.
c Parameter Description:
c MAXEVE:   Max number of events (must be at least the size of the number 
c           of events listed in the event file)
c MAXDATA:  Max number of observations (must be at least the size of the 
c           number of observations).  
c MAXEVE0:  Max number of events used for SVD. If only LSQR is used, 
c           MAXEVE0 can be set to 2 to free up memory. 
c MAXDATA0: Max number of observations used for SVD. If only LSQR is used, 
c           MAXDATA0 can be set to 1 to free up memory. 
c MAXLAY:   Max number of model layers.
c MAXSTA:   Max number of stations.
c MAXCL:    Max number of clusters allowed. 
	integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0, MAXDATA0, 
     & MAXCL

cc parameters for small size problems (e.g. SUN ULTRA-5, 256 MB RAM)
c         parameter(MAXEVE=   700,    
c     &          MAXDATA=  50000,
c     &          MAXEVE0=  700,	
c     &          MAXDATA0= 20000,	
c     &          MAXLAY=   22,		
c     &          MAXSTA=   16,		
c     &          MAXCL=    25)		

c parameters for medium size problems (e.g. : SUN ULTRA-2, 768 MB RAM)
c       parameter(MAXEVE=  8000,
c     &          MAXDATA=  5000000,
c       parameter(MAXEVE=  10800,
c     &          MAXDATA=  3500000,
c     &          MAXEVE0=  2,	
c     &          MAXDATA0= 1,	
c     &          MAXLAY=   20,		
c     &          MAXSTA=   2400,		
c     &          MAXCL=    50)		

cc parameters for large problems (e.g. SUN BLADE 100, 2 GB RAM):
c      parameter(MAXEVE=   10800,    
c     &          MAXDATA=  3100000,
c     &          MAXEVE0=  50,	
c     &          MAXDATA0= 10000,	
c     &          MAXLAY=   15,		
c     &          MAXSTA=   1300,		
c     &          MAXCL=    100)		

cc parameters for very large problems, with cluster1 enabled (e.g. SUN BLADE 100, 2 GB RAM):
c      parameter(MAXEVE=   16300,    
c     &          MAXDATA=  5000000,
c     &          MAXEVE0=  2,	
c     &          MAXDATA0= 1,	
c     &          MAXLAY=   14,		
c     &          MAXSTA=   16,		
c     &          MAXCL=    1)		

c GOFAR PARAMS
cc parameters for customized problems (e.g. SUN BLADE 100, 2 GB RAM): %FOR GOFAR
      parameter(MAXEVE=   16150,    
     &          MAXDATA=  7000000,
     &          MAXEVE0=  2,	
     &          MAXDATA0= 1,	
     &          MAXLAY=   22,		
     &          MAXSTA=   16,		
     &          MAXCL=    250)		

