
# get arrivals from AEC database for a given orid
# add AK arrivals to TA arrival table
#  
#  J.Eakins
#  2015 

use Getopt::Std ;
use Datascope;
 

if (! getopts(v) || @ARGV != 3 ) {
    print "USAGE:  $0 AKpickdb TAoutputdb orid \n";
    die;
}

$akdb =  $ARGV[0];
$tadb =  $ARGV[1];
$orid =  $ARGV[2];

print STDERR "Adding picks for orid: $orid\n";

@akpicks	= dbopen ("$akdb" , "r") ;
@tapicks	= dbopen ("$tadb" , "r+") ;


@akarrival	= dblookup(@akpicks,  "", "arrival"    , "" , "");
@akorigin 	= dblookup(@akpicks,  "", "origin"     , "" , "");
@akassoc  	= dblookup(@akpicks,  "", "assoc"      , "" , "");

@taarrival	= dblookup(@tapicks,  "", "arrival"    , "" , "");
@tascratch	= dblookup(@taarrival, 0, 0, 0, "dbSCRATCH" ) ;
@tanull   	= dblookup(@taarrival, 0, 0, 0, "dbNULL" ) ;

$subset = "orid=='$orid'" ; 

@akorigin = dbsubset(@akorigin,$subset);

if (dbquery (@akorigin,"dbRECORD_COUNT") != 1) {
  print "Can't find $orid in $akdb\n";
  die;
}

@akj	= dbjoin (@akorigin, @akassoc) ;
@akj	= dbjoin (@akj, @akarrival) ;

@akarrival	= dbseparate(@akj,"arrival");

$narrs	= dbquery (@akarrival,"dbRECORD_COUNT");

print STDERR "Number of arrivals to add from $orid: $narrs\n";

for ($akarrival[3] = 0; $akarrival[3]<$narrs; $akarrival[3]++) {
  ($sta,$chan,$time,$iphase,$deltim,$auth)  = dbgetv(@akarrival, qw (sta chan time iphase deltim auth) );
  push(@arrival_record,
	"sta",		$sta,
	"chan",		$chan,
	"time",		$time,
	"iphase",	$iphase,
	"deltim",	$deltim,
	"auth",		$auth
  ) ; 
	
  eval {dbaddv(@taarrival,@arrival_record) } ;
  if ($@) {
     warn $@;
     elog_complain("Problem adding arrival records:  $sta, $chan, $iphase, time: ". &strydtime($time) . ".\n")  ;
     elog_die("No record added!\n");
  } else {
     elog_notify("Added arrival record to database: $tadb\n")  ;
  }


}

dbclose(@tapicks);
dbclose(@akpicks);

exit; 



 
 
