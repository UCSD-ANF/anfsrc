
# codartools.pm
# 
# Mark Otero and Kent Lindquist
# 

package codartools;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	rbtimestamps_ok
	is_valid_lluv
	rb2lluv
	lluv2hash
	lluvtables
	Verbose
	codeVersion
	processedBy
	greatCircle
	geodVersion
);	

use File::Basename;
use Geo::Ellipsoid;
use POSIX qw(ceil floor);
use Datascope;

BEGIN {
	# Public:
	$Verbose = 0;
	$codeVersion = '%ProcessingTool: "codartools.pm" 1.00';
	$processedBy = '%ProcessedBy: "HFRNet"';
	$greatCircle = '%GreatCircle: "WGS84" 6378137.000  298.257223563';
	$geodVersion = '%GeodVersion: "PGEO" ' .  
			$Geo::Ellipsoid::VERSION . 
			' 2005 11 04';
}

sub is_valid_lluv {

	my( @block ) = @_;

	my( $Valid_filetype ) = "^\\s*%FileType:\\s+LLUV\\s+rdls";
	my( $Valid_site ) = "^\\s*%Site:\\s+\\w{4}";
	my( $Valid_timestamp ) = "^\\s*%TimeStamp:\\s+\\d{4}\\s+\\d{1,2}\\s+" .
			   "\\d{1,2}\\s+\\d{1,2}\\s+\\d{1,2}\\s+\\d{1,2}";
	my( $Valid_timezone ) = "^\\s*%TimeZone:\\s+(\")?(GMT|UTC)(\")?";
	my( $Valid_patterntype ) = "^\\s*%PatternType:\\s+[A-Za-z]{3,}";

	if( ! @block || scalar( @block ) < 1 ) {
		
		elog_complain( "is_valid_lluv: empty data block\n" );

		return 0;
	}

	if( ! grep( /$Valid_filetype/i, @block ) ) {					

		# Suppress this complaint since this is the first test on the 
		# input file, therefore also indicative of the need to convert 
		# the file to LLUV format. Don't clutter the logs. 
		#
		#	elog_complain( "is_valid_lluv: FileType row invalid " .
		#	"or not present\n" );

		return 0;

	}  elsif( ! grep( /$Valid_site/i, @block ) ) {

		elog_complain( "is_valid_lluv: Site row invalid or " .
				"not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_timestamp/, @block ) ) {	

		elog_complain( "is_valid_lluv: TimeStamp row invalid or " .
				"not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_timezone/i, @block ) ) {

		elog_complain( "is_valid_lluv: TimeZone row invalid or " .
				"not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_patterntype/i, @block ) ) {

		elog_complain( "is_valid_lluv: PatternType row invalid or " .
				"not present\n" );

		return 0;
	}

	my( @tmp ) = grep( /^\s*%Origin:/i, @block );

	my ($key, $lat, $lon) = split( ' ', $tmp[0], 3 );

	if( $lat < -90 || $lat > 90 || $lon < -180 || $lon > 180 ) {

		elog_complain( "is_valid_lluv: invalid lat,lon " .
				"'($lat,$lon)' \n" );

		return 0;
	}

	# Radial Data Verification:
	# Since there is no order in the way the keywords may appear, 
	# search for TableType and TableColmns in groupwise manner where
	# encountering a new TableType clears the TableColumns entry.

	my( $line, $TableCols, $TableType, $TableSubType );

	foreach $line ( @block ) {

	    if( $line !~ /^\s*%/ ) {

		#By now, you're already hit data
	    	last;
	    }

	    if( $line =~ /^\s*%TableType:/i ) {

	        if( defined( $TableType ) ) {

		    	if( defined( $TableCols ) ) {

	            		$TableCols = undef ;
			}
	        }

	        ($key, $TableType, $TableSubType) = split( ' ', $line, 3 );
	    }

	    if( $line =~ /^\s*%TableColumns:/i ) {

	    	($key, $TableCols) = split( ' ', $line, 2 ); 
	    }
	}

	if( ! defined( $TableType ) ||
	    ! defined( $TableSubType ) ||
	    ! defined( $TableCols ) ) {

		elog_complain( "is_valid_lluv: Table type, subtype and/or " .
				"columns are not defined\n" ); 

	    	return 0;
	}

	# Now verify that we have metadata for the right TableType.  If so,
	# extract the radial data lines into a list and verify each line has
	# $TableColumns elements.

	my( @Radata, @cols );

	if( $TableType =~ /LLUV/i && $TableSubType =~ /RDL/i ) {

	    @Radata = grep( /^\s*[^%]/, @block );

	    if( scalar( @Radata ) == 0 ) {

		elog_complain( "is_valid_lluv: No radial data found\n" );

		return 0;
	    }

	    foreach $line ( @Radata ) {

	        @cols = split( ' ', $line );
		
		if( scalar( @cols ) != $TableCols ) {

			elog_complain( "is_valid_lluv: Radial data columns " .
					"don't match table columns stated " .
					"in metadata\n" ); 

			return 0;
		}
	    }

	} else {

		elog_complain( "is_valid_lluv: LLUV RDL table is empty or " .
				"LLUV RDL table and subtype were not found\n" );


		return 0;
	}

	return 1;
}

sub rb2lluv {
	my ( $patt ) = shift( @_ );
	my ( $site ) = shift( @_ );
	my ( @inblock ) = @_;

	my( $ly, $lm, $ld, $lH, $lM, $lS, $tStamp, $tz ) = 
				extract_rbblock_timestamp( @inblock );

	if( ! defined( $ly ) ) {

		elog_complain( "ERROR extracting timestamp\n" );
        	return ();
	}

	inform( "Time-stamp obtained: $tStamp, $tz\n" );

	my( $lat, $lon ) = extract_rbblock_position( @inblock );

	if( ! defined( $lat ) ) {

		elog_complain( "ERROR extracting radar position\n" );
        	return ();
	}

	inform( "Origin obtained: %11.7f %12.7f\n", $lat, $lon );

	# Convert data from range-bin to LLUV

	my( @data ) = datablock_rb2lluv( $lat, $lon, @inblock );

	unless( @data == 16 ) {

		elog_complain( "ERROR converting range-bin data to LLUV\n" );
        	return ();
	}
    	my $rangeRes  = shift( @data );
    	my $tCoverage = shift( @data );
    	my $rangeEnd  = shift( @data );
    	my $metaStart = shift( @data );

    	inform( "Data converted from range-bin to LLUV\n" );

    	my( %metadata ) = getMetadata( $patt, $site, $metaStart, @inblock );

    	unless( scalar keys %metadata > 0 ) {
		elog_complain( "ERROR extracting metadata\n" );
		return ();
    	}

	$metadata{"TimeZone"}               = $tz unless ! defined( $tz );
	$metadata{"TimeStamp"}              = $tStamp;
	$metadata{"TimeCoverage"}           = $tCoverage;
	$metadata{"Origin"}                 = $lat . " " . $lon ;
	$metadata{"RangeResolutionKMeters"} = $rangeRes;
	$metadata{"RangeEnd"}               = $rangeEnd;

	unless ( exists $metadata{"Site"} && 
		 exists $metadata{"TimeStamp"} &&
		 exists $metadata{"TimeZone"} &&
                 exists $metadata{"Origin"} && 
		 exists $metadata{"PatternType"} ) {

		elog_complain( "Minimum metadata requirements not met " .
				"for conversion\n" );

        	return ();
    	}

	@outblock = pack_LLUV( \@data, \%metadata );

	return( @outblock );
}

sub lluv2hash {
	my ( @inblock ) = @_;

	my( $PosInt ) = "[[:digit:]]+";
	my( $Int ) = "[-[:digit:]]+";
	my( $PosFP ) = "[[:digit:].]+";		# Positive Floating-Point
	my( $FP ) = "[-[:digit:].]+";		# Positive Floating-Point

	my( %lluv_parsemap ) = (
		"TransmitCenterFreqMHz" => "TransmitCenterFreqMHz:\\s+($PosFP)",
		"Lat"			=> "Origin:\\s+($FP)",
		"Lon"			=> "Origin:\\s+$FP\\s+($FP)",
		"loop1_amp_calc"	=> "PatternAmplitudeCalculations:\\s+($PosFP)",
		"loop2_amp_calc"	=> "PatternAmplitudeCalculations:\\s+$PosFP\\s+($PosFP)",
		"loop1_phase_calc"	=> "PatternPhaseCalculations:\\s+($FP)",
		"loop2_phase_calc"	=> "PatternPhaseCalculations:\\s+$FP\\s+($FP)",
		"TimeCoverage"		=> "TimeCoverage:\\s+($PosFP)\\s+Minutes",
		"MergedCount"		=> "MergedCount:\\s+($PosInt)",
		"RangeStart"		=> "RangeStart:\\s+($PosInt)",
		"RangeEnd"		=> "RangeEnd:\\s+($PosInt)",
		"ProcessedTimeStamp"	=> "ProcessedTimeStamp:\\s+([[:digit:][:space:]]+)",
		"RangeResolutionKMeters" => "RangeResolutionKMeters:\\s+($PosFP)",
		"ReferenceBearing" 	=> "ReferenceBearing:\\s+($PosFP)",
		"DopplerResolutionHzPerBin" => "DopplerResolutionHzPerBin:\\s+($PosFP)",
		"Manufacturer"		=> "Manufacturer:\\s+(.*)",
		"TransmitSweepRateHz"	=> "TransmitSweepRateHz:\\s+($PosFP)",
		"TransmitBandwidthKHz"	=> "TransmitBandwidthKHz:\\s+($FP)",
		"CurrentVelocityLimit"	=> "CurrentVelocityLimit:\\s+($PosFP)",
		"RadialMinimumMergePoints" => "RadialMinimumMergePoints:\\s+($PosInt)",
		"loop1_amp_corr"	=> "PatternAmplitudeCorrections:\\s+($FP)",
		"loop2_amp_corr"	=> "PatternAmplitudeCorrections:\\s+$FP\\s+($FP)",
		"loop1_phase_corr"	=> "PatternPhaseCorrections:\\s+($FP)",
		"loop2_phase_corr"	=> "PatternPhaseCorrections:\\s+$FP\\s+($FP)",
		"BraggSmoothingPoints"	=> "BraggSmoothingPoints:\\s+($PosInt)",
		"RadialBraggPeakDropOff" => "RadialBraggPeakDropOff:\\s+($PosFP)",
		"BraggHasSecondOrder"	=> "BraggHasSecondOrder:\\s+($PosInt)",
		"RadialBraggPeakNull"	=>  "RadialBraggPeakNull:\\s+($PosFP)",
		"RadialBraggNoiseThreshold" => "RadialBraggNoiseThreshold:\\s+($PosFP)",
		"music_param_01"	=> "RadialMusicParameters:\\s+($FP)",
		"music_param_02"	=> "RadialMusicParameters:\\s+$FP\\s+($FP)",
		"music_param_03"	=> "RadialMusicParameters:\\s+$FP\\s+$FP\\s+($FP)",
		"ellip"			=> "GreatCircle:\\s+\"([[:alnum:]]+)\"",
		"earth_radius"		=> "GreatCircle:\\s+\"[[:alnum:]]+\"\\s+($PosFP)",
		"ellip_flatten"		=> "GreatCircle:\\s+\"[[:alnum:]]+\"\\s+$PosFP\\s+($PosFP)",
		"rad_merger_ver"	=> "ProcessingTool:\\s+\"RadialMerger\"\\s+($PosFP\\.$PosInt)", 
		"spec2rad_ver"		=> "ProcessingTool:\\s+\"SpectraToRadial\"\\s+($PosFP\\.$PosInt)",
		"ctf_ver"		=> "CTF:\\s+($FP)",
		"lluvspec_ver"		=> "LLUVSpec:\\s+($PosFP)",
		"geod_ver"		=> "GeodVersion:\\s+(\"[CP]GEO\"\\s+$PosFP)",
		"rad_slider_ver"	=> "ProcessingTool:\\s+\"RadialSlider\"\\s+($PosFP\\.$PosInt)",
		"rad_archiver_ver"	=> "ProcessingTool:\\s+\"RadialArchiver\"\\s+($PosFP\\.$PosInt)",
		"patt_date"		=> "PatternDate:\\s+([[:digit:][:space:]]+)",
		"patt_res"		=> "PatternResolution:\\s+($PosFP)",
		"patt_smooth"		=> "PatternSmoothing:\\s+($PosFP)",
		"spec_range_cells"	=> "SpectraRangeCells:\\s+($PosInt)",
		"spec_doppler_cells"	=> "SpectraDopplerCells:\\s+($PosInt)",
		"curr_ver"		=> "ProcessingTool:\\s+\"Currents\"\\s+($PosFP)",
		"codartools_ver"	=> "ProcessingTool:\\s+\"codartools.pm\"\\s+($PosFP)",
		"first_order_calc"	=> "FirstOrderCalc:\\s+($PosInt)",
		"lluv_tblsubtype"	=> "TableType:\\s+LLUV\\s+(.*)",
		"proc_by"		=> "ProcessedBy:\\s+\"(.*)\"",
		"merge_method"		=> "MergeMethod:\\s+($PosInt)",
		"patt_method"		=> "PatternMethod:\\s+($PosInt)",
	);

	my( %vals );

	foreach $key ( keys( %lluv_parsemap ) ) {

		grep( /$lluv_parsemap{$key}/ && ($vals{$key} = $1), @inblock );
	}

	$vals{geod_ver} =~ s/"//g;

	if( defined( $vals{ProcessedTimeStamp} ) ) {
		
		my( $time_pattern ) = "($PosInt)\\s+($PosInt)\\s+($PosInt)\\s+" . 
				      "($PosInt)\\s+($PosInt)\\s+($PosInt)";

		$vals{ProcessedTimeStamp} =~ /$time_pattern/;

		my( $yr, $mo, $dy, $hr, $mn, $sec ) = ( $1, $2, $3, $4, $5, $6 );

		$vals{proc_time} = str2epoch( "$mo/$dy/$yr $hr:$mn:$sec" );
	}

	if( defined( $vals{patt_date} ) ) {
		
		my( $time_pattern ) = "($PosInt)\\s+($PosInt)\\s+($PosInt)\\s+" . 
				      "($PosInt)\\s+($PosInt)\\s+($PosInt)";

		$vals{patt_date} =~ /$time_pattern/;

		my( $yr, $mo, $dy, $hr, $mn, $sec ) = ( $1, $2, $3, $4, $5, $6 );

		$vals{patt_date} = str2epoch( "$mo/$dy/$yr $hr:$mn:$sec" );
	}

	# Extract the number of radial vectors:

	my( @res );

	grep( /TableType:\s+(.*)|TableRows:\s+([[:digit:]]+)/ && eval { 
				if( defined( $1 ) ) { push( @res, $1 ); }
				if( defined( $2 ) ) { push( @res, $2 ); }
			}, @inblock );

	while( ( $atable = shift( @res ) ) && ( $nrows = shift( @res ) ) ) {
		
		if( $atable =~ /LLUV\s+RDL/ ) {

			$vals{nrads} = $nrows;
		}
	}

	return %vals;
}

sub lluvtables {
	my ( @inblock ) = @_;

	my( $line, @parts, $colname );

	my( %tables ) = ();

	my( $state ) = "search";

	while( $line = shift( @inblock ) ) {

		if( $line =~ /^%%/ ) {

			next;
		}

		if( $state eq "search" ) {
		
			if( $line =~ /^%TableType: (.*)/ ) {
			
				$tabletype = $1;

				$state = "tablespecs";
			}

		} elsif( $state eq "tablespecs" ) {

			if( $line =~ /^%TableColumns:\s+([[:digit:]]+)/ ) {

				$tables{$tabletype}{ncolumns} = $1;

			} elsif( $line =~ /^%TableColumnTypes:\s+(.*)/ ) {

				@{$tables{$tabletype}{colnames}} = 
							split( /\s+/, $1 );

			} elsif( $line =~ /^%TableRows:\s+([[:digit:]]+)/ ) {

				$tables{$tabletype}{nrows} = $1;

			} elsif( $line =~ /^%TableStart:/ ) {

				$state = "ingest";

			} else {

				elog_complain( "unexpected parser state " .
						"in lluvtables!! consequences " .
						"unknown\n" ); 

				$state = "search";
			}

		} elsif( $state eq "ingest" ) {

			if( $line =~ /^%TableEnd:/ ) {

				$tabletype = undef;
	
				$state = "search";

				next;
			}

			$line =~ s/^%?\s*//;

			@parts = split( /\s+/, $line );

			if( scalar( @parts ) != $tables{$tabletype}{ncolumns} ) {

				elog_complain( "Problem parsing $tabletype!" .
				 "Expected $tables{$tabletype}{ncolumns}, " .
				 "got " . scalar( @parts ) . "; skipping row\n" );

				next;
			}

			for( $i = 0; $i < scalar( @parts ); $i++ ) {

				$colname = $tables{$tabletype}{colnames}[$i];

				push( @{$tables{$tabletype}{$colname}}, 
				      $parts[$i] );
			}
		}
	}

	return %tables;
}

sub inform {
        my( $message ) = @_;

        if( $Verbose ) {

                elog_notify( $message );
        }
}

sub extract_filename_timestamp {

	my( $pathFile ) = @_;

    	my( $fileName ) = basename( $pathFile );

	my( $fy, $fm, $fd, $fH, $fM );

	my( $expr ) = "^Rad[sz]\\w{4}[_\\s](\\d{2})[-_](\\d{2})[-_]" .
		      "(\\d{2})[-_\\s](\\d{2})(\\d{2})(.rv)?\$";

	if( $fileName =~ m/$expr/ ) {

        	($fy, $fm, $fd, $fH, $fM) = ($1, $2, $3, $4, $5);

	} else {

		elog_complain( "ERROR: Unable to extract time from filename " .
			     "using match expression\n" );

        	return ();
	}

	return( $fy, $fm, $fd, $fH, $fM );
}

sub extract_rbblock_timestamp {
	my( @block ) = @_;

    	my( $tz );

        my( $expr ) = "^\\s*\\d{1,2}:\\d{2}(:\\d{2})?\\s*(\\w{2,3}\\s)?" .
		      "\\s*\\w+,\\s*\\w+\\s*\\d{1,2},\\s*\\d{4}\\s*" .
		      "(\\w{1,4})?\\s*(\\w{1,4})?\\s*(-\\d+)\\s*\$";

	if( $block[0] !~ m/$expr/i ) {
		
		elog_complain( "Failed to extract time elements from line 1\n" );
		return ();
	}

	my( $firstworda ) = $2; 
	my( $secondword ) = $3;
	my( $anumber ) = $5;

        if( defined( $firstword ) && $firstword !~ /(AM|PM)/ ) { 

                $tz = $firstword;
                $tz =~ s/\s+$//;
	}

	if( defined( $secondword ) && ! defined( $tz ) ) {

        	$tz = $secondword;
	}

        my( $ly, $lm, $ld, $lH, $lM, $lS );

        ($ly, $lm, $ld, $lH, $lM, $lS) =
		(gmtime($anumber - 2082844800 + 2**32))[5, 4, 3, 2, 1, 0];
        $lm++;
        $ly -= 100 if $ly >= 100;

	my( $tstamp );

        if ($ly < 50) {

        	$tstamp = $ly+2000 . " $lm $ld $lH $lM 00";

        } else {

        	$tstamp = $ly+1900 . " $lm $ld $lH $lM 00";
        }

	return( $ly, $lm, $ld, $lH, $lM, $lS, $tstamp, $tz );
}

sub rbtimestamps_ok {
	my( $pathname ) = shift @_;
	my( @block ) = @_;

	my( $fy, $fm, $fd, $fH, $fM ) = extract_filename_timestamp( $pathname );

	my( $ly, $lm, $ld, $lH, $lM, $lS, $tstamp, $tz ) = 
			extract_rbblock_timestamp( @block );

        if( ($ly != $fy) || 
	    ($lm != $fm) || 
	    ($ld != $fd) || 
	    ($lH != $fH) || 
	    ($lM != $fM) || 
	    ($lS != 0) ) {

		elog_complain( "ERROR: Filename time-stamp $fy $fm $fd " .
			     "$fH $fM 0 doesn't match serial time-stamp " .
			     "$ly $lm $ld $lH $lM $lS\n" );
		return 0;
        }

	return 1;
}

sub extract_rbblock_position {

	my( @block )  = @_;
	my( $dLat );
	my( $dLon );

    	# Expression to check for more common position reported in degrees
	# and decimal minutes w/various separators:

	$expr_deg_decimalmin = "^\\s*(\\d{1,2})(\\302)?" .
				"(\\260|\\241|\\373|\\s)(\\d{1,2}.\\d+)" .
				"('|\\241)(N|S)(,|\\s)\\s*(\\d{1,3})" .
				"(\\302)?(\\260|\\241|\\373|\\s)" .
				"(\\d{1,2}.\\d+)('|\\241)(E|W)\\s*\$";

	# Expression to check for decimal degrees (e.g. as in station RFG1):

	$expr_decimal_deg = "^\\s*(\\d{1,2}.\\d+)(\\302)?\\241(N|S)," .
			     "(\\d{1,3}.\\d+)(\\302)?\\241(E|W)\\s*\$";

	if ($block[1] =~ m/$expr_deg_decimalmin/i ) {

        	if( defined( $1 ) && 
		    defined( $4 ) && 
		    defined( $6 ) && 
		    defined( $8 ) && 
		    defined( $11 ) && 
		    defined( $13 ) ) {

            		$dLat = $1 + $4/60;

			if( $6 eq "S" ) {
            			$dLat *= -1;
			}

            		$dLon = $8 + $11/60;

			if( $13 eq "W" ) {
            			$dLon *= -1;
			}
        	}

	} elsif ($block[1] =~ m/$expr_decimal_deg/i ) {

        	if( defined( $1 ) && 
		    defined( $3 ) &&
		    defined( $4 ) &&
		    defined( $6 ) ) {

            		$dLat = $1; 

			if( $3 eq "S" ) {
            			$dLat *= -1;
			}

            		$dLon = $4;

			if( $6 eq "W" ) {
            			$dLon *= -1;
			}
        	}

	} else {

		elog_complain( "Position could not be parsed from LINE 2\n" );
        	return ();
	}

	return( $dLat, $dLon );
}


sub datablock_rb2lluv {
	my $lat = shift( @_ );
	my $lon = shift( @_ );
	my @block   = @_;

	# Get distance to first range cell, range resolution, 
	# reference angle and time coverage

	$block[2] =~ s/^\s+//;
	$block[2] =~ s/\s+$//;

	my( $d0, $rRes, $refAng, $dt ) = split( ' ', $block[2] );

	$dt *= 60;

	if( ! defined( $d0 ) || 
	    ! defined( $rRes ) || 
	    ! defined( $refAng ) || 
	    ! defined( $dt ) ) {

		elog_complain( "ERROR: Failed to read line 3\n" );
        	return;
	}

	# Get number of range cells
	my( $nRngCells );

	if ( $block[3] =~ m/^\s*(\d+)\s*$/ ) {

        	$nRngCells = $1;

	} else { 

		elog_complain( "ERROR: Failed to read line 4\n" );
        	return;
	}

	# Get starting range cell index

	my $rngStart; 

	if ( $block[4] =~ m/^\s*\d+\s+(\d+)\s*$/ ) {

        	$rngStart = $1;

	} else {

		elog_complain( "ERROR obtaining starting range bin on line 5\n" );
        	return;
	}

	# Loop through each range cell & build lists of bearing, speed,
	# uncertinty, range cell index & range.

	my $lineInd = 4;
	my ($rangeCell, $nVect, $nLinesPerVar, $rbVar, @vals, $i);
	my (@Bearings, @Speeds, @Uncerts, @CellInds, @Ranges);

	foreach $rangeCell ($rngStart..$nRngCells+$rngStart-1) {

		# Read total number of vectors for range cell

		if ( $block[$lineInd] =~ m/^\s*(\d+)\s+$rangeCell\s*$/ ) {
            		$nVect = $1;
            		$lineInd++;
		} else {
	    		elog_complain( "ERROR reading data from line %i\n", 
					$lineInd + 1 );
            		return;
		}

		# If vectors found for range cell, read them into a list 
		# for each variable:

		if ($nVect > 0) {

			$nLinesPerVar = ceil($nVect/7);

			foreach $i (1..3) {

                		foreach (1..$nLinesPerVar) {
                    			$block[$lineInd] =~ s/^\s+//;
                    			$block[$lineInd] =~ s/\s+$//;
                    			push( @vals, 
						split( ' ', $block[$lineInd]) );
                    			$lineInd++;
                		}

                		unless( @vals == $nVect ) {
		    			elog_complain( 
					 "ERROR reading data for range  cell " .
					 "%i\n", $rangeCell );
                    			return;
                		}

                		push @Bearings, @vals if $i == 1;
                		push @Speeds,   @vals if $i == 2;
                		push @Uncerts,  @vals if $i == 3;

                		undef @vals;
			}

			foreach (1..$nVect) {

                		push @CellInds, $rangeCell;
                		push @Ranges, $d0 + ($rRes*($rangeCell-1));
			}
		}
	}

	# First metadata line index 
	my $metaStart = $lineInd++;

	# Define the ellipsoid for lat/lon, Easting/Northing conversions

	my $geo = Geo::Ellipsoid -> new( 
					ellipsoid => 'WGS84', 
					units     => 'degrees'
					);

	# Define constants
	my $pi      = atan2(1,1) * 4;
	my $deg2rad = $pi/180;

	# Loop through each element in the data list

	my( @Lats, @Lons, @Eastings, @Northings, @Directions, @Us, @Vs );

	foreach $i (0..$#Bearings) {

		# Add reference angle to bearings and convert
		# bearing from polar coords reported by CODAR ( E = 0, CCW) 
		# to compass coords expected by
		# Geo::Ellipsoid module (N = 0, CW)

        	$Bearings[$i] += $refAng; 
        	$Bearings[$i] = mod(90-$Bearings[$i], 360);

        	# Calculate latitude, longitude, Easting & Northing
		# from range & bearing
        	($Lats[$i], $Lons[$i]) = 
			$geo -> at($lat, $lon, $Ranges[$i]*1000, $Bearings[$i]);

        	($Eastings[$i], $Northings[$i]) = 
			$geo -> displacement($lat, $lon, $Lats[$i], $Lons[$i]);

        	$Eastings[$i]  /= 1000;
        	$Northings[$i] /= 1000;

        	# Compute bearing from radial vector to radar site

        	$Directions[$i] = 
			$geo -> bearing($Lats[$i], $Lons[$i], $lat, $lon);

        	my $directionECCW = mod(90-$Directions[$i], 360);

        	# Compute radial u & v components from scalar speed & bearing

        	$Us[$i] = cos($directionECCW*$deg2rad) * $Speeds[$i];
        	$Vs[$i] = sin($directionECCW*$deg2rad) * $Speeds[$i];
	}

	# Put all data into 2D array (array of arrays)

	my( @data ) = (
        	[@Lons],     [@Lats],     [@Us],         [@Vs],
        	[@Uncerts],  [@Eastings], [@Northings],  [@Ranges],     
        	[@Bearings], [@Speeds],   [@Directions], [@CellInds]
		);

	if( ! defined( $data[0][0] ) ) {

		elog_complain( "ERROR no data in range-bin file data block!\n" );

        	return;
		
	} 

	return $rRes, $dt, $nRngCells, $metaStart, @data;
}

sub mod {
	my ($x, $y) = @_;
	my $n = floor($x/$y);
	my $val = $x - $n*$y;
	return $val;
}


sub getMetadata {
	my( $patt )  = shift @_;
	my( $site )  = shift @_;
	my( $metaStart ) = shift @_;
	my( @block ) = @_;

	my( %rb_to_lluv_keyword_map ) = (
		"CenterFreqMHz"        => "TransmitCenterFreqMHz",
		"DopplerFreqHz"        => "DopplerResolutionHzPerBin",
		"AverFirmssPts"        => "BraggSmoothingPoints",
		"LimitMaxCurrent"      => "CurrentVelocityLimit",
		"UseSecondOrder"       => "BraggHasSecondOrder",
		"FactorDownPeakLimit"  => "RadialBraggPeakDropOff",
		"FactorDownPeakNull"   => "RadialBraggPeakNull",
		"FactorAboveNoise"     => "RadialBraggNoiseThreshold",
		"AmpAdjustFactors"     => "PatternAmplitudeCorrections",
		"AmpCalculated"        => "PatternAmplitudeCalculations",
		"PhaseAdjustFactors"   => "PatternPhaseCorrections",
		"PhaseCalculated"      => "PatternPhaseCalculations",
		"MusicParams"          => "RadialMusicParameters",
		"NumMergeRads"         => "MergedCount",
		"MinRadVectorPts"      => "RadialMinimumMergePoints",
		"FirstOrderCalc"       => "FirstOrderCalc",
		"Currents"             => "Currents",
		"RadialMerger"         => "RadialMerger",
		"SpectraToRadial"      => "SpectraToRadial",
		"RadialSlider"         => "RadialSlider",
	);

	# Extract metadata from each line and put into a hash until '!END' 
	# or all lines read.  Hash key will be metadata descriptor and value 
	# will be remainder of line - ie. key = 'NumMergeRads', value = '7'.

	my( $lineInd, %trailer );

	foreach $lineInd ($metaStart..@block-1) {

		my $line = $block[$lineInd];

		last if $line =~ /!END/i;

		$line =~ s/^\s+//;
		$line =~ s/\s+$//;
		$line =~ /^([A-Za-z]+)\s+(.*)$/;
		$trailer{$1} = $2 if (defined $1) & (defined $2);
	}

	return unless( scalar( keys( %trailer ) ) > 0 );

	# Map range-bin keywords to lluv keywords

	my( $key, $val, %metadata );

	while ( ($key, $val) = each %trailer ) {

		if ( defined $rb_to_lluv_keyword_map{$key} ) {

			$metadata{ $rb_to_lluv_keyword_map{$key} } = $val;

		} else {

			elog_complain( "WARNING, unmatched metadata field " .
					"from range-bin file: $key\t$val\n" )

			unless $key eq "RadSmoothing";
		}
	}

	$metadata{"PatternType"} = "Ideal"    if $patt eq 's';
        $metadata{"PatternType"} = "Measured" if $patt eq 'z';
        $metadata{"Site"}        = $site;

	return %metadata;
}

sub pack_LLUV {
	my( $dataRef, $metaRef ) = @_;

	my( @outblock );

	# Begin writing metadata

	push @outblock, "%CTF: 1.00";
	push @outblock, "%FileType: LLUV rdls \"RadialMap\"";
	push @outblock, "%LLUVSpec: 1.02  2006 01 11";
	push @outblock, "%Manufacturer: CODAR Ocean Sensors. SeaSonde";
	push @outblock, "%Site: $metaRef->{'Site'} \"\"";
	push @outblock, "%TimeStamp: $metaRef->{'TimeStamp'}";

	# Since GMT offset & daylight savings in included in TimeZone key, only
	# report GMT & UTC times.  Could create a hash of timezones & GMT
	# offsets, then would need to determine if daylight savings.  For now,
	# only convert GMT, UTC & no timezone files.

	if (exists $metaRef->{'TimeZone'}) {

		my $tz = $metaRef->{'TimeZone'};

		if ( ($tz eq 'GMT') || ($tz eq 'UTC') ) {

			push @outblock, "%TimeZone: \"$tz\" +0.000 0" 

		} else {

			elog_complain( "Non-UTC/GMT Timezone detected, " .
					"aborting!\n" );

			return ();
		}
	}

        if( exists( $metaRef->{'TimeCoverage'} ) ) {

		push @outblock, 
			"%TimeCoverage: $metaRef->{'TimeCoverage'} Minutes";
	}

	push @outblock, 
		sprintf( "%%Origin: %11.7f %12.7f", 
			 (split( ' ', $metaRef->{'Origin'} ))[0, 1] );

	push @outblock, "$greatCircle";
	push @outblock, "$geodVersion";

	push @outblock, sprintf "%%RangeResolutionKMeters: %6.3f",
        $metaRef->{'RangeResolutionKMeters'}
        if exists $metaRef->{'RangeResolutionKMeters'};

	push @outblock, sprintf "%%TransmitCenterFreqMHz: %9.6f",
        $metaRef->{'TransmitCenterFreqMHz'}
        if exists $metaRef->{'TransmitCenterFreqMHz'};

	push @outblock, sprintf "%%DopplerResolutionHzPerBin: %11.9f",
        $metaRef->{'DopplerResolutionHzPerBin'}
        if exists $metaRef->{'DopplerResolutionHzPerBin'};

	push @outblock, sprintf "%%BraggSmoothingPoints: %d",
        $metaRef->{'BraggSmoothingPoints'}
        if exists $metaRef->{'BraggSmoothingPoints'};

	push @outblock, sprintf "%%CurrentVelocityLimit: %6.1f",
        (split ' ', $metaRef->{'CurrentVelocityLimit'})[0]
        if exists $metaRef->{'CurrentVelocityLimit'};

	push @outblock, sprintf "%%BraggHasSecondOrder: %d",
        $metaRef->{'BraggHasSecondOrder'}
        if exists $metaRef->{'BraggHasSecondOrder'};

	push @outblock, sprintf "%%RadialBraggPeakDropOff: %6.3f",
        $metaRef->{'RadialBraggPeakDropOff'}
        if exists $metaRef->{'RadialBraggPeakDropOff'};

	push @outblock, sprintf "%%RadialBraggPeakNull: %5.3f",
        $metaRef->{'RadialBraggPeakNull'}
        if exists $metaRef->{'RadialBraggPeakNull'};

	push @outblock, sprintf "%%RadialBraggNoiseThreshold: %5.3f",
        $metaRef->{'RadialBraggNoiseThreshold'}
        if exists $metaRef->{'RadialBraggNoiseThreshold'};

	push @outblock, sprintf "%%PatternAmplitudeCorrections: %6.4f %6.4f", 
        (split ' ', $metaRef->{'PatternAmplitudeCorrections'})[0, 1]
        if exists $metaRef->{'PatternAmplitudeCorrections'};

	push @outblock, sprintf "%%PatternAmplitudeCalculations: %6.4f %6.4f", 
        (split ' ', $metaRef->{'PatternAmplitudeCalculations'})[0, 1]
        if exists $metaRef->{'PatternAmplitudeCalculations'};

	push @outblock, sprintf "%%PatternPhaseCorrections: %5.2f %5.2f",
        (split ' ', $metaRef->{'PatternPhaseCorrections'})[0, 1]
        if exists $metaRef->{'PatternAmplitudeCalculations'};

	push @outblock, sprintf "%%PatternPhaseCalculations: %4.2f %4.2f",
        (split ' ', $metaRef->{'PatternPhaseCalculations'})[0, 1]
        if exists $metaRef->{'PatternPhaseCalculations'};

	push @outblock, sprintf "%%RadialMusicParameters: %6.3f %6.3f %6.3f",
        (split ' ', $metaRef->{'RadialMusicParameters'})[0, 1, 2]
        if exists $metaRef->{'RadialMusicParameters'};

	push @outblock, sprintf "%%MergedCount: %d",
        $metaRef->{'MergedCount'}
        if exists $metaRef->{'MergedCount'};

	push @outblock, sprintf "%%RadialMinimumMergePoints: %d",
        $metaRef->{'RadialMinimumMergePoints'}
        if exists $metaRef->{'RadialMinimumMergePoints'};

	push @outblock, sprintf "%%FirstOrderCalc: %d",
        $metaRef->{'FirstOrderCalc'}
        if exists $metaRef->{'FirstOrderCalc'};

	push @outblock, "%RangeStart: 1";

	push @outblock, sprintf "%%RangeEnd: %d",
        $metaRef->{'RangeEnd'}
        if exists $metaRef->{'RangeEnd'};

	push @outblock, "%ReferenceBearing: 0 DegNCW";
	push @outblock, "%PatternType: $metaRef->{'PatternType'}";

	# Print data

	push @outblock, "%TableType: LLUV RDL5";
	push @outblock, "%TableColumns: 16";

	push @outblock, "%TableColumnTypes: LOND LATD VELU VELV VFLG ESPC " .
			"ETMP MAXV MINV XDST YDST RNGE BEAR VELO HEAD SPRC";

	push @outblock, sprintf "%%TableRows: %d", scalar @{$dataRef->[0]};
	push @outblock, "%TableStart:";

	push @outblock, "%%   Longitude   Latitude    U comp   V comp  " .
			"VectorFlag    Spatial    Temporal     Velocity    " .
			"Velocity  X Distance  Y Distance  Range   Bearing  " .
			"Velocity  Direction   Spectra";

	push @outblock, "%%     (deg)       (deg)     (cm/s)   (cm/s)  " .
			"(GridCode)    Quality     Quality     Maximum     " .
			"Minimum      (km)        (km)      (km)  (deg NCW)  " .
			"(cm/s)   (deg NCW)   RngCell";

	my ($i, $j);

	foreach $i (0..$#{$dataRef->[0]}) {

		my( @line ) = ();

		foreach $j (0..$#$dataRef) {

			if( $j == 0 ) { 		
				
				# Longitude:

				push @line, 
				   sprintf "  %12.7f", $dataRef->[$j][$i];

			} elsif( $j == 1 ) { 		
				
				# Latitude:

				push @line, 
				   sprintf " %11.7f" , $dataRef->[$j][$i];

			} elsif( $j == 2 ) { 		
			
				# U:

				push @line, 
				   sprintf " %8.3f"  , $dataRef->[$j][$i];

			} elsif( $j == 3 ) { 		

				# V:

				push @line, 
				   sprintf " %8.3f"  , $dataRef->[$j][$i];

			} elsif( $j == 4 ) {

				# VectorFlag:

				push @line, sprintf " %10d"  , 0; 

				# SpatialQuality:

				if ($dataRef->[$j][$i] eq 'NAN(001)') {

					push @line, 
					   sprintf " %11s", 'nan';

				} else {    
					push @line, 
					  sprintf " %11.3f", 
					          $dataRef->[$j][$i];
				}

				# TemporalQuality:

				push @line, 
				    sprintf " %11.3f", 999;

				# VelMax:

				push @line, 
				   sprintf " %11.3f", $dataRef->[$j+5][$i];

				# VelMin:

				push @line, 
				   sprintf " %11.3f", $dataRef->[$j+5][$i];

			} elsif( $j == 5 ) {

				# Xdistance:

				push @line, 
				   sprintf " %11.4f", $dataRef->[$j][$i];

			} elsif( $j == 6 ) {

				# Ydistance:

				push @line, 
				   sprintf " %11.4f", $dataRef->[$j][$i];

			} elsif( $j == 7 ) {

				# Range:

				push @line, 
				   sprintf " %8.3f", $dataRef->[$j][$i];

			} elsif( $j == 8 ) {

				# Bearing:

				push @line, 
				   sprintf " %7.1f", $dataRef->[$j][$i];

			} elsif( $j == 9 ) {

				# Velocity:

				push @line, 
				   sprintf " %9.2f", $dataRef->[$j][$i];

			} elsif( $j == 10 ) {

				# Direction:

				push @line, 
				   sprintf " %9.1f", $dataRef->[$j][$i];

			} elsif( $j == 11 ) {

				# RangeCell:

				push @line, 
				   sprintf " %9d", $dataRef->[$j][$i];
			}
		}

		push( @outblock, join( "", @line ) );
	}

	push @outblock, "%TableEnd:";
	push @outblock, "%%";

	# Print remaining metadata
	my( @now ) = gmtime;
	$now[5] += 1900;
	$now[4] += 1;

    	foreach $i (1..5) { 

		$now[$i] = "0$now[$i]" if $now[$i] < 10 
	}

	push @outblock, 
		sprintf "%%ProcessedTimeStamp: %4s %2s %2s %2s %2s %2s", 
			(@now)[5, 4, 3, 2, 1, 0];

	push @outblock, "$processedBy";
	push @outblock, "$codeVersion";

	push @outblock, sprintf "%%ProcessingTool: \"Currents\" %s",
        $metaRef->{'Currents'}
        if exists $metaRef->{'Currents'};

	push @outblock, sprintf "%%ProcessingTool: \"RadialMerger\" %s",
        $metaRef->{'RadialMerger'}
        if exists $metaRef->{'RadialMerger'};

	push @outblock, sprintf "%%ProcessingTool: \"SpectraToRadial\" %s",
        $metaRef->{'SpectraToRadial'}
        if exists $metaRef->{'SpectraToRadial'};

	push @outblock, sprintf "%%ProcessingTool: \"RadialSlider\" %s",
        $metaRef->{'RadialSlider'}
        if exists $metaRef->{'RadialSlider'};

	push @outblock, "%End:";

	return @outblock;
}

1;
