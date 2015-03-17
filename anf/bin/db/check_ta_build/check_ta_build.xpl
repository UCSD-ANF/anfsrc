
use strict ;
#use warnings; 
use Datascope ;
use orb ;
use archive ;
use Getopt::Std ;
use utilfunct ; 

our ($opt_1, $opt_2, $opt_3, $opt_4, $opt_5, $opt_p, $opt_n, $opt_t, $opt_V, $opt_v);
our (@db, @dbnetwork, @dbcalibration, @dbstage, @dbsite, @dbsnet, @dbschanloc, @dbdlsensor);
our (@dbcalib_g);
our (@BHdbstage,@HNdbstage);
our (@HH, @HN, @dlsensorq330);
our ($dlsensorsub, $BHstagesub, $HNstagesub, $calibsub );
our (@allstas,@pfstas,@hhstas,@missinghh,@hnstas,@missinghn_meta,@missinghn_q330,@q330_epi_dl);
our (@missingdb, @missingpf, @missinghh_meta,@missinghh_q330,@q330_bb100_dl);
our (%db_epiBH_dl,%db_epiHN_dl,%q330_sn_dl);

our (@TAnet, @TAsnet, @TAcalibration);
our ($csta, $cchan, $ctime, $cendtime); 

my ($dbin,$sta,$dl,$sn,$targetname);
my ($row, $nrecs, $BHnrecs, $HNnrecs, $badsta, $baddlsta, $mytime);
my ($key, $error, $errorhh, $errorhn, $errorq330, $errorstart, $testfails) = () ;

my (%Pf,@skipstas);

my (%inverted) ;

my ( $nbytes, $orb, $orbname, $packet, $pkt, $pktid, $reject,$select,$source,$target );
my ( $result, $srcname, $stime, $time, $t );

my ($Pgm,$cmd);

$Pgm = $0 ;
$Pgm =~ s".*/"" ;
$cmd = "\n$0 @ARGV" ;

$t = now();

if (! getopts('12345p:t:nvV')  || (@ARGV != 1 )) {
   print STDERR "getopts or number of arguments failure.\n";
   &usage;
}

$dbin		= $ARGV[0]  ;

if ($opt_t ) {
  $targetname = $opt_t;
} else {
  $targetname = ".*";
}

if (!$opt_1 && !$opt_2 && !$opt_3 && !$opt_4 && !$opt_5) {  # specific test not selected, run all
  $opt_1 = 1 ;
  $opt_2 = 1 ;
  $opt_3 = 1 ;
  $opt_4 = 1 ;
  $opt_5 = 1 ;
}

%Pf = getparam( $opt_p || $Pgm );
$select = $Pf{select_packets} ;
$reject = $Pf{reject_packets} ;
@skipstas = $Pf{skip_starttime_check} ;

print "select => ($select)\n" if $opt_V ;
print "reject => ($reject)\n" if $opt_V ;


@db             = dbopen($dbin,"r") ;
@dbnetwork	= dblookup(@db,"","network","","");
@dbcalibration	= dblookup(@db,"","calibration","","");
@dbsite		= dblookup(@db,"","site","","");
@dbstage	= dblookup(@db,"","stage","","");
@dbsnet		= dblookup(@db,"","snetsta","","");
@dbschanloc	= dblookup(@db,"","schanloc","","");
@dbdlsensor	= dblookup(@db,"","dlsensor","","");

$dlsensorsub	= "endtime=='9999999999.99900'||endtime>='$t'" ;

@dbdlsensor	= dbsubset(@dbdlsensor,$dlsensorsub) ;

my $HNsub	= "($dlsensorsub)&&chan=='HNZ' " ;
my $HHsub	= "($dlsensorsub)&&chan=='HHZ' " ;

@HN		= dbsubset(@dbstage, $HNsub) ;
@HN		= dbsort(@HN, "-u", "sta"); 

@HH		= dbsubset(@dbstage, "$HHsub") ;
@HH		= dbsort(@HH, "-u", "sta"); 

$nrecs	= dbquery(@dbsite,dbRECORD_COUNT);
print "Number of records in site table: $nrecs\n";

my $sitesub	= "offdate=='-1'||offdate>=yearday($t)" ;
@dbsite		= dbsubset(@dbsite,$sitesub) ;

$nrecs	= dbquery(@dbsite,dbRECORD_COUNT);
print "Number of active sites: $nrecs\n";

