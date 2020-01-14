#
#   dbwfserver_ta_setup:
#       script to subset all sitechan
#       tables for TA dbwfserver instances
#
#   Original author: Juan C. Reyes
#   Modifications by: Geoff Davis
#   email:  support@anf.ucsd.edu
#

use warnings;
use strict;
use archive qw/savemail sendmail/;
use sysinfo;
use Datascope;
use Data::Dumper;
use File::Copy;
use File::Basename 'basename';
use Pod::Usage 'pod2usage';
use Getopt::Std 'getopts';
use IPC::Cmd 'can_run';

#
# CONFIG
#
our $PROGNAME = basename($0);
our $PFNAME = $PROGNAME;
our $PF_REVISION_TIME = 1579029286;
our @DBPATH_SUBKEYS = qw/db temp new/;

our %options; # Command line options
our $params;  # Pointer to contents of the parameter file
our $dbadd;   # path to dbadd executable

sub log_die {
    my $msg = shift;
    our %options;

    # If we are supposed to send email, Start savemail unless a savemail
    # session was started already. Otherwise, output mysteriously
    # disappears and random tempfiles get left around.
    if ($options{'m'}){
        savemail() unless $options{'f'};
        elog_complain($msg);
        sendmail('dbwfserver_ta_setup: ERROR',$options{'m'}) if $options{'m'};
    }



    elog_die($msg);

}

sub _validate_wfdisc_exists($) {
    # Given a db_path, verify that the associated Datascope wfdisc table exists
    my $db_path = shift;
    my $wfdisc_filename = $db_path . '.wfdisc';
    log_die("Can't find DB: " . $wfdisc_filename) unless -f $wfdisc_filename;
}

sub _validate_dbpath_subkeys($) {
    # Verify that the DBPATH_SUBKEYS exist for a given $db_name in
    # $params->{database_paths}
    my $db_name = shift;
    our $params;
    our @DBPATH_SUBKEYS;
    foreach my $key_name ( @DBPATH_SUBKEYS ) {
        unless (exists($params->{'database_paths'}{$db_name}{$key_name})) {
            log_die(
                'Parameter file key ' . $key_name . ' for database ' .\
                $db_name . " is missing. Can't continue.");
        }
    }
}

sub restart_systems{
    # Restart the real-time system in $RTSYSTEM_DIRECTORY with rtkill

    my @procs = ();
    my $name;
    my $fh;
    our %options;
    our $params;

    my $rtdir = $params->{'rtsystem_directory'};
    my $pf_file = $rtdir . '/rtexec.pf';
    elog_notify("Restart rtexec tasks: [$pf_file]") ;

    #
    # Change to realtime directory
    #
    chdir $rtdir or log_die("ERROR: Cannot chdir to $rtdir");


    elog_notify("rtkill -l =>") ;
    open($fh, '-|', 'rtkill -l') or log_die("ERROR: rtkill -l => $!") ;

    while ($name = <$fh>) {
        elog_notify("\t$name") ;
        next if $name =~ /^(\s*)$/ ;
        $name =~ /^\s*(\w*)\s*(on)\s*$/ ;
        if ( $1 ) {
            push ( @procs, $1 ) ;
            elog_notify("GOT PROC: [$1]") ;
        }
    }

    close($fh);


    #
    # Restart rtsystem
    #
    foreach my $d ( @procs ){
        elog_notify("\tRestart: [$d]");
        my_run("rtkill -r $d") unless $options{'n'};
    }
}


sub remove_table_temp_file{
    my $table = shift;
    our $options;

    elog_notify("\tRemove temp file: [$table]");
    return 0 if $options{'n'};

    if ( -f $table ){
        unlink($table) or log_die("ERROR: Cannot remove temp file $table");
    }
    return 0;
}

sub my_run{
    my $cmd = shift ;
    our %options;

    elog_notify("\tRunning cmd: [$cmd]");
    return if $options{'n'};

    system($cmd) == 0 or log_die("ERROR in system call: [$cmd]");

    if ($? == -1){
        log_die("failed to execute: [$cmd] => $!");
    } elsif ($? & 127) {
        log_die("child died with signal %d, %s coredump",
            ($? & 127),
            ($? & 128) ? 'with' : 'without');
    }
    else {
        elog_notify("\t\tchild exited with value %d", $? >> 8);
    }
    return;
}

