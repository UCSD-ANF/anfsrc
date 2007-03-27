
#
#   Copyright (c) 2004-2007 Lindquist Consulting, Inc.
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

if( ! &Getopts('m:r:d:p:a:S:ov') || $#ARGV != 1 ) {

	die( "Usage: $Program [-v] [-o] [-m match] [-r reject] " .
		"[-p pffile] [-S statefile] [-a after] " .
		"[-d dbname] orbname builddir\n" );

} else {

	$orbname = $ARGV[0];
	$builddir = $ARGV[1];
} 

inform( "orbhfradar2db starting at " . 
	     strtime( str2epoch( "now" ) ) . 
	     " (orbhfradar2db \$Revision: 1.31 $\ " .
	     "\$Date: 2007/03/27 23:44:53 $\)\n" );

if( $opt_v ) {

	$hfradartools::Verbose++;
	$codartools::Verbose++;
}

if( $opt_d ) {

	$trackingdb = $opt_d;

	if( ! -e "$trackingdb" ) {

		inform( "Creating tracking-database $trackingdb\n" );

		dbcreate( $trackingdb, $hfradartools::Schema );	
	}

	@db = dbopen( $trackingdb, "r+" );

	my( $open_schema ) = dbquery( @db, dbSCHEMA_NAME );

	if( $open_schema ne $hfradartools::Schema ) {
		
		elog_die( "database '$trackingdb' uses schema " .
			  "'$open_schema' which does not match the schema " .
			  "'$hfradartools::Schema' assumed by orbhfradar2db. Bye!\n" );
	}

}

if( $opt_p ) { 

	$Pfname = $opt_p;

} else { 

	$Pfname = $Program;
}


$orbfd = orbopen( $orbname, "r&" );

if( $orbfd < 0 ) {
	die( "Failed to open $orbname for reading!\n" );
}

if( $opt_S ) {

	$stop = 0;
	exhume( $opt_S, \$stop, 15 );
	orbresurrect( $orbfd, \$pktid, \$time  );
	orbseek( $orbfd, "$pktid" );
}

if( $opt_a eq "oldest" ) {

	inform( "Repositioning orb pointer to oldest packet\n" );

	orbseek( $orbfd, "ORBOLDEST" );

} elsif( $opt_a ) {
	
	inform( "Repositioning orb pointer to time $opt_a\n" );

	orbafter( $orbfd, str2epoch( $opt_a ) );
}

%formats = %{pfget( $Pfname, "formats" )};

if( $opt_m ) {
	
	$match = $opt_m;

} else {

	$match = ".*/(";

	foreach $format ( keys %formats ) {

		$match .= "$format|";
	}

	substr( $match, -1, 1, ")" );
}

inform( "orbhfradar2db: using match expression \"$match\"\n" );

orbselect( $orbfd, $match );

if( $opt_r ) {

	inform( "orbhfradar2db: using reject expression \"$opt_r\"\n" );

	orbreject( $orbfd, $opt_r );
}

for( ; $stop == 0; ) {

	($pktid, $srcname, $time, $packet, $nbytes) = orbreap( $orbfd );

	if( $opt_S ) {
		
		bury();
	}

	next if( $opt_a && $opt_a ne "oldest" && $time < str2epoch( "$opt_a" ) );

	inform( "received $srcname timestamped " . strtime( $time ) . "\n" );

	undef( $net );
	undef( $sta );
	undef( $pktsuffix );

	( $net, $sta, $pktsuffix ) = ( $srcname =~ m@^([^/_]*)_([^/_]*)/(.*)@ );

	if( ! defined( $net ) || ! defined( $sta ) || ! defined( pktsuffix ) ) {
		
		elog_complain( "orbhfradar2db: failure parsing source-name " .
				"'$srcname' into 'net_sta/suffix', skipping\n" );

		next;
	}

	$format = $formats{$pktsuffix}->{format};

	( $version, $block ) = unpack( "na*", $packet );

	if( $version == 100 ) {

		elog_complain( "WARNING: orb-hfradar packet-version 100 is " .
			"no longer supported because it does not fully " .
			"support multiple patterntypes. Please upgrade your " .
			"acquisition code; skipping packet!\n" );
		
		next;

		$patterntype = "-";

	} elsif( $version == 110 ) {

		( $patterntype, $block ) = unpack( "aa*", $block );
			
	} else {
		
		elog_complain( "Unsupported version number $version for $srcname, " . 
				strtime( $time ) . " in orbhfradar2db\n" );

		next;
	}

	$table = $formats{$pktsuffix}->{table};

	if( $table ne "radialfiles" ) {

		elog_complain( "Unsupported table type $table for $srcname, " . 
				strtime( $time ) . " in orbhfradar2db\n" );

		next;

	}

	$dfiles_pattern = $formats{$pktsuffix}->{dfiles_pattern};
	$dfiles_pattern =~ s/%{net}/$net/g;
	$dfiles_pattern =~ s/%{sta}/$sta/g;
	$dfiles_pattern =~ s/%{format}/$format/g;
	$dfiles_pattern =~ s/%{patterntype}/$patterntype/g;

	$relpath = epoch2str( $time, $dfiles_pattern );

	$relpath = concatpaths( $builddir, $relpath );

	( $subdir, $dfile, $suffix ) = parsepath( $relpath );

	if( "$suffix" ) { $dfile .= ".$suffix" }

	if( -e "$relpath" && ! $opt_o ) {

		if( $opt_v ) {
			
			elog_complain( "Won't overwrite $relpath; file exists\n" );
		}

		next;
	}

	system( "mkdir -p $subdir" );

	# it's possible the path is already absolute, though not guaranteed. 
	# treat as though it were relative:

	$abspath = abspath( $relpath );

	( $dir, $dfile, $suffix ) = parsepath( $abspath );

	if( "$suffix" ) { $dfile .= ".$suffix" }

	inform( "Creating $abspath\n" );

	open( F, ">$relpath" );
	print F $block;
	close( F );

	if( $opt_d ) {

		# DEBUG add relpath temporarily

		my( %vals ) = hfradartools::dbadd_metadata( \@db, $net, $sta, $time, 
					$format, $patterntype, $relpath, $block );

		hfradartools::dbadd_radialfile( @db, $net, $sta, $time, $format, 
			$patterntype, $dir, $dfile, $relpath, \%vals );

	}
}
