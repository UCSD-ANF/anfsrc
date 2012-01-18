#
#   baler44_uploaded: script to migrate data from baler44 files uploaded to ANF
#   author: Juan C. Reyes
#   email:  reyes@ucsd.edu
#   No BRTT support
#

use archive;
use sysinfo;
use Datascope;
use Pod::Usage "pod2usage";
use Getopt::Std "getopts";
use File::Copy;


#
#  Program setup
#
#{{{
    $start = now();
    $parent = $$;

    pod2usage({-exitval => 2, -verbose => 2}) if ( ! getopts('vnhm:') || @ARGV != 2 );

    pod2usage({-exitval => 2, -verbose => 2}) if $opt_h;

    savemail() if $opt_m; 

    elog_init($0,@ARGV);

    elog_notify('');
    elog_notify("$0 @ARGV");
    elog_notify("Starting execution at ".strydtime($start)." on ".my_hostname());
    elog_notify('');
    elog_notify('');

    $source = $ARGV[0];
    $target = $ARGV[1];

    elogdie("[$ARGV[0]] not a folder") unless -d $source;
    elogdie("[$ARGV[1]] not a folder") unless -d $target;

    #
    # Read source directory
    #
    opendir $temp, $source or elogdie("Couldn't open dir '$source': $!");
    foreach (readdir $temp){
        next if /^\.\.?$/;
        push @stations,$_;
    }
    closedir $temp;
    if ( $opt_v ) {
        elog_notify("Folders in source directory: [$source]");
        if (scalar @stations > 0 ) {
            elog_notify("\t$source/$_") foreach sort @stations;
        } else {
            elog_notify("\t*** EMPTY ***");
        }
    }
    unless (scalar @stations > 0 ){
        elog_notify("Source[$source] folder is empty.");
        elog_notify("Nothing to do!");
        sendmail("baler44_uploaded: No files",$opt_m) if $opt_m;
        exit 0;
    }

    #
    # Read target directory
    #
    opendir $temp, $target or elogdie("Couldn't open dir '$target': $!");
    foreach (readdir $temp){
        next if /^\.\.?$/;
        push @archives,$_;
    }
    closedir $temp;
    if ( $opt_v ) {
        elog_notify("Folders in target directory: [$target]");
        elog_notify("\t$target/$_") foreach sort @archives;
    }
    elogdie("[$target] folder is empty!") unless scalar @archives > 0;

#}}}

