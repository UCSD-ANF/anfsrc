
#
# STATION_AOF_DUMPS
# The script reformats a folder 
# with BVLAOU and VLAOU files 
# from a baler into a station
# folder. 
# 10/27/2010
# Juan Reyes
# reyes@ucsd.edu
#
use strict; 
use warnings;

use Datascope ;
use archive; #to send emails
use sysinfo;
use Getopt::Std;
use File::Copy 'copy';
use File::Path 'mkpath';
use File::Spec 'rel2abs';

our($results,$pgm,$cmd,$usage);
our($SOURCE,$ARCHIVE,$DIR,$FF);
our($opt_d,$opt_m,$opt_v,$opt_n);
our($k1,$k2,$test);

#{{{
    $cmd = "\n$0 @ARGV" ;

    elog_init($0,@ARGV);

    if ( ! getopts('vndm:') || @ARGV < 2) { 
        $usage  = "\n\nUsage: $0 [-v] [-n] [-d] [-m email] source archive [dirRegex] [filesRegex]\n\n";
        elog_notify($cmd);
        elog_die($usage);
    }

    $SOURCE     = $ARGV[0];
    $ARCHIVE    = $ARGV[1];
    $DIR        = $ARGV[2];
    $FF         = $ARGV[3];

    if(!defined( $DIR  ) || $DIR eq '-' ) { $DIR=('BVLAOU|VLAOU');}
    if(!defined( $FF   ) || $FF  eq '-' ) { $FF ='(C\d*_){1}(.+){1}\.bms(_\d*)?';}

    #
    # Convert to absolute path
    #
    $SOURCE  = File::Spec->rel2abs($SOURCE);
    elog_die("ERROR: Can't access direcotry $SOURCE\n\n") unless -d $SOURCE;

    $ARCHIVE = File::Spec->rel2abs($ARCHIVE);
    elog_die("ERROR: Can't access direcotry $ARCHIVE\n\n") unless -d $ARCHIVE;

    elog_notify("Initialize mail") if $opt_v && $opt_m;
    savemail() if $opt_m ; 

    elog_notify($cmd);
#}}}

#
# Main
#
#{{{
    read_move();
    elog_notify("END") if $opt_v;
    sendmail("$0 ".my_hostname() , $opt_m) if $opt_m;
#}}}

sub read_move {
#{{{

    my $file;

    elog_notify("Reading source dirctory $SOURCE") if $opt_v;

    #
    # error out on single files
    #

    elog_notify("open directory $SOURCE") if $opt_v;

    opendir(DIR ,$SOURCE) or elog_die("Failed to open $SOURCE: $!\n");

    while($file = readdir DIR ) {

        elog_notify("$SOURCE => $file") if $opt_v;

        move_files($SOURCE,$file) if ($file =~ /($DIR)/);

    }
    close DIR;


    return;
#}}}
}

sub move_files {
#{{{
    my $path   = shift;
    my $folder = shift;
    my $status = 1;
    my ($file,$new);


    opendir(FILES,"$path/$folder") or elog_die("Failed to open $path/$folder: $!\n");

    LOOP: foreach $file ( readdir FILES ) {

        if ( $file =~ /^\.\.?$/ ) {next LOOP;}

        if ($file =~ /$FF/) { 

            my $new = "$ARCHIVE/$2/$folder";

            elog_notify("\t$2 ($folder) [$file => $new]") if $opt_v;

            next LOOP if $opt_n;

            elog_notify("mkpath($new)") if ($opt_v and ! -d "$new/$file");

            eval { mkpath($new) } unless -d $new ;

            elog_die("Couldn't create $new: $@") if $@;

            elog_complain("ERROR: $new/$file exists in archive.") if -f "$new/$file";

            next LOOP if -f "$new/$file";

            elog_notify("copy $file -> $new") if $opt_v;

            copy("$path/$folder/$file","$new/$file");

            elog_die("Can't copy file $file to $new") unless -f "$new/$file"; 

            elog_notify("Removing original file $file") if ($opt_v and $opt_d);

            unlink "$path/$folder/$file" if $opt_d;

            elog_complain("ERROR: Can't remove file $path/$folder/$file: $!") if (-f "$path/$folder/$file" and $opt_d); 

        }
    }

    close FILES;

    return;
#}}}
}
    
