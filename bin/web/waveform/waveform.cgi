#!/opt/antelope/4.5p/bin/perl
use lib "/opt/antelope/4.5p/data/perl";

use orb;
use Datascope;

if ($#ARGV==-1)
{
    foreach $file (`ls /home/rt/db/`)
    {
	open(file2,"/home/rt/db/$file");
	if (-f file2)
	{
	    @s=`head -3 /home/rt/db/$file`;
	    if ($s[1] =~ /^schema\s+rt1.0/)
	    {
		chomp($file);
		push(@l,$file);
	    }
	}
	close(file2);
    }
    #@l=`/bin/grep rt1.0 /home/rt/db/*`;
    print "Content-type: text/html\nPragma: no-cache\n\n";
    print "<HTML><HEAD><TITLE>ROADNet Waveform Display</TITLE></HEAD>\n<BODY><H1>ROADNet Waveform Display</H1>\n<HR>\n<h3>Select a database</h3>\n<UL>\n";
    foreach $item (@l)
    {
	(@c1)=split /\//, $item;
	($db,$c2)=split /:/, $c1[$#c1];
	print "<LI><A HREF=\"waveform.cgi?$db\">$db</A></LI>\n";
    }
    print "</UL>\n</BODY></HTML>\n";	
    exit(0);
}
elsif ($#ARGV==0)
{
    $db=$ARGV[0];

    print "Content-type: text/html\nPragma: no-cache\n\n";
    print "<HTML><HEAD><TITLE>ROADNet Waveform Display</TITLE></HEAD>\n<BODY><H1>ROADNet Waveform Display</H1>\n<HR>\n<h3>Select a Station/Channel</h3>\n<UL>\n";
    $first=1;

    $n="";
    if ($db eq "pfo")
    {
	$n="n";
    }
    foreach $item (`/opt/antelope/4.5p/bin/dbselect /home/rt/db/$db.wfdisc sta chan | sort -u -k1,1 -k2,2$n`)
    {
	chomp($item);
	($sta,$cha,$c1)=split /\s+/,$item;
	$item =~ s/ +/_/g;
	$item =~ s/_$//;
	if ($sta ne $last_sta)
	{
	    if ($first)
	    {
		$first=0;
		print "<LI>$sta\n<UL>\n";
	    }
	    else
	    {
		print "</UL></LI>\n<LI>$sta\n<UL>\n";
	    }
	}
	print "<LI><A HREF=\"waveform.cgi?$db+$item\">$cha</A></LI>\n";
	$last_sta=$sta;
    }
    print "</UL></LI></UL>\n</BODY></HTML>\n";	
}
elsif ($#ARGV == 1)
{
    $db=$ARGV[0];
    $stachan=$ARGV[1];
    ($sta,$chan)=split /\_/,$stachan,2;

    $start=$end=0;

    foreach $item (`/opt/antelope/4.5p/bin/dbsubset /home/rt/db/$db.wfdisc "sta == '$sta' && chan == '$chan'" | /opt/antelope/4.5p/bin/dbselect - time endtime samprate segtype`)
    {
	($c1, $m1,$m2,$samprate,$segtype,$c1)=split /\s+/,$item;
	chomp($segtype);
	if ($segtype eq "")
	{
	    $segtype="NONE";
	}
	if ($start == 0)
	{
	    $start=$m1;
	}
	if ($m1<$start)
	{
	    $start=$m1;
	}
	
	if ($m2>$end)
	{
	    $end=$m2;
	}
    }

    print "Content-type: text/html\nPragma: no-cache\n\n";
    print "<HTML><HEAD><TITLE>ROADNet Waveform Display</TITLE></HEAD>\n<BODY><H1>ROADNet Waveform Display</H1>\n<HR>\n<B>Database:</B> $db<BR>\n<B>Station_Channel:</B> $stachan<BR>\n";
    $c=`/opt/antelope/4.5p/bin/trlookup_segtype $segtype`;
    chomp($c);
    if ($c eq "")
    { $c = "no units"; }
    print "<B>Units:</B> $c<BR>";
    $st_ascii=`/opt/antelope/4.5p/bin/epoch -l $start`;
    chomp($st_ascii);
    $end_ascii=`/opt/antelope/4.5p/bin/epoch -l $end`;
    chomp($end_ascii);
    print "<B>Data starts:</B> $st_ascii<BR>";
    print "<B>Data ends:</B> $end_ascii<BR>";
    $range=($end-$start)/(24*60*60);
    printf("<B>Data Span:</B> %0.3f Days<BR>",$range);

    $latency=(time()-$end)/60/60;
    printf("<B>Data Latency:</B> %0.2f hours<BR>",$latency);
    print "<P><H3>Select a time range to display</h3>\n";
    print "<UL>";
    $cur=$end;
    $range=$cur-5*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 5 min</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-1*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 1 hr</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-6*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 6 hrs</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-12*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 12 hrs</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-24*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 24 hrs</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-48*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 2 days</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-7*24*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 7 days</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    $range=$cur-30*24*60*60;
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype\">Last 30 days</A> (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$range+$cur+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    print "<LI><A HREF=\"waveform.cgi?$db+$stachan+$start+$end+$samprate+$segtype\">All Data (slow)</A> (<A HREF=\"waveform.cgi?$db+$stachan+$start+$end+raw+$samprate+$segtype\">raw</A>) (<A HREF=\"waveform.cgi?$db+$stachan+$start+$end+$samprate+$segtype+filter+filter\">filtered</A>)</LI>";
    print "</UL>\n<HR>\n<H3>Choose your own time frame (PST/PDT)</H3>\n";

    $cur_time=time();
    $emon=`/opt/antelope/4.5p/bin/epoch -l +%m $cur_time`;
    chomp($emon);
    $eday=`/opt/antelope/4.5p/bin/epoch -l +%d $cur_time`;
    chomp($eday);
    $eyear=`/opt/antelope/4.5p/bin/epoch -l +%Y $cur_time`;
    chomp($eyear);
    $ehr=`/opt/antelope/4.5p/bin/epoch -l +%H $cur_time`;
    chomp($ehr);
    $emin=`/opt/antelope/4.5p/bin/epoch -l +%M $cur_time`;
    chomp($emin);
    $esec=`/opt/antelope/4.5p/bin/epoch -l +%S.%s $cur_time`;
    chomp($esec);

    $cur_time-=30*60;

    $smon=`/opt/antelope/4.5p/bin/epoch -l +%m $cur_time`;
    chomp($smon);
    $sday=`/opt/antelope/4.5p/bin/epoch -l +%d $cur_time`;
    chomp($sday);
    $syear=`/opt/antelope/4.5p/bin/epoch -l +%Y $cur_time`;
    chomp($syear);
    $shr=`/opt/antelope/4.5p/bin/epoch -l +%H $cur_time`;
    chomp($shr);
    $smin=`/opt/antelope/4.5p/bin/epoch -l +%M $cur_time`;
    chomp($smin);
    $ssec=`/opt/antelope/4.5p/bin/epoch -l +%S.%s $cur_time`;
    chomp($ssec);

    print "<FORM METHOD=POST ACTION=waveform.cgi?a+b+c><P>Start (mm/dd/yyyy hh:mm:ss.sss): <INPUT TYPE=text NAME=smon VALUE=$smon SIZE=2> <B>/</B> <INPUT TYPE=TEXT NAME=sday VALUE=$sday SIZE=2> <B>/</B> <INPUT TYPE=TEXT NAME=syear VALUE=$syear SIZE=4> <INPUT TYPE=TEXT NAME=shr VALUE=$shr size=2> <B>:</B> <INPUT TYPE=TEXT NAME=smin VALUE=$smin size=2> <B>:</B> <INPUT TYPE=TEXT NAME=ssec VALUE=$ssec size=6></P>";
    print "<P> End (mm/dd/yyyy hh:mm:ss.sss): <INPUT TYPE=text NAME=emon VALUE=$emon SIZE=2> <B>/</B> <INPUT TYPE=TEXT NAME=eday VALUE=$eday SIZE=2> <B>/</B> <INPUT TYPE=TEXT NAME=eyear VALUE=$eyear SIZE=4>  <INPUT TYPE=TEXT NAME=ehr VALUE=$ehr size=2> <B>:</B> <INPUT TYPE=TEXT NAME=emin VALUE=$emin size=2> <B>:</B> <INPUT TYPE=TEXT NAME=esec VALUE=$esec size=6></P>";
    print "Graph Type: <SELECT NAME=type><OPTION>Graph</OPTION><OPTION>Raw</OPTION><OPTION VALUE=\"fil\">Filtered Graph</Option><OPTION>XML</OPTION></SELECT><BR><P>";
    print "<INPUT TYPE=HIDDEN NAME=samprate VALUE=$samprate><INPUT TYPE=HIDDEN NAME=segtype VALUE=$segtype><INPUT TYPE=HIDDEN NAME=db VALUE=$db><INPUT TYPE=HIDDEN NAME=stacha VALUE=$stachan><INPUT TYPE=SUBMIT VALUE=\"Your own time\"></FORM>";
    print "</BODY></HTML>\n";
}
elsif ($#ARGV==2)
{
    require 'cgi-lib.pl';

    &ReadParse;

    $db=$in{'db'};
    $stacha=$in{'stacha'};
    $mon=$in{'smon'};
    $day=$in{'sday'};
    $year=$in{'syear'};
    $hr=$in{'shr'};
    $min=$in{'smin'};
    $sec=$in{'ssec'};
    $time=`/opt/antelope/4.5p/bin/epoch -l $mon/$day/$year $hr:$min:$sec`;
    ($c2,$eps,$c1)=split /\s+/, $time;
    $mon=$in{'emon'};
    $day=$in{'eday'};
    $year=$in{'eyear'};
    $hr=$in{'ehr'};
    $min=$in{'emin'};
    $sec=$in{'esec'};
    $samprate=$in{'samprate'};
    $segtype=$in{'segtype'};
    $type=$in{'type'};
    $time=`/opt/antelope/4.5p/bin/epoch -l $mon/$day/$year $hr:$min:$sec`;
    ($c2,$epe,$c1)=split /\s+/, $time;
    if ($type eq "Raw")
    {
	print "Location: waveform.cgi?$db+$stacha+$eps+$epe+raw+$samprate+$segtype\n\n";
    }
    elsif ($type eq "XML")
    {
	print "Location: waveform.cgi?$db+$stacha+$eps+$epe+xml+$samprate+$segtype\n\n";
    }
    elsif ($type eq "Graph")
    {
	print "Location: waveform.cgi?$db+$stacha+$eps+$epe+$samprate+$segtype\n\n";
    }
    else
    {
	print "Location: waveform.cgi?$db+$stacha+$eps+$epe+$samprate+$segtype+filter+filter\n\n";
    }
}
elsif ($#ARGV==5 || $#ARGV==7)
{
    $db=$ARGV[0];
    $stacha=$ARGV[1];
    ($sta,$chan)=split /_/, $stacha,2;
    $start=$ARGV[2];

    $end=$ARGV[3];
    $samprate=$ARGV[4];
    $segtype=$ARGV[5];
    $samples=($end-$start)*$samprate;
    if ($samples > 3000000)
    {
	print stderr "waveform.cgi Status: 400\n";
	print "Status: 400\nContent-type: text/html\n\n<HTML><HEAD><TITLE>400 Bad Request</TITLE></HEAD><BODY><H1>400 Bad Request</h1><HR><P>You requested $samples samples but no one is authorized for more then 3 million samples per graph.</P></BODY></HTML>\n";
	exit(0);
    }

    if ($samples > 864000 && (!defined $ENV{"REMOTE_USER"}))
    {
	    #print stderr "waveform.cgi Status: 401\n";
	    #print "Status: 401\nContent-type: text/html\n\n<HTML><HEAD><TITLE>401 Unauthorized</TITLE></HEAD><BODY><H1>401 Unauthorized</H1><HR><P>You requested $samples samples but you are not authorized for that many samples per graph. Less than 864,000 samples does not require authorization. To authorize your IP address contact Todd Hansen or your ROADNet representative.</P><PRE>";
	    #print %ENV;
	    #print "</PRE></BODY></HTML>";
	print "Location: /auth/waveform.cgi?$db+$stacha+$start+$end+$samprate+$segtype\n\n";
	exit(0);
    }

    if (($v=`ps ax | grep gnuplot | grep -v grep | grep -v "sh -c" | wc -l`) > 15)
    {
	print stderr "waveform.cgi Status: 503\n";
	print "Status: 503\nContent-type: text/html\n\n<HTML><HEAD><TITLE>503 Waveform Service overloaded</TITLE></HEAD><BODY><H1>503 Waveform Service overloaded, try again later</h1><HR><P>You requested $samples samples of data but you are competing with $v other users and your request was denied due to the number of users, regardless of the size of your request.</P></BODY></HTML>\n";
	exit(0);
    }

    if ($#ARGV==7)
    { $filter=1; }
    else
    { $filter=0; }

    $none=1;
    open(TMP,">/tmp/waveform.$$.dat");
    foreach $item (`/opt/antelope/4.5p/bin/trsample -cot -n $samples -s "sta=='$sta' && chan=='$chan'" /home/rt/db/$db $start $end`)
    {
	$none=0;
	chomp($item);
	@array=split /\s+/, $item;

	if ($#array==1)
	{
	    $time=epoch2str($array[0],"%d/%m/%Y.%H:%M:%S.%s");
	    if ($filter == 0 || abs($array[1])<=32767)
	    {
		if (defined $orig_time && ($array[0]-$orig_time) > (1/$samprate)*1.5 )
		{
			print TMP "\n";	
		}
		print TMP "$time $array[1]\n";
		$orig_time=$array[0];
	    }
	    else
	    {
		print TMP "\n";
	    }
	}
    }
    close(TMP);

    if ($none==0)
    {
	$str = "Content-type: image/png\nPragma: no-cache\n\n";
	open(FOO,">/dev/stdout");
	syswrite(FOO,$str,42);
	close(FOO);
	
	open(GIF, "| /usr/bin/gnuplot > /dev/stdout");

	$time=epoch2str($start,"%m/%d/%Y");

	$c=`/opt/antelope/4.5p/bin/trlookup_segtype $segtype`;
	chomp($c);
	if ($c eq "")
	{	
	    $c="no units";
	}
	print GIF "set ylabel \"$c\"\n";
	print GIF "set timefmt \"%d\/%m\/%Y.%H:%M:%S\"\n";
	print GIF "set xdata time\n";
	print GIF "set xtics rotate autofreq\n";
	if ($end-$start > 24*3*60*60)
	{
	    print GIF "set format x \" %m/%d/%y\"\n";
	    if ($filter)
	    {
		print GIF "set title \"$db $stacha (filtered)\"\n";
	    }
	    else
	    {
		print GIF "set title \"$db $stacha\"\n";
	    }
	}
	else
	{
	    print GIF "set format x \" %H:%M\"\n";
	    if ($filter)
	    {
		print GIF "set title \"$db $stacha filtered (start: $time)\"\n";
	    }
	    else
	    {
		print GIF "set title \"$db $stacha (start: $time)\"\n";
	    }
	}
	print GIF "set data style lines \n";
	print GIF "set xlabel \"Time GMT\"\n";
	print GIF "set size 1,0.6\n";
	print GIF "set terminal png color\n";
	print GIF "plot \"/tmp/waveform.$$.dat\" using 1:2 notitle 3\n";
	close GIF;

    }
    else
    {
	print "Content-type: text/plain\nPragma: no-cache\n\n";
	print "No Data Available for this time range\n";
    }

    unlink("/tmp/waveform.$$.dat");
}
elsif ($#ARGV==6)
{
    $db=$ARGV[0];
    $stacha=$ARGV[1];
    ($sta,$chan)=split /_/, $stacha, 2;
    $start=$ARGV[2];
    $end=$ARGV[3];
    $raw=$ARGV[4];
    $samprate=$ARGV[5];
    $segtype=$ARGV[6];

    $samples=(24*60*60)*$samprate;
    
    if ($raw eq "raw")
    {
	print "Content-type: text/plain\nPragma: no-cache\n\n";
	$c=`/opt/antelope/4.5p/bin/trlookup_segtype $segtype`;
	chomp($c);
	if ($c eq "")
	{
	    $c="no units";
	}
	print "#Units = $c\n";
    }
    else
    {
	print "Content-type: text/xml\nPragma: no-cache\n\n";
    }
    $ENV{"PFPATH"}="/opt/antelope/4.5p/data/pf:/home/rt/pf";
    print `/var/Web/xml_get.pl $raw /home/rt/db/$db $sta $chan $start $end $samples`;

}

