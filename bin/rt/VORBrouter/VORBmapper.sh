: # use perl
eval 'exec $ANTELOPE/bin/perl -S $0 "$@"'
if 0;

use lib "$ENV{ANTELOPE}/data/perl" ;
use orb;
use Datascope;
use Storable qw(dclone);
require "getopts.pl";

# Copyright (c) 2003 The Regents of the University of California
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
#   Updated By: Todd Hansen 10/24/2003

$VERSION="\$Revision: 1.3 $";

$orbname=":";
$verbose=0;
$UUID=4;
elog_init ($0, @ARGV);
$lastchangetime=0;

srand;
$changenum=int(rand 1000);

if( ! &Getopts('vVu:o:') || @ARGV != 0 ) 
{
    die( "Usage: VORBmapper [-v] [-V] [-u UUID] [-o orbname]\n" );
}
else 
{
    if ($opt_V)
    {
	die ("VORBMapper $VERSION\n\n\tVORBmapper [-v] [-V] [-u UUID] [-o orbname]\n\n\tTodd Hansen\n\tUCSD ROADNet Project\n\n\tPlease report problems to: tshansen@ucsd.edu\n\n");
    }
    if ($opt_v)
    {
	$verbose=1;
    }
    if ($opt_u)
    {
	$UUID=$opt_u;
    }
    if ($opt_o)
    {
	$orbname=$opt_o;
    }
}

%LSPhash;
%n;
%t;

$orb=orbopen($orbname,"r&") || die "unable to open orb $orbname\n";
$orbfd_out = orbopen( $orbname, "w&" ) || die "unable to open output orb $orbname\n";

orbselect($orb,"/pf/VORBrouter");

if (!-d "VORBmapper")
{
    `mkdir VORBmapper`;
}
if (!-d "connection")
{
    `mkdir connection`;
}

while (1)
{    
    ($pktid, $srcname, $time, $pkt, $nbytes) = orbreap($orb);
    ($result, $packet) = unstuffPkt( $srcname, $time, $pkt, $nbytes );
    if( $result ne "Pkt_pf" ) 
    {
	if (verbose)
	{
	    printf stderr "Received a $result, skipping\n";
	}
    }
    elsif (pfget($packet->pf,"Version") != 0)
    {
	printf(stderr "wrong packet version from $srcname, ignoring\n");
    }
    elsif (pfget($packet->pf,"Type") == 8)
    {
	$lspUUID=pfget($packet->pf,"UUID");
	if ($verbose)
	{
	    printf(stderr "got an LSP packet from $lspUUID\n");
	}

	if (pfget($packet->pf,"Creation")>20*60+time())
	{
	    printf(stderr "$lspUUID sent us a packet > 20 min in future, ignoringing.\n");
	}
	elsif (defined $LSPhash{$lspUUID})
	{
	    if ($LSPhash{$lspUUID}{'creation'}<pfget($packet->pf,"Creation"))
	    {
		undef $LSPhash{$lspUUID};
		$LSPhash{$lspUUID}{'string'}=pf2string($packet->pf);
		$LSPhash{$lspUUID}{'creation'}=pfget($packet->pf,"Creation");
		$s=pfget($packet->pf,"ActNeigh");
		%s=%{$s};
		foreach $i (keys %s)
		{
		    $LSPhash{$lspUUID}{"neigh"}{$i}=$s{$i};
		}
		
		$s=pfget($packet->pf,"selects");
		$lcv=0;
		foreach $i (@{$s})
		{
		    $LSPhash{$lspUUID}{"selects"}[$lcv]=$i;
		    $lcv++;
		}		

		if (defined $LSPhash{$UUID})
		{
		    %n=();
		    %t=();
		    &regen_routing();
		    &check_changes();
		}
		elsif (verbose)
		{
		    printf stderr "can\'t generate route table without LSP from my node\, got $lspUUID\n";
		}
	    }
	    elsif (verbose)
	    {
		printf(stderr "$lspUUID ctl packet old, ignoring (%f vs new %f)\n",$LSPhash{$lspUUID}{'creation'},pfget($packet->pf,"Creation"));
	    }
	}
	else
	{
	    undef $LSPhash{$lspUUID};
	    $LSPhash{$lspUUID}{'string'}=pf2string($packet->pf);
	    $LSPhash{$lspUUID}{'creation'}=pfget($packet->pf,"Creation");
	    $s=pfget($packet->pf,"ActNeigh");
	    %s=%{$s};
	    foreach $i (keys %s)
	    {
		$LSPhash{$lspUUID}{"neigh"}{$i}=$s{$i};
	    }
	    
	    $s=pfget($packet->pf,"selects");
	    $lcv=0;
	    foreach $i (@{$s})
	    {
		$LSPhash{$lspUUID}{"selects"}[$lcv]=$i;
		$lcv++;
	    }

	    if (defined $LSPhash{$UUID})
	    {
		%n_o=%n;
		%t_o=%t;
		undef %n;
		undef %t;
		%n;
		%t;
		&regen_routing();
		&check_changes();
	    }
	    elsif (verbose)
	    {
		printf stderr "can\'t generate route table without LSP from my node\, got $lspUUID\n";
	    }
	}
    }
}

