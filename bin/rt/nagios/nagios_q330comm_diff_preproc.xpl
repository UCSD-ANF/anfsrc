

#
# Copyright (c) 2006 The Regents of the University of California
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
#   This code was created as part of the USArray ANF project.
#
#   Written By: Steve Foley 4/6/2006
# 
#
# Takes a nagios host filename and a db containing a q330comm table
# and puts them into the same, sorted format of names and IP addresses.
# The output files are suitable for diffing.
#
# Requires nagios alias to appear before address, does not support getopts

use strict;
use lib "$ENV{ANTELOPE}/data/perl";
use Datascope;

our $Q330_TABLE_NAME = "q330comm";

our ($alias, $address, $rows, $inp);
our ($host_filename, $host_out_filename, $table_out_filename);
our (%nagios_alias_addr_list, %table_alias_addr_list);
our (@db, $dbname);

sub print_keys($ %);

#######
sub print_keys ($ %)
{
    my ($filename) = shift;
    my %alias_addr_list = @_;
    my ($key);

    open (OUTFILE, ">$filename") or die "Couldnt open $filename\n";
    foreach $key (sort (keys (%alias_addr_list)))
    {
	print OUTFILE "$key\t$alias_addr_list{$key}\n";
    }
    close (OUTFILE);
}

########
sub usage ()
{
    print "Usage: $0 nagios_file table host_output table_output\n";
}

########
MAIN:
{
    if ($#ARGV != 3) { &usage(); exit(1); }

    $host_filename = $ARGV[0];
    $dbname = $ARGV[1];
    $host_out_filename = $ARGV[2];
    $table_out_filename = $ARGV[3];

    ## Handle the nagios file first
    open (HOSTS, $host_filename) or die "Could not open $ARGV[0]\n";
    
    while (<HOSTS>) 
    {
	
	# grep out alias (only one word allowed)
	if (($alias) = (/\s*alias\s*(\w*)\s*$/))
	{
	    # add the TA_ first if needed
	    if ($alias !~ /TA_.*/)
	    {
		$alias = "TA_$alias";
	    }
	    # grep out address
	    $_ = <HOSTS>;
	    if (($address) = (/\s*address\s*(\d+\.\d+\.\d+\.\d+)/))
	    {
		# pop into assoc array
		$nagios_alias_addr_list{$alias} = $address;
	    }
	}
    }

    close (HOSTS);

    print_keys($host_out_filename, %nagios_alias_addr_list);
    
    ## On to the database side of things
    @db = dbopen ($dbname, "r") or die "Could not open $dbname\n";
    @db = dblookup (@db, 0, $Q330_TABLE_NAME, 0, 0);
    $rows = dbquery (@db, "dbRECORD_COUNT");
    
    $db[3] = 0;
    while ($db[3] < $rows)
    {
	($alias, $inp) = dbgetv(@db, qw(dlsta inp));
	$db[3]++;
	($address) = (split /:/, $inp)[1];
	$table_alias_addr_list{$alias} = $address;
    }

    print_keys($table_out_filename, %table_alias_addr_list);
}
