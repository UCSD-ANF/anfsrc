#
#   dbwfserver_ta_setup: script to subset all sitechan tables for TA dbwfserver instances
#   author: Juan C. Reyes
#   email:  reyes@ucsd.edu
#   No BRTT support
#

use archive;
use sysinfo;
use Datascope;
use File::Copy;
use Pod::Usage "pod2usage";
use Getopt::Std "getopts";
use IPC::Cmd qw/can_run/;


select STDOUT; $| = 1;
select STDERR; $| = 1;
#
#  Program setup
#
#{{{
    $start = now();
    $parent = $$;

    pod2usage({-exitval => 2, -verbose => 2}) if ( ! getopts('fnhm:') || @ARGV != 0 );

    pod2usage({-exitval => 2, -verbose => 2}) if $opt_h;

    elog_init($0,@ARGV);

    elog_die("ERRO: Need flag '-m email' to use the '-f' option") if $opt_f and ! $opt_m;
    savemail() if $opt_f;

    elog_notify('');
    elog_notify("$0 @ARGV");
    elog_notify("Starting execution at ".strydtime($start)." on ".my_hostname());
    elog_notify('');

    elog_notify("**** DRY/NULL RUN ****") if $opt_n;

    #
    # RealTime system
    #
    $rt_path = "/export/home/rt/rtsystems/dbwfserver/";

    #
    #Seismic database
    #
    $ta_path = "/anf/TA/rt/usarray/";
    $ta_db = "/anf/TA/rt/usarray/usarray";
    $ta_temp = "db/dbwfserver_temp";
    $ta_new = "db/dbwfserver_usarray";

    #
    #SOH database
    #
    $soh_path = "/anf/TA/rt/status/";
    $soh_db = "/anf/TA/rt/status/usarray_status";
    $soh_temp = "db/dbwfserver_temp";
    $soh_new = "db/dbwfserver_status";

    #
    #INFRAMET database
    #
    $inframet_path = "/anf/TA/rt/usarray/";
    $inframet_db = "/anf/TA/rt/usarray/inframet";
    $inframet_temp = "db/dbwfserver_tmp";
    $inframet_new = "db/dbwfserver_inframet";

    #
    #ANZA database
    #
    $anza_path = "/anf/ANZA/rt/anza/";
    $anza_db = "/anf/ANZA/rt/anza/anza";
    $anza_temp = "db/dbwfserver_tmp";
    $anza_new = "db/dbwfserver_anza";

    #
    # We want access to ssh and scp
    #
    $dbadd = can_run('dbadd') or log_die("dbadd missing on PATH:".path());

    #
    # Verify Database
    #
    foreach $d ( qw/anza inframet soh ta/ ){
        $d_db = ${$d."_db"};
        log_die("Can't find DB: $d_db.wfdisc") unless -f "$d_db.wfdisc"; 
    }

#}}}

#
#  Main
#
#{{{


    #
    # Run external commands
    #
    foreach $d ( qw/anza inframet soh ta/ ){

        #
        # Build temp vars
        #
        $d_db = ${$d."_db"};
        $d_path = ${$d."_path"};
        $d_new = $rt_path . ${$d."_new"};
        $d_temp = $rt_path . ${$d."_temp"};

        elog_notify("$d:");
        elog_notify("\tGo to: [$d_path]");
        log_die("ERROR: Cannot access directory $d_path") unless chdir $d_path;


        #
        # Clean old temp files
        #
        elog_notify("\tClean temp tables for $d");
        elog_notify("\tRemove temp file: [$d_temp.lastid]");
        if ( -f "$d_temp.lastid" and ! $opt_n ) {
            log_die("ERROR: Cannot remove temp file $d_temp.lastid ") unless unlink("$d_temp.lastid");
        }
        elog_notify("\tRemove temp file: [$d_temp.sitechan]");
        if ( -f "$d_temp.sitechan" and ! $opt_n ) {
            log_die("ERROR: Cannot remove temp file $d_temp.sitechan ") unless unlink("$d_temp.sitechan");
        }

        # 
        # Build sitechan table
        #
        run("$dbadd -a $d_db.wfdisc $d_temp.sitechan");

        # 
        # Move sitechan table
        #
        elog_notify("\tMove temp file: [mv $d_temp.sitechan,$d_new.sitechan]");
        unless ( $opt_n ) {
            log_die("ERROR: Cannot move file $d_temp.sitechan to $d_new.sitechan") 
                    unless move("$d_temp.sitechan","$d_new.sitechan");
        }

        #
        # Remove lastid file
        #
        elog_notify("\tRemove temp file: [$d_temp.lastid]");
        if ( -f "$d_temp.lastid" and ! $opt_n ) {
            log_die("ERROR: Cannot remove temp file $d_temp.lastid ") unless unlink("$d_temp.lastid");
        }
        elog_notify("");
    }

    #
    # Restart rtsystem
    #
    elog_notify("\tRestart rtexec tasks: [$rt_path/rtexec.pf]");
    log_die("ERROR: Cannot access directory $rt_path") unless chdir $rt_path;
    run("rtkill -r ANZA") unless $opt_n;
    run("rtkill -r INFRAMET") unless $opt_n;
    run("rtkill -r PFO") unless $opt_n;
    run("rtkill -r SOH") unless $opt_n;
    run("rtkill -r TA") unless $opt_n;

    $end = now();
    $run_time_str = strtdelta($end - $start);
    $start = strydtime($start);
    $end = strydtime($end);

    elog_notify("\n\n----------------- END -----------------\n\n");
    elog_notify("Start: $start End: $end");
    elog_notify("Runtime: $run_time_str");

    exit 0;

