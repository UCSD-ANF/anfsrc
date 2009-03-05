
# weratools.pm
# 
# Kent Lindquist and Mark Otero
# 

package weratools;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	is_wera
	wera2codarlluv
);	

use File::Basename;
use Datascope;
use codartools;
use strict;
use warnings;

BEGIN {
	# Public:
	$weratools::Verbose = 0;
	$weratools::PatternType = "Ideal";
	$weratools::Valid_WERA = "%Manufacturer:.*WERA";
	$weratools::Valid_site = "^\\s*%Site:\\s+\\w{3,4}";
}

sub inform {
        my( $message ) = @_;

        if( $weratools::Verbose ) {

                elog_notify( $message );
        }
}

sub is_wera {

	my( @block ) = @_;

	if( ! @block || scalar( @block ) < 1 ) {
		
		elog_complain( "is_wera: empty data block\n" );

		return 0;
	}

	if( ! grep( /$weratools::Valid_WERA/, @block ) ) {					

		return 0;

	} else {

		return 1;

	}
}

sub wera2codarlluv {

	my( @block ) = @_;

	$codartools::Valid_site = $weratools::Valid_site;
	$codartools::Verbose = $weratools::Verbose;

	splice( @block, -1, 0, "%PatternType: $weratools::PatternType" );

	if( ! codartools::is_valid_lluv( @block ) ) {

		elog_complain( "wera2codarlluv: Failed to convert data block to CODAR LLUV\n" );

		return undef;
	} 

	splice( @block, -2, 1 );

	return @block;
}

1;
