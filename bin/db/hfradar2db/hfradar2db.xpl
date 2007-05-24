
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
use orb;
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

$Usage = "Usage: $Program [-o] [-v] [-p pfname] -s dbname filename net sta patterntype time\n";

if( ! &Getopts( 'op:sv' ) ) {

	die( "$Usage" );
}

if( $opt_s && scalar( @ARGV ) != 6 ) {

	die( "$Usage" );
}

inform( "orbhfradar2db starting at " .
	strtime( str2epoch( "now" ) ) .
	" (orbhfradar2db \$Revision: 1.1 $\ " .
	"\$Date: 2007/05/24 00:50:02 $\)\n" );

if( $opt_p ) {
	
	$Pf = $opt_p;
}

if( $opt_v ) {

	$hfradartools::Verbose++;
	$codartools::Verbose++;
}

if( $opt_o ) {

	$overwrite = 1;

} else {

	$overwrite = 0;
}

$dbname = $ARGV[0];

if( ! -e "$dbname" ) {

	inform( "Creating database $dbname\n" );

	dbcreate( $dbname, $hfradartools::Schema );
}

@db = dbopen( $dbname, "r+" );

$dbdir = (parsepath( "$dbname" ))[0];

if( $opt_s ) {
	
	$filename = $ARGV[1];
	$net = $ARGV[2];
	$sta = $ARGV[3];
	$patterntype = $ARGV[4];
	$time = str2epoch( $ARGV[5] );

	$filesize = (stat($filename))[7];
}

$dfiles_pattern = pfget( $Pf, "dfiles_pattern" );
$format = pfget( $Pf, "format" );
$table = pfget( $Pf, "table" );

open( F, "$filename" );
read( F, $block, $filesize );
close( F );

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
	
	elog_die( "Failed to write file to database\n" );
}

my( %vals ) = hfradartools::dbadd_metadata( \@db, $net, $sta, $time,
	$format, $patterntype, $block );

hfradartools::dbadd_radialfile( @db, $net, $sta, $time, $format,
	$patterntype, $dir, $dfile, $mtime, \%vals );



