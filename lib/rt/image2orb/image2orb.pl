use lib "$ENV{ANTELOPE}/data/perl" ;
use Datascope ;
use orb;

# image2orb.pl
#
# Prototype Library to put images into an Antelope ORB
#
# Kent Lindquist 
# Lindquist Consulting
# 2002

sub image2orb {
	my( $orb, $time, $srcname, $description, $imgdata ) = @_;
	
	if( $srcname =~ m@/@ && $srcname !~ m@/EXP/IMG$@ ) {

		elog_complain( "image2orb: can't handle suffix for $srcname" );
		return -1;

	} elsif( $srcname !~ m@/@ ) {
		
		$srcname .= "/EXP/IMG";
	}

	# version 1.0 image packet:
	$imgpkt = pack( "n", 100 );
	$imgpkt .= sprintf( "%-64s", "$description\0" );
	$imgpkt .= $imgdata;

	orbput( $orb, $srcname,
	     	      $time,
	     	      $imgpkt,
	     	      length( $imgpkt ) ) ;
	
	return 0;
}

1;
