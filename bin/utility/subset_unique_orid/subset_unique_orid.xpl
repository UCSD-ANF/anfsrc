# 

#{{{
use Datascope ;
use Getopt::Std;
use Pod::Usage;

#}}}

######################
#  Program setup     #
######################
#{{{

    elog_init($0, @ARGV);
    $cmd = "$0 @ARGV" ;
    $start = now();

    if ( ! &getopts('s:') || @ARGV < 1 || @ARGV > 2 ){
        pod2usage({-exitval => 2, -verbose => 2});
    }

    elog_notify('');
    elog_notify( $cmd );
    elog_notify ("Starting execution at ".strydtime(now()));
    elog_notify('');
    elog_notify('');

    $opt_s ||= 'ANF|UCSD';
    $db_in = @ARGV[0];
    $db_out = @ARGV[1];

    $db_out ||= "${db_in}subset";

    elog_die('Output database already exists') if -f "${db_out}.origin";

    elog_notify("IN: $db_in ");
    elog_notify("OUT: $db_out ");
    elog_notify("SUBSET: $opt_s ");

#}}}

#{{{ MAIN
    
    #
    # This part runs the data archival process
    #
    get_events();

    $end = now();
    $run_time = $end - $start;
    $run_time_str = strtdelta($run_time);
    $start = strydtime($start);
    $end = strydtime($end);

    elog_notify('');
    elog_notify("Start: $start End: $end");
    elog_notify("Runtime: $run_time_str");
    sendmail("Done $0 on $host ", $opt_m) if $opt_m; 
    elog_notify('');
#}}}

sub get_events { 
#{{{
    my %events;
    my (@db_in,@db_sub,@db_out);
    my ($orid,$evid,$auth);
    my ($nrecords);

    #
    # input DB
    #
    @db = dbopen($db_in,'r+') or elog_die("Cannot open $db_in");
    @db = dblookup(@db,"","origin","","") or elog_die("Can't open $db_in.origin");

    #
    # output DB
    #
    @out = dbopen($db_out,'r+') or elog_die("Cannot open $db_out");
    @out = dblookup(@out,"","origin","","") or elog_die("Can't open $db_out.origin");

    #
    # Get all events from input db
    #
    $nrecords =  dbquery(@db, "dbRECORD_COUNT") ;
    for ($db[3]=0; $db[3] < $nrecords; $db[3]++) {

        $events{ dbgetv(@db,'evid') } = ();

    }

    #
    # Loop over each event
    #
    foreach (sort keys %events) {

        @db_sub = dbsubset(@db, "evid =~ /$_/");

        #
        # Subset for events with only one orid
        #
        if ( dbquery(@db_sub, "dbRECORD_COUNT") == 1) {

            $db_sub[3]=0;
            ($time, $lat, $lon, $depth, $ndef, $nass, $orid, $evid, $commid, $grn, $auth) = 
                dbgetv(@db_sub,qw/time lat lon depth ndef nass orid evid commid grn auth/);

            #
            # Match regex
            #
            next unless $auth =~ /$opt_s/;
            print "$orid, $evid, $auth =~ /$opt_s/\n";

            #
            # Add to new database
            #
            dbaddv(@out,"time",$time,"lat",$lat,"lon",$lon,"depth",$depth,"ndef",$ndef,"nass",$nass,"orid",$orid,
                    "evid",$evid,"commid",$commid,"grn",$grn,"auth",$auth);
        }

    }
#}}}
}

__END__

=pod

=head1 NAME

subset_unique_orid- get events with unique orids that match a subset for AUTH

=head1 SYNOPSIS

subset_unique_orid [-s] input_db [out_db]

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-s> 

Subset for this string in the AUTH field. Defaults to 'ANF|UCSD'.

=back

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).


