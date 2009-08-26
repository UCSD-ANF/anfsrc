use Datascope; 
use archive;
use sysinfo;
use Getopt::Std;
use File::Copy;
use POSIX ":sys_wait_h";

use strict;

our ($cmd,$host,$date,$PF,%pf,$Problems,@errors);
our ($pid,$files_ref,$file,$station,$prev_files);
our ($opt_v,$opt_m,$opt_p);
our ($folder_name,$mseed);
our ($subject,$title);

######################
#                    #
#  Program setup     #
#                    #
######################

$cmd = $0;
elog_init($cmd, @ARGV);
$cmd =~ s".*/"";
$date= localtime();
$host = my_hostname();

getopts('vp:m:');

#
#Get parameters
#
$PF = $opt_p || "ftp_uploads.pf" ;
%pf = getparam($PF);

#
#Save log if send_mail==1
#
if ( $opt_m ) { savemail(); }


elog_notify("\nStarting execution on   $host   $date\n\n");

if( $opt_v ) {
    elog_notify("Variables:");
    elog_notify("\tFormat : $pf{format} ");
    elog_notify("\tFTP dir: $pf{ftp_dir}");
    elog_notify("\tArchive: $pf{archive}");
    elog_notify("\tDump   : $pf{dump}   ");
    elog_notify("\tMail   : $opt_m      ");
} 
    

######################
#                    #
#  Sanity Check      #
#                    #
######################

#
# Check Dirs
#
if(! -d $pf{ftp_dir} )  {
    die_and_mail("Problems with ftp directory $pf{ftp_dir}: $!");
}
if(! -d $pf{archive} )  {
    die_and_mail ("Problems with archive directory $pf{archive}: $!");
}
if(! -d $pf{dump} )  {
    die_and_mail ("Problems with dump directory $pf{dump}: $!");
}

#
# Check for siblings 
#
if ( check_siblings() ) { 
    die_and_mail("Another copy of $0 running!"); 
}

######################
#                    #
#  Start main        #
#                    #
######################

#
# Read ftp direcotry
#
elog_notify("Reading dirctory $pf{ftp_dir}") if $opt_v;
$files_ref = read_dir( $pf{ftp_dir} );

#
# For each file...
#
FILE: while( my($file,$size) = each %$files_ref ) {

#
# Get the station name
#
    $file =~ /($pf{format})/ ;
    $station = $3;
    elog_notify("\n") if $opt_v;
    elog_notify("$station") if $opt_v;

#
# Stop if no station name was found
#
    if (! $station) { 
        elog_complain("No match out of regex!: $pf{format}");
        next FILE;
    }

    elog_notify("Starting migration of data.") if $opt_v;

#
# Create Folders
#
    $folder_name = folders($pf{archive});
    $mseed       = "${folder_name}/mseed";
    if (-e $mseed ) {
#
# Copy the file
#
        elog_notify("Copy $file to $mseed/") if $opt_v;
        if (! copy("${file}", "${mseed}/") ) {
            problem("Error on copy of file $file to $mseed/: $!");
            next FILE;
        }

#
# BALER2DB
#
        elog_notify("baler2db on file.") if $opt_v;
        $pid = run_cmd("xterm -e sh -c \"baler2db $mseed /anf/TA/dbs/dbmaster/usarray /anf/TA/baler/all_ta_data > $folder_name/list_cd_baler2db 2>&1\" ");
        if (! $pid) { next FILE; }
        wait_for_pid($pid);


#
# DBVERIFY
# 
        if (! -e "${folder_name}/raw_baler.wfdisc" ) {
            problem("No raw_baler.wfdisc from baler2db on $file");
            read_log("${folder_name}/list_cd_baler2db");
            next FILE;
        }

        elog_notify("dbverify on raw.") if $opt_v;
        $pid = run_cmd("xterm -e sh -c \"dbverify -v ${folder_name}/raw_baler.wfdisc > ${folder_name}/outver_raw 2>&1\"");
        if (! $pid) { next FILE; }
        wait_for_pid($pid);

        elog_notify("dbverify on clean.") if $opt_v;
        $pid = run_cmd("xterm -e sh -c \"dbverify -v ${folder_name}/cleaned_baler.wfdisc > ${folder_name}/outver_cln 2>&1\"");
        if (! $pid) { next FILE; }
        wait_for_pid($pid);

        read_log("${folder_name}/outver_raw");
        read_log("${folder_name}/outver_cln");

#
# If success, move file
#
        if ( -e "${folder_name}/cleaned_baler.wfdisc" ) {
            elog_notify("Moving $file to $pf{dump}");
            if (! move($file, "$pf{dump}/") ) {
                problem("Error moving file $file to $pf{dump}: $!");
            }
        }
        else {
            problem("Leaving file $file in place.");
        }

    } #end of if $mseed

    else { 
        problem("Can't create new folder structure");
        elog_complain("Leaving ${file} in $pf{ftp_dir}"); 
    }

} #end of while



