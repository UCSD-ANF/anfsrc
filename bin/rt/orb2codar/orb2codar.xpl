#
# orb2codar
# 
# Kent Lindquist
# Lindquist Consulting
# 2004
#

use Datascope ;
use orb;
require "getopts.pl";

$Schema = "Codar0.3";

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('d:p:a:ov') || $#ARGV != 1 ) {

	die( "Usage: $Program [-v] [-o] [-p pffile] [-a after] [-d dbname] orbname builddir\n" );

} else {

	$orbname = $ARGV[0];
	$builddir = $ARGV[1];
} 

if( $opt_d ) {

	$trackingdb = $opt_d;

	if( ! -e "$trackingdb" ) {

		if( $opt_v ) {
			elog_notify( "Creating tracking-database $trackingdb\n" );
		}

		dbcreate( $trackingdb, $Schema );	
	}

	@db = dbopen( $trackingdb, "r+" );
}

if( $opt_p ) { 

	$Pfname = $opt_p;

} else { 

	$Pfname = $Program;
}


$orbfd = orbopen( $orbname, "r&" );

if( $orbfd < 0 ) {
	die( "Failed to open $orbname for reading!\n" );
}

if( $opt_a eq "oldest" ) {

	orbseek( $orbfd, "ORBOLDEST" );

} elsif( $opt_a ) {
	
	orbafter( $orbfd, str2epoch( $opt_a ) );
}

@hierarchies = @{pfget( $Pfname, "hierarchies" )};
%format = %{pfget( $Pfname, "formats" )};

$match = "(";

for( $i = 0; $i <= $#hierarchies; $i++ ) {

	$match .= "$hierarchies[$i]->{srcname}|";

	$hashes{$hierarchies[$i]->{srcname}} = $hierarchies[$i];
}

substr( $match, -1, 1, ")" );

if( $opt_v ) {

	elog_notify( "orb2codar: using match expression \"$match\"\n" );
}

orbselect( $orbfd, $match );

for( ;; ) {

	($pktid, $srcname, $time, $packet, $nbytes) = orbreap( $orbfd );

	next if( $opt_a && $opt_a ne "oldest" && $time < str2epoch( "$opt_a" ) );

	if( $opt_v  ) {

		elog_notify( "received $srcname timestamped " . strtime( $time ) . "\n" );
	}

	$relpath = epoch2str( $time, $hashes{$srcname}->{dfiles_pattern} );

	$relpath = concatpaths( $builddir, $relpath );

	( $subdir, $dfile, $suffix ) = parsepath( $relpath );

	if( "$suffix" ) { $dfile .= ".$suffix" }

	if( -e "$relpath" && ! $opt_o ) {

		if( $opt_v ) {
			
			elog_complain( "Won't overwrite $relpath; file exists\n" );
		}

		next;
	}

	system( "mkdir -p $subdir" );

	( $version, $block ) = unpack( "na*", $packet );

	# it's possible the path is already absolute, though not guaranteed. 
	# treat as though it were relative:

	$abspath = abspath( $relpath );

	( $dir, $dfile, $suffix ) = parsepath( $abspath );

	if( "$suffix" ) { $dfile .= ".$suffix" }

	if( $opt_v ) {

		elog_notify( "Creating $abspath\n" );
	}

	open( F, ">$relpath" );
	print F $block;
	close( F );

	if( $opt_d ) {

		$mtime = (stat("$relpath"))[9];

		@db = dblookup( @db, "", "$hashes{$srcname}->{table}", "", "" );

		( $sta, $pktsuffix ) = ( $srcname =~ m@^([^/]*)/(.*)@ );

		$format = $formats{$pktsuffix};

		$rec = dbfind( @db, "sta == \"$sta\" && " .
				    "time == $time && format == \"$format\"", -1 );

		if( $rec < 0 ) {

			dbaddv( @db, "sta", $sta,
				"time", $time,
				"format", $format,
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
