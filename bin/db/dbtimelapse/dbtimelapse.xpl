#
# dbtimelapse
# 
# Kent Lindquist 
# Lindquist Consulting
# 2004
#

require "getopts.pl" ;
use Datascope ;

sub free_views {
	my( @db ) = splice( @_, 0, 4 );
	my( @view_names ) = @_;

	foreach $view ( @view_names ) {
		
		@db = dblookup( @db, "", $view, "", "" );

		dbfree( @db );
	}

	return;
}

sub make_movie {
	my( $ref ) = @_;
	my( %moviepf ) = %$ref;

	my( @view_names ) = ();

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

	push( @view_names, dbquery( @db, "dbTABLE_NAME" ) );

	@db = dbsort( @db, "time" );

	push( @view_names, dbquery( @db, "dbTABLE_NAME" ) );

	my( $nrecs ) = dbquery( @db, dbRECORD_COUNT );

	if( $nrecs <= $moviepf{minframes} ) {

		elog_complain( "...not enough records (have $nrecs; minframes set to $moviepf{minframes}) for '$moviepf{name}' in $dbname\n" );

		free_views( @db, @view_names );

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

		$tmplist = "/tmp/imlist_$<_$$";

		open( L, ">$tmplist" );

		foreach $file ( @files ) {

		print L "$file\n";
		}

		close( L );	

		# ImageMagick sometimes needs the extension to 
		# perform correctly:

		if( $path !~ /\.$format$/ ) {

			$path .= ".$moviepf{format}";
		}

		$cmd = "convert $verbose $options $startimage $delay \@$tmplist $endimage $path";

		if( $opt_v ) {
			
			elog_notify( "dbtimelapse: executing: $cmd\n" );
		}

		system( "$cmd" );

		unlink( $tmplist );

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

		free_views( @db, @view_names );

		return;
	}

	if( $moviepf{auto_extension} ne "" ) {

		system( "mv $path$moviepf{auto_extension} $path" );
	}

	# Guarantee that the extension is correct:

	if( $path !~ /\.$moviepf{format}$/ ) {

		system( "mv $path $path.$moviepf{format}" );

		$path .= ".$moviepf{format}";
	}

	if( ! -e "$path" ) {
	
		elog_complain( "dbtimelapse: Failed to create $path!\n" );

		free_views( @db, @view_names );

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

	if( $opt_v ) {
			
		elog_notify( "dbtimelapse: finished making $path\n" );
	}

	free_views( @db, @view_names );

	return;
}

$Usage = "Usage: $pgm [-v] [-m] [-p pffile] database [movie]\n       $pgm [-v] [-t template] [-p pffile] [-i imagename] [-s start [-e end]] database outputfile"; 

if ( ! &Getopts('vmt:p:i:s:e:') || @ARGV < 1 || @ARGV > 2 ) { 

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

if( ( $rc = pfrequire( $Pf, "9/21/04" ) ) < 0 ) {

	die( "$Pf.pf is not present or too old (pfrequire rc = $rc). Bye.\n" );
}

%movies = %{pfget( $Pf, "movies" )};
%defaults = %{pfget( $Pf, "defaults" )};

$defaults{name} = "custom";

if( $opt_i ) {
	
	$defaults{imagename} = $opt_i;
} 

if( $opt_s ) {
	
	$defaults{start} = $opt_s;
} 

if( $opt_e ) {
	
	$defaults{end} = $opt_e;
} 

if( $opt_t ) {
	
	$defaults{template} = $opt_t;
}

if( ! defined $defaults{template} ) {

	die( "No template defined for defaults array in $Pf.pf! Bye.\n" );
}

foreach $movie ( keys %movies ) {

	$movies{$movie}->{name} = $movie;

	$movie_template = $movies{$movie}->{"template"};

	if( ! defined $movie_template ) {
		
		$movie_template = $defaults{template};
	}

	%template = %{pfget( $Pf, "templates{$movie_template}" )};

	if( ! defined %template ) {
		
		complain( "Couldn't find template '$movie_template' " .
		     "in $Pf.pf! Skipping movie '$movie'\n" );

		next;
	}

	foreach $param ( keys %template ) {

		if( ! defined $movies{$movie}->{$param} ) {

			$movies{$movie}->{$param} = $template{$param};
		}
	}

	foreach $param ( keys %defaults ) {
		
		if( ! defined $movies{$movie}->{$param} ) {
			
			$movies{$movie}->{$param} = $defaults{$param};
		}
	}
}

%template = %{pfget( $Pf, "templates{$defaults{template}}" )};

foreach $param ( keys %template ) {

	$defaults{$param} = $template{$param};
}

if( $opt_i ) {

	if( @ARGV ) {

		$defaults{path} = pop( @ARGV );

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
	
	make_movie( \%defaults );

} else {

	foreach $movie ( keys %movies ) {

		make_movie( $movies{$movie} );
	}
}
