#
# dbtimelapse
# 
# Kent Lindquist 
# Lindquist Consulting
# 2004
#

require "getopts.pl" ;
use Datascope ;

$Pf = "dbtimelapse";

if ( ! &Getopts('v') || @ARGV != 1 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "Usage: $pgm [-v] database\n" ) ; 

} else {

	$dbname = pop( @ARGV );
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

foreach $movie ( keys %movies ) {
	
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

	$cmd = "convert $verbose $startimage $delay $images $endimage $path";

	system( "$cmd" );
}

# 
# $added = 0;
# for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {
# 
# 	$imagefile = dbextfile( @db );
# 	( $imagename, $time, $format ) = dbgetv( @db, "imagename", "time", "format" );
# 
# 	$dbthumb[3] = dbaddv( @dbthumb, "imagename", $imagename, 
# 		          "time", $time,
# 		          "thumbsize", $thumbnail_size,
# 		          "format", $format );
# 
# 	$thumbfile = trwfname( @dbthumb, $thumbnail_filenames );
# 
# 	$cmd = "$thumbnail_command $imagefile $thumbfile";
# 
# 	if( $opt_v ) {
# 		print STDERR "Running: $cmd\n";
# 	}
# 
# 	system( $cmd );
# 
# 	$added++;
# }
# 
# print "Added $added thumbnails\n";
# 
