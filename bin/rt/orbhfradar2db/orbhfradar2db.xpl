#
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
#

use Datascope ;
use orb;
use codartools;
require "getopts.pl";

sub inform {
	my( $msg ) = @_;

	if( $opt_v ) {

		elog_notify( "$msg" );
	}
}

sub dbadd_metadata {
	my( $block ) = pop( @_ );
	my( $time ) = pop( @_ );
	my( $sta ) = pop( @_ );
	my( $net ) = pop( @_ );
	my( @db ) = @_;

	my( @block ) = split( /\r?\n/, $block );

	if( ! codartools::is_valid_lluv( @block ) ) {

		elog_complain( "Packet from '$net', '$sta' timestamped " . strtime( $time ) .
			       " is not valid LLUV format; omitting addition of station, " .
			       "network and metadata to database\n" );
		return;
	}

	my( %vals ) = codartools::lluv2hash( @block );

	my( $lat ) = $vals{Lat};
	my( $lon ) = $vals{Lon};
	my( $cfreq ) = $vals{TransmitCenterFreqMHz};

	@db = dblookup( @db, "", "site", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\" && " .
			    "sta == \"$sta\" && " .
			    "endtime >= $time",
			     -1 );

	if( $rec < 0 ) {

		$rc = dbaddv( @db, 
			"net", $net,
			"sta", $sta,
			"time", $time,
			"lat", $lat,
			"lon", $lon,
			"cfreq", $cfreq );

		if( $rc < dbINVALID ) {
			@dbthere = @db;
			$dbthere[3] = dbINVALID - $rc - 1 ;
			( $matchnet, $matchsta, $matchtime, 
			  $matchlat, $matchlon, $matchcfreq ) =
		   		dbgetv( @dbthere, "net", "sta", "time", 
						  "lat", "lon", "cfreq" );
			
			elog_complain( "Row conflict in site table (Old, new): " .
				       "net ($net, $matchnet); " .
				       "sta ($sta, $matchsta); " .
				       "time ($time, $matchtime); " .
				       "lat ($lat, $matchlat); " .
				       "lon ($lon, $matchlon); " .
				       "cfreq ($cfreq, $matchcfreq); " .
				       "Please fix by hand (site row needs enddate?) " 
				       );
		} 

	} else {

		@dbt = @db;
		$dbt[3] = $rec;

		@dbscratch = @db;
		$dbscratch[3] = dbSCRATCH;
		dbputv( @dbscratch, "lat", $lat, "lon", $lon, "cfreq", $cfreq );
		($lat, $lon, $cfreq) = dbgetv( @dbscratch, "lat", "lon", "cfreq" );

		( $matchlat, $matchlon, $matchcfreq, $matchtime ) = 
			dbgetv( @dbt, "lat", "lon", "cfreq", "time" );

		if( $lat == $matchlat &&
		    $lon == $matchlon &&
		    $cfreq == $matchcfreq ) {

			if( $time < $matchtime ) {

				inform( "Advancing start time for $net,$sta site-table row " . 
			   	   "from " . strtime($matchtime) . " to " . strtime( $time ) .
				   "\n" );

				dbputv( @dbt, "time", $time );
			}

		} else {

			elog_complain( "Row conflict in site table for $net, $sta: " .
				       "time ($time, $matchtime); " .
				       "lat ($lat, $matchlat); " .
				       "lon ($lon, $matchlon); " .
				       "cfreq ($cfreq, $matchcfreq); " .
				       "Please fix by hand " .
				       "(packets earlier than an existing row are coming " .
				       "in with different lat/lon/cfreq?)\n" 
				       );
		}
	}

	@db = dblookup( @db, "", "network", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\"", -1 );

	if( $rec < 0 ) {

		$rc = dbaddv( @db, "net", $net );
	}

	 return %vals;
}

$Schema = "Hfradar0.6";

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('m:r:d:p:a:S:ov') || $#ARGV != 1 ) {

	die( "Usage: $Program [-v] [-o] [-m match] [-r reject] [-p pffile] [-S statefile] [-a after] [-d dbname] orbname builddir\n" );

} else {

	$orbname = $ARGV[0];
	$builddir = $ARGV[1];
} 

inform( "orbhfradar2db starting at " . 
	     strtime( str2epoch( "now" ) ) . 
	     " (orbhfradar2db \$Revision: 1.13 $\ " .
	     "\$Date: 2006/11/06 23:50:24 $\)\n" );