foreach $row (0..$nrecs-1) {
  $dbsite[3] = $row;
  ($sta) = dbgetv(@dbsite,qw(sta));
  push(@allstas,$sta);
}

$nrecs	= dbquery(@dbdlsensor,dbRECORD_COUNT);

foreach $row (0..$nrecs-1) {
  $dbdlsensor[3] = $row;
  my ($q330sn) = dbgetv(@dbdlsensor,qw(dlident));
  push(@dlsensorq330,$q330sn);
}

&collect_orbstash if ($opt_1 || $opt_2 || $opt_3 || $opt_5) ;

# 
#  Check #1 - Check for number of open stations in metadata vs. number of open stations in q3302orb parameter files
#

if ($opt_1) {		# check that number of open stations in metadata corresponds to number of stations in q3302orb pf files

# This is similar to check_q330pf_db, but no tie in to wfs

print "\nCheck #1  --  started  -- \n";

# all active stations are in @allstas 
# all q330sn+dlsta are available in %q330_sn_dl , stalist in @pfstas

@pfstas = keys(%q330_sn_dl); 

printf "Operational stas in db:  %s\n", $#allstas+1 ;
printf "Operational stas in pfs: %s\n", $#pfstas+1  ;

@missingdb	 = remain(\@pfstas,\@allstas);
@missingpf	 = remain(\@allstas,\@pfstas);

if ($#missingdb >= 0) { 	# there are some stations missing open record descriptions in metadata
				# or being collected when they should be removed from pf
  foreach (@missingdb) {
     print "  $_ is open in database, but missing from q3302orb.pf files \n";
     $error++;
  }
} 

if ($#missingpf >= 0) { 	# there are some stations missing from collection in pf which
				# have open records in db
  foreach (@missingpf) {
     print "  $_ is requested for collection via q3302orb.pf files, but closed in metadata\n";
     $error++;
  }
} 

   if (!$error) {
        print "\nCheck #1  **  PASSED  **  No mismatch between open stations in db and q3302orb pfs\n\n";	 
   } else {
        print "\nCheck #1  **  FAILED  **  Clean-up open records/acquisition differences \n\n";	 
	$testfails++;
   }
}

#
# Check #2 - all stations with HH channels (100sps) collected have HH described in metadata
#

if ($opt_2) { 	

# For TA, not all stations collect 100sps HH...
# need to modify this check to only check for proper template <-> metadata availability


print "Check #2  --  started  -- \n";
   $nrecs	= dbquery(@HH,dbRECORD_COUNT);

   foreach $row (0..$nrecs-1) {
     $HH[3] = $row;
     ($sta) = dbgetv(@HH,qw(sta));
     push(@hhstas,$sta);
   }

# check that missinghh is -1 length (passes check)
   printf "Total number of stations : %s\n", $#allstas if $opt_V ;
   printf "Total number of stations with HH channels in metadata: %s\n", $#hhstas if $opt_V ;
   printf "Total number of stations with HH channels collected in q3302orb: %s\n", $#q330_bb100_dl if $opt_V ;


   @missinghh_meta = remain(\@q330_bb100_dl,\@hhstas);
   @missinghh_q330 = remain(\@hhstas,\@q330_bb100_dl);

   if ($#missinghh_meta >= 0) { 	# there are some stations missing HH channel descriptions in metadata)
     foreach (@missinghh_meta) {
        print "  $_ is missing an HH channel description but collecting HH data\n";
        $errorhh++;
     }
   } 

   if ($#missinghh_q330 >= 0) { 	# there are some stations with HH channel descriptions in metadata not collecting HH in acq)
     foreach (@missinghh_q330) {
        print "  $_ is not collecting HH data via q3302orb, but should be \n";
        $errorhh++;
     }
   } 

   if (!$errorhh) {
      print "\nCheck #2  **  PASSED  ** All stations have HH channels described\n\n";	 
   } else {
      print "\nCheck #2  **  FAILED  **  Some stations have HH description missing \n\n";	 
      $testfails++;
   }

}

#
# Check #3a - all HN channels use epi datalogger template 
#


