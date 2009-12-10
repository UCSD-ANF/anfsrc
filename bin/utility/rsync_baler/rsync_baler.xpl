#
#   rsync_baler: script to create a local copy of remote baler
#   author: Juan C. Reyes
#   email:  reyes@ucsd.edu
#   No BRTT support
#

#{{{
use strict;
use warnings;
use POSIX;
use sysinfo;
use archive;
use Net::FTP;
use Datascope ;
use Pod::Usage;
use IO::Handle;
use File::Fetch;
use Getopt::Std;
use IPC::Cmd qw[can_run run];


our($opt_r,$opt_s,$opt_h,$opt_v,$opt_m,$opt_p,$opt_d);
our($PF,%pf,$DB,@db,@db_sta,@db_ip,$dbname,$dbpath);
our($station,@errors,%table);
our(@db_stations,$running);
our($temp_sta,$pgm,$cmd,$ps_path);
our($start,$end,$run_time,$run_time_str,$type);
our($sta,@stas,$active_pids,$stations,$table,$folder);
our($pid,$log,$address,$ip_sta);
our($host,$key,$value,$file_fetch);
our($dlsta,$net,$ip);

#}}}

######################
#  Program setup     #
######################
#{{{
    $pgm = $0;
    elog_init($pgm, @ARGV);
    $cmd = "\n\t$0 @ARGV" ;
    $start = now();
    $host = my_hostname();

    if ( ! &getopts('hdvm:p:s:r:') || @ARGV != 1 ) { 
        pod2usage({-exitval => 2,
                   -verbose => 2});
    }

    if ( $opt_h ) { 
        pod2usage({-exitval => 2,
                   -verbose => 2});
    }

    #
    # Initialize  mail
    #
    if ($opt_m){
        elog_notify("Initialize mail") if $opt_d;
        savemail();
    }

    elog_notify( $cmd );
    elog_notify ("Starting execution at ".strydtime(now())." on ".my_hostname());

    #
    # Implicit flag
    #
    $opt_v      = defined($opt_d) ? $opt_d : $opt_v ;    

    #
    # Get parameters
    #
    elog_notify("Getting params") if $opt_d;
    $PF = $opt_p || "rsync_baler.pf" ;
    %pf = getparam($PF);

    #
    ## Set File::Fetch options
    #
    $File::Fetch::WARN      = 0 unless $opt_d; 
    $File::Fetch::DEBUG     = 1 if $opt_d; 
    $File::Fetch::TIMEOUT   = 0; 
    $File::Fetch::BLACKLIST = $pf{method_blacklist} if $pf{method_blacklist};

    #
    ## Set IPC::Cmd options
    #
    $IPC::Cmd::VERBOSE = 1 if $opt_d;

    #
    ## Check IPC Methods
    #
    if ($opt_d) {
        ### system path 

        ### check for features
        if (IPC::Cmd->can_use_ipc_open3){
            elog_notify("IPC::Open3 available: ".IPC::Cmd->can_use_ipc_open3(1));
        }
        else { elog_notify("IPC::Open3 available: 0"); }

        if (IPC::Cmd->can_use_ipc_run){
            elog_notify("IPC::Run available: ".IPC::Cmd->can_use_ipc_run(1));
        }
        else { elog_notify("IPC::Run available: 0"); }

        if (IPC::Cmd->can_capture_buffer){
            elog_notify("Can capture buffer: ".IPC::Cmd->can_capture_buffer);
        }
        else { elog_notify("Can capture buffer: 0"); }
    }

    #
    # Check if we have access to the software 
    #
    if ($pf{fix_mseed_cmd}) {
        $ps_path   = can_run('msfixoffsets') or elog_and_die("msfixoffsets is not installed or missing in PATH");
        elog_notify("msfixoffsets path=$ps_path") if $opt_d;
    }
    if ($pf{keep_miiseed_db}) {
        $ps_path   = can_run('miniseed2days') or elog_and_die("miniseed2days is not installed or missing in PATH");
        elog_notify("miniseed2days path=$ps_path") if $opt_d;
    }

    #
    # Init Database
    #
    $DB    = $ARGV[0];
    elog_notify("Opening $DB:") if $opt_d;
    @db = dbopen ( $DB, "r" ) or elog_and_die("Can't open DB: $DB"); 

    @db_sta = dblookup(@db, "", $pf{db_sta_table}, "", "");
    table_check(\@db_sta);

    if ($pf{db_sta_table} ne $pf{db_ip_table}) {
        @db_ip = dblookup(@db, "", $pf{db_ip_table} , "", "");
        table_check(\@db_ip);
    }
    else { @db_ip = @db_sta; }
