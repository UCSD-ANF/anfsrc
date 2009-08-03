use Datascope ;
use sysinfo;
use archive;
use Getopt::Std;
use IO::Handle;
#use FileHandle ":clearerr";
use POSIX ":sys_wait_h";


our($opt_v, $opt_m, $opt_v) ;
our($PF,$DB);
our(@errors,$Problems,%table);
our(@stations,@db_stations,$section);

######################
#                    #
#  Program setup     #
#                    #
######################

    $pgm = $0;
    elog_init($pgm, @ARGV);
    $cmd = "\n\t$0 @ARGV" ;
    $start = now();


    if ( ! &getopts('dvm:p:s:') || @ARGV != 1 ) { 
      $usage  = "\n\n\tUsage: $0 [-v][-d] [-s sta_regex] \n";
      $usage .= "\t\t[-p pf] [-m mail_to] DB \n\n";
      elog_and_die( $usage );
    }

    $DB    = $ARGV[0];

    #
    # Implicit flag
    #
    $opt_v      = defined($opt_d) ? $opt_d : $opt_v ;    

    #
    # Init mail
    #
    elog_notify("Initialize mail") if $opt_d && $opt_m;
    savemail() if $opt_m ; 

    elog_notify( $cmd ) if $opt_v;
    elog_notify ("Starting execution at ".strydtime(now())." on ".`uname -n`) if $opt_v;

    #
    # Get parameters
    #
    elog_notify("Getting params") if $opt_d;
    $PF         = $opt_p || "rsync_baler.pf" ;
    %pf = getparam($PF);

