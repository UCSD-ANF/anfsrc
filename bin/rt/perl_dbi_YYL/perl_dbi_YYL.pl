#!/usr/bin/perl

use DBI;

#
# /usr/bin/perl must be used since it is oracle compatible. hence the path 
# to perlpf must be hard coded.
#
use lib "/opt/antelope/4.8/data/perl";

use perlpf;


# Copyright (c) 2003-2006 The Regents of the University of California
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
# IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
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
#  This code was created as part of the ROADNet project.
#  See http://roadnet.ucsd.edu/
# 
#  This code is designed to pull data from Taiwan's oracle database 
#  and to inject it into the ROADNet ORB network.
# 
#    This Code By     : Todd Hansen    19-Oct-2006 
#    Last Updated By  : Todd Hansen    20-Oct-2006
#

$ParamFile = "perl_dbi_YYL.pf";
$samplerate = 1/(10*60); # 1 sample every 10 min
$verbose = 1;
$lastTimeStamp = 0;
$cycle_time = 3600; # check for new data every hour
$cycle_time_new_data = 600; # a shorter cycle time to repeat download if 
                            # there is still data available.
$num_days_perdownload = 3;  # the number of days of data to download - 1
$TimeZone = "Hongkong";
$tmpfile="/tmp/$NetSta.pf";

