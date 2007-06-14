
#
#   Copyright (c) 2007 Lindquist Consulting, Inc.
#   All rights reserved. 
#                                                                     
#   Written by Dr. Kent Lindquist, Lindquist Consulting, Inc. 
#
#   This software is licensed under the New BSD license: 
#
#   Redistribution and use in source and binary forms,
#   with or without modification, are permitted provided
#   that the following conditions are met:
#   
#   * Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#   
#   * Redistributions in binary form must reproduce the
#   above copyright notice, this list of conditions and
#   the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#   
#   * Neither the name of Lindquist Consulting, Inc. nor
#   the names of its contributors may be used to endorse
#   or promote products derived from this software without
#   specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
#   CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#   WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#   WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#   PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
#   THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
#   IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
#   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#   POSSIBILITY OF SUCH DAMAGE.
#

use Datascope ;
use codartools;
use hfradartools;
require "getopts.pl";

sub inform {
	my( $msg ) = @_;

	if( $opt_v ) {

		elog_notify( "$msg" );
	}
}

chomp( $Program = `basename $0` );

elog_init( $Program, @ARGV );

$Pf = "$Program.pf";

$Usage = "Usage: $Program [-o] [-v] [-p pfname] [-n net] [-s sta] [-b patterntype] [-t time] dbname filename\n";

if( ! &Getopts( 'op:s:vn:s:b:t:' ) || scalar( @ARGV ) < 2 ) {

	die( "$Usage" );
}

inform( "hfradar2db starting at " .
	strtime( str2epoch( "now" ) ) .
	" (hfradar2db \$Revision: 1.4 $\ " .
	"\$Date: 2007/06/14 06:20:37 $\)\n" );

if( $opt_p ) {
	
	$Pf = $opt_p;
}

$dfiles_pattern = pfget( $Pf, "dfiles_pattern" );
$format = pfget( $Pf, "format" );
$table = pfget( $Pf, "table" );
$net_regex = pfget( $Pf, "net" );
$sta_regex = pfget( $Pf, "site" );
$patterntype_regex = pfget( $Pf, "patterntype" );
$time_regex = pfget( $Pf, "timestamp" );

if( $opt_v ) {

	$hfradartools::Verbose++;
	$codartools::Verbose++;
}

if( $opt_o ) {

	$overwrite = 1;

} else {

	$overwrite = 0;
}

$dbname = shift( @ARGV );

if( ! -e "$dbname" ) {

	inform( "Creating database $dbname\n" );

	dbcreate( $dbname, $hfradartools::Schema );
}

@db = dbopen( $dbname, "r+" );

$dbdir = (parsepath( "$dbname" ))[0];

@filelist = @ARGV;

foreach $filename ( @filelist ) {

	$filesize = (stat($filename))[7];

	open( F, "$filename" );
	read( F, $block, $filesize );
	close( F );
	
	# Use a temporary variable called $dfile to conform to the definitions 
	# used for eval() code in hfradar2db.pf (matching formalism with 
	# hfradar2orb.pf):

	( $dfile, $suffix ) = (parsepath( "$filename" ))[1..2];
	if( $suffix ) {
		$dfile .= "." . $suffix;
	}


	undef( $net );
	undef( $sta );
	undef( $patterntype );
	undef( $time );

	if( $opt_n ) {

		$net = $opt_n;

	} else {
			
		eval( "$net_regex" );
	}

	if( $opt_s ) {
	
		$sta = $opt_s;

	} else { 

		eval( "$sta_regex" );
		$sta = $site;
	}

	if( $opt_b ) {

		$patterntype = $opt_b;

	} else {

		eval( "$patterntype_regex" );
	}

	if( $opt_t ) {

		$time = str2epoch( $opt_t );

	} else {

		eval( "$time_regex" );
		$time = $timestamp;
	}

	if( ! defined( $net ) ) {
		
		elog_complain( "Skipping '$filename', 'net' is not defined!\n" );

		next;
	}

	if( ! defined( $sta ) ) {
		
		elog_complain( "Skipping '$filename', 'sta' is not defined!\n" );

		next;
	}

	if( ! defined( $patterntype ) ) {
		
		elog_complain( "Skipping '$filename', 'patterntype' is not defined!\n" );

		next;
	}

	if( ! defined( $time ) ) {
		
		elog_complain( "Skipping '$filename', 'time' is not defined!\n" );

		next;
	}

	my( $dir, $dfile, $mtime ) = 
	hfradartools::write_radialfile( $dfiles_pattern,
					$dbdir, 
					$overwrite,
					$net,
					$sta,
					$time,
					$format,
					$patterntype,
					$block );

	if( ! defined( $dir ) ) {
	
		elog_complain( "Failed to write file '$filename' to " .
			       "database, skipping!\n" );

		next;
	}

	my( %vals ) = hfradartools::dbadd_metadata( \@db, $net, $sta, $time,
		$format, $patterntype, $block );

	hfradartools::dbadd_diagnostics( \@db, $net, $sta, $time, 
		$format, $patterntype, $block );

	hfradartools::dbadd_radialfile( @db, $net, $sta, $time, $format,
		$patterntype, $dir, $dfile, $mtime, \%vals );

}