######################
#                    #
#  Sanity Check      #
#                    #
######################
    elog_notify("Sanity check") if $opt_d;
    elog_notify("\t\tLook for data directory") if $opt_d;
    if(! -e $pf{local_data_dir} )  {
        elog_and_die("Can't access dir => $pf{local_data_dir}.");
    }

    elog_notify("\t\tLook for DB") if $opt_d;
    if(! -e ${DB} )  {
        elog_and_die("Can't access DB => ${DB}.");
    }

    elog_notify("\t\tCheck for siblings") if $opt_d;
    #
    #get rid of arguments if any
    #
    @temp = split(/ /,$0);
    #
    #get rid of abs-path
    #only need the last
    #
    @temp = split(/\//,shift(@temp));
    $my_cmd = pop(@temp);
    if ( check_ps($my_cmd) != 1 ) { 
        elog_and_die("Another copy of $my_cmd running.");
    }

######################
#                    #
#  Get station list  #
#  from database     #
#                    #
######################
    @db_stations = get_stations($DB);

######################
#                    #
#  Start sync of data#
#                    #
######################
foreach $folder ( @{$pf{remote_folder}} ) {
    $section++;
    elog_notify("Now FOLDER:$folder IT:$section") if $opt_d;
    @stas = @db_stations;
    STATION: while ( 1 ) {

        $active_pids = 0 ;
        for my $key ( keys %table ) {
            elog_notify("STATION: $key") if $opt_d;
            if ( $table{$key}{$section}{PID} ) { 
                $resp = waitpid($table{$key}{$section}{PID},WNOHANG);
                elog_notify("\tWAITPID: PID RESP = $resp and $?") if $opt_d;
                if ($resp == -1) {  
                    elog_notify("\t\tNo child running. RESP = $resp and $?") if $opt_d;
                }
                elsif (WIFEXITED($?)) { 
                    elog_notify("\t\tInoperative $key => $table{$key}{$section}{PID} RESP = $resp and $?") if $opt_d;
                    elog_notify("\tDone sync of $station:$folder") if $opt_v;
                    $table{$key}{$section}{END}   = now();
                    $table{$key}{$section}{PID}       = 0; 
                }
                else{
                    elog_notify("\t\tActive $key => $table{$key}{$section}{PID} RESP = $resp and $?") if $opt_d;
                    ++$active_pids; 
                }
            }
        }
        elog_notify("\t\t$active_pids active pid's") if $opt_d;

        if ( $active_pids < $pf{max_procs} && scalar @stas ) {
            $station = pop(@stas);
            if ( $ip_sta=get_ip($DB,$station) ) {
                if( check_ps($ip_sta) ) { 
                        problem("Process running on $ip_sta ($station). Skipping!."); 
                        next STATION;
                }

                elog_notify("\tStart sync of $station:$folder") if $opt_v;

                #
                # Prepare Variables and Folders
                #
                $local_path = "$pf{local_data_dir}/$station";
                $log = "$local_path/log";
                if(! -e $local_path) { makedir($local_path); }
                if(! -e $log) { makedir($log); }
                $log .= "/${station}_${section}";
                open (LOGFILE , ">$log") or elog_and_die("Can't open logfile $log: $!");
                close LOGFILE;
                #
                # Start child
                if ($folder =~ /html/) { $remote_path = "http://$ip_sta:$pf{http_port}/$folder"; }
                else { $remote_path = "ftp://$ip_sta:$pf{ftp_port}/$folder"; }
                $pid=new_child($station,$remote_path,$local_path,$log);

                $LOGFILE = "${station}_${pid}";
                open ($LOGFILE , "<$log") or elog_and_die("Can't open logfile $log: $!");

                #
                # Store data in hash element
                #
                $table{$station}{$section}{PID}           = $pid;
                $table{$station}{$section}{LOGPNTR}       = $LOGFILE;
                $table{$station}{$section}{FOLDER}        = $folder;
                $table{$station}{$section}{IP}            = $ip_sta;
                $table{$station}{$section}{LOCAL_DIR}     = $local_path;
                $table{$station}{$section}{LOGFILE}       = $log;
                $table{$station}{$section}{START}         = now();

                elog_notify( "\t\t".strydtime($table{$station}{$section}{START}) ) if $opt_d;


                if($opt_d) {
                    elog_notify("\t\tNew HASH for $station:");
                    for my $key ( keys %{$table{$station}{$section}} ) {
                            elog_notify("\t\t\t$key => $table{$station}{$section}{$key}\n");
                    }
                }
                ++$active_pids;
            } #end of if $address
            else { problem("No ip for station $station"); } 
        }

        if ( $active_pids == 0 && ! scalar @stas ) { last STATION; } 

        monitor_child(\%table);

    } #end of while $station

} #end of foreach $folder

    report(\%table);

###############################
# FUNCTIONS                   #
###############################


######################
#                    #
#  Report status     #
#                    #
######################
sub report {
    my $pid_tbl = shift;

    if ($opt_v || $opt_m) {
        elog_notify("=================================");
        elog_notify("=Report rsync_balers            =");
        elog_notify("=================================");
        for my $sta ( sort keys %$pid_tbl ) {
            elog_notify("=================================");
            elog_notify("STA: $sta");
            for my $folder ( sort keys %{$pid_tbl->{$sta}} ) {
                $total = strtdelta($pid_tbl->{$sta}->{$folder}->{END} - $pid_tbl->{$sta}->{$folder}->{START});
                elog_notify("---------------------------------");
                elog_notify("\tFOLDER => ".$pid_tbl->{$sta}->{$folder}->{FOLDER} );
                elog_notify("\tFILES  => ".$pid_tbl->{$sta}->{$folder}->{FILES} );
                elog_notify("\tSTART  => ".strydtime($pid_tbl->{$sta}->{$folder}->{START}) );
                elog_notify("\tEND    => ".strydtime($pid_tbl->{$sta}->{$folder}->{END}) );
                elog_notify("\tTOTAL  =>  $total");
                if ( $pid_tbl->{$sta}->{$folder}->{ERROR} ) {
                    elog_notify("\tERRORS => ".$pid_tbl->{$sta}->{$folder}->{ERROR} );
                }
            }
            elog_notify("=================================");
        } 
    }

    if (@errors) {
        elog_notify("=================================");
        elog_notify("=Problems:                      =");
        elog_notify("=================================");
        $Problems = 0 ;
        foreach (@errors) {
            $Problems++ ;
            elog_notify("\n");
            elog_complain("Problem #$Problems") ;
            elog_complain("\t\t$_");
            elog_notify("\n");
        }
    }

    if ($opt_m) { 
        sendmail("REPORT ON $0 $host ", $opt_m); 
        savemail(); 
    }
}

######################
#                    #
#  Start new child   #
#                    #
######################
sub new_child { 
    my $station   = shift;
    my $remote_path= shift;
    my $local_path= shift;
    my $log_file  = shift;
    my $resp    = 0; 
    my $LOGFILE   = '';
    my $flags; 

    #
    #To test run sleep
    #
    #$random = int(rand(10));
    #$args = "sleep $random ";
    if ($remote_path =~ /ftp:/) { $flags = "--passive-ftp --continue --timestamping "; }
    $args = "wget --no-verbose --recursive --no-directories $flags -o $log_file -P $local_path \"$remote_path\" ";

    elog_notify("\t\t$args") if $opt_v;
    #elog_notify("TETS: $test");

    $resp = fork();
    if (! $resp) { exec($args); }

    if(pid_exists($resp)){ 
        elog_notify("\t\tPID:$resp") if $opt_d;
        return $resp;
    }
    problem("PID:$resp for $station $ip process. Skipping!");
    return 0; 
}

######################
#                    #
#  Monitor child     #
#                    #
######################
sub monitor_child { 
    my $ptable = shift;
    my $active_pids;
    my $log;
    my $pid;
    my $temp_regex;

    for my $sta ( keys %$ptable ) {
        for my $folder ( sort keys %{$ptable->{$sta}} ) {
            $log = $ptable->{$sta}->{$folder}->{LOGPNTR};
            $pid = $ptable->{$sta}->{$folder}->{PID};

            if (!defined($log)) { next; }
            elog_notify("reading $sta logfile") if $opt_d;

            #
            #read from last position 
            #
            while (<$log>){
                elog_notify("\t$sta || $_") if $opt_d;
                if ($_ =~ m/^.*RETR (.*) ... done.$/) { 
                    $ptable->{$sta}->{$folder}->{FILES} = " $1 |".$ptable->{$sta}->{$folder}->{FILES}; 
                }
                elsif ($_ =~ m/.*"($ptable->{$sta}->{$folder}->{LOCAL_DIR})\/(.*)".*/) { 
                    $ptable->{$sta}->{$folder}->{FILES} = " $2 |".$ptable->{$sta}->{$folder}->{FILES}; 
                }
                elsif ($_ =~ m/ERROR/) { 
                    $ptable->{$sta}->{$folder}->{ERROR} = " $_ |".$ptable->{$sta}->{$folder}->{ERROR}; 
                    problem("$sta:$folder - $_");
                }
            }

            #
            #This will clear EOF flag on pointer
            #
            $log->clearerr();
        }
    }
}

######################
#                    #
#  Get IP from DB    #
#                    #
######################
sub get_ip {
    my $db     = shift;
    my $sta    = shift;
    my $address;
    my $table  = $pf{db_table};
    my $column = $pf{db_table_cl};

    @db = dbopen ( $db, "r" ) or elog_and_die("Can't open DB: $db"); 
    if(@db == NULL) { elog_and_die("NULL value for DB: $db"); };  
    @db = dblookup(@db, "", $table, "", "");
    @db = dbsubset ( @db, " sta =~ /$sta/ ");
    @db = dbsort( @db,"time" );
    $nrecords = dbquery(@db,dbRECORD_COUNT) ; 

    if ($nrecords) {
        $db[3]  =  $nrecords - 1;
        $address=  dbgetv(@db, $column); 
        $address=~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
        elog_notify("\t\tIP=$1") if $opt_d;
        return $1;
    }
    else { problem("No records for sta $sta in DB $db") }

    return 0; 
}

######################
#                    #
#  Get Stas from DB  #
#                    #
######################
sub get_stations {
  my $db_name = shift;
  my $table  = $pf{db_sta_table};
  my $column = $pf{db_sta_table_cl};
  my $string = $pf{db_sta_table_st};
  my @sta_array;
  my @db;

    @db = dbopen ( $db_name, "r" ) or elog_and_die("Can't open DB: $db_name"); 
    $db = dbquery (@db, "dbDATABASE_NAME") ; 
    $dbpath = dbquery (@db, "dbDBPATH") ; 
    @db = dblookup(@db, "", $table , "", "");
    @db = dbsubset ( @db, " $column =~ /$string/ ");
    @db = dbsort ( @db, "-u", "sta");
    @db = dbsubset ( @db, "sta =~ /$opt_s/") if $opt_s;

    $nrecords = dbquery(@db,dbRECORD_COUNT) ; 
    elog_notify("$nrecords records in DB $db") if $opt_d;
    for ( $db[3] = 0 ; $db[3] < $nrecords ; $db[3]++ ) { 
        $sta = dbgetv(@db, 'sta'); 
        push @sta_array, $sta;
    }  
    elog_notify("\t@sta_array") if $opt_d;
    return @sta_array;
}

######################
#                    #
#  Read PF file      #
#                    #
######################
sub getparam { # %pf = getparam($PF);
    my ($PF) = @_ ;
    my ($subject);
    my (%pf) ;

    foreach my $value (qw/local_data_dir remote_folder 
                        ftp_path db_table db_table_cl 
                        db_sta_table db_sta_table_cl http_port
                        db_sta_table_st max_procs ftp_port/){
        $pf{$value} = pfget($PF,$value);
        if( ! defined( $pf{$value}) ) { elog_and_die("Missing value for $value in PF:$PF"); }
        elog_notify( "\t\t$value -> $pf{$value}") if $opt_d;
    }

    return (%pf);
}

######################
#                    #
# Check processes    #
# for string         #
#                    #
######################
sub check_ps {
    my $string  = shift;
    my $line    = '';
    my $results = 0;

    open $output, "-|", "ps -ef" or elog_and_die("Can't run ps -ef:$!");
    while(<$output>) {
        $line=$_;
        if ($line =~ m/$string/) { $results ++; }
    }
    close $output;
    return $results;
}

######################
#                    #
# update to elog_die #
#                    #
######################
sub elog_and_die {
    my $msg = shift;

    if ($opt_m) { 
        problem($msg);
        sendmail("ERROR: $0 DIED ON host $host", $opt_m); 
    }
    elog_die($msg);
}

######################
#                    #
# Report problems    #
#                    #
######################
sub problem { # use problem("log of problem");
    my $text = shift; 

    push(@errors,$text);

    if ($opt_v) {
        $Problems++ ;
        elog_notify("\n");
        elog_complain("Problem #$Problems") ;
        elog_complain("\t\t$_");
        elog_notify("\n");
    }
}
