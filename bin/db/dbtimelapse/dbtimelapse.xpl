#
# dbtimelapse
# 
# Kent Lindquist 
# Lindquist Consulting
# 2004
#

require "getopts.pl" ;
use Datascope ;

sub make_movie {
	my( $movie ) = @_;

	if( $opt_v ) {

		print "Making movie $movie:\n";
	}

	$converter = datafile( "PATH", $movies{$movie}->{converter} );

	if( ! defined( $converter ) || ! -x $converter ) {

		print STDERR "Can't find $movies{$movie}->{converter} on path; Giving up.\n";
	
		return;
	}

	@db = dblookup( @db, "", "$movies{$movie}->{table}", "", "" );

	@db = dbsubset( @db, "$movies{$movie}->{expression}" );

	@db = dbsort( @db, "time" );

	$nrecs = dbquery( @db, dbRECORD_COUNT );

	if( $nrecs <= 3 ) {

		elog_complain( "...not enough records for $movie in $dbname, skipping\n" );

		next;
	}

	@files = ();
	for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {

		next if( $db[3] % $movies{$movie}->{decimation} != 0 );
		
		push( @files, dbextfile( @db ) );
	}

	$path = "$movies{$movie}->{path}";
	$options = "$movies{$movie}->{options}";

	if( $movies{$movie}->{converter} eq "convert" ) {

		if( $opt_v ) {

			$verbose = "-verbose";

		} else {

			$verbose = "";
		}
			
		if( defined( $startlabel ) && $startlabel ne "" ) {

			$startimage = "$startlabel " . shift( @files );

		} else {

			$startimage = "";
		}

		if( defined( $endlabel ) && $endlabel ne "" ) {

			$endimage = "$endlabel " . pop( @files );

		} else {

			$endimage = "";
		}

		$images = join( " ", @files );

		$cmd = "convert $verbose $options $startimage $delay $images $endimage $path";

		system( "$cmd" );

	} elsif( $movies{$movie}->{converter} eq "transcode" ) {

		if( $opt_v ) {

			$verbose = "-q 1";

		} else {

			$verbose = "-q 0";
		}
			
		$tmplist = "/tmp/imlist_$<_$$";

		open( L, ">$tmplist" );

		foreach $file ( @files ) {

			print L "$file\n";
		}

		close( L );	

		$cmd = "transcode -i $tmplist -x imlist,null $verbose $options -o $path";

		system( $cmd );

		unlink( $tmplist );

	} else {

		print STDERR "Undefined converter $movies{$movie}->{converter}; Giving up.\n";

		return;
	}

	return;
}

$Pf = "dbtimelapse";

if ( ! &Getopts('v') || @ARGV < 1 || @ARGV > 2 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "Usage: $pgm [-v] database\n" ) ; 

} else {

	$dbname = shift( @ARGV );
}

if( @ARGV ) {

	$requested_movie = pop( @ARGV );
} 

$startlabel = pfget( $Pf, "startlabel" );
$endlabel = pfget( $Pf, "endlabel" );
$delay = pfget( $Pf, "delay" );

%movies = %{pfget( $Pf, "movies" )};

@db = dbopen ( "$dbname", "r+" );

if( defined( $requested_movie ) ) {

	if( ! defined( $movies{$requested_movie}->{path} ) ) {

		elog_die( "Couldn't find path for $requested_movie in $Pf\n" );
	}

	make_movie( $requested_movie );

} else {

	foreach $movie ( keys %movies ) {

		make_movie( $movie );
	}
}
