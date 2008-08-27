
#   Copyright (c) 2004-2006 Lindquist Consulting, Inc.
#   All rights reserved. 
#                                                                     
#   Written by Dr. Kent Lindquist, Lindquist Consulting, Inc. 
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#   KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#   WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
#   PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
#   OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR 
#   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#   SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#   This software may be used freely in any way as long as 
#   the copyright statement above is not removed. 

use Datascope ;
use orb;
use Time::HiRes;
use File::Find;
use Fcntl ':flock';
use hfradar2orb;
use codartools;
require "getopts.pl";

sub file_is_wanted {
	my( $dfile ) = @_;

	if( $dfile !~ /$patterns[$i]->{match}/ ) {

		return 0;
	}

	undef( $site );
	undef( $timestamp );
	undef( $patterntype );

	eval( "$patterns[$i]->{site};" );
	eval( "$patterns[$i]->{timestamp};" );
	eval( "$patterns[$i]->{patterntype};" );

	if( ! defined( $site ) || $site eq "" ) {

		elog_complain( "site not defined for $_; skipping\n" );

		return 0;
	}

	if( ! defined( $timestamp ) || $timestamp eq "" ) {

		elog_complain( "timestamp not defined for $_; skipping\n" );

		return 0;
	}

	if( ! defined( $patterntype ) || $patterntype eq "" ) {

		elog_complain( "patterntype not defined for $_; skipping\n" );

		return 0;
	}

	if( $opt_m && $timestamp < $mintime ) {

		if( $opt_v ) {

			elog_notify( "Skipping '$dfile': " . strtime( $timestamp ) . 
				     " is less than minimum of " .
				     strtime( $mintime ) . "\n" );
		}

		return 0;
	}

	if( $opt_S && $timestamp < $starttime ) {

		return 0;
	}

	if( defined( $too_new ) && 
	    $timestamp > str2epoch( "now" ) + $too_new ) {

		if( $opt_v ) {

			chomp( $s = strtdelta( $too_new ) );
			$s =~ s/\s*$//;
			$s =~ s/^\s*//;

			elog_notify( "Skipping '$dfile' because its timestamp of '" .
				      strtime( $timestamp ) . 
				     "' is more than $s " . 
				     "after current system-clock time\n" );

			return 0;
		}
	}

	return 1;
}

sub check_lock {
	my( $lockfile_name ) = @_;

	if( ! defined( $lockfile_name ) ) {
		
		return;
	}

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

	if( ! defined( $lockfile_name ) ) {
		
		return;
	}

	flock( LOCK, LOCK_UN );

	close( LOCK );

	if( $opt_v ) {
		
		elog_notify( "Unlocked $lockfile_name" );
	}

	return;
}

