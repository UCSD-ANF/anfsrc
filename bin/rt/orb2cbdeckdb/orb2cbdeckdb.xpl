
#
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
#   Written By: Steve Foley 7/30/2004
#
# Note: This code requires that DBI and DBD::DB2 packages are installed
# in the Antelope perl area. 

use strict;
use Getopt::Long;
use DBI;
use Datascope;
use orb;

use vars qw($dbh $opt_version $opt_help $opt_verbose $opt_src $opt_orb
	    $opt_configfile $dbalias $dbuser $dbpassword $orb $statefile
	    $stateref $tracefile $tracelevel $timezone);

# Prototypes
sub clean_exit($);
	       
# Constants
my $VERSION           = '$Revision: 1.2 $';
my $AUTHOR            = 'Steve Foley, UCSD ROADNet Project, sfoley@ucsd.edu';

my $DBALIAS_INDEX     = "dbalias";
my $DBUSER_INDEX      = "dbuser";
my $DBPASSWORD_INDEX  = "dbpassword";
my $STATEFILE_INDEX   = "statefile";
my $TRACE_FILE_INDEX  = "tracefile";
my $TRACE_LEVEL_INDEX = "tracelevel";
my $TIME_ZONE_INDEX   = "timezone";
my $NUM_CHANNELS      = 16;

my $TIME_FORMAT       = "%Y-%m-%d-%H.%M.%S.%s";
my $TIME_LENGTH       = 24;
my $TABLE             = "DB2ADMIN.TB_ID1_16";

my $INSERT_STMT = "INSERT INTO $TABLE(MDATE,C1,C2,C3,C4,C5,C6,C7,C8,C9," .
  "C10,C11,C12,C13,C14,C15,C16) VALUES(TIMESTAMP(CAST(? AS CHAR($TIME_LENGTH))),?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)";

# Defaults
my $VERBOSE = 0;

#####
#
MAIN:
{
    my ($sql_result, $status);
    my ($pktid, $packet_src, $packet_time, $raw_packet, $num_bytes);
    my ($orb_result, $packet, $packet_type, $packet_desc, $timestamp);
    my ($prep_stmt);
    my ($channel_count, $sample_count, $i, @pkt_data, $nsamps);
    my (@db_in_vals);
    my ($result);

    elog_init($0, @ARGV);

    Getopt::Long::Configure("bundling");
    $status = check_args();
    if ($status)
    {
	elog_die("Error processing arguments!\n");
    }

    # load parameters
    $dbalias = pfget($opt_configfile, $opt_src . "{$DBALIAS_INDEX}");
    $dbuser = pfget($opt_configfile, $opt_src . "{$DBUSER_INDEX}");
    $dbpassword = pfget($opt_configfile, $opt_src . "{$DBPASSWORD_INDEX}");
    $statefile = pfget($opt_configfile, $opt_src . "{$STATEFILE_INDEX}");
    $tracefile = pfget($opt_configfile, $opt_src . "{$TRACE_FILE_INDEX}");
    $tracelevel = pfget($opt_configfile, $opt_src . "{$TRACE_LEVEL_INDEX}");
    $timezone = pfget($opt_configfile, $opt_src . "{$TIME_ZONE_INDEX}");
	

    if ($VERBOSE)
    {
	elog_debug("Options: DB Alias: $dbalias, User: $dbuser,\n"
	  . "   Password: $dbpassword, State file: $statefile\n");
    }

    # Connect to the orb
    $orb = orbopen("$opt_orb", "r&") or elog_die("Cannot open orb!\n");
    orbselect($orb, "$opt_src") or
	    elog_die("Cannot select on the ORB!\n");
    orbseek($orb, "ORBOLDEST"); # go to the end if we cant resurrect later

    # Reposition
    if ($statefile)
    {
	$stateref = 0;
	exhume ($statefile, \$stateref, 15);
	$pktid = 0;
	$packet_time = 0;
	$result = orbresurrect($orb, \$pktid, \$packet_time);
	if ($result < 0)
	{
	    elog_complain("Resurection failed. No statefile? Off a second?\n");
	}
    }

    # Open the DB now
    $dbh = DBI->connect("dbi:DB2:$dbalias",$dbuser,
			$dbpassword,{AutoCommit =>0} )
         or elog_die "Sorry, cannot connect to $dbalias $DBI::errstr\n";
    
    # In verbose mode, turn on DBI debugging
    if (($VERBOSE) && ($tracefile) && ($tracelevel))
    {
	DBI->trace($tracelevel, $tracefile);
    }

    # Do the really important stuff
    for (;$stateref == 0;)
    {
	# grab a packet from the orb FIXME!!
	if (($pktid, $packet_src, $packet_time, $raw_packet, $num_bytes) =
	    orbreap($orb))
	{
	    # unstuff it
	    if ($VERBOSE)
	    {
#		showPkt($pktid, $packet_src, $packet_time, $raw_packet, 
#			$num_bytes, 2);
	    }

	    ($result, $packet) = unstuffPkt($packet_src, $packet_time,
					    $raw_packet, $num_bytes);
	    if (defined $packet)
	    {
		# Quick sanity check
		($packet_type, $packet_desc) = $packet->PacketType();
		if ($packet_type ne "MGENC")
		{
		    elog_notify("Bad packet type: $packet_type\n");
		    next;
		}

		# get the number of samples
		$nsamps = $packet->channels(0)->nsamp;

		# prep the statement
		$prep_stmt = $dbh->prepare($INSERT_STMT);

		for ($sample_count = 0; 
		     $sample_count < $nsamps;
		     $sample_count++)
		{
		    # Get a timestamp based on how many samples in we are
		    $timestamp = epoch2str($packet->time() + 
					   ((1/$nsamps)*$sample_count),
					   $TIME_FORMAT, $timezone);

		    for ($channel_count = 0; 
			 $channel_count < $NUM_CHANNELS;
			 $channel_count++)
		    {
			@pkt_data = $packet->channels($channel_count)->data();
			$db_in_vals[$channel_count] =$pkt_data[$sample_count]
			    * ($packet->channels($channel_count)->calib);

			if (!defined $db_in_vals[$channel_count])
			{
			    elog_notify("Empty sample at sample: "
					. $sample_count . ", channel: "
					. $channel_count . "\n");
			}
		    } #end channel loop
		    # Now make the insert
		    eval
		    {
			$prep_stmt->bind_param(1, $timestamp, 
					       $DBI::SQL_VARCHAR);
			for ($i = 2; $i <= $NUM_CHANNELS+1; $i++)
			{
			    $prep_stmt->bind_param($i,$db_in_vals[$i-2],
						   $DBI::SQL_DOUBLE);

			}
			$prep_stmt->execute();
		    };
		    # handle exception
		    if ($@)
		    {
			elog_complain("Could not insert data with time: "
				      . "$timestamp, error: $@\n");
			$dbh->rollback() or elog_die("Couldnt rollback!\n");
		    }
		} # end sample loop

		# Commit nsamps of data
		eval
		{
		    $dbh->commit();
		    if ($VERBOSE)
		    {
			elog_debug("Commited row after packet time: " . 
				   "$timestamp at " . now() . "\n"); 
		    }
		    bury();
		};
		# handle exception
		if ($@)
		{
		    elog_complain("Could not commit and bury, error: $@\n");
		    $dbh->rollback() or elog_die("Couldnt rollback!\n");
		}
		$prep_stmt->finish(); # make a new one later
	    }
	} # end while(1)
    }
}