if ($opt_3) {

print "Check #3  --  started  -- \n";


   $nrecs	= dbquery(@HN,dbRECORD_COUNT);

   foreach $row (0..$nrecs-1) {
     $HN[3] = $row;
     ($sta) = dbgetv(@HN,qw(sta));
     push(@hnstas,$sta);
   }

   printf "Number of stations with epi metadata: %s\n", $#hnstas+1 if $opt_V ;

#
# Check #3b - all "epi" datalogger template have HN channels described
#

# check station in q3302orb.pf has value in hnstas (passes check)

   @missinghn_meta = remain(\@q330_epi_dl,\@hnstas);
   @missinghn_q330 = remain(\@hnstas,\@q330_epi_dl);

   if ($#missinghn_meta >= 0) { 	# there are some stations missing HN channel descriptions in metadata)
     foreach (@missinghn_meta) {
        print "  $_ is missing an HN channel description but collecting HN data\n";
        $errorhn++;
     }
   } 

   if ($#missinghn_q330 >= 0) { 	# there are some stations with HN channel descriptions in metadata not collecting HN in acq)
     foreach (@missinghn_q330) {
        print "  $_ is not collecting HN data via q3302orb, but should be \n";
        $errorhn++;
     }
   } 

   if (!$errorhn) {
      print "\nCheck #3  **  PASSED  ** All stations have HN channels described\n\n";	 
   } else {
      print "\nCheck #3  **  FAILED  **  Some stations have HN description missing \n\n";	 
      $testfails++;
   }

}

#
# check #4 - coincident start times for broadband, inframet and strong motion
#

if ($opt_4) {

print "Check #4  --  started  -- \n";

# TA specific hard-code of channels to check for simultaneous starts

   $calibsub	= "chan=~/BHZ|HNZ|BDO_EP|BDF_EP|LDM_EP/" ;
   @dbcalibration = dbsubset(@dbcalibration,$calibsub) ;
   @dbcalibration = dbsort(@dbcalibration,"sta","chan","time") ;
   $nrecs	= dbquery(@dbcalibration,dbRECORD_COUNT);

   @dbcalib_g 	= dbgroup(@dbcalibration, "sta") ;
   $nrecs	= dbquery(@dbcalib_g ,dbRECORD_COUNT);

#   print "$nrecs records after group by sta/time/chan\n" if $opt_V ;

   for ($dbcalib_g[3] = 0 ; $dbcalib_g[3]<$nrecs; $dbcalib_g[3]++) {
      my $nrows = dbex_eval (@dbcalib_g, "count()");

      if ($nrows >= 1 ) {
	my $bundle = dbgetv(@dbcalib_g, "bundle") ;
	my @bundle = split (' ', $bundle) ;
        my %stuff = () ;

	my $mintime = 0 ;
	my %stahash = ();

	for ( ; $bundle[3] < $bundle[2] ; $bundle[3]++ ) {
           ($csta, $cchan, $ctime, $cendtime) = dbgetv ( @bundle, "sta", "chan", "time", "endtime" ) ;

	   # skip over stations where we know a sensor was installed later

	   if ($csta ~~ @skipstas ) {
		print "  Ignoring possible issue with $csta per pf skip_starttime_check exclusion \n" if $opt_v ;
		last;	
	   }

	   # populate hash with ctime

	   if (!$stahash{$cchan} || $stahash{$cchan} >= $ctime) {
	   	$stahash{$cchan} = $ctime;
	   } else  {
		printf "%s:%s has an older record.  Skipping %s \n", $csta,$cchan, strtime($ctime) if $opt_V ; 
	   }
		
        }

# now need to go through all of the keys/values to find if there is a value that differs
# how about reversing it and seing if I come up with a hash with size of 1?

	%inverted = reverse %stahash ;
	my $invertedsize = keys( %inverted ) ;

	if ($invertedsize > 1) {	# means there is a channel with a different/unique start time
	   print "Check for possible starttime problems for $csta.\n";
   	   foreach my $k (sort keys %inverted) {
		printf "    mismatch for %s at %s \n", $inverted{$k}, strtime($k) ;
	   }
	   
        $errorstart++;

	}

      }

   }

   # need to bundle by station, group channel info including time and endtime
   # find min time for each channel and see if it matches

   if (!$errorstart) {
      print "\nCheck #4  **  PASSED  ** No mismatches in channel start times \n\n";	 
   } else {
      print "\nCheck #4  **  FAILED  ** Check for starttime mismatches \n\n";	 
      $testfails++;
   }


}

#
# check #5 - compare q3302orb.pf q330 dlsta and sn with dlsensor and stage.ssident
#
 
