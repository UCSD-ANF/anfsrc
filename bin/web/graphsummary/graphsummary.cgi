#!/usr/bin/perl
#
# This program prints a simple page with a 24 hour summary of MET data
# for a given source. Arguments are the source name (Revelle or Melville)
#
# Date started: 23 April 2004
# Author: Steve Foley

use File::Basename;

$SOURCENAME = "";
# SOURCE_NET_STATION_KEY keys should generally be printable,
# while the values are net_station format for internal hashing.
%SOURCE_NET_STATION_KEY = ("Melville" => "SIO_Melvil",
			   "ZUMA" => "LACOFD_ZUMA");
# SOURCE_DB values are what go to "<value>" in waveform.cgi args
%SOURCE_DB = ("Melville" => "siodbs_melville",
	      "Revelle" => "siodbs_revelle",
	      "ZUMA" => "db_LACOFD");
@{$CHANNELS_TO_PLOT{"Revelle"}} =
    (AT, BP, SW, LW, PR, RH, TW, TI, WT, SA, OX, FL);
@{$CHANNELS_TO_PLOT{"Melville"}} =
    (AT, BP, SW, LW, PR, RH, TW, TI, WT, SA, OX, FL);
@{$CHANNELS_TO_PLOT{"ZUMA"}} =
    (Bar, RainRate, UV, batt, pktver, rainday, rainmon, rainyr, solar,
     tranbat, wdir, wind);

%STATUS_TXT = ();

MAIN:
{
    # get source args
    if ($#ARGV == 0) 
    {
	$SOURCENAME = $ARGV[0];    
    }
   else
    {
	&print_bad_args();
	exit;
    }

    # process the source
    if (&source_defined($SOURCENAME))
    {	
	&load_status_hash();
	&print_header($SOURCENAME);
	&generate_plots($SOURCENAME);
	&print_footer();
    }
    else
    {
	&print_bad_args();
    }
}

# Generate a page full of the important plots for the given source
sub generate_plots
{
    my $source = shift;
    my $hashkey;
    foreach $channel (@{$CHANNELS_TO_PLOT{$source}})
    {
	$hashkey = $SOURCE_NET_STATION_KEY{$SOURCENAME} . "_" . $channel;
	($net,$sta,$cha,$loc,$lasttime,$calib,$segtype,$samprate,$val,$cval) =
	    split /\s/, $STATUS_TXT{$hashkey};
	$range24hr = $lasttime - (24*60*60);
	print "<P><A HREF=\"/waveform.cgi?"
	    . &make_db_sta_chan($SOURCENAME, $channel)
	    . "\">"
	    . "<IMG SRC=\"/waveform.cgi?"
	    . &make_db_sta_chan($SOURCENAME, $channel)
	    . "+$range24hr+$lasttime+$samprate+$segtype+filter+filter\" "
	    . "WIDTH=\"640\" HEIGHT=\"288\" ALT=\"Graph of $channel\">"
	    . "</A></P>\n";
    }
}

# Load status.txt file into a hash keyed by net and station
sub load_status_hash
{
    foreach $i (`cat /var/Web/status.txt`)
    {
        ($net,$station,$channel,$rest)=split /\s/,$i, 4;
        $station=substr($station,0,6);
	$hashkey = $net . "_" . $station . "_" . $channel;
	$STATUS_TXT{"$hashkey"}=join ("\t", $net, $station, $channel, $rest);
#	print "key: $hashkey, value: $STATUS_TXT{$hashkey}\n";
    }

}

# generate something like "siodbs_melville+Melvil_AT" from a source and a channel
# as arguments (in that order)
sub make_db_sta_chan
{
    my ($source) = shift;
    my ($channel) = shift;

    my ($hashkey) = $SOURCE_NET_STATION_KEY{$source} . "_" . $channel;

    ($net, $sta, $chan) = 
	split /\s/, $STATUS_TXT{$hashkey};
    return "$SOURCE_DB{$source}+$sta" . "_" . $channel;
}

# print the page header, take into account source name as first arg.
sub print_header
{
    my ($sourcename) = shift;
    print "Content-type: text/html\nPragma: no-cache\n\n";

    print "<HTML><HEAD><TITLE>" 
	. "Last 24 hours of basic weather data for $sourcename"
	. "</TITLE>\n"
	. "<H1>Last 24 hours of basic weather data for $sourcename"
	. "</H1><HR></HEAD><BODY>\n"
	. "For more detailed graphs, "
	. "<A HREF=\"/waveform?$SOURCE_DB{$sourcename}\">click here</A>.\n"
	. "Click on the graphs for more plot options of that data.\n";
}

# Print a simple page footer to close things off nicely.
sub print_footer
{
    print "</BODY></HTML>\n"
}

# Indicate bad arguments have been received
sub print_bad_args
{
    my ($basename) = &File::Basename::fileparse($0);
    print "Content-type: text/html\nPragma: no-cache\n\n";
    print "<HTML><HEAD><TITLE>Bad Arguments</TITLE></HEAD>\n<BODY>"
	. "Bad arguments were given to this script. "
	. "The data source may not have been specified, or data may not be "
	. "available for that source.\n" 
	. "Please try the following links or contact the webmaster:\n"
	. "<UL>\n"
	. "<LI><A HREF=\"/$basename?Melville\">R/V Melville</A></LI>\n"
	. "<LI><A HREF=\"/$basename?Revelle\">R/V Revelle</A></LI>\n"
	. "<LI><A HREF=\"/$basename?ZUMA\">LACOFD ZUMA</A></LI>\n"
	. "</UL></HTML>\n";
}

# Checks to see if the sourcename is a valid one. Takes source name as a scalar
# argument, and returns a boolean. Could check for specific sources...
sub source_defined
{
     my ($sourcename) = shift;
     if ((defined $sourcename) && ($sourcename ne "") 
	 && ($SOURCE_DB{$sourcename} ne ""))
     { return 1; }
     else
     { return 0; }
}