######
# check_args - Check the arguments that were handed in
sub check_args()
{   
    GetOptions("v"     => \$opt_version,  "version"  => \$opt_version,
               "V"     => \$opt_verbose,  "verbose"  => \$opt_verbose,
               "h"     => \$opt_help,     "help"     => \$opt_help,
               "o=s"   => \$opt_orb,      "orb=s"    => \$opt_orb,
               "s=s"   => \$opt_src,      "source=s" => \$opt_src,
               "c=s"   => \$opt_configfile, "config=s"  => \$opt_configfile
               );
    
    # handle options here
    if ($opt_version)
    {
        print_version();
        exit -1;
    }
    
    if ($opt_verbose)
    {
        $VERBOSE = 1;
    }
    
    if ($opt_help)
    {
	print_usage();
        exit -1;
    }
    
    if (!defined $opt_orb)
    {
	print_usage();
	elog_die "Missing orb parameter!";
    }
    if (!defined $opt_src)
    {
	print_usage();
	elog_die "Missing source parameter!";
    }
    if (!defined $opt_configfile)
    {
	print_usage();
	elog_die "Missing config file parameter!";
    }
}

######
# clean_exit - Cleanly shutdown a connection and exit with the return code
# parameter.
sub clean_exit($)
{
    my ($exit_code) = shift;

    elog_notify("Cleaning up and exiting!\n");

    # Shutdown DB connection
    $dbh->commit();
    $dbh->disconnect();
    
    # close orb
#    if ($statefile)
#    {
#	bury();
#    }
    orbclose($orb);

    exit $exit_code;
}


######
# Usage - Print out the usage for the program
sub print_usage()
{
    print "$0 version $VERSION\nwritten by $AUTHOR\n";
    print "Usage: $0 [-V] [-v] [-h] -s srcname -o orbname -c configfile\n";
}

######
# print_version - Prints the version of the program
sub print_version()
{
    print "$0 version $VERSION\nwritten by $AUTHOR\n";
}
