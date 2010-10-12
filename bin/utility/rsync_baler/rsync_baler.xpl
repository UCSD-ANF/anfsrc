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
#use archive;
use Net::FTP;
use Datascope ;
use Pod::Usage;
use IO::Handle;
use File::Fetch;
use File::Spec;
use Getopt::Std;
use IPC::Cmd qw[can_run run];


our($opt_j,$opt_f,$opt_r,$opt_s,$opt_h,$opt_v,$opt_m,$opt_p,$opt_V,$opt_R);
our($PF,%pf,@db,@db_sta,@db_ip,@db_on,$dbname,$dbpath);
our($dbout,$local_path,$start_of_report,@dbr,$nrecords);
our($station,@errors,%table,$time,$dfile,$bandwidth,$media);
our($reserve_media,$total_bytes,$bytes);
our($temp_sta,$cmd,$ps_path);
our($start,$end,$run_time,$run_time_str,$type);
our($sta,@stas,$active_pids,$stations,$table,$folder);
our($pid,$log,$address,$ip_sta);
our($host,$key,$value,$file_fetch);
our($dlsta,$net,$ip);
our($Problems,$problems_hash,$prob,$txt);

use constant false => 0;
use constant true  => 1;
#}}}

######################
#  Program setup     #
######################
#{{{

    #
    # Print log messages immediately
    #
    # If return codes are not checked, it's easy 
    # for error log messages to disappear. For 
    # debugging purposes, it may be useful to 
    # force messages to be printed immediately.
    #
    $ENV{'ELOG_DELIVER'} = 'stdout';

    #
    # Change ELOG_TAGs
    $ENV{'ELOG_TAG'} = '*log*@l@*log*@n@*debug*@D@*complain*@c';

    elog_init($0, @ARGV);
    $cmd = "$0 @ARGV" ;
    $start = now();
    $host = my_hostname();

    if ( ! &getopts('j:fhdVvm:p:s:r:R:') || @ARGV > 0 ) { 
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
        elog_debug("Initialize mail") if $opt_V;
        savemail();
    }

    elog_notify('');
    elog_notify( $cmd );
    elog_notify("Starting execution at ".strydtime(now())." on ".my_hostname());
    elog_notify('');
    elog_notify('');

    #
    # Implicit flag
    #
    $opt_v = defined($opt_V) ? $opt_V : $opt_v ;

    #
    # Get parameters
    #
    elog_debug("Getting params") if $opt_V;
    $PF = $opt_p || "rsync_baler.pf" ;
    %pf = getparam($PF);

    # nice print of pf file
    elog_debug("Parameters from PF file $PF:") if $opt_V;
    print_pf(\%pf,1) if $opt_V;

    #
    ## Set File::Fetch options
    #
    $File::Fetch::WARN      = 0 unless $opt_V; 
    $File::Fetch::DEBUG     = 1 if $opt_V; 
    $File::Fetch::TIMEOUT   = 0; 
    $File::Fetch::BLACKLIST = $pf{method_blacklist} if $pf{method_blacklist};

    #
    ## Set IPC::Cmd options
    #
    $IPC::Cmd::VERBOSE = 1 if $opt_V;

    #
    ## Check IPC Methods
    #
    if ($opt_V) {

        elog_debug('');
        elog_debug('Verify IPC Methods:');

        if (IPC::Cmd->can_use_ipc_open3){
            elog_debug("\tIPC::Open3 available: ".IPC::Cmd->can_use_ipc_open3(1));
        }
        else { elog_debug("\tIPC::Open3 available: 0"); }

        if (IPC::Cmd->can_use_ipc_run){
            elog_debug("\tIPC::Run available: ".IPC::Cmd->can_use_ipc_run(1));
        }
        else { elog_debug("\tIPC::Run available: 0"); }

        if (IPC::Cmd->can_capture_buffer){
            elog_debug("\tCan capture buffer: ".IPC::Cmd->can_capture_buffer);
        }
        else { elog_debug("\tCan capture buffer: 0"); }

        elog_debug('');
    }

    #
    # Check if we have access to the system calls: {msfixoffsets and miniseed2db} 
    #
    elog_debug('') if $opt_V;
    elog_debug("Verify path for system calls:") if $opt_V;

    if ($pf{fix_mseed_cmd}) {
        $ps_path   = can_run('msfixoffsets') or elog_and_die("msfixoffsets missing in PATH");
        elog_debug("\tmsfixoffsets path=$ps_path") if $opt_V;
    }
    else{ elog_debug("\tNot running msfixoffsets...(edit PF file to enable)") if $opt_V; }

    if ($pf{keep_miiseed_db}) {
        $ps_path   = can_run('minseed2db') or elog_and_die("minseed2db missing in PATH");
        elog_debug("\tminiseed2days path=$ps_path") if $opt_V;
    }
    else{ elog_debug("\tNot running minseed2db...(edit PF file to enable)") if $opt_V; }

    #
    # Init Database
    #
    elog_debug('') if $opt_V;
    elog_debug("Opening $pf{database}:") if $opt_V;
    @db = dbopen ( $pf{database}, "r" ) or elog_and_die("Can't open DB: $pf{database}"); 
    
    # Open table for list of valid stations 
    @db_on = dblookup(@db, "", "deployment" , "", "");
    table_check(\@db_on);

    # Open table for list of stations 
    @db_sta = dblookup(@db, "", "stabaler", "", "");
    table_check(\@db_sta);

    # Open table for list of current ips
    @db_ip = dblookup(@db, "", "staq330" , "", "");
    table_check(\@db_ip);

    #
    # Verify access to directory
    #
    if(! -e $pf{local_data_dir} )  {
        elog_and_die("Can't access dir => $pf{local_data_dir}.");
    }

    if ( $opt_j ) {
        $opt_j = File::Spec->rel2abs( $opt_j ); 
        elog_debug("Write table in json file: $opt_j") if $opt_V;
    }

#}}}
######################
#  Get station list  #
######################
#{{{

    elog_debug('') if $opt_V;
    elog_debug('Get list of stations:') if $opt_V;
    $stations = get_stations_from_db(); 


    #
    # Print list of stations
    #
    if ( $opt_v ) {
        elog_notify('');
        elog_notify('List of statons to rsync:');
        elog_notify("\t".join( " ", sort keys %$stations ));
        elog_notify('');
    }
    if ( $opt_V ) {
        foreach $temp_sta (sort keys %$stations) {
            if ($stations->{$temp_sta}->{ip}) {
                elog_debug("\t$temp_sta => $stations->{$temp_sta}->{ip}");
            }
            else {
                elog_debug("\t$temp_sta => NONE! ");
            }
        }
        elog_debug('');
    }

#}}}

######################
#  MAIN:             #
######################
#{{{

    #
    # Run this part for a full database report
    #
    if ( $opt_R ) { report($stations); }

    #
    # Run this part for a full database report and json file dump
    #
    elsif ( $opt_j ) { json_report($stations); }
    #
    # This part forks the script so you 
    # can pull data from multiple stations
    # simultaneously.
    #
    else { get_data(); }

    problem_print();

    #
    # Calc total time for script
    #
    $end = now();
    $run_time = $end - $start;
    $start = strydtime($start);
    $end = strydtime($end);
    $run_time_str = strtdelta($run_time);

    elog_notify('');
    elog_notify('');
    elog_notify('----------------- END -----------------');
    elog_notify('');
    elog_notify("Start: $start End: $end");
    elog_notify("Runtime: $run_time_str");
    sendmail("Done $0 on $host ", $opt_m) if $opt_m; 
    elog_notify('');

#}}}

