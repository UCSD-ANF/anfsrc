
require "getopts.pl" ;
use Datascope ;
 
$size = "120x120";
$thumbnails_dir = "./thumbnails";

if ( ! &Getopts('d:s:v') || @ARGV != 1 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "Usage: $pgm [-v] [-d thumbnails_dir] [-s size] database\n" ) ; 

} else {

	$dbname = pop( @ARGV );
}

if( $opt_s ) {
	$size = $opt_s;
}

if( $opt_d ) {
	$thumbnails_dir = $opt_d;
}

@db = dbopen ( "$dbname", "r+" );
@db = dblookup( @db, "", "images", "", "" );
@dbthumb = dblookup( @db, "", "thumbnails", "", "" );

@db = dbnojoin( @db, @dbthumb );
$nrecs = dbquery( @db, dbRECORD_COUNT );

$added = 0;
for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {

	$imagefile = dbextfile( @db );
	( $imagename, $time, $dfile, $format ) = dbgetv( @db, "imagename", 
			"time", "dfile", "format" );
	$thumb_dfile = "t_$dfile";
	$thumbfile = concatpaths( $thumbnails_dir, $thumb_dfile );

	$cmd = "convert -size $size $imagefile +profile \"*\" -resize $size $thumbfile";

	if( $opt_v ) {
		print STDERR "Running: $cmd\n";
	}

	system( $cmd );

	dbaddv( @dbthumb, "imagename", $imagename, 
		          "time", $time,
		          "thumbsize", $size,
		          "format", $format,
		          "dir", $thumbnails_dir,
		          "dfile", $thumb_dfile );

	$added++;
}

print "Added $added thumbnails\n";

