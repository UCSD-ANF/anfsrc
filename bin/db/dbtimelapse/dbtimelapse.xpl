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
	my( $ref ) = @_;
	my( %moviepf ) = %$ref;

	if( $opt_v ) {

		print "Making movie '$moviepf{name}':\n";
	}

	my( $converter ) = datafile( "PATH", $moviepf{converter} );

	if( ! defined( $converter ) || ! -x $converter ) {

		print STDERR "Can't find $moviepf{converter} on path; Giving up.\n";
	
		return;
	}

	my( @db ) = dblookup( @db, "", "$moviepf{table}", "", "" );

	my( $expression );

	if( defined( $moviepf{expression} ) && $moviepf{expression} ne "" ) {
		
		$expression = $moviepf{expression};

	} else {

		$expression = "imagename == \"$moviepf{imagename}\" && time >= \"$moviepf{start}\"";

		if( defined( $moviepf{end} ) && $moviepf{end} ne "" ) {
			
			$expression .= " && time <= \"$moviepf{end}\"";
		}
	}

	@db = dbsubset( @db, "$expression" );

	@db = dbsort( @db, "time" );

	my( $nrecs ) = dbquery( @db, dbRECORD_COUNT );

	if( $nrecs <= $moviepf{minframes} ) {

		elog_complain( "...not enough records (have $nrecs; minframes set to $moviepf{minframes}) for '$moviepf{name}' in $dbname\n" );

		return;

	} elsif( $opt_v ) {

		elog_notify( "dbtimelapse: processing $nrecs frames from $dbname\n" );
	}

	my( @files ) = ();
	for( $db[3] = 0; $db[3] < $nrecs; $db[3]++ ) {

		next if( $db[3] % $moviepf{decimation} != 0 );
		
		push( @files, dbextfile( @db ) );
	}

	my( $path ) = "$moviepf{path}";
	my( $options ) = "$moviepf{options}";
	my( $startlabel ) = "$moviepf{startlabel}";
	my( $endlabel ) = "$moviepf{endlabel}";
	my( $delay ) = "$moviepf{delay}";

	if( $moviepf{converter} eq "convert" ) {

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

		if( $opt_v ) {
			
			elog_notify( "dbtimelapse: executing: $cmd\n" );
		}

		system( "$cmd" );

	} elsif( $moviepf{converter} eq "transcode" ) {

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

		if( $opt_v ) {
			
			elog_notify( "dbtimelapse: executing: $cmd\n" );
		}

		system( $cmd );

		unlink( $tmplist );

	} else {

		print STDERR "Undefined converter $moviepf{converter}; Giving up.\n";

		return;
	}

	if( $opt_m ) {

		$db[3] = 0;

		my( $imagename, $imagesize ) = 
			dbgetv( @db, "imagename", "imagesize" );
	
		my( $time ) = dbex_eval( @db, "min(time)" );
		my( $endtime ) = dbex_eval( @db, "max(time)" );

		my( $length_sec ) = $endtime - $time;

		my( $dir, $dfile, $suffix ) = parsepath( $path );

		if( defined( $suffix ) && $suffix ne "" ) {
			
			$dfile .= ".$suffix";
		}

		@dbmovies = dblookup( @db, "", "movies", "", "" );

		$dbmovies[3] = dbfind( @dbmovies, "dfile == \"$dfile\"", -1 );

		if( $dbmovies[3] < 0 ) {
		
			$dbmovies[3] = dbaddnull( @dbmovies );
		}

		dbputv( @dbmovies,
			     "imagename", $imagename,
			     "time", $time,
			     "endtime", $endtime,
			     "length_sec", $length_sec,
			     "imagesize", $imagesize, 
			     "format", $moviepf{format},
			     "dir", $dir,
			     "dfile", $dfile,
			     "auth", "dbtimelapse" );
	} 

	return;
}

$Usage = "Usage: $pgm [-v] [-m] [-p pffile] database [movie]\n       $pgm [-v] [-p pffile] [-i imagename] [-s start [-e end]] database outputfile"; 

if ( ! &Getopts('vmp:i:s:e:') || @ARGV < 1 || @ARGV > 2 ) { 

    	my $pgm = $0 ; 
	$pgm =~ s".*/"" ;
	die ( "$Usage\n" );

} else {

	$dbname = shift( @ARGV );
}

if( $opt_p ) {

	$Pf = $opt_p;

} else { 

	$Pf = "dbtimelapse";
}

%movies = %{pfget( $Pf, "movies" )};
%default = %{pfget( $Pf, "default" )};

$default{name} = "custom";

if( $opt_i ) {
	
	$default{imagename} = $opt_i;
} 

if( $opt_s ) {
	
	$default{start} = $opt_s;
} 

if( $opt_e ) {
	
	$default{end} = $opt_e;
} 

foreach $movie ( keys %movies ) {

	$movies{$movie}->{name} = $movie;

	foreach $param ( keys %default ) {
		
		if( ! defined $movies{$movie}->{$param} ) {
			
			$movies{$movie}->{$param} = $default{$param};
		}
	}
}

if( $opt_i ) {

	if( @ARGV ) {

		$default{path} = pop( @ARGV );

	} else {

		die( "$Usage\n" );
	}

} else {

	if( @ARGV ) {

		$requested_movie = pop( @ARGV );
	} 
}

@db = dbopen ( "$dbname", "r+" );

if( defined( $requested_movie ) ) {

	if( ! defined( $movies{$requested_movie}->{path} ) ) {

		elog_die( "Couldn't find path for $requested_movie in $Pf\n" );
	}

	make_movie( $movies{$requested_movie} );

} elsif( $opt_i ) {
	
	make_movie( \%default );

} else {

	foreach $movie ( keys %movies ) {

		make_movie( $movies{$movie} );
	}
}