#
#  Main
#
#{{{

    foreach my $station (sort @stations) {
        elog_notify("");
        elog_notify("Working with station: [$station]");

        #
        # Verify we have a folder
        #
        my $source_sta = "$source/$station";
        unless ( -d $source_sta ) {
            elog_complain("");
            elog_complain("ERROR: source [$source_sta] is not a folder.");
            elog_complain("");
            next;
        }

        #
        # Verify station source folder
        #
        opendir $temp, $source_sta or elogdie("Cannot open dir [$source_sta]: $!");
        foreach (readdir $temp){
            next if /^\.\.?$/;
            push @files,$_;
        }
        closedir $temp;

        unless ( scalar @files > 0 ) {
            elog_complain("");
            elog_complain("Folder for station [$station] is empty!.");
            rm_dir($source_sta) unless $opt_n;
            elog_complain("");
            next;
        }

        #
        # Verify station target folder
        #
        my $target_sta = "$target/$station";
        my $target_md5 = "$target_sta/md5";
        unless ( -d $target_sta ) {
            elog_complain("");
            elog_complain("ERROR: Cannot find [$target_sta].");
            elog_complain("Create folder [$target_sta]");
            elog_complain("");
            unless ( $opt_n ) {
                mkdir $target_sta or elog_complain("Cannot create folder [$target_sta]: $!");
                elog_complain("No target directory [$target_sta]. Avoid station...") unless -d $target_sta;
                next unless -d $target_sta;
            }
        }

        #
        # Verify station md5 folder
        #
        unless ( -d $target_md5 ) {
            elog_complain("");
            elog_complain("ERROR: Cannot find [$target_md5].");
            elog_complain("Create folder [$target_md5]");
            elog_complain("");
            unless ( $opt_n ) {
                mkdir $target_md5 or elog_complain("Cannot create folder [$target_md5]: $!");
                elog_complain("No target directory [$target_md5]. Avoid station...") unless -d $target_md5;
                next unless -d $target_md5;
            }
        }

        #
        # Move md5 files
        #
        opendir $temp, $source_sta or elogdie("Cannot open dir [$source_sta]: $!");
        foreach (readdir $temp){
            next if /^\.\.?$/;
            if (/.*\.md5/){
                elog_notify("mv $source_sta/$_ $target_md5/$_");
                unless ( $opt_n ) {
                    move("$source_sta/$_","$target_md5/$_")or elogdie("Cannot mv [$_ -> $target_md5]: $!");
                }
                elog_complain("ERROR: Cannot verify [$target_md5/$_]") unless -f "$target_md5/$_";
                elog_notify("[$target_md5/$_] verified") if $opt_v and -f "$target_md5/$_";
            } else {
                elog_notify("mv $source_sta/$_ $target_sta/$_");
                unless ( $opt_n ) {
                    move("$source_sta/$_","$target_sta/$_") or elogdie("Cannot mv [$_ -> $target_sta]: $!");
                }
                elog_complain("ERROR: Cannot verify [$target_sta/$_]") unless -f "$target_sta/$_";
                elog_notify("[$target_sta/$_] verified") if $opt_v and -f "$target_sta/$_";
            }
        }
        closedir $temp;

        #
        # Remove source folder
        #
        elog_notify("Done with folder [$station]") if $opt_v;
        elog_notify("Remove source directory [$source_sta]") if $opt_v;
        rm_dir($source_sta) unless $opt_n;
    }

    $end = now();
    $run_time_str = strtdelta($end - $start);
    $start = strydtime($start);
    $end = strydtime($end);

    if ( $opt_v ) {
        elog_notify("\n\n----------------- END -----------------\n\n");
        elog_notify("Start: $start End: $end");
        elog_notify("Runtime: $run_time_str");
    }

    sendmail("baler44_uploaded: Successful upload",$opt_m) if $opt_m;

    exit 0;

#}}}

sub rm_dir {
#{{{
    my $dir = shift;

    elog_notify("") if $opt_v;
    elog_notify("Remove: $dir") if $opt_v;
    rmdir $dir or elog_complain("Cannot remove directory [$dir]: $!");
    elog_notify("") if $opt_v;

#}}}
}

sub elogdie {
#{{{
    my $msg = shift;

    elog_complain("ERROR: Call to elog_die().");
    elog_complain($msg);

    sendmail("baler44_uploaded: ERROR",$opt_m) if $opt_m;

    elog_die($msg);
#}}}
}

__END__
#{{{
=pod

=head1 NAME

baler44_uploaded - automatic uplaod of Baler44 files

=head1 SYNOPSIS

baler44_uploaded [-h] [-n] [-v] [-m email] source_dir target_dir 

=head1 SUPORT

No BRTT support == contact Juan Reyes <reyes@ucsd.edu>

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h> 

Produce this documentation

=item B<-n> 

Test  mode/dry  run.  Does not delete, copy or move  any file or folder.

=item B<-v> 

Produce logs for children

=item B<-m emails> 

List of emails to send logs.

=back

=head1 DESCRIPTION

baler44_uploaded  migrates  files  from the remote uploads to permanent
archives.  Desing to run out of crontab and email results.  The  script
will  lList  files in the source directory and migrates the data to the
target directory. The source directory gets  data  from  the  automatic
uplaod  GUI  run  by AOF (Allan) and a PHP script at anf.ucsd.edu saves
the data in a temp folder.

The script will strat reading the source directory and moving each file
into  its  station  directory on the target directory. If the folder is
missing the script will create one. If the folder for the checksums  is
missing  the scirpt will create a folder "md5" inside the target direc-
tory.

The assumptions of the program are that:

    The source directory is one level deep and include folders  with
    the names of the stations.

    Every file for the station is in the station folder. No matching
    for station name is performed at this time.  That  was  done  at
    uplaod time.

=head1 ENVIRONMENT

needs to have sourced $ANTELOPE/setup.csh.

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).

=cut
#}}}
