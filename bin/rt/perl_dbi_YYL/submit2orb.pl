#!/opt/antelope/4.8/bin/perl

use lib "/opt/antelope/4.8/data/perl";
use orb;


$orb = orbopen($ARGV[0],"w&") or die "can\'t connect to orb $ARGV[0]";

$pf=`cat $ARGV[1]`;
orbput($orb,"$ARGV[2]/EXP/ORACLEpf",$ARGV[3],$pf,length($pf));
orbclose($orb);
print "1\n";
