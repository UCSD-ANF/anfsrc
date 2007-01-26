
#
#   Copyright (c) 2004-2006 Lindquist Consulting, Inc.
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
require "getopts.pl";

sub inform {
	my( $msg ) = @_;

	if( $opt_v ) {

		elog_notify( "$msg" );
	}
}

sub dbadd_metadata {
	my( $block ) = pop( @_ );
	my( $patterntype ) = pop( @_ );
	my( $format ) = pop( @_ );
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

	@db = dblookup( @db, "", "site", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\" && " .
			    "sta == \"$sta\" && " .
			    "endtime >= $time",
			     -1 );

	if( $rec < 0 ) {

		$key = "$net:$sta";

		if( defined( $Stanames{$key} ) ) {

			$staname = $Stanames{$key};

		} else {

			$staname = "-";
		}

		$rc = dbaddv( @db, 
			"net", $net,
			"sta", $sta,
			"staname", $staname,
			"time", $time,
			"lat", $lat,
			"lon", $lon,
			);

		if( $rc < dbINVALID ) {
			@dbthere = @db;
			$dbthere[3] = dbINVALID - $rc - 1 ;
			( $matchnet, $matchsta, $matchtime, 
			  $matchlat, $matchlon, $matchstaname ) =
		   		dbgetv( @dbthere, "net", "sta", "time", 
						  "lat", "lon", "staname" );
			
			elog_complain( "Row conflict in site table (Old, new): " .
				       "net ($net, $matchnet); " .
				       "sta ($sta, $matchsta); " .
				       "staname ($sta, $matchstaname); " .
				       "time ($time, $matchtime); " .
				       "lat ($lat, $matchlat); " .
				       "lon ($lon, $matchlon); " .
				       "Please fix by hand (site row needs enddate?) " 
				       );
		} 

	} else {

		@dbt = @db;
		$dbt[3] = $rec;

		@dbscratch = @db;
		$dbscratch[3] = dbSCRATCH;
		dbputv( @dbscratch, "lat", $lat, "lon", $lon, );
		($lat, $lon) = dbgetv( @dbscratch, "lat", "lon" );

		( $matchlat, $matchlon, $matchtime ) = 
			dbgetv( @dbt, "lat", "lon", "time" );

		if( $lat == $matchlat &&
		    $lon == $matchlon ) {

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
				       "Please fix by hand " .
				       "(packets earlier than an existing row are coming " .
				       "in with different lat/lon?)\n" 
				       );
		}
	}

	@db = dblookup( @db, "", "network", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\"", -1 );

	if( $rec < 0 ) {

		$rc = dbaddv( @db, "net", $net );
	}

	my( $cfreq ) = -9999.0;
	my( $range_res ) = -9999.0;
	my( $ref_bearing ) = -9999.0;
	my( $dres ) = -9999.0;
	my( $manufacturer ) = "-";
	my( $xmit_sweep_rate ) = -9999.0;
	my( $xmit_bandwidth ) = -9999.0;
	my( $max_curr_lim ) = -9999.0;
	my( $min_rad_vect_pts ) = -1;
	my( $loop1_amp_corr ) = -9999.0;
	my( $loop2_amp_corr ) = -9999.0;
	my( $loop1_phase_corr ) = -9999.0;
	my( $loop2_phase_corr ) = -9999.0;
	my( $bragg_smooth_pts ) = -1;
	my( $rad_bragg_peak_dropoff ) = -9999.0;
	my( $second_order_bragg ) = -1;
	my( $rad_bragg_peak_null ) = -9999.0;
	my( $rad_bragg_noise_thr ) = -9999.0;
	my( $music_param_01 ) = -9999.0;
	my( $music_param_02 ) = -9999.0;
	my( $music_param_03 ) = -9999.0;
	my( $ellip ) = "-";
	my( $earth_radius ) = -9999.0;
	my( $ellip_flatten ) = -9999.0;
	my( $rad_merger_ver ) = "-";
	my( $spec2rad_ver ) = "-";
	my( $ctf_ver ) = "-";
	my( $lluvspec_ver ) ="-"; 
	my( $geod_ver ) = "-";
	my( $rad_slider_ver ) = "-"; 
	my( $rad_archiver_ver ) = "-";
	my( $patt_date ) = -9999999999.99900;
	my( $patt_res ) = -9999.0;
	my( $patt_smooth ) = -9999.0;
	my( $spec_range_cells ) = -1;
	my( $spec_doppler_cells ) = -1;
	my( $curr_ver ) = "-";
	my( $codartools_ver ) = "-"; 
	my( $first_order_calc ) = -1;
	my( $lluv_tblsubtype ) = "-";
	my( $proc_by ) = "-";
	my( $merge_method ) = -1;
	my( $patt_method ) = -1;
	
	if( defined( $vals{TransmitCenterFreqMHz} ) ) {
	
		$cfreq = $vals{TransmitCenterFreqMHz};
	}

	if( defined( $vals{RangeResolutionKMeters} ) ) {
	
		$range_res = $vals{RangeResolutionKMeters};
	}

	if( defined( $vals{ReferenceBearing} ) ) {
	
		$ref_bearing = $vals{ReferenceBearing};
	}

	if( defined( $vals{DopplerResolutionHzPerBin} ) ) {
	
		$dres = $vals{DopplerResolutionHzPerBin};
	}

	if( defined( $vals{Manufacturer} ) ) {
	
		$manufacturer = $vals{Manufacturer};
	}

	if( defined( $vals{TransmitSweepRateHz} ) ) {
	
		$xmit_sweep_rate = $vals{TransmitSweepRateHz};
	}

	if( defined( $vals{TransmitBandwidthKHz} ) ) {
	
		$xmit_bandwidth = $vals{TransmitBandwidthKHz};
	}

	if( defined( $vals{CurrentVelocityLimit} ) ) {
	
		$max_curr_lim = $vals{CurrentVelocityLimit};
	}

	if( defined( $vals{RadialMinimumMergePoints} ) ) {
	
		$min_rad_vect_pts = $vals{RadialMinimumMergePoints};
	}

	foreach $keyname qw( loop1_amp_corr 
			     loop2_amp_corr 
			     loop1_phase_corr
			     loop2_phase_corr
			     music_param_01
			     music_param_02
			     music_param_03
			     ellip
			     earth_radius
			     ellip_flatten
			     rad_merger_ver
			     spec2rad_ver
			     ctf_ver
			     lluvspec_ver
			     geod_ver
			     rad_slider_ver
			     rad_archiver_ver
			     patt_date
			     patt_res
			     patt_smooth
			     spec_range_cells
			     spec_doppler_cells
			     curr_ver
			     codartools_ver
			     first_order_calc
			     lluv_tblsubtype
			     proc_by
			     merge_method
			     patt_method
					    ) {

		if( defined( $vals{$keyname} ) ) {
	
			eval( "\$$keyname = \$vals{$keyname};" );
		}
	}


	if( defined( $vals{BraggSmoothingPoints} ) ) {
	
		$bragg_smooth_pts = $vals{BraggSmoothingPoints};
	}

	if( defined( $vals{RadialBraggPeakDropOff} ) ) {
	
		$rad_bragg_peak_dropoff = $vals{RadialBraggPeakDropOff};
	}

	if( defined( $vals{BraggHasSecondOrder} ) ) {
	
		$second_order_bragg = $vals{BraggHasSecondOrder};
	}

	if( defined( $vals{RadialBraggPeakNull} ) ) {
	
		$rad_bragg_peak_null = $vals{RadialBraggPeakNull};
	}

	if( defined( $vals{RadialBraggNoiseThreshold} ) ) {
	
		$rad_bragg_noise_thr = $vals{RadialBraggNoiseThreshold};
	}

	@db = dblookup( @db, "", "radialmeta", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\" && " .
			    "sta == \"$sta\" && " .
			    "format == \"$format\" && " .
			    "patterntype == \"$patterntype\" && " .
			    "time <= $time && $time <= endtime",
			     -1 );

	if( $rec < 0 ) {

		$rc = dbaddv( @db, 
			"net", $net,
			"sta", $sta,
			"format", $format,
			"patterntype", $patterntype,
			"time", $time,
			"endtime", $time,
			"cfreq", $cfreq,
			"range_res", $range_res,
			"ref_bearing", $ref_bearing,
			"dres", $dres,
			"manufacturer", $manufacturer,
			"xmit_sweep_rate", $xmit_sweep_rate,
			"xmit_bandwidth", $xmit_bandwidth,
			"max_curr_lim", $max_curr_lim,
			"min_rad_vect_pts", $min_rad_vect_pts,
			"loop1_amp_corr", $loop1_amp_corr,
			"loop2_amp_corr", $loop2_amp_corr,
			"loop1_phase_corr", $loop1_phase_corr,
			"loop2_phase_corr", $loop2_phase_corr,
			"bragg_smooth_pts", $bragg_smooth_pts,
			"rad_bragg_peak_dropoff", $rad_bragg_peak_dropoff,
			"second_order_bragg", $second_order_bragg,
			"rad_bragg_peak_null", $rad_bragg_peak_null,
			"rad_bragg_noise_thr", $rad_bragg_noise_thr,
			"music_param_01", $music_param_01,
			"music_param_02", $music_param_02,
			"music_param_03", $music_param_03,
			"ellip", $ellip,
			"earth_radius", $earth_radius,
			"ellip_flatten", $ellip_flatten,
			"rad_merger_ver", $rad_merger_ver,
			"spec2rad_ver", $spec2rad_ver,
			"ctf_ver", $ctf_ver,
			"lluvspec_ver", $lluvspec_ver,
			"geod_ver", $geod_ver,
			"rad_slider_ver", $rad_slider_ver,
			"rad_archiver_ver", $rad_archiver_ver,
			"patt_date", $patt_date,
			"patt_res", $patt_res,
			"patt_smooth", $patt_smooth,
			"spec_range_cells", $spec_range_cells,
			"spec_doppler_cells", $spec_doppler_cells,
			"curr_ver", $curr_ver,
			"codartools_ver", $codartools_ver,
			"first_order_calc", $first_order_calc,
			"lluv_tblsubtype", $lluv_tblsubtype,
			"proc_by", $proc_by,
			"merge_method", $merge_method,
			"patt_method", $patt_method,
			);

		if( $rc < dbINVALID ) {

			elog_complain( "Failed to add radialmeta row " .
				"(rc $rc) " . 
				"for $net $sta $format $patterntype " .
				strtime( $time ) . " !!\n" );
		} 

	} else {

		@dbt = @db;
		$dbt[3] = $rec;

		( $matchtime, $matchendtime ) = 
			dbgetv( @dbt, "time", "endtime" );

		if( ( $matchtime != $matchendtime ) || 
		    ( $matchtime != $time ) ) {

		    elog_complain( "SCAFFOLD Packet appears to overlap " .
			"an already-condensed row; will not modify database " .
			"for $net $sta $format $patterntype " .
			strtime( $time ) . "\n" );

	     	    # SCAFFOLD	
		    # NB could check to see if metadata match and 
		    # let the code move on if so (no harm, db is consistent) 
		    # Or could add with a '+' tacked to station name
		    # (may have to do that anyway for row clashes...
		    # if we can avoid problems with recursion in the clash...)

		} else {

			$rc = dbputv( @dbt, 
				"cfreq", $cfreq,
				"range_res", $range_res,
				"ref_bearing", $ref_bearing,
				"dres", $dres,
				"manufacturer", $manufacturer,
				"xmit_sweep_rate", $xmit_sweep_rate,
				"xmit_bandwidth", $xmit_bandwidth,
				"max_curr_lim", $max_curr_lim,
				"min_rad_vect_pts", $min_rad_vect_pts,
				"loop1_amp_corr", $loop1_amp_corr,
				"loop2_amp_corr", $loop2_amp_corr,
				"loop1_phase_corr", $loop1_phase_corr,
				"loop2_phase_corr", $loop2_phase_corr,
				"bragg_smooth_pts", $bragg_smooth_pts,
				"rad_bragg_peak_dropoff", $rad_bragg_peak_dropoff,
				"second_order_bragg", $second_order_bragg,
				"rad_bragg_peak_null", $rad_bragg_peak_null,
				"rad_bragg_noise_thr", $rad_bragg_noise_thr,
				"music_param_01", $music_param_01,
				"music_param_02", $music_param_02,
				"music_param_03", $music_param_03,
				"ellip", $ellip,
				"earth_radius", $earth_radius,
				"ellip_flatten", $ellip_flatten,
				"rad_merger_ver", $rad_merger_ver,
				"spec2rad_ver", $spec2rad_ver,
				"ctf_ver", $ctf_ver,
				"lluvspec_ver", $lluvspec_ver,
				"geod_ver", $geod_ver,
				"rad_slider_ver", $rad_slider_ver,
				"rad_archiver_ver", $rad_archiver_ver,
				"patt_date", $patt_date,
				"patt_res", $patt_res,
				"patt_smooth", $patt_smooth,
				"spec_range_cells", $spec_range_cells,
				"spec_doppler_cells", $spec_doppler_cells,
				"curr_ver", $curr_ver,
				"codartools_ver", $codartools_ver,
				"first_order_calc", $first_order_calc,
				"lluv_tblsubtype", $lluv_tblsubtype,
				"proc_by", $proc_by,
				"merge_method", $merge_method,
				"patt_method", $patt_method,
				);

			if( $rc < 0 ) {

		    		elog_complain( "Row modification failed for " .
					"radialmeta data from " .
					"$net $sta $format $patterntype " .
					strtime( $time ) . " !!\n" );
			}
		}
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
	     " (orbhfradar2db \$Revision: 1.21 $\ " .
	     "\$Date: 2007/01/26 13:42:02 $\)\n" );


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

	@dbs = dblookup( @db, "", "site", "", "" );

	@dbs = dbsort( @dbs, "time" );

	$nsites = dbquery( @dbs, dbRECORD_COUNT );

	for( $dbs[3] = 0; $dbs[3] < $nsites; $dbs[3]++ ) {
	
		( $net, $sta, $staname ) = dbgetv( @dbs, "net", "sta",
							 "staname" );

		$key = "$net:$sta";

		if( $staname ne "-" ) {
		
			$Stanames{$key} = $staname;
		}
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

		my( %vals ) = dbadd_metadata( @db, $net, $sta, $time, 
					$format, $patterntype, $block );

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
				"loop1_amp_calc", $loop1_amp_calc,
				"loop2_amp_calc", $loop2_amp_calc,
				"loop1_phase_calc", $loop1_phase_calc,
				"loop2_phase_calc", $loop2_phase_calc,
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
			dbputv( @dbt, 
				"mtime", $mtime,
				"sampling_period_hrs", $sampling_period_hrs,
				"nmerge_rads", $nmerge_rads,
				"range_bin_start", $range_bin_start,
				"range_bin_end", $range_bin_end,
				"loop1_amp_calc", $loop1_amp_calc,
				"loop2_amp_calc", $loop2_amp_calc,
				"loop1_phase_calc", $loop1_phase_calc,
				"loop2_phase_calc", $loop2_phase_calc,
				"nrads", $nrads,
				"proc_time", $proc_time,
				);

		}
	}
}