#}}}

sub run{
#{{{
    my $cmd = shift;

    elog_notify("\tRunning cmd: [$cmd]");
    return if $opt_n;

    system($cmd) == 0 or log_die("ERROR in system call: [$cmd]");

    if ($? == -1) {
        log_die("failed to execute: [$cmd] => $!");
    } elsif ($? & 127) {
        log_die("child died with signal %d, %s coredump", ($? & 127), ($? & 128) ? 'with' : 'without');
    }
    else {
        elog_notify("\t\tchild exited with value %d", $? >> 8);
    }

    return;
#}}}
}

sub log_die {
#{{{
    my $msg = shift;

    savemail() unless $opt_f;

    elog_complain($msg);

    sendmail('dbwfserver_ta_setup: ERROR',$opt_m) if $opt_m;

    elog_die($msg);
#}}}
}


__END__
#{{{
=pod

=head1 NAME

dbwfserver_ta_setup - Build subset for sitechan table for the WaveformServer

=head1 SYNOPSIS

dbwfserver_ta_setup [-h] [-n] [-d] [-f] [-m email]

=head1 SUPORT

No BRTT support == contact Juan Reyes <reyes@ucsd.edu>

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h> 

Produce this documentation

=item B<-n> 

Test  mode/dry  run.  Does not delete, copy or move  any file or folder.

=item B<-f> 

Force email at end of script. The default is to send emails only on errors. Needs -m flag. 

=item B<-m email> 

Email this address in case of error or if -f flag is set.


=back

=head1 DESCRIPTION

dbwfserver_ta_setup will build new sitechan tables for the Inframet, Seismic and SOH instances of the 
WaveformServers of the TA daatasets and one for ANZA. This should run every day so any new sta:chan entry 
on the wfdisc will be recognized by the software. After creating the new sitechan tables the software will
move them to the production paths and then restart the servers. By default the script will only email
on errors. If the -f flag is set then an email will be produced on every run.

=head1 BUGS AND CAVEATS

All paths are hardcoded in the script. 

    #
    # RealTime system
    #
    $rt_path = "/export/home/rt/rtsystems/dbwfserver/";

    #
    #Seismic database
    #
    $ta_path = "/anf/TA/rt/usarray/";
    $ta_db = "/anf/TA/rt/usarray/usarray";
    $ta_temp = "db/dbwfserver_temp";
    $ta_new = "db/dbwfserver_usarray";

    #
    #SOH database
    #
    $soh_path = "/anf/TA/rt/status/";
    $soh_db = "/anf/TA/rt/status/usarray_status";
    $soh_temp = "db/dbwfserver_temp";
    $soh_new = "db/dbwfserver_status";

    #
    #INFRAMET database
    #
    $inframet_path = "/anf/TA/rt/usarray/";
    $inframet_db = "/anf/TA/rt/usarray/inframet";
    $inframet_temp = "db/dbwfserver_tmp";
    $inframet_new = "db/dbwfserver_inframet";

    #
    #ANZA database
    #
    $anza_path = "/anf/ANZA/rt/anza/";
    $anza_db = "/anf/ANZA/rt/anza/anza";
    $anza_temp = "db/dbwfserver_tmp";
    $anza_new = "db/dbwfserver_anza";


=head1 ENVIRONMENT

needs to have sourced $ANTELOPE/setup.csh.

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).

=cut
#}}}
