
require "getopts.pl" ;
use Datascope ;

#Fake the trwfname call since it's not in the perldb interface
sub trwfname {
	my( $pattern ) = pop( @_ );
	my( @db ) = @_;

	( $time, $imagename, $format ) = dbgetv( @db, "time", "imagename", "format" );
	$relpath = epoch2str( $time, $pattern );
	$relpath =~ s/{imagename}/$imagename/;
	$relpath =~ s/{format}/$format/;

	( $dir, $base, $suffix ) = parsepath( $relpath );
		
	system( "mkdir -p $dir" );

	$dfile = $base;
	if( $suffix ne "" ) {
		$dfile .= "." . $suffix;
	}

	dbputv( @db, "dir", $dir, "dfile", $dfile );

	return $relpath;
}
 
$Pf = "make_thumbnails";

if ( ! &Getopts('v') || @ARGV != 1 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "Usage: $pgm [-v] database\n" ) ; 

} else {

	$dbname = pop( @ARGV );
}

$thumbnail_filenames = pfget( $Pf, "thumbnail_filenames" );
$thumbnail_size = pfget( $Pf, "thumbnail_size" );
$thumbnail_command = pfget( $Pf, "thumbnail_command" );

@db = dbopen ( "$dbname", "r+" );
@db = dblookup( @db, "", "images", "", "" );
@dbthumb = dblookup( @db, "", "thumbnails", "", "" );

@db = dbnojoin( @db, @dbthumb );
$nrecs = dbquery( @db, dbRECORD_COUNT );

$added = 0;
for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {

	$imagefile = dbextfile( @db );
	( $imagename, $time, $format ) = dbgetv( @db, "imagename", "time", "format" );

	$dbthumb[3] = dbaddv( @dbthumb, "imagename", $imagename, 
		          "time", $time,
		          "imagesize", $thumbnail_size,
		          "format", $format );

	$thumbfile = trwfname( @dbthumb, $thumbnail_filenames );

	$cmd = "$thumbnail_command $imagefile $thumbfile";

	if( $opt_v ) {
		print STDERR "Running: $cmd\n";
	}

	system( $cmd );

	$added++;
}

print "Added $added thumbnails\n";

