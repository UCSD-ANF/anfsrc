
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

if ( ! &Getopts('t:v') || @ARGV != 1 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "Usage: $pgm [-v] [-t template] database\n" ) ; 

} else {

	$dbname = pop( @ARGV );
	$dbname = abspath( $dbname );
}

if( $opt_t ) {
	$template_name = $opt_t;
} else {
	$template_name = "thumbnails";
}

$ref = pfget( $Pf, "templates{$template_name}" );

if( ! defined( $ref ) ) {

	die( "Can't find template '$template_name' in $Pf.pf! Bye.\n" );

} elsif( $opt_v ) {

	print STDERR "Using '$template_name' template\n";
	
}

$filenames = $ref->{"filenames"};
$size = $ref->{"size"};
$command = $ref->{"command"};
$format = $ref->{"format"};
$table = $ref->{"table"};

( $dbdir, $dbbase ) = parsepath( $dbname );

chdir( $dbdir );

@db = dbopen ( "$dbname", "r+" );
@db = dblookup( @db, "", "images", "", "" );
@dbtable = dblookup( @db, "", "$table", "", "" );

@db = dbnojoin( @db, @dbtable );
$nrecs = dbquery( @db, dbRECORD_COUNT );

if( $opt_v ) {
    	print STDERR "Processing $nrecs rows:\n";
}

$added = 0;
for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {

	$imagefile = dbextfile( @db );
	( $imagename, $time ) = dbgetv( @db, "imagename", "time" );

	$dbtable[3] = dbaddv( @dbtable, "imagename", $imagename, 
		          "time", $time,
		          "imagesize", $size,
		          "format", $format );

	$newfile = trwfname( @dbtable, $filenames );

	$cmd = "$command $imagefile $newfile";

	if( $opt_v ) {
		print STDERR "Running: $cmd\n";
	}

	system( "$cmd" );

	$added++;
}

print "Added $added thumbnails\n";