if ($opt_5) {

print "Check #5  --  started  -- \n";

   # force a subset for a single stream for each datalogger - assumes one datalogger per station
   # minor check to verify HN and BH have same digitizer
   $BHstagesub	= "chan=='BHZ'&&(endtime=='9999999999.99900'||endtime>='$t')&&gtype=='digitizer'" ;
   $HNstagesub	= "chan=='HNZ'&&(endtime=='9999999999.99900'||endtime>='$t')&&gtype=='digitizer'" ;

   @BHdbstage	= dbsubset(@dbstage,$BHstagesub) ;
   @HNdbstage	= dbsubset(@dbstage,$HNstagesub) ;
   $BHnrecs	= dbquery(@BHdbstage,dbRECORD_COUNT);
   $HNnrecs	= dbquery(@HNdbstage,dbRECORD_COUNT);

   print "Number of BH stage records after subset: $BHnrecs\n" if $opt_V ;
   print "Number of HN stage records after subset: $HNnrecs\n" if $opt_V ;

   foreach $row (0..$BHnrecs-1) {
     $BHdbstage[3] = $row;
     ($sta,$sn) = dbgetv(@BHdbstage,qw(sta ssident));
     $db_epiBH_dl{ $sta } = $sn; 
   }

   foreach $row (0..$HNnrecs-1) {
     $HNdbstage[3] = $row;
     ($sta,$sn) = dbgetv(@HNdbstage,qw(sta ssident));
     $db_epiHN_dl{ $sta } = $sn; 
   }

# compare sta/sn for calibration db vs sta/sn for q3302orb.pf

   foreach $key (sort keys %db_epiBH_dl) {

# compare values of q330 vs db (stage table)  using the same key for both
     if (!exists  $q330_sn_dl{$key}) {
	print "Open record in db does not exist in q3302orb.pf stash packet \n" ; 
	print "Sta: $key  q330sn in db:  $db_epiBH_dl{$key}\n"  ;

# need to put in a get-out-of-jail-free escape in case the record is available in q3302orb_prelim.pf 
# WORK NEEDED HERE!!! (another call to grab packets, from the prelim orb, process, and re-check?)

     } else {		# now check to see if they match
	if ($q330_sn_dl{$key} !~ $db_epiBH_dl{$key}) {
	   print "\n  ERROR!!  Mismatch between q3302orb.pf and stage table (BH records) for q330 serial number for $key!\n";
	   print "   q3302orb.pf:  $q330_sn_dl{$key}\n";
	   print "   db(BH stage):    $db_epiBH_dl{$key}\n";
	   $errorq330++;
	}

     }
# compare values of q330 vs db (dlsensor table)  using the same key for both

    unless ( grep (/$q330_sn_dl{$key}/, @dlsensorq330))  {
  	print "\n  ERROR!!  dlsensor missing a record for q330 available in q3302orb.pf -  $key:$q330_sn_dl{$key}\n\n";
	$errorq330++;
    }

# compare values of db (stage) vs db (dlsensor table)  using the same key for both
     unless (grep (/$db_epiBH_dl{$key}/, @dlsensorq330))  {
	print "\n  ERROR!!  dlsensor missing a record for q330 in calibration table -  $key:$db_epiBH_dl{$key}\n\n";
	$errorq330++;
     }

   }

   foreach $key (sort keys %db_epiHN_dl) {

# compare values of q330 vs db (stage table)  using the same key for both
     if (!exists  $q330_sn_dl{$key}) {
	print "\n  ERROR!!  Open record in db does not exist in q3302orb.pf stash packet \n";
	print "Sta: $key  q330sn in db:  $db_epiHN_dl{$key}\n\n";
     } else {		# now check to see if they match
	if ($q330_sn_dl{$key} !~ $db_epiHN_dl{$key}) {
	   print "\n  ERROR!!  Mismatch between q3302orb.pf and stage table (HN records) for q330 serial number for $key!\n";
	   print "   q3302orb.pf:  $q330_sn_dl{$key}\n";
	   print "   db(HN stage):    $db_epiHN_dl{$key}\n";
	   $errorq330++;
	}

     }


   }

   if (!$errorq330) {
      print "\nCheck #5  **  PASSED  ** No q330 serial number mismatches \n\n";	 
   } else {
      print "\nCheck #5  **  FAILED  ** Check for q330 serial number mismatches\n\n";	 
      $testfails++;
   }

}

# summary of error counts

print "\n\n";
print "***  Total # of $testfails test failures requiring database clean-up!!  ***\n\n";
print "Total number of open station pf/db difference errors: $error\n" if $error ;
print "Total number of missing HH descriptions: $errorhh\n" if $errorhh ;
print "Total number of HN metadata and/or q330 template mismatches: $errorhn \n" if $errorhn;
print "Total number of possible metadata starttime mismatches across channels: $errorstart \n" if $errorstart;
print "Total number of q330 serial number mismatches: $errorq330 \n" if $errorq330;
print "\n\n";

