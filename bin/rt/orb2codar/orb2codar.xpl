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

$Schema = "Codar0.4";

chomp( $Program = `basename $0` );

elog_init( $0, @ARGV );

if( ! &Getopts('m:r:d:p:a:ov') || $#ARGV != 1 ) {

	die( "Usage: $Program [-v] [-o] [-m match] [-r reject] [-p pffile] [-a after] [-d dbname] orbname builddir\n" );

} else {

	$orbname = $ARGV[0];
	$builddir = $ARGV[1];
} 

if( $opt_v ) {
	elog_notify( "orb2codar starting at " . 
		     strtime( str2epoch( "now" ) ) . "\n" );
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

	if( $opt_v ) {
		
		elog_notify( "Repositioning orb pointer to oldest packet\n" );
	}

	orbseek( $orbfd, "ORBOLDEST" );

} elsif( $opt_a ) {
	
	if( $opt_v ) {
		
		elog_notify( "Repositioning orb pointer to time $opt_a\n" );
	}

	orbafter( $orbfd, str2epoch( $opt_a ) );
}

%formats = %{pfget( $Pfname, "formats" )};

if( $opt_m ) {
	
	$match = $opt_m;

} else {

	$match = ".*/(";

	foreach $format ( keys %formats ) {

		$match .= "$format|";
	}

	substr( $match, -1, 1, ")" );
}

if( $opt_v ) {

	elog_notify( "orb2codar: using match expression \"$match\"\n" );
}

orbselect( $orbfd, $match );

if( $opt_r ) {

	if( $opt_v ) {

		elog_notify( "orb2codar: using reject expression \"$opt_r\"\n" );
	}

	orbreject( $orbfd, $opt_r );
}

for( ;; ) {

	($pktid, $srcname, $time, $packet, $nbytes) = orbreap( $orbfd );

	next if( $opt_a && $opt_a ne "oldest" && $time < str2epoch( "$opt_a" ) );

	if( $opt_v  ) {

		elog_notify( "received $srcname timestamped " . strtime( $time ) . "\n" );
	}

	( $sta, $pktsuffix ) = ( $srcname =~ m@^([^/]*)/(.*)@ );

	$format = $formats{$pktsuffix}->{format};

	( $version, $block ) = unpack( "na*", $packet );

	if( $version == 100 ) {

		$beampattern = "-";

	} elsif( $version == 110 ) {

		( $beampattern, $block ) = unpack( "aa*", $block );
			
	} else {
		
		elog_complain( "Unsupported version number $version for $srcname, " . 
				strtime( $time ) . " in orb2codar\n" );
		next;
	}

	$dfiles_pattern = $formats{$pktsuffix}->{dfiles_pattern};
	$dfiles_pattern =~ s/%{sta}/$sta/g;
	$dfiles_pattern =~ s/%{format}/$format/g;
	$dfiles_pattern =~ s/%{beampattern}/$beampattern/g;

	$relpath = epoch2str( $time, $dfiles_pattern );

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

		$table = $formats{$pktsuffix}->{table};

		@db = dblookup( @db, "", "$table", "", "" );

		$rec = dbfind( @db, "sta == \"$sta\" && " .
				    "time == $time && format == \"$format\"", -1 );

		if( $rec < 0 ) {

			dbaddv( @db, "sta", $sta,
				"time", $time,
				"format", $format,
				"beampattern", $beampattern,
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
