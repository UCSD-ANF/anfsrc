
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
#   Written By: Steve Foley 7/20/2004

use Datascope; # now()
use Getopt::Long;
use vars qw($opt_version $opt_help $opt_verbose $opt_warn $opt_crit
            $warn_at $warn_low $warn_high $crit_at $crit_low $crit_high
	    $opt_orb $opt_sroucei $VERBOSE);

use nagios_antelope_utils qw(&categorize_return_value
			     &parse_ranges
			     &print_version
			     &print_results
			     %ERRORS
			     $VERBOSE);


$VERSION = '$Revision: 1.2 $';
$AUTHOR = "Steve Foley, UCSD ROADNet Project, sfoley\@ucsd.edu";
$PROGNAME = $0;
$NAGIOS_SERVICE_NAME = "ORB UPTIME";
$DEFAULT_ORB = ":";

$NAGIOS_CHECK_ORBSTAT = '/opt/nagios/libexec/nagios_check_orbstat';

### PROTOTYPES
sub get_time_diff();
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

   $result_perf = get_time_diff();

   if ($result_perf < 0)
   {
       print_results($NAGIOS_SERVICE_NAME, $ERRORS{'UNKNOWN'}, $result_perf,
		     "uptime");
       exit $ERRORS{'UNKNOWN'};
   }


   ($result_code, $result_perf) 
	= categorize_return_value($result_perf, $warn_at, $warn_hi, $warn_low,
	 			  $crit_at, $crit_hi, $crit_low);
   if ($result_code != $ERRORS{'UNKNOWN'})
   {
       print_results($NAGIOS_SERVICE_NAME, $result_code, 
		     strtdelta($result_perf), "uptime");       
   }
   else 
   {
       print_results($NAGIOS_SERVICE_NAME, $result_code, 
		     $result_perf, "uptime");
   }

   exit $result_code;
}

##### 
# Get the difference in time between now and the last ORB startup
# Returns the number of seconds since the last ORB startup or -1 if no packet
# was found.
#
sub get_time_diff()
{
    my ($now, $orbstat_result, $orb_start_time, $time_diff);
    $now = now();
    $orbstat_result = 
	`$NAGIOS_CHECK_ORBSTAT -s $opt_source -t server -p started -o $opt_orb`;
    $orb_start_time = (split /\s/, $orbstat_result)[4];
    
    if ($orb_start_time  !~ /^\d+\.?\d*$/)
    {
	return -1;
    }
    
    $time_diff = ($now - $orb_start_time);

    if ($VERBOSE)
    {
	print "Source: $opt_source\n";
	print "ORB: $opt_orb\n";
	print "Current time: $now\n";
	print "orbstat result: $orbstat_result";
	print "ORB start time: $orb_start_time\n";
	print "Difference: $time_diff\n";
    }
    
    return $time_diff;
   
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
               "o=s"   => \$opt_orb,      "orb=s"    => \$opt_orb,
               "s=s"   => \$opt_source,   "source=s" => \$opt_source
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

    if (!defined $opt_orb)
    {
	$opt_orb = $DEFAULT_ORB;
    }

    # Gotta have warn, crit, and source options
    if ((!defined $opt_source) || (!defined $opt_warn) || (!defined $opt_crit))
    {
        print_usage();
        exit $ERRORS{'UNKNOWN'};
    }

    # Make sure our source is a pforbstat source
    if ($opt_source !~ /.*\/pf\/orbstat$/)
    {
	print "Source must be of type /pf/orbstat!\n";
	exit $ERRORS{'UNKNOWN'};
    }

    # Deal with our ranges
    ($warn_at, $warn_hi, $warn_low, $crit_at, $crit_hi, $crit_low) =
	parse_ranges($opt_warn, $opt_crit);
    if ((!defined $warn_at) || (!defined $warn_hi) || (!defined $warn_low)
	|| (!defined $crit_at) || (!defined $crit_hi)
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
    print "Usage: $0 -s source -o orb -w warn -c crit\n";
}

#####
#
#
sub print_help()
{
    print_version($VERSION, $AUTHOR);
    print_usage();
    print "\n";
    print " Check on the uptime of an orb based on a pforbstat packet coming";
    print " back from it. Use the warn and crit options to set thresholds";
    print " for alerting for recent downtime.";
    print " Uses nagios_check_orbstat for parsing.";
    print "\n";
    print "-s  (--source)  = The pforbstat source to look at\n";
    print "-o  (--orb)     = The ORB to look at (addr:port, default \":\")\n";
    print "-w  (--warn)    = Nagios range phrase ([@][min:]max) to "
        . "trigger a warning\n";
    print "-c  (--crit)    = Nagios range phrase ([@][min:]max) to "
        . "trigger a critical\n";
    print "-h  (--help)    = This help message\n";
    print "-V  (--version) = The version of this script\n";
    print "-v  (--verbose) = The verbosity of the output\n";
    print "\n";
}



