#
#
# Dynamically create parameter files for orbmonrtd
#
# Juan Reyes
# reyes@ucsd.edu
#

use strict ;
use warnings ;
use sysinfo;
use utilfunct;
use Getopt::Std ;
use File::Spec;
use File::Basename;
use File::Path qw(make_path);
use Datascope ;
use File::Copy;


our ($parent,$start,$host);
our ($target);
our ($opt_c,$opt_V,$opt_v,$opt_m,$opt_p);
our (%pf,%temp_pf);
our ($fh,$key,$output,$line);
our ($dlsta,$i,$ii);
our (%stations,@tmp,@channels);
our ($datalogger);
our ($tempf,$dirname);

our (@db,@dbtmp,@deployment,@sensor,@site,@comm);
our ($amin,$amax,$net,$template,$r,$lat,$lon);
our ($vnet,$snet,$sta,$chan,$time,$endtime);
our (@selected,$stas);

# Temporary file to use for building the parameter files
$tempf = '/tmp/orbmonrtd_pf_generator_temp';

$ENV{'ELOG_MAXMSG'} = 0;
$parent = $$;
$start = now();
$host = my_hostname();

elog_init($0,@ARGV);
elog_notify("$0 @ARGV");
elog_notify("Starting at ".strydtime($start)." on $host");


if ( ! &getopts('cvVm:p:') || @ARGV > 1 ) { 
    elog_die( "Usage: $0 [-v] [-V] [-c] [-m email] [-p parameter_file]");
}


#
# Initialize  mail
#
if ($opt_m){
    savemail();
    elog_notify("Initialize mail") if $opt_v;
}


#
# Implicit flag
#
$opt_v = $opt_V if $opt_V;
$opt_p ||= "orbmonrtd_pf_generator.pf" ;

#
# Config
#
elog_notify("Use temp file => $tempf") if $opt_v;

#
# Get parameters from config file
#
elog_notify("Getting params from: $opt_p") if $opt_v;
elog_die("Cannot find parameter file: $opt_p") unless -f $opt_p;
%pf = getparam($opt_p);

prettyprint(\%pf) if $opt_V;

#
# For every "bundle" defined in the parameter file
# verify minimum configuration parameters.

for $key ( sort keys $pf{'bundles'} ) {
    elog_notify("") if $opt_v;
    elog_notify("Bundle [$key]") if $opt_v;

    elog_die("No database in:\n $pf{'bundles'}{$key}") unless $pf{'bundles'}{$key}{'database'};
    elog_notify("   * source_database => $pf{'bundles'}{$key}{'database'}") if $opt_v;

    elog_die("No output in:\n $pf{'bundles'}{$key}") unless $pf{'bundles'}{$key}{'output'};
    elog_notify("   * output_file => $pf{'bundles'}{$key}{'output'}") if $opt_v;

    elog_die("No orb in:\n $pf{'bundles'}{$key}") unless $pf{'bundles'}{$key}{'orb'};
    elog_notify("   * orb => $pf{'bundles'}{$key}{'orb'}") if $opt_v;

    elog_die("No tw in:\n $pf{'bundles'}{$key}") unless $pf{'bundles'}{$key}{'tw'};
    elog_notify("   * time_window => $pf{'bundles'}{$key}{'tw'}") if $opt_v;

    elog_die("No channel_template in:\n $pf{'bundles'}{$key}") unless defined $pf{'bundles'}{$key}{'channel_template'};
    elog_notify("   * channel_template => $pf{'bundles'}{$key}{'channel_template'}") if $opt_v;

    elog_notify("") if $opt_v;

}

elog_notify("All BUNDLES verified in $opt_p. Continue with build of parameter files.") if $opt_v;



