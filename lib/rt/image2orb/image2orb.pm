# image2orb.pm
#
# Perl Module to put images into an Antelope ORB
#
# Kent Lindquist 
# Lindquist Consulting
# 2002-2004

package image2orb;

require Exporter;
@ISA = ('Exporter');

@EXPORT = qw( image2orb );
@EXPORT_OK = qw( $Suffix $Current_Version $ORB_MAX_DATA_BYTES
		 $Description_length $Format_length );

use Datascope ;
use orb;

$Suffix = "/EXP/IMG";
$Current_Version = 110;
$ORB_MAX_DATA_BYTES = 1000000;
$Description_length = 64;
$Format_length = 25;

sub deduce_magic_format {
	my( $imgdata ) = @_;

        if( substr( $imgdata, 0, 2 ) eq "\377\330" ) {

                return "jpeg";

        } elsif( substr( $imgdata, 0, 3 ) eq "GIF" ) {

                return "gif";

        } elsif( substr( $imgdata, 0, 2 ) eq "\115\115" ) {

                return "tiff";

        } elsif( substr( $imgdata, 0, 2 ) eq "\111\111" ) {

                return "tiff";

        } elsif( substr( $imgdata, 0, 8 ) eq "\211PNG\r\n\032\n" ) {

                return "png";

        } elsif( substr( $imgdata, 0, 2 ) eq "P4" ) {

                return "pbm";

        } elsif( substr( $imgdata, 0, 2 ) eq "P5" ) {

                return "pgm";

        } elsif( substr( $imgdata, 0, 2 ) eq "P6" ) {

                return "ppm";

        } else {

                return "";
        }
}

sub image2orb {
	my( $orb, $time, $srcname, $description, $imgdata, $format ) = @_;
	
	if( $srcname =~ m@/@ && $srcname !~ m@$Suffix$@ ) {

		elog_complain( "image2orb: can't handle suffix for $srcname" );
		return -1;

	} elsif( $srcname !~ m@/@ ) {
		
		$srcname .= "$Suffix";
	}

	if( ! defined( $format ) ) {

		$format = deduce_magic_format( $imgdata );
	}

	$description = substr( $description, 0, $Description_length - 1 );
	$format = substr( $format, 0, $Format_length - 1 );

	# header: version ifragment nfragments offset format description image

	$header_size = 2 + 2 + 2 + 4 + $Format_length + $Description_length;
	$max_chunk_size = $ORB_MAX_DATA_BYTES - $header_size;

	$nfragments = int( length( $imgdata ) / $max_chunk_size ) + 1;

	$offset = 0;

	for( $ifragment = 1; $ifragment <= $nfragments; $ifragment++ ) {

		$imgpkt = pack( "n", $Current_Version );

		$imgpkt .= pack( "n", $ifragment );
		$imgpkt .= pack( "n", $nfragments );

		$imgpkt .= pack( "N", $offset );

		$imgpkt .= sprintf( "%-$Format_length\s", "$format\0" );
		$imgpkt .= sprintf( "%-$Description_length\s", "$description\0" );

		$chunk = substr( $imgdata, $offset, $max_chunk_size );

		$imgpkt .= $chunk;

		orbput( $orb, $srcname,
	     	      	$time,
	     	      	$imgpkt,
	     	      	length( $imgpkt ) ) ;

		$offset += length( $chunk );
	}
	
	return 0;
}

1;