#}}}

######################
#  Sanity Check      #
######################
#{{{
    if(! -e $pf{local_data_dir} )  {
        elog_and_die("Can't access dir => $pf{local_data_dir}.");
    }
#}}}

######################
#  Get station list  #
#  from database     #
#  or pf file        #
######################
#{{{
    if ( %{$pf{stations}} ) {
        while (  my ($dlsta,$net,$sta,$ip) = each  %{$pf{stations}} ) {
            elog_notify("From PF file: $dlsta:$net:$sta:$ip") if $opt_d;

            if ( $opt_s ) { next unless $sta =~ /$opt_s/; }
            if ( $opt_r ) { next if $sta =~ /$opt_r/; }

            $ip =~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
            $ip =  $1;
            $ip ||= get_ip($sta);
            if ($ip){ 
                $stations->{$sta}->{ip}=$ip; 
                $stations->{$sta}->{dlsta}=$dlsta; 
                $stations->{$sta}->{net}=$net; 
            }
            else { problem("No IP for station $sta.") if $opt_d; }
        }
    }
    else { $stations = get_stations(); }

    #
    # Cleaning up!
    #
    dbclose(@db_sta);
    if ($pf{db_sta_table} ne $pf{db_ip_table}) { dbclose(@db_ip); }
#}}}

######################
#  MAIN:             #
######################
#{{{
    @stas = keys %$stations;
    STATION: while ( 1 ) {
        $active_pids = check_pids($stations); 
        if ( $active_pids < $pf{max_procs} && scalar @stas ) {
            elog_notify("Stations in queue: @stas") if $opt_d;

            $temp_sta = pop(@stas);
            elog_notify("\tStarting sync of $temp_sta") if $opt_d;

            $stations->{$temp_sta}->{start} = now();
            $stations->{$temp_sta}->{pid}   = new_child($stations,$temp_sta);

            ++$active_pids;
        }
        if ( $active_pids == 0 && ! scalar @stas ) { last STATION; } 
    }

    @stas = keys %$stations;
    elog_notify("*** End rsync of ".scalar @stas." stations. ***");

    $end = now();
    $run_time = $end - $start;
    $run_time_str = strtdelta($run_time);
    $start = strydtime($start);
    $end = strydtime($end);

    elog_notify("Start: $start End: $end");
    elog_notify("Runtime: $run_time_str");
    elog_notify("Stations: @stas");
    sendmail("Done $0 on $host ", $opt_m) if $opt_m; 
#}}}

######################
#  Check on PID's    #
######################
sub check_pids {
#{{{
    my $ptable = shift;
    my $active_pids = 0 ;
    my $resp = 0;

    while ( my ($key,$value) = each  %$ptable ) {
            if ( $ptable->{$key}->{pid} ) { 
                $resp = waitpid($ptable->{$key}->{pid},WNOHANG);

                if ($resp == -1) {  
                    elog_notify("\t\tNo child running. RESP = $resp and $?") if $opt_d; 
                }
                elsif (WIFEXITED($?)) { $table->{$key}->{pid} = 0; }
                else{ ++$active_pids; }

            }
    }
    return $active_pids; 
#}}}
}

