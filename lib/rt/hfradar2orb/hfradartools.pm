
# hfradartools.pm
#
#   Copyright (c) 2003-2007 Lindquist Consulting, Inc.
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

package hfradartools;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	dbadd_site
	dbadd_metadata
	dbadd_diagnostics
	dbadd_radialfile
	write_radialfile
	Verbose
	Schema
);	

use Datascope;

BEGIN {
	# Public:
	$Verbose = 0;
	$Schema = "Hfradar0.6";
}

sub inform {
	my( $msg ) = @_;

	if( $Verbose ) {

		elog_notify( "$msg" );
	}

	return;
}

sub dbreopen {
	my( $dbref ) = pop( @_ );	

	my( $dbname ) = dbquery( @{$dbref}, dbDATABASE_NAME );

	dbclose( @{$dbref} );

	@{$dbref} = dbopen( $dbname, "r+" );

	return;
}

sub dbadd_site {
	my( $lon ) = pop( @_ );
	my( $lat ) = pop( @_ );
	my( $time ) = pop( @_ );
	my( $sta ) = pop( @_ );
	my( $net ) = pop( @_ );
	my( $dbref ) = pop( @_ );

	my( @dbs, $nsites, $oldnet, $oldsta, $staname, $key );

	my( @db ) = @{$dbref};

	@db = dblookup( @db, "", "site", "", "" );

	if( ! defined( %Stanames ) ) {

		@dbs = dbsort( @db, "time" );

		$nsites = dbquery( @dbs, dbRECORD_COUNT );

		for( $dbs[3] = $nsites - 1; $dbs[3] >= 0; $dbs[3]-- ) {
	
			( $oldnet, $oldsta, $staname ) = 
				dbgetv( @dbs, "net", "sta", "staname" );

			$key = "$oldnet:$oldsta";

			if( $staname ne "-" && ( ! defined( $Stanames{$key} ) ) ) {
		
				$Stanames{$key} = $staname;
			}
		}
	}

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

			dbreopen( $dbref );

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

			elog_complain( "WARNING: Data block for $net, $sta ($lat,$lon) at " .
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

			dbreopen( $dbref );

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

			dbreopen( $dbref );

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
			"and Data block for $net, $sta ($lat, $lon) at time " . 
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
	my( $dbref ) = pop( @_ );

	my( @block ) = split( /\r?\n/, $block );

	if( ! codartools::is_valid_lluv( @block ) ) {

		elog_complain( "Data block from '$net', '$sta' timestamped " . strtime( $time ) .
			       " is not valid LLUV format; omitting addition of station, " .
			       "network and metadata to database\n" );
		return;
	}

	my( %vals ) = codartools::lluv2hash( @block );

	dbadd_site( $dbref, $net, $sta, $time, $vals{Lat}, $vals{Lon} );

	my( @db ) = @{$dbref};

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
	@dbscratch = dblookup( @db, "", "radialmeta", "", "dbSCRATCH" );

	dbputv( @dbscratch, 
		     "net", $net, 
		     "sta", $sta, 
		     "format", $format, 
		     "patterntype", $patterntype,
		     "time", $time,
		     "endtime", $time );

	my( @records ) = dbmatches( @dbscratch, @db, "radialmeta_hook" );

	if( @records < 1 ) {

		eval {

		dbputv( @dbscratch, 
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

		$rc = dbadd( @db );

		};

		if( $@ ne "" ) {

			elog_complain( "Unexpected dbaddv (actually dbaddnull/dbputv) " .
				"failure for radialmeta table: $@\n" );

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
		$dbt[3] = shift( @records );

		( $matchtime, $matchendtime ) = 
			dbgetv( @dbt, "time", "endtime" );

		if( ( $matchtime != $matchendtime ) || 
		    ( $matchtime != $time ) ) {

		    elog_complain( "SCAFFOLD Data block appears to overlap " .
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

sub dbadd_diagnostics {
	my( $block ) = pop( @_ );
	my( $patterntype ) = pop( @_ );
	my( $format ) = pop( @_ );
	my( $time ) = pop( @_ );
	my( $sta ) = pop( @_ );
	my( $net ) = pop( @_ );
	my( $dbref ) = pop( @_ );

	my( @block ) = split( /\r?\n/, $block );

	my( %tables ) = codartools::lluvtables( @block );

	print "SCAFFOLD inside dbadd_diagnostics, planning to add to db\n";

	return;
}

sub dbadd_radialfile {
	my( $valsref ) = pop( @_ );
	my( $mtime ) = pop( @_ );
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

	@db = dblookup( @db, "", "radialfiles", "", "" );

	$db[3] = dbquery( @db, dbRECORD_COUNT );

	$rec = dbfind( @db, "net == \"$net\" && " .
			    "sta == \"$sta\" && " .
			    "time == $time && " .
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

			elog_complain( "Unexpected dbaddv failure for radialfiles table: $@\n" );

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

	return;
}

sub write_radialfile {
	my( $block ) = pop( @_ );
	my( $patterntype ) = pop( @_ );
	my( $format ) = pop( @_ );
	my( $time ) = pop( @_ );
	my( $sta ) = pop( @_ );
	my( $net ) = pop( @_ );
	my( $overwrite ) = pop( @_ );
	my( $dbdir ) = pop( @_ );
	my( $dfiles_pattern ) = pop( @_ );

	my( $path_relto_descriptor, $subdir, $dfile, $suffix, $mtime );

	$path_relto_descriptor = $dfiles_pattern;

	$path_relto_descriptor =~ s/%{net}/$net/g;
	$path_relto_descriptor =~ s/%{sta}/$sta/g;
	$path_relto_descriptor =~ s/%{format}/$format/g;
	$path_relto_descriptor =~ s/%{patterntype}/$patterntype/g;

	$path_relto_descriptor = epoch2str( $time, $path_relto_descriptor );

        ( $dir, $dfile, $suffix ) = parsepath( $path_relto_descriptor );

        if( "$suffix" ) { $dfile .= ".$suffix" }

        $path_relto_cwd = concatpaths( $dbdir, $path_relto_descriptor );

	$subdir = (parsepath( $path_relto_cwd ))[0];

	system( "mkdir -p $subdir" );

	$abspath = abspath( $path_relto_cwd );

	if( -e "$abspath" && ! $overwrite ) {

		if( $Verbose ) {

			elog_complain( "Won't overwrite $abspath; file exists\n" );
		}

		return undef;
	}

        inform( "Creating $abspath\n" );

        open( F, ">$abspath" );
        print F $block;
        close( F );

	$mtime = (stat("$abspath"))[9];

	return( $dir, $dfile, $mtime );
}

1;
