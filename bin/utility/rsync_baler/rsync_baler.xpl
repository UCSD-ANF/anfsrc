use Datascope ;
use sysinfo;
use archive;
use Getopt::Std;
use FileHandle;


our($opt_v, $opt_m, $opt_v) ;
our($PF,$DB);

######################
#                    #
#  Program setup     #
#                    #
######################

    $pgm = $0;
    elog_init($pgm, @ARGV);
    $cmd = "\n$0 @ARGV" ;
    $start = now();


    if ( ! &getopts('dvm:p:') || @ARGV != 1 ) { 
      $usage  = "\n\nUsage: $0 \n [-v][-d]";
      $usage .= "[-p pf] [-m mail_to] DB \n\n";
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
    elog_notify("Initialize mail") if $opt_v && $opt_m;
    savemail() if $opt_m ; 

    elog_notify( $cmd ) if $opt_v;
    elog_notify ("Starting execution on ".`uname -n`) if $opt_v;
    elog_notify (strydtime($start)) if $opt_v;

    #
    # Get parameters
    #
    elog_notify("Getting params") if $opt_v;
    $PF         = $opt_p || "rsync_baler.pf" ;
    %pf = getparam($PF);

######################
#                    #
#  Sanity Check      #
#                    #
######################
    elog_notify("Look for data directory") if $opt_v;
    if(! -e $pf{local_data_dir} )  {
        elog_and_die("Configuration error.\n\tError in dir => $pf{local_data_dir} .");
    }

    elog_notify("Look for DB") if $opt_v;
    if(! -e ${DB} )  {
        elog_and_die("Configuration error.\n\tError in DB => ${DB} .");
    }

    elog_notify("Check for siblings") if $opt_v;
    if ( check_siblings() ) { 
        elog_and_die("Another copy of $0 running.");
    }
######################
#                    #
#  Get station list  #
#  from database     #
#  or PF file        #
#                    #
######################
    @stas = get_stations($DB);

######################
#                    #
#  Start sync of data#
#                    #
######################
    STATION: while ( scalar @stas ) {
        $station = pop(@stas);
        elog_notify("Start getftp of station $station") if $opt_v;
        
        if( $pid_tbl{$station}{PID} ) { 
            elog_notify("Previous instance of $station") if $opt_v;
            $tem_pid = $pid_tbl{$station}{PID};
            if( eval pid_exists($temp_pid) ){ 
                elog_notify("Verified PID $temp_pid ") if $opt_v; 
                next STATION;
            }
            else{ 
                elog_notify("Can't find PID=$temp_pid") if $opt_v; 
                elog_notify("Starting new wget of $station") if $opt_v; 
            }

        }

        if ( $ip_sta=get_ip($DB,$station) ) {
            #
            # Prepare Variables
            #
            $local_path = "$pf{local_data_dir}/$station";
            $log = "$local_path/log";
            if(! -e $local_path) { makedir($local_path); }
            if(! -e $log) { makedir($log); }

            #
            # Clean logfile
            #
            $log .= "/$station.txt";
            open(LOG,">$log") or elog_and_die("Can't create $log: $!");
            print LOG "LOG-PARENT: $cmd on $stime \n\n";
            close(LOG);

            #
            # Start child
            #
            $pid =
                new_child($station,$ip_sta,$pf{port},$local_path,$pf{ftp_path},$log);
            $LOGFILE = "${station}_${pid}";
            open ($LOGFILE , "<$log") or elog_and_die(" Can't open logfile $log: $!");

            #
            # Store data in hash element
            #
            $pid_tbl{$station}{PID}           = $pid;
            $pid_tbl{$station}{log_file_pntr} = $LOGFILE;
            $pid_tbl{$station}{IP}            = $ip_sta;
            $pid_tbl{$station}{PORT}          = $pf{port};
            $pid_tbl{$station}{LOCAL_DIR}     = $local_path;
            $pid_tbl{$station}{LOGFILE}       = $log;

            if($opt_d) {
              elog_notify("\tNEW CHILD OBJECT:");
              for my $key ( keys %{$pid_tbl{$station}} ) {
                    elog_notify("\t\t$key => $pid_tbl{$station}{$key}\n");
              }
            }

            #
            # Go to SysAdmin loop
            #
            monitor_child($pf{max_procs} ,\%pid_tbl);

            $elapsed = now() - $start;
            if ( $pf{mode} eq 'continuous') {
                if( $elapsed > $pf{max_time} ) {
                    report();
                    $start = now();
                    @stas = get_stations($DB);
                }
            }
            else{
                if( $elapsed > $pf{max_time} ) {
                    last STATION;
                }
            }


        } #end of if $address

        else { elog_complain("No ip for station $station") if $opt_v; } 


    } #end of while $station

    monitor_child(1,\%pid_tbl);

    report();

###############################
# FUNCTIONS                   #
###############################


######################
#                    #
#  Report status     #
#                    #
######################
sub report {

    elog_notify("=================================");
    elog_notify("=Report rsync_balers            =");
    for my $sta ( sort keys %pid_tbl ) {
        elog_notify("=================================");
        elog_notify("STA: $sta");
        if($pid_tbl{$sta}{PID} != 0) {
            elog_notify("\tDownloading now.");
        }
        else{
            for my $key ( sort keys %{$pid_tbl{ $sta }} ) {
                if    ($key eq "PID" || $key eq "log_file_pntr") { next;}
                elog_notify("\t$key => $pid_tbl{ $sta }{ $key }");
            }
        }
        elog_notify("=================================");
    } 
    elog_notify("Active PID's:");
    for my $sta ( sort keys %pid_tbl ) {
        if($pid_tbl{$sta}{PID} == 0) {next;}
        elog_notify("\t$sta => $pid_tbl{$sta}{PID}");
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
  my $ip        = shift;
  my $port      = shift;
  my $local_path= shift;
  my $ftp_path  = shift;
  my $log_file  = shift;

    elog_notify("Starting new wget for station $station") if $opt_v ;

    $args = ("\twget --passive-ftp --continue --timestamping --no-directories -o $log_file -P $local_path \"ftp://$ip:$port/$ftp_path/*\" &");

    elog_notify("\t$args") if $opt_v;

    my $my_pid = open(TO_READ, "-|",$args );

#
# Check the PID 
# 
    elog_notify("\tReported by perl: $my_pid") if $opt_v;
    if(! eval pid_exists($my_pid)){ 
        elog_notify("\tERROR in PID $my_pid") if $opt_v;
        $my_pid += 1;
    }
    if(! eval pid_exists($my_pid)){
    elog_notify("\tERROR in PID $my_pid") if $opt_v;
    return 0; 
    }

    elog_notify("\tUsing PID $my_pid") if $opt_v;


    if($opt_d){
        my %info = pidinfo($my_pid);
        for my $key ( keys %info ) {
        elog_notify("\t$key => ".$info{$key});
        }
    }
    return $my_pid;
}


######################
#                    #
#  Monitor child     #
#                    #
######################
sub monitor_child { 
    my $cnt = shift;
    my $ptable = shift;
    my $active_pids;
    my $log;
    my $pid;
    my $temp_regex;


      while( 1 ) {
        # 
        # Get active PID's
        #
        $active_pids = 0 ;
        for my $sta ( keys %$ptable ) {
          if ( $ptable->{$sta}->{PID} ) { 
            ++$active_pids;
          }
        }
        #
        #If last loop, sleep 
        #and wait for logs to
        #update.
        #
        if ($active_pids == 0) { sleep(2); } 

        for my $sta ( keys %$ptable ) {
          $log = $ptable->{$sta}->{log_file_pntr};
          $pid = $ptable->{$sta}->{PID};

          if (!defined($log)) { 
            elog_complain("ERROR: No logfile defined for $sta") if $opt_v;
            next;
          }
          elog_notify("$sta reading from  logfile $log") if $opt_d;

          $ptable->{$sta}->{LAST_CHECKED} = strydtime(now());

          #
          #read from last position 
          #
          while (<$log>){
            elog_notify("\t$sta || $_") if $opt_d;
            if ($_ =~ m/^.*RETR (.*) ... done.$/) { push($ptable->{$sta}->{FLAGGED},$1); }
         }
         #
         #This will clear
         #EOF flag on pointer
         #
         $log->clearerr();

         #check pid
         if ( ! eval pid_exists($pid) ) {
            $ptable->{$sta}->{PID} = 0;
         }
      }
      if ($active_pids < $cnt) { last; } 
   }
   return 0;
}

######################
#                    #
#  Get IP from DB    #
#                    #
######################
sub get_ip {
  my $db        = shift;
  my $sta       = shift;
  my $address;
  my $table  = $pf{db_table};
  my $column = $pf{db_table_cl};


  elog_notify("Looking for IP") if $opt_v;
  elog_notify("Opening database: $db") if $opt_v;
  @db = dbopen ( $db, "r" ) or elog_complain("ERROR: No DB in: $db ***"); 

  if(@db == NULL) { elog_and_die("ERROR: \n\n\t**Can't access DB $db**"); };  

  @db = dblookup(@db, "", $table, "", "");
  @db = dbsubset ( @db, " sta =~ /$sta/ ");
  @db = dbsort( @db,"time" );

  $nrecords = dbquery(@db,dbRECORD_COUNT) ; 
  elog_notify("$nrecords records for sta $sta in DB $db") if $opt_v;

  if ($nrecords) {
    $db[3]  =  $nrecords - 1;
    $address=  dbgetv(@db, $column); 
    $address=~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
    elog_notify("Found ip=$1") if $opt_v;
    return $1;
  }
  else { 
    elog_notify("ERROR: No records for sta $sta in DB $db") if $opt_v;
    return 0; 
  }

} #end of get_ip

######################
#                    #
#  Get Stas from DB  #
#                    #
######################


sub get_stations {
  my $db_name = shift;
  my @list   = @{$pf{sta_list}};
  my $table  = $pf{db_sta_table};
  my $column = $pf{db_sta_table_cl};
  my $string = $pf{db_sta_table_st};
  my @sta_array;

    elog_notify("Looking for stations") if $opt_v;

    if( scalar @list ){
        elog_notify("Using stations in PF file.") if $opt_v;
        foreach ( @list ) {
          push(@sta_array,$_);
          elog_notify("\tStation - $_") if $opt_v;
        }
    }
    else {
        elog_notify("Using stations in DB: $db_name") if $opt_v;

        my @db = dbopen ( $db_name, "r" ) or elog_and_die("ERROR: Can't open sta_db: $db_name"); 
        $db = dbquery (@db, "dbDATABASE_NAME") ; 
        $dbpath = dbquery (@db, "dbDBPATH") ; 
        @db = dblookup(@db, "", $table , "", "");
        @db = dbsubset ( @db, " $column =~ /$string/ ");
        @db = dbsort ( @db, "-u", "sta");

        $nrecords = dbquery(@db,dbRECORD_COUNT) ; 
        elog_notify("$nrecords records in DB $db") if $opt_v;
        for ( $db[3] = 0 ; $db[3] < $nrecords ; $db[3]++ ) { 
          $sta = dbgetv(@db, 'sta'); 
          elog_notify("\tStation - $sta") if $opt_v;
          push @sta_array, $sta;
        }  
    }

    return @sta_array;

} #end of get_stations


######################
#                    #
#  Read PF file      #
#                    #
######################
sub getparam { # %pf = getparam($PF);
    my ($PF) = @_ ;
    my ($subject);
    my (%pf) ;

  foreach my $value (qw/local_data_dir ftp_path ftp_login ftp_pass 
                        sta_list db_table db_table_cl db_sta_table db_sta_table_cl 
                        db_sta_table_st max_procs port mode max_time/){
      $pf{$value} = pfget($PF,$value);
      elog_notify( "$value -> $pf{$value}") if $opt_v;
  }

  if(!defined( $pf{ftp_path}   ) ) { $pf{ftp_path} ='/';    }
  if(!defined( $pf{ftp_login} ) ) { $pf{ftp_login}  =''; }
  if(!defined( $pf{ftp_pass}  ) ) { $pf{ftp_pass}  ='';  }
  if(!defined( $pf{mode}      ) ) { $pf{mode}  ='continuous';  }
  if(!defined( $pf{port}      ) ) { $pf{port}  ='5382';  }
  if(!defined( $pf{max_time}  ) ) { $pf{max_time}  ='14400';  }
  if(!defined( $pf{sta_list}  ) ) { $sta_list = '.*';     }

  if(!defined($pf{local_data_dir}) ) {
      elog_complain("ERROR: \n\nMissing local_data_dir $pf{local_data_dir}.");
      $subject = "Problems - $pgm $host   Paremeter file error.";
      sendmail($subject, $opt_m) if $opt_m ;
      elog_and_die("\n$subject");
  }

    return (%pf);

} #end of getparam
 
######################
#                    #
# Check for siblings #
#                    #
######################
sub check_siblings {

  #get rid of arguments if any
  my @temp = split(/ /,$0);

  #get rid of abs-path
  #only need the last
  my @cmds = split(/\//,shift(@temp));
  my $my_cmd = pop(@cmds);


  elog_notify( "I'm $my_cmd with PID $$") if $opt_v;
  open $output, "-|", "ps -ef" or elog_and_die("ERROR: Can't run ps -e:$!");
  while(<$output>) {
    $line=$_;
    if ($line =~ m/$my_cmd/) {
      if ( $line =~ m/$$/ ) { 
          elog_notify( "I see myself PID: $$ in \n $line") if $opt_v; 
          }
      else { return 1; }
    }

  }
  close $output;
  return 0;
}
 
######################
#                    #
# update to elog_die #
#                    #
######################
sub elog_and_die {
    my $msg = shift;

    if ($opt_m) { 
        elog_notify("\n\n");
        elog_complain($msg);
        sendmail("ERROR ON $0 $host ", $opt_m); 
    }

    elog_die($msg);

}
