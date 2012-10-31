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
use Datascope ;
use File::Copy;


our ($parent,$start,$host);
our ($target);
our ($opt_V,$opt_v,$opt_m,$opt_p);
our (%pf,%temp_pf);
our ($fh,$key,$output,$line,$chan);
our ($dlsta,$net,$sta,$i,$ii);
our (%stations,@tmp,@channels);
our ($datalogger,$template);


$ENV{'ELOG_MAXMSG'} = 0;
$parent = $$;
$start = now();
$host = my_hostname();

elog_init($0,@ARGV);
elog_notify("$0 @ARGV");
elog_notify("Starting at ".strydtime($start)." on $host");


if ( ! &getopts('vVm:p:') || @ARGV > 1 ) { 
    elog_die( "Usage: $0 [-v] [-V] [-m email] [-p parameter_file] directory");
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
# Get parameters from config file
#
elog_notify("Getting params from: $opt_p") if $opt_v;
elog_die("Cannot find parameter file: $opt_p") unless -f $opt_p;
%pf = getparam($opt_p);

prettyprint(\%pf) if $opt_V;

#
# Config
#
$target = $ARGV[0] || './' ;
$target = File::Spec->rel2abs( $target ) ;
elog_notify("User directory: $opt_p") if $opt_v;
elog_die("Cannot find work directory: $target") unless -d $target;
elog_die("Cannot change to directory: $target") unless chdir $target;


#
# For every "source" defined in the parameter file
# load the q3302orb.pf file and build a new 
# orbmonrtd.pf file.

for $key ( sort keys $pf{'sources'} ) {
    elog_notify("") if $opt_v;
    elog_notify("Build file for bundle [$key]") if $opt_v;

    elog_complain("No orb in:\n $pf{'sources'}{$key}") unless $pf{'sources'}{$key}{'orb'};
    next unless $pf{'sources'}{$key}{'orb'};

    elog_complain("No src in:\n $pf{'sources'}{$key}") unless $pf{'sources'}{$key}{'src'};
    #next unless $pf{'sources'}{$key}{'src'};

    elog_complain("No output in:\n $pf{'sources'}{$key}") unless $pf{'sources'}{$key}{'output'};
    next unless $pf{'sources'}{$key}{'output'};

    elog_complain("No tw in:\n $pf{'sources'}{$key}") unless $pf{'sources'}{$key}{'tw'};
    next unless $pf{'sources'}{$key}{'tw'};

    elog_notify("") if $opt_v;

    #
    # Open temp_file to write file
    #
    unlink $pf{'temp_file'} if -e $pf{'temp_file'};

    #
    # Open file for output of parameters
    #
    open($fh, ">", $pf{'temp_file'}) or elog_die("cannot open $pf{'temp_file'}: $!");


    #
    # Get configuration of q3302orb.pf
    #
    if ( $pf{'sources'}{$key}{'src'} ) {
        #{{{
        elog_notify("Getting params from: $pf{'sources'}{$key}{'src'}") if $opt_v;
        %temp_pf = getparam($pf{'sources'}{$key}{'src'}) or elog_die("Cannot access: $pf{'sources'}{$key}{'src'}");

        elog_die("Cannot find parameter file for q3302orb.pf => $pf{'sources'}{$key}{'src'}") unless %temp_pf;

        prettyprint(\%temp_pf) if $opt_V;

        for $i ( keys $temp_pf{'dataloggers'} ) {
            elog_notify("$pf{'sources'}{$key}{'src'} dataloggers[$i] = $temp_pf{'dataloggers'}[$i]") if $opt_V;
            @tmp = split(' ',$temp_pf{'dataloggers'}[$i]);
            $dlsta    = $tmp[0];
            $net      = $tmp[1];
            $sta      = $tmp[2];
            $template = $tmp[6];
            elog_notify("New datalogger $dlsta $net $sta $template") if $opt_v;

            unless ($dlsta and $net and $sta and $template) {
                elog_die("ERROR parsing: $pf{'sources'}{$key}{'src'} datalogger [$i] => @tmp");
            }

            #
            # Stations we want only
            #
            if ($pf{'sources'}{$key}{'sta_include'}) {
                if ( $sta !~ /$pf{'sources'}{$key}{'sta_include'}/ ) {
                    elog_complain('');
                    elog_complain("Station rejected by sta_include: $pf{'sources'}{$key}{'sta_include'}");
                    elog_complain('');
                    next; 
                }
            }

            #
            # Stations we avoid only
            #
            if ($pf{'sources'}{$key}{'sta_reject'}) {
                if ( $sta =~ /$pf{'sources'}{$key}{'sta_reject'}/ ) {
                    elog_complain('');
                    elog_complain("Station rejected by sta_reject: $pf{'sources'}{$key}{'sta_reject'}");
                    elog_complain('');
                    next; 
                }
            }


            #
            # Verify we have template for station
            #
            unless ( $pf{'datalogger_templates'}{$template} ) {
                elog_complain('');
                elog_complain("ERROR: No template for @tmp");
                elog_complain('');
                next;
            }


            #
            # Add to list
            #
            $stations{$dlsta} = [$net, $sta, $template];

        }
        #}}}
    }

    #
    # Stations we want only
    #
    elog_notify("Adding forced stations:") if $opt_v;
    for $i (keys $pf{'sources'}{$key}{'forced_stations'}) {
        @tmp = split('_',$i);
        $dlsta    = $i;
        $net      = $tmp[0];
        $sta      = $tmp[1];
        $template = $pf{'sources'}{$key}{'forced_stations'}{$i};
        elog_notify("New datalogger $dlsta $net $sta $template") if $opt_v;

        #
        # Add to list
        #
        $stations{$dlsta} = [$net, $sta, $template];

    }


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
    for $i (sort keys %stations){
        elog_notify("Adding $i");

        $dlsta    = $i;
        $net      = $stations{$i}[0];
        $sta      = $stations{$i}[1];
        $template = $stations{$i}[2];

        #
        # Some templates have 2 sets of channels
        #
        for $ii (keys $pf{'datalogger_templates'}{$template} ){

            @channels = split('_',$pf{'datalogger_templates'}{$template}{$ii}{'chans'});

            for $chan (sort @channels){
                elog_notify("Test config for $chan in $dlsta") if $opt_v;

                #
                # Channels we want only
                #
                if ($pf{'sources'}{$key}{'chan_include'}) {
                    if ( $chan !~ /$pf{'sources'}{$key}{'chan_include'}/ ) {
                        elog_complain('');
                        elog_complain("Channel rejected by chan_include: $pf{'sources'}{$key}{'chan_include'}");
                        elog_complain('');
                        next; 
                    }
                }

                #
                # Channels we avoid only
                #
                if ($pf{'sources'}{$key}{'chan_reject'}) {
                    if ( $sta =~ /$pf{'sources'}{$key}{'chan_reject'}/ ) {
                        elog_complain('');
                        elog_complain("Channel rejected by chan_reject: $pf{'sources'}{$key}{'chan_reject'}");
                        elog_complain('');
                        next; 
                    }
                }

                #
                # We build the line now
                #

                $line = "${net}_${sta}_${chan} $pf{'sources'}{$key}{'orb'} ";
                $line .= "$pf{'sources'}{$key}{'tw'} ";
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
    elog_die("No temp file present after loop.") unless $pf{'temp_file'};

    #
    # Clean path of output file.
    #
    $output = File::Spec->rel2abs( $pf{'sources'}{$key}{'output'} );
    elog_notify("Save to output file: $output");

    #
    # Remove output file
    #
    unlink $output if -e $output;

    #
    # Move file
    #
    move($pf{'temp_file'},$output) or elog_die("Problems moving temp file to $output: $!");

}


exit 0 ;
