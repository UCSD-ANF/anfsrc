use IPC::Open2;
require "getopts.pl";

$VERSION="\$Revision: 1.4 $\ ";

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
#   Written By: Todd Hansen 10/15/2003
#   Updated By: Todd Hansen 8/9/2004

$address="";
$reject="";
$match="";
$timeout=3*60; # minutes
$orbname=":";
$nailpath="";
$checkinterval=30; # minutes
$subject="";
$tmpfiledir="/tmp";
$graphvizdir="";

if( ! &Getopts('Vg:x:r:m:o:t:d:s:n:c:') || @ARGV != 0 ) 
{
    die( "Usage: map_changes [-V] [-o orbname] [-m match] [-r reject] [-t latencytimeout] [-d tmpfiledir] [-s emailsubject] [-n nailpath] [-g graphvizpath] [-c checkinterval] -x \"emailaddr(s)\"\n" );
}
else 
{
    if ($opt_V)
    {
        die ("map_changes $VERSION\n\n\tmap_changes [-V] [-o orbname] [-m match] [-r reject] [-t latencytimeout] [-d tmpfiledir] [-s emailsubject] [-n nailpath] [-g graphvizpath] [-c checkinterval] -x \"emailaddr(s)\"\n\n\tTodd Hansen\n\tUCSD ROADNet Project\n\n\tPlease report problems to: tshansen@ucsd.edu\n\n");
    }

    if ($opt_o)
    {
	$orbname=$opt_o;
	$subject="$orbname";
    }

    if (!$opt_x)
    {
      print "option -x required\n";	
      die( "Usage: map_changes [-V] [-o orbname] [-m match] [-r reject] [-t latencytimeout] [-d tmpfiledir] [-s emailsubject] [-n nailpath] [-g graphvizpath] [-c checkinterval] -x \"emailaddr(s)\"\n" );
    }
    $address=$opt_x;
    
    if ($opt_n)
    {
	$nailpath="$opt_n/";
    }

    if ($opt_g)
    {
	$graphvizpath="$opt_g/";
    }

    if ($opt_s)
    {
	$subject=$opt_s;
    }

    if ($opt_d)
    {
	$tmpfiledir=$opt_d;
    }

    if ($opt_t)
    {
	$timeout=$opt_t;
    }

    if ($opt_r)
    {
	$reject="\'-r $opt_r\'";
    }

    if ($opt_m)
    {
	$match="-m \'$opt_m\'";
    }
}

$ORBSTATSTR="orbstat $match $reject -s $orbname";
$timeout*=60;

while (1)
{
    undef @logs;
    undef @routers;
    undef @routes;
    undef @srcgood;
    undef @srcbad;
    @history=`cat $tmpfiledir/most_recent_$orbname.dot`;
    `cp $tmpfiledir/most_recent_$orbname.dot $tmpfiledir/previous_$orbname.dot`; 
    @current=`orbtopo_db -o $orbname > $tmpfiledir/most_recent_$orbname.dot; cat $tmpfiledir/most_recent_$orbname.dot`;
    
    foreach $line (@history)
    {
	if ($line !~ /^Digraph/ && $line !~ /^\}/ && $line !~ /->/)
	{
	    chomp($line);
	    ($c1,$name,$c2)=split /\s+/,$line;
	    $found=0;
	    foreach $l2 (@current)
	    {
		if ($l2 =~ /$name/ && $l2 !~ /->/)
		{
		    $found=1;
		}
	    }
	    if ($found == 0)
	    {
#		push(@routers, "\t$name [shape=diamond,style=filled,fillcolor=red]\n");
		$line=~s/\]/,fillcolor=red\]/;
		push(@routers, "\t$line\n");
		if ($line =~ /hexagon/)
		{
		    push(@logs,"Site $name is no longer connected\n");
		}
		else
		{
		    push(@logs,"Database $name is no longer connected\n");
		}
	    }
	    else
	    {
		push(@routers, $line);
	    }
	}
	elsif ($line !~ /^Digraph/ && $line !~ /^\}/)
	{
	    ($c1,$name,$c2,$name2,$c3)=split /\s+/,$line;	    
	    $found=0;
	    foreach $l2 (@current)
	    {
		if ($l2 =~ /$name\s+->\s+$name2/)
		{
		    $found=1;
		}
	    }
	    
	    if ($found == 0)
	    {
	#	push(@routes,"\t$name -> $name2 [color=red]\n");
		$line=~s/\]/,color=red\]/;
		push(@routes, "\t$line\n");
		push(@logs,"Data Transfer Down: $name -> $name2\n");
	    }
	    else
	    {
		push(@routes,$line);
	    }
	}
    }
    
    foreach $line (@current)
    {
	if ($line !~ /^Digraph/ && $line !~ /^\}/ && $line !~ /->/)
	{
	    chomp($line);
	    ($c1,$name,$c2)=split /\s+/,$line;
	    $found=0;
	    foreach $l2 (@history)
	    {
		if ($l2 =~ /$name/ && $l2 !~ /->/)
		{
		    $found=1;
		}
	    }
	    
	    if ($found==0)
	    {
		$line=~s/\]/,fillcolor=green\]/;
