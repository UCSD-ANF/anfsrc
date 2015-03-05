use lib "$ENV{ANTELOPE}/data/perl" ;

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

elog_notify("\nStarting execution on   $host   $date\n\n") ;

if ( ! getopts('nvrp:') || @ARGV != 2 ) {
    die ( "Usage: $pgm [-v] [-r] [-p pf] database output_dir\n" ) ;
}

#  Get options and parameters
$database = File::Spec->rel2abs($ARGV[0]) ;
$archive = File::Spec->rel2abs($ARGV[1]) ;

#Get parameters
%pf = getparam(  $opt_p || "calib_images.pf"  );

if( $opt_v ) {
    elog_notify("database: [$database]") ;
    elog_notify("archive:  [$archive]") ;
    elog_notify("Variables:") ;
    elog_notify("\tconvert_cmd = $pf{convert_cmd}   ") ;
    elog_notify("\timg_format  = $pf{img_format}   ") ;
}

# Check Dirs
elog_die("Problems looking for directory $archive: $!") unless -d $archive ;


# Open a virtual display
$cmd = "Xvfb :$$ -fbdir /var/tmp -screen :$$ 1600x1200x24" ;
elog_notify( "\t[$cmd]" ) if $opt_v ;
my $vpid = open(my $pipe, "$cmd |") or elog_die("Cannot run [$cmd]") ;
elog_notify("Set display to :$$") if $opt_v ;
$ENV{DISPLAY} = ":$$" ;



elog_notify( "Open database $database" ) if $opt_v ;
@db = dbopen( $database, 'r+' ) or elog_die("Problem opending db $database") ;
@dbcalplot = dblookup( @db, 0, "calplot", 0, 0 ) ;

$records = dbquery(@dbcalplot,"dbRECORD_COUNT") ;
# Review each entry on db
for ($row=0; $row < $records ; $row++ ) {
    elog_notify("Entry [$row] of [$records]") if $opt_v ;
    $dbcalplot[3] = $row ;
    ( $sta, $chan, $time) = dbgetv( @dbcalplot, "sta", "chan", "time") ;

    $pdfdir = File::Spec->canonpath( "$archive/$sta" ) ;
    makedir( $pdfdir) unless -e $pdfdir ;

    $file = "$sta\_$chan\_" ;
    $file .= epoch2str($time,"%Y-%j-%H-%M") ;
    $file .= ".$pf{img_format}" ;

    $fullpath = File::Spec->canonpath( "$pdfdir/$file" ) ;

    if (-f $fullpath and ! $opt_r) {
        elog_notify( "\t$fullpath already exists" ) if $opt_v ;
    } else {
        elog_complain( "\t$fullpath missing" ) if $opt_v ;

        ##  build plots
        $cmd  = "displayscal -dumpandexit $pdfdir/temp.ps $database $row" ;
        elog_notify( "\t[$cmd]" );
        next unless run_cmd( $cmd ) ;

        ##  convert plots
        $cmd  = "$pf{convert_cmd} $pdfdir/temp.ps $fullpath" ;
        elog_notify( "\t[$cmd]" );
        elog_die("Cannot run [$cmd]" ) unless run_cmd( $cmd ) ;

        unlink "$pdfdir/temp.ps" or elog_die("Cannot unlink $pdfdir/temp.ps") ;

        elog_notify( "\tNew file $fullpath" ) ;
    }

}

dbclose(@db) ;

elog_notify("Close virtual display $id on pid: $vpid") ;
kill(9, $vpid) or elog_die("Cannot close virtual display $id on pid: $vpid") ;

######################$
#  Read PF file      #$
######################$
sub getparam {
    my ($PF) = @_ ;
    my ($subject) ;
    my (%pf) ;

    foreach my $value (qw/img_format convert_cmd/){
        $pf{$value} = pfget($PF,$value) ;
        elog_die("Missing value for $value in PF:$PF") unless defined $pf{$value} ;
    }

    return (%pf) ;
}

exit(1) ;
