use lib "$ENV{ANTELOPE}/data/perl" ;

#use strict;
#use warnings;
use File::Find qw(finddepth);

use File::Spec ;
use Getopt::Std ;
use Datascope ;
use archive ;
use sysinfo ;
use utilfunct ;

my $pgm = $0 ;

$pgm =~ s".*/"" ;
$date= localtime() ;
$host = my_hostname();

elog_init($pgm, @ARGV) ;


if ( ! getopts('nvr') || @ARGV != 1 ) {
    die ( "Usage: $pgm [-v] [-r] [-n] dir\n" ) ;
}

elog_notify("\nStarting execution on   $host   $date\n\n") if $opt_v  ;

#  Get options and parameters
$archive = File::Spec->rel2abs($ARGV[0]) ;

if( $opt_v ) {
    elog_notify("archive:  [$archive]") ;
    elog_notify("options:") ;
    elog_notify("\t-n: $opt_n") ;
    elog_notify("\t-r: $opt_r") ;
    elog_notify("\t-v: $opt_v") ;
}

# Check Dirs
elog_die("Problems looking for directory $archive: $!") unless -d $archive ;


# Open a virtual display
$cmd = "Xvfb :$$ -fbdir /var/tmp -screen :$$ 1600x1200x24" ;
elog_notify( "\t[$cmd]" ) if $opt_v ;
my $vpid = open(my $pipe, "$cmd |") or elog_die("Cannot run [$cmd]") ;
elog_notify("Set display to :$$") if $opt_v ;
$ENV{DISPLAY} = ":$$" ;

my @files;
finddepth(sub {
    return if($_ eq '.' || $_ eq '..');
    return unless $_ =~ m/.*\.pdf/;
    push @files, $File::Find::name;
}, $archive );

# Review each entry on db
foreach my $file ( @files ) {
    #$fullpath = File::Spec->canonpath( "$archive/$file" ) ;
    $fullpath = File::Spec->canonpath( $file ) ;
    elog_notify("[$fullpath]") if $opt_v ;

    $fullpath =~ m/^(.*)(\.pdf)$/;

    my $pngfile = "$1.png";

    elog_notify("PNG version: [$pngfile]") if $opt_v ;

    # remove the png version if running with -r flag.
    if ( -f $pngfile and $opt_r ) {
        elog_notify( "\t$pngfile already exists. REMOVE FIRST." ) if $opt_v ;
        # not if NULL RUN
        if (not $opt_n) {
            unlink $pngfile or elog_die("Cannot unlink $pngfile") ;
        } else {
            elog_notify( "- AVOID, NULL RUN -" );
        }
    }

    if ( -f $pngfile ) {
        elog_notify( "\t$pngfile already exists" ) if $opt_v ;
    } else {
        elog_complain( "\t$pngfile missing" ) if $opt_v ;


        ##  convert plots
        $cmd  = "convert -antialias -density 130 $fullpath $pngfile" ;
        elog_notify( "\t[$cmd]" ) if $opt_v ;

        if ($opt_n) {
            elog_notify( "- AVOID, NULL RUN -" );
        } else {
            elog_die("Cannot run [$cmd]" ) unless run_cmd( $cmd ) ;

            if ( -f $pngfile ) {
                elog_notify( "\tNew file $fullpath" ) if $opt_v  ;
            } else {
                elog_complain( "\tMISSING: $pngfile" ) ;
            }
        }
    }

}

elog_notify("Done.") if $opt_v ;

elog_notify("Close virtual display $id on pid: $vpid") if $opt_v  ;
kill(9, $vpid) or elog_die("Cannot close virtual display $id on pid: $vpid") ;

exit(1) ;
