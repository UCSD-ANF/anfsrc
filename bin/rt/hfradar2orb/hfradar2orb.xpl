#
# hfradar2orb
# 
# Kent Lindquist
# Lindquist Consulting
# 2004
#

use Datascope ;
use orb;
use Time::HiRes;
use File::Find;
use hfradar2orb;
require "getopts.pl";

sub wanted {

	if( ! -f "$_" ) {

		return;

	} elsif( $_ !~ /$subdirs[$i]->{match}/ ) {

		return;
	}

	$dfile = $_;

	undef( $site );
	undef( $timestamp );
	undef( $beampattern );

	eval( "$subdirs[$i]->{site};" );
	eval( "$subdirs[$i]->{timestamp};" );
	eval( "$subdirs[$i]->{beampattern};" );

	if( ! defined( $site ) ) {

		elog_complain( "site not defined for $_; skipping\n" );

		return;
	}

	if( ! defined( $timestamp ) ) {

		elog_complain( "timestamp not defined for $_; skipping\n" );

		return;
	}

	if( ! defined( $beampattern ) ) {

		elog_complain( "beampattern not defined for $_; skipping\n" );

		return;
	}

	if( $opt_m && $timestamp < $mintime ) {

		if( $opt_v ) {

			elog_notify( "Skipping $dfile: " . strtime( $timestamp ) . 
				     " is less than minimum of " .
				     strtime( $mintime ) . "\n" );
		}

		return;
	}

	if( defined( $too_new ) && $timestamp > str2epoch( "now" ) + $too_new ) {

		if( $opt_v ) {

			chomp( $s = strtdelta( $too_new ) );
			$s =~ s/\s*$//;
			$s =~ s/^\s*//;

			elog_notify( "Skipping $dfile because its timestamp of '" .
				      strtime( $timestamp ) . 
				     "' is more than $s " . 
				     "after current system-clock time\n" );

			return;
		}
	}
	
	if( $opt_v ) {

		elog_notify "Processing $dfile, timestamped " . 
			epoch2str( $timestamp, "%D %T %Z", "" ) . "\n";
	}

	hfradar2orb::encapsulate_packet( $dfile, $site, $beampattern,
			    $subdirs[$i]->{format}, $timestamp, $Orbfd );
		
	if( $opt_i ) {

		Time::HiRes::sleep( $opt_i );
	}

	if( $opt_n ) {
		
		elog_notify( "\tPreserving file " . abspath( $dfile ) . "\n" );

	} else {
		
		if( $opt_v ) {

			elog_notify( "\tRemoving file " . abspath( $dfile ) . "\n" );
		}

		unlink( "$_" );
	}
}

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('i:m:p:vn') || @ARGV != 2 ) {

	die( "Usage: $Program [-v] [-n] [-p pffile] [-i interval_sec] [-m mintime] basedir orbname\n" );

} else {

	$basedir = $ARGV[0];
	$orbname = $ARGV[1];
} 

if( $opt_p ) { 

	$Pfname = $opt_p;

} else { 

	$Pfname = $Program;
}

if( $opt_m ) {

	$mintime = str2epoch( "$opt_m" );
}

if( $opt_v ) {

	$now = str2epoch( "now" );
 	elog_notify( "Starting at " . epoch2str( $now, "%D %T %Z", "" ) . "\n" );
}

@subdirs = @{pfget( $Pfname, "subdirs" )};
$too_new = pfget( $Pfname, "too_new" );

if( defined( $too_new ) && $too_new eq "" ) {

	undef( $too_new );
}

if( defined( $too_new ) ) {

	if( $too_new ne "0" ) {
		
		$too_new = is_epoch_string( $too_new );

		if( ! defined( $too_new ) ) {

			elog_die( "Badly formed value '$too_new' for parameter 'too_new'. Bye.\n" )
		}
	}

	if( $opt_v ) {

		chomp( $s = strtdelta( $too_new ) );
		$s =~ s/\s*$//;
		$s =~ s/^\s*//;

		elog_notify( "Rejecting packets that are more than $s in the future\n" );
	}
	
}

$Orbfd = orbopen( $orbname, "w&" );

if( $Orbfd < 0 ) {

	elog_die( "Failed to open orbserver named '$orbname' for writing! Bye.\n" );
}

for( $i = 0; $i <= $#subdirs; $i++ ) {
	
	if( $opt_v ) {

		elog_notify( "Processing files in $basedir/$subdirs[$i]->{subdir} " .
			     "matching /$subdirs[$i]->{match}/\n" );
	}

	find( \&wanted, "$basedir/$subdirs[$i]->{subdir}" );
}

if( $opt_v ) {

	$now = str2epoch( "now" );
 	elog_notify( "Ending at " . epoch2str( $now, "%D %T %Z", "" ) . "\n" );
}