if ( $Problems ) { $title = "finished with ERROR(S)"; }
else {$title ="Successful"; }
$date= localtime();
$subject = "$cmd $title on $host at $date";
elog_notify($subject);
sendmail($subject,$opt_m) if $opt_m;


###############################
# FUNCTIONS                   #
###############################


######################
#                    #
#  Start new child   #
#                    #
######################
sub run_cmd { 
    my $command   = shift;

    elog_notify("\t\t$command") if $opt_v;

    my $resp = fork();
    if (! $resp) { exec($command); }

    if(pid_exists($resp)){ 
        elog_notify("\t\tPID:$resp") if $opt_v;
        return $resp;
    }       
    problem("No pid: $resp for $command");
    return 0;
}

######################
#                    #
# Wait for pid to end#
#                    #
######################
sub wait_for_pid {
    my $proc = shift;
    my $resp = 0;

    while(1) {
        $resp = waitpid($proc,WNOHANG);
        if ($resp == -1) {
            problem("Problems with PID:$proc $?");
            last;        
        }   
        elsif (WIFEXITED($?)) { last; }   
    }     
}


######################
#                    #
#  Read directory    #
#                    #
######################
sub read_dir {
    my $path = shift;
    my $file = {}; 
    opendir DIR, $path or die_and_mail("Failed to open $path: $!");

    while(my $f = readdir DIR) {
        next if $f eq "." or $f eq "..";
        my $test = $path."/".$f;
        if(-d $test){ next; } 
        $file->{$test} = (-s $test); 
    }
    close DIR;
    return ($file);
} #end of read_local_dir


######################
#                    #
#  Create Folders    #
#                    #
######################
sub folders {
    my $archive = shift;
    my $f_log; 

#
# Prepare folder structure
#
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
    $year += 1900;
    $mon += 1;
    my $month = sprintf("%02d",$mon);
    $mday = sprintf("%02d",$mday);
    my $folder_name = "${archive}/${year}_${month}_${mday}";

#
# Check if we need to append version
#
    if (-e $folder_name ) {
        my $original = $folder_name;
        for my $ver (1..20) {
            my $new_folder_name = "${folder_name}_$ver";
            if (-e $new_folder_name) { next;}
            else { $folder_name = "${folder_name}_$ver"; last; }
        }
        if ($original eq $folder_name) {
            problem("Can't create new folder $folder_name. More than 20 versions.");
        return 0;
        }
    }
#
# Creating folders
#
    my $mseed = "${folder_name}/mseed";
    mkdir $folder_name or die_and_mail("Can't mkdir $folder_name"); 
    mkdir $mseed or die_and_mail("Can't mkdir $mseed");

    if ( -e $mseed ) { return($folder_name); }
    else { return 0; }

}


######################
#                    #
#  Read ext. logfile #
#                    #
######################
sub read_log {
    my $file = shift;
    my $log;

    elog_notify("Output of $file:");

    if ( -f $file ) {
        $log = "\n\n\t-----------------------------\n";
        open (TEXT, "<$file");
        while (<TEXT>) {
            $log .=  "\t$_";
        }
        close TEXT;
        $log .= "\n\t-----------------------------\n";
    }
    else { problem("No log file $file"); }


    elog_complain($log);

}

######################
#                    #
# Check for siblings #
#                    #
######################
sub check_siblings {
  
  elog_notify("$0 with PID $$") if $opt_v;
  open output, "-|", "ps -e -o pid,args" or die_and_mail("Can't run ps -e:$!"); 
  while(<output>) {
    split; 
    my $pid = shift(@_);
    my $cmd = join('',@_);

    if ($cmd =~ m/$0/) {
        if ( $pid eq $$ ) { next; }
        else { return 1; }
    }
  }
  close output;
  return 0;
}

######################
#                    #
#  Send email and die#
#                    #
######################
sub die_and_mail {
    my $why = shift;

    problem($why);
    if ( $opt_m ) { sendmail("$0 died on host $host",$opt_m); }
    elog_die("ERROR: $0 died on host $host");
}

######################$
#                    #$
#  Read PF file      #$
#                    #$
######################$
sub getparam { # %pf = getparam($PF);
    my ($PF) = @_ ;
    my ($subject);
    my (%pf) ;

    foreach my $value (qw/format ftp_dir archive dump /){
        $pf{$value} = pfget($PF,$value);
        if( ! defined( $pf{$value}) ) { 
            die_and_mail("Missing value for $value in PF:$PF"); 
        }
    }  

    return (%pf);
}

######################
#                    #
# Report problems    #
#                    #
######################
sub problem { # use problem("log of problem");
    my $text = shift; 

    push(@errors,$text);

    $Problems++ ;
    elog_notify("\n");
    elog_complain("Problem #$Problems") ;
    elog_complain("\t\t$text");
    elog_notify("\n");
}

