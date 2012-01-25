#
#   update_baler44_firmware: script to update baler44 firmware remotely 
#   author: Juan C. Reyes
#   email:  reyes@ucsd.edu
#   No BRTT support
#

use Expect;
use archive;
use sysinfo;
use Net::Ping;
use Datascope;
use File::Spec;
use Pod::Usage "pod2usage";
use Getopt::Std "getopts";
use IPC::Cmd qw/can_run run/;


select STDOUT; $| = 1;
select STDERR; $| = 1;
#
#  Program setup
#
#{{{
    $start = now();
    $parent = $$;

    pod2usage({-exitval => 2, -verbose => 2}) if ( ! getopts('dnhu:p:s:r:m:') || @ARGV > 2 || @ARGV < 1 );

    pod2usage({-exitval => 2, -verbose => 2}) if $opt_h;

    elog_init($0,@ARGV);

    elog_notify('');
    elog_notify("$0 @ARGV");
    elog_notify("Starting execution at ".strydtime($start)." on ".my_hostname());
    elog_notify('');
    elog_notify('');

    if ( @ARGV > 1 ) {
        $database = $ARGV[0];
        $firmware = $ARGV[1];
        $interactive = 0;
        elog_notify("Configuration: DATABASE");
        elog_notify("\tDatabase: [$database]");
        elog_notify("\tFirmware: [$firmware]");
        elog_notify("");
    } else {
        $firmware = $ARGV[0];
        $interactive = 1;
        elog_notify("Configuration: INTERACTIVE");
        elog_notify("\tFirmware: [$firmware]");
        elog_notify("");
    }

    $opt_u ||= 'root2';
    $opt_p ||= 'root2';
    $opt_m ||= 'mnt';

    $database = File::Spec->rel2abs( $database ) ;
    $firmware = File::Spec->rel2abs( $firmware ) ;


    elog_die("Cannot find file [$firmware]") unless -f $firmware;
    elog_die("[$firmware] not a valid firmware file") unless $firmware =~ /b44update-.*-16K.*/;
    # example of a firmware file b44update-20110801B-16K-sg.tar.jz.asc

    #
    ## Set IPC::Cmd options
    #
    $IPC::Cmd::VERBOSE = 1 if $opt_d;

    #
    # We want access to ssh and scp
    #
    $ssh = can_run('ssh') or log_die("ssh missing on PATH:".path());
    $scp = can_run('scp') or log_die("scp missing on PATH:".path());

    #
    # Verify Database
    #
    unless ( $interactive ) {
        elog_notify("Opening $database:");
        @db = dbopen ( $database, "r" ) or log_die("Can't open DB: $database"); 
        @db_ip = dblookup(@db, "", "staq330" , "", "");
        table_check(\@db_ip);
    }

#}}}

#
#  Main
#
#{{{

    if ( $interactive ) {

        elog_notify("Running in INTERACTIVE mode");

        while (1) {
            print "\nIP of the Baler44 to upgrade (black to end script)?  ";
            $ip = 0;
            chomp ($ip = <STDIN>);

            last unless $ip;
            elog_notify("");
            elog_notify("[$ip]");

            elog_complain("\tERROR: Not a valid IP address") unless $ip =~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
            next unless $1; 

            update_sta($1); 

            elog_notify("\tDone"); 

        }

    } else {

        $stations = get_stations_from_db(); 

        STATION: foreach $sta (sort keys %$stations) {
            elog_notify("");
            elog_notify("[$sta]");

            my $table = $stations->{$sta};
            my $ip = $table->{ip};

            elog_complain("\tERROR: No IP") unless $ip;
            next STATION unless $ip;

            update_sta($ip); 

            elog_notify("\tDone"); 

        }

    }

    $end = now();
    $run_time_str = strtdelta($end - $start);
    $start = strydtime($start);
    $end = strydtime($end);

    elog_notify("\n\n----------------- END -----------------\n\n");
    elog_notify("Start: $start End: $end");
    elog_notify("Runtime: $run_time_str");

    exit 0;

#}}}