# end of checks

dbclose(@db);

exit (0);

# start subs here

sub usage {
        print STDERR <<END;
            \nUSAGE: $0 {-1,-2,-3,-4,-5} [-p pf] [-t targetname] [-v] db 

END
        exit(1);
}

sub collect_orbstash {

print "starting collect_orbstash\n" if $opt_V;

 foreach $orbname (@{$Pf{orbs}}) {	
     
   $orb = orbopen ( $orbname, "r" ) ;
   die ("Can't open $orbname" ) if $orb < 0 ;

   my $n = orbselect ( $orb, ".*/pf/st" ) ;

   print "number of packets through orbselect for $orbname: $n\n" if $opt_V ;

   orbselect ( $orb, "$select" ) if $select ;
   orbreject ( $orb, "$reject" ) if $reject ;

   $pktid = orbseek($orb, "ORBOLDEST");

   $pktid = orbseek($orb, "ORBNEWEST" ) ;
   $pktid = orbtell ($orb);

   my $pktcnt = 0 ;

   my $when;
   my @sources ;

   ($when, @sources) = orbsources($orb) ;

#    prettyprint(\@sources) if $opt_V ;

   foreach  $source (@sources) {
        elog_notify(sprintf ("%-15s    %8d    %s    \n",
                $source->srcname, $source->npkts,
                strtdelta($when-$source->slatest_time) ) ) if $opt_v ;
   }


   foreach $source (@sources) { 
      $pktcnt++; 

#      ($time, $packet, $nbytes) = orbgetstash($orb,".*/pf/st") ;
# this causes a string failure ^^^^
      $target = $source->srcname ;

      ($time, $packet, $nbytes) = orbgetstash($orb,"$target") ;

      printf "Collected packet: %s at %s from $target\n" , $pktid  , epoch2str($time,"%Y%j-%T") if $opt_V ;

      eval {
        ($result, $pkt) = unstuffPkt($target, $time, $packet, $nbytes) ;
      } ;

      if ( $@ ) {
         printf "unstuffPkt failed: $@\n" ;
      } else {
	 print "packet type: $result\n" if $opt_V ;
	 if ($result !~ 'Pkt_stash') {
	   print "Not a stash packet - cannot confirm q330 serial number and datalogger template\n";
	   next; 
         }

	 my $pfname = "stash.$pktcnt";

	 pfnew ($pfname);
	 pfcompile ($pkt->string, $pfname);

	 my $pfarr = pfget ($pfname, ""); 

         &process_stash  ( $pfarr, $pfname ) ;

	 next ;

      }
   }

   orbclose ($orb);

  }

}

sub process_stash {
    my $stasharr = shift ;
    my $pfname  = shift ;

    my ($dl) ;
 

    print "I am inside process_stash for $target \n" if ($opt_V);

    if ( ! defined $stasharr->{"q3302orb.pf"}) {
 	print "Hmm.  I did not find q3302orb.pf info?\n";
	return;
    } 

    foreach my $k ( sort keys %{$stasharr->{"q3302orb.pf"}}) {
	if ($k =~ /dataloggers/) {

	   foreach $dl (@{$stasharr->{"q3302orb.pf"}{$k}}) {
#		print "dl is $dl \n";
		my ($qdlsta, $qnet, $qsta, $qsn,$q,$qdp,$qtemplate,$qacq) = split(/\s+/, $dl);
	        print "qdlsta:  $qdlsta  qtemplate: $qtemplate\n" if $opt_V ;

		if ($qtemplate ~~ @{$Pf{hn}}) {	
		   push (@q330_epi_dl,$qsta);
		}
		if ($qtemplate ~~ @{$Pf{bb100}}) {	
		   push (@q330_bb100_dl,$qsta);
		} 

#  need to populate q330_sn_dl with active dl(sta) and serial number		
		$q330_sn_dl{ $qsta } = $qsn; 
	   }

	}
    }

    printf "Total number of dataloggers using an epi datalogger template after processing $target : %s\n", $#q330_epi_dl+1 if $opt_V;
    printf "Total number of dataloggers using a 100sps bb datalogger template after processing $target : %s\n", $#q330_bb100_dl+1 if $opt_V;

    return ;
}



