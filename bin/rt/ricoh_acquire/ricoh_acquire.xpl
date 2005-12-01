# Prototype acquisition script for Ricoh camera images
# Kent Lindquist 
# Lindquist Consulting
# May, 2002

use Datascope ;
use orb;
use image2orb;
require "getopts.pl";
require "ricoh_tools.pl";

if( ! &Getopts('tsvVp:') || @ARGV != 1 ) {

	die( "Usage: ricoh_acquire [-t] [-s] [-v] [-V] [-p pffile] orbname\n" );

} else {

	$orbname = $ARGV[0];

	if( $opt_V ) { $opt_v++ };

	if( $opt_p ) {

		$Pf = $opt_p;

	} else {

		$Pf = "ricoh_acquire";
	}
}

$Camera_ip = pfget( $Pf, "camera_ip" );
$Camera_TZ = pfget( $Pf, "camera_TZ" );
$image_srcname = pfget( $Pf, "image_srcname" );
$description = pfget( $Pf, "image_description" );
$acquire_interval_sec = pfget( $Pf, "acquire_interval_sec" );

$Camera_address = "http://$Camera_ip";

$browser = new LWP::UserAgent;
$browser->agent( "TestScript/0.1 " . $browser->agent );

$orb = orbopen( $orbname, "w" );
if( $orb < 0 ) {
	die( "ricoh_acquire: couldn't open orb $orbname\n" );
}

for( ;; ) {

	if( $opt_v ) {
		printf STDERR "Attempting to acquire packet:...";
	}

	( $jpgdata, $base_filename, $datestr ) =
	 	acquire_i700_image( $browser, $Camera_address );

	if( ! defined( $jpgdata ) ) {
		elog_complain( "ricoh_acquire: image acquisition failed.\n" );
		sleep( 1 );
		next;
	}

	if( $opt_t ) {

		$time = str2epoch( "now" );

	} else {

		$time = str2epoch( "$datestr $Camera_TZ" );
	}

	delete_i700_images( $browser, $Camera_address );

	$rc = image2orb( $orb, $time, $image_srcname, 
			 $description, $jpgdata );
	
	if( $opt_v ) {
		if( $rc < 0 ) {
			printf STDERR "failed\n";
		} else {
			printf STDERR "succeeded\n";
		} 
	}

	if( $opt_v ) {
		printf STDERR "Sleeping $acquire_interval_sec seconds; ";
	}

	sleep( $acquire_interval_sec );
}

orbclose( $orb );
