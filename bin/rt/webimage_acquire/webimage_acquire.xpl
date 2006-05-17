# Prototype acquisition script for web images
# and Axis 2400 video server images
# Kent Lindquist 
# Lindquist Consulting
# June, 2002

use Datascope;
use orb;
use LWP;
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
	
	$ua = new LWP::UserAgent;
	$ua->agent( "webimage_acquire/0.1 " . $ua->agent );

	$req = new HTTP::Request( GET=>"$web_address" );

	$res = $ua->request( $req );

	if( $res->is_success ) {

		$time = str2epoch( "now" );

		my( $datablock ) = $res->content;

		if( length( $datablock ) > 0 ) {

			image2orb( $orb, $time, $srcname,
				   $description, $datablock );

			if( $opt_v ) {
				printf STDERR "succeeded\n";
			}

		} else {

			printf STDERR "failed: received zero-length data block\n";
		}

	} else {

		printf STDERR "failed: " . $res->status_line . "\n";
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
