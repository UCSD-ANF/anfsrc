# Prototype acquisition script for images
# Kent Lindquist 
# Lindquist Consulting
# May, 2002

use Datascope ;
use orb;
require "getopts.pl";
require "image2orb.pl";

if( ! &Getopts('t:d:v') || @ARGV != 3 ) {

	die( "Usage: image2orb [-v] [-t timestamp] [-d description] orbname srcname filename\n" );

} else {

	$orbname = $ARGV[0];
	$image_srcname = $ARGV[1];
	$image_filename = $ARGV[2];

	if( $opt_t ) {
		$time = str2epoch( $opt_t );
	} else {
		$time = str2epoch( "now" );
	}

	if( $opt_d ) {
		$description = $opt_d;
	} else {
		$description = $image_filename;
		$description =~ s".*/"";
	}
}

if( ! -e "$image_filename" ) {

	die( "image2orb: couldn't find $image_filename\n" ); 

} else {

	open( I, "$image_filename" );
	$imagedata = join( "", <I> );
	close( I );
}

$orb = orbopen( $orbname, "w" );
if( $orb < 0 ) {
	die( "image2orb: couldn't open orb $orbname\n" );
}

if( $opt_v ) {
	printf STDERR "Putting $image_filename on $orbname...";
}

$rc = image2orb( $orb, $time, $image_srcname, $description, $imagedata );
	
if( $opt_v ) {
	if( $rc < 0 ) {
		printf STDERR "failed\n";
	} else {
		printf STDERR "succeeded\n";
	} 
}

orbclose( $orb );
