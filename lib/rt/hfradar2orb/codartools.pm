
package codartools;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	is_valid_LLUV
	timestamps_ok
	extract_filename_pattern_site
	convertBlock
	writeLLUV
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

	# Private:
	$Valid_filetype = "^\\s*%FileType:\\s+LLUV\\s+rdls";
	$Valid_site = "^\\s*%Site:\\s+\\w{4}";
	$Valid_timestamp = "^\\s*%TimeStamp:\\s+\\d{4}\\s+\\d{1,2}\\s+" .
			   "\\d{1,2}\\s+\\d{1,2}\\s+\\d{1,2}\\s+\\d{1,2}";
	$Valid_timezone = "^\\s*%TimeZone:\\s+(\")?(GMT|UTC)(\")?";
	$Valid_patterntype = "^\\s*%PatternType:\\s+[A-Za-z]{3,}";
}

sub is_valid_LLUV {

	my( @block ) = @_;

	if( ! @block || scalar( @block ) < 1 ) {
		
		elog_complain( "is_valid_LLUV: empty data block\n" );

		return 0;
	}

	if( ! grep( /$Valid_filetype/i, @block ) ) {					

		elog_complain( "is_valid_LLUV: FileType row invalid " .
				"or not present\n" );

		return 0;

	}  elsif( ! grep( /$Valid_site/i, @block ) ) {

		elog_complain( "is_valid_LLUV: Site row invalid or " .
				"not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_timestamp/, @block ) ) {	

		elog_complain( "is_valid_LLUV: TimeStamp row invalid or " .
				"not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_timezone/i, @block ) ) {

		elog_complain( "is_valid_LLUV: TimeZone row invalid or " .
				"not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_patterntype/i, @block ) ) {

		elog_complain( "is_valid_LLUV: PatternType row invalid or " .
				"not present\n" );

		return 0;
	}

	my( @tmp ) = grep( /^\s*%Origin:/i, @block );

	my ($key, $lat, $lon) = split( ' ', $tmp[0], 3 );

	if( $lat < -90 || $lat > 90 || $lon < -180 || $lon > 180 ) {

		elog_complain( "is_valid_LLUV: invalid lat,lon " .
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

	    	return 0;
	}

	# Now verify that we have metadata for the right TableType.  If so,
	# extract the radial data lines into a list and verify each line has
	# $TableColumns elements.

	my( @Radata, @cols );

	if( $TableType =~ /LLUV/i && $TableSubType =~ /RDL/i ) {

	    @Radata = grep( /^\s*[^%]/, @block );

	    if( scalar( @Radata ) == 0 ) {

		return 0;
	    }

	    foreach $line ( @Radata ) {

	        @cols = split( ' ', $line );
		
		if( scalar( @cols ) != $TableCols ) {

			return 0;
		}
	    }

	} else {

		return 0;
	}

	return 1;
}

sub convertBlock {
	my ( $patt ) = shift( @_ );
	my ( $site ) = shift( @_ );
	my ( @inblock ) = @_;

	my( $ly, $lm, $ld, $lH, $lM, $lS, $tStamp, $tz ) = 
				extract_rbblock_timestamp( @inblock );

	inform( "Time-stamp obtained: $tStamp, $tz\n" );

	my( $lat, $lon ) = extract_rbblock_position( @inblock );

	if( ! defined( $lat ) ) {

		elog_complain( "ERROR extracting radar position\n" );
        	return( undef, undef );
	}

	inform( "Origin obtained: %11.7f %12.7f\n", $lat, $lon );

	# Convert data from range-bin to LLUV
	my @data = &rb2lluv($lat, $lon, @inblock);
	unless (@data == 16) {
		elog_complain( "ERROR converting range-bin data to LLUV\n" );
        	return( undef, undef );
	}
    	my $rangeRes  = shift(@data);
    	my $tCoverage = shift(@data);
    	my $rangeEnd  = shift(@data);
    	my $metaStart = shift(@data);
    	inform( "Data converted from range-bin to LLUV\n" );

    	my %metadata = &getMetadata( $patt, $site, $metaStart, @inblock );

    	unless( scalar keys %metadata > 0 ) {
		elog_complain( "ERROR extracting metadata\n" );
		return( undef, undef );
    	}

	$metadata{"TimeZone"}               = $tz unless ! defined( $tz );
	$metadata{"TimeStamp"}              = $tStamp;
	$metadata{"TimeCoverage"}           = $tCoverage;
	$metadata{"Origin"}                 = $lat . " " . $lon ;
	$metadata{"RangeResolutionKMeters"} = $rangeRes;
	$metadata{"RangeEnd"}               = $rangeEnd;
	unless ( exists $metadata{"Site"}   & exists $metadata{"TimeStamp"} &
                 exists $metadata{"Origin"} & exists $metadata{"PatternType"} ) {
		elog_complain( "ERROR: Minimum metadata requirements not met for conversion\n" );
        	return( undef, undef );
    	}
	inform( "Metadata extracted & minimum requirements for conversion met\n" );

	return ( \@data, \%metadata );
}

sub inform {
        my( $message ) = @_;

        if( $Verbose ) {

                elog_notify( $message );
        }
}

sub extract_filename_pattern_site {

	my( $pathFile ) = @_;

    	my( $fileName ) = basename( $pathFile );

	my( $patt, $site );

	my( $expr ) = "^Rad([sz])(\\w{4})[_\\s]\\d{2}[-_]\\d{2}[-_]" .
		      "\\d{2}[-_\\s]\\d{2}\\d{2}(.rv)?\$";

	if( $fileName =~ m/$expr/ ) {

        	$patt = $1;
        	$site = $2;

	} else {

		elog_complain( "ERROR: Unable to extract site & pattern " .
			"from filename using match expression\n" );
	}

	return( $patt, $site );
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

        	return( undef );
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
		return undef;
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

sub timestamps_ok {
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
        	return undef;
	}

	return( $dLat, $dLon );
}


sub rb2lluv {
    my $lat = shift( @_ );
    my $lon = shift( @_ );
    my @file   = @_;

    # Get distance to first range cell, range resolution, reference angle &
    # time coverage
    $file[2] =~ s/^\s+//;
    $file[2] =~ s/\s+$//;
    my ($d0, $rRes, $refAng, $dt) = split ' ', $file[2];
    $dt *= 60;
    unless ( (defined $d0) & (defined $rRes) & (defined $refAng) & (defined $dt) ) {
	elog_complain( "ERROR: Failed to read line 3\n" );
        return;
    }

    # Get number of range cells
    my $nRngCells;
    if ( $file[3] =~ m/^\s*(\d+)\s*$/ ) {
        $nRngCells = $1;
    } else { 
	elog_complain( "ERROR: Failed to read line 4\n" );
        return;
    }

    # Get starting range cell index
    my $rngStart; 
    if ( $file[4] =~ m/^\s*\d+\s+(\d+)\s*$/ ) {
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
        if ( $file[$lineInd] =~ m/^\s*(\d+)\s+$rangeCell\s*$/ ) {
            $nVect = $1;
            $lineInd++;
        } else {
	    elog_complain( "ERROR reading data from line %i\n", $lineInd + 1 );
            return;
        }

	# If vectors found for range cell, read them into a list for each variable
        if ($nVect > 0) {
            $nLinesPerVar = ceil($nVect/7);
            foreach $i (1..3) {
                foreach (1..$nLinesPerVar) {
                    $file[$lineInd] =~ s/^\s+//;
                    $file[$lineInd] =~ s/\s+$//;
                    push( @vals, (split ' ', $file[$lineInd]) );
                    $lineInd++;
                }
                unless (@vals == $nVect) {
		    elog_complain( "ERROR reading data for range cell %i\n", $rangeCell );
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
    my (@Lats, @Lons, @Eastings, @Northings, @Directions, @Us, @Vs);
    foreach $i (0..$#Bearings) {

        # Add reference angle to bearings and convert bearing from polar coords reported 
        # by CODAR ( E = 0, CCW) to compass coords expected by Geo::Ellipsoid module 
        # (N = 0, CW)
        $Bearings[$i] += $refAng; 
        $Bearings[$i] = mod(90-$Bearings[$i], 360);

        # Calculate latitude, longitude, Easting & Northing from range & bearing
        ($Lats[$i],    $Lons[$i])       = $geo -> at($lat, $lon, $Ranges[$i]*1000, $Bearings[$i]);
        ($Eastings[$i], $Northings[$i]) = $geo -> displacement($lat, $lon, $Lats[$i], $Lons[$i]);
        $Eastings[$i]  /= 1000;
        $Northings[$i] /= 1000;

        # Compute bearing from radial vector to radar site
        $Directions[$i] = $geo -> bearing($Lats[$i], $Lons[$i], $lat, $lon);
        my $directionECCW = mod(90-$Directions[$i], 360);

        # Compute radial u & v components from scalar speed & bearing
        $Us[$i] = cos($directionECCW*$deg2rad) * $Speeds[$i];
        $Vs[$i] = sin($directionECCW*$deg2rad) * $Speeds[$i];
    }

    # Put all data into 2D array (array of arrays)
    my @data = (
        [@Lons],     [@Lats],     [@Us],         [@Vs],
        [@Uncerts],  [@Eastings], [@Northings],  [@Ranges],     
        [@Bearings], [@Speeds],   [@Directions], [@CellInds]
    );
    return $rRes, $dt, $nRngCells, $metaStart, @data;
}


sub mod {
	my ($x, $y) = @_;
	my $n = floor($x/$y);
	my $val = $x - $n*$y;
	return $val;
}


sub getMetadata {
    my $patt  = shift @_;
    my $site  = shift @_;
    my $metaStart = shift @_;
    my @block      = @_;

    # Establish metadata mapping hash between rb keywords and lluv keywords
    my %map = (
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
    # or all lines read.  Hash key will be metadata descriptor and value will
    # be remainder of line - ie. key = 'NumMergeRads', value = '7'.
    my ($lineInd, %trailer);
    foreach $lineInd ($metaStart..@block-1) {
        my $line = $block[$lineInd];
        last if $line =~ /!END/i;
        $line =~ s/^\s+//;
        $line =~ s/\s+$//;
        $line =~ /^([A-Za-z]+)\s+(.*)$/;
        $trailer{$1} = $2 if (defined $1) & (defined $2);
    }
    return unless scalar keys %trailer > 0;

    # Map range-bin keywords to lluv keywords
    my ($key, $val, %metadata);
    while ( ($key, $val) = each %trailer ) {
        if ( defined $map{$key} ) {
            $metadata{ $map{$key} } = $val;
        } else {
		elog_complain( "WARNING, unmatched metadata field from range-bin file: $key\t$val\n" )
                unless $key eq "RadSmoothing";
        }
    }

	$metadata{"PatternType"} = "Ideal"    if $patt eq 's';
        $metadata{"PatternType"} = "Measured" if $patt eq 'z';
        $metadata{"Site"}        = $site;

    return %metadata;
}


sub writeLLUV {
	my( $out, $dataRef, $metaRef ) = @_;

	# Begin writing metadata
	print $out "%CTF: 1.00\n";
	print $out "%FileType: LLUV rdls \"RadialMap\"\n";
	print $out "%LLUVSpec: 1.02  2006 01 11\n";
	print $out "%Manufacturer: CODAR Ocean Sensors. SeaSonde\n";
	print $out "%Site: $metaRef->{'Site'} \"\"\n";
	print $out "%TimeStamp: $metaRef->{'TimeStamp'}\n";

	# Since GMT offset & daylight savings in included in TimeZone key, only report
	# GMT & UTC times.  Could create a hash of timezones & GMT offsets, then would
	# need to determine if daylight savings.  For now, only convert GMT, UTC & no
	# timezone files.
	if (exists $metaRef->{'TimeZone'}) {
		my $tz = $metaRef->{'TimeZone'};
		if ( ($tz eq 'GMT') | ($tz eq 'UTC') ) {
			print $out "%TimeZone: \"$tz\" +0.000 0\n" 
		} else {
			elog_complain( "ERROR: Non-UTC/GMT Timezone detected, aborting!\n" );
			return 0;
		}
	}

	print $out "%TimeCoverage: $metaRef->{'TimeCoverage'} Minutes\n"
        if exists $metaRef->{'TimeCoverage'};

	printf $out "%%Origin: %11.7f %12.7f\n", (split ' ', $metaRef->{'Origin'})[0, 1];
	print  $out "$greatCircle\n";
	print  $out "$geodVersion\n";
	printf $out "%%RangeResolutionKMeters: %6.3f\n",
        $metaRef->{'RangeResolutionKMeters'}
        if exists $metaRef->{'RangeResolutionKMeters'};
	printf $out "%%TransmitCenterFreqMHz: %9.6f\n",
        $metaRef->{'TransmitCenterFreqMHz'}
        if exists $metaRef->{'TransmitCenterFreqMHz'};
	printf $out "%%DopplerResolutionHzPerBin: %11.9f\n",
        $metaRef->{'DopplerResolutionHzPerBin'}
        if exists $metaRef->{'DopplerResolutionHzPerBin'};
	printf $out "%%BraggSmoothingPoints: %d\n",
        $metaRef->{'BraggSmoothingPoints'}
        if exists $metaRef->{'BraggSmoothingPoints'};
	printf $out "%%CurrentVelocityLimit: %6.1f\n",
        (split ' ', $metaRef->{'CurrentVelocityLimit'})[0]
        if exists $metaRef->{'CurrentVelocityLimit'};
	printf $out "%%BraggHasSecondOrder: %d\n",
        $metaRef->{'BraggHasSecondOrder'}
        if exists $metaRef->{'BraggHasSecondOrder'};
	printf $out "%%RadialBraggPeakDropOff: %6.3f\n",
        $metaRef->{'RadialBraggPeakDropOff'}
        if exists $metaRef->{'RadialBraggPeakDropOff'};
	printf $out "%%RadialBraggPeakNull: %5.3f\n",
        $metaRef->{'RadialBraggPeakNull'}
        if exists $metaRef->{'RadialBraggPeakNull'};
	printf $out "%%RadialBraggNoiseThreshold: %5.3f\n",
        $metaRef->{'RadialBraggNoiseThreshold'}
        if exists $metaRef->{'RadialBraggNoiseThreshold'};
	printf $out "%%PatternAmplitudeCorrections: %6.4f %6.4f\n", 
        (split ' ', $metaRef->{'PatternAmplitudeCorrections'})[0, 1]
        if exists $metaRef->{'PatternAmplitudeCorrections'};
	printf $out "%%PatternAmplitudeCalculations: %6.4f %6.4f\n", 
        (split ' ', $metaRef->{'PatternAmplitudeCalculations'})[0, 1]
        if exists $metaRef->{'PatternAmplitudeCalculations'};
	printf $out "%%PatternPhaseCorrections: %5.2f %5.2f\n",
        (split ' ', $metaRef->{'PatternPhaseCorrections'})[0, 1]
        if exists $metaRef->{'PatternAmplitudeCalculations'};
	printf $out "%%PatternPhaseCalculations: %4.2f %4.2f\n",
        (split ' ', $metaRef->{'PatternPhaseCalculations'})[0, 1]
        if exists $metaRef->{'PatternPhaseCalculations'};
	printf $out "%%RadialMusicParameters: %6.3f %6.3f %6.3f\n",
        (split ' ', $metaRef->{'RadialMusicParameters'})[0, 1, 2]
        if exists $metaRef->{'RadialMusicParameters'};
	printf $out "%%MergedCount: %d\n",
        $metaRef->{'MergedCount'}
        if exists $metaRef->{'MergedCount'};
	printf $out "%%RadialMinimumMergePoints: %d\n",
        $metaRef->{'RadialMinimumMergePoints'}
        if exists $metaRef->{'RadialMinimumMergePoints'};
	printf $out "%%FirstOrderCalc: %d\n",
        $metaRef->{'FirstOrderCalc'}
        if exists $metaRef->{'FirstOrderCalc'};
	print  $out "%RangeStart: 1\n";
	printf $out "%%RangeEnd: %d\n",
        $metaRef->{'RangeEnd'}
        if exists $metaRef->{'RangeEnd'};
	print  $out "%ReferenceBearing: 0 DegNCW\n";
	print  $out "%PatternType: $metaRef->{'PatternType'}\n";

	# Print data
	print  $out "%TableType: LLUV RDL5\n";
	print  $out "%TableColumns: 16\n";
	print  $out "%TableColumnTypes: LOND LATD VELU VELV VFLG ESPC ETMP MAXV MINV XDST YDST RNGE BEAR VELO HEAD SPRC\n";
	printf $out "%%TableRows: %d\n", scalar @{$dataRef->[0]};
	print  $out "%TableStart:\n";
	print  $out "%%   Longitude   Latitude    U comp   V comp  VectorFlag    Spatial    Temporal     Velocity    Velocity  X Distance  Y Distance  Range   Bearing  Velocity  Direction   Spectra\n";
	print  $out "%%     (deg)       (deg)     (cm/s)   (cm/s)  (GridCode)    Quality     Quality     Maximum     Minimum      (km)        (km)      (km)  (deg NCW)  (cm/s)   (deg NCW)   RngCell\n";
	my ($i, $j);
	foreach $i (0..$#{$dataRef->[0]}) {
		foreach $j (0..$#$dataRef) {
			printf $out "  %12.7f", $dataRef->[$j][$i]   if $j ==  0; # Longitude
			printf $out " %11.7f" , $dataRef->[$j][$i]   if $j ==  1; # Latitude
			printf $out " %8.3f"  , $dataRef->[$j][$i]   if $j ==  2; # U
			printf $out " %8.3f"  , $dataRef->[$j][$i]   if $j ==  3; # V
				if ($j == 4) {
					printf $out " %10d"  , 0;                             # VectorFlag
					if ($dataRef->[$j][$i] eq 'NAN(001)') {
						printf $out " %11s", 'nan';                       # SpatialQuality (NaN)
					} else {    
						printf $out " %11.3f", $dataRef->[$j][$i];        # SpatialQuality
					}
					printf $out " %11.3f", 999;                           # TemporalQuality
					printf $out " %11.3f", $dataRef->[$j+5][$i];          # VelMax
					printf $out " %11.3f", $dataRef->[$j+5][$i];          # VelMin
				}
			printf $out " %11.4f" , $dataRef->[$j][$i]   if $j ==  5; # Xdistance
			printf $out " %11.4f" , $dataRef->[$j][$i]   if $j ==  6; # Ydistance
			printf $out " %8.3f"  , $dataRef->[$j][$i]   if $j ==  7; # Range
			printf $out " %7.1f"  , $dataRef->[$j][$i]   if $j ==  8; # Bearing
			printf $out " %9.2f"  , $dataRef->[$j][$i]   if $j ==  9; # Velocity
			printf $out " %9.1f"  , $dataRef->[$j][$i]   if $j == 10; # Direction
			printf $out " %9d\n"  , $dataRef->[$j][$i]   if $j == 11; # RangeCell
		}
	}

	print  $out "%TableEnd:\n";
	print  $out "%%\n";

	# Print remaining metadata
	my @now = gmtime;
	$now[5] += 1900;
	$now[4] += 1;

    	foreach $i (1..5) { $now[$i] = "0$now[$i]" if $now[$i] < 10 }
	printf $out "%%ProcessedTimeStamp: %4s %2s %2s %2s %2s %2s\n", (@now)[5, 4, 3, 2, 1, 0];
	print  $out "$processedBy\n";
	print  $out "$codeVersion\n";
	printf $out "%%ProcessingTool: \"Currents\" %s\n",
        $metaRef->{'Currents'}
        if exists $metaRef->{'Currents'};
	printf $out "%%ProcessingTool: \"RadialMerger\" %s\n",
        $metaRef->{'RadialMerger'}
        if exists $metaRef->{'RadialMerger'};
	printf $out "%%ProcessingTool: \"SpectraToRadial\" %s\n",
        $metaRef->{'SpectraToRadial'}
        if exists $metaRef->{'SpectraToRadial'};
	printf $out "%%ProcessingTool: \"RadialSlider\" %s\n",
        $metaRef->{'RadialSlider'}
        if exists $metaRef->{'RadialSlider'};
	print  $out "%End:\n";

	return 1;
}