#		push(@routers, "\t$name [shape=diamond,style=filled,fillcolor=green]\n");
		push(@routers, "\t$line\n");
		if ($line =~ /hexagon/)
		{
		    push(@logs,"New site visible: $name\n");
		}
		else
		{
		    push(@logs,"New database visible: $name\n");
		}
	    }
	    
	}
	elsif ($line !~ /^Digraph/ && $line !~ /^\}/)
	{
	    ($c1,$name,$c2,$name2)=split /\s+/,$line;	    
	    $found=0;
	    foreach $l2 (@history)
	    {
		if ($l2 =~ /$name\s+->\s+$name2/)
		{
		    $found=1;
		}
	    }
	    
	    if ($found==0)
	    {
#		push(@routes,"\t$name -> $name2 [color=green]\n");
		$line=~s/\]/,color=green\]/;
		push(@routes, "\t$line\n");
		push(@logs,"Data Transfer Up: $name -> $name2\n");
	    }
	}
    }    
    
    if (defined @logs)
    {
	$dot="dot";
	open(DESIGN, "| $graphvizdir$dot -Tgif -o $tmpfiledir/status.$$.gif 2> /dev/null");
	print DESIGN "Digraph \"Route Status\" {\n";
	print DESIGN "\trankdir=\"LR\";\n";
	foreach $line (@routers)
	{
	    print DESIGN $line;
	}
	foreach $line (@routes)
	{
	    print DESIGN $line;
	}
	print DESIGN "}\n";
	
	close(DESIGN);    
	
	sleep(3);
	$nail="nail";
	open(MAIL, "|$nailpath$nail -a $tmpfiledir/status.$$.gif -s \"$subject Topology Change\" $address 2>  /dev/null");
	print MAIL "The following topology changes have been detected:\n\n";
	$lcv=1;
	foreach $l (@logs)
	{
	    print MAIL "$lcv. $l\n";
	    $lcv++;
	}    

	print MAIL "See the attached image for the current topology.\n";
	close(MAIL);
	
	sleep (20);
	unlink("$tmpfiledir/status.$$.gif");
    }

    $y=`date +%Y`;
    $ct=time()-$timeout;
    chomp($y);

    foreach $l (`$ORBSTATSTR`)
    {
	chomp($l);
	if ($l =~ /^\S+\/\S+/)
	{
	    @A=split /\s+/, $l;
	    $t=`epoch $y-$A[8] $A[9]`; 
	    ($c1,$t,$c1)=split /\s+/,$t;
	    if ($t < $ct)
	    {
		push(@srcbad,$A[0]);
		$srcbad_lag{$A[0]}=$ct-$t+$timeout;
	    }
	    else
	    {
		push(@srcgood,$A[0]);
	    }
	}
    }
    

    undef @logs;
    $lcv=1;
    foreach $i (@srcbad)
    {
	if (`grep \"$i \" $tmpfiledir/srcoutage_$orbname.dat | wc -l`!=1)
	{
	    $g=sprintf("%.2f",$srcbad_lag{$i}/60/60);
	    push(@logs,"$lcv $i is out dated. ($g hr latency)\n");
	    $lcv++;
	}
    }

    undef %srcbad_lag;


    foreach $i (@srcgood)
    {
	if (`grep \"$i \" $tmpfiledir/srcoutage_$orbname.dat | wc -l`!=0)
	{
	    push(@logs,"$lcv $i is now up arriving.\n");
	    $lcv++;
	}
    }

    @outs =`cat $tmpfiledir/srcoutage_$orbname.dat`;
    foreach $i (@outs)
    {
       chomp($i);
       $i =~ s/\s+$//;
       $l=0;
       foreach $i2 (@srcgood)
       {
         if ($i2 =~ /$i$/)
	 {
	     $l=1;
         }
       }

       if ($l == 0)
       {
		foreach $i2 (@srcbad)
		{
			if ($i2 =~ /$i$/)
			{
				$l=1;
			}
		}
        }

	if ($l == 0)
  	{
		push(@logs,"$lcv $i is no longer contained in the ORB.\n");
		$lcv++;
	}
    }

    if (defined @logs)
    {
	$nail="nail";
	open(MAIL, "|$nailpath$nail -s \"$subject Data Change\" $address");
	print MAIL "The following data availability changes have been detected:\n\n";
	print MAIL @logs;
	close(MAIL);
    }

    open(FOO,">$tmpfiledir/srcoutage_$orbname.dat");
    foreach $i (@srcbad)
    {
	print FOO "$i \n";
    }
    print FOO "\n";
    close(FOO);
    
    sleep($checkinterval*60);
}
    
