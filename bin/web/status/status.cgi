#!/opt/antelope/4.5p/bin/perl
use lib "/opt/antelope/4.5p/data/perl";
     
use orb;
use Datascope;

if ($#ARGV==-1)
{
    @l=`cat /var/Web/status.txt | awk  'BEGIN{FS = "\\t\"} {print \$1}' | sort -u | egrep -v ^#`;
    print "Content-type: text/html\nPragma: no-cache\n\n";
    print "<HTML><HEAD><TITLE>ROADNet Status Page Display</TITLE></HEAD>\n<BODY><H1>ROADNet Status Page Display</H1>\n<HR>\n<h3>Select a database</h3>\n<UL>\n";
    foreach $item (@l)
    {
	(@c1)=split /\//, $item;
	($db,$c2)=split /:/, $c1[$#c1];
	print "<LI><A HREF=\"status.cgi?$db\">$db</A></LI>\n";
    }
    print "</UL>\n</BODY></HTML>\n";	
    exit(0);
}
elsif ($#ARGV==0 || $#ARGV==1)
{
    $db=$ARGV[0];
    if ($db eq "scc")
    { $db = "SCC"; }

    foreach $i (`egrep \"^$db\" /var/Web/status.txt`)
    {
	chomp($i);
	($net,$sta,$chan,$loc,$time,$calib,$segtype,$samprate,$value)=split /\t/,$i;
	$segtype{$sta}{$chan}=$segtype;
	if ($calib != 0)
	{
	    $samples{$sta}{$chan}=$value*$calib;
	}
	else
	{
	    $samples{$sta}{$chan}=$value;
	}
	$timestamp{$sta}{$chan}=$time;
	$h{"$sta $chan"}{"rate"}=$samprate;
    }

    if ($db eq "SCC")
    {
	# Paul's code here
	
	# Compute which site to display data for.
	if($#ARGV == 1)
	{ $ref = lc($ARGV[1]); }
#	else { $ref = "ib"; }

	$doText = 0;

	if( rindex($ref,"ci") >= 0) {$sta = "CI"}
	elsif( rindex($ref,"ib") >= 0) {$sta = "IB";}
	else { $doText = 1; }
	
	$sdcoos='http://sdcoos.ucsd.edu';
	
	print "Content-type: text/html\nPragma: no-cache\n\n";

	if($sta eq "IB" && $doText == 0){
		print "<script>document.title=\"Imperial Beach Meteorological Data\";</script>\n\n";
	}
	
	elsif($sta eq "CI" && $doText == 0){ 
		print "<script>document.title=\"Coronado Islands Meteorological Data\";</script>\n\n";
	}
	else{
	    print "<!--- Just a test --->\n";
	    print "<HTML><HEAD><TITLE>SCC DAta</TITLE><BODY><h1>SCC data</H1>\n<HR>\n<A HREF=\"http://sdcoos.ucsd.edu/data/mercali/ib_main.cfm\">IB</A>\n<BR>\n<A HREF=\"http://sdcoos.ucsd.edu/data/mercali/ci_main.cfm\">CI</A></BODY></HTML>";
	}
	

	
# INSERT DATA HERE

	if($doText == 0){
		print "<center>\n<table border=0 style='border-compress:compress; border: solid #111111 1px' class='Text' width='250' cellpadding='2' cellspacing='0'>\n";
	}
	
	$ref = $ENV{'HTTP_REFERER'};
	$ref = lc($ref);
	
	$ctr=0;
	@mon = (31,59,90,120,151,181,212,243,273,304,334,365);
	@mnames = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
	$hrmin = $samples{$sta}{"hour_min"};
	$hrmin /= 1000;
	
	
	use POSIX "floor";
	$yr = $samples{$sta}{"year"};
	$yr /= 1000;

	$lr = 0;
	if( ($yr %4) == 0)
	{ $lr = 1; }
	
	$hr = substr($hrmin,0,2);
	#$min = substr($hrmin,2,2);
	$min = $hrmin % 100;
	$hr = floor($hrmin/100);
	
	$jday = $samples{$sta}{"day"};
	$jday /= 1000;

	# TODO: Test during a leap year.
	if( $jday > @mon[1] && $lr > 0)		# Leap year calculation
	{ 
		$jday -= $lr; 
		@mon[0] -= $lr;
		@mon[1] -= $lr;
	}
	while(@mon[$ctr] < $jday) {$ctr++;}
	$jday = $jday - @mon[$ctr-1];
	$dispMon = @mnames[$ctr];
	

	if($doText == 0){
		print " <tr valign='top'><td>$dispMon $jday, $yr $hr:";
		if($min < 10) {print "0";}
		print "$min UTC</td>";
		print "  <td align='right' id='convert_label'><a href='javascript:self.units()' target='_self'>Metric Units</a></td></tr>\n";
	}
	
	@inOrder = qw(wind_sp wind_dir air_temp rel_hum baro_pr sol_rad rain_fal);
	@mysegd = qw(s a t p P W D);
	@inOrderUnits = ("m/s", "&#176;", "&#176; C", "%", "mb", "Wm<sup>-2</sup>", "mm");
	@inOrderLabels = ("Wind Speed", "Wind Direction (from)", "Air Temperature", "Relative Humidity", 
				"Barometric Pressure", "Solar Radiation", "Rain Fall");

	@windDir = ("N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW");
	@windLim = (11,33,56,78,101,123,146,168,191,213,236,258,281,303,326,348);

	for($ctr=0;$ctr < @inOrder;$ctr++)
	{
	
	    $chan=@inOrder[$ctr];
	    $mychan=@inOrderLabels[$ctr];
	    $myseg=@inOrderUnits[$ctr];
		$segd=$segtype{$sta}{$chan};
		$seg=`/opt/antelope/4.5p/bin/trlookup_segtype $segd`;
		chomp($seg);
		$samp=$samples{$sta}{$chan};
		$time=$timestamp{$sta}{$chan}+30;
		$oldtime=$time-24*60*60*7;
		$rate=$h{"$sta $chan"}{"rate"};

		if($ctr == 1)  #IF this is processing wind direction.
		{
			#Following 1 line needed for temporary correction.
			if($sta eq "CI") {$samp = ($samp + 180) % 360};

			$wctr = 0;
			while($samp > @windLim[$wctr]) { $wctr++; }
			if($wctr >= @windLim)
			{ $myseg = "$myseg (@windDir[0])"; }
			else { $myseg = "$myseg (@windDir[$wctr])"; }
		}

		if($doText == 0){
			if( ($ctr % 2) == 0 ){ print " <TR class='even'>\n"; }
			else { print " <TR>\n"; }

			print "  <input type='hidden' name='$mychan' value=\"http://mercali.ucsd.edu/scc_waveform.cgi?$db+$sta". "_$chan+$oldtime+$time+$rate+@mysegd[$ctr]+filter+filter\">\n\n";
			print "  <TD class='label' id='$chan". "_label'><A HREF=\"http://mercali.ucsd.edu/scc_waveform.cgi?scc+$sta". "_$chan+$oldtime+$time+$rate+@mysegd[$ctr]+filter+filter\" target='_blank'>$mychan</A></TD>\n";
			print "  <TD align='right' id='$chan'>$samp $myseg</TD></TR>\n\n";
		}
		
# THIS IS WHERE THE LIST OF GRAPHS IS GENERATED
		else{	
			print "<CFOUTPUT>\n<CFHTTP url=\"http://mercali.ucsd.edu/scc_waveform.cgi?$db+$sta". "_$chan+$oldtime+$time+$rate+@mysegd[$ctr]+filter+filter\"\n";
			print "  port=\"80\" method=\"get\" name=\"$mychan\" resolveURL=\"yes\" throwOnError=\"no\" redirect=\"no\" timeout=\"20\"\n";
			print "  path=\"#root#sdcoos/data/mercali/\"\n";
			print "  file=\"$chan\">\n";
			print "</CFHTTP>\n</CFOUTPUT>\n\n";
		}

	
	}


	if($doText == 0){
	    print "<TR><TD colspan='2' align='center' class='label'><A HREF=\"javascript:showAll()\" target='_self'>View All Plots</A></TD></TR>\n";
	    print "\n</table>\n</center>\n\n\n";
	}
	
	
# END DATA INSERT
# END of Paul's Code
    }
    elsif ($db eq "HM")
    {
	print "Content-type: text/html\nPragma: no-cache\n\n";
	print "<HTML><HEAD><TITLE>Climate Research Data Summary (Values are uncalibrated!)</TITLE></HEAD>\n";
	print "<BODY>\n<H1>Climate Research Data Summary (Values are uncalibrated!)</H1>\n<HR>\n";
	print "<TABLE><TD>";

	foreach $sta (keys %samples)
	{
	    print "<h3>Station $sta</H3>\n<UL>\n";
	    foreach $chan (keys %{$samples{$sta}})
	    {
		$segd=$segtype{$sta}{$chan};
		$seg=`/opt/antelope/4.5p/bin/trlookup_segtype $segd`;
		chomp($seg);
		$samp=$samples{$sta}{$chan};
		$time=$timestamp{$sta}{$chan}+30;
		$oldtime=$time-24*60*60*7;
		$rate=$h{"$sta $chan"}{"rate"};
		print "<LI><B><A HREF=\"http://mercali.ucsd.edu/waveform.cgi?hm+$sta". "_$chan+$oldtime+$time+$rate+$segd+filter+filter\">$chan:</A></B> $samp $seg</LI>\n";
	    }
	    print "</UL>\n";
	}
	print "</TD>\n<TD VALIGN=TOP><IMG SRC=\"http://mercali.hpwren.ucsd.edu/webimg_small.cgi?SMER_Gorge_Axis1+1\"><BR><P>SMER Gorge Cam 1</P><HR><IMG SRC=\"http://mercali.hpwren.ucsd.edu/webimg_small.cgi?SMER_Gorge_Axis2+1\"><BR><P>SMER Gorge Cam 2</P><HR><IMG SRC=\"http://mercali.hpwren.ucsd.edu/webimg_small.cgi?SMER_Gorge_Axis3+1\"><BR><P>SMER Gorge Cam 3</P><HR><IMG SRC=\"http://mercali.hpwren.ucsd.edu/webimg_small.cgi?SMER_NORTH_Axis1+1\"><BR><P>SMER North Cam 1</P><HR><IMG SRC=\"http://mercali.hpwren.ucsd.edu/webimg_small.cgi?SMER_NORTH_Axis2+1\"><BR><P>SMER North Cam 2</P><HR><IMG SRC=\"http://mercali.hpwren.ucsd.edu/webimg_small.cgi?SMER_NORTH_Axis3+1\"><BR><P>SMER North Cam 3</P></TD><TR></TABLE>\n</BODY></HTML>\n";
    }
    else
    {
	print "Content-type: text/plain\nPragma: no-cache\n\n";
	foreach $sta (keys %samples)
	{
	    foreach $chan (keys %{$samples{$sta}})
	    {
		$time=$timestamp{$sta}{$chan};
		$samp=$samples{$sta}{$chan};
		$segtype=$segtype{$sta}{$chan};
		print "$time\t$sta\t$chan\t$samp\t$segtype\n";
	    }
	}
    }
}
