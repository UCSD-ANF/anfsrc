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

	$builddir = $ARGV[0];
	$orbname = $ARGV[1];
} 

if( $opt_d ) {

	$trackingdb = $opt_d;

	if( ! -e "$trackingdb" ) {

		if( $opt_v ) {
			print( "Creating tracking-database $trackingdb\n" );
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


$orbfd = orbopen( $orbname, "w&" );
# 
# 	$cmd = "find $basedir $statecmd -name '$subdirs[$i]->{glob}' -print";
# 
# 	$mtime = (stat("$file"))[9];
# 
# 	@db = dblookup( @db, "", "$subdirs[$i]->{table}", "", "" );
# 
# 	if( $newdb ) {
# 
# 		dbaddv( @db, "sta", $subdirs[$i]->{site},
# 		     	"time", $epoch,
# 		     	"pktsuffix", $subdirs[$i]->{pktsuffix},
# 		     	"mtime", $mtime,
# 		     	"dir", $dir,
# 		     	"dfile", $dfile );
# 	} else {
# 
# 		$rec = dbfind( @db, 
# 			"sta == \"$subdirs[$i]->{site}\" && time == $epoch && pktsuffix == \"$subdirs[$i]->{pktsuffix}\"", -1 );
# 
# 		if( $rec < 0 ) {
# 
# 			dbaddv( @db, "sta", $subdirs[$i]->{site},
# 		     		"time", $epoch,
# 		     		"pktsuffix", $subdirs[$i]->{pktsuffix},
# 		     		"mtime", $mtime,
# 		     		"dir", $dir,
# 		     		"dfile", $dfile );
# 		} else {
# 
# 			@dbt = @db;
# 			$dbt[3] = $rec;
# 			dbputv( @dbt, "mtime", $mtime );
# 
# 		}
# 
# 
# 	}
