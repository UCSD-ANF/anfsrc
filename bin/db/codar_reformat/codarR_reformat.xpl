use Datascope;

sub reformat_origin_string {
	my( $origin_string ) = shift( @_ );
	my( $orglat, $orglon );

	if( $origin_string !~ 
		m@\s*(\d+)\D([\.\d]+)'([NS]),\s*(\d+)\D([\.\d]+)'([EW])@i ) {
		die( "codarR_reformat: Failed to extract coordinate origin" );
	} else {
		$latdeg = $1;
		$latmin = $2;
		$lathemi = $3;
		$londeg = $4;
		$lonmin = $5;
		$lonhemi = $6;
	}

	$orglat = $latdeg + $latmin / 60.;

	if( $lathemi =~ m/S/i ) {
		$orglat *= -1;
	}

	$orglon = $londeg + $lonmin / 60.;

	if( $lonhemi =~ m/W/i ) {
		$orglon *= -1;
	}

	return ( $orglat, $orglon );
}

if( $#ARGV != 1 ) {
	die( "Usage: codarR_reformat filename dbname\n" );
} else {
	$datafile = $ARGV[0];
	$dbname = $ARGV[1];
}

open( F, "$datafile" );

if( ! -e "$dbname" ) {
	open( D, ">$dbname" );
	print D "#\nschema Codar0.1\n";
	close( D );
}

@db = dbopen( "$dbname", "r+" );
@db = dblookup( @db, "", "radial", "", "" );
if( $db[1] < 0 ) {
	die( "codarR_reformat: Couldn't find table 'radial' in $dbname" );
}

@lines = split( /\r/, <F> );

# open( S, ">stuff" );
# print S join( "\n", @lines );
# close( S );
# exit( 0 );



if( shift( @lines ) !~ /^\s*(.*)\s+([-\d]+)/ ) {
	die( "codarR_reformat: No time/origin line. Bye.\n" );
} else {
	$time_string = $1;
	$time_secfrom1904 = $2;
}

$origin_string = shift( @lines );
( $orglat, $orglon )  = reformat_origin_string( $origin_string );

print "$orglat, $orglon\n";

$line = shift( @lines );
$line =~ s/^\s*//;

($dist_to_first_rc_km, $dist_between_rc_km, $refangle_ccwfromeast, $timecov_hrs ) = 
	split( /\s+/, $line );

print "Vals are $dist_to_first_rc_km, $dist_between_rc_km, $refangle_ccwfromeast, $timecov_hrs\n";

$ncells = shift( @lines );
$ncells =~ s/^\s*//;
$ncells =~ s/\s*$//;


while( $line = shift( @lines ) ) {
	chomp( $line );
	next if( $line =~ /^\s*$/ );
	$line =~ s/^\s*//;

	@parts = split( /\s+/, $line );
	if( $#parts != 1 ) {
		print "$line\n";
		last;
	} else {
		( $nvectors, $current_index ) = @parts;
	}

	print "$nvectors $current_index\n";

	$lines_per_block = int( $nvectors / 7 ) + ( $nvectors % 7 == 0 ? 0 : 1 );

	$bearings = join( " ", splice( @lines, 0, $lines_per_block ) );
	$bearings =~ s/^\s*//;
	@bearings = split( /\s+/, $bearings );

	$velocities = join( " ", splice( @lines, 0, $lines_per_block ) );
	$velocities =~ s/^\s*//;
	@velocities = split( /\s+/, $velocities );

	$uncertainties = join( " ", splice( @lines, 0, $lines_per_block ) );
	$uncertainties =~ s/^\s*//;
	@uncertainties = split( /\s+/, $uncertainties );

# SCAFFOLD 	( $dx, $dy, $u, $v, $eu, $ev, $gridflag, $cov,
# SCAFFOLD 	  $lat, $lon, $n1, $n2, $n3, $n4, $n5, $n6 ) = 
# SCAFFOLD 					split( /\s+/, $line );

# SCAFFOLD 	dbaddv( @db, "time", $time,
# SCAFFOLD 		     "orglat", $orglat,
# SCAFFOLD 		     "orglon", $orglon,
# SCAFFOLD 		     "dx", $dx,
# SCAFFOLD 		     "dy", $dy,
# SCAFFOLD 		     "u", $u,
# SCAFFOLD 		     "v", $v,
# SCAFFOLD 		     "eu", $eu,
# SCAFFOLD 		     "ev", $ev,
# SCAFFOLD 		     "gridflag", $gridflag,
# SCAFFOLD 		     "cov", $cov,
# SCAFFOLD 		     "lat", $lat,
# SCAFFOLD 		     "lon", $lon,
# SCAFFOLD 		     "n1", $n1,
# SCAFFOLD 		     "n2", $n2,
# SCAFFOLD 		     "n3", $n3,
# SCAFFOLD 		     "n4", $n4,
# SCAFFOLD 		     "n5", $n5,
# SCAFFOLD 		     "n6", $n6 );
		
}

print shift( @lines );

dbclose( @db );
close( F );