if( $opt_d ) {

	$trackingdb = $opt_d;

	if( ! -e "$trackingdb" ) {

		inform( "Creating tracking-database $trackingdb\n" );

		dbcreate( $trackingdb, $Schema );	
	}

	@db = dbopen( $trackingdb, "r+" );

	my( $open_schema ) = dbquery( @db, dbSCHEMA_NAME );

	if( $open_schema ne $Schema ) {
		
		elog_die( "database '$dbname' uses schema " .
			  "'$open_schema' which does not match the schema " .
			  "'$Schema' assumed by orbhfradar2db. Bye!\n" );
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

		my( %vals ) = dbadd_metadata( @db, $net, $sta, $time, $block );

		my( $sampling_period_hrs ) = -9999.0;
		my( $loop1_amp_calc ) = -9999.0;
		my( $loop2_amp_calc ) = -9999.0;
		my( $loop1_phase_calc ) = -9999.0;
		my( $loop2_phase_calc ) = -9999.0;
		my( $nmerge_rads ) = -1;
		my( $nrads ) = -1;
		my( $range_bin_start ) = -1;
		my( $range_bin_end ) = -1;
		my( $proc_time ) = -9999999999.99900;

		if( defined( $vals{TimeCoverage} ) ) {
			
			$sampling_period_hrs = $vals{TimeCoverage} / 60;
		}

		if( defined( $vals{MergedCount} ) ) {
			
			$nmerge_rads = $vals{MergedCount};
		}

		if( defined( $vals{RangeStart} ) ) {
			
			$range_bin_start = $vals{RangeStart};
		}

		if( defined( $vals{RangeEnd} ) ) {
			
			$range_bin_end = $vals{RangeEnd};
		}

		if( defined( $vals{loop1_amp_calc} ) ) {
			
			$loop1_amp_calc = $vals{loop1_amp_calc};
		}

		if( defined( $vals{loop2_amp_calc} ) ) {
			
			$loop2_amp_calc = $vals{loop2_amp_calc};
		}

		if( defined( $vals{loop1_phase_calc} ) ) {
			
			$loop1_phase_calc = $vals{loop1_phase_calc};
		}

		if( defined( $vals{loop2_phase_calc} ) ) {
			
			$loop2_phase_calc = $vals{loop2_phase_calc};
		}

		if( defined( $vals{nrads} ) ) {
			
			$nrads = $vals{nrads};
		}

		if( defined( $vals{proc_time} ) ) {
			
			$proc_time = $vals{proc_time};
		}

		$mtime = (stat("$relpath"))[9];

		$table = $formats{$pktsuffix}->{table};

		@db = dblookup( @db, "", "$table", "", "" );

		$db[3] = dbquery( @db, dbRECORD_COUNT );

		$rec = dbfind( @db, "net == \"$net\" && " .
				    "sta == \"$sta\" && " .
				    "time == $time && " .
				    "format == \"$format\" && " .
				    "patterntype == \"$patterntype\"",
				     -1 );

		if( $rec < 0 ) {

			$rc = dbaddv( @db, 
				"net", $net,
				"sta", $sta,
				"time", $time,
				"format", $format,
				"patterntype", $patterntype,
				"mtime", $mtime,
				"dir", $dir,
				"dfile", $dfile,
				"sampling_period_hrs", $sampling_period_hrs,
				"nmerge_rads", $nmerge_rads,
				"range_bin_start", $range_bin_start,
				"range_bin_end", $range_bin_end,
				"nrads", $nrads,
				"proc_time", $proc_time,
				);

			if( $rc < dbINVALID ) {
				@dbthere = @db;
				$dbthere[3] = dbINVALID - $rc - 1 ;
				( $matchnet, $matchsta, $matchtime, 
				  $matchformat, $matchpatterntype,
				  $matchmtime, $matchdir, $matchdfile ) =
			   		dbgetv( @dbthere, "net", "sta", "time", "format", 
							  "patterntype", "mtime", 
							  "dir", "dfile" );
				
				elog_complain( "Row conflict (Old, new): " .
					       "net ($net, $matchnet); " .
					       "sta ($sta, $matchsta); " .
					       "time ($time, $matchtime); " .
					       "format ($format, $matchformat); " .
					       "patterntype ($patterntype, $matchpatterntype); " .
					       "mtime ($mtime, $matchmtime); " .
					       "dir ($dir, $matchdir); " .
					       "dfile ($dfile, $matchdfile)\n" );
			} 

		} else {

			@dbt = @db;
			$dbt[3] = $rec;
			dbputv( @dbt, "mtime", $mtime );

		}
	}
}
