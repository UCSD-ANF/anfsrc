# Prototype acquisition script for web images
# and Axis 2400 video server images
# Kent Lindquist 
# Lindquist Consulting
# June, 2002

use Datascope;
use orb;
use image2orb;

require "getopts.pl" ;
 
if ( ! &Getopts('vd:') || @ARGV < 3 || @ARGV > 4 ) { 

    die ( "Usage: $0 [-v] [-d description] orbname srcname web_address [sleeptime_sec]\n" ) ; 

} else {
	$orbname = $ARGV[0];
	$srcname = $ARGV[1];
	$web_address = $ARGV[2];
	if( @ARGV == 4 ) {
		$repeat = 1;
		$sleeptime_sec = $ARGV[3];
	} else {
		$repeat = 0;
	}
}


if( ! -x datafile( "PATH", "wget" ) ) {

	die( "webimage_acquire needs wget on its path; not found. Bye.\n" );
}

$sourceurl = $web_address;
$sourceurl =~ s@^http://@@;
$sourceurl =~ s@/.*$@@;

if( $opt_d ) {
	$description = $opt_d;
} else {
	$description = "Image from $sourceurl";
}

$orb = orbopen( $orbname, "w&" );

if( $orb < 0 ) {
	die( "Failed to open orbserver '$orbname'!\n" );
}

while( 1 ) {
	$now = strtime( str2epoch( "now" ) );

	if( $opt_v ) {
		printf STDERR "Attempting to acquire a packet at $now:...";
	}
	
	++$uniq;

	$tmpfile = "/tmp/webimage_acquire_$<_$$_$uniq";

	$output = `wget -O $tmpfile '$web_address' 2>&1`;

	if( grep( /saved/, $output ) ) {

		$time = str2epoch( "now" );

		$size = (stat($tmpfile))[7];

		if( $size > 0 ) {

			open( D, "$tmpfile" );
			read( D, $datablock, $size );
			close( D );

			image2orb( $orb, $time, $srcname,
				   $description, $datablock );

			if( $opt_v ) {
				printf STDERR "succeeded\n";
			}

		} else {

			printf STDERR "failed: received zero-length data block\n";
		}

		undef( $datablock ); 

		unlink( $tmpfile );

	} else {

		printf STDERR "failed: " . $output . "\n";
	}

	if( ! $repeat ) {
		
		last;

	} else {

		if( $opt_v ) {
			printf STDERR "Sleeping $sleeptime_sec; ";
		}
	
		sleep( $sleeptime_sec );

	}
}