if ($#ARGV!=3)
{
    print stderr "Incorrect command line!\n\tperl_dbi_YYL.pl NET_STA database orbname statefile\n";
    exit(-1);
}

$NetSta    = $ARGV[0]; # NCHC_YYL
$DataBase  = $ARGV[1]; # YYL.YYL_BOG_BUOY_HI_RES
$orbname = $ARGV[2];   # :roadnet
$StateFile = $ARGV[3]; # YYL.state

print "NET_STA = $NetSta\nDataBase = $DataBase\nORBname = $orbname\nStateFile = $StateFile\n";

if (-e $StateFile && `grep lastDownloadedDataTimeStamp $StateFile | wc -l` > 0)
{
    $lastTimeStamp=pfget($StateFile,"lastDownloadedDataTimeStamp");
    print "StateFile: lastTimeStamp = $lastTimeStamp\n";
}

$lastdownloaded=0;
while (1)
{
    %selects=%{pfget($ParamFile,$NetSta)};
    @select_names=keys %selects;
    if ($#select_names < 0)
    {
	print "$ParamFile does not specify any SQL channels to look at!\n";
	exit(-1);
    }

    $dbh = DBI->connect('DBI:Oracle:palm228.nchc.org.tw:1521/ecogrid.nchc.org.tw','rpop','tw0824Rpop') or die "Couldn't connect to database: " . DBI->errstr;
    
    $oldest_timestamp=&min_time($dbh);
    $newest_timestamp=&max_time($dbh);
    
    if ($verbose)
    { print "Database Time Boundaries: $oldest_timestamp - $newest_timestamp\n"; }
    
    if ($lastTimeStamp < $newest_timestamp)
    {
	if ($verbose) 
	{
	    print "downloading data...\n";
	}

	if ($lastTimeStamp > $oldest_timestamp-60)
	{ $queryTimeStamp=$lastTimeStamp; }
	else
	{ $queryTimeStamp=$oldest_timestamp-60; }	

	my $startmon = `epoch -o $TimeZone +%b $queryTimeStamp`;
	my $startday = `epoch -o $TimeZone +%e $queryTimeStamp`;
	my $startyear = `epoch -o $TimeZone +%y $queryTimeStamp`;
	my $starttime = `epoch -o $TimeZone +%H%M $queryTimeStamp`;
	$queryTimeStamp+=$num_days_perdownload*24*3600;
	my $endmon = `epoch -o $TimeZone +%b $queryTimeStamp`;
	my $endday = `epoch -o $TimeZone +%e $queryTimeStamp`;
	my $endyear = `epoch -o $TimeZone +%y $queryTimeStamp`;
       
	chomp($startmon);
	chomp($startday);
	chomp($startyear);
	chomp($starttime);
	chomp($endmon);
	chomp($endday);
	chomp($endyear);

	my $q_str="";
	foreach $item (@select_names)
	{
	    $q_str.=", $item";
	}

	my $sth = $dbh->prepare("SELECT SAMPLEDATE, SAMPLE_TIME$q_str FROM $DataBase WHERE SAMPLEDATE BETWEEN \'$startday-$startmon-$startyear\' AND \'$endday-$endmon-$endyear\' AND (SAMPLEDATE <> \'$startday-$startmon-$startyear\' OR SAMPLE_TIME > \'$starttime\') ORDER BY SAMPLEDATE, SAMPLE_TIME") or die "couldn't prepare statement: " . $dbh->errstr;
	
	$sth->execute() or die "Couldn't execute statement: " . $sth->errstr;

	my @data;
	my $cnt=0;
	while (@data = $sth->fetchrow_array())
	{
	    my $sample_date=$data[0];
	    my $sample_time=$data[1];

	    # deal with date dumbness
	    my ($day,$mon,$year)=split /-/, $sample_date;
	    $year+=2000;
    
	    if ($mon eq "JAN")
	    { $mon = 1; }
	    elsif ($mon eq "FEB")
	    { $mon = 2; }
	    elsif ($mon eq "MAR")
	    { $mon = 3; }
	    elsif ($mon eq "APR")
	    { $mon = 4; }
	    elsif ($mon eq "MAY")
	    { $mon = 5; }
	    elsif ($mon eq "JUN")
	    { $mon = 6; }
	    elsif ($mon eq "JUL")
	    { $mon = 7; }
	    elsif ($mon eq "AUG")
	    { $mon = 8; }
	    elsif ($mon eq "SEP")
	    { $mon = 9; }
	    elsif ($mon eq "OCT")
	    { $mon = 10; }
	    elsif ($mon eq "NOV")
	    { $mon = 11; }
	    elsif ($mon eq "DEC")
	    { $mon = 12; }
	    
	    my $hr;
	    my $min;
	    if ($sample_time < 100)
	    {
		$hr=0;
		$min=$sample_time;
	    }
	    elsif ($sample_time < 1000)
	    {
		$hr=substr($sample_time,0,1);
		$min=substr($sample_time,1);
	    }
	    else
	    {
		$hr=substr($sample_time,0,2);
		$min=substr($sample_time,2);
	    }

	    my $timestr=sprintf "epoch -i $TimeZone +%s $year-%02d-$day $hr:$min","%E",$mon;
	    $sample_timestamp=`$timestr`;
	    chomp($sample_timestamp);

	    my $pkt="Version 100\n";
	    $pkt.="Timestamp $sample_timestamp\n";
	    $pkt.="SampleRate $samplerate\n";
	    $pkt.="Channels &Arr{\n";
	    for (my $lcv = 0; $lcv < $#data-2; $lcv++)
	    {
		if ($data[$lcv+2] =~ /^\s*$/)
		{ $data[$lcv+2]=3.4e38; }

		$data[$lcv+2] =~ s/\t+/ /g;

		$pkt.= " " .$selects{$select_names[$lcv]}. " " . $data[$lcv+2] . "\n";
	    }
	    $pkt.="}\n";

	    # submit pkt, update lastTimeStamp
	    open(FOO,">$tmpfile");
	    print FOO $pkt;
	    close(FOO);

	    `submit2orb.pl $orbname $tmpfile $NetSta $sample_timestamp` or die 'failed to submit packet';
	
	    $lastTimeStamp=$sample_timestamp;
	    &bury_statefile($lastTimeStamp);
	    $cnt++;
	}

	if ($verbose)
	{
	    print "number of rows returned: " . $sth->rows . "\n";
	}
	if ($sth->rows == 0)
	{
	    print "no rows returned!\n";
	    exit(-1);
	}
	
	$sth->finish;
    }
    elsif ($verbose)
    {
	printf "No new data available. (previousTimeStamp = $lastTimeStamp)\n";
    } 

    $dbh->disconnect;
    
    $curTime=`epoch +%E now`;
    chomp($curTime);
    if ($lastdownloaded > 0 && $cycle_time-$curTime+$lastdownloaded > 0)
    {
	if ($verbose)
	{
	    printf "Sleeping %d seconds\n",$cycle_time-$curTime+$lastdownloaded;
	}
	sleep($cycle_time-$curTime+$lastdownloaded);
    }
    else
    {
	if ($verbose)
	{
	    print "Sleeping $cycle_time seconds\n";
	}

	if ($lastTimeStamp < $newest_timestamp)
	{
	    sleep($cycle_time_new_data);
	}
	else
	{
	    sleep($cycle_time);
	}
    }
}

sub bury_statefile
{
    my ($lastDataTimeStamp)=@_;
    open(FOO,">$StateFile");
    print FOO "lastDownloadedDataTimeStamp\t$lastDataTimeStamp\n";
    close(FOO);
}

sub min_time()
{
    my $sth = $dbh->prepare("select MIN(SAMPLEDATE) from $DataBase") or die "couldn't prepare statement: " . $dbh->errstr;
    
    $sth->execute() or die "Couldn't execute statement: " . $sth->errstr;
    
    my @data = $sth->fetchrow_array();
    my $oldest_date=$data[0];
    $sth->finish;
    
    my $sth = $dbh->prepare("select MIN(SAMPLE_TIME) from $DataBase where SAMPLEDATE = '$data[0]'") or die "couldn't prepare statement: " . $dbh->errstr;
    
    $sth->execute() or die "Couldn't execute statement: " . $sth->errstr;

    @data = $sth->fetchrow_array();
    my $oldest_time=$data[0];

    $sth->finish;

    # deal with date dumbness
    my ($day,$mon,$year)=split /-/, $oldest_date;
    $year+=2000;

    if ($mon eq "JAN")
    { $mon = 1; }
    elsif ($mon eq "FEB")
    { $mon = 2; }
    elsif ($mon eq "MAR")
    { $mon = 3; }
    elsif ($mon eq "APR")
    { $mon = 4; }
    elsif ($mon eq "MAY")
    { $mon = 5; }
    elsif ($mon eq "JUN")
    { $mon = 6; }
    elsif ($mon eq "JUL")
    { $mon = 7; }
    elsif ($mon eq "AUG")
    { $mon = 8; }
    elsif ($mon eq "SEP")
    { $mon = 9; }
    elsif ($mon eq "OCT")
    { $mon = 10; }
    elsif ($mon eq "NOV")
    { $mon = 11; }
    elsif ($mon eq "DEC")
    { $mon = 12; }
    
    my $hr;
    my $min;

    if ($oldest_time < 100)
    {
	$hr=0;
	$min=$oldest_time;
    }
    elsif ($oldest_time < 1000)
    {
	$hr=substr($oldest_time,0,1);
	$min=substr($oldest_time,1);
    }
    else
    {
	$hr=substr($oldest_time,0,2);
	$min=substr($oldest_time,2);
    }

    my $timestr=sprintf "epoch -i $TimeZone +%s $year-%02d-$day $hr:$min","%E",$mon;
    my $oldest_timestamp=`$timestr`;
    chomp($oldest_timestamp);

    return ($oldest_timestamp);
}

sub max_time
{
    my $sth = $dbh->prepare("select MAX(SAMPLEDATE) from $DataBase") or die "couldn't prepare statement: " . $dbh->errstr;

    $sth->execute() or die "Couldn't execute statement: " . $sth->errstr;

    my @data = $sth->fetchrow_array();
    my $newest_date=$data[0];

    $sth->finish;
    
    my $sth = $dbh->prepare("select MAX(SAMPLE_TIME) from $DataBase where SAMPLEDATE = '$data[0]'") or die "couldn't prepare statement: " . $dbh->errstr;

    $sth->execute() or die "Couldn't execute statement: " . $sth->errstr;

    @data = $sth->fetchrow_array();
    my $newest_time=$data[0];

    $sth->finish;

    # deal with date dumbness
    my ($day,$mon,$year)=split /-/, $newest_date;
    $year+=2000;
    
    if ($mon eq "JAN")
    { $mon = 1; }
    elsif ($mon eq "FEB")
    { $mon = 2; }
    elsif ($mon eq "MAR")
    { $mon = 3; }
    elsif ($mon eq "APR")
    { $mon = 4; }
    elsif ($mon eq "MAY")
    { $mon = 5; }
    elsif ($mon eq "JUN")
    { $mon = 6; }
    elsif ($mon eq "JUL")
    { $mon = 7; }
    elsif ($mon eq "AUG")
    { $mon = 8; }
    elsif ($mon eq "SEP")
    { $mon = 9; }
    elsif ($mon eq "OCT")
    { $mon = 10; }
    elsif ($mon eq "NOV")
    { $mon = 11; }
    elsif ($mon eq "DEC")
    { $mon = 12; }

    my $hr;
    my $min;
    if ($newest_time < 100)
    {
	$hr=0;
	$min=$newest_time;
    }
    elsif ($newest_time < 1000)
    {
	$hr=substr($newest_time,0,1);
	$min=substr($newest_time,1);
    }
    else
    {
	$hr=substr($newest_time,0,2);
	$min=substr($newest_time,2);
    }
  
    my $timestr=sprintf "epoch -i $TimeZone +%s $year-%02d-$day $hr:$min","%E",$mon;
    my $newest_timestamp=`$timestr`;
    chomp($newest_timestamp);

    return($newest_timestamp);
}