######################
#  Start new child   #
######################
sub new_child { 
#{{{
    my ($table,$station) = @_;
    my $ip      = 0;
    my $folder  = '';
    my $type    = '';
    my $resp    = 0; 
    my $file_removed = 0;
    my $f_removed = 0;
    my ($media,$local_path,$loc_file,$rem_file,$ftp);
    my ($nrecords,@temp_download,@dbwr,@dbr,@dbr_sub,$net);
    my ($avoid,$replace,$start_folder,$file,$size,$speed,$run_time);
    my ($port,@download,$start_sta,$start_file,$where,$attempts);
    my (@diff,$results,$run_time_str,$fixed_files,$dbout,$outcome);
    my ($end_file,$record,$dlsta,$time,$endtime,$dir,$dfile,$status);

    #
    # Producing child here...
    #
    $resp = fork();

    #
    # Is this parent or child???
    #
    if (! $resp) { 

        #
        #For child...
        #
        $start_sta = now();
        elog_notify("$station Start time ".strydtime($start_sta)) if $opt_v;

        #
        # Prepare Variables and Folders
        #
        $local_path = prepare_vars($station); 
        if (! $table->{$station}->{ip} ) { elog_and_die("No ip for station.",$station); }
        $ip     = $table->{$station}->{ip};
        $dlsta  = $table->{$station}->{dlsta};
        $net    = $table->{$station}->{net};

        #
        # Opend station database
        #
        $dbout = "$local_path/$pf{dbout}";
        elog_notify("$station Opening database ($dbout).") if $opt_d;
        if ( ! -e $dbout) {
            elog_notify("$station Creating new database ($dbout).") if $opt_d;
            dbcreate($dbout,"rsyncbaler",$local_path,0,0) or elog_and_die("Can't create output database $dbout",$station);
        }   
        elog_notify("$station Openning database table  ($dbout.rsyncbaler)") if $opt_d;
        @dbr  = dbopen_table($dbout.".rsyncbaler","r+") or elog_and_die("Can't open DB: $dbout",$station);


        #
        # Check if we need a new database
        #
        #$file_removed = 1 if ! -e "$local_path/$pf{miniseed_db_name}.wfdisc"; 

        #
        # For each of the folders and html files...
        #
        while( ($folder,$type) = each %{$pf{remote_folder}} ) {
            $fixed_files = 0;
            $start_folder = now();
            elog_notify("$station Start rsync of $folder ".strydtime($start_folder)) if $opt_d;
            if ($type eq 'ftp') {
                $port = $pf{ftp_port};
                $ftp = loggin_in($ip,$port,$station);

                #
                # Get files from dires
                #
                elog_notify("$station Reading remote directory $folder") if $opt_d;
                ($rem_file,$f_removed) = read_dir( $folder, $ftp );
                $file_removed = 1 if $f_removed;

                elog_notify("$station Reading local directory $local_path") if $opt_d;
                ($loc_file,$f_removed) = read_dir( $local_path );
                $file_removed = 1 if $f_removed;
                if ( $opt_d) {
                    print_files($rem_file,"$station Files on REMOTE folder");
                    print_files($loc_file,"$station Files on LOCAL folder");
                }
                $ftp->quit;

                #
                # Flag files for download
                #
                if ( $rem_file ) { @download = compare_dirs($loc_file,$rem_file,$dlsta,@dbr); }
                else { @download = () }
                if ( @download && $folder =~ /.*reservemedia.*/) {
                    problem("Secondary media in use. ($folder)",$station); 
                    $media = "reservemedia";
                }
                else { $media = "activemedia"; }
            }
            elsif ($type eq 'http') { 
                $port = $pf{http_port};
                $media = "http";

                $record = dbfind(@dbr, "dlsta == '$dlsta' && dfile == '$folder'", -1); 
                if( '-1' == $record ) { problem("Can't understand dlsta param ($dlsta) or file ($folder)",$station); }   
                elsif( '-2' != $record ) { 
                    @dbr_sub = dbsubset(@dbr, "dlsta == '$dlsta' && dfile == '$folder'" );
                    $dbr_sub[3]=0;
                    ($avoid,$replace) = dbgetv(@dbr_sub,qw/avoid replace/);
                    if ($avoid eq 'y') {
                        elog_notify("$station FILE:$folder flagged on db with 'avoid' flag. SKIPPING!") if $opt_v;
                        next;
                    }
                }
                else {
                    elog_notify("$station NEW: [ $dlsta | $folder ]") if $opt_d;
                    dbaddv(@dbr, "dlsta", $dlsta, "dfile", $folder );
                }
                push @download, $folder; 
            }
            else { elog_and_die("Can't interpret file/folder type ($type). Options: 'ftp' or 'http'.",$station); }

            #
            # Start the download.
            #
            FILE: foreach $file (@download) {
                $start_file = now();
                $where = 0;
                $outcome = "Start Download";

                #
                # Check if we have a limit of time
                #
                if ( $pf{max_child_run_time} ) { 
                    if ( int($pf{max_child_run_time}) < ($start_file - $start_sta) ) {
                        problem("Rsync exceeds allowed time set in max_child_run_time ($pf{max_child_run_time}).",$station);
                        last FILE;
                    }
                }
                if (-e "$local_path/$file") {
                    if ( unlink "$local_path/$file" ) { 
                        elog_notify("$station Success remove of previous file $local_path/$file") if $opt_v; 
                        $file_removed = 1;
                    }
                    else { 
                        problem("Can't delete previous file $local_path/$file",$station); 
                        next FILE;
                    }
                }

                #
                # Update DB
                #
                @dbr_sub = dbsubset(@dbr, "dlsta == '$dlsta' && dfile == '$file'" );
                $nrecords = dbquery(@dbr_sub,dbRECORD_COUNT) ; 
                if ($nrecords != 1) {
                    elog_and_die("Problems on database entry for dlsta=='$dlsta' && dfile=='$file' => $nrecords",$station);
                }
                $dbr_sub[3]=0;
                $attempts = dbgetv(@dbr_sub,'attempts');
                dbputv(@dbr_sub, 
                    "time", $start_file, 
                    "status", $outcome,
                    "dir",$local_path,
                    "net",$net,
                    "media",$media,
                    "sta",$station);

                #
                # Prepare download cmd
                #
                if ($type eq 'ftp') { $file_fetch = File::Fetch->new(uri => "$type://$ip:$port/$folder/$file"); }
                else { $file_fetch = File::Fetch->new(uri => "$type://$ip:$port/$file"); }

                elog_notify("$station Start download of ".$file_fetch->uri) if $opt_d;

                #
                # Run Fetch cmd. "extraction" 
                #
                eval {  $where = $file_fetch->fetch( to => "$local_path" ); };
                problem("File::Fetch ".$file_fetch->uri." ".$file_fetch->error(1)."$@",$station) if $@; 
                $end_file = now();
                $run_time= $end_file-$start_file;
                $run_time_str = strtdelta($run_time);

                # Update DB
                if ($type eq 'ftp') { $attempts++; }
                else { $attempts = 1; }
                dbputv(@dbr_sub, "endtime", $end_file, "attempts", $attempts);

                #
                # Variable $where is the full path of the downloaded file
                # only set on successful downloads. 
                #
                if( $where ) { 
                    elog_notify("$station Success in download of $file after $run_time_str") if $opt_d;

                    # Update DB
                    dbputv(@dbr_sub, "status", 'Downloaded');

                    #
                    # Verify bandwidth of ftp connection
                    #
                    if ( $pf{min_bandwidth} && $type eq 'ftp') {
                        $size = $rem_file->{$file}->{size} / 1024;
                        $speed = $size / $run_time;
                        elog_notify("$station $file Size:$size Kb  Time:$run_time secs Speed:$speed Kb/sec") if $opt_d;
                        if ( $speed < $pf{min_bandwidth}) {
                            problem("The calculated bandwidth ($speed)Kb/s is lower than the threshold in pf file ($pf{min_bandwidth})Kb/s",$station);
                        }

                        # Update DB
                        dbputv(@dbr_sub, "bandwidth", $speed);

                    }

                    #
                    # In case we need to fix the miniseed files...
                    #
                    if ( $pf{fix_mseed_cmd} && $type eq 'ftp') { 
                        fix_file($station,$where); 

                        # Update DB
                        dbputv(@dbr_sub, "fixed", "y");
                    }

                    #
                    # In case we need to maintain miniseed database
                    #
                    if ( $pf{keep_miniseed_db} && $type eq 'ftp') {
                        #
                        # Avoid if we need to rebuild db anyway.
                        #
                        if (! $file_removed) { 
                            mseed_db($local_path,$station,$where); 

                            # Update DB
                            dbputv(@dbr_sub, "mseeddb", "y");
                        }
                    }
                }
                
                #
                # If download failed...
                #
                else {
                    $run_time_str = strtdelta(now()-$start_file);
                    problem("Failed download of $file after $run_time_str",$station) if $opt_d;

                    # Update DB
                    dbputv(@dbr_sub, "status", 'Failed download');
                }
            } #end of foreach @downloads

            #
            # Done with folder
            # Print stats 
            #
            $run_time = now() - $table->{$station}->{start};
            $run_time_str = strtdelta($run_time);
            if ($opt_v) {
                $results = "\t\n\t\t$station: Done rsync of $folder";
                $results .= "\n\t\tDuration:  $run_time_str";
                $results .= "\n\t\tLocal_dir: $pf{local_data_dir}/$station/";
                $results .= "\n\t\tFlagged: ".@download." files";
                $results .= "\n\t\tFixed:  $fixed_files files";
                elog_notify("$results\n");
            }
        } # end of while $folders

        #
        # Cleaning up!
        #
        dbclose @dbr;

        #
        # Rebuild miniseed folder
        #
        #if ( $file_removed && $pf{keep_miniseed_db} ){
        #    clean_mseed_dir($local_path,$station,1);
        #    mseed_db($local_path,$station);
        #    problem("Rebuild miniSeed db in $local_path/$pf{miniseed_db_name}",$station);
        #}

        #
        # Calc the total time to rsync station
        #
        $run_time = now() - $table->{$station}->{start};
        $run_time_str = strtdelta($run_time);
        if ($opt_d) {
            $results = "\t\n\t\t$station: Done!";
            $results .= "\n\t\tDuration: $run_time_str";
            elog_notify("$results\n");
        }
        #
        # End of child
        #
        exit 0;
    }

    #
    # Return to parent
    #
    if(pid_exists($resp)){ 
        elog_notify("$station: PID=$resp") if $opt_d;
        return $resp;
    }
    problem("PID=$resp for $station $ip process. Skipping!",$station);
    return 0; 
#}}}
}