sub process_ssh_files {
	my( $address, $dir, $dfile ) = @_;

	if( ! file_is_wanted( $dfile ) ) {

		return;
	}

	if( $opt_v ) {

		elog_notify "Processing '$dfile', timestamped " . 
			epoch2str( $timestamp, "%D %T %Z", "" ) . "\n";
	}

	$dfile_copy = "/tmp/$dfile";
	$dfile_copy =~ s/ /_/g;

	my( $dfile_escaped ) = $dfile;
	$dfile_escaped =~ s/ /\\\\\\ /g;

	my( $v );

	if( $opt_V ) {
		
		$v = "-v";

	} else {
		
		$v = "";
	}

	my( $rc ) = system( "scp $v $address:$dir/$dfile_escaped $dfile_copy" );

	if( ! -f "$dfile_copy" ) {
		
		elog_complain( "Failed to transfer '$dfile' from $address:$dir " .
			       "via scp (rc=$rc, new copy of dfile doesn't exist)! " .
				"Skipping '$dfile'.\n" );

		return;

	} elsif( $rc != 0 ) {

		elog_complain( "Failed to transfer '$dfile' from $address:$dir " .
			       "via scp (nonzero rc=$rc from scp)! Skipping '$dfile'.\n" );

		return;
	}

	my( $buflength ) = (stat($dfile_copy))[7];

	open( P, "$dfile_copy" );

	my( $readlength ) = read( P, $buffer, $buflength, 0 );

	close( P );

	if( $readlength != $buflength ) {
		
		elog_complain( "Failed to read '$dfile_copy'! " .
			"(read $readlength bytes, expected $buflength " .
			"bytes). Skipping.\n" );

		unlink( $dfile_copy );

		return;
	}

	$buffer =~ s@\r\n@\n@g;
	$buffer =~ s@\r@\n@g;

	my( @block ) = split( /\n/, $buffer );

	if( ! codartools::is_valid_lluv( @block ) ) {

		if( $opt_v ) {
			
			elog_notify( "Converting '$dfile' to LLUV format\n" );
		}

		@block = codartools::rb2lluv( $patterntype, $site, $timestamp, @block );

		if( ! @block ) {

			elog_complain( "Failed to convert '$dfile' to LLUV " .
					"format! Skipping.\n" );

			unless( $opt_n ) {

				unlink( $dfile_copy );
			}

			return;

		} else{

			$buffer = join( "\n", @block );
			$buffer .= "\n";
		}
	}

	hfradar2orb::encapsulate_packet( $buffer, $net, $site, $patterntype, 
					 $output_format, $timestamp, 
					 $Orbfd );

	if( $opt_S ) {

		$starttime = $timestamp + 0.01;

		bury();
	}
		
	unless( $opt_n ) {
	
		unlink( $dfile_copy );
	}

	if( $opt_i ) {

		Time::HiRes::sleep( $opt_i );
	}

}

sub process_local_files {

	if( ! -f "$_" ) {

		return;

	} elsif( ! file_is_wanted( $_ ) ) {

		return;
	}

	$dfile = $_;
	
	if( $opt_v ) {

		elog_notify "Processing '$dfile', timestamped " . 
			epoch2str( $timestamp, "%D %T %Z", "" ) . "\n";
	}

	my( $buflength ) = (stat($dfile))[7];

	open( P, "$dfile" );

	my( $readlength ) = read( P, $buffer, $buflength, 0 );

	close( P );

	if( $readlength != $buflength ) {
		
		elog_complain( "Failed to read '$dfile'! " .
			"(read $readlength bytes, expected $buflength " .
			"bytes). Skipping.\n" );

		return;
	}

	$buffer =~ s@\r\n@\n@g;
	$buffer =~ s@\r@\n@g;

	my( @block ) = split( /\n/, $buffer );

	if( ! codartools::is_valid_lluv( @block ) ) {

		if( $opt_v ) {
			
			elog_notify( "Converting '$dfile' to LLUV format\n" );
		}

		@block = codartools::rb2lluv( $patterntype, $site, $timestamp, @block );

		if( ! @block ) {

			elog_complain( "Failed to convert '$dfile' to LLUV " .
					"format! Skipping.\n" );

			if( $opt_n ) {
		
				elog_notify( "\tPreserving file " . abspath( $dfile ) . "\n" );

			} else {
		
				if( $opt_v ) {
	
					elog_notify( "\tRemoving file " . abspath( $dfile ) . "\n" );
				}

				unlink( "$dfile" );
			}

			return;

		} else{

			$buffer = join( "\n", @block );
			$buffer .= "\n";
		}
	}

	hfradar2orb::encapsulate_packet( $buffer, $net, $site, $patterntype,
			    $output_format, $timestamp, $Orbfd );
		
	if( $opt_S ) {

		$starttime = $timestamp + 0.01;

		bury();
	}
		
	if( $opt_i ) {

		Time::HiRes::sleep( $opt_i );
	}

	if( $opt_n ) {
		
		elog_notify( "\tPreserving file " . abspath( $dfile ) . "\n" );

	} else {
		
		if( $opt_v ) {

			elog_notify( "\tRemoving file " . abspath( $dfile ) . "\n" );
		}

		unlink( "$dfile" );
	}
}

