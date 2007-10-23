#
#   hfradar2orb.pm
#
#   Copyright (c) 2004-2006 Lindquist Consulting, Inc.
#   All rights reserved. 
#                                                                     
#   Written by Dr. Kent Lindquist, Lindquist Consulting, Inc. 
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#   KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#   WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
#   PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
#   OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR 
#   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#   SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#   This software may be used freely in any way as long as 
#   the copyright statement above is not removed. 
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
	$Max_packet_size = pfget( $Pfname, "max_packet_size" );
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

	my( $open_schema ) = dbquery( @db, dbSCHEMA_NAME );

	if( $open_schema ne $Schema ) {
		
		elog_complain( "WARNING: database '$dbname' uses schema " .
			"'$open_schema' which does not match the schema " .
			"'$Schema' assumed by hfradar2orb perl module\n" );
	}

	return @db;
}

sub verbose_orbput {
	my( $orb, $srcname, $epoch, $packet, $site, $ith, $n ) = @_;

	my( $rc ) = orbput( $orb, $srcname, $epoch, $packet, length( $packet ) );

	if( $Verbose ) {

		if( $rc == 0 ) {

			elog_notify "Sent packet $ith of $n for '$site' to orb, timestamped " . 
				epoch2str( $epoch, "%D %T %Z", "" ) . "\n";

		} else {

			elog_complain "Failed to send packet $ith of $n for '$site' to orb, " .
				"timestamped " . 
				epoch2str( $epoch, "%D %T %Z", "" ) . "\n";
		}
	}

	return $rc;
}

sub encapsulate_packet { 
	my( $buffer, $net, $site, $patterntype, $format, $epoch, $orb ) = @_;

	if( ! defined( $Formats{$format} ) ) {
	
		elog_complain( "encapsulate_packet: No format '$format' " .
			       "in $Pfname.pf!! Skipping '$site' at " .
			       strtime( $epoch ) . "\n" );
		return -1;
	}

	my( $pktsuffix, $version, $table ) = split( /\s+/, $Formats{$format} );

	my( $packet, $isubpacket, $nsubpackets );

	my( $srcname ) = "$net\_$site" . "/" . "$pktsuffix";

	if( $version == 120 ) {

		my( @subpackets ) = ();

		while( length( $buffer ) ) {

			push( @subpackets, substr( $buffer, 0, $Max_packet_size - 7, "" ) );
		} 

		$nsubpackets = scalar( @subpackets );

		for( $isubpacket = 1; $isubpacket <= $nsubpackets; $isubpacket++ ) {

			$packet = pack( "nann", $version, $patterntype, $isubpacket, $nsubpackets );

			$packet .= shift( @subpackets );

			verbose_orbput( $orb, $srcname, $epoch, $packet, $site, $isubpacket, $nsubpackets );
		}

	} elsif( $version == 110 ) {

		$packet = pack( "na", $version, $patterntype );

		$packet .= $buffer;

		if( length( $packet ) > $Max_packet_size ) {

			elog_complain( "encapsulate_packet: packet for '$site' at " .
			    strtime( $epoch ) . " is larger than $Max_packet_size byte " .
			    "maximum from $Pfname.pf and version '$version' doesn't " .
			    "support splitting: Skipping packet!!\n" );

			return -1;
		}

		verbose_orbput( $orb, $srcname, $epoch, $packet, $site, 1, 1 );

	} elsif( $version == 100 ) {

		$packet = pack( "n", $version );

		$packet .= $buffer;

		if( length( $packet ) > $Max_packet_size ) {

			elog_complain( "encapsulate_packet: packet for '$site' at " .
			    strtime( $epoch ) . " is larger than $Max_packet_size byte " .
			    "maximum from $Pfname.pf and version '$version' doesn't " .
			    "support splitting: Skipping packet!!\n" );

			return -1;
		}

		verbose_orbput( $orb, $srcname, $epoch, $packet, $site, 1, 1 );

	} else {
		
		elog_complain( "encapsulate_packet: format version '$version' not understood! " .
		  	"Check for errors in $Pfname.pf; skipping packet!!\n" );

		return -1;
	}

	return 0;
}

sub record_file {
	my( $file, $net, $site, $patterntype, $format, $epoch, @db ) = @_;

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
				"net == \"$net\" && " .
				"sta == \"$site\" && " .
				"time == $epoch && " .
				"format == \"$format\"",
				-1 );

	if( $rec < 0 ) {

		dbaddv( @db, 
			"net", $net,
			"sta", $site,
	     		"time", $epoch,
	     		"format", $format,
	     		"patterntype", $patterntype,
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
