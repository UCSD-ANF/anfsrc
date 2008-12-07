
# weratools.pm
# 
# Kent Lindquist and Mark Otero
# 

package weratools;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	is_wera
);	

use File::Basename;
use Datascope;

BEGIN {
	# Public:
	$Verbose = 0;
	$Valid_WERA = "%Manufacturer:.*WERA";
}

sub inform {
        my( $message ) = @_;

        if( $Verbose ) {

                elog_notify( $message );
        }
}

sub is_wera {

	my( @block ) = @_;

	if( ! @block || scalar( @block ) < 1 ) {
		
		elog_complain( "is_wera: empty data block\n" );

		return 0;
	}

	if( ! grep( /$Valid_WERA/, @block ) ) {					

		return 0;

	} else {

		return 1;

	}
}

1;
