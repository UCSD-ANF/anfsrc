#
# codar2orb
# 
# Kent Lindquist
# Lindquist Consulting
# 2003-2004
#

use Datascope ;
use orb;
require "getopts.pl";

$Schema = "Codar0.3";

sub encapsulate_packet { 
	my( $file, $site, $pktsuffix, $epoch, $orb ) = @_;

	open( P, "$file" );
	@block = <P>;
	close( P );

	my( $packet ) = pack( "n", 100 ) . join( "", @block );

	my( $srcname ) = "$site" . "/" . "$pktsuffix";

	orbput( $orbfd, $srcname, $epoch, $packet, length( $packet ) );
}

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('m:p:s:v') || $#ARGV != 2 ) {

	die( "Usage: $Program [-v] [-p pffile] [-s statefile] [-m mintime] trackingdb basedir orbname\n" );

} else {

	$trackingdb = $ARGV[0];
	$basedir = $ARGV[1];
	$orbname = $ARGV[2];
} 

if( $opt_p ) { 

	$Pfname = $opt_p;

} else { 

	$Pfname = $Program;
}

if( $opt_m ) {

	$mintime = str2epoch( "$opt_m" );
}

if( $opt_s ) {

	$statefile = $opt_s;
} 

if( ! -e "$trackingdb" ) {

	if( $opt_v ) {
		print( "Creating tracking-database $trackingdb\n" );
	}

	dbcreate( $trackingdb, $Schema );	

	$newdb = 1;

} else {

	$newdb = 0;
}

@db = dbopen( $trackingdb, "r+" );

@subdirs = @{pfget( $Pfname, "subdirs" )};

$orbfd = orbopen( $orbname, "w&" );

if( $opt_s && -e "$statefile" ) {

	$statecmd = "-newer $statefile";

} else {

	$statecmd = "";
}

@files = ();

$now = str2epoch( "now" );
$start = epoch2str( $now, "%Y%m%d%H%M", "" );

if( $opt_v && $opt_s ) {
	
	if( -e "$statefile" ) {
		
		print( "Previous timestamp ", strtime( (stat("$statefile"))[9] ), "\n" );

	} else {

		print( "No previous timestamp; creating $statefile\n" );
	}

	print( "Updating timestamp and starting at ", strtime( $now ), "\n" );
}

for( $i = 0; $i <= $#subdirs; $i++ ) {
	
	$cmd = "find $basedir $statecmd -name '$subdirs[$i]->{glob}' -print";

	if( $opt_v ) {

		print( "Executing: $cmd\n" );
	}	


	open( F, "$cmd |" );

	foreach $file ( <F> ) {

		chomp( $file );

		$file = abspath( $file );

		$mtime = (stat("$file"))[9];
		($dir, $dfile, $suffix ) = parsepath( $file );

		if( "$suffix" ) { $dfile .= ".$suffix" }
	
		eval( "\@mdyhms = $subdirs[$i]->{mdyhms};" );

		$epoch = str2epoch( sprintf( "%s/%s/%s %s:%s:%s", @mdyhms ) );

		if( $opt_m && $epoch < $mintime ) {

			#print "Skipping $dfile, timestamped ", strtime( $epoch ), "\n";
			next;
		}
	
		if( $opt_v ) {

			print "Processing $dfile, timestamped ", strtime( $epoch ), "\n";
		}

		encapsulate_packet( $file, $subdirs[$i]->{site}, 
				    $subdirs[$i]->{pktsuffix}, $epoch, $orbfd );
		
		@db = dblookup( @db, "", "$subdirs[$i]->{table}", "", "" );

		if( $newdb ) {

			dbaddv( @db, "sta", $subdirs[$i]->{site},
			     	"time", $epoch,
			     	"pktsuffix", $subdirs[$i]->{pktsuffix},
			     	"mtime", $mtime,
			     	"dir", $dir,
			     	"dfile", $dfile );
		} else {

			$rec = dbfind( @db, 
				"sta == \"$subdirs[$i]->{site}\" && time == $epoch && pktsuffix == \"$subdirs[$i]->{pktsuffix}\"", -1 );

			if( $rec < 0 ) {

				dbaddv( @db, "sta", $subdirs[$i]->{site},
			     		"time", $epoch,
			     		"pktsuffix", $subdirs[$i]->{pktsuffix},
			     		"mtime", $mtime,
			     		"dir", $dir,
			     		"dfile", $dfile );
			} else {

				@dbt = @db;
				$dbt[3] = $rec;
				dbputv( @dbt, "mtime", $mtime );

			}


		}
	}

	close( F );

}

if( $opt_s ) {

	system( "touch -t $start $statefile" );
}