sub main {
    #
    #  Program setup
    #
    select STDOUT; $| = 1 ;
    select STDERR; $| = 1 ;
    my $start = now() ;
    my $parent = $$ ;
    our %options;
    our $params;
    our ($PFNAME, $PF_REVISION_TIME);

    if ( ! getopts('rfnhm:', \%options) || @ARGV != 0 ) {
        pod2usage({-exitval => 2, -verbose => 2}) ;
    }

    pod2usage({-exitval => 2, -verbose => 2}) if $options{'h'};

    elog_init($0,@ARGV) ;

    # Load parameter file
    pfrequire($PFNAME, $PF_REVISION_TIME);
    $params = pfget($PFNAME, "");

    # Parse command line options
    if ($options{'f'} and ! $options{'m'}) {
        elog_die("ERROR: Need flag '-m email' to use the '-f' option");
    }

    savemail() if $options{'f'};

    elog_notify('') ;
    elog_notify("$0 @ARGV") ;
    elog_notify("Starting at ".strydtime($start)." on ".my_hostname()) ;
    elog_notify('') ;

    if ($options{'n'}) {
        elog_notify("**********************") ;
        elog_notify("**** DRY/NULL RUN ****") ;
        elog_notify("**********************") ;
    }

    #
    # We need dbadd
    #
    $dbadd = can_run('dbadd') or log_die("dbadd missing from PATH:".path()) ;

    #
    # Verify Database paths are set and that the source databases exist
    #
    foreach my $db_name (keys ($params->{'database_paths'})){
        elog_debug("validating $db_name subkeys\n");
        _validate_dbpath_subkeys($db_name);
        my $db_path = $params->{'database_paths'}{$db_name}{'db'};
        elog_debug("validating $db_name wfdisc exists\n");
        _validate_wfdisc_exists($db_path);
    }

    #
    # Run external commands
    #
    foreach my $d (keys($params->{'database_paths'})){

        print "GOT HERE\n";

        #
        # Build temp vars
        #
        my $d_db = $params->{'database_paths'}{$d}{'db'};
        my $d_new = $params->{'database_paths'}{$d}{'new'};
        my $d_temp = $params->{'database_paths'}{$d}{'temp'};

        #
        # Clean old temp files
        #
        elog_notify("\tClean temp tables for $d") ;

        remove_table_temp_file( "${d_temp}.lastid" ) ;
        remove_table_temp_file( "${d_temp}.sitechan" ) ;

        #
        # Build sitechan table
        #
        elog_notify("$dbadd -a $d_db.wfdisc $d_temp.sitechan") ;
        my_run("$dbadd -a $d_db.wfdisc $d_temp.sitechan  >& /dev/null") unless $options{'n'} ;

        #
        # Move sitechan table
        #
        elog_notify("\tMove temp file: [mv $d_temp.sitechan,$d_new.sitechan]") ;
        unless ( $options{'n'} ) {
            move("$d_temp.sitechan","$d_new.sitechan") or
            log_die("ERROR: Cannot move file $d_temp.sitechan to $d_new.sitechan");
        }

        #
        # Remove lastid file
        #
        remove_table_temp_file( "${d_temp}.lastid" ) ;

        elog_notify("") ;

    }

    restart_systems() if $options{'r'} ;

    my $end = now() ;
    my $run_time_str = strtdelta($end - $start) ;
    $start = strydtime($start) ;
    $end = strydtime($end) ;

    elog_notify("\n\n----------------- END -----------------\n\n") ;
    elog_notify("Start: $start End: $end") ;
    elog_notify("Runtime: $run_time_str") ;



    sendmail('dbwfserver_ta_setup: Success',$options{'m'}) if $options{'m'} and $options{'f'} ;

    return (0);
}

#
# Run main()
#
exit(main(@ARGV));

__END__

=pod

=head1 NAME

dbwfserver_ta_setup - Build subset for sitechan table for the WaveformServer

=head1 SYNOPSIS

dbwfserver_ta_setup [-h] [-n] [-d] [-f] [-m email]

=head1 SUPORT

No BRTT support == contact ANF Support <support@anf.ucsd.edu>

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h>

Produce this documentation

=item B<-n>

Test  mode/dry  run.  Does not delete, copy or move  any file or folder.

=item B<-r>

Restart all running procs on the real-time system at the end of the script.

=item B<-f>

Force email at end of script. The default is to send emails only on errors. Needs -m flag.

=item B<-m email>

Email this address in case of error or if -f flag is set.


=back

=head1 DESCRIPTION

dbwfserver_ta_setup uses the dbadd(1) command to build new sitechan tables for
the Inframet, Seismic and SOH instances of the WaveformServers of the TA
daatasets and one for ANZA. This should run every day so any new sta:chan entry
in the source database wfdisc will be recognized by the software. After
creating the new sitechan tables the software will move them to the production
paths and then restart the servers. By default the script will only email on
errors. If the -f flag is set then an email will be produced on every run.

=head1 BUGS AND CAVEATS

The -r option will run the command rtkill -l and will parse for
all lines with the "on" status. Then it will restart all of those
procs with the rtkill command.

=head1 ENVIRONMENT

The Antelope environment must be set correctly.

=head1 AUTHORS

Juan C. Reyes
Geoff Davis
<support@anf.ucsd.edu>


=head1 SEE ALSO

Perl(1)
dbadd(1)

=cut
# vim:ft=perl
