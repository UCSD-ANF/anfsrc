use Datascope;

sub reformat_origin_string {
	my( $origin_string ) = shift( @_ );
	my( $orglat, $orglon );

	if( $origin_string !~ 
		m@\s*(\d+)\D([\.\d]+)'([NS]),\s+(\d+)\D([\.\d]+)'([EW])@i ) {
		die( "codarV_reformat: Failed to extract coordinate origin" );
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
	die( "Usage: codarV_reformat filename dbname\n" );
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
@db = dblookup( @db, "", "vector", "", "" );
if( $db[1] < 0 ) {
	die( "codarV_reformat: Couldn't find table 'vector' in $dbname" );
}

@lines = split( /\r/, <F> );

if( shift( @lines ) ne "Total vectors" ) {
	die( "codarV_reformat: was expecting file to start with \"Total vectors\". Bye.\n" );
}

if( shift( @lines ) !~ /Format version # 4/ ) {
	die( "codarV_reformat: File not labelled as version 4. Bye.\n" );
}

if( shift( @lines ) !~ /^\s*(.*)\s+Org:\s+(.*)/ ) {
	die( "codarV_reformat: No time/origin line. Bye.\n" );
} else {
	$time_string = $1;
	$origin_string = $2;
}

@time_elements = split( /\s+/, $time_string );
if( $time_string =~ /\s+[AP]\.?M\.?\s+/i ) {
	$dayname_position = 2;
} else {
	$dayname_position = 1;
}
splice( @time_elements, $dayname_position, 1 );
$time = str2epoch( join( " ", @time_elements ) );

( $orglat, $orglon )  = reformat_origin_string( $origin_string );

while( $line = shift( @lines ) ) {
	chomp( $line );
	next if( $line =~ /^\s*$/ );
	$line =~ s/^\s*//;

	( $dx, $dy, $u, $v, $eu, $ev, $gridflag, $cov,
	  $lat, $lon, $n1, $n2, $n3, $n4, $n5, $n6 ) = 
					split( /\s+/, $line );

	dbaddv( @db, "time", $time,
		     "orglat", $orglat,
		     "orglon", $orglon,
		     "dx", $dx,
		     "dy", $dy,
		     "u", $u,
		     "v", $v,
		     "eu", $eu,
		     "ev", $ev,
		     "gridflag", $gridflag,
		     "cov", $cov,
		     "lat", $lat,
		     "lon", $lon,
		     "n1", $n1,
		     "n2", $n2,
		     "n3", $n3,
		     "n4", $n4,
		     "n5", $n5,
		     "n6", $n6 );
		
}

dbclose( @db );
close( F );
