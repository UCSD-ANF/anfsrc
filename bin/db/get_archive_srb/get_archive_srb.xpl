# Copyright (c) 2005 Lindquist Consulting, Inc.
# All rights reserved. 
#
# Written by Dr. Kent Lindquist, Lindquist Consulting, Inc.
#
# This software may be used freely in any way as long as 
# the copyright statement above is not removed. 

require "getopts.pl";
use Datascope;

sub my_trwfname {
	my( $trwfname_pattern ) = pop( @_ );
	my( @db ) = @_;
	my( $path );

	foreach $field ( "sta", "chan", "time", "wfid", "chanid", "jdate",
			 "endtime", "nsamp", "samprate", "calib", "calper",
			 "instype", "segtype", "datatype", "clip", "foff",
			 "commid" ) {

		my( $val ) = dbgetv( @db, $field );

		$trwfname_pattern =~ s/%{$field}/$val/g;
	}

	$time = dbgetv( @db, "time" );

	$path = epoch2str( $time, $trwfname_pattern );

	( $dir, $dfile, $suffix ) = parsepath( $path );

	if( defined( $suffix ) && $suffix ne "" ) {
		
		$dfile .= "." . $suffix;
	}

	if( makedir( $dir ) != 0 ) {
		
		elog_complain( "Failed to make directory '$dir'!\n" );

		return undef;

	} else {

		dbputv( @db, "dir", $dir, "dfile", $dfile );

		return $path;
	}
}

$Program = $0;
$Program =~ s".*/"";
$Pf = $Program;
$Usage = "$Program [-v] [-p pfname] [-w wfsrb_subset] dbin dbout";

elog_init( $Program, @ARGV );

if( ! &Getopts( "vp:w:" ) || @ARGV != 2 ) {
	
	elog_die( $Usage );

} else {

	$dbin = shift( @ARGV );
	$dbout = shift( @ARGV );
}

if( $opt_p ) {
	
	$Pf = $opt_p;
}

if( $opt_v ) {

	$v = "-v";

	elog_notify( "Starting $Program run at " .
		epoch2str( str2epoch( "now" ), "%D %T %Z", "" ) );

	elog_notify( "Initializing SRB connection ...\n" );

} else {

	$v = "";
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

	elog_notify( "Testing SRB connection ..." );
}

if( ( $rc = system( "$SgetU_path > /dev/null 2>&1" ) ) != 0 ) {

	elog_die( "SRB connection Failed! Bye.\n" );

} else {

	if( $opt_v ) {
		
		elog_notify( "SRB connection Initialized\n" );
	}
}
if( $opt_v ) {
	elog_notify( "Running dbprocess commands to get wfsrb table or view ...\n" );
}

@dbprocess_commands = @{pfget( $Pf, "dbprocess_commands" )};
$trwfname_pattern = pfget( $Pf, "trwfname_pattern" );
$Spath = pfget( $Pf, "Spath" );

@Scommands = ( "Sget", "SgetU" );

foreach $Scommand ( @Scommands ) {

	$var = "$Scommand" . "_path";

	if( defined( $Spath ) && $Spath ne "" && 
	    -x "$Spath/$Scommand" ) {
		
		$$var = "$Spath/$Scommand";

	} elsif( -x ( $apath = datafile( "PATH", "$Scommand" ) ) ) {
			
		$$var = $apath;

	} else {
		
		die( "$Program: Couldn't find the command '$Scommand'! " .
		     "Please update your path or set the Spath parameter " .
		     "in $Pf.pf. Bye.\n" );
	}
}

@dbout = dbopen( $dbout, "r+" );

if( $dbout[0] < 0 ) {
	
	elog_die( "Failed to open '$dbout' for writing. Bye!" );
}

@dbout = dblookup( @dbout, "", "wfdisc", "", "" );

if( ! dbquery( @dbout, dbTABLE_IS_ADDABLE ) ) {

	elog_die( "Table '$dbout.wfdisc' does not allow record additions. Bye!" );
}

@dbin = dbopen( $dbin, "r" );

