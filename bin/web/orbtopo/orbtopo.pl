#!/opt/antelope/4.5p/bin/perl

use lib "/opt/antelope/4.5p/data/perl" ;

use orb;
use Datascope;
use Socket;

$orb=orbopen(":","r&");

$n = orbselect ($orb, ".*/pf/orbstat");

orbseek($orb,"ORBOLDEST");

$done=0;

while ($done==0)
{

    ($pktid, $srcname, $time, $packet, $nbytes) = orbreap_timeout($orb,12);
    if (defined $pktid)
    {
	if ($time > time()-2*60*60)
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
	print "$result exit $srcname\n";
	exit(-1);
    }

    ($type, $desc) = $pkt->PacketType() ;

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
			    
			    if ($i =~ /^-/)
			    {
				$skip_next=2;
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
				    $v=`dig -nomultiline $host | grep $host | grep -v ";"`;
				    chomp($v);
				    ($c1,$c2,$c3,$c4,$host,$c5)=split /\s+/, $v;
				    $host=inet_aton($host);
				    $host=gethostbyaddr($host, AF_INET);
				    if ($host eq "")
				    {$host=$host2;}			    
				}
			    
				if ($port =~ /^[\s\n]*$/)
				{ $port=6510; }
				
				if ($port =~/^\d+$/)
				{
				    foreach $portname (`egrep \"\s*$port\s*\" /opt/antelope/4.5p/data/pf/orbserver_names.pf`)
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
				    $output.= "\t\"$host:$port\" -> ";
				}
				elsif ($first==0)
				{
				    $hosts{$host}{$port}="orb";
				    $output.= "\"$host:$port\" [color=blue]\n";
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

print FOO "$output";
print FOO "}\n";
close(FOO);