sub ssh_find {
	my( $coderef, $address, $dir ) = @_;

	if( $opt_v ) {
		elog_notify( "Retrieving file listing from $address:$dir " .
			     "via ssh...\n" );
	}

	my( @files_present ) = `ssh $address ls -1 $dir`;

	chomp( @files_present );

	foreach $dfile ( @files_present ) {

		&{$coderef}( $address, $dir, $dfile );
	}

	return;
}

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('i:m:p:S:l:vVn') || @ARGV != 3 ) {

	die( "Usage: $Program [-vVn] [-p pffile] [-S Statefile] [-i interval_sec] [-l lockfile] [-m mintime] net [[user@]ipaddress:]basedir orbname\n" );

} else {

	$net     = $ARGV[0];
	$basedir = $ARGV[1];
	$orbname = $ARGV[2];

	if( $opt_l ) {
		
		$lockfile = $opt_l;
	}
} 

if( $opt_V ) {
	
	$opt_v++;
}

if( $opt_v ) {

	$now = str2epoch( "now" );

 	elog_notify( "Starting at " . epoch2str( $now, "%D %T %Z", "" ) . 
		     " (hfradar2orb \$Revision: 1.26 $\ " .
		     "\$Date: 2008/08/27 19:42:30 $\)\n" );

	$hfradar2orb::Verbose++;
	$codartools::Verbose++;
}

check_lock( $lockfile );

if( $basedir =~ /^[^\/]+:/ ) {
	
	$ssh_mode = 1;

	( $ssh_address, $ssh_basedir ) = split( /:/, $basedir );

	if( $opt_v ) {

		elog_notify( "Retrieving files via ssh to $ssh_address\n" );
	}

	if( ! -x ( $program = datafile( "PATH", "ssh" ) ) ) {
		
		release_lock( $lockfile );

		elog_die( "Can't find 'ssh' executable on path! Bye.\n" );
	}

	if( ! -x ( $program = datafile( "PATH", "scp" ) ) ) {

		release_lock( $lockfile );

		elog_die( "Can't find 'scp' executable on path! Bye.\n" );
	}

} else {

	$ssh_mode = 0;

	if( $opt_v ) {

		elog_notify( "Retrieving files from local directories\n" );
	}
}

if( $opt_p ) { 

	$Pfname = $opt_p;

} else { 

	$Pfname = $Program;
}

if( $opt_m ) {

	$mintime = str2epoch( "$opt_m" );
}

if( $opt_S ) {

	if( $opt_v ) {

		elog_notify( "Tracking acquisition in statefile '$opt_S'\n" );
	}

	$stop = 0;

	$starttime = 0;

	exhume( $opt_S, \$stop, 15 );

	if( resurrect( "starttime", \$starttime, TIME_RELIC ) == 0 ) {
		
		if( $opt_v ) {

			elog_notify( "$Resuming from file timestamps of " .
				     strtime( $starttime ) . "\n" );
		}
	}
}

@patterns = @{pfget( $Pfname, "patterns" )};
$too_new = pfget( $Pfname, "too_new" );
$output_format = pfget( $Pfname, "output_format" );

if( defined( $too_new ) && $too_new eq "" ) {

	undef( $too_new );
}

if( defined( $too_new ) ) {

	if( $too_new ne "0" ) {
		
		$too_new = is_epoch_string( $too_new );

		if( ! defined( $too_new ) ) {

			release_lock( $lockfile );

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

	release_lock( $lockfile );

	elog_die( "Failed to open orbserver named '$orbname' for writing! Bye.\n" );
}

for( $i = 0; $i <= $#patterns; $i++ ) {
	
	if( $opt_v ) {

		elog_notify( "Processing files in " .
			     "$basedir " .
			     "matching /$patterns[$i]->{match}/\n" );
	}

	if( $ssh_mode ) {

		ssh_find( \&process_ssh_files, 
			  $ssh_address, 
			  "$ssh_basedir" );

	} else {

		find( \&process_local_files, 
		      "$basedir" );
	}
}

release_lock( $lockfile );

if( $opt_v ) {

	$now = str2epoch( "now" );
 	elog_notify( "Ending at " . epoch2str( $now, "%D %T %Z", "" ) . "\n" );
}
