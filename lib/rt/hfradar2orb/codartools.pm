
package codartools;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	is_valid_LLUV
	Verbose
	codeVersion
	processedBy
	greatCircle
	geodVersion
);	

use Geo::Ellipsoid;
use POSIX qw(ceil floor);

BEGIN {
	# Public:
	$Verbose = 0;
	$codeVersion = '%ProcessingTool: "codar_rb2lluv.pl" 1.00';
	$processedBy = '%ProcessedBy: "HFRNet"';
	$greatCircle = '%GreatCircle: "WGS84" 6378137.000  298.257223563';
	$geodVersion = '%GeodVersion: "PGEO" ' .  $Geo::Ellipsoid::VERSION . ' 2005 11 04';

	# Private:
	$Valid_filetype = "^\s*%FileType:\s+LLUV\s+rdls";
	$Valid_site = "^\s*%Site:\s+\w{4}";
	$Valid_timestamp = "^\s*%TimeStamp:\s+\d{4}\s+\d{1,2}\s+\d{1,2}\s+" .
			   "\d{1,2}\s+\d{1,2}\s+\d{1,2}";
	$Valid_timezone = "^\s*%TimeZone:\s+(")?(GMT|UTC)(")?";
	$Valid_patterntype = "^\s*%PatternType:\s+[A-Za-z]{3,}";
}

