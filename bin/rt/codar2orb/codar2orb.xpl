#
# codar2orb
# 
# Kent Lindquist
# Lindquist Consulting
# 2003-2004
#

use Datascope ;
use orb;
use Time::HiRes;
require "getopts.pl";

$Schema = "Codar0.3";

sub encapsulate_packet { 
	my( $file, $site, $format, $epoch, $orb ) = @_;

	my( $pktsuffix, $version ) = split( /\s+/, $formats{$format} );

	my( $packet ) = pack( "n", $version );

	my( $srcname ) = "$site" . "/" . "$pktsuffix";

	my( $offset ) = length( $packet );

	my( $blocklength ) = (stat($file))[7];

	open( P, "$file" );

	$readlength = read( P, $packet, $blocklength, $offset );

	close( P );

	$rc = orbput( $orbfd, $srcname, $epoch, $packet, length( $packet ) );

	if( $opt_V ) {

		elog_notify( "Packet status:\nRead   $readlength\n" .
			     "    of $blocklength\n" .
			     " length " . length( $packet ) . "\n" .
			     "   for $srcname\n" .
			     "  from $file\n" .
 			     "    rc $rc\n" );
	}

	return;
}

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('i:m:p:s:vV') || $#ARGV != 2 ) {

	die( "Usage: $Program [-v] [-V] [-p pffile] [-s statefile] [-m mintime] trackingdb basedir orbname\n" );

} else {

	$trackingdb = $ARGV[0];
	$basedir = $ARGV[1];
	$orbname = $ARGV[2];
} 

if( $opt_V ) {
	
	$opt_v++;
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
		elog_notify( "Creating tracking-database $trackingdb\n" );
	}

	dbcreate( $trackingdb, $Schema );	

	$newdb = 1;

} else {

	$newdb = 0;
}

@db = dbopen( $trackingdb, "r+" );

@subdirs = @{pfget( $Pfname, "subdirs" )};
%formats = %{pfget( $Pfname, "formats" )};
$prune = pfget( $Pfname, "prune" );

$orbfd = orbopen( $orbname, "w&" );

if( $opt_s ) {

	$statecmd = "-newer $statefile";

	$quit = 0;

	exhume( $statefile, \$quit, 15 );

} else {

	$statecmd = "";
}

if( defined( $prune ) && $prune ne "" ) {

	$prunecmd = "\\( -name $prune -prune \\) -o ";

} else {
	
	$prunecmd = "";
}

@files = ();

# $now = str2epoch( "now" );
# $start = epoch2str( $now, "%Y%m%d%H%M", "" );
# 
# if( $opt_v && $opt_s ) {
# 	
# 	if( -e "$statefile" ) {
# 		
# 		elog_notify( "Previous timestamp " . strtime( (stat("$statefile"))[9] ) . "\n" );
# 
# 	} else {
# 
# 		elog_notify( "No previous timestamp; creating $statefile\n" );
# 	}
# 
# 	elog_notify( "Updating timestamp and starting at " . strtime( $now ) . "\n" );
# }

for( $i = 0; $i <= $#subdirs; $i++ ) {
	
	$now = str2epoch( "now" );

	if( $opt_v ) {

	 	elog_notify( "Starting at " . epoch2str( $now, "%D %T %Z", "" ) . "\n" );
	}

	if( $opt_s ) {

		# Really what makes each subdir unique is the glob expression. 
		# However, the code below uses 'site' and 'format' to form
		# the statefile variable to avoid the hack of bizarre glob 
		# expressions in the key names. In all reasonable usage 
		# scenarios, this should be adequate, plus the verbose log 
		# messages should make the behavior clear:

		$timestamp_variable = "time_" . $subdirs[$i]->{site} . "_" . $subdirs[$i]->{format};

		if( resurrect( "$timestamp_variable", \$$timestamp_variable, TIME_RELIC ) == 0 ) {
			
			$previous = $$timestamp_variable;

			if( $opt_v ) {
				
				elog_notify( "Previous timestamp for " . 
					     "$subdirs[$i]->{site} $subdirs[$i]->{format}: " .
					     epoch2str( $previous, "%D %T %Z", "" ) . "\n" );
			}

		} else {
			
			$previous = 0;

			if( $opt_v ) {
				
				elog_notify( "No previous timestamp for " . 
					     "$subdirs[$i]->{site} $subdirs[$i]->{format}.\n" );
			}
		}
		
		$start = epoch2str( $previous, "%Y%m%d%H%M", "" );

		system( "touch -t $start $statefile" );
	}

	# Order is critical in the 'find' command arguments:

	$cmd = "find $basedir $statecmd \\( $prunecmd -name '$subdirs[$i]->{glob}' \\) -type f -print";

	if( $opt_v ) {

		elog_notify( "Executing: $cmd\n" );
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

			next;
		}
	
		if( $opt_v ) {

			elog_notify "Processing $dfile, timestamped " . epoch2str( $epoch, "%D %T %Z", "" ) . "\n";
		}

		encapsulate_packet( $file, $subdirs[$i]->{site}, 
				    $subdirs[$i]->{format}, $epoch, $orbfd );
		
		@db = dblookup( @db, "", "$subdirs[$i]->{table}", "", "" );

		if( $newdb ) {

			dbaddv( @db, "sta", $subdirs[$i]->{site},
			     	"time", $epoch,
			     	"format", $subdirs[$i]->{format},
			     	"mtime", $mtime,
			     	"dir", $dir,
			     	"dfile", $dfile );
		} else {

			$rec = dbfind( @db, 
				"sta == \"$subdirs[$i]->{site}\" && time == $epoch && format == \"$subdirs[$i]->{format}\"", -1 );

			if( $rec < 0 ) {

				dbaddv( @db, "sta", $subdirs[$i]->{site},
			     		"time", $epoch,
			     		"format", $subdirs[$i]->{format},
			     		"mtime", $mtime,
			     		"dir", $dir,
			     		"dfile", $dfile );
			} else {

				@dbt = @db;
				$dbt[3] = $rec;
				dbputv( @dbt, "mtime", $mtime );

			}
		}

		if( $opt_i ) {

			Time::HiRes::sleep( $opt_i );
		}
	}

	close( F );

	if( $opt_s ) {

		if( $opt_v ) {
				
			elog_notify( "Updating timestamp for " . 
				     "$subdirs[$i]->{site} $subdirs[$i]->{format} to: " .
				     epoch2str( $now, "%D %T %Z", "" ) . "\n" );
		}

		$$timestamp_variable = $now;

		bury();
	}
}
