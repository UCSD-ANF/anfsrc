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

    if ( ! &getopts('s:v') || @ARGV < 1 || @ARGV > 2 ){
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

    $db_out ||= "${db_in}_subset";

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
    my ($r, $nrecords);

    my ($lat,$lon,$depth,$time,$orid,$evid,$jdate,
        $nass,$ndef,$ndp,$grn,$srn,$etype,$review,
        $depdp,$dtype,$mb,$mbid, $ms,$msid,$ml,$mlid,
        $algorithm,$auth,$commid,$lddate);

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
    elog_notify("$nrecords records in $db_in") if $opt_v;
    for ($db[3]=0; $db[3] < $nrecords; $db[3]++) {

        $e = dbgetv(@db,'evid');
        elog_notify("$e") if $opt_v;
        $events{ $e } = ();

    }

    #
    # Loop over each event
    #
    foreach (sort keys %events) {

        elog_notify("$_") if $opt_v;
        @db_sub = dbsubset(@db, "evid =~ /$_/");


        $r = dbquery(@db_sub, "dbRECORD_COUNT");
        elog_notify("\t$r records") if $opt_v;

        #
        # Subset for events with only one orid
        #
        if ( $r == 1) {

            elog_notify("\tGot one auth only for event $_.") if $opt_v;

            #
            # Get data
            #
            $db_sub[3]=0;
            ($lat,$lon,$depth,$time,$orid,$evid,$jdate,
                $nass,$ndef,$ndp,$grn,$srn,$etype,$review,
                $depdp,$dtype,$mb,$mbid, $ms,$msid,$ml,$mlid,
                $algorithm,$auth,$commid,$lddate) = dbgetv(@db_sub, 
                qw/lat lon depth time orid evid jdate nass ndef 
                ndp grn srn etype review depdp dtype mb mbid 
                ms msid ml mlid algorithm auth commid lddate/);

            elog_notify("\t $lat,$lon,$depth,$time,$orid,$evid,$jdate,$nass,$ndef,$ndp,$grn,$srn,$etype,$review,$depdp,$dtype,$mb,$mbid, $ms,$msid,$ml,$mlid,$algorithm,$auth,$commid,$lddate") if $opt_v;

            #
            # Match regex
            #
            if ( $opt_v ) {
                elog_notify("\tNO MATCHED ON: $auth =~ /$opt_s/") unless $auth =~ /$opt_s/;
            }
            next unless $auth =~ /$opt_s/;
            elog_notify("\t$orid, $evid, $auth =~ /$opt_s/");

            #
            # Add to new database
            #
            dbaddv(@out,"lat",$lat,"lon",$lon,"depth",$depth,"time",$time,"orid",$orid,"evid",$evid,"jdate",$jdate,
                    "nass",$nass,"ndef",$ndef,"ndp",$ndp, "grn", $grn, "srn",$srn, "etype",$etype, "review", $review, 
                    "depdp",$depdp, "dtype",$dtype, "mb",$mb,"mbid",$mbid,"ms",$ms,"msid",$msid,"ml",$ml,"mlid",$mlid,
                    "algorithm",$algorithm,"auth",$auth,"commid",$commid,"lddate",$lddate);
           }

    }
#}}}
}

__END__

=pod

=head1 NAME

subset_unique_orid- get events with unique orids that match a subset for AUTH

=head1 SYNOPSIS

subset_unique_orid [-s] [-v] input_db [out_db]

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-v> 

Run in verbose or debug mode.

=item B<-s> 

Subset for this string in the AUTH field. Defaults to 'ANF|UCSD'.

=back

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).