sub update_sta { 
#{{{
        my $ip = shift;
        elog_complain("\tCannot update without IP:[$ip]") unless $ip;

        elog_notify("\tIP: $ip"); 

        #
        # Ping the station
        #
        $p = Net::Ping->new("tcp", 10);
        $p->port_number(5381);
        elog_complain("\tERROR: Not Responding!!!!") unless $p->ping($ip);
        return unless $p->ping($ip);
        undef($p);

        #
        # Verify station's firmware
        #
        elog_notify("\tVerify firmware");
        $error = 0;
        $ver = '';
        $newdata = '';
        $cmd=Expect->spawn("ssh -p 5386 root2\@$ip");
        elog_notify("\t$_") foreach $cmd->command();
        $cmd->max_accum($cmd->max_accum()*10);
        $cmd->exp_internal(1) if $opt_d;
        $cmd->log_stdout(0);
        $cmd->log_file(\&myloggerfunc);

        $cmd->expect(300,
                ['-re', qr/yes\/no/i , sub {my $exp = shift; 
                                        $exp->send("yes\r");
                                        elog_complain("\tAdd host to list");
                                        exp_continue; }],
                [qr/password:/ => sub { my $exp = shift;
                                        $exp->send("$opt_p\r");
                                        elog_complain("\tForward password");
                                        exp_continue; } ],
                [qr/denied/ => sub { $error = 1; elog_notify("\tERROR: Wrong username:password"); } ],
                [qr/closed/ => sub { my $exp = shift; 
                                        $error = 1;
                                        elog_notify("\tERROR: ".$exp->before().$exp->match().$exp->after()); } ],
                [qr/timeout/ => sub { my $exp = shift; 
                                        $error = 1; 
                                        elog_complain("\tERROR timeout: ".$exp->match());} ],
                [qr/(%|>|#|\$)/ => sub {my $exp = shift; 
                                        $exp->send("mkdir /$opt_m/admin/; rm /$opt_m/admin/b44update-*.tar.jz.asc; awk '/BALER44-(.*)-16K/ {print}' /tmp/stats.html; echo 'do''ne';\r");
                                        exp_continue;}],
                [EOF => sub {elog_complain("\tEOF"); }],
                [qr/done/ => sub { } ]);
        if ( $error ) {
            elog_complain("\tExit status => ". $cmd->exitstatus());
            elog_complain("\tERROR on last command. ".  $cmd->error());
            $cmd->soft_close();
            return;
        }
        $newdata =~ /.* BALER44-(\S*)-16K .*/;
        elog_complain("\tERROR on regex for version of firmware:\n$newdata") unless $1;
        $ver = $1 || 0;
        elog_complain("\tVersion => $ver");
        if ( $cmd->exitstatus() ) {
            elog_complain("\tExit status => ". $cmd->exitstatus());
            elog_complain("\tERROR on last command. ".  $cmd->error());
            $cmd->soft_close();
            return;
        }
        $cmd->soft_close();

        #
        # compare versions
        #
        elog_complain("\tUpgrade to => $firmware");
        $firmware =~ /-(\S*)-16K-/;
        if ( $1 == $ver ) {
            elog_complain("System already using version $ver from file $firmware");
            return;
        }

        elog_notify("\tEnd of test run for $ip") if $opt_n;
        return if $opt_n;

        #
        # Upload the file to the /mnt/admin folder
        #
        elog_notify("\tUpload $firmware");
        $cmd=Expect->spawn("scp -P 5386 $firmware root2\@$ip:/$opt_m/admin/");
        elog_notify("\t$_") foreach $cmd->command();
        $cmd->expect(300,
                [qr/yes/ , sub {my $exp = shift; 
                                        $exp->send("yes\r");
                                        elog_complain("\tAdd host to list");
                                        exp_continue; }],
                [qr/password:/ => sub { my $exp = shift;
                                        $exp->send("$opt_p\r");
                                        elog_complain("\tForward password");
                                        exp_continue; } ],
                [qr/denied/ => sub { elog_notify("\tERROR: Wrong username:password"); } ],
                [qr/closed/ => sub { my $exp = shift;
                                        elog_notify("\tERROR: ".$exp->before().$exp->match().$exp->after()); } ],
                [EOF => sub {elog_complain("\tEOF"); }],
                [timeout => sub { elog_complain("\tERROR timeout");} ],
                '-re', '\#');
        if ( $cmd->exitstatus() ) {
            elog_complain("\tExit status => ". $cmd->exitstatus());
            elog_complain("\tERROR on last command. ".  $cmd->error());
            $cmd->soft_close();
            return;
        }
        $cmd->soft_close();

        elog_notify("\tDone uploading $firmware");

        #
        # Reboot system
        #
        elog_notify("\tReboot system");
        $newdata = '';
        $cmd=Expect->spawn("ssh -p 5386 root2\@$ip");
        elog_notify("\t$_") foreach $cmd->command();
        $cmd->max_accum($cmd->max_accum()*10);
        $cmd->exp_internal(1) if $opt_d;
        $cmd->log_stdout(0);
        $cmd->log_file(\&myloggerfunc);

        $cmd->expect(300,
                ['-re', qr/yes\/no/i , sub {my $exp = shift; 
                                        $exp->send("yes\r");
                                        elog_complain("\tAdd host to list");
                                        exp_continue; }],
                [qr/password:/ => sub { my $exp = shift;
                                        $exp->send("$opt_p\r");
                                        elog_complain("\tForward password");
                                        exp_continue; } ],
                [qr/denied/ => sub { elog_notify("\tERROR: Wrong username:password"); } ],
                [qr/closed/ => sub { my $exp = shift;
                                        elog_notify("\tERROR: ".$exp->before().$exp->match().$exp->after()); } ],
                [qr/timeout/ => sub { my $exp = shift; elog_complain("\tERROR timeout: ".$exp->match());} ],
                [qr/(%|>|#|\$)/ => sub {my $exp = shift; 
                                        $exp->send("touch /tmp/turnoff; echo 'do''ne';\r");
                                        exp_continue;}],
                [EOF => sub {elog_complain("\tEOF"); }],
                [qr/done/ => sub { } ]);
        if ( $cmd->exitstatus() ) {
            elog_complain("\tExit status => ". $cmd->exitstatus());
            elog_complain("\tERROR on last command. ".  $cmd->error());
            $cmd->soft_close();
            return;
            next STATION;
        }
        $cmd->soft_close();
        elog_notify("\tDone rebooting system.");

        return;
#}}}
}

