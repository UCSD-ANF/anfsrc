#!/usr/bin/perl
use IPC::Open2;

$address="tshansen\@nlanr.net fvernon\@ucsd.edu kent\@lindquistconsulting.com";
#$address="tshansen\@nlanr.net";
if (`ps awwx | grep map_changes.pl | grep -v grep | grep -v emacs | grep -v /bin/sh | grep -v tcsh | wc -l`!=1)
{
    exit(0);
}
else
{
    print stderr "map_changes.pl restarted!\n";
}

while (1)
{
    undef @logs;
    undef @routers;
    undef @routes;
    undef @srcgood;
    undef @srcbad;
    @history=`cat /home/tshansen/src/topo/most_recent.dot`;
    @current=`/home/tshansen/src/topo/orbtopo2.pl > /home/tshansen/src/topo/most_recent.dot; cat /home/tshansen/src/topo/most_recent.dot`;
    
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
		if ($l2 =~ /$name -> $name2/)
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
		if ($l2 =~ /$name -> $name2/)
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
	open(DESIGN, "| /usr/local/bin/dot -Tgif -o /tmp/status.$$.gif 2> /dev/null");
	print DESIGN "Digraph \"Route Status\" {\n";
	print DESIGN "\trankdir="LR";\n";
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
	open(MAIL, "|/usr/bin/nail -a /tmp/status.$$.gif -s \"ROADNet Topology Change\" $address 2>  /dev/null");
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
	unlink("/tmp/status.$$.gif");
    }

    $y=`date +%Y`;
    $ct=time()-3*60*60;
    chomp($y);

    foreach $l (`orbstat -s :`)
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
	if (`grep \"$i \" /home/tshansen/src/topo/srcoutage.dat | wc -l`!=1)
	{
	    push(@logs,"$lcv $i is out dated.\n");
	    $lcv++;
	}
    }

    foreach $i (@srcgood)
    {
	if (`grep \"$i \" /home/tshansen/src/topo/srcoutage.dat | wc -l`!=0)
	{
	    push(@logs,"$lcv $i is now up arriving.\n");
	    $lcv++;
	}
    }

    if (defined @logs)
    {
	open(MAIL, "|/usr/bin/nail -s \"ROADNet Data Change\" $address");
	print MAIL "The following data availability changes have been detected:\n\n";
	print MAIL @logs;
	close(MAIL);
    }

    open(FOO,">/home/tshansen/src/topo/srcoutage.dat");
    foreach $i (@srcbad)
    {
	print FOO "$i \n";
    }
    print FOO "\n";
    close(FOO);
    
    sleep(30*60);
}
    