######################
#  Run fix file      #
######################
sub fix_file {
#{{{
    my $sta  = shift;
    my $file  = shift;
    my $cmd;
    my $success;
    my $error_code;
    my $full_buf;
    my $stdout_buf;
    my $stderr_buf;

    $cmd = "$pf{fix_mseed_cmd} $file";

    elog_notify("$sta $cmd") if $opt_d;

    ($success,$error_code,$full_buf,$stdout_buf,$stderr_buf) = run( command => $cmd, verbose => 0 );

    if (! $success && $pf{print_fix_errors} ) {
        problem("\t\nCmd:$cmd
            \n\tSuccess:$success
            \n\tError_code:$error_code
            \n\tStdout:@$stdout_buf
            \n\tStderr:@$stderr_buf",$station);
    }
    if ( $success && $opt_d ){
        elog_notify("\t\nStation:$station
            \n\tCmd:$cmd
            \n\tSuccess:$success
            \n\tError_code:$error_code
            \n\tStdout:@$stdout_buf
            \n\tStderr:@$stderr_buf");
    }
#}}}
}

######################
#  Update mSEED db   #
######################
sub mseed_db {
#{{{
    my $dir  = shift;
    my $sta  = shift;
    my $file  = shift;
    my $args;
    my $text;
    my $pid;
    my $cmd; 
    my $path;
    my $success;
    my $error_code;
    my $full_buf;
    my $stdout_buf;
    my $stderr_buf;

    if ( ! chdir($dir) ) { elog_and_die("Can't change to directory $dir : $!", $sta); }

    #
    # Fix the files in dir
    #
    if ( $pf{fix_mseed_cmd}) {
        opendir DIR, $dir or elog_and_die("Can't open dir:$dir: $!",$sta);
        for (readdir DIR) {
            if ( $_ =~ /.*($sta).*/ ){ fix_file($sta,"$dir/$_"); }
        }
    }
    closedir DIR;

    if ($file) {
        $cmd = "miniseed2days -d $pf{miniseed_db_name} $file;"; 
    }
    else {
        $cmd = "miniseed2days -d $pf{miniseed_db_name} *${sta}* ;"; 
    }
    elog_notify("$sta Creating miniseed database: $cmd ") if $opt_d;


    ($success,$error_code,$full_buf,$stdout_buf,$stderr_buf) = 
            run( command => $cmd, verbose => 0 );
    if (! $success && $pf{print_miniseed_errors} ){
        problem("\t\nCmd:$cmd\n\tSuccess:$success\n\tError_code:$error_code\n\tStdout:@$stdout_buf\n\tStderr:@$stderr_buf",$sta);
    }
    if ( $success && $opt_d){
        elog_notify("\t\nStation:$sta\t\nCmd:$cmd\n\tSuccess:$success\n\tError_code:$error_code\n\tStdout:@$stdout_buf\n\tStderr:@$stderr_buf");
    }
#}}}
}

######################
#  Remove mSEED dir  #
######################
sub clean_mseed_dir {
#{{{
    my $dir  = shift;
    my $sta  = shift;
    my $base = shift;
    local *DIR;

    opendir DIR, $dir or elog_and_die("Can't open dir:$dir: $!",$station);
    for (readdir DIR) {
        next if /^\.{1,2}$/;
        my $path = "$dir/$_";
        if ( $base && $_ =~ /($pf{miniseed_db_name})\..*/ ){
            unlink $path;
        }
        elsif (-d $path && $path =~ /^\d+$/ ) { 
            cleanup($path,$sta,0) if -d $path;
        }
        elsif (-f $path && $dir =~ /^\d+$/ ) { 
            unlink $path if -f $path;
        }
    }
    closedir DIR;
    if ($dir =~ /^\d+$/ && ! $base ) { 
        rmdir $dir or elog_and_die("Can't remove directory $dir $!",$sta);
    }
#}}}
}

######################
#  Print files       #
######################
sub print_files {
#{{{
    my $list = shift;
    my $type = shift;
    my $file;
    my $size = 0;
    my $text = '';
    my @total = ();

    foreach $file (sort keys %$list) {
        $size = $list->{$file}->{size};
        push @total, $file;
        $text .= "\t\tName: $file Size: $size\n";
    }
    elog_notify("$type ".scalar @total."\n$text");
    return 0;
#}}}
}

######################
#  Compare Dirs      #
######################
sub compare_dirs {
#{{{
  my ($local_files,$remote_files,$dlsta,@db)= @_;
  my (@db_sub,@flagged); 
  my ($rf,$lf,$record);
  my ($avoid,$replace);

    FILE: foreach $rf ( keys %$remote_files ) {
        $record = dbfind(@db, "dlsta == '$dlsta' && dfile == '$rf'", -1); 
        if( '-1' == $record ) { problem("Can't understand dlsta param ($dlsta) or file ($rf)",$station); }   
        elsif( '-2' != $record ) { 
            @db_sub = dbsubset(@db, "dlsta == '$dlsta' && dfile == '$rf'" );
            $db_sub[3]=0;
            ($avoid,$replace) = dbgetv(@db_sub,qw/avoid replace/);
            if ($avoid eq 'y') {
                elog_notify("$station FILE:$rf flagged on db with 'avoid' flag. SKIPPING!") if $opt_v;
                next FILE;
            }
            if ($replace eq 'y') {
                push @flagged, $rf;
                dbputv(@db_sub, 'status', 'Flagged' );
                elog_notify("$dlsta FILE:$rf flagged on db with 'replace' flag.!") if $opt_v;
                next FILE;
            }
        }
        else {
            elog_notify("$station NEW: [ $dlsta | $rf ]") if $opt_d;
            dbaddv(@db, "dlsta", $dlsta, "dfile", $rf );
        }
        foreach $lf ( keys %$local_files ) {
            if($lf eq $rf) {
                @db_sub = dbsubset(@db, "dlsta == '$dlsta' && dfile == '$rf'" );
                $db_sub[3]=0;
                if($local_files->{$lf}->{size} < $remote_files->{$rf}->{size}) {
                    dbputv(@db_sub, 'status', 'Flagged' );
                    push @flagged, $rf;
                    next FILE;
                }
                else { 
                    elog_notify("$station UPDATE: [ $dlsta | $rf | Downloaded ]") if $opt_d;
                    dbputv(@db_sub, "status", 'Downloaded');
                    next FILE;
                }
            }
        }
        push @flagged, $rf;
    } #end of foreach $rt


    return @flagged;
#}}}
}

######################
#  Login in to sta   #
######################
sub loggin_in {
#{{{
    my $my_ip   = shift;
    my $my_port = shift;
    my $station = shift;
    my $my_ftp;

    if ($my_ip && $my_port && $station) {
        eval {  
            $my_ftp=Net::FTP->new(Host=>$my_ip, Passive=>1, Timeout=>30, Port=>$my_port);
            if ($my_ftp) {
                $my_ftp->login();
                $my_ftp->binary();
            } 
            else  {
                elog_and_die("Can't ftp to $my_ip:$my_port : $@ ",$station);
            }
        }; # Eval ends.
        elog_and_die("Problem in ftp connection to $my_ip:$my_port. Error: $@",$station) if $@;
    }
    return $my_ftp;
#}}}
}

######################
#  Read rem/loc dir  #
######################
sub read_dir {
#{{{
   my $path     = shift;
   my $ftp_pnt  = shift;
   my %file     = (); 
   my @directory= ();
   my $removed  = 0;
   my $open;
   my $name;
   my $epoch;
   my $line;
   my $f;
   my @n;
   my @split_name;

    if(defined($ftp_pnt)) {
        @directory = $ftp_pnt->dir( $path) ;
        if(@directory){
            foreach $line (@directory) {
                next if $line =~ m/^d.+\s\.\.?$/;
                @n = (split(/\s+/, $line, 9));
                @split_name= split(/\//,$n[8]);
                $name = pop @split_name;
                $file{$name}{size} = $n[4];
            }
        }
    }
    else {
        $open = opendir DIR, $path or
        elog_and_die("Failed to open $path: $!");
        if ( $open ) {
            while($f = readdir DIR) {
                my $file = "$path/$f";
                if(-d "$file"){ next; } 
                elsif($f =~ /..-...._\d-\d+-\d+/ ){ 
                    unlink $file; 
                    $removed = 1;
                    problem("Removing incomplete file ($file).");
                } 
                else { $file{$f}{size} = (stat($file))[7]; }
            }
            close(DIR);
        }
    }

   return (\%file,$removed);
#}}}
}

######################
#  Prepare vars/files#
######################
sub prepare_vars {
#{{{
    my $station  = shift;
    my $local_path = '';
    my $log = ''; 

    if ( $station ) {
        $local_path = "$pf{local_data_dir}/$station";
        if(! -e $local_path) { makedir($local_path); }
        return $local_path;
    }
    else{
        elog_and_die("No value for station ($station) in function prepare_vars. ",$station);
    }
    return 0;
#}}}
}

######################
#  Get Stas from DB  #
######################
sub get_stations {
#{{{
    my $table  = $pf{db_sta_table};
    my $column = $pf{db_sta_table_cl};
    my $string = $pf{db_sta_table_st};
    my ($dlsta,$net,$sta);
    my %sta_hash;
    my @db;
    my $nrecords;
    my $ip;

    @db = dbsubset ( @db_sta, " $column =~ /$string/ ");
    @db = dbsort ( @db, "-u", "dlsta");
    @db = dbsubset ( @db, "sta =~ /$opt_s/") if $opt_s;
    @db = dbsubset ( @db, "sta !~ /$opt_r/") if $opt_r;

    $nrecords = dbquery(@db,dbRECORD_COUNT) ; 
    elog_notify("$nrecords records in DB $DB") if $opt_d;
    for ( $db[3] = 0 ; $db[3] < $nrecords ; $db[3]++ ) { 
        ($dlsta,$net,$sta) = dbgetv(@db, qw/dlsta net sta/); 
        $ip = get_ip($sta);
        if ($ip){ 
            $sta_hash{$sta}{ip}=$ip; 
            $sta_hash{$sta}{dlsta}=$dlsta; 
            $sta_hash{$sta}{net}=$net; 
            elog_notify("From database $sta:$ip") if $opt_d;
        }
        else { problem("No IP for station $sta.",$sta) if $opt_d; }
    }  

    return \%sta_hash;
#}}}
}

######################
#  Get IP from DB    #
######################
sub get_ip {
#{{{
    my $sta    = shift;
    my $address = '';
    my $nrecords = 0;
    my @db;


    if ($sta) {
        @db = dbsubset ( @db_ip, " sta =~ /$sta/ && endtime == NULL");
        $nrecords = dbquery(@db,dbRECORD_COUNT) ; 

        if ($nrecords == 1) {
            $db[3]  =  $nrecords - 1;
            $address=  dbgetv(@db, $pf{db_ip_table_cl}); 
            $address=~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
            return $1;
        }
        else { problem("Function get_ip return ($nrecords) records",$sta) if $opt_d; }
    }
    else { problem("No value passed for station ($sta) in get_ip function.",$sta) if $opt_d; }
    return 0;
#}}}
}

######################
#  Read PF file      #
######################
sub getparam { # %pf = getparam($PF);
#{{{
    my $PF = shift ;
    my $subject;
    my %pf;

    foreach my $value (qw/local_data_dir remote_folder method_blacklist 
                        miniseed_db_name ftp_path db_ip_table db_ip_table_cl
                        keep_miniseed_db db_sta_table db_sta_table_cl http_port
                        min_bandwidth print_miniseed_errors print_fix_errors stations
                        dbout fix_mseed_cmd db_sta_table_st max_procs ftp_port/){
        $pf{$value} = pfget($PF,$value);
        if( ! defined( $pf{$value}) ) { elog_and_die("Missing value for $value in PF:$PF"); }
        #elog_notify( "\t\t$value -> $pf{$value}") if $opt_d;
    }
    #print_pfe(\%pf,1) if $opt_d;
    return (%pf);
#}}}
}

######################
# check table access #
######################
sub table_check {  #  
#{{{
    my $db = shift;
    my $sta = shift;
    my $res;

    $sta ||= '';

    elog_notify("Checking Database  @$db") if $opt_d;
    if (! dbquery(@$db,"dbTABLE_PRESENT")) {
            elog_and_die( dbquery(@$db,"dbTABLE_NAME")." table is not available.",$sta);  
    }
#}}}
}

######################
# update to elog_die #
######################
sub elog_and_die {
#{{{
    my $msg = shift;
    my $station = shift;
    my $host = my_hostname();

    $station ||= '';

    problem($msg,$station);
    if ($opt_m && ! $station) { 
        sendmail("ERROR: $0 DIED ON host $host", $opt_m); 
    }
    elog_die($station);
#}}}
}

######################
# Report problems    #
######################
sub problem { # use problem("log of problem");
#{{{
    my $text = shift; 
    my $station = shift; 

    $station ||= '';

    elog_notify("\n");
    elog_complain("$station Problem\n\n\t\t\t\t$text");
    elog_notify("\n");
#}}}
}


__END__
#{{{
=pod

=head1 NAME

rsync_baler - Sync a remote baler directory to a local copy

=head1 SYNOPSIS

rsync_baler [-h][-v][-d] [-s sta_regex] [-r sta_regex] [-p pf] [-m mail_to] DB

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h> 

Produce this documentation

=item B<-v> 

Produce verbose output while running

=item B<-d>

Produce very-verbose output while running

=item B<-p>

Parameter file name 

=item B<-s>

Select station regex 

=item B<-r>

Reject station regex 

=item B<-m>

List of emails to send output

=back

=head1 DESCRIPTION

This script  creates a local repository of a field Baler44 station.
The script is simple and may fail if used outside ANF-TA installation. 

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).

=cut
#}}}
