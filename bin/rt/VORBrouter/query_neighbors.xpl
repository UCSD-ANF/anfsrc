
use orb;
use Datascope;
use Socket;

$c=0;
print "ActNeigh &Arr{\n";
foreach $i (`ls  connection`)
{
    chomp($i);
    open(FOO,"connection/$i");
    if (0.00208333 > -M FOO) # 3 min
    {
	$ip=`cat connection/$i`;
	chomp($ip);
	if ((@pf=pffiles("VORBneighbor.pf"))<0)
	{
	    fprintf stderr "pfupdate failed!\n";
	}
	$str=pfget($pf[0],"neighbors");
	%t=%{$str};
	($pubkey,$metric)=split /\s+/, $t{$ip}; 
	if ($metric eq "")
	{
	    print "\t$i\t1\n";
	}
	else
	{
	    print "\t$i\t$metric\n";
	}
	$c++;
    }
}

print "}\n";

print "\nneighbor_cnt\t$c\n";
