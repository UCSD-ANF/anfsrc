use orb;
use Datascope;
use Socket;
require "getopts.pl";

$VERSION="\$Revision: 1.2 $\ ";

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
#   Updated By: Todd Hansen 8/16/2004

$orbname=":";
$twin=3;

if( ! &Getopts('Vw:o:') || @ARGV != 0 ) 
{
    die( "Usage: orbtopo_db [-V] [-w timewindow] [-o orbname]\n" );
}
else 
{
    if ($opt_V)
    {
        die ("orbtopo_db $VERSION\n\n\torbtopo_db [-V] [-w timewindow] [-o orbname]\n\n\tTodd Hansen\n\tUCSD ROADNet Project\n\n\tPlease report problems to: tshansen@ucsd.edu\n\n");
    }
   
    if ($opt_w)
    {
	$twin=$opt_w;
    }

    if ($opt_o)
    {
	$orbname=$opt_o;
    }
}
$orb=orbopen($orbname,"r&");

$n = orbselect ($orb, ".*/pf/orbstat");

orbseek($orb,"ORBOLDEST");

$done=0;

while ($done==0)
{

    ($pktid, $srcname, $time, $packet, $nbytes) = orbreap_timeout($orb,20);
    if (defined ($pktid) && $packet !~ /^\s*$/)
    {
	if ($time > time()-$twin*60*60)
	{
	    $hash{$srcname}=$packet;
	    $timehash{$srcname}=$time;
	    $bytehash{$srcname}=$nbytes;
	}
    }
    else
    {
	$done=1;
    }
}

orbclose($orb);


