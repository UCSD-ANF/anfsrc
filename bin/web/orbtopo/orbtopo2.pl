#!/opt/antelope/4.5p/bin/perl

use lib "/opt/antelope/4.5p/data/perl" ;

use orb;
use Datascope;
use Socket;

$twin=now()-6*60*60;

foreach $i (`dbsubset ~rt/db/ucsd_orbregistry.connections "when >= '$twin'" | dbselect - fromaddress fromport toaddress toport latency_sec`)
{
    ($fromaddress,$fromport,$toaddress,$toport,$latency)=split /\s+/, $i;
    ($fromaddresso,$fromporto,$toaddresso,$toporto,$latencyo)=split /\s+/, $i;

    $srcnameip=$fromaddress;
    $srcnameip=inet_aton($srcnameip);
    $srcnameip=gethostbyaddr($srcnameip, AF_INET);
    if ($srcnameip ne "")
    { $fromaddress=$srcnameip; }

    $srcnameip=$toaddress;
    $srcnameip=inet_aton($srcnameip);
    $srcnameip=gethostbyaddr($srcnameip, AF_INET);
    if ($srcnameip ne "")
    { $toaddress=$srcnameip; }

    foreach $portname (`egrep \"\s*$fromport\s*\" /opt/antelope/4.5p/data/pf/orbserver_names.pf`)
    {
	if ($portname =~ /\s+$fromport\s+/)
	{
	    ($fromport,$mold)=split /\s+/,$portname;
	}
    }

    foreach $portname (`egrep \"\s*$toport\s*\" /opt/antelope/4.5p/data/pf/orbserver_names.pf`)
    {
	if ($portname =~ /\s+$toport\s+/)
	{
	    ($toport,$mold)=split /\s+/,$portname;
	}
    }

    $hosts{"$fromaddress:$fromport"}="$fromaddresso:$fromporto";
    $hosts{"$toaddress:$toport"}="$toaddresso:$toporto";
    $latency=strtdelta($latency);
    $conn{"$fromaddress:$fromport->$toaddress:$toport"}="\"$fromaddress:$fromport\" -> \"$toaddress:$toport\" [color=blue, label=\"$latency\"]";
}
print "Digraph orbtopo {\n";
foreach $i (keys %hosts)
{
    ($ip,$port)=split /:/,$hosts{$i};
    $v=`dbsubset ~rt/db/ucsd_orbregistry.servers "serveraddress=='$ip' && serverport=='$port' && when >= '$twin'" | dbselect - maxdata`;
    chomp($v);
    if ($v > 0)
    {
    	$f=sprintf("\\n%.2f MB", $v/1024.0/1024.0);
    }
    else
    {
	$f="";
    }
    print "\t\"$i\" [shape=hexagon,style=filled,fillcolor=lightgoldenrod1, label=\"$i$f\"]\n";
}
foreach $i (keys %conn)
{
    print "\t";
    print $conn{$i};
    print "\n";
}
print "}\n";