sub regen_routing
{
    foreach $cUUID (keys %LSPhash)
    {
	if ($LSPhash{$cUUID}{'creation'}>time()-5*60)
	{
	    %s=%{$LSPhash{$cUUID}{'neigh'}};
	    foreach $i (keys %s)
	    {
		if (!defined $n{$cUUID}{"neigh"}{$i} || $n{$cUUID}{"neigh"}{$i}<$s{$i}+$curmetric)
		{
		    $n{$cUUID}{"neigh"}{$i}=$s{$i};
		}
	    }
	}	    	    

	if ($LSPhash{$cUUID}{'creation'}>time()-2*24*60*60)
	{
	    $lcv=0;
	    foreach $i (@{$LSPhash{$cUUID}{'selects'}})
	    {
		$n{$cUUID}{"selects"}[$lcv]=$i;
		$lcv++;
	    }
	}
    }

    &trapse($UUID,0,"","");
}

sub trapse
{
    ($cUUID,$metric,$hops,$next)=@_;

    if (defined $n{$cUUID}{"visited"})
    {
	return;
    }

    $n{$cUUID}{"visited"}=1;

    foreach $i (keys %{$n{$cUUID}{"neigh"}})
    {
	if (!defined $t{$i} || $t{$i}{"metric"}>$n{$cUUID}{"neigh"}{$i}+$metric)
	{
	    $t{$i}{"metric"}=$n{$cUUID}{"neigh"}{$i}+$metric;
	    if ($next eq "")
	    {
		$t{$i}{"nexthop"}=$i;
		$t{$i}{"hops"}="$i";
	    }
	    else
	    {
		$t{$i}{"nexthop"}=$next;
		$t{$i}{"hops"}="$hops, $i";
	    }
	} 
	if ($next eq "")
	{
	    &trapse($i,$metric+$n{$cUUID}{"neigh"}{$i},$i,$i);
	}
	else
	{
	    &trapse($i,$metric+$n{$cUUID}{"neigh"}{$i},"$hops, $i",$next);	    
	}
    }    
}

sub check_changes
{
    $c=0;    

    foreach $cUUID (keys %n)
    {
	foreach $s (@{$n{$cUUID}{"selects"}})
	{
	    $c2=1;
	    foreach $d (@{$n_o{$cUUID}{"selects"}})
	    {
		if ($s eq $d)
		{
		    $c2=0;
		}
	    }
	    
	    if ($c2)
	    { $c=1; }
	}
    }

    if ($c==0)
    {
	foreach $cUUID (keys %t)
	{
	    if ($cUUID != $UUID)
	    {
		if ($t_o{$cUUID}{"nexthop"} != $t{$cUUID}{"nexthop"})
		{ $c=1 };
	    }
	}
    }
	
    if ($c==1)
    { 
	$changnum++; 
	if ($changenum>1000)
	{ $changenum=0; }
    }

    if ($c==1 || $lastchangetime<now()-3*60)
    {
	$lastchangetime=now();
	if (verbose)
	{
	    printf stderr "updating route table $changenum\n";
	}
	
	$p = "Version\t0\n";
	$p .= "Type\t9\n";
	$p .= "UUID\t$UUID\n";
	$p .= "lastUUID\t$UUID\n";
	$t=time();
	$p .= "Creation\t$t\n";
	$p .= "ChangeNumber\t$changenum\n";
	
	$p .= "\nrequests\t&Arr{\n";
	foreach $cUUID (keys %n)
	{
	    $p .= "\t$cUUID\t&Arr{\n\t\tregex\t&Tbl{\n";
	    foreach $s (@{$n{$cUUID}{"selects"}})
	    {
		$p .= "\t\t\t$s\n"; 
	    }
	    $p .= "\t\t}\n\t}\n";
	    
	}
	$p .= "}\n";
	
	$p .= "routes\t&Arr{\n";
	$p .= "\t# dst next_hop\n";
	foreach $cUUID (keys %t)
	{
	    if ($cUUID != $UUID)
	    {		
		$nh=$t{$cUUID}{"nexthop"};
		$p .= "\t$cUUID\t$nh\n";
	    }
	}
	$p .= "}\n";
	
	$p .= "route_detail\t&Arr{\n";
	$p .= "\t# dst metric hops\n";
	foreach $cUUID (keys %t)
	{
	    if ($cUUID != $UUID)
	    {
		$nh=$t{$cUUID}{"hops"};
		$m=$t{$cUUID}{"metric"};
		$p .= "\t$cUUID\t$m\t$nh\n";
	    }
	}
	$p .= "}\n";

    open(FH,">VORBmapper/VORBrouter.pf");
    print FH $p;
    close(FH);
    `cd VORBmapper; pf2orb VORBrouter $orbname`;
    }
}