sub get_stations_from_db {
#{{{
    my ($dlsta,$net,$sta);
    my %sta_hash;
    my @db_1;
    my $nrecords;
    my $ip;

    #
    # Get stations with baler44s
    #
    elog_notify("dbsubset ( endtime == NULL)") if $opt_d;
    @db_ip = dbsubset ( @db_ip, "endtime == NULL");

    elog_notify("dbsubset ( sta =~ /$opt_s/)") if $opt_d && $opt_s;
    @db_ip = dbsubset ( @db_ip, "sta =~ /$opt_s/") if $opt_s;

    elog_notify("dbsubset ( sta !~ /$opt_s/)") if $opt_d && $opt_r;
    @db_ip = dbsubset ( @db_ip, "sta !~ /$opt_r/") if $opt_r;

    $nrecords = dbquery(@db_ip,dbRECORD_COUNT) ; 


    for ( $db_ip[3] = 0 ; $db_ip[3] < $nrecords ; $db_ip[3]++ ) { 

        ($dlsta,$net,$sta,$ip) = dbgetv(@db_ip, qw/dlsta net sta inp/); 

        elog_notify("[$sta] [$net] [$dlsta] [$ip]") if $opt_d;

        $sta_hash{$sta}{dlsta}      = $dlsta; 
        $sta_hash{$sta}{net}        = $net; 

        # regex for the ip
        $ip =~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
        $sta_hash{$sta}{ip} = $1 if $1; 
        elog_complain("Failed grep on IP $database.staq330{inp}->(ip'$ip',dlsta'$dlsta')") unless $1;

        $sta_hash{$sta}{ip} ||= 0; 

    }


    eval { dbclose(@db_ip);  };

    return \%sta_hash;
#}}}
}

sub table_check {
#{{{
    my $db = shift;

    elog_notify("Verify Database: ".dbquery(@$db,"dbDATABASE_NAME") ) if $opt_;

    elog_die( dbquery(@$db,"dbTABLE_NAME")." not available.") unless dbquery(@$db,"dbTABLE_PRESENT");

    elog_notify("\t".dbquery(@$db,"dbDATABASE_NAME")."{ ".dbquery(@$db,"dbTABLE_NAME")." }: --> OK") if $opt_;

#}}}
}


sub myloggerfunc{
#{{{
    my ($data) = @_;
    $data =~ s/\r//g;
    $newdata .=  $data;
#}}}
}

    pod2usage({-exitval => 2, -verbose => 2}) if ( ! getopts('dnhu:p:s:r:m:') || @ARGV > 2 || @ARGV < 1 );
__END__
#{{{
=pod

=head1 NAME

update_baler44_firmware - upload new firmware to balers

=head1 SYNOPSIS AUTOMATIC

update_baler44_firmware [-h] [-n] [-d] [-u user] [-p password] [-s select] [-r reject] [-m media] database firmware_file

=head1 SYNOPSIS INTERACTIVE

update_baler44_firmware [-h] [-n] [-d] [-u user] [-p password] [-m media] firmware_file

=head1 SUPORT

No BRTT support == contact Juan Reyes <reyes@ucsd.edu>

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h> 

Produce this documentation

=item B<-n> 

Test  mode/dry  run.  Does not delete, copy or move  any file or folder.

=item B<-d> 

Debug mode

=item B<-s select_regex> 

Regex to select stations from the database. [ONLY ON AUTOMATIC RUN]

=item B<-r regex> 

Regex to reject stations from the database (all except these). [ONLY ON AUTOMATIC RUN]

=item B<-u username> 

Username to log into Balers. Defaults to "root2"

=item B<-p password> 

Password to log into Balers. Defaults to "root2"

=item B<-m mountpoint> 

Base path to upload firmware file to.  Defaults to "mnt"


=back

=head1 DESCRIPTION

update_baler44_firmware  uploads new firmware to Baler44 using ssh 
connections. Needs database with staq330 table to run automatically or 
needs submit each IP by hand in interactive mode. In automatic database mode
you can specify a regex for select or a regex for reject for the stations
in the staq330 table. If the -n flag is used then the firts ssh to the station
will make sure that the /mnt/admin directory is in place and will query the 
status page for the current firmware version. It will stop before uploading the 
new firmwasre to the baler.

=head1 ENVIRONMENT

needs to have sourced $ANTELOPE/setup.csh.

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).

=cut
#}}}