######################
#  Get data          #
######################
sub get_data {
#{{{

    @stas = sort keys %$stations;

    STATION: while ( 1 ) {
        $active_pids = check_pids($stations); 
        if ( $active_pids < $pf{max_procs} && scalar @stas ) {

            $temp_sta = pop(@stas);

            if (! $stations->{$temp_sta}->{active} ){ 
                problem("Station $temp_sta is not active in deployment table.",$temp_sta); 
                next;
            }

            if (! $stations->{$temp_sta}->{ip} ){ 
                problem("No IP for station $temp_sta.",$temp_sta); 
                next;
            }

            elog_debug("\tStarting rsync of $temp_sta (in queue: ".scalar @stas." )") if $opt_V;

            $stations->{$temp_sta}->{start} = now();
            $stations->{$temp_sta}->{pid}   = new_child($stations,$temp_sta);

            ++$active_pids;
        }

        # Get out of loop if we don't have more stations to pull data from
        if ( $active_pids == 0 && ! scalar @stas ) { last STATION; } 

    }

    @stas = keys %$stations;
    elog_notify("*** End rsync of ".scalar @stas." stations. ***");
    elog_notify('');

#}}}
}

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
                    elog_debug("\t\tNo child running. RESP = $resp and $?") if $opt_V; 
                }
                elsif (WIFEXITED($?)) { 
                    $table->{$key}->{pid} = 0; 
                    elog_debug("\tDone with $key") if $opt_V; 
                }
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
    my (%active_media_files,$media,$local_path,$loc_file,$rem_file,$ftp);
    my ($size,$nrecords,@temp_download,@dbwr,@dbr,@dbr_sub,$net);
    my ($local_path_file,$avoid,$replace,$file,$speed,$run_time);
    my ($fixed,$port,@download,$start_sta,$start_file,$where,$attempts);
    my ($rem_s,$loc_s,@diff,$results,$run_time_str,$fixed_files,$dbout);
    my ($end_file,$record,$dlsta,$time,$endtime,$dir,$dfile);
    my ($k,$m,$g,$total_size,%temp_hash,@total_downloads,@total_flags);

    #
    # Split in two...
    #
    $resp = fork();

    #
    # Is this parent or child???
    #
    if (! $resp) { 

        $start_sta = now();
        elog_debug('') if $opt_V;;
        elog_debug("$station Start time ".strydtime($start_sta)) if $opt_V;

        #
        # Prepare Variables and Folders
        #
        $local_path = File::Spec->rel2abs( prepare_vars($station) ); 
        if (! $table->{$station}->{ip} ) { elog_and_die("No ip for station.",$station); }
        $ip     = $table->{$station}->{ip};
        $dlsta  = $table->{$station}->{dlsta};
        $net    = $table->{$station}->{net};

        #
        # Opend station database
        #
        $dbout = "$local_path/$station";
        $dbout .= "_baler";

        #
        # Fix path
        #
        $dbout = File::Spec->rel2abs( $dbout ); 

        elog_debug("$station Opening database ($dbout).") if $opt_V;
        if ( ! -e $dbout) {
            elog_debug("$station Creating new database ($dbout).") if $opt_V;
            dbcreate ( $dbout, "css3.0", $local_path, '', "\n# BALER44 archival database. \n# Juan Reyes \n# reyes\@ucsd.edu \n#" );
            #dbcreate($dbout,"CSS3.0",$local_path);
        }   

        elog_debug("$station Openning database table  ($dbout.rsyncbaler)") if $opt_V;
        @dbr  = dbopen($dbout,"r+") or elog_and_die("Can't open DB: $dbout",$station);
        @dbr  = dblookup(@dbr,"","rsyncbaler","","") or elog_and_die("Can't open DB TABLE: $dbout.rsyncbaler",$station);

        #elog_debug('dbTABLE_PRESENT: '. dbquery(@dbr, "dbTABLE_PRESENT"));
        #elog_debug('dbTABLE_SIZE: '. dbquery(@dbr, "dbTABLE_SIZE"));
        #elog_debug('dbTABLE_DETAIL: '. dbquery(@dbr, "dbTABLE_DETAIL"));
        #elog_debug('dbRECORD_COUNT: '. dbquery(@dbr, "dbRECORD_COUNT"));
        #$nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
        #for ( $dbr[3] = 0 ; $dbr[3] < $nrecords ; $dbr[3]++ ) {
        #    elog_debug("READ TABLE:". dbget (@dbr));
        #}
        #elog_die('end of test');

        #eval { dbquery(@dbr,"dbTABLE_PRESENT"); };
        #if ($@) {
        #    problem( "$dbout.rsyncbaler is not available.($@)",$temp_sta);
        #    elog_complain(sprintf("%6s", $temp_sta) . " ::      0      ERROR: database error($@)!");
        #    exit 0;
        #}

        #
        # For each of the folders
        #
        #while( $folder = @{$pf{remote_folder}} ) {
        foreach $folder ( @{$pf{remote_folder}} ) {


            $fixed_files = 0;

            # loggin in to station
            $port = $pf{ftp_port};

            elog_notify("Now: $station $ip:$port $folder") if $opt_v;

            if ($opt_V) { 
                elog_notify("$station $ip:$port debug='on'");
                $ftp = loggin_in($ip,$port,$station,1);
            }
            else { $ftp = loggin_in($ip,$port,$station); }

            # Get files from directory lists
            elog_debug("$station Reading remote directory $folder") if $opt_V;
            $rem_file = read_dir( $station, $folder, $ftp );

            elog_debug("$station Reading local directory $local_path") if $opt_V;
            $loc_file = read_dir( $station, $local_path );

            eval {  $ftp->quit if $ftp; };
            problem("Net::FTP error...\n\t\t*".$ftp->uri."\n\t\t*".$ftp->error(1)."\n\t\t*$@",$station) if $@; 

            #
            # Flag files for download
            #
            @download = compare_dirs($loc_file,$rem_file,$dlsta,$station,@dbr);

            if ( @download && $folder =~ /.*reservemedia.*/) {
                problem("Secondary media in use. ($folder)",$station); 
                $media = "reservemedia";
            }
            else { 
                $media = "activemedia";
            }

            #
            # Track total files on remote
            #
            foreach (sort keys %$rem_file) {
                $active_media_files{$_}{size} = $rem_file->{$_}->{size};
            }

            #
            # Track total files to download from ALL folders.
            #
            @total_flags = (@total_flags,@download);

            #
            # Start the download.
            #
            FILE: foreach $file ( sort @download) {
                $start_file = now();
                $where = 0;

                #
                # Check if we are over the limit of time
                #
                if ( $pf{max_child_run_time} ) { 
                    if ( int($pf{max_child_run_time}) < ($start_file - $start_sta) ) {
                        problem("Rsync exceeds allowed time set in max_child_run_time ($pf{max_child_run_time}).",$station);
                        last FILE;
                    }
                }

                #
                # Fix path
                #
                $local_path_file = File::Spec->rel2abs( "$local_path/$file" ); 

                #
                # Verify if we have the file in the local dir
                #
                if (-e "$local_path_file") {
                    if ( unlink "$local_path_file" ) { 
                        elog_notify("$station Success remove of previous file $local_path_file"); 
                    }
                    else { 
                        problem("Can't delete previous file $local_path_file",$station); 
                        next FILE;
                    }
                }

                #
                # Update DB
                #
                @dbr_sub = dbsubset(@dbr, "dlsta == '$dlsta' && dfile == '$file' && status == 'downloading' " );
                $attempts = dbquery(@dbr_sub,dbRECORD_COUNT) ; 

                $attempts += 1;

                elog_debug("$station DB NEW: [ $dlsta | $local_path | $attempts | 'downloading' | $media ] ") if $opt_V;

                dbaddv(@dbr, 
                    "net",      $net,
                    "dlsta",    $dlsta,
                    "dfile",    $file,
                    "sta",      $station,
                    "time",     now(), 
                    "status",   "downloading",
                    "dir",      $local_path,
                    "attempts", $attempts,
                    "lddate",   now(),
                    "media",    $media);

                #
                # Prepare download cmd
                #
                $file_fetch = File::Fetch->new(uri => "ftp://$ip:$port/$folder/$file");
                elog_debug("$station Start download of ".$file_fetch->uri) if $opt_V;

                #
                # Run Fetch cmd.
                #
                eval {  
                    $where = $file_fetch->fetch( to => "$local_path" ); 
                };
                problem("File::Fetch 'fetch' error...\n\t\t*".$file_fetch->uri."\n\t\t*$@",$station) if $@; 

                $end_file = now();
                $run_time= $end_file-$start_file;
                $run_time_str = strtdelta($run_time);

                #
                # Variable $where is the full path of the downloaded file
                # only set on successful downloads. 
                #
                if( $where ) { 
                    elog_debug("$station Success in download of $file after $run_time_str") if $opt_V;

                    push @total_downloads, $file;

                    #
                    # Keep track of total data downloaded
                    #
                    $size = -s $where; 
                    $total_size += $size;

                    #
                    # Verify bandwidth of ftp connection
                    #
                    $size = $rem_file->{$file}->{size} / 1024;
                    $speed = $size / $run_time;
                    elog_debug("$station $file Size:$size Kb  Time:$run_time secs Speed:$speed Kb/sec") if $opt_V;
                    #if ( $speed < $pf{min_bandwidth}) {
                    #    problem("Bandwidth of ($speed)Kb/s is very low!",$station);
                    #}
                    #
                    #else { $speed = 0.00; }

                    #
                    # If empty set to 0.00
                    #
                    $speed ||= 0.00;

                    #
                    # In case we need to fix the miniseed files...
                    #
                    if ( $pf{fix_mseed_cmd} ) { 

                        elog_debug("$station Fixing miniseed file with: $pf{fix_mseed_cmd} " ) if $opt_V;
                        fix_file($station,$where); 
                        $fixed = 'y';

                    }
                    else {
                        $fixed = 'n';
                    }

                    #
                    # Add to DB
                    #
                    elog_debug("$station NEW: [ $dlsta | $start_file | $end_file | $attempts | 'downloaded' | $media | $size | $speed ] ") if $opt_V;

                    dbaddv(@dbr, 
                        "net",      $net, 
                        "sta",      $station, 
                        "time",     $start_file, 
                        "endtime",  $end_file, 
                        "dir",      $local_path, 
                        "attempts", $attempts, 
                        "media",    $media, 
                        "filebytes",$size, 
                        "bandwidth",$speed, 
                        "dlsta",    $dlsta,
                        "fixed",    $fixed,
                        "dfile",    $file,
                        "lddate",   now(),
                        "status",   "downloaded");


                }

                #
                # If download failed... $where == NULL
                #
                else {

                    $run_time_str = strtdelta(now()-$start_file);
                    problem("Failed download of $file after $run_time_str",$station);

                }
            } #end of foreach @downloads

            #
            # Done with folder
            # Print stats 
            #
            if ($opt_V) {
                elog_notify('');
                elog_notify("$station: Done rsync of $folder");
            }

        } # end of while $folders

        #
        # Cleaning up!
        #
        eval {  
            dbclose @dbr;
        };
        problem("Datascope dbclose failed!\n{@dbr} \n\t\t*$@",$station) if $@; 

        #
        # Calc the total time to rsync station
        #
        $run_time = now() - $table->{$station}->{start};
        $run_time_str = strtdelta($run_time);

        elog_notify('');
        elog_notify('');
        elog_notify("\t$station: Done rsync of " . scalar @total_downloads. " files out of ". scalar @total_flags . " in $run_time_str");
        elog_notify("\t$station: IP:$ip");
        elog_notify('');


        #
        # Check for missing files
        # Get the values missing from array.
        #
        if ( scalar @total_downloads != scalar @total_flags ) { foreach (@total_downloads) { $temp_hash{$_} = 1; } }
        if ( %temp_hash ) {
            foreach ( sort @total_flags) { 
                if ( ! exists $temp_hash{$_} ) { elog_notify("\t$station: Missing file >> $_"); }
            }
        }


        #
        # Get download ratios
        #
        elog_debug("$station Reading local directory $local_path") if $opt_V;
        $loc_file = read_dir( $station, $local_path );


        #
        # check archived ratio
        #
        #$rem_s = print_files(\%active_media_files,"\t$station: on REMOTE folder:");
        $loc_s = print_files($loc_file,"\t$station: on LOCAL folder:");

        #if ($rem_s > 0) { 
        #    elog_notify("\t$station: Ratio archived: " . sprintf("%0.1f",($loc_s/$rem_s) * 100) . "%"); 
        #}
        #else { elog_notify("\t$station: Ratio archived: ERROR!"); }

        #
        # Calc data downloaded
        #
        $total_size ||= 0;
        $k = sprintf("%0.1f",$total_size/1024);
        $m = sprintf("%0.1f",$k/1024);
        $g = sprintf("%0.1f",$m/1024);

        if( $g > 1 ) { elog_notify("\t$station: Total data downloaded $g Gb"); } 
        elsif( $m > 1 ) { elog_notify("\t$station: Total data downloaded $m Mb"); } 
        elsif( $k > 1 ) { elog_notify("\t$station: Total data downloaded $k Kb"); } 
        elsif( $total_size > 0 ) { elog_notify("\t$station: Total data downloaded $total_size bytes"); } 
        else{ problem("No data downloaded",$station); } 
        elog_notify('');

        #
        # End of child
        #
        exit 0;
    }

    #
    # Return to parent
    #
    if(pid_exists($resp)){ 
        elog_debug("$station: PID=$resp") if $opt_V;
        return $resp;
    }
    problem("PID=$resp for $station $ip process. Skipping!",$station);
    return 0; 