foreach $srcname (keys %hash)
{
    ($srcnameip,$srcnameport)=split /:/, $srcname;
    ($srcnameport,$c1)=split /\//,$srcnameport;
    if ($srcnameport eq "")
    { $srcnameport = "6510"; }
    $s2=$srcnameip;
    $srcnameip=inet_aton($srcnameip);
    $srcnameip=gethostbyaddr($srcnameip, AF_INET);
    if ($srcnameip eq "")
    { $srcnameip = $s2; }
    $packet=$hash{$srcname};
    $time=$timehash{$srcname};
    $nbytes=$bytehash{$srcname};

    ($result, $pkt) = unstuffPkt($srcname,$time,$packet,$nbytes);
    
    if (!defined $pkt)
    {
#	print "$packet\n";
#	print "$result exit $srcname $time\n";
#	exit(-1);
    }
    else	
    {
    ($type, $desc) = $pkt->PacketType();

    if ($type!=Pkt_pf)
    {
	print stderr "wrong packet type in $srcname (expected Pkt_pf)\n";
    }
    else
    {
	($net, $sta, $chan, $loc, $suffix, $subcode) = $pkt->parts() ;
	$pf = $pkt->pf;
	foreach $i (pfget($pf,"clients"))
	{
	    foreach $j (keys %{$i})
	    {
		%k=%{$i};
		if ($k{$j}{"what"} =~  /orb2db/ && $k{$j}{"what"} !~ /orb2dbt/)
		{
			$line=$k{$j}{"what"};
			$addr=$k{$j}{"address"};
			$p_addr=$k{$j}{"port"};
	
			@list=split /\s+/,$line;
			$first=1;			
			$skip_next=-1;
			foreach $i (@list)
			{
				if ($i =~ /orb2db/)
				{
					$skip_next=1;
				}

				if ($i =~ /^-v/)
				{
				    $skip_next=1;
				}
			    	elsif ($i =~ /^-/)
			    	{
				    $skip_next=2;
			    	}
	
				if ($first<0)
				{
					$skip_next=1;
				}
				
				if ($skip_next==0)
				{
				    if ($first)
				    {
					($host,$port)=split /:/, $i;
				    }	
				    else
				    {
					$host=$addr;
					$port=$p_addr;
				    }
				    
				    if (($host =~ /^[\s\n]*$/) || $host eq "127.0.0.1" || $host eq "localhost" || $host eq "")
				    {
					$host="$addr";
					if (($host =~ /^[\s\n]*$/) || $host eq "127.0.0.1" || $host eq "localhost" || $host eq "") 
					{
					    $host=$srcnameip;
					}
					
					if ($host =~ /^\d+\.\d+\.\d+\.\d+/)
					{
					    $host2=$host;
					    $host=inet_aton($host);
					    $host=gethostbyaddr($host, AF_INET);
					    if ($host eq "")
					    {$host=$host2;}
					}
					else
					{
					    $host2=$host;
					    ($name,$aliases,$addrtype,$length,@addrs) = gethostbyname($host);
					    $host=gethostbyaddr($addrs[0], AF_INET);
					    if ($host eq "")
					    {$host=$host2;}
					}
				    }
				    elsif ($host =~ /^\d+\.\d+\.\d+\.\d+/)
				    {
					$host2=$host;
					$host=inet_aton($host);
					$host=gethostbyaddr($host, AF_INET);
					if ($host eq "")
					{$host=$host2;}
				    }
				    else
				    {
					$host2=$host;
					
					($name,$aliases,$addrtype,$length,@addrs) = gethostbyname($host);
					
					$host=gethostbyaddr($addrs[0], AF_INET);
					if ($host eq "")
					{$host=$host2;}			    
				    }
				    
				    if ($port =~ /^[\s\n]*$/)
				    { $port=6510; }
				    
				    if ($port =~/^\d+$/)
				    {  
					foreach $portname (`pfecho orbserver_names | egrep \"\s*$port\s*\"`)
					{
					    if ($portname =~ /\s+$port\s+/)
					    {
						($port,$mold)=split /\s+/,$portname;
					    }
					}
				    }
				    
				    if (!defined $whats{$k{$j}{"what"}})
				    {
					$host=~s/\./_/g;
					if ($first==1)
					{
					    $hosts{$host}{$port}="orb";
					    $t= "\t\"$host:$port\" -> ";
					}
					elsif ($first==0)
					{
					    $latency=strtdelta($k{$j}{"latency_sec"});
					    $db{$host}{$i}="db";
					    $output.= "$t\"$host:$i\" [color=blue, label=\"$latency\"]\n";
					    $whats{$k{$j}{"what"}}=1;
					}
					$first--;
				    }
				}
				
				if ($skip_next != 0)
				{
				    $skip_next--;
				}
			    }
		    }

		if ($k{$j}{"what"} =~  /orb2orb/)
		{
		    $line=$k{$j}{"what"};
		    $addr=$k{$j}{"address"};
		    $p_addr=$k{$j}{"port"};
		    if (!($addr eq  $srcnameip || $addr eq "127.0.0.1"))
		    {
			@list=split /\s+/,$line;
			$first=1;
			$skip_next=-1;
			foreach $i (@list)
			{
			    if ($i =~ /orb2orb/)
			    {
				$skip_next=1;
			    }

			    if ($i =~ /^-[dflUvx]/)
			    {
				$skip_next=1;
			    }
			    elsif ($i =~ /^-/)
			    {
				$skip_next=2;
			    }

			    if ($first<0)
			    {
				$skip_next=1;
			    }

			    if ($skip_next == 0)
			    {
				($host,$port)=split /:/, $i;
				if (($host =~ /^[\s\n]*$/) || $host eq "127.0.0.1" || $host eq "localhost" || $host eq "")
				{
				    $host="$addr";
				    if (($host =~ /^[\s\n]*$/) || $host eq "127.0.0.1" || $host eq "localhost" || $host eq "") 
				    {
					$host=$srcnameip;
				    }
				    
				    if ($host =~ /^\d+\.\d+\.\d+\.\d+/)
				    {
					$host2=$host;
					$host=inet_aton($host);
					$host=gethostbyaddr($host, AF_INET);
					if ($host eq "")
					{$host=$host2;}
				    }
				    else
				    {
					$host2=$host;
					($name,$aliases,$addrtype,$length,@addrs) = gethostbyname($host);
					$host=gethostbyaddr($addrs[0], AF_INET);
					if ($host eq "")
					{$host=$host2;}			    
				    }
				}
				elsif ($host =~ /^\d+\.\d+\.\d+\.\d+/)
				{
				    $host2=$host;
				    $host=inet_aton($host);
				    $host=gethostbyaddr($host, AF_INET);
				    if ($host eq "")
				    {$host=$host2;}
				}
				else
				{
				    $host2=$host;

				($name,$aliases,$addrtype,$length,@addrs) = gethostbyname($host);

				$host=gethostbyaddr($addrs[0], AF_INET);
				   # $v=`dig -nomultiline $host | grep $host | grep -v ";"`;
				   # chomp($v);
				   # ($c1,$c2,$c3,$c4,$host,$c5)=split /\s+/, $v;
				   # $host=inet_aton($host);
				   # $host=gethostbyaddr($host, AF_INET);

				    if ($host eq "")
				    {$host=$host2;}			    
				}
			    
				if ($port =~ /^[\s\n]*$/)
				{ $port=6510; }
				
				if ($port =~/^\d+$/)
				{
				    foreach $portname (`pfecho orbserver_names | egrep \"\s*$port\s*\"`)
				    {
					if ($portname =~ /\s+$port\s+/)
					{
					    ($port,$mold)=split /\s+/,$portname;
					}
				    }
				}
				$host=~s/\./_/g;
				if ($first)
				{
				    $hosts{$host}{$port}="orb";
				    $t= "\t\"$host:$port\" -> ";
				}
				elsif ($first==0)
				{
				    $latency=strtdelta($k{$j}{"latency_sec"});
				    $hosts{$host}{$port}="orb";
				    $output.= "$t \"$host:$port\" [color=blue, label=\"$latency\"]\n";
				}
				$first--;
			    }
			    
			    if ($skip_next!=0)
			    {
				$skip_next--;
			    }
			}
		    }
		}
	    }
	}
	}
    }
}

#open(FOO,">/dev/stdout");
#syswrite FOO, "Content-type: image/gif\nPragma: no-cache\n\n";
#syswrite FOO, "Content-type: text/plain\nPragma: no-cache\n\n";
#close(FOO);

#open(FOO,"|/usr/local/bin/dot -Tgif -o /dev/stdout 2>/dev/null");
open(FOO,">/dev/stdout");
print FOO "Digraph orbtopo {\n";

foreach $host (keys %hosts)
{
    foreach $port (keys %{$hosts{$host}})
    {
        print FOO "\t\"$host:$port\" [shape=hexagon,style=filled,fillcolor=lightgoldenrod1]\n";
    }
}

foreach $host (keys %db)
{
    foreach $ldb (keys %{$db{$host}})
    {
        print FOO "\t\"$host:$ldb\" [shape=doubleoctagon,style=filled,fillcolor=lightgoldenrod1]\n";
    }
}

print FOO "$output";
print FOO "}\n";
close(FOO);