sub is_valid_LLUV {

	my( @block ) = @_;

	if( ! defined( @block ) || scalar( @block ) < 1 ) {
		
		elog_complain( "is_valid_LLUV: empty data block\n" );

		return 0;
	}

	if( ! grep( /$Valid_filetype/i, @block ) ) {					

		elog_complain( "is_valid_LLUV: FileType row invalid or not present\n" );

		return 0;

	}  elsif( ! grep( /$Valid_site/i, @block ) ) {

		elog_complain( "is_valid_LLUV: Site row invalid or not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_timestamp/, @block ) {	

		elog_complain( "is_valid_LLUV: TimeStamp row invalid or not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_timezone/i, @block ) ) {

		elog_complain( "is_valid_LLUV: TimeZone row invalid or not present\n" );

		return 0;

	} elsif( ! grep( /$Valid_patterntype/i, @block ) {

		elog_complain( "is_valid_LLUV: PatternType row invalid or not present\n" );

		return 0;
	}

	my( @tmp ) = grep( /^\s*%Origin:/i, @block );

	my ($key, $lat, $lon) = split( ' ', $tmp[0], 3 );

	if( $lat < -90 || $lat > 90 || $lon < -180 || $lon > 180 ) {

		elog_complain( "is_valid_LLUV: invalid lat,lon '($lat,$lon)' \n" );

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
	    ! defined( $TableCols ) {

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


# Get file to convert from input
$pathFile = $ARGV[0];
$file     = basename $pathFile;
$rootDir  = $pathFile;
$rootDir  =~ s%/$file%%;

# Generate LLUV filename
$lluvFile = &lluvFname($file);
die "ERROR: Input filename format $file not recognized\n"
	unless defined $lluvFile;

# Convert file
die "ERROR: Failure in conversion of $pathFile\n"
	unless &convertFile($pathFile, "$rootDir/$lluvFile");


sub lluvFname {
	my $file = $_[0];
	my $lluvFile;
	if ($file =~ m/^Rad([sz])(\w{4})[_\s](\d{2})[-_](\d{2})[-_](\d{2})[-_\s](\d{2})(\d{2})(.rv)?$/) {
	    my $patt = $1;
	    my $site = $2;
	    my $yyyy = $3;
	    my $mm   = $4;
	    my $dd   = $5;
	    my $HH   = $6;
	    my $MM   = $7;
	    $yyyy += 1900 if $yyyy > 50;
	    $yyyy += 2000 if $yyyy < 50;
	    $patt = 'i' if $patt eq 's';
	    $patt = 'm' if $patt eq 'z';
	    $lluvFile = "RDL${patt}_${site}_${yyyy}_${mm}_${dd}_$HH$MM.ruv";
	} else {
	    return;
	}
	return $lluvFile;
}


sub convertFile {
	my ($pathFile, $lluvFile) = @_;

	# Slurp file
	my @file = &slurpFile($pathFile);
	unless (@file > 0) {
	    print STDERR "ERROR reading $pathFile\n";
	    return;
	}
	print "Read $pathFile\n";

	# Check time-stamp OK & get time-zone
	my @tInfo = &chkTime($pathFile, @file);
	unless (@tInfo == 2) {
	    print STDERR "ERROR processing time-stamp from $pathFile\n";
	    return;
	}
	print "Time-stamp obtained: @tInfo\n";

	# Get Radar Position
	my @origin = &getPos(@file);
	unless (@origin == 2) {
	    print STDERR "ERROR extracting radar position from $pathFile\n";
	    return;
	}
	printf "Origin obtained: %11.7f %12.7f\n", $origin[0], $origin[1];

	# Convert data from range-bin to LLUV
	my @data = &rb2lluv(@origin, @file);
	unless (@data == 16) {
	    print STDERR "ERROR converting range-bin data to LLUV from $pathFile\n";
	    return;
	}
	my $rangeRes  = shift(@data);
	my $tCoverage = shift(@data);
	my $rangeEnd  = shift(@data);
	my $metaStart = shift(@data);
	print "Data converted from range-bin to LLUV\n";

	# Extract metadata, add metadata collected from header
	# & verify minimum metadata has been obtained
	my %metadata = &getMetadata($pathFile, $metaStart, @file);
	unless (scalar keys %metadata > 0) {
	    print STDERR "ERROR extracting metadata from $pathFile\n";
	    return;
	}
	$metadata{"TimeZone"}               = $tInfo[0] unless $tInfo[0] eq "NOTZ";
	$metadata{"TimeStamp"}              = $tInfo[1];
	$metadata{"TimeCoverage"}           = $tCoverage;
	$metadata{"Origin"}                 = $origin[0] . " " . $origin[1] ;
	$metadata{"RangeResolutionKMeters"} = $rangeRes;
	$metadata{"RangeEnd"}               = $rangeEnd;
	unless ( exists $metadata{"Site"}   & exists $metadata{"TimeStamp"} &
	         exists $metadata{"Origin"} & exists $metadata{"PatternType"} ) {
	    print STDERR "ERROR: Minimum metadata requirements not met for conversion\n";
	    return;
	}
	print "Metadata extracted & minimum requirements for conversion met\n";

	# Write out as LLUV
	unless ( &writeLLUV($lluvFile, \@data, \%metadata) ) { 
	    print STDERR "ERROR writing data to $lluvFile\n";
	    return;
	}
	print "LLUV format file written to $lluvFile\n";
	return 1;
}


sub slurpFile {
	my $inFile = $_[0];
	unless (-e $inFile) {
	    print STDERR "ERROR: $inFile couldn't be found\n";
	    return;
	}
	my $inputRecordSeparator = $/;
	undef $/;
	open F, $inFile;
	my $file = <F>;
	$/ = $inputRecordSeparator;
	$file =~ s/\r/\n/g;
	my @file = split /\n/, $file;
	return @file;
}


sub chkTime {
	my $pathFile = shift @_;
	my @file     = @_;

	# Get timestamp from filename
	my $fileName = basename $pathFile;
	my ($fy, $fm, $fd, $fH, $fM, $tStamp);
	if ($fileName =~ m/^Rad[sz]\w{4}[_\s](\d{2})[-_](\d{2})[-_](\d{2})[-_\s](\d{2})(\d{2})(.rv)?$/) {
	    ($fy, $fm, $fd, $fH, $fM) = ($1, $2, $3, $4, $5);
	    if ($fy < 50) {
	        $tStamp = $fy+2000 . " $fm $fd $fH $fM 00";
	    } else {
	        $tStamp = $fy+1900 . " $fm $fd $fH $fM 00";
	    }
	} else {
	    print STDERR "ERROR: Unable to extract time from filename using match expression\n";
	    return;
	}


	# Extract time info from line 1 of range-bin file
	my $tz;
	if ($file[0] =~ 
	    m/^\s*\d{1,2}:\d{2}(:\d{2})?\s*(\w{2,3}\s)?\s*\w+,\s*\w+\s*\d{1,2},\s*\d{4}\s*(\w{1,4})?\s*(\w{1,4})?\s*(-\d+)\s*$/i) {

	    # Get timezone, if found
	    if (defined $2) {
	        if ($2 !~ /(AM|PM)/) {
	            $tz = $2;
	            $tz =~ s/\s+$//;
	        }
	    }
	    $tz = $3 if (defined $3) & (!defined $tz);

	    # Verify serial date against filename timestamp
	    ($ly, $lm, $ld, $lH, $lM, $lS)= (gmtime($5 - 2082844800 + 2**32))[5, 4, 3, 2, 1, 0];
	    $lm++;
	    $ly -= 100 if $ly >= 100;
	    unless ( ($ly == $fy) & ($lm == $fm) & ($ld == $fd) & ($lH == $fH) & ($lM == $fM) & ($lS == 0) ) {
	        print STDERR "ERROR: Filename time-stamp $fy $fm $fd $fH $fM 0 doesn't match serial time-stamp $ly $lm $ld $lH $lM $lS\n";
	        return;
	    }

	# Return if line 1 couldn't be parsed
	} else {
	    print STDERR "ERROR: Format unrecognized on LINE 1\n";
	    return;
	}

	# If sucessful, return timezone (NOTZ = no timezone)
	return ($tz, $tStamp) if defined $tz;
	return "NOTZ", $tStamp;
}


sub getPos {
	my @file  = @_;
	my $dLat;
	my $dLon;

	# Check for more common position reported in degrees & decimal minutes w/various separators
	if ($file[1] =~ 
	    m/^\s*(\d{1,2})(\302)?(\260|\241|\373|\s)(\d{1,2}.\d+)('|\241)(N|S)(,|\s)\s*(\d{1,3})(\302)?(\260|\241|\373|\s)(\d{1,2}.\d+)('|\241)(E|W)\s*$/i) {
	    if ( (defined $1) & (defined $4) & (defined $6) & (defined $8) & (defined $11) & (defined $13) ) {
	        $dLat = $1 + $4/60;
	        $dLat = -1 * $dLat if $6  eq "S";
	        $dLon = $8 + $11/60;
	        $dLon = -1 * $dLon if $13 eq "W";
	    }

	# Check for decimal degrees (ie. RFG1)
	} elsif ($file[1] =~ m/^\s*(\d{1,2}.\d+)(\302)?\241(N|S),(\d{1,3}.\d+)(\302)?\241(E|W)\s*$/i) { 
	    if ( (defined $1) & (defined $3) & (defined $4) & (defined $6) ) {
	        $dLat = $1; 
	        $dLat = -1 * $dLat if $3 eq "S";
	        $dLon = $4;
	        $dLon = -1 * $dLon if $6 eq "W";
	    }
	} else {
	    print STDERR "ERROR: Position could not be parsed from LINE 2\n";
	    return;
	}
	my @origin = ($dLat, $dLon);
	return @origin;
}


sub rb2lluv {
	my @origin = (shift @_, shift @_);
	my @file   = @_;

	# Get distance to first range cell, range resolution, reference angle &
	# time coverage
	$file[2] =~ s/^\s+//;
	$file[2] =~ s/\s+$//;
	my ($d0, $rRes, $refAng, $dt) = split ' ', $file[2];
	$dt *= 60;
	unless ( (defined $d0) & (defined $rRes) & (defined $refAng) & (defined $dt) ) {
	    print STDERR "ERROR: Failed to read line 3\n";
	    return;
	}

	# Get number of range cells
	my $nRngCells;
	if ( $file[3] =~ m/^\s*(\d+)\s*$/ ) {
	    $nRngCells = $1;
	} else { 
	    print STDERR "ERROR: Failed to read line 4\n";
	    return;
	}

	# Get starting range cell index
	my $rngStart; 
	if ( $file[4] =~ m/^\s*\d+\s+(\d+)\s*$/ ) {
	    $rngStart = $1;
	} else {
	    print STDERR "ERROR obtaining starting range bin on line 5\n";
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
	        printf STDERR "ERROR reading data from line %i\n", $lineInd + 1;
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
	                printf STDERR "ERROR reading data for range cell %i\n", $rangeCell;
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
	    ($Lats[$i],    $Lons[$i])       = $geo -> at($origin[0], $origin[1], $Ranges[$i]*1000, $Bearings[$i]);
	    ($Eastings[$i], $Northings[$i]) = $geo -> displacement($origin[0], $origin[1], $Lats[$i], $Lons[$i]);
	    $Eastings[$i]  /= 1000;
	    $Northings[$i] /= 1000;

	    # Compute bearing from radial vector to radar site
	    $Directions[$i] = $geo -> bearing($Lats[$i], $Lons[$i], $origin[0], $origin[1]);
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
	my $pathFile  = shift @_;
	my $metaStart = shift @_;
	my @file      = @_;

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
	foreach $lineInd ($metaStart..@file-1) {
	    my $line = $file[$lineInd];
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
	        print STDERR "WARNING, unmatched metadata field from range-bin file: $key\t$val\n"
	            unless $key eq "RadSmoothing";
	    }
	}

	# Extract site and beampattern from filename
	$fileName = basename $pathFile;
	if ($fileName =~ m/^Rad([sz])(\w{4})[_\s]\d{2}[-_]\d{2}[-_]\d{2}[-_\s]\d{2}\d{2}(.rv)?$/) {
	    my ($patt, $site) = ($1, $2);
	    $metadata{"PatternType"} = "Ideal"    if $patt eq 's';
	    $metadata{"PatternType"} = "Measured" if $patt eq 'z';
	    $metadata{"Site"}        = $site;
	} else {
	    print STDERR "ERROR: Unable to extract site & pattern from filename using match expression\n";
	    return;
	}

	return %metadata;
}


sub writeLLUV {
	my ($lluvFile, $dataRef, $metaRef) = @_;
	return unless open LLUV, "> $lluvFile";

	# Begin writing metadata
	print LLUV "%CTF: 1.00\n";
	print LLUV "%FileType: LLUV rdls \"RadialMap\"\n";
	print LLUV "%LLUVSpec: 1.02  2006 01 11\n";
	print LLUV "%Manufacturer: CODAR Ocean Sensors. SeaSonde\n";
	print LLUV "%Site: $metaRef->{'Site'} \"\"\n";
	print LLUV "%TimeStamp: $metaRef->{'TimeStamp'}\n";

	# Since GMT offset & daylight savings in included in TimeZone key, only report
	# GMT & UTC times.  Could create a hash of timezones & GMT offsets, then would
	# need to determine if daylight savings.  For now, only convert GMT, UTC & no
	# timezone files.
	if (exists $metaRef->{'TimeZone'}) {
	    my $tz = $metaRef->{'TimeZone'};
	    if ( ($tz eq 'GMT') | ($tz eq 'UTC') ) {
	        print LLUV "%TimeZone: \"$tz\" +0.000 0\n" 
	    } else {
	        print STDERR "ERROR: Non-UTC/GMT Timezone detected, aborting!\n";
	        close LLUV;
	        unlink $lluvFile;
	        return;
	    }
	}

	print  LLUV "%TimeCoverage: $metaRef->{'TimeCoverage'} Minutes\n"
	    if exists $metaRef->{'TimeCoverage'};
	printf LLUV "%%Origin: %11.7f %12.7f\n", (split ' ', $metaRef->{'Origin'})[0, 1];
	print  LLUV "$greatCircle\n";
	print  LLUV "$geodVersion\n";
	printf LLUV "%%RangeResolutionKMeters: %6.3f\n",
	    $metaRef->{'RangeResolutionKMeters'}
	    if exists $metaRef->{'RangeResolutionKMeters'};
	printf LLUV "%%TransmitCenterFreqMHz: %9.6f\n",
	    $metaRef->{'TransmitCenterFreqMHz'}
	    if exists $metaRef->{'TransmitCenterFreqMHz'};
	printf LLUV "%%DopplerResolutionHzPerBin: %11.9f\n",
	    $metaRef->{'DopplerResolutionHzPerBin'}
	    if exists $metaRef->{'DopplerResolutionHzPerBin'};
	printf LLUV "%%BraggSmoothingPoints: %d\n",
	    $metaRef->{'BraggSmoothingPoints'}
	    if exists $metaRef->{'BraggSmoothingPoints'};
	printf LLUV "%%CurrentVelocityLimit: %6.1f\n",
	    (split ' ', $metaRef->{'CurrentVelocityLimit'})[0]
	    if exists $metaRef->{'CurrentVelocityLimit'};
	printf LLUV "%%BraggHasSecondOrder: %d\n",
	    $metaRef->{'BraggHasSecondOrder'}
	    if exists $metaRef->{'BraggHasSecondOrder'};
	printf LLUV "%%RadialBraggPeakDropOff: %6.3f\n",
	    $metaRef->{'RadialBraggPeakDropOff'}
	    if exists $metaRef->{'RadialBraggPeakDropOff'};
	printf LLUV "%%RadialBraggPeakNull: %5.3f\n",
	    $metaRef->{'RadialBraggPeakNull'}
	    if exists $metaRef->{'RadialBraggPeakNull'};
	printf LLUV "%%RadialBraggNoiseThreshold: %5.3f\n",
	    $metaRef->{'RadialBraggNoiseThreshold'}
	    if exists $metaRef->{'RadialBraggNoiseThreshold'};
	printf LLUV "%%PatternAmplitudeCorrections: %6.4f %6.4f\n", 
	    (split ' ', $metaRef->{'PatternAmplitudeCorrections'})[0, 1]
	    if exists $metaRef->{'PatternAmplitudeCorrections'};
	printf LLUV "%%PatternAmplitudeCalculations: %6.4f %6.4f\n", 
	    (split ' ', $metaRef->{'PatternAmplitudeCalculations'})[0, 1]
	    if exists $metaRef->{'PatternAmplitudeCalculations'};
	printf LLUV "%%PatternPhaseCorrections: %5.2f %5.2f\n",
	    (split ' ', $metaRef->{'PatternPhaseCorrections'})[0, 1]
	    if exists $metaRef->{'PatternAmplitudeCalculations'};
	printf LLUV "%%PatternPhaseCalculations: %4.2f %4.2f\n",
	    (split ' ', $metaRef->{'PatternPhaseCalculations'})[0, 1]
	    if exists $metaRef->{'PatternPhaseCalculations'};
	printf LLUV "%%RadialMusicParameters: %6.3f %6.3f %6.3f\n",
	    (split ' ', $metaRef->{'RadialMusicParameters'})[0, 1, 2]
	    if exists $metaRef->{'RadialMusicParameters'};
	printf LLUV "%%MergedCount: %d\n",
	    $metaRef->{'MergedCount'}
	    if exists $metaRef->{'MergedCount'};
	printf LLUV "%%RadialMinimumMergePoints: %d\n",
	    $metaRef->{'RadialMinimumMergePoints'}
	    if exists $metaRef->{'RadialMinimumMergePoints'};
	printf LLUV "%%FirstOrderCalc: %d\n",
	    $metaRef->{'FirstOrderCalc'}
	    if exists $metaRef->{'FirstOrderCalc'};
	print  LLUV "%RangeStart: 1\n";
	printf LLUV "%%RangeEnd: %d\n",
	    $metaRef->{'RangeEnd'}
	    if exists $metaRef->{'RangeEnd'};
	print  LLUV "%ReferenceBearing: 0 DegNCW\n";
	print  LLUV "%PatternType: $metaRef->{'PatternType'}\n";

	# Print data
	print  LLUV "%TableType: LLUV RDL5\n";
	print  LLUV "%TableColumns: 16\n";
	print  LLUV "%TableColumnTypes: LOND LATD VELU VELV VFLG ESPC ETMP MAXV MINV XDST YDST RNGE BEAR VELO HEAD SPRC\n";
	printf LLUV "%%TableRows: %d\n", scalar @{$dataRef->[0]};
	print  LLUV "%TableStart:\n";
	print  LLUV "%%   Longitude   Latitude    U comp   V comp  VectorFlag    Spatial    Temporal     Velocity    Velocity  X Distance  Y Distance  Range   Bearing  Velocity  Direction   Spectra\n";
	print  LLUV "%%     (deg)       (deg)     (cm/s)   (cm/s)  (GridCode)    Quality     Quality     Maximum     Minimum      (km)        (km)      (km)  (deg NCW)  (cm/s)   (deg NCW)   RngCell\n";
	my ($i, $j);
	foreach $i (0..$#{$dataRef->[0]}) {
	    foreach $j (0..$#$dataRef) {
	        printf LLUV "  %12.7f", $dataRef->[$j][$i]   if $j ==  0; # Longitude
	        printf LLUV " %11.7f" , $dataRef->[$j][$i]   if $j ==  1; # Latitude
	        printf LLUV " %8.3f"  , $dataRef->[$j][$i]   if $j ==  2; # U
	        printf LLUV " %8.3f"  , $dataRef->[$j][$i]   if $j ==  3; # V
	        if ($j == 4) {
	            printf LLUV " %10d"  , 0;                             # VectorFlag
	            if ($dataRef->[$j][$i] eq 'NAN(001)') {
	                printf LLUV " %11s", 'nan';                       # SpatialQuality (NaN)
	            } else {    
	                printf LLUV " %11.3f", $dataRef->[$j][$i];        # SpatialQuality
	            }
	            printf LLUV " %11.3f", 999;                           # TemporalQuality
	            printf LLUV " %11.3f", $dataRef->[$j+5][$i];          # VelMax
	            printf LLUV " %11.3f", $dataRef->[$j+5][$i];          # VelMin
	        }
	        printf LLUV " %11.4f" , $dataRef->[$j][$i]   if $j ==  5; # Xdistance
	        printf LLUV " %11.4f" , $dataRef->[$j][$i]   if $j ==  6; # Ydistance
	        printf LLUV " %8.3f"  , $dataRef->[$j][$i]   if $j ==  7; # Range
	        printf LLUV " %7.1f"  , $dataRef->[$j][$i]   if $j ==  8; # Bearing
	        printf LLUV " %9.2f"  , $dataRef->[$j][$i]   if $j ==  9; # Velocity
	        printf LLUV " %9.1f"  , $dataRef->[$j][$i]   if $j == 10; # Direction
	        printf LLUV " %9d\n"  , $dataRef->[$j][$i]   if $j == 11; # RangeCell
	    }
	}
	print  LLUV "%TableEnd:\n";
	print  LLUV "%%\n";

	# Print remaining metadata
	my @now = gmtime;
	$now[5] += 1900;
	$now[4] += 1;
	foreach $i (1..5) { $now[$i] = "0$now[$i]" if $now[$i] < 10 }
	printf LLUV "%%ProcessedTimeStamp: %4s %2s %2s %2s %2s %2s\n", (@now)[5, 4, 3, 2, 1, 0];
	print  LLUV "$processedBy\n";
	print  LLUV "$codeVersion\n";
	printf LLUV "%%ProcessingTool: \"Currents\" %s\n",
	    $metaRef->{'Currents'}
	    if exists $metaRef->{'Currents'};
	printf LLUV "%%ProcessingTool: \"RadialMerger\" %s\n",
	    $metaRef->{'RadialMerger'}
	    if exists $metaRef->{'RadialMerger'};
	printf LLUV "%%ProcessingTool: \"SpectraToRadial\" %s\n",
	    $metaRef->{'SpectraToRadial'}
	    if exists $metaRef->{'SpectraToRadial'};
	printf LLUV "%%ProcessingTool: \"RadialSlider\" %s\n",
	    $metaRef->{'RadialSlider'}
	    if exists $metaRef->{'RadialSlider'};
	print  LLUV "%End:\n";

	# Close file & return
	close LLUV;
	return 1;
}
