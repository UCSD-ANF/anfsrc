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
		elog_notify( "Locking $lockfile_name...." );
	}

	open( LOCK, ">$lockfile_name" );

	if( flock( LOCK, LOCK_EX|LOCK_NB ) != 1 ) {

		elog_die( "Failed to lock '$lockfile_name'! Bye.\n" );
	}

	print LOCK "$$\n"; 

	if( $opt_v ) {
		elog_notify( "Locking $lockfile_name....Locked." );
	}

	return;
}

sub release_lock {
	my( $lockfile_name ) = @_;

	$lockfile_name = ".$lockfile_name";
	
	flock( LOCK, LOCK_UN );

	close( LOCK );

	if( $opt_v ) {
		elog_notify( "Unlocked $lockfile_name" );
	}

	return;
}

sub Smkdir_p {
	my( $collection ) = @_;

	if( $opt_v ) {
		elog_notify( "Making top-level collection '$collection'\n" );
	}

	if( ( $rc = system( "$Smkdir_path $collection" ) ) == 0 ) {

		return;
	}	

	# Assume the collection is an absolute path with a home:

	$collection =~ m@(/.*home/[^/]+)(/.*)?@;

	$home = $1;
	
	if( ! defined( $2 ) ) {

		return;
	}

	my( @parts ) = split( m@/@, $2 );

	my( $subcoll ) = $home;

	while( $part = shift( @parts ) ) {

		$subcoll .= "/$part";
		system( "$Smkdir_path $subcoll" );
	}
}

sub make_subcollections {
	my( $top_collection ) = pop( @_ );
	my( @db ) = @_;

	Smkdir_p( $top_collection );

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

$num_errors = 0;

if ( ! &Getopts('s:p:veft') || @ARGV != 2 ) { 

	die ( "Usage: rtbackup_srb [-eftv] [-p pfname] [-s wfdisc_subset] database collection\n" ) ; 

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

if( $opt_f ) {

	$f = "-f";

} else {

	$f = "";
}

if( $collection !~ m@^/([-_a-zA-Z0-9]+)/home/.+@ ) {

	elog_die( "The SRB Zone must be explicitly specified in the collection ".
	          "name, e.g. /A_ZONE/home/somedir\n" );
} else {

	$Szone = $1;

	if( $opt_v ) {

		elog_notify( "Szone is $Szone\n" );
	}
}

$Spath = pfget( $Pf, "Spath" );
@backup_resources = @{pfget( $Pf, "backup_resources" )};

@Scommands = ( "Sput",
	       "Smkdir",
	       "Senv",
	       "SgetU",
	       "Sbkupsrb",
	     );

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

$mdasAuthFile = "/tmp/MdasAuth.$<.$$";
$mdasEnvFile = "/tmp/MdasEnv.$<.$$";

$ENV{mdasAuthFile} = $mdasAuthFile;
$ENV{mdasEnvFile} = $mdasEnvFile;

open( A, ">$mdasAuthFile" );
print A pfget( $Pf, "MdasAuth" );
close( A );

open( E, ">$mdasEnvFile" );
print E pfget( $Pf, "MdasEnv" );
close( E );

if( $opt_v ) {
	elog_notify( "Testing SRB connection:\n" );
}

if( ( $rc = system( "$SgetU_path > /dev/null 2>&1" ) ) != 0 ) {

	elog_die( "SRB connection Failed! Bye.\n" );

} else {

	if( $opt_v ) {
		
		elog_notify( "SRB connection Initialized\n" );
	}
}

( $descriptor_dir, $descriptor_basename, $descriptor_suffix ) = 
						parsepath( $dbname );

if( defined( $descriptor_suffix ) && $descriptor_suffix ne "" ) {

	$descriptor_basename .= ".$descriptor_suffix";
}

check_lock( "rtdbclean" );

@db = dbopen( "$dbname", "r+" );

@schema_tables = dbquery( @db, dbSCHEMA_TABLES );

if( ! grep( /wfsrb/, @schema_tables ) ) {

	release_lock( "rtdbclean" );

	elog_die( "No table 'wfsrb' in schema for '$dbname'. Bye!\n" );
}

@dbwfsrb = dblookup( @db, "", "wfsrb", "", "" );

if( ! dbquery( @dbwfsrb, dbTABLE_IS_WRITABLE ) ) {

	elog_die( "Table '$dbname.wfsrb' is not writable. Bye!\n" );
}

$wfsrb_table_filename = dbquery( @dbwfsrb, dbTABLE_FILENAME );

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

$nrecs_new_wfsrb = dbquery( @db, dbRECORD_COUNT );

if( $nrecs_new_wfsrb <= 0 && ! $opt_t ) {

	if( $opt_v ) {
		
		elog_notify( "No records to add to SRB. Bye.\n" );
	}

	release_lock( "rtdbclean" );

	exit( 0 );
}

make_subcollections( @db, $collection );

for( $db[3] = 0; $db[3] < $nrecs_new_wfsrb; $db[3]++ ) {
	
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

		$rc = system( "$Sput_path $v $f $filename $Scoll" );

		if( $rc != 0 ) {

			elog_complain( "Sput failed for $filename!!\n" );

			$num_errors++;

			next;
		}

		$Added{$filename}++;
	}

	$dbwfsrb[3] = dbaddnull( @dbwfsrb );

	dbputv( @dbwfsrb,
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

$descriptor_filename = dbquery( @db, dbDATABASE_FILENAME );

if( $opt_v ) {
	elog_notify( "Adding $descriptor_filename to $Szone:$collection\n" );
}

# Always force overwrite:
$rc = system( "$Sput_path $v -f $descriptor_filename $collection/$descriptor_basename" );

if( $rc != 0 ) {

	elog_complain( "Sput failed for $descriptor_filename!!\n" );

	$num_errors++;
}

if( $opt_t ) {

	@backup_tables = dbquery( @db, dbSCHEMA_TABLES );

} elsif( $nrecs_new_wfsrb > 0 ) {

	@backup_tables = ( "wfsrb" );

} else {
	
	@backup_tables = ();
}

foreach $table ( @backup_tables ) {

	@db = dblookup( @db, "", "$table", "", "" );

	$present = dbquery( @db, dbTABLE_PRESENT );

	if( ! $present ) { 

		next; 
	}

	$table_filename = dbquery( @db, dbTABLE_FILENAME );

	if( $opt_v ) {
		elog_notify( "Adding $table_filename to $Szone:$collection " .
			     "as $descriptor_basename.$table\n" );
	}

	# Always force overwrite:
	# Version stamping of these files is still missing:
	$rc = system( "$Sput_path $v -f $table_filename $collection/$descriptor_basename.$table" );

	if( $rc != 0 ) {

		elog_complain( "Sput failed for $table_filename!!\n" );

		$num_errors++;
	}
}

dbclose( @db );

foreach $resource ( @backup_resources ) {

	if( $opt_v ) {
		
		elog_notify( "Backing up top-level collection " .
			     "to resource '$resource'\n" );
	}

	$rc = system( "$Sbkupsrb_path -r -S $resource $collection" );

	if( $rc != 0 ) {

		elog_complain( "Sbkupsrb failed for resource '$resource'!!\n" );

		$num_errors++;
	}
}

release_lock( "rtdbclean" );

unlink( "$mdasAuthFile" );
unlink( "$mdasEnvFile" );

if( $num_errors > 0 ) {

	elog_die( "Total of $num_errors errors during run\n" );

} else {

	elog_notify( "Total of $num_errors errors during run\n" );
	exit( 0 );
}
