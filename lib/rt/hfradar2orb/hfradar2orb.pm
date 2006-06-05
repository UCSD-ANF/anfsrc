#
# hfradar2orb
# 
# Kent Lindquist
# Lindquist Consulting
# 2004
#

package hfradar2orb;
require Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
	mdyhms2epoch
	encapsulate_packet 
	open_tracking_database 
	record_file
	Verbose Pfname Formats
);

use Datascope ;
use orb;

BEGIN {
	$Pfname = "hfradar2orb_pm";
	$Verbose = 0;

	%Formats = %{pfget( $Pfname, "formats" )};
	$Schema = pfget( $Pfname, "schema" );
}

sub mdyhms2epoch {
	my( @mdyhms ) = @_;

	my( $epoch ) = str2epoch( sprintf( "%s/%s/%s %s:%s:%s", @mdyhms ) );
	
	return $epoch;
}

sub open_tracking_database { 
	my( $dbname ) = @_;

	if( ! -e "$dbname" ) {

		if( $Verbose ) {

			elog_notify( "Creating tracking-database $dbname\n" );
		}

		dbcreate( $dbname, $Schema );	
	}

	my( @db ) = dbopen( $dbname, "r+" );

	return @db;
}

sub encapsulate_packet { 
	my( $buffer, $site, $beampattern, $format, $epoch, $orb ) = @_;

	if( ! defined( $Formats{$format} ) ) {
	
		elog_complain( "encapsulate_packet: No format '$format' " .
			       "in $Pfname.pf!! Skipping '$site' at " .
			       strtime( $epoch ) . "\n" );
		return -1;
	}

	my( $pktsuffix, $version, $table ) = split( /\s+/, $Formats{$format} );

	my( $packet );

	if( $version > 100 ) {

		$packet = pack( "na", $version, $beampattern );

	} else {

		$packet = pack( "n", $version );
	}

	$packet .= $buffer;

	my( $srcname ) = "$site" . "/" . "$pktsuffix";

	$rc = orbput( $orb, $srcname, $epoch, $packet, length( $packet ) );

	if( $Verbose ) {

		if( $rc == 0 ) {
			elog_notify "Sent '$file' to orb, timestamped " . 
				epoch2str( $epoch, "%D %T %Z", "" ) . "\n";
		} else {
			elog_complain "Failed to send '$dfile' to orb, " .
				"timestamped " . 
				epoch2str( $epoch, "%D %T %Z", "" ) . "\n";
		}
	}

	return 0;
}

sub record_file {
	my( $file, $site, $beampattern, $format, $epoch, @db ) = @_;

	if( ! defined( $Formats{$format} ) ) {
	
		elog_complain( "No format '$format' in $Pfname.pf!!" .
			       " Skipping file '$file'\n" );
		return -1;
	}

	my( $pktsuffix, $version, $table ) = split( /\s+/, $Formats{$format} );

	chomp( $file );

	$file = abspath( $file );

	my( $mtime ) = (stat("$file"))[9];

	my( $dir, $dfile, $suffix ) = parsepath( $file );

	if( "$suffix" ) { $dfile .= ".$suffix" }

	if( $Verbose ) {

		elog_notify "Adding '$dfile' to database, timestamped " . 
			epoch2str( $epoch, "%D %T %Z", "" ) . "\n";
	}

	@db = dblookup( @db, "", "$table", "", "" );

	my( $rec ) = dbfind( @db, 
		"sta == \"$site\" && time == $epoch && format == \"$format\"", -1 );

	if( $rec < 0 ) {

		dbaddv( @db, "sta", $site,
	     		"time", $epoch,
	     		"format", $format,
	     		"beampattern", $beampattern,
	     		"mtime", $mtime,
	     		"dir", $dir,
	     		"dfile", $dfile );
	} else {

		my( @dbt ) = @db;
		$dbt[3] = $rec;
		dbputv( @dbt, "mtime", $mtime );
	}

	return 0;
}

1;
