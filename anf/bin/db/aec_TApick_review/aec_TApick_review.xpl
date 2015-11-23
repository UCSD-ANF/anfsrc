

# aec_TApick_review - subset AEC bulletin for a given time period, reduce tables
#		to include only TA footprint picks and events over a given magnitude
#
# 	subset resultant output origin table to reduce duplicates (via last_origin_lddate)
#		- need to nojoin output assoc/arrival with lat_origin_lddate.origin ?
#
#
# J.Eakins
# 10/2015 
# jeakin@ucsd.edu
#

use Datascope;
use orb ;
use utilfunct;
use strict;
use warnings;

use Getopt::Std;

our ($opt_k,$opt_v,$opt_p,$opt_X);
our (%Pf,$pf,$aecdb,$tadb);
our (@db,@arrival,@assoc,@origin,@netmag,@dbj);
our (@aec,@deployment,@dbas,@dbar,@dbnm,@dbo);
our ($dep,$start,$end,$mag);
our ($dir,$dbname,$nada);
our ($newdb,$outdb,@rm_list,$cmd);

our ($subset,$nrecs);

  my $pgm = $0 ;
  $pgm =~ s".*/"" ;
  elog_init ( $pgm, @ARGV) ;
  $cmd = "\n$0 @ARGV" ;

  elog_notify($cmd) if $opt_v ;

# not sure if I have this argv check correct...
  if ( !getopts('vVXkp:') || ( @ARGV != 0 && @ARGV != 2 ) ) {
	  die ("USAGE: $0 [-v] [-V] [-k] [-p pf] [-X {start end}]   \n");
  }

$opt_v = $opt_v ? "-v" : "" ;

if ($opt_X) {

  elog_notify("Using -X, expert mode, requires a correcly modified aec_TApick_review.pf file\n"); 

  $start = $ARGV[0] ?  $ARGV[0]  : elog_die("Must specify start and end time with -X\n");
  $end   = $ARGV[1] ?  $ARGV[1]  : elog_die("Must specify start and end time with -X\n");

  $pf = $opt_p ?  $opt_p  : "aec_TApick_review" ;

  %Pf 		= getparam ($pf);

  $aecdb	= $Pf{aecdb};
  $dep		= $Pf{deployment};
  $mag		= $Pf{mag_cutoff};


} else {		# will ask for manual input

  elog_notify("Requesting input to build database of AEC picks to review\n") if $opt_v ;

  $aecdb	= ask ( "Input database containing AEC arrival, origin, and netmag):  ") ;
  $dep		= ask ( "Deployment database (/path/to/dbops/db):  "  ) ;
  $mag		= ask ( "Magnitude cutoff (between -2.0 and 10.0):  "  ) ;
  $start	= ask ( "Start date/time :  "  ) ;
  $end  	= ask ( "End   date/time :  "  ) ;

}

# validate input 

$start = validate_input($start); 
$end   = validate_input($end ); 

if ($start >= $end ) {
  elog_die ( sprintf ("Start time, %s, is not less than %s", strtime($start) ,strtime($end) ) ) ;
}

$mag = ($mag >= -2.0 && $mag <= 10.0) ?  $mag : elog_die("Value for magnitude subset, $mag, does not seem valid\n");

print "aecdb:  $aecdb\n" if $opt_v ;
print "deployment:  $dep\n" if $opt_v ;

@aec = dbopen_table ( $aecdb.".arrival", "r" ) ; 
elog_die ("No arrival records in $aecdb") if (!dbquery (@aec,"dbRECORD_COUNT")) ;
@deployment = dbopen_table ($dep.".deployment", "r");  
elog_die ("No records in $dep deployment table") if (!dbquery (@deployment,"dbRECORD_COUNT")) ;

# now that deployment table and aecdb are confirmed, create a descriptor file that points to both

dbfree	(@deployment) ; 
dbclose	(@aec); 

($dir,$dbname,$nada) = parsepath($aecdb);
my $descaecdb = "$dir" . "/{" . $dbname . "}" ;

($dir,$dbname,$nada) = parsepath($dep);
my $descdep = "$dir" . "/{" . $dbname . "}" ;

my $dbpath = $descaecdb . ":" . $descdep ;

dbcreate ("aec_dep", "css3.0", "$dbpath");

# open up the newly referenced database and do some joins


@aec 		= dbopen ( "aec_dep","r" ) or elog_die("Can't open AEC+deployment database: aec_dep");

