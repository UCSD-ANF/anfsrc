# 
# rtbackup_srb
# Program to back-up Datascope data to a Storage Resource Broker
# Kent Lindquist
# Lindquist Consulting
# 2004
#

use Datascope;
require "getopts.pl";
use Fcntl ':flock';

sub check_lock {
	my( $lockfile_name ) = @_;

	$lockfile_name = ".$lockfile_name";

	if( $opt_v ) {
		elog_notify( "Locking $lockfile_name" );
	}

	open( LOCK, ">$lockfile_name" );

	if( flock( LOCK, LOCK_EX|LOCK_NB ) != 1 ) {

		die( "Failed to lock '$lockfile_name'! Bye.\n" );
	}

	print LOCK "$$\n";

	return;
}

sub release_lock {
	
	flock( LOCK, LOCK_UN );

	close( LOCK );

	return;
}

sub make_subcollections {
	my( $top_collection ) = pop( @_ );
	my( @db ) = @_;

	system( "$Smkdir_path $top_collection" );

	@dbpaths = dbsort( @db, "-u", "dir" );

	$npaths = dbquery( @dbpaths, dbRECORD_COUNT );

	for( $dbpaths[3] = 0; $dbpaths[3] < $npaths; $dbpaths[3]++ ) {

		$dir = dbgetv( @dbpaths, "dir" );

		if( $opt_v ) {

			elog_notify( "Making sub-collection '$dir'\n" );
		}

		my( @parts ) = split( m@/@, $dir );

		my( $subcoll ) = $top_collection;

		while( $part = shift( @parts ) ) {

			$subcoll .= "/$part";
			system( "$Smkdir_path $subcoll" );
		}
	}
}

elog_init( $0, @ARGV );

if ( ! &Getopts('s:p:ve') || @ARGV != 2 ) { 

	die ( "Usage: rtbackup_srb [-p pfname] [-s wfdisc_subset] [-v] [-e] database collection\n" ) ; 

} else {

	$collection = pop( @ARGV );
	$dbname = pop( @ARGV );
}

if( $opt_p ) {

	$Pf = $opt_p;

} else {

	$Pf = "rtbackup_srb";
}

if( $opt_v ) {

	$v = "-v";

} else {

	$v = "";
}

$Spath = pfget( $Pf, "Spath" );

@Scommands = ( "Sinit",
	       "Sput",
	       "Smkdir",
	       "Senv",
	       "Sexit" );

foreach $Scommand ( @Scommands ) {

	$var = "$Scommand" . "_path";

	if( defined( $Spath ) && $Spath ne "" && 
	    -x "$Spath/$Scommand" ) {
		
		$$var = "$Spath/$Scommand";

	} elsif( -x ( $apath = datafile( "PATH", "$Scommand" ) ) ) {
			
		$$var = $apath;

	} else {
		
		die( "rtbackup_srb: Couldn't find the command '$Scommand'! " .
		     "Please update your path or set the Spath parameter " .
		     "in $Pf.pf. Bye.\n" );
	}
}

if( $opt_v ) {
	elog_notify( "Initializing SRB connection:\n" );
}

if( ( $rc = system( "$Sinit_path $v" ) ) != 0 ) {
	
	die( "Sinit failed! Please check ~/.srb/.MdasAuth and " .
	     "~/.srb/.MdasEnv. Bye.\n" );

} else {
	
	if( $opt_v ) {
		
		elog_notify( "SRB connection Initialized\n" );
	}
}

chomp( $Szone = `$Senv_path | grep MCATZONE` );
$Szone =~ s/.*MCATZONE\s*=\s*//;
$Szone =~ s/\s*$//;

check_lock( "rtdbclean" );

@db = dbopen( "$dbname", "r+" );

@schema_tables = dbquery( @db, dbSCHEMA_TABLES );

if( ! grep( /wfsrb/, @schema_tables ) ) {

	die( "No table 'wfsrb' in schema for '$dbname'. Bye!\n" );
}

@dbwfsrb = dblookup( @db, "", "wfsrb", "", "" );

if( ! dbquery( @dbwfsrb, dbTABLE_IS_WRITABLE ) ) {

	die( "Table '$dbname.wfsrb' is not writable. Bye!\n" );
}

@dbwfdisc = dblookup( @db, "", "wfdisc", "", "" );

if( $opt_s ) {

	if( $opt_v ) {
		elog_notify( "Subsetting wfdisc for records matching " .
			     "'$opt_s'\n" );
	}
	@dbwfdisc = dbsubset( @dbwfdisc, "$opt_s" );
}

if( $opt_e ) {

	$jdate_today = epoch2str( str2epoch( "now" ), "%Y%j" );

	if( $opt_v ) {
		elog_notify( "Excluding data on and later than today's " .
			     "jdate of $jdate_today\n" );
	}
	
	@dbwfdisc = dbsubset( @dbwfdisc, "jdate < $jdate_today" );
}

@dbwfsrb = dblookup( @db, "", "wfsrb", "", "" );

@db = dbnojoin( @dbwfdisc, @dbwfsrb );

$nrecs = dbquery( @db, dbRECORD_COUNT );

if( $nrecs <= 0 ) {

	if( $opt_v ) {
		
		elog_notify( "No records to add to SRB. Bye.\n" );
	}

	exit( 0 );
}

make_subcollections( @db, $collection );

for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {
	
	( $sta, $chan, $time, $wfid, $chanid, $jdate, $endtime,
	  $nsamp, $samprate, $calib, $calper, $instype, $segtype,
  	  $datatype, $clip, $dir, $dfile, $foff, $commid ) =

		dbgetv( @db,
			"sta", "chan", "time", "wfid",
			"chanid", "jdate", "endtime",
			"nsamp", "samprate", "calib",
			"calper", "instype", "segtype",
			"datatype", "clip", "dir", "dfile",
			"foff", "commid" );

	$filename = dbextfile( @db );

	$Scoll = $collection . "/" . $dir;
	$Sobj = $dfile;

	# Don't re-add the same file just because of different 
	# foff values for different rows:

	if( ! defined( $Added{$filename} ) ) {

		if( $opt_v ) {
			elog_notify( "Adding file $dfile to $Szone:$Scoll\n" );
		}

		$rc = system( "$Sput_path $v $filename $Scoll" );

		if( $rc != 0 ) {

			elog_complain( "Sput failed for $filename!!\n" );

			next;
		}

		$Added{$filename}++;
	}

	dbaddv( @dbwfsrb,
		"sta", $sta,
		"chan", $chan,
		"time", $time,
		"wfid", $wfid,
		"chanid", $chanid,
		"jdate", $jdate,
		"endtime", $endtime,
		"nsamp", $nsamp,
		"samprate", $samprate,
		"calib", $calib,
		"calper", $calper,
		"instype", $instype,
		"segtype", $segtype,
		"datatype", $datatype,
		"clip", $clip,
		"Szone", $Szone,
		"Scoll", $Scoll,
		"Sobj", $Sobj,
		"foff", $foff,
		"commid", $commid );
}

dbclose( @db );

release_lock;

system( "$Sexit_path" );
