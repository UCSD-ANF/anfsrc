use Datascope ;
use orb;

chomp( $Program = `basename $0` );

if( $#ARGV < 1 ) {
	die( "Usage: $Program orbname dbname [after]\n" );
} else {
	$orbname = $ARGV[0];
	$dbname = $ARGV[1];
	if( $#ARGV >= 2 ) {
		eval( "\$after = str2epoch( \"$ARGV[2]\" );" );
		if( ! defined( $after ) ) {
			die( "Failed to convert \"$ARGV[2]\". Bye.\n" ); 
		}
	}
} 

$orbfd = orbopen( $orbname, "r&" );

orbselect( $orbfd, ".*/EXP/CDRV" );

if( defined( $after ) ) {

	orbafter( $orbfd, $after );
}

for( ;; ) {
	($pktid, $srcname, $time, $packet, $nbytes) = orbreap($orbfd) ;

	( $version, $block ) = unpack( "na*", $packet );

	$tempfile = "/tmp/orbcodar2db_tmp";
	open( F, "> $tempfile" );
	print F $block;
	close( F );
	
	system( "codarV_reformat $tempfile $dbname" );

	unlink( $tempfile );
}
