use Datascpe; 
use archive;
use sysinfo;
use File::Copy;

######################
#                    #
#  Program setup     #
#                    #
######################

$cmd = $0;
$cmd =~ s".*/"";
$date= localtime();
$host = my_hostname();

getopts('vp:m:');

#
#Get parameters
#
$PF = $opt_p || "rsync_baler.pf" ;
%pf = getparam($PF);


#
#Save log if send_mail==1
#
if ( $opt_m ) { savemail(); }


elog_notify("\nStarting execution on   $host   $date\n\n");

if( $opt_v ) {
    elog_notify("Variables:");
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
if(! -f $pf{ftp_dir} )  {
    die_and_mail("Problems with ftp directory $pf{ftp_dir}: $!");
}
if(! -f $pf{archive} )  {
    die_and_mail ("Problems with archive directory $pf{archive}: $!");
}
if(! -f $pf{dump} )  {
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
die "End of test";
#
# For each file...
#
FILE: while( my($file,$size) = each %$files_ref ) {
#
# Get the station name
#
    $file =~ /($format)/ ;
    $station = $3;

#
# Append previous station to log if any
#
    elog_notify("\n") if $opt_v;
    elog_notify("$station") if $opt_v;

#
# Check if unique
#
    $prev_files = read_dir( $archive );
    while( my $prev = keys %$prev_files ) {
        if( $file =~ m/($prev)/ ) {
            problem("File already in database!.");
            elog_notify("Moving file to $pf{dump}.") if $opt_v;
            if (! move($file, "$pf{dump}/${file}_duplicate") ) {
                problem("Error moving file $file to $pf{dump}: $!");
            }
            next FILE; 
        }   
    }

    elog_notify("Starting migration of data.") if $opt_v;

#
# Create Folders
#
    $folder_name = folders();
    $mseed       = "${folder_name}/mseed";

    if (-e $mseed ) {
#
# Copy the file
#
        elog_notify("Copy file $file to $mseed.") if $opt_v;
        if (! copy($file, "$mseed/$file") ) {
            problem("Error on copy of file $file to $mseed: $!");
            next FILE;
        }

#
# BALER2DB
#
        elog_notify("baler2db on file.") if $opt_v;
        system("baler2db $mseed /anf/TA/dbs/dbmaster/usarray /anf/TA/baler/all_ta_data > $folder_name/list_cd_baler2db");

#
# DBVERIFY
# 
        if (! -e "${folder_name}/raw_baler.wfdisc" ) {
            problem("No raw_baler.wfdisc from baler2db on $file);"
            read_log("${folder_name}/list_cd_baler2db");
            next FILE;
        }

        elog_notify("dbverify on raw.") if $opt_v;
        system("dbverify $folder_name/raw_baler.wfdisc > $folder_name/outver_raw");

        elog_notify("dbverify on clean.") if $opt_v;
        system("dbverify $folder_name/cleaned_baler.wfdisc > $folder_name/outver_cln");

        read_log("${folder_name}/outver_raw");
        read_log("${folder_name}/outver_cln");

#
# If success, move file
#
        if (-e "$mseed/$file") { 
            elog_notify("Moving $file to $pf{dump}");
            if (! move($file, "$pf{dump}/") ) {
                problem("Error moving file $file to $pf{dump}: $!");
            }
        }
        else {
            problem("Error on cp command ($copy). Leaving file $file");
        }

    } #end of if $mseed

    else { 
        problem("Can't create new folder structure");
        elog_complain("Leaving file on ftp directory $pf{ftp_dir}"); 
    }

} #end of while

print $log if $v;
if ( $sta_log ) {
  if ( $Problems ) { $add = "ERROR in"; }
  else {$add ="Successful"; }
  $subject = " $cmd on $host";
  &sendmail($subject,$office) if $pf{send_mail} ;
}


###############################
# FUNCTIONS                   #
###############################


######################
#                    #
#  Read directory    #
#                    #
######################
sub read_dir {
    my $path = shift;
    my $file = {}; 
    my $DIR;

    elog_notify("Now with directory $path") if $opt_v;
    opendir $DIR, $path or die_and_mail("Failed to open $path: $!");

    while(my $f = readdir $DIR) {
        next if $f eq "." or $f eq "..";
        my $test = $path."/".$f;
        if(-d $test){ next; } 
        if ($f =~ /($format)/) { 
        elog_notify("Found file $f for station $3" if $opt_v;
        $file->{$test} = (-s $test); 
        }   
   }   
   close $DIR;
   return ($file);
} #end of read_local_dir


######################
#                    #
#  Create Folders    #
#                    #
######################
sub folders {
    my $f_log; 

#
# Prepare folder structure
#
    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
    $year += 1900;
    $mon += 1;
    $month = sprintf("%02d",$mon);
    $mday = sprintf("%02d",$mday);
    my $folder_name = "${archive}/${year}_${month}_${mday}";

#
# Check if we need to append version
#
    if (-e $folder_name ) {
        $original = $folder_name;
        for $ver (1..20) {
            $new_folder_name = "${folder_name}_$ver";
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
    $mseed = "${folder_name}/mseed";
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
    $log = "\n\t-----------------------------\n";

    if ( -f $file ) {
        open (TEXT, "<$file");
        while (<TEXT>) {
            $log .=  "\t$_";
        }
        close TEXT;
    }
    else { problem("No file $file"); }

    $log .= "\n\t-----------------------------\n";

    elog_complain($log);

}

######################
#                    #
# Check for siblings #
#                    #
######################
sub check_siblings {
  
  $my_cmd = $0;
  $my_cmd =~ s".*/"";

  elog_notify("$my_cmd with PID $$") if $opt_v;
  open $output, "-|", "ps -e -o pid,args" or die_and_mail("Can't run ps -e:$!"); 
  while(<$output>) {
    split; 
    my $pid = shift(@_);
    my $cmd = join('',@_);

    if ($cmd =~ m/$my_cmd/) {
        if ( $pid eq $$ ) { next; }
        else { return 1; }
    }
  }
  close $output;
  return 0;
}

######################
#                    #
#  Send email and die#
#                    #
######################
sub die_and_mail {
    my $why = shift;

    if ( $pf{send_mail} ) {
        problem("$why");
        sendmail("$0 died with $errors errors on host $host",$opt_m);
    }
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

    foreach my $value (qw/format wait verbose send_mail ftp_dir archive dump /){
        $pf{$value} = pfget($PF,$value);
        if( ! defined( $pf{$value}) ) { 
            die_and_mail("Missing value for $value in PF:$PF"); 
        }
        elog_notify( "\t\t$value -> $pf{$value}") if $opt_v;
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
    elog_complain("\t\t$_");
    elog_notify("\n");
}

