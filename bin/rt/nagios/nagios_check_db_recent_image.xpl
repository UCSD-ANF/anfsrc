
# Copyright (c) 2004 The Regents of the University of California
# All Rights Reserved
#
# Permission to use, copy, modify and distribute any part of this software for
# educational, research and non-profit purposes, without fee, and without a
# written agreement is hereby granted, provided that the above copyright
# notice, this paragraph and the following three paragraphs appear in all
# copies.
#
# Those desiring to incorporate this software into commercial products or use
# for commercial purposes should contact the Technology Transfer Office,
# University of California, San Diego, 9500 Gilman Drive, La Jolla, CA
# 92093-0910, Ph: (858) 534-5815.
#
# IN NO EVENT SHALL THE UNIVESITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
# LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF THE UNIVERSITY
# OF CALIFORNIA HAS BEEN ADIVSED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
# CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
# ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF CALIFORNIA MAKES NO
# REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EITHER IMPLIED OR
# EXPRESS, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT THE USE OF THE
# SOFTWARE WILL NOT INFRINGE ANY PATENT, TRADEMARK OR OTHER RIGHTS.
#
#   This code was created as part of the ROADNet project.
#   See http://roadnet.ucsd.edu/
#
#   Written By: Steve Foley 12/14/2004

use strict;
use Getopt::Long;
use Datascope;
#use lib "$ENV[ANTELOPE}/data/perl" ;

use vars qw($opt_version $opt_help $opt_verbose $opt_warn $opt_crit
            $warn_at $warn_low $warn_high $crit_at $crit_low $crit_high
	    $status $opt_imagename $opt_dbname $VERBOSE);

use nagios_antelope_utils qw(&categorize_return_value
			     &parse_ranges
			     &print_version
			     &print_results
			     %ERRORS
			     $VERBOSE);


our $VERSION = '$Revision: 1.1 $';
our $AUTHOR = "Steve Foley, UCSD ROADNet Project, sfoley\@ucsd.edu";
our $PROGNAME = $0;
our $NAGIOS_SERVICE_NAME = "IMAGE AGE CHECK";
our $DEFAULT_ORB = ":";

our $TABLE_NAME = "images";
our $IMAGE_NAME_FIELD = "imagename";
our $IMAGE_TIME_FIELD = "time";

### PROTOTYPES
sub get_value($$);
sub check_args();
sub print_help();

MAIN:
{
   my ($result_code, $result_perf);
   Getopt::Long::Configure("bundling");
   $status = check_args();
   if ($status)
   {
      print "ERROR: processing arguments\n";
      exit $ERRORS{'UNKNOWN'};
   }

   $result_perf = get_value($opt_dbname, $opt_imagename);

   if (!defined $result_perf)
   {
       print_results($NAGIOS_SERVICE_NAME, $ERRORS{'UNKNOWN'}, "",
		     "age");
       exit $ERRORS{'UNKNOWN'};
   }


   ($result_code, $result_perf) 
	= categorize_return_value($result_perf, $warn_at, $warn_high, 
				  $warn_low, $crit_at, $crit_high, $crit_low);
   print_results($NAGIOS_SERVICE_NAME, $result_code, $result_perf, "age");

   exit $result_code;
}

##### 
# Get the value to be checked. In this case, it comes from the age of the 
# most recent db entry for a given image name.
# Param: dbpath - The full path to the database where the image resides
#        imagename - The name of the image to find
# Returns the age of the last image in the table or undef if a value
# was not found.
#
sub get_value($$)
{
    my ($numrecs, $time, $imagename, $dbname, $result, @db);
    $dbname = shift;
    $imagename = shift;

    $result = undef;

    if ((!defined $dbname) || (!defined $imagename))
    {
	return undef;
    }

    @db = dbopen( $dbname, "r" );
    @db = dblookup( @db, "", $TABLE_NAME, "", "" );

    $numrecs = dbquery( @db, dbRECORD_COUNT );

    $db[3] = dbfind( @db, "$IMAGE_NAME_FIELD == \"$imagename\"", $numrecs, 1 );

    $time = dbgetv( @db, "$IMAGE_TIME_FIELD" );

    $result = strtdelta(str2epoch("now") - $time);

    if ($VERBOSE)
    {
	print "Image timestamp: " . strtime( $time ) . "\n";
	print "Image age: $result\n";
    }
    
    return $result; 
}

######
# Check the arguments supplied
sub check_args()
{
    my ($fetching_params) = 0;

    GetOptions("V"     => \$opt_version,  "version"  => \$opt_version,
               "v"     => \$opt_verbose,  "verbose"  => \$opt_verbose,
               "h"     => \$opt_help,     "help"     => \$opt_help,
               "w=s"   => \$opt_warn,     "warn=s"   => \$opt_warn,
               "c=s"   => \$opt_crit,     "crit=s"   => \$opt_crit,
               "d=s"   => \$opt_dbname,   "dbname=s" => \$opt_dbname,
               "i=s"   => \$opt_imagename,"imgname=s" => \$opt_imagename
               );
    # handle options here
    if ($opt_version)
    {
        print_version($VERSION, $AUTHOR);
        exit $ERRORS{'OK'};
    }

    if ($opt_verbose)
    {
        $VERBOSE = 1;
        $nagios_antelope_utils::VERBOSE = 1;
    }

    if ($opt_help)
    {
        print_help();
        exit $ERRORS{'OK'};
    }

    # Gotta have warn, crit, dbname, and imagename options
    if ((!defined $opt_dbname) || (!defined $opt_imagename)
	|| (!defined $opt_warn) || (!defined $opt_crit))
    {
        print_usage();
        exit $ERRORS{'UNKNOWN'};
    }

    # Deal with our ranges
    ($warn_at, $warn_high, $warn_low, $crit_at, $crit_high, $crit_low) =
	parse_ranges($opt_warn, $opt_crit);
    if ((!defined $warn_at) || (!defined $warn_high) || (!defined $warn_low)
	|| (!defined $crit_at) || (!defined $crit_high)
	|| (!defined $crit_low))
    {
	print "Error in threshold ranges!\n";
	exit $ERRORS{'UNKNOWN'};
    }
}

######
#
sub print_usage()
{
    print "Usage: $0 -d dbname -i imagename [-v]  -w warn -c crit\n";
}

#####
#
#
sub print_help()
{
    print_version($VERSION, $AUTHOR);
    print_usage();
    print "\n";
    print " Check on a data value in status.txt. This file should list\n";
    print " sources that are arriving in real-time. Use the warn and crit\n";
    print " options to set thresholds for alerting on bad values.\n";
    print "\n";
    print "-d  (--dbname)  = The filename with path of the database\n";
    print "-i  (--imgname)  = The image name as it would appear in the db\n";
    print "-w  (--warn)    = Nagios range phrase ([@][min:]max) to "
        . "trigger a warning\n";
    print "-c  (--crit)    = Nagios range phrase ([@][min:]max) to "
        . "trigger a critical\n";
    print "-h  (--help)    = This help message\n";
    print "-V  (--version) = The version of this script\n";
    print "-v  (--verbose) = The verbosity of the output\n";
    print "\n";
}

