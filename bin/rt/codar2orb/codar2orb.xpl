use Datascope ;
use orb;
use Net::FTP;
require "getopts.pl";

chomp( $Program = `basename $0` );
elog_init( $0, @ARGV );

if( ! &Getopts('p:d') || $#ARGV != 0 ) {
	die( "Usage: $Program [-p pffile] [-d] orbname\n" );
} else {
	$orbname = $ARGV[0];
} 

if( $opt_p ) { 
	$Pfname = $opt_p;
} else { 
	$Pfname = $Program;
}

$orbfd = orbopen( $orbname, "w&" );

$latest = pfget( "$Pfname", "latest_time" );
$user = pfget( "$Pfname", "user" );
$password = pfget( "$Pfname", "password" );
$location = pfget( "$Pfname", "location" );
$ftpdir = pfget( "$Pfname", "ftpdir" );
$localdir = pfget( "$Pfname", "localdir" );
$srcname_base = pfget( "$Pfname", "srcname_base" );
$pid = pfget( "$Pfname", "pid" );

$pscount = `/usr/bin/ps -p $pid | grep -v PID | wc -l`;
chomp( $pscount );
if( $pscount >= 1 && $pid != 0 ) {
	die( "$Program appears to be already running. Bye.\n" );
}

$pffilename = `pfecho -w $Pfname | tail -1`;
chomp( $pffilename );
$pffilename = `abspath $pffilename`;
chomp( $pffilename );

opendir( D, "$localdir" ) || die( "Couldn't open $localdir\n" );
@list = readdir( D );
closedir( D );

@list = grep( /^Tot.*/, @list );

grep( ( $_ = $localdir . "/" . $_ ), @list );
grep( chomp( $_ = `abspath $_` ), @list );

$latest_time = $epoch = $latest;

foreach $file ( @list ) {

	chomp( $file );
	$convert = $file;
	$convert =~ s@^.*/@@;

	$convert =~ /(.*)_(\d\d)-(\d\d)-(\d\d)_(\d\d)(\d\d)/;
	$convert = "$3/$4/$2 $5:$6"; 
	$name = "$1";

	undef $epoch;
	eval( "\$epoch = str2epoch( \"$convert\" );" );
	if( ! defined( $epoch ) ) {
		print STDERR "Skipping $file: str2epoch problem\n";
		next;
	}

	next if( $epoch <= $latest );
	
	print "Processing file $file timestamped ", strtime( $epoch ), "\n";

	unless( $opt_l ) {
		$ftp->get( "$file" );
	}

	open( F, "$file" );
	@block = <F>;
	close( F );

	$packet = pack( "n", 100 ) . join( "", @block );
	$srcname = "$srcname_base" . "/EXP/CDRV";
	orbput( $orbfd, $srcname, $epoch, $packet, length( $packet ) );

	$latest_time = $epoch > $latest_time ? $epoch : $latest_time;

	if( (! $opt_l ) || $opt_d ) {
		unlink( "$file" );
	}

	update_pffile( $$ );
}

update_pffile( 0 );
