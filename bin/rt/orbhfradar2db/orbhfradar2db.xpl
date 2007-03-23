
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
use rtmail;
require "getopts.pl";

sub inform {
	my( $msg ) = @_;

	if( $opt_v ) {

		elog_notify( "$msg" );
	}
}

sub dbadd_site {
	my( $lon ) = pop( @_ );
	my( $lat ) = pop( @_ );
	my( $time ) = pop( @_ );
	my( $sta ) = pop( @_ );
	my( $net ) = pop( @_ );
	my( @db ) = @_;

	@db = dblookup( @db, "", "site", "", "" );

	my( @dbnull ) = dblookup( @db, "", "", "", "dbNULL" );
	my( @dbscratch ) = dblookup( @db, "", "", "", "dbSCRATCH" );

	dbputv( @dbscratch, "lat", $lat, "lon", $lon, );
	( $lat, $lon ) = dbgetv( @dbscratch, "lat", "lon" );

	my( $rec, $staname, $rc );

	# Test for a perfectly matching row:

	$rec = dbfind( @db, "net == \"$net\" && " .
			     "sta == \"$sta\" && " .
			     "lat == \"$lat\" && " .
			     "lon == \"$lon\" && " .
			     "time <= $time && " .
			     "$time <= endtime",
			     -1 );

	if( $rec >= 0 ) {

		# There's a perfect match:

		return;
	}

	# Test for brand-new site:

	$rec = dbfind( @db, "net == \"$net\" && " .
			     "sta == \"$sta\"",
			     -1 );

	if( $rec < 0 ) {

		# We've never seen it:

		inform( "Adding site row for $net\_$sta\n" );

		$rc = dbaddv( @db, 
			"net", $net,
			"sta", $sta,
			"time", $time,
			"lat", $lat,
			"lon", $lon,
			);

		if( $rc < 0 ) {

			elog_complain( "Unexpected failure adding $net\_$sta " .
			     "to site table!! dbaddv failed. \n" );

			return;

		} else {

			return;
		}
	}

	# Prepare for condensation into existing dataset:
	 
	dbget( @dbnull, 0 );

	$null_endtime = dbgetv( @dbnull, "endtime" );

	dbputv( @dbscratch, "net", $net, "sta", $sta );

	my( @rows ) = dbmatches( @dbscratch, @db, "site_hook", "net", "sta" );

	my( @times, @endtimes, @indices, @min_times, @max_endtimes );

	for( $i = 0; $i < scalar( @rows ); $i++ ) {

		$db[3] = $rows[$i];

		( $times[$i], $endtimes[$i] ) = dbgetv( @db, "time", "endtime" );
	}

	@indices = 0..$#rows;

	@indices = sort { 
				if( $times[$a] < $times[$b] ) {

					return -1;

				} elsif( $times[$a] > $times[$b] ) {
					
					return 1;

				} elsif( $endtimes[$a] < $endtimes[$b] ) {
					
					return -1;

				} elsif( $endtimes[$a] > $endtimes[$b] ) {
					
					return 1;

				} else {
					
					return 0;
				}
				
			} @indices;

	$min_times[$indices[0]] = -9999999999.999;

	for( $i = 1; $i <= $#indices; $i++ ) {

		$max_endtimes[$i-1] = $times[$i];
		$min_times[$i] = $endtimes[$i-1];
	}

	$max_endtimes[$indices[$#indices]] = 9999999999.999;

	# Test for simple move of station: 

	$db[3] = $rows[$indices[$#indices]];

	( $match_lat, $match_lon, $match_time, $match_endtime ) = 
		dbgetv( @db, "lat", "lon", "time", "endtime" );

	if( ( $time > $match_time ) && ( $match_endtime == $null_endtime ) ) {

		my( @dbr );

		@dbr = dbprocess( @db, 
			"dbopen radialfiles",
			"dbsubset net == \"$net\" && sta == \"$sta\"",
			"dbsort time" );

		$nrecs = dbquery( @dbr, dbRECORD_COUNT );

		if( $nrecs <= 0 ) {

			elog_complain( "Unexpected failure adding $net\_$sta " .
				"to site table!! No radialfiles entries " .
				"available to deduce site-table endtime " .
				"for previous row\n" );

			return;
		}

		$dbr[3] = $nrecs - 1;

		$endtime = dbgetv( @dbr, "time" );

		inform( "Closing site row for $net\_$sta at $endtime " .
			"and opening new row\n" );

		dbputv( @db, "endtime", $endtime );

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

		if( $rc < 0 ) {

			elog_complain( "Unexpected failure adding $net\_$sta " .
		     	"to site table!! dbaddv failed. \n" );

			return;

		} else {

			return;
		}
	}

	# Test for nudging an existing row:

	for( $i = 0; $i <= $#indices; $i++ ) {

		$db[3] = $rows[$indices[$i]];

		( $match_lat, $match_lon, $match_time, $match_endtime ) = 
			dbgetv( @db, "lat", "lon", "time", "endtime" );

		if( $match_time <= $time && $time <= $match_endtime &&
		    ( ( $lat != $match_lat ) || ( $lon != $match_lon ) ) ) {

			elog_complain( "WARNING: Packet $net, $sta ($lat,$lon) at " .
					strtime( $time ) . " conflicts with row " .
					"$db[3] of site database!! Unable to fix!\n" );

			return;
		}

		if( ( $lat == $match_lat ) && 
		    ( $lon == $match_lon ) &&
		    ( $time < $match_time ) && 
		    ( $time > $min_times[$indices[$i]] ) ) {

			inform( "Advancing start time for $net,$sta " .
				"site-table row $db[3] from " . 
				strtime( $match_time ) . " to " . 
				strtime( $time ) .  "\n" );

			dbputv( @db, "time", $time );

			return;
		}

		if( ( $lat == $match_lat ) && 
		    ( $lon == $match_lon ) &&
		    ( $time > $match_endtime ) && 
		    ( $time < $max_endtimes[$indices[$i]] ) ) {

			inform( "Delaying end time for $net,$sta " .
				"site-table row $db[3] from " . 
				strtime( $match_time ) . " to " . 
				strtime( $time ) .  "\n" );

			dbputv( @db, "endtime", $time );

			return;
		}
	}

	# Test for manually closed last row:

	$db[3] = $rows[$indices[$#indices]];

	( $match_endtime ) = dbgetv( @db, "endtime" );

	if( $time > $match_endtime ) {

		# Latest row already closed and lat/lon is different:

		inform( "Adding current site row for $net\_$sta\n" );

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

		if( $rc < 0 ) {

			elog_complain( "Unexpected failure adding $net\_$sta " .
			     "to site table!! dbaddv failed. \n" );

			return;

		} else {

			return;
		}
	}

	elog_complain( "WARNING: Unexpected mismatch between site database " .
			"and Packet $net, $sta ($lat, $lon) at time " . 
			strtime( $time ) . " : unable to update site database; " .
			"please diagnose and fix by hand\n" );

	return;
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

	dbadd_site( @db, $net, $sta, $time, $vals{Lat}, $vals{Lon} );

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

		eval {

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

		};

		if( $@ ne "" ) {

			elog_complain( "Unexpected dbaddv failure for radialmeta table: $@\n" );

			# DEBUG 

			elog_complain( "Sending message about rc $rc\n" );

			$msg = "Error message from eval is $@, rc $rc" .
				"net $net\nsta $sta\ntime $time\nformat $format\n" .
				"patterntype $patterntype\ndbname $trackingdb\n" . 
				"table radialmeta\nCurrent_time" . strtime( now ) . "UTC\n";

			open( F, "|mailx -s 'orbhfradar2db problem' kent\@lindquistconsulting.com,motero\@mpl.ucsd.edu" );
			print F $msg;
			close( F );

			return;
		}

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

sub dbadd_radialfile {
	my( $valsref ) = pop( @_ );
	my( $relpath ) = pop( @_ );
	my( $dfile ) = pop( @_ );
	my( $dir ) = pop( @_ );
	my( $patterntype ) = pop( @_ );
	my( $format ) = pop( @_ );
	my( $time ) = pop( @_ );
	my( $sta ) = pop( @_ );
	my( $net ) = pop( @_ );
	my( @db ) = @_;

	my( %vals ) = %{$valsref};

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

	my( $mtime ) = (stat("$relpath"))[9];

	$table = $formats{$pktsuffix}->{table};

	@db = dblookup( @db, "", "$table", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\" && " .
			    "sta == \"$sta\" && " .
			    "abs( time - $time ) < $time_epsilon_sec && " .
			    "format == \"$format\" && " .
			    "patterntype == \"$patterntype\"",
			     -1 );

	if( $rec < 0 ) {

		eval {

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
		};

		if( $@ ne "" ) {

			elog_complain( "Unexpected dbaddv failure for $table table: $@\n" );

			# DEBUG 

			elog_complain( "Sending message about rc $rc\n" );

			my( $msg ) = "Error message from eval is $@, rc $rc" .
				"net $net\nsta $sta\ntime $time\nformat $format\n" .
				"patterntype $patterntype\ndbname $trackingdb\n" . 
				"table $table\nCurrent_time" . strtime( now ) . "UTC\n";

			open( F, "|mailx -s 'orbhfradar2db problem' " .
				 "kent\@lindquistconsulting.com," .
				 "motero\@mpl.ucsd.edu" );
			print F $msg;
			close( F );

			return;
		}

		if( $rc < dbINVALID ) {
			@dbthere = @db;
			$dbthere[3] = dbINVALID - $rc - 1 ;
			my( $matchnet, $matchsta, $matchtime, 
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
	     " (orbhfradar2db \$Revision: 1.28 $\ " .
	     "\$Date: 2007/03/23 05:46:49 $\)\n" );


if( $opt_d ) {

	$trackingdb = $opt_d;

	if( ! -e "$trackingdb" ) {

		inform( "Creating tracking-database $trackingdb\n" );

		dbcreate( $trackingdb, $Schema );	
	}

	@db = dbopen( $trackingdb, "r+" );

	my( $open_schema ) = dbquery( @db, dbSCHEMA_NAME );

	if( $open_schema ne $Schema ) {
		
		elog_die( "database '$trackingdb' uses schema " .
			  "'$open_schema' which does not match the schema " .
			  "'$Schema' assumed by orbhfradar2db. Bye!\n" );
	}

	@dbs = dblookup( @db, "", "site", "", "" );

	@dbs = dbsort( @dbs, "time" );

	$nsites = dbquery( @dbs, dbRECORD_COUNT );

	for( $dbs[3] = $nsites - 1; $dbs[3] >= 0; $dbs[3]-- ) {
	
		( $net, $sta, $staname ) = dbgetv( @dbs, "net", "sta",
							 "staname" );

		$key = "$net:$sta";

		if( $staname ne "-" && ( ! defined( $Stanames{$key} ) ) ) {
		
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

$time_epsilon_sec = pfget( $Pfname, "time_epsilon_sec" );

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

		dbadd_radialfile( @db, $net, $sta, $time, $format, 
			$patterntype, $dir, $dfile, $relpath, \%vals );

	}
}
