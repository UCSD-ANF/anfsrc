
#
# orbmonimg
# Rewrite of orb-based image display utility
# Kent Lindquist
# Lindquist Consulting
# 2004
#

require "getopts.pl" ;
 
use IO;
use Tk;
use Tk::JPEG;
use Datascope;
use orb;
use image2orb;

sub quit {

	$mw->destroy();
}

sub construct_time_string {
	my( $time ) = @_;

	if( $no_packets ) {

		return $no_packets_message;
	} 

	my( $now ) = str2epoch( "now" );

	my( $latency ) = strtdelta( $now - $time );

	$latency =~ s/^\s*//;
	$latency =~ s/\s*$//;
	$latency =~ s/milliseconds/msec/;

	my( $time_string ) = epoch2str( $time, "%D %T %Z" );

	$time_string .= " ($latency old)";

	return $time_string;
}

sub label_window {
	my( $fieldname, $variable_ref, $field_description ) = @_;

	$framevar = "f_$fieldname";

	$$framevar = $mw->Frame( -background => "beige" )->
			grid( -sticky => "ew" );

	$$framevar->Label( -text => $field_description,
		 	   -background => "khaki",
			   -width => 20, 
			   -anchor => "e",
			   )
		  ->pack( -side => "left" );

	$$framevar->Label( -textvariable => $variable_ref,
		 	   -background => "beige",
			   -anchor => "w" )
		  ->pack( -side => "left", -fill => "x", -expand => "yes" );

	return;
}

sub reschedule {

	$mw->after( $update_interval_ms, \&update_image );
}

sub limit_imagesize {
	my( $photo ) = @_;

	$curwidth = $photo->width;
	$curheight = $photo->height;

	$widthfix = $curheight / $image_display_height;
	$heightfix = $curwidth / $image_display_width;

	$factor = int( $widthfix > $heightfix ? $widthfix : $heightfix );

	if( $factor > 1.0 ) {
		
		$photo->copy( $photo, -subsample => $factor );
	}
}

sub update_image {

	$updated = epoch2str( str2epoch( "now" ), "%D %T %Z" );

	$time_string = construct_time_string( $latest_time );

	($pktid, $srcname, $time, $packet, $nbytes) = 
		orbreap_timeout( $orb, $orbreap_timeout ) ;

	if( ! defined( $pktid ) ) {
		
		reschedule;

		return;

	} else {

		$no_packets = 0;

		$latest_time = $time;

		$time_string = construct_time_string( $latest_time );

		$srcname_string = $srcname;


		$version = unpack( "n", $packet );
		$version_string = "$version";

		if( $version == 100 ) {

			( $version, $description, $blob ) = 
				unpack( "n" .
					"a$image2orb::Description_length" .
					"a*", $packet );

			$format = image2orb::deduce_magic_format( $blob );

		} elsif( $version == 110 ) {

			( $version, $ifragment, $nfragments, 
			  $blob_offset, $format, $description, 
			  $blob ) = 
				unpack( "nnnN" .
					"a$image2orb::Format_length" .
					"a$image2orb::Description_length" .
					"a*", $packet );

			if( $nfragments != 1 ) {
				
				elog_complain( "Multi-packet images not yet " .
					" supported (source $srcname)\n" );
				reschedule;
				return;
			}

		} else {

			elog_complain( "Version $version not yet supported\n" );

			reschedule;

			return;
		}
	} 

	$description_string = $description;
	$format_string = $format;

	# Force loading by file: Tk::JPEG does not appear to 
	# -data capability of Tk::Photo

	$tempfile = "/tmp/orbmonimg_$<_$$.$format";
	$fh = new IO::File;
	$fh->open( ">$tempfile" );
	$fh->write( $blob, length( $blob ) );
	$fh->close;

	$photo = $c->Photo( "latest_image", -file => "$tempfile" );

	limit_imagesize( $photo );

	$c->createImage( 0, 0, -image => "latest_image", -anchor => "nw" );

	reschedule;

	return;
}

elog_init( $0, @ARGV );

if ( ! &Getopts('p:m:r:v') || @ARGV != 1 ) { 

	die ( "Usage: orbmonimg [-v] [-p pffile] [-m match] [-r reject] orbname\n" ) ; 

} else {

	$orbname = pop( @ARGV );
}

if( $opt_p ) {

	$Pfname = $opt_p;

} else {

	$Pfname = "orbmonimg";
}

if( $opt_m ) {
	
	$match = $opt_m;

} else {

	$match = ".*$image2orb::Suffix";
}

if( $opt_r ) {

	$reject = $opt_r;
}

$update_interval_ms = pfget( $Pfname, "update_interval_ms" );
$orbreap_timeout_s = pfget( $Pfname, "orbreap_timeout_s" );
$image_display_width = pfget( $Pfname, "image_display_width" );
$image_display_height = pfget( $Pfname, "image_display_height" );
$no_packets_message = pfget( $Pfname, "no_packets_message" );

$mw = new MainWindow;

$mw->title( "orbmonimg:   $orbname" );
$mw->resizable( 0, 0 );

$updated = epoch2str( str2epoch( "now" ), "%D %T %Z" );
$srcname_string = $no_packets_message;
$time_string = $no_packets_message;
$version_string = $no_packets_message;
$description_string = $no_packets_message;
$format_string = $no_packets_message;
$no_packets = 1;

label_window( "updated", \$updated, "Latest update:" );
label_window( "srcname", \$srcname_string, "Srcname:" );
label_window( "time_string", \$time_string, "Packet Time:" );
label_window( "version_string", \$version_string, "Packet Version:" );
label_window( "description_string", \$description_string, "Packet Description:" );
label_window( "format_string", \$format_string, "Packet Format:" );

$c = $mw->Canvas( -width => $image_display_width,
		  -height => $image_display_height, 
		  -background => "salmon" )->grid;

$quite = $mw->Button( -text => "Quit",
		      -background => "red", 
		      -command => \&quit )
	    ->grid( -sticky => "ew" );

$orb = orbopen( $orbname, "r" );

orbselect( $orb, $match );

if( defined( $reject ) ) {
	
	orbreject( $orb, $reject );
}

$mw->afterIdle( \&update_image );

MainLoop;