if( $dbin[0] < 0 ) {
	
	elog_die( "Failed to open '$dbin' for reading. Bye!" );
}

@dbin = dbprocess( @dbin, @dbprocess_commands );

if( ! grep( /wfsrb/, dbquery( @dbin, dbVIEW_TABLES ) ) && 
    dbquery( @dbin, dbTABLE_NAME ) ne "wfsrb" ) {
	
	elog_die( "Couldn't find table wfsrb in input view. Bye!" );
}

if( $opt_w ) {

	if( $opt_v ) {

		elog_notify( "Subsetting resulting table for '$opt_w' ...\n" );
	}

	@dbin = dbsubset( @dbin, $opt_w );
}

$nrecs = dbquery( @dbin, dbRECORD_COUNT );

if( $opt_v ) {

	elog_notify( "Processing $nrecs input-view rows ...\n" );
}

for( $dbin[3] = 0; $dbin[3] < $nrecs; $dbin[3]++ ) {

	( $sta, $chan, $time, $wfid, $chanid, $jdate, $endtime,
  	  $nsamp, $samprate, $calib, $calper, $instype, $segtype,
	  $datatype, $clip, $Szone, $Scoll, $Sobj, $foff, $commid ) =
	
		dbgetv( @dbin,
			"sta", "chan", "time", "wfid",
			"chanid", "jdate", "endtime",
			"nsamp", "samprate", "calib",
			"calper", "instype", "segtype",
			"datatype", "clip", "Szone", "Scoll",
			"Sobj", "foff", "commid" );
	
	@dbout = dblookup( @dbout, "", "", "", "dbSCRATCH" );

	dbputv( @dbout,
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
		"foff", $foff,
		"commid", $commid );

	$path = my_trwfname( @dbout, $trwfname_pattern );

	if( ! defined( $path ) ) {

		next;
	}

	if( ( $dbout[3] = dbaddchk( @dbout ) ) < 0 ) {
	
		@dbout = dblookup( @dbout, "", "", "", "dbSCRATCH" );

		elog_complain( "Failed to add record to wfdisc!\n" );
		elog_notify( "\tField values for failed row are:\n" );

		foreach $field ( "sta", "chan", "time", "wfid", "chanid",
			 "jdate", "endtime", "nsamp", "samprate", "calib", 
			 "calper", "instype", "segtype", "datatype", "clip", 
			 "foff", "commid" ) {

			my( $val ) = dbgetv( @dbout, $field );

			if( $field =~ /time|endtime/ ) {
				$val = strtime( $val );
			}

			elog_notify( "\t\t$field:\t$val\n" );
		}

		next;
	}

	if( $Extracted{"$Scoll/$Sobj"} ) {

		if( $opt_v ) {
			elog_notify( "SRB object $Scoll/$Sobj has " .
				"already been extracted\n" );
		}

		next;
	}

	if( -e "$path" ) {
		
		elog_complain( "Will not overwrite '$path'! Skipping, " .
		     "removing already added wfdisc row\n" );

		dbdelete( @dbout );

		next;
	}

	if( $opt_v ) {
	
		elog_notify( "Extracting SRB object $Scoll/$Sobj to $path\n" );
	}

	$rc = system( "$Sget_path $v $Scoll/$Sobj $path" );

	if( $rc == -1 ) {
			
		elog_die( "Failed to launch $Sget: $!. Bye!\n" );	

	} elsif( $rc != 0 ) {

		elog_complain( "Sget failed for '$Scoll/$Sobj'! " .
		 "Removing newly added wfdisc row.\n" );
	
		dbdelete( @dbout );
	}

	$Extracted{"$Scoll/$Sobj"}++;
}

if( -e "$dbout.wfdisc" && -z "$dbout.wfdisc" ) {
	
	if( $opt_v ) {

		elog_notify( "Removing zero-length file $dbout.wfdisc\n" );
	}

	unlink( "$dbout.wfdisc" );
}

if( $opt_v ) {

	elog_notify( "Ending $Program run at " .
		epoch2str( str2epoch( "now" ), "%D %T %Z", "" ) );
}