#}}}
}

######################
#  Produce report    #
######################
sub report { 
#{{{
    $stations = shift;
    my ($kilos,$megas);
    my ($dfile, $media,$status);
    my ($reserve_media, $bytes, $bandwidth);
    my (@total,%total,@flagged,@downloaded,@missing,%missing,$ratio);
    my ($text,$time, $endtime);
    my (@dbr_d,@dbr_f);
    my ($total_bytes);
    my $bandwidth_low;
    my $bandwidth_high;

    foreach $temp_sta ( sort keys %$stations ) {

        #
        # clean vars
        #
        undef ($kilos);
        undef ($megas);
        undef ($dfile);
        undef ($media);
        undef ($status);
        undef ($reserve_media);
        undef ($bytes);
        undef ($bandwidth);
        undef (%total);
        undef (@total);
        undef (@flagged);
        undef (@downloaded);
        undef (@missing);
        undef (%missing);
        undef ($ratio);
        undef ($text);
        undef ($time);
        undef ($endtime);
        undef (@dbr_d);
        undef (@dbr_f);
        undef ($total_bytes);
        $bandwidth_low = 99999;
        $bandwidth_high = 0;


        #
        # Prepare vars
        #
        $local_path = prepare_vars($temp_sta); 
        $dbout = "$local_path/$temp_sta"."_baler";

        #
        # Fix path
        #
        $dbout = File::Spec->rel2abs( $dbout ); 

        elog_notify("\n") if $opt_v;
        elog_notify("$temp_sta:") if $opt_v;
        elog_debug("\tdatabase: $dbout") if $opt_V;

        #
        # Verify database existence
        #
        if ( ! -e $dbout) {
            problem('No local database.',$temp_sta) if $opt_v;
            $text = sprintf("%6s", $temp_sta) . " ::      0      ERROR: No database in local directory!";
            elog_notify($text);
            next;
        }

        #
        # Opening Database
        #
        elog_debug("\tOpenning database table  ($dbout.rsyncbaler)") if $opt_V;
        @dbr = dbopen_table("$dbout.rsyncbaler","r+") or problem("Can't open DB TABLE: $dbout.rsyncbaler",$temp_sta);

        #
        # Verify Database
        #
        #elog_debug("DB:@dbr");
        eval { dbquery(@dbr,"dbTABLE_PRESENT"); };
        if ($@) {
            problem( "$dbout.rsyncbaler is not available.($@)",$temp_sta);
            $text = sprintf("%6s", $temp_sta) . " ::      0      ERROR: database error($@)!";
            next;
        }

        #
        #
        #
        #
        #
        #
        # Fix tables
        # Use this part to update values on the database. Usually when new 
        # functionality is introduce to the software. 
        #
        #$nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
        #for ( $dbr[3] = 0 ; $dbr[3] < $nrecords ; $dbr[3]++ ) {
        #
        #    ($status) = dbgetv (@dbr, "status");
        #
        #    if ( $status =~ /Downloaded/i ) {
        #        dbputv(@dbr,"status","downloaded");
        #    }
        #    elsif ($status =~ /Flagged/i ) {
        #        dbputv(@dbr,"status","flagged");
        #    }
        #    elsif ($status =~ /start/i ) {
        #        dbputv(@dbr,"status","downloading");
        #    }
        #    else {
        #        problem("ERROR: status='$status' on $dbout (@dbr)",$temp_sta);
        #    }
        #}
        #
        # End of fix tables
        #
        #
        # Use this to remove values
        #$nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
        #for ( $dbr[3] = 0 ; $dbr[3] < $nrecords ; $dbr[3]++ ) {
        #
        #    ($status) = dbgetv (@dbr, "dfile");
        #
        #    if ( $status =~ /stats\.html/i ) {
        #        elog_debug("\n\n\t$temp_sta:\nGot stats.html\n\n\n");
        #        dbmark(@dbr);
        #        $crunch = 1;
        #    }
        #}
        #dbcrunch(@dbr) if $crunch;
        #
        #
        #
        #
        #
        #


        #
        # Check data in DB
        #
        @dbr = dbsort(@dbr,'dfile');
        $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
        if ($nrecords < 1) {
            problem('database is empty.',$temp_sta) if $opt_v;
            $text = sprintf("%6s", $temp_sta) . " ::      0           (ERROR: Database empty!)";
            next;
        }

        #
        # Get list of flagged files
        #
        @dbr_f= dbsubset ( @dbr, "status == 'flagged'");
        $nrecords = dbquery(@dbr_f, 'dbRECORD_COUNT') ;
        elog_notify("\tfiles flagged: $nrecords") if $opt_V;
        for ( $dbr_f[3] = 0 ; $dbr_f[3] < $nrecords ; $dbr_f[3]++ ) {
            push @flagged, dbgetv (@dbr_f, 'dfile');
        }

        #
        # Get list of downloaded files
        #
        @dbr_d= dbsubset ( @dbr, "status == 'downloaded'");
        $nrecords = dbquery(@dbr_d, 'dbRECORD_COUNT') ;
        elog_notify("\tfiles downloaded: $nrecords") if $opt_V;
        for ( $dbr_d[3] = 0 ; $dbr_d[3] < $nrecords ; $dbr_d[3]++ ) {
            push @downloaded, dbgetv (@dbr_d, 'dfile');
        }

        #
        # Check archive status
        #
        @missing{@flagged} = ();
        delete @missing {@downloaded};
        @missing = sort keys %missing;

        @total{@flagged} = ();
        @total{@downloaded} = ();
        @total = sort keys %total;


        if ( scalar(@total) ) {
            elog_notify("Missing ".scalar(@missing)." files. Total files (".scalar(@total).")") if $opt_v;
            $ratio = sprintf("%0.2f",(scalar(@downloaded) / scalar(@total)) * 100);
        }
        else { 
            elog_notify("No files in database.") if $opt_v;
            $ratio = 0.00
        }

        elog_notify("$ratio% downloaded from station") if $opt_v;


        if ($opt_V){
            foreach (sort @missing){
                elog_notify("\t$_");
            }
        }


        #
        # Get last file in DB
        #
        if ($opt_v) {
            @dbr = dbsubset ( @dbr, "status == 'downloaded'");
            $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
            elog_notify("\tfiles donwloaded: $nrecords");

            if ($nrecords < 1) {
                problem('No files with status "downloaded".',$temp_sta) if $opt_v;
            }
            else {
                #
                # Sort on download time
                #
                @dbr = dbsort(@dbr,'time');
                $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
                # Last downloaded
                $dbr[3] = $nrecords-1;

                ($dfile,$time) = dbgetv (@dbr, qw/dfile time/);
                if ($time > 0 ) {
                    elog_notify("\tLast:     $dfile downloaded on:".strtime($time));
                }
                else {
                    elog_notify("\tLast:     $dfile downloaded on: UNKNOWN");
                }

                #
                # Sort on file name
                #
                @dbr = dbsort(@dbr,'dfile');
                $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;

                #
                # Get youngest
                #
                $dbr[3] = $nrecords-1;

                ($dfile,$time) = dbgetv (@dbr, qw/dfile time/);
                if ($time > 0 ) {
                    elog_notify("\tYoungest: $dfile downloaded on:".strtime($time));
                }
                else {
                    elog_notify("\tYoungest: $dfile downloaded on: UNKNOWN");
                }

                #
                # Get oldest
                #
                $dbr[3] = 0;

                ($dfile,$time) = dbgetv (@dbr, qw/dfile time/);
                if ($time > 0 ) {
                    elog_notify("\tOldest:   $dfile downloaded on:".strtime($time));
                }
                else {
                    elog_notify("\tOldest:   $dfile downloaded on: UNKNOWN");
                }

            }
        }

        #
        # Subset the last N-days
        #
        $dfile = $media = $status = '';
        $reserve_media = $bytes = $bandwidth = 0;
        $time = $endtime = $total_bytes = 0;
        $bandwidth_low = 1000;
        $bandwidth_high = 0;

        $start_of_report = str2epoch("-".$opt_R."days");
        elog_notify("\tOn the last $opt_R days (since: ".strtime($start_of_report)."):") if $opt_v;


        #
        # Reopen the database
        #
        @dbr = dbsubset ( @dbr, "time >= $start_of_report");
        @dbr  = dbsort(@dbr,'dfile');
        $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
        elog_debug("\t\tfiles donwloaded: $nrecords") if $opt_V;

        $text = sprintf("%6s", $temp_sta) . " :: ";

        #total files from THAT station
        # Note: calculated by adding downloaded files
        # and flagged files in a unique set. 
        $text .= sprintf("%6d", scalar(@total)) . " ";

        # total missing 
        $text .= sprintf("%6d", scalar(@missing)) . " ";

        # total ratio
        $text .= sprintf("%6.2f", $ratio) . "% ";

        # in the last R days
        $text .= sprintf("%6d", $nrecords) . " ";

        if ($nrecords > 0) {

            for ( $dbr[3] = 0 ; $dbr[3] < $nrecords ; $dbr[3]++ ) {

                ($dfile, $bandwidth, $endtime, $bytes, $media) = dbgetv (@dbr, qw/dfile bandwidth endtime filebytes media/);

                elog_debug("\t$dfile ::: $media ::: $bandwidth Kb/s ::: ".strtime($endtime)) if $opt_V;

                # Track size of files
                $total_bytes += $bytes;
                # Track min bandwidth
                if ($bandwidth_low > $bandwidth and $bandwidth > 0.01){ $bandwidth_low = $bandwidth; }
                # Track max bandwidth
                if ($bandwidth_high < $bandwidth){ $bandwidth_high = $bandwidth; }
                # Track media in use
                if ($media =~ /.*reservemedia.*/) { $reserve_media = 1; }
            }

            #convert size
            $text .= sprintf("%15.2f", $total_bytes/1024) . " Mb     ";

            if ($reserve_media) {
                problem('Media in use: RESEVE.',$temp_sta) if $opt_v;
                $text .= "RESERVEMEDIA ";
            }
            else {
                elog_notify("\t\tMedia in use: ACTIVE") if $opt_v;
                $text .= "activemedia  ";
            }

            $bandwidth_high = sprintf("%6.1f", $bandwidth_high);
            $bandwidth_low = sprintf("%6.1f", $bandwidth_low);
            $text .= "$bandwidth_high Kb/s  ";
            $text .= "$bandwidth_low Kb/s  ";

            elog_notify("\t\tMax reported bandwidth: $bandwidth_high") if $opt_v;

            if ($opt_v) { 
                if ($bandwidth_low < $pf{min_bandwidth}  and $bandwidth_low ) { 
                    problem("Min reported bandwidth: $bandwidth_low Kb/s",$temp_sta);
                }
                else {
                    elog_notify("\t\tMin reported bandwidth: $bandwidth_low Kb/s");
                }
            }

        }

        elog_notify("$text");


        dbclose(@dbr);
    }
    elog_notify('');
    elog_notify('');

#}}}
}

