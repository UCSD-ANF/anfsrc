use LWP;
use HTTP::Request::Common;

# ricoh_tools.pl
# 
# Prototype Library to acquire images from Ricoh i700
# based on initial work by Hans-Werner Braun
#
# Kent Lindquist
# Lindquist Consulting
# 2002

sub save_http_response {
	my( $cmd, $pkt ) = @_;

	$rspcount++;

	open( P, ">Response_$rspcount" );
	print P "$cmd\n\n";
	print P $pkt;
	close( P );
}

sub test_http_response {
	my( $res ) = @_;
	
	if( ! $res->is_success ) {

		elog_complain( $res->error_as_HTML() );
		return undef;

	} elsif( grep( m@Internal Server Error@, $res->content ) ) {

		elog_complain( "Failed:\n\n" . $res->content . "\n\n" );
		return undef;

	} else {

		if( $opt_V ) { printf STDERR "succeeded.\n\n"; }
		return $res;
	}
}

sub http_get {
	my( $browser, $cmd ) = @_;
	
	if( $opt_V ) { printf STDERR "http_get:\n\t$cmd\n"; }

	my( $req ) = GET( "$cmd" );

	my( $res ) = $browser->request( $req );

	if( $opt_s ) { save_http_response( $cmd, $res->content ); }

	$res = test_http_response( $res );
	
	return $res;
}

sub http_post {
	my( $browser, $cmd, $hashref ) = @_;

	if( $opt_V ) { printf STDERR "http_post:\n\t$cmd\n"; }

	my( $req ) = POST( "$cmd", $hashref );

	$res = $browser->request( $req );

	if( $opt_s ) { save_http_response( $cmd, $res->content ); }

	$res = test_http_response( $res );
}

sub acquire_i700_image {
	my( $browser, $a ) = @_;

	$res = http_get( $browser, "$a/http_capture_stl.cgi?start=+CAPTURE+" );
	if( ! defined( $res ) ) {
		return undef;
	}

	$res = http_get( $browser, "$a/http_monitor_workbtn.cgi" );
	if( ! defined( $res ) ) {
		return undef;
	}

	$res = http_get( $browser, "$a/http_image_workdata.cgi" );
	if( ! defined( $res ) ) {
		return undef;
	}

	grep( m@SRC="/RAM/([^"]*)"@ && ($filename = $1), $res->content );
	$base_filename = $filename;
	$base_filename =~ s/\?.*$//;
	
	grep( m@<DIV CLASS="JNB">([\d\.: ]+)</DIV>@ && ($fileprop_datestr = $1),
		 $res->content );
	$fileprop_datestr =~ s/\./-/g;

	$res = http_get( $browser, "$a/ATA1/DCIM/100RICOH/$filename" );
	if( ! defined( $res ) ) {
		return undef;
	}

	my( $image ) = $res->content;
	
	grep( m@(\d\d\d\d:\d\d:\d\d \d\d:\d\d:\d\d)@ && ($jpeg_timestamp = $1), 
		$res->content );
	$jpeg_timestamp =~ s/(\d\d\d\d):(\d\d):(\d\d)/$1-$2-$3/;

	return ( $image, $base_filename, $jpeg_timestamp );
}

sub delete_i700_images {
	my( $browser, $a ) = @_;

	$res = http_get( $browser, "$a/http_ricoh_index.cgi" );
	if( ! defined( $res ) ) {
		elog_complain( "delete_i700_images: image deletion failed\n" );
		return;
	}

	grep( m@http_headmenu.cgi\?id=([^"]*)"@ && ($confirm1 = $1), 
	      $res->content );

	$res = http_get( $browser, "$a/http_job_normal.cgi?2+id=$confirm1" );
	if( ! defined( $res ) ) {
		elog_complain( "delete_i700_images: image deletion failed\n" );
		return;
	}

	$res = http_get( $browser, "$a/http_AllDelConfirm.cgi?=ALL+DELETE" );
	if( ! defined( $res ) ) {
		elog_complain( "delete_i700_images: image deletion failed\n" );
		return;
	}

	grep( m@http_AllDelSubmit.cgi\?id=([^"]*)"@ && ($confirm = $1), 
	      $res->content );

	$res = http_post( $browser, 
			  "$a/http_AllDelSubmit.cgi?id=$confirm", 
			  [media => 3, folder => "100RICOH"] );
	if( ! defined( $res ) ) {
		elog_complain( "delete_i700_images: image deletion failed\n" );
		return;
	}
}

1;
