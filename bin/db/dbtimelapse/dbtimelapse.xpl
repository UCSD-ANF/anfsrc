#
# dbtimelapse
# 
# Kent Lindquist 
# Lindquist Consulting
# 2004
#

require "getopts.pl" ;
use Datascope ;

sub make_movie {
	my( $movie ) = @_;

	if( $opt_v ) {

		print "Making movie $movie:\n";
	}

	@db = dblookup( @db, "", "$movies{$movie}->{table}", "", "" );

	@db = dbsubset( @db, "$movies{$movie}->{expression}" );

	@db = dbsort( @db, "time" );

	$nrecs = dbquery( @db, dbRECORD_COUNT );

	if( $nrecs <= 3 ) {

		elog_complain( "...not enough records for $movie in $dbname, skipping\n" );

		next;
	}

	@files = ();
	for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {
		
		push( @files, dbextfile( @db ) );
	}

	if( defined( $startlabel ) && $startlabel ne "" ) {

		$startimage = "$startlabel " . shift( @files );

	} else {

		$startimage = "";
	}

	if( defined( $endlabel ) && $endlabel ne "" ) {

		$endimage = "$endlabel " . pop( @files );

	} else {

		$endimage = "";
	}

	$images = join( " ", @files );

	$path = "$movies{$movie}->{path}";
	$options = "$movies{$movie}->{options}";

	$cmd = "convert $verbose $options $startimage $delay $images $endimage $path";

	system( "$cmd" );
}

$Pf = "dbtimelapse";

if ( ! &Getopts('v') || @ARGV < 1 || @ARGV > 2 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "Usage: $pgm [-v] database\n" ) ; 

} else {

	$dbname = shift( @ARGV );
}

if( @ARGV ) {

	$requested_movie = pop( @ARGV );
} 

if( $opt_v ) {

	$verbose = "-verbose";

} else {

	$verbose = "";
}

$startlabel = pfget( $Pf, "startlabel" );
$endlabel = pfget( $Pf, "endlabel" );
$delay = pfget( $Pf, "delay" );

%movies = %{pfget( $Pf, "movies" )};

@db = dbopen ( "$dbname", "r+" );

if( defined( $requested_movie ) ) {

	if( ! defined( $movies{$requested_movie}->{path} ) ) {

		elog_die( "Couldn't find path for $requested_movie in $Pf\n" );
	}

	make_movie( $requested_movie );

} else {

	foreach $movie ( keys %movies ) {

		make_movie( $movie );
	}
}