@arrival	= dblookup ( @aec, "", "arrival", "", "") ; 
@assoc		= dblookup ( @aec, "", "assoc", "", "") ; 
@deployment	= dblookup ( @aec, "", "deployment", "", "") ; 
@origin		= dblookup ( @aec, "", "origin", "", "") ; 
@netmag		= dblookup ( @aec, "", "netmag", "", "") ; 

$subset	= "time>='$start'&&time<='$end'" ;
$nrecs  = dbquery (@origin,"dbRECORD_COUNT");
print STDERR "Number of origin records before time subset: $nrecs\n" if $opt_v ;

@origin	= dbsubset(@origin, $subset);
$nrecs  = dbquery (@origin,"dbRECORD_COUNT");
print STDERR "Number of origin records after time subset: $nrecs\n" if $opt_v ;

@dbj	= dbjoin(@origin, @netmag);
$nrecs  = dbquery (@dbj,"dbRECORD_COUNT");
print STDERR "Number of origin-netmag records before magnitude subset: $nrecs\n" if $opt_v ;

$subset	= "magnitude>=$mag" ;

@dbj	= dbsubset(@dbj, $subset);
$nrecs  = dbquery (@dbj,"dbRECORD_COUNT");
print STDERR "Number of origin-netmag records after magnitude subset: $nrecs\n" if $opt_v ;

@dbj	= dbjoin(@dbj, @assoc);
@dbj	= dbjoin(@dbj, @arrival);
@dbj	= dbjoin(@dbj, @deployment);

$nrecs  = dbquery (@dbj,"dbRECORD_COUNT");
print STDERR "Number of records after all table joins: $nrecs\n" if $opt_v ;

# Create temporary output db called aecfull_START_END_gtMAG

$mag =~ s/\./_/;		 # need to strip any "." from magnitude to make a valid db name

$outdb = "aecfull_" . yearday($start). "_" . yearday($end) . "_gt" . $mag ; 
$newdb = $outdb . "dupes" ;

@dbo = dbseparate(@dbj,'origin');
dbunjoin (@dbo, $newdb);

@dbar = dbseparate(@dbj,'arrival');
dbunjoin (@dbar, $newdb);

@dbas = dbseparate(@dbj,'assoc');
dbunjoin (@dbas, $newdb);

@dbnm = dbseparate(@dbj,'netmag');
dbunjoin (@dbnm, $newdb);

dbclose (@aec);

# call last_origin_lddate
# use $newdb as input create output clean db with no dupes 

$cmd = "last_origin_lddate $opt_v $newdb $outdb";
print "Cmd is: $cmd\n" if $opt_v ;

# error out if $outdb already exists because last_origin_lddate will append to it 
# which defeats the purpose of removing dupes

elog_die ("ERROR!  $outdb\.origin already exists.  Won't append.\n") if (-e "$outdb.origin") ;

&myrun($cmd);

# do funky gymnastics because last_origin_lddate doesn't deal with assoc and arrival tables

$cmd = "/bin/cp $newdb.arrival $outdb.arrival" ; 
myrun("$cmd");
$cmd = "/bin/cp $newdb.assoc   $outdb.assoc"    ;   
myrun("$cmd") ;

$cmd = "dbnojoin $outdb.assoc   origin | dbdelete  -" ;
myrun("$cmd");
$cmd = "dbnojoin $outdb.arrival assoc  | dbdelete  -" ;
myrun("$cmd");


# clean up temp dbs unless -k 
@rm_list = qw(arrival assoc netmag origin);

if (!$opt_k) {
   foreach my $rm_tb (@rm_list) {
     $cmd = "/bin/rm $newdb.$rm_tb " ;
     &myrun("$cmd");
   }
   $cmd = "/bin/rm $newdb" ;
   &myrun("$cmd");
   $cmd = "/bin/rm aec_dep";
   &myrun("$cmd");
}


exit ;


# SUBS below here

sub trim {

        # from Perl Cookbook (O'Reilly) recipe 1.14, p.30

        my @out = @_ ;
        for (@out) {
             s/^\s+//;
             s/\s+$//;
        }
        return wantarray ? @out  : $out[0];
}

sub validate_input {
   my ($time) = @_ ;

   $time = is_epoch_string($time)<1 ? elog_die("Problem with input time: $time.  Make sure you use a valid time string.\n") : str2epoch($time) ;
   return $time ;
}

sub myrun {               # run system cmds safely
    my ( $cmd ) = @_ ;
    system ( $cmd ) ;
    if ($?) {
        elog_complain(0, "$cmd error $? \n") ;
        exit(1); 
    }
}


sub usage {
        print STDERR <<END;


       USAGE: $0 [-v] [-p pf] [-X {start end}]  

END
        exit(1);
}