#
# Get each bundle and build a parameter file with the 
# subset of station_channel combinations
#
for $key ( sort keys $pf{'bundles'} ) {
    #
    # Open temp_file to write file
    #
    unlink $tempf if -e $tempf;

    #
    # Clean local variable
    #
    $stas = ();

    #
    # Open file for output of parameters
    #
    open($fh, ">", $tempf) or elog_die("cannot open $tempf: $!");


    elog_notify("Getting stations from: $key => $pf{'bundles'}{$key}{'database'}") if $opt_v;

    #
    # Database interaction
    #
    @db = dbopen($pf{'bundles'}{$key}{'database'},'r+') or 
        elog_die("Cannot open $pf{'bundles'}{$key}{'database'}");

    @deployment = dblookup(@db,"","deployment","","") or elog_die("Can't open deployment table");
    @sensor = dblookup(@db,"","sensor","","") or elog_die("Can't open sensor table");
    @site = dblookup(@db,"","site","","") or elog_die("Can't open site table");
    @comm = dblookup(@db,"","comm","","") or elog_die("Can't open comm table");


    #
    # We need valid databases
    #
    $r = dbquery(@deployment, "dbRECORD_COUNT");
    elog_die("\t$r records in deployment table") unless $r;
    $r = dbquery(@sensor, "dbRECORD_COUNT");
    elog_die("\t$r records in sensor table") unless $r;
    $r = dbquery(@site, "dbRECORD_COUNT");
    elog_die("\t$r records in site table") unless $r;


    #subset for valid entries only
    #@deployment = dbsubset(@deployment, "equip_install < now() && equip_remove == NULL");
    @deployment = dbsubset(@deployment, "time < now() && (endtime == NULL || endtime > now())");


    $r = dbquery(@deployment, "dbRECORD_COUNT");
    elog_notify("\t$r records in deployment table after subset for valid entries") if $opt_v;


    #
    # Join tables
    #
    @dbtmp = dbjoin(@deployment,@site) or elog_die("Can't join with site table");
    $r = dbquery(@dbtmp, "dbRECORD_COUNT");
    elog_notify("\t$r records after join with site") if $opt_v;

    #@dbtmp = dbjoin(@dbtmp,@sensor,"sta#sta") or elog_die("Can't join with sensor table");
    @dbtmp = dbjoin(@dbtmp,@sensor) or elog_die("Can't join with sensor table");
    $r = dbquery(@dbtmp, "dbRECORD_COUNT");
    elog_notify("\t$r records after join with sensor") if $opt_v;

    if ($opt_c) {

        elog_notify("\tNeed to join with comm") if $opt_v;
        @dbtmp = dbjoin(@dbtmp,@comm) or elog_die("Can't join with comm table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after join with comm") if $opt_v;

        #
        # We don't use stations with NULL or 'none' comms
        #
        @dbtmp = dbsubset(@dbtmp,"commtype !~ /none/ && commtype != NULL") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after commtype subset ") if $opt_v;

    }

    #
    # Networks we want only
    #
    if ($pf{'bundles'}{$key}{'net_include'}) {
        elog_complain('');
        elog_complain("Apply net_include: $pf{'bundles'}{$key}{'net_include'}");
        elog_complain('');

        @dbtmp = dbsubset(@dbtmp,"snet =~ /$pf{'bundles'}{$key}{'net_include'}/") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after net_include subset ") if $opt_v;

    }

    #
    # Networks we want to reject
    #
    if ($pf{'bundles'}{$key}{'net_reject'}) {
        elog_complain('');
        elog_complain("Apply net_reject: $pf{'bundles'}{$key}{'net_reject'}");
        elog_complain('');

        @dbtmp = dbsubset(@dbtmp,"snet !~ /$pf{'bundles'}{$key}{'net_reject'}/") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after net_reject subset ") if $opt_v;

    }

    #
    # Stations we want only
    #
    if ($pf{'bundles'}{$key}{'sta_include'}) {
        elog_complain('');
        elog_complain("Apply sta_include: $pf{'bundles'}{$key}{'sta_include'}");
        elog_complain('');

        @dbtmp = dbsubset(@dbtmp,"sta =~ /$pf{'bundles'}{$key}{'sta_include'}/") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after sta_include subset ") if $opt_v;

    }

    #
    # Stations we want to reject
    #
    if ($pf{'bundles'}{$key}{'sta_reject'}) {
        elog_complain('');
        elog_complain("Apply sta_reject: $pf{'bundles'}{$key}{'sta_reject'}");
        elog_complain('');

        @dbtmp = dbsubset(@dbtmp,"sta !~ /$pf{'bundles'}{$key}{'sta_reject'}/") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after sta_reject subset ") if $opt_v;

    }

    #
    # Channels we want only
    #
    if ($pf{'bundles'}{$key}{'chan_include'}) {
        elog_complain('');
        elog_complain("Apply chan_include: $pf{'bundles'}{$key}{'chan_include'}");
        elog_complain('');

        @dbtmp = dbsubset(@dbtmp,"chan =~ /$pf{'bundles'}{$key}{'chan_include'}/") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after chan_include subset ") if $opt_v;

    }

    #
    # Channels we want to reject
    #
    if ($pf{'bundles'}{$key}{'chan_reject'}) {
        elog_complain('');
        elog_complain("Apply chan_reject: $pf{'bundles'}{$key}{'chan_reject'}");
        elog_complain('');

        @dbtmp = dbsubset(@dbtmp,"chan !~ /$pf{'bundles'}{$key}{'chan_reject'}/") or elog_die("Can't subset on table");
        $r = dbquery(@dbtmp, "dbRECORD_COUNT");
        elog_notify("\t$r records after chan_reject subset ") if $opt_v;

    }

    #
    # Get data
    #
    for ($dbtmp[3] = 0; $dbtmp[3] < $r; $dbtmp[3]++) {

        ($vnet,$snet,$sta,$chan,$lat,$lon,$time,$endtime) = dbgetv(@dbtmp, qw/vnet snet sta chan lat lon time endtime/);

        elog_notify("\t$vnet ${snet}_${sta}_${chan} => [$lat,$lon] [$time,$endtime]") if $opt_v;

        $stas->{$sta} = () unless defined $stas->{$sta};

        $stas->{$sta}->{'vnet'} = $vnet;
        $stas->{$sta}->{'net'} = $snet;
        $stas->{$sta}->{'lat'} = $lat;
        $stas->{$sta}->{'lon'} = $lon;
        $stas->{$sta}->{'time'} = $time;
        $stas->{$sta}->{'endtime'} = $endtime;
        $stas->{$sta}->{'width'} = $pf{'bundles'}{$key}{'width'};
        $stas->{$sta}->{'height'} = $pf{'bundles'}{$key}{'height'};
        $stas->{$sta}->{'filter'} = $pf{'bundles'}{$key}{'filter'};
        $stas->{$sta}->{'orb'} = $pf{'bundles'}{$key}{'orb'};
        $stas->{$sta}->{'tw'} = $pf{'bundles'}{$key}{'tw'};

        push(@{$stas->{$sta}->{'chans'}},$chan) unless grep (/$chan/,@{$stas->{$sta}->{'chans'}});

    }

    dbclose(@db);


    #
    # Print local dictionary of data
    #
    if ($opt_v) {
        #prettyprint($stas);
        for my $k1 ( sort keys %$stas ) {
            elog_notify("STATION: $k1");
            for my $k2 ( keys %{$stas->{ $k1 }} ) {
                if(ref($stas->{$k1}->{$k2}) eq 'ARRAY'){
                    elog_notify("\tval: $k2 ". join(" ",@{$stas->{ $k1 }->{ $k2 }}));
                } else {
                    elog_notify("\tval: $k2 $stas->{ $k1 }->{ $k2 }");
                }
            }
        }
    }

    elog_die('No stations in memory after database subsets.') unless scalar keys %$stas;


    #
    # Initiate file
    #
    print $fh "#\n";
    print $fh "# Parameter file for orbmonrtd for vnc setup\n";
    print $fh "# File was created by $0 @ARGV\n";
    print $fh "# From host $host\n";
    print $fh "#\n";

    print $fh "$pf{'padding'}\n";

    print $fh "    sources &Tbl{\n";


    #
    # Get sorted list of stations 
    #
    for $i (sort keys %$stas){
        elog_notify("");
        elog_notify("$i:");

        $net      = $stas->{$i}->{'net'};
        $template = $pf{'bundles'}{$key}{'channel_template'};
        elog_die("Not valid template $template for $i") unless keys %{$pf{'channel_template'}{$template}};

        #
        # Stations may have multiple channels. They will be verified 
        # with the list of channels in the template.
        #
        elog_notify("\ttemplate definition: $template" ) if $opt_v;
        elog_notify("\t\t".join(' ',sort keys %{$pf{'channel_template'}{$template}}) ) if $opt_v;
        elog_notify("\tselected channels:" ) if $opt_v;
        elog_notify("\t\t".join(' ',sort @{$stas->{$i}->{'chans'}}) ) if $opt_v;

        #for $ii (sort keys %{$pf{'channel_template'}{$template}} ){
        for $ii (sort @{$stas->{$i}->{'chans'}} ){

            elog_notify("\t$ii") if $opt_v;

            #elog_die("$ii not in template $template for file $opt_p") unless defined $pf{'channel_template'}{$template}{$ii};
            elog_notify("\t\t".join(' ',sort keys %{$pf{'channel_template'}{$template}}) ) if $opt_v;

            @selected = ();
            for (keys %{$pf{'channel_template'}{$template}}) {
                push(@selected, $_) if $ii =~ /$_/;
            }

            elog_notify("\ttemplate match for channel $ii => [@selected]");

            elog_complain("\n\n\tGot more than one template match for channel $ii => [@selected]\n\n") 
                        if length @selected > 1;

            elog_die("No template match for channel $ii") if scalar @selected < 1;

            elog_notify("\t$selected[0] => $pf{'channel_template'}{$template}{$selected[0]}") if $opt_v; 

            ($amin,$amax) = split / /, $pf{'channel_template'}{$template}{$selected[0]};

            elog_die("No amin/amax for $ii") unless $amin and $amax;


            #
            # We build the line now
            #
            $line = "${net}_${i}_${ii} ";
            $line .= "$stas->{$i}->{'orb'} ";
            $line .= "$stas->{$i}->{'tw'} ";
            $line .= "$amin ";
            $line .= "$amax ";
            $line .= "$stas->{$i}->{'width'} ";
            $line .= "$stas->{$i}->{'height'} ";
            $line .= "$stas->{$i}->{'filter'}";
            elog_notify("\tAdding $line") if $opt_v;
            elog_notify("") if $opt_v;

            print $fh "        $line\n";

            next;

            for $chan (sort @channels){
                elog_notify("Test config for $chan in $dlsta") if $opt_v;

                #
                # We build the line now
                #

                $line = "${net}_${sta}_${chan} $pf{'bundles'}{$key}{'database'} ";
                $line .= "$pf{'bundles'}{$key}{'tw'} ";
                $line .= "$pf{'datalogger_templates'}{$template}{$ii}{'amin'} ";
                $line .= "$pf{'datalogger_templates'}{$template}{$ii}{'amax'} ";
                $line .= "$pf{'datalogger_templates'}{$template}{$ii}{'width'} ";
                $line .= "$pf{'datalogger_templates'}{$template}{$ii}{'height'}";

                elog_notify("Adding $line") if $opt_v;

                print $fh "        $line\n";

            }
        }
    }

    #
    # Finish file
    #
    print $fh "    }\n";
    close $fh;


    #
    # Verify that we have a file
    #
    elog_die("No temp file present after loop.") unless -f $tempf;

    #
    # Clean path of output file.
    #
    $output = File::Spec->rel2abs( $pf{'bundles'}{$key}{'output'} );
    elog_notify("Save to output file: $output");
    $dirname  = dirname($output);
    make_path($dirname) unless -d $dirname;

    #
    # Remove output file
    #
    unlink $output if -e $output;

    #
    # Move file
    #
    move($tempf,$output) or elog_die("Problems moving temp file to $output: $!");
    #move($output,"$target/") or elog_die("Problems moving $output file to $target: $!");

}


exit 0 ;
