#
#   Copyright (c) 2006 Lindquist Consulting, Inc.
#   All rights reserved. 
#                                                                     
#   Written by Dr. Kent Lindquist, Lindquist Consulting, Inc. 
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#   KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#   WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
#   PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
#   OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR 
#   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#   SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#   This software may be used freely in any way as long as 
#   the copyright statement above is not removed. 
#

use Geo::Ellipsoid;
use POSIX qw(ceil floor);
use lib "$ENV{ANTELOPE}/data/perl" ;

use Datascope;
use codartools;

require "getopts.pl";

sub slurpFile {

	my( $inFile ) = $_[0];

	unless( -e $inFile ) {

		elog_complain( "ERROR: $inFile couldn't be found\n" );
        	return;
	}

	my( $inputRecordSeparator ) = $/;
	undef $/;

	open( F, $inFile );

	my( $file ) = <F>;

	$/ = $inputRecordSeparator;

	$file =~ s/\r/\n/g;

	my( @file ) = split( /\n/, $file );

	return @file;
}

sub extract_filename_pattern_site {

	my( $pathFile ) = @_;

    	my( $fileName ) = basename( $pathFile );

	my( $patt, $site );

	my( $expr ) = "^Rad([sz])(\\w{4})[_\\s]\\d{2}[-_]\\d{2}[-_]" .
		      "\\d{2}[-_\\s]\\d{2}\\d{2}(.rv)?\$";

	if( $fileName =~ m/$expr/ ) {

        	$patt = $1;
        	$site = $2;

	} else {

		elog_complain( "ERROR: Unable to extract site and pattern " .
			"from filename using match expression\n" );
	}

	return( $patt, $site );
}

($dir, $program ) = parsepath( $0 );

elog_init( $program, @ARGV );

if( ! &Getopts( 'v' ) || scalar( @ARGV ) != 2 ) {
	
	elog_die( "Usage: convert_rb2lluv [-v] infile outfile\n" );

} else {
	
	$infile = shift( @ARGV );
	$outfile = shift( @ARGV );
}

if( $opt_v ) {

	$codartools::Verbose = 1;
}

@inblock = &slurpFile( $infile );

if( ! codartools::rbtimestamps_ok( $infile, @inblock ) ) {

	elog_die( "Timestamp mismatch between file name and contents\n" );
}

( $patt, $site ) = extract_filename_pattern_site( $infile );

@outblock = codartools::rb2lluv( $patt, $site, @inblock );

if( ! @outblock ) {

	elog_die( "Failure in conversion of $infile\n" );

} elsif( ! codartools::is_valid_lluv( @outblock ) ) {

	elog_die( "Converted $infile is not valid LLUV\n" );

} elsif( $opt_v ) {
	
	elog_notify( "Converted $infile is validated LLUV data\n" );
}

if( ! open( LLUV, "> $outfile" ) ) {
	
	elog_die( "Failed to open '$outfile' for writing. Bye.\n" );

} else {

	print LLUV join( "\n", @outblock );
	print LLUV "\n";

}

close( LLUV );