######################
#  Produce json file #
######################
sub json_report { 
#{{{
    $stations = shift;
    my ($kilos,$megas);
    my ($dfile, $media,$status);
    my (@folders,$bytes, $bandwidth);
    my (@total,%total,@flagged,@downloaded,@missing,%missing,$ratio);
    my ($text,$time, $endtime);
    my (@dbr_d,@dbr_f);
    my ($total_bytes);
    my ($count);
    my $bandwidth_low;
    my $bandwidth_high;
    my $start_of_report;;




    #
    # Get stations for folder
    #
    opendir(DIR, $pf{local_data_dir}) or die "Can't open $pf{local_data_dir}: $!";
    for (readdir DIR) {
        next if /^\.{1,2}$/;
        push @folders, $_;
    }
    close DIR;


    # 
    # Clear file for data dump
    #
    unlink($opt_j) if -e $opt_j;

    open(SAVEOUT, "&STDOUT");
    open(SAVEERR, "&STDERR");
    open ( STDOUT, ">$opt_j");
    open ( STDERR, ">&STDOUT");

    $text =  "";

    #foreach $temp_sta ( sort keys %$stations ) {
    foreach $temp_sta ( sort @folders ) {

        #
        # clean vars
        #
        undef ($kilos);
        undef ($megas);
        undef ($dfile);
        undef ($media);
        undef ($status);
        undef ($bytes);
        undef ($bandwidth);
        undef (%total);
        undef (@total);
        undef (@flagged);
        undef (@downloaded);
        undef (@missing);
        undef (%missing);
        undef ($ratio);
        undef ($time);
        undef ($endtime);
        undef (@dbr_d);
        undef (@dbr_f);
        undef ($total_bytes);
        undef ($start_of_report);
        $bandwidth_low = 99999;
        $bandwidth_high = 0;
        $count = 0;

        #
        # Prepare vars
        #
        $local_path = prepare_vars($temp_sta); 
        $dbout = "$local_path/$temp_sta"."_baler";
        $text .= "\"$temp_sta\": {";

        #
        # Fix path
        #
        $dbout = File::Spec->rel2abs( $dbout ); 
        $text .= "\n\t\"path\": \"$dbout\"";

        #
        # Get station info
        #
        if ( $stations->{$temp_sta}->{'active'} ) {
            $text .= ",\n\t\"active\": \"true\"";
        }
        else { 
            $text .= ",\n\t\"active\": \"false\"";
        }

        if ( $stations->{$temp_sta}->{'vnet'} ) {
            $text .= ",\n\t\"vnet\": \"". $stations->{$temp_sta}->{'vnet'} ."\"";
        }
        else{
            $text .= ",\n\t\"vnet\": \"NONE!\"";
        }

        if ( $stations->{$temp_sta}->{'ip'} ) {
            $text .= ",\n\t\"ip\": \"". $stations->{$temp_sta}->{'ip'} ."\"";
        }
        else{
            $text .= ",\n\t\"ip\": \"NONE!\"";
        }

        if ( $stations->{$temp_sta}->{'equip_install'} ) {
            $text .= ",\n\t\"equip_install\": \"". $stations->{$temp_sta}->{'equip_install'} ."\"";
        }
        else{
            $text .= ",\n\t\"equip_install\": \"NONE!\"";
        }

        if ( $stations->{$temp_sta}->{'equip_remove'} ) {
            $text .= ",\n\t\"equip_remove\": \"". $stations->{$temp_sta}->{'equip_remove'} ."\"";
        }
        else{
            $text .= ",\n\t\"equip_remove\": \"NONE!\"";
        }

        delete( $stations->{$temp_sta} );

        #
        # Get stations for folder
        #
        if ( opendir(DIR, $local_path) ) {
            for (readdir DIR) {
                next if /^\.{1,2}$/;
                if ( $_ =~ /.*-($temp_sta)_.*/ ){ $count++; }
            }
        }
        else { 
            $text .= ",\n\t\"error\": \"Can not access directory!\" },\n";
            next;
        }
        close DIR;

        $text .= ",\n\t\"local\": $count";

        #
        # Verify database existence
        #
        if (! -e $dbout) {
            $text .= ",\n\t\"error\": \"No database in directory!\" },\n";
            next;
        }

        #
        # Opening Database
        #
        @dbr = dbopen_table("$dbout.rsyncbaler","r+") or next;

        #
        # Verify Database
        #
        eval { dbquery(@dbr,"dbTABLE_PRESENT"); };
        next if $@;

        #
        # Check data in DB
        #
        @dbr = dbsort(@dbr,'dfile');
        $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
        if ($nrecords < 1) {
            $text .= ",\n\t\"error\": \"Database empty!\" },\n";
            next;
        }

        #
        # Get list of flagged files
        #
        @dbr_f= dbsubset ( @dbr, "status == 'flagged'");
        $nrecords = dbquery(@dbr_f, 'dbRECORD_COUNT') ;
        for ( $dbr_f[3] = 0 ; $dbr_f[3] < $nrecords ; $dbr_f[3]++ ) {
            push @flagged, dbgetv (@dbr_f, 'dfile');
        }

        #
        # Get list of downloaded files
        #
        @dbr_d= dbsubset ( @dbr, "status == 'downloaded'");
        $nrecords = dbquery(@dbr_d, 'dbRECORD_COUNT') ;
        for ( $dbr_d[3] = 0 ; $dbr_d[3] < $nrecords ; $dbr_d[3]++ ) {
            push @downloaded, dbgetv (@dbr_d, 'dfile');
        }

        #
        # Check archive status
        #
        @missing{@flagged} = ();
        delete @missing {@downloaded};
        @missing = sort keys %missing;

        @total{@flagged} = ();
        @total{@downloaded} = ();
        @total = sort keys %total;


        if ( scalar(@total) ) {
            $ratio = sprintf("%0.2f",(scalar(@downloaded) / scalar(@total)) * 100);
        }
        else { 
            $ratio = 0.00
        }

        $text .= ",\n\t\"ratio\": $ratio";

        $text .= ",\n\t\"total\": " . scalar(@total);
        $text .= ",\n\t\"downloaded\": " . scalar(@downloaded);


        if ($nrecords > 0) {
            #
            # Get list of downloaded files
            #
            for ( $dbr_d[3] = 0 ; $dbr_d[3] < $nrecords ; $dbr_d[3]++ ) {
                ($dfile, $bandwidth, $bytes, $media) = dbgetv (@dbr_d, qw/dfile bandwidth filebytes/);

                # Track size of files
                $total_bytes += $bytes;
                # Track min bandwidth
                if ($bandwidth_low > $bandwidth and $bandwidth > 0.01){ $bandwidth_low = $bandwidth; }
                # Track max bandwidth
                if ($bandwidth_high < $bandwidth){ $bandwidth_high = $bandwidth; }
            }

            $total_bytes = sprintf("%0.2f", $total_bytes/1024);
            $text .= ",\n\t\"Mbytes\": " . ($total_bytes);

            $bandwidth_high = sprintf("%0.1f", $bandwidth_high);
            $bandwidth_low = sprintf("%0.1f", $bandwidth_low);
            $text .= ",\n\t\"low_b\": $bandwidth_low";
            $text .= ",\n\t\"high_b\": $bandwidth_high";

            #
            # Get last file in DB
            #
            @dbr = dbsubset ( @dbr, "status == 'downloaded'");
            $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;

            #
            # Sort on download time
            #
            @dbr = dbsort(@dbr,'time');
            $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
            # Last downloaded
            $dbr[3] = $nrecords-1;

            ($dfile,$time,$media) = dbgetv (@dbr, qw/dfile time media/);

            $text .= ",\n\t\"last\": \"$dfile\"";
            $text .= ",\n\t\"last_time\": \"$time\"";

            if ($media =~ /.*reservemedia.*/) {
                $text .= ",\n\t\"media\": \"RESERVEMEDIA\"";
            }
            else {
                $text .= ",\n\t\"media\": \"activemedia\"";
            }

            #
            # Get total in last 30 days
            #
            $start_of_report = str2epoch("-30days");

            @dbr = dbsubset ( @dbr, "time >= $start_of_report");
            $nrecords = dbquery(@dbr, 'dbRECORD_COUNT') ;
            $total_bytes = 0.00;
            if ($nrecords > 0) {
                for ( $dbr[3] = 0 ; $dbr[3] < $nrecords ; $dbr[3]++ ) {
                    $total_bytes += dbgetv (@dbr, 'filebytes');
                }
            }
            $total_bytes = sprintf("%0.2f", $total_bytes/1024);
            $text .= ",\n\t\"30Mbytes\": " . ($total_bytes);
        }

        $text .= "\n\t},\n";

        dbclose(@dbr);

    }

    foreach $temp_sta ( sort keys %$stations ) {
        $text .= "\"$temp_sta\": {";
            $text .= "\n\t\"active\": \"true\"";

            if ( $stations->{$temp_sta}->{'vnet'} ) {
                $text .= ",\n\t\"vnet\": \"". $stations->{$temp_sta}->{'vnet'} ."\"";
            }
            else{
                $text .= ",\n\t\"vnet\": \"NONE!\"";
            }
            if ( $stations->{$temp_sta}->{'ip'} ) {
                $text .= ",\n\t\"ip\": \"". $stations->{$temp_sta}->{'ip'} ."\"";
            }
            else{
                $text .= ",\n\t\"ip\": \"NONE!\"";
            }
        $text .= ",\n\t\"error\": \"Missing from local archive!\" },\n";
    }

    chop $text;
    chop $text;
    print "{\n$text\n}";

    open ( STDOUT, "&SAVEOUT");
    open ( STDERR, "&SAVEERR");

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

    elog_debug("$sta $cmd") if $opt_V;

    ($success,$error_code,$full_buf,$stdout_buf,$stderr_buf) = run( command => $cmd, verbose => 0 );

    if (! $success && $pf{print_fix_errors} ) {
        problem("\t\nCmd:$cmd
            \n\tSuccess:$success
            \n\tError_code:$error_code
            \n\tStdout:@$stdout_buf
            \n\tStderr:@$stderr_buf",$station);
    }
    if ( $success && $opt_V ){
        elog_debug("\t\nStation:$sta
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
        $cmd = "minseed2db $file $pf{miniseed_db_name};"; 
    }
    else {
        $cmd = "minseed2db ./ $pf{miniseed_db_name};"; 
    }
    elog_debug("$sta Creating miniseed database: $cmd ") if $opt_V;


    ($success,$error_code,$full_buf,$stdout_buf,$stderr_buf) = 
            run( command => $cmd, verbose => 0 );
    if (! $success && $pf{print_miniseed_errors} ){
        problem("\t\nCmd:$cmd\n\tSuccess:$success\n\tError_code:$error_code\n\tStdout:@$stdout_buf\n\tStderr:@$stderr_buf",$sta);
    }
    if ( $success && $opt_V){
        elog_debug("\t\nStation:$sta\t\nCmd:$cmd\n\tSuccess:$success\n\tError_code:$error_code\n\tStdout:@$stdout_buf\n\tStderr:@$stderr_buf");
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
    my $total_size  = 0;
    my $total_files = 0;
    my $kilos = 0;
    my $megas = 0;

    foreach $file (sort keys %$list) {
        $total_size  += $list->{$file}->{size};
        $total_files += 1;
    }

    $kilos = sprintf("%0.2f", $total_size/1024);
    $megas = sprintf("%0.2f", $kilos/1024);

    elog_notify("$type $total_files files => $megas Mb");

    return $megas;
#}}}
}

######################
#  Compare Dirs      #
######################
sub compare_dirs {
#{{{
    my ($local_files,$remote_files,$dlsta,$station,@db)= @_;
    my (@flagged,@db_temp); 
    my ($rf,$record);
    my ($dfile,$time,$endtime,$status,$attempts,$lddate);

    FILE: foreach $rf ( keys %$remote_files ) {
        #elog_notify("Got db of $record records") if $opt_V;
        elog_notify("Subset for dfile == $rf && status == downloaded") if $opt_V;
        @db_temp = dbsubset(@db, "dfile == '$rf' && status == 'downloaded'");
        elog_notify("dbselect results : @db_temp") if $opt_V;
        $record  =  dbquery(@db_temp, "dbRECORD_COUNT");
        elog_notify("subset results : $record") if $opt_V;

        #
        # Found
        #
        if( 1 == $record ) { 
            elog_debug("$station $rf already downloaded.") if $opt_V;
            next FILE;
        }

        #
        # not present in db.
        #
        elsif( $record == 0 ) { 
            elog_debug("$station $rf not in database") if $opt_V;
        }

        #
        # Too many
        #
        elsif( $record > 1 ) { 
            problem("$rf downloaded more than once.(total=$record)",$station);

            for ( $db_temp[3] = 0 ; $db_temp[3] < $record ; $db_temp[3]++ ) {
            
                ($dfile,$time,$endtime,$status,$attempts,$lddate) = dbgetv (@db_temp, qw/dfile time endtime status attempts lddate/);
                elog_complain("\t$db_temp[3])dfile:  $dfile");
                elog_complain("\t$db_temp[3])time:    $time ->".strydtime($time));
                elog_complain("\t$db_temp[3])endtime: $endtime ->".strydtime($endtime));
                elog_complain("\t$db_temp[3])status:  $status");
                elog_complain("\t$db_temp[3])attempts:$attempts");
                elog_complain("\t$db_temp[3])lddate:  $lddate ->".strydtime($lddate));
                elog_complain(' ');
            
            }
            next FILE;
        }

        #
        # ERROR!!!
        #
        else { 
            problem("Can't understand (dfile == $rf && status == downloaded).records=$record",$sta); 
            next FILE;
        }


        #
        # If missing on db ...
        #
        if ( defined $local_files->{$rf} ) {
            if($local_files->{$rf}->{size} != $remote_files->{$rf}->{size}) {
                elog_debug("$station File flagged: $rf ") if $opt_V;
                dbaddv(@db, 
                    "net",      'TA',
                    "sta",      $station,
                    "dlsta",    $dlsta,
                    "dfile",    $rf,
                    "time",     now(), 
                    "lddate",   now(), 
                    "status",   "flagged");

                push @flagged, $rf;
            }
            else {
                elog_debug("$station File $rf already downloaded.") if $opt_V;
                dbaddv(@db, 
                    "net",      'TA',
                    "sta",      $station,
                    "dlsta",    $dlsta,
                    "dfile",    $rf,
                    "time",     now(), 
                    "lddate",   now(), 
                    "status",   "downloaded");
            }
        }
        else { 
            elog_debug("$station File flagged: $rf ") if $opt_V;
            dbaddv(@db, 
                "net",      'TA',
                "sta",      $station,
                "dlsta",    $dlsta,
                "dfile",    $rf,
                "time",     now(), 
                "lddate",   now(), 
                "status",   "flagged");
            push @flagged, $rf;
        }
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
    my $debug   = shift;
    my $my_ftp;

    $debug ||= 0;

    if ($my_ip && $my_port && $station) {

        if ( $opt_f or $debug )  {
            $my_ftp = Net::FTP->new(Host=>$my_ip, Passive=>1, Timeout=>300, Port=>$my_port, Debug=>1);
        }
        else { 
            $my_ftp = Net::FTP->new(Host=>$my_ip, Passive=>1, Timeout=>180, Port=>$my_port, Debug=>0);
        }

        eval { $my_ftp->login()  }; 
        problem("Cannot login to $my_ip:$my_port ($@)". $my_ftp->message , $station) if ($@) ;

    }
    return $my_ftp;
#}}}
}

######################
#  Read rem/loc dir  #
######################
sub read_dir {
#{{{
   my $sta      = shift;
   my $path     = shift;
   my $ftp_pntr  = shift;
   my %file     = (); 
   my @directory= ();
   my $open;
   my $name;
   my $this_month;
   my $prev_month;
   my $prev_month_epoch;
   my $epoch;
   my $regex;
   my $line;
   my $f;
   my @n;
   my @split_name;
   my $attempt = 1;
   my $ip = $ftp_pntr->host if $ftp_pntr;

    if(defined($ftp_pntr)) {
        while ( $attempt <= 4 ) {

            #
            # Build regex for this month
            #
            $this_month = "*" . "$sta" . "_4-" . epoch2str( now(), "%Y%m") . '*';

            #
            # Build regex for prev. month
            #
            $regex = epoch2str( now(), "%m/1/%Y 00:00:00.0");
            $prev_month_epoch = str2epoch($regex) - 100;

            $prev_month = "*" . "$sta" . "_4-" . epoch2str( $prev_month_epoch, "%Y%m") . '*';

            #
            # Get list from Baler
            #
            elog_notify("$sta $ip:$pf{ftp_port} ftp->dir($path/$prev_month)(connection attempt $attempt).") if $opt_v;
            @directory = $ftp_pntr->dir("$path/$prev_month") if $ftp_pntr;

            elog_notify("$sta $ip:$pf{ftp_port} ftp->dir($path/$this_month)(connection attempt $attempt).") if $opt_v;
            push ( @directory , $ftp_pntr->dir("$path/$this_month") ) if $ftp_pntr;

            #
            # pntr->dir() sometimes fail. verify output
            #
            elog_notify("$sta (connection attempt $attempt) dir=". @directory) if $opt_V;

            if( scalar @directory or $path =~ /.*reserve.*/ ){
                #
                # if success...
                #
                foreach $line (@directory) {
                    next if $line =~ m/^d.+\s\.\.?$/;
                    @n = (split(/\s+/, $line, 9));
                    @split_name= split(/\//,$n[8]);
                    $name = pop @split_name;
                    $file{$name}{size} = $n[4];
                    elog_notify("\t$name-> $file{$name}{size}") if $opt_v;
                }
                last;
            }
            else { 
                #
                # if empty list...
                #
                $attempt ++;

                eval{ $ftp_pntr->quit(); };

                sleep 61;

                if ($attempt > 2 or $opt_V) { 
                    problem("Net::FTP $ip empty list for: $path ". $ftp_pntr->message, $sta);
                    elog_notify("$sta $ip:$pf{ftp_port} debug='on' (connection attempt $attempt).");
                    $ftp_pntr = loggin_in($ip,$pf{ftp_port},$sta,1);
                }
                else { $ftp_pntr = loggin_in($ip,$pf{ftp_port},$sta); }
            }
        } # end of while()
    } # end of ftp dir read

    else {
        if ( opendir DIR, $path ) { 
            while($f = readdir DIR) {
                my $file = "$path/$f";
                if(-d "$file"){ next; } 
                elsif($f =~ /..-...._\d-\d+-\d+/ ){ 
                    unlink $file; 
                    problem("Removing incomplete file ($file).", $sta);
                } 
                else { 
                    $file{$f}{size} = (stat($file))[7];
                    elog_notify("\t$f-> $file{$f}{size}") if $opt_V;
                }
            }
            close(DIR);
        }
        else{ elog_and_die("Failed to open $path: $!", $sta); }
    }

   return (\%file);
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
        if(! -e $local_path) { 
            makedir($local_path);
            elog_notify("$station New station. Local directory empty.");
        }
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
sub get_stations_from_db {
#{{{
    my ($dlsta,$net,$sta,$vnet);
    my ($equip_install,$equip_remove);
    my @active_stations;
    my %sta_hash;
    my @db_temp;
    my @db_2;
    my $nrecords;
    my $ip;

    #
    # Get list of active staions
    #
    @db_temp = dbsubset ( @db_on, "equip_install != NULL  && equip_remove == NULL");
    @db_temp = dbsubset ( @db_temp, "sta =~ /$opt_s/") if $opt_s;
    @db_temp = dbsubset ( @db_temp, "sta !~ /$opt_r/") if $opt_r;

    elog_log('RECORDS: active on deployment:'. dbquery(@db_temp, dbRECORD_COUNT) ) if $opt_V; 
    #
    # Get stations with baler44s
    #
    @db_temp = dbjoin ( @db_temp,@db_sta, "sta","deployment.snet#stabaler.net");
    @db_temp = dbsubset ( @db_temp, "stabaler.endtime == NULL");
    @db_temp = dbsubset ( @db_temp, "stabaler.model =~ /PacketBaler44/ ");

    elog_log('RECORDS: deployment join with stabaler and sub on BALER44:'. dbquery(@db_temp, dbRECORD_COUNT) ) if $opt_V; 

    #
    # Get ips for the selected stations
    #
    @db_temp = dbjoin ( @db_temp,@db_ip, "sta","dlsta","net");
    @db_temp = dbsubset ( @db_temp, " staq330.endtime == NULL ");

    elog_log('RECORDS: deployment join with stabaler join with staq330:'. dbquery(@db_temp, dbRECORD_COUNT) ) if $opt_V; 

    $nrecords = dbquery(@db_temp,dbRECORD_COUNT) ; 
    for ( $db_temp[3] = 0 ; $db_temp[3] < $nrecords ; $db_temp[3]++ ) { 
        ($dlsta,$net,$sta,$ip) = dbgetv(@db_temp, qw/dlsta net sta staq330.inp/); 

        elog_debug("$db_temp[3]) $dlsta | $net | $sta | $ip"  ) if $opt_V;

        $sta_hash{$sta}{dlsta}  = $dlsta; 
        $sta_hash{$sta}{net}    = $net; 
        $sta_hash{$sta}{active} = false; 

        #
        # regex for the ip
        #
        $ip=~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
        if ( ! $1) {
            problem("No IP for $sta in $pf{database}.stabaler{inp}->(ip'$ip',dlsta'$dlsta')",$sta);
        }
        else {
            $sta_hash{$sta}{ip} = $1; 
        }

        #
        # Verify deployment table
        #
        @db_2 = dbsubset ( @db_on, " sta =~ /$sta/ && snet =~ /$net/");
        if ( dbquery(@db_2,dbRECORD_COUNT) ) {
            $db_2[3] = dbquery(@db_2,dbRECORD_COUNT) - 1;
            ($vnet,$equip_install,$equip_remove) = dbgetv(@db_2, qw/vnet equip_install equip_remove/); 

            $sta_hash{$sta}{active}        = true; 
            $sta_hash{$sta}{vnet}          = $vnet; 
            $sta_hash{$sta}{equip_install} = $equip_install; 
            $sta_hash{$sta}{equip_remove}  = $equip_remove; 

        }
        else { 
            problem("Can not find sta == ($sta) && net == ($net) in deployment table.");
        }
    }  

    return \%sta_hash;
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

    foreach my $value (qw/local_data_dir remote_folder method_blacklist max_child_run_time
                        database min_bandwidth print_miniseed_errors print_fix_errors
                        ftp_path http_port fix_mseed_cmd max_procs ftp_port/){
        $pf{$value} = pfget($PF,$value);
        if( ! defined( $pf{$value}) ) { elog_and_die("Missing value for $value in PF:$PF"); }
        elog_debug( sprintf("\t%-22s -> %s", ($value,$pf{$value})) ) if $opt_V;
    }

    elog_debug('') if $opt_V;

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

    elog_debug("Verify Database: ".dbquery(@$db,"dbDATABASE_NAME") ) if $opt_V;

    if (! dbquery(@$db,"dbTABLE_PRESENT")) {
            elog_and_die( dbquery(@$db,"dbTABLE_NAME")." table is not available.",$sta);  
    }
    else { 
        if ( $opt_V ) {
            elog_debug("\t".dbquery(@$db,"dbDATABASE_NAME")."{ ".dbquery(@$db,"dbTABLE_NAME")." }: dbTABLE_PRESENT --> OK"); 
            elog_debug('');
        }
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
# Print pf structures#
######################
sub print_pf { 
#{{{
    my $r     = shift;
    my $level = shift;
    my $tab;
    my $nexttab;
    my $k1;
    my $v1;
    my $i;
    my $line;

    foreach (0 .. $level){ $tab .= "    "; }
    $level += 1;
    $nexttab = $tab . "    ";

    while( ($k1,$v1) = each %$r ){
        if (ref($v1) eq "ARRAY") {
            elog_debug("${tab} $k1@ >>");
            for $i (0 .. (@$v1-1)){
                if ( ref(@$v1[$i]) eq "ARRAY" ) {
                    elog_debug("${nexttab} $i @ >>");
                    print_pf(@$v1[$i],$level+1);
                }
                elsif ( ref(@$v1[$i]) eq "HASH" ) {
                    elog_debug("${nexttab} $i % >>");
                    print_pf(@$v1[$i],$level+1);
                }
                else {
                    if (length($i) > 30) {
                        elog_debug("$nexttab$i --> @$v1[$i]");
                    }
                    else{
                        $line = '';
                        for (my $n=0; $n < 30-length($i); $n++){ $line .= '-'; }
                        elog_debug("$nexttab$i$line> @$v1[$i]");
                    }
                }
            }
        }
        elsif (ref($v1) eq "HASH") {
            elog_debug("${tab} $k1 % >>");
            print_pf($v1,$level);
        }
        else{
            if (length($k1) > 30) {
                elog_debug("$tab$k1 --> $v1");
            }
            else{
                $line = '';
                for (my $n=0; $n < 30-length($k1); $n++){ $line .= '-'; }
                elog_debug("$tab$k1$line> $v1");
            }
        }
    }
#}}}
}

######################
# Track  problems    #
######################
sub problem { # use problem("log of problem");
#{{{
    my $text = shift; 
    my $station = shift; 

    $Problems++;

    $station ||= '*NONE*';

    $problems_hash->{$station}->{$Problems} = $text;

    elog_complain("*");
    elog_complain("*");
    elog_complain("* Problem #$Problems:");
    elog_complain("* \t$station: $text");
    elog_complain("*");
    elog_complain("*");
#}}}
}

######################
# Track  problems    #
######################
sub problem_print { # use problem();
#{{{

    my $s_v; 
    my $p_v; 

    $Problems ||= 0;

    elog_complain('');
    elog_complain('');
    elog_complain("-------- Problems: --------");
    elog_complain('');

    if ( $Problems > 0 ){

        for  $s_v ( sort keys %$problems_hash ) {
            elog_complain("\tOn station $s_v:");
            for $p_v ( sort keys %{$problems_hash->{$s_v}} ) {
                elog_complain("\t\t $p_v) $problems_hash->{$s_v}->{$p_v}");
            }
            elog_complain('');
        }

    }
    else {
        elog_complain('No problems.');
    }

    elog_complain("-------- End of problems: --------");
    elog_complain('');

#}}}
}

######################
# Init mail tmp file #
######################
sub savemail { 
#{{{
    my ($tmp) = @_ ;
    $tmp = "/tmp/#$0_maillog_$$" if ! defined $tmp ;
    
    unlink($tmp) if -e $tmp;

    #$ENV{'ELOG_DELIVER'} = "stdout $tmp";
    # OR
    open(SAVEOUT, "&STDOUT");
    open(SAVEERR, "&STDERR");
    open ( STDOUT, ">$tmp");
    open ( SAVEERR, ">&STDOUT");

    
#}}}
}

######################
# Send and clean mail#
######################
sub sendmail { 
#{{{
    my ( $subject, $who, $tmp ) = @_ ;

    my $result;

    $tmp = "/tmp/#$0_maillog_$$" if ! defined $tmp ;
    open ( STDERR, &SAVEERR ) ;
    open ( STDOUT, &SAVEOUT ) ;
    $who =~ s/,/ /g ;
    $result = system ( "rtmail -C -s '$subject' $who < $tmp");
    if ( $result != 0 ) { 
        warn ( "rtmail fails: $@\n" ) ;
    }
    $result = system ( "cat $tmp");
    unlink $tmp ; 
#}}}
}

__END__
#{{{
=pod

=head1 NAME

rsync_baler - Sync a remote baler directory to a local copy

=head1 SYNOPSIS

rsync_baler [-h] [-v] [-V] [-j file] [-R days] [-s sta_regex] [-r sta_regex] [-p pf] [-m email,email]

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h> 

Produce this documentation

=item B<-v> 

Produce verbose output while running

=item B<-V>

Produce very-verbose output (debuggin)

=item B<-f>

Debug FTP connection.

=item B<-p file>

Parameter file name 

=item B<-j file>

Produce report of databases in json format.

=item B<-s>

Select station regex 

=item B<-r>

Reject station regex 

=item B<-R days>

Produce report of the past X days

=item B<-m email,email,email>

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
