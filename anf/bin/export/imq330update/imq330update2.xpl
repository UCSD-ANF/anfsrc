use warnings;
use strict;
use Pod::Usage;
use Datascope;
use Getopt::Long;
use POSIX;
use File::Basename;
use Intermapper::HTTPClient;
use nagios_antelope_utils qw(&print_version);
use Data::Dumper;

our($params, $imhttp, $quit);

# Constants
our $AUTHOR = "Geoff Davis";
our $VERSION = '0.1';
our $PROGNAME = basename ($0);

# Defaults
our $PFNAME = $PROGNAME;
our $PF_REVISION_TIME = 1245573334;

our $import_file = "/tmp/import.tab";

MAIN:
{
    # Set signals to call &sig_handle
    $SIG{INT} = $SIG{TERM} = $SIG{HUP} = $SIG{KILL} = \&sig_handle;

    # Start log
    elog_init($0, @ARGV);

    # Check args and load parameters
    init();

    elog_notify("Starting $PROGNAME.");
    loop();
}

sub init{
    my ($opt_version, $opt_help, $opt_pf);
    Getopt::Long::Configure("bundling");
    GetOptions(
        "V" => \$opt_version, "version" => \$opt_version,
        "h" => \$opt_help, "help" => \$opt_help,
        "f=s" => \$opt_pf, "pf=s" => \$opt_pf,
    ) || pod2usage(-verbose => 0, -exitval => 1);

    if ($opt_version) {
        print_version($VERSION, $AUTHOR);
        exit 0;
    }

    $PFNAME = $opt_pf if $opt_pf;

    if ($opt_help) {
        pod2usage({-exitval => 0, -verbose => 2, -input => \*DATA});
    }

    # Load parameter file
    pfrequire($PFNAME, $PF_REVISION_TIME);
    $params = pfget($PFNAME, "");

    $imhttp = new Intermapper::HTTPClient(
        $params->{imhttp_host},
        $params->{imhttp_proto},
        $params->{imhttp_port},
        $params->{imhttp_username},
        $params->{imhttp_password},
    );
}

# Loop routine: deletes, add,s and updates stations in Intermapper.
# Subroutine never exits unless the process is signaled.
sub loop {

    until($quit) {
        elog_debug("Starting loop");
        # Do update
        process();

        # sleep until next call
        elog_debug("Sleeping for ".$params->{delay}." seconds");
        sleep $params->{delay};
    }
    elog_notify("$PROGNAME stopped.");

}

# Trap signals
sub sig_handle {
    $quit = 1;
    elog_notify("Received signal, stopping $PROGNAME...");
}

# Handle the actual processing of Intermapper data
sub process {
    my @export_fields = qw( mappath id name address latitude
        longitude comment shape);
    elog_notify("Getting export of Intermapper data...");
    my $export_data_ref = intermapper_export(@export_fields);
    unless ($export_data_ref) {
        elog_complain("Couldn't get export data from Intermapper server.");
        elog_complain("No updates will take place.");
        return 1;
    }

    elog_notify(
        sprintf(
            "Export complete with %d lines retrieved.",
            scalar(@{$export_data_ref})
        )
    );

    elog_notify(sprintf("Processing Intermapper export data for map \"%s\"...",
            $params->{mappath}));
    my $im_records = process_export_data($export_data_ref, @export_fields);
    elog_notify("Processing complete.");
    print Dumper($im_records);

    elog_notify(0, "Querying db ", $params->{db}, " for station data...");
    #($decert_records,$certcom_records) = db_query();
    my $current_stations_ref = db_query();
    elog_notify("Query complete");
    #print Dumper($current_stations_ref);

    elog_notify("checking for stations to delete from Intermapper...");
    delete_stations($im_records, $current_stations_ref);
}

sub intermapper_export {
    my @export_fields = @_;

    my $export_table = 'devices';
    my $export_format = 'tab';
    my ($retval,@output) = $imhttp->export_data(
        $export_format,
        $export_table,
        \@export_fields,
    );

    #if ($retval > 0) {
    if ($retval != $Intermapper::HTTPClient::IM_OK) {
        elog_complain($output[0]);
        elog_debug("Intermapper return value: $retval");
        return;
    }
    else {
        elog_debug("Intermapper return value: $retval");
        return \@output;
    }
}

# process the data from the intermapper_export function
# NOTE: assumes that the first field is always 'mappath'
# NOTE: requires that name is one of the fields
# NOTE: field names are downcased for the purposes of the hash.
# returns a hash, keyed by the name field.
sub process_export_data {

    my ($export_data_ref, @fields) = @_;
    my @lcfields = map {lc($_)}@fields;
    my %im_records;

    elog_debug("got fields: ".join(" ", @fields));

    unless (lc($fields[0]) eq 'mappath') {
        elog_complain("process_export_data - first field must be mappath");
        return -1;
    }

    unless (grep {$_ eq 'name'} @lcfields) {
        elog_complain("name must be one of the fields");
        return -1;
    }

    foreach my $record(@{$export_data_ref}) {
        if (index($record, $params->{mappath} . "\t") == 0) {
            my @vals=split(/\t/, $record);
            my %subhash;
            # merge two @ARRAYS into a %HASH using hash slices
            # http://www.perlmonks.org/?node_id=4402
            @subhash{@lcfields} = @vals;
            my $name = $subhash{name};
            $im_records{$name} = \%subhash;
        }
        else {
            next;
        }
    }
    elog_debug(sprintf("Kept %d of %d records", scalar(keys %im_records),
            scalar(@{$export_data_ref})));
    return \%im_records;

}

# Returns a reference to a hash, keyed by snet_sta
sub db_query {
    my @dbfields = qw(vnet snet sta commtype provider lat lon inp ssident);

    my %active_records; # we return this if everything goes well

    my @db = dbopen($params->{db}, 'r');
    my @dbdep = dblookup(@db, 0, 'deployment', 0, 0);
    my @dbcomm = dblookup(@db, 0, 'comm', 0, 0);
    my @dbsite = dblookup(@db, 0, 'site', 0, 0);

    # Get all currently active stations
    my $query=sprintf(
        'snet =~ /%s/ && ' .
        '(cert_time != NULL && cert_time <= now()) &&' .
        '(decert_time == NULL || decert_time >= now())',
        $params->{network},
    );
    my @cert = dbsubset(@dbdep, $query);
    my @certsite = dbjoin(@cert,@dbsite);
    my @certsitecomm = dbjoin(@certsite,@dbcomm);

    # Keep only current comms table entries
    $query = 'comm.endtime == NULL || comm.endtime >= now()';
    my @active = dbsubset(@certsitecomm, $query);

    my $nrec = dbquery(@active, "dbRECORD_COUNT");
    elog_notify("Found $nrec active stations in deployments table");

    # Now get the staq330 table, find only the active entries
    my @dbstaq330 = dblookup(@db, 0, 'staq330', 0, 0);
    $query  = 'time != NULL && time <= now() && ';
    $query .= '(endtime == NULL || endtime >= now())';
    my @curr_q330 = dbsubset(@dbstaq330, $query);
    my @active_q330 = dbjoin(@active, @curr_q330, 'sta'); #must join on sta

    $nrec = dbquery(@active_q330, "dbRECORD_COUNT");
    elog_notify("Found $nrec active stations joined to staq330");
    for ($active_q330[3] = 0; $active_q330[3] < $nrec; $active_q330[3]++) {
        my %vals;
        my @vals_a = dbgetv(@active_q330,@dbfields);
        # hash slice trick to merge two arrays
        @vals{@dbfields}=@vals_a;
        my $snet_sta = join('_', $vals{snet}, $vals{sta});
        if (defined($active_records{$snet_sta})) {
            elog_complain(
                "Problem with dbmaster: duplicate entries for $snet_sta"
            );
        }
        $active_records{$snet_sta}=\%vals;

    }
    dbclose(@db);

    elog_debug(0,
        "returning hash with ", scalar(keys(%active_records)), " elements");
    return \%active_records;
}

sub delete_stations {
    my ($im_stations,$active_stations) = @_;

    my @keysim = keys(%{$im_stations});
    my @keysactive = keys(%{$active_stations});
    elog_debug(0, "IM: " . scalar(@keysim) . " ACTIVE: " . scalar(@keysactive));
    my @delete = grep { my $x = $_; not grep { $x eq $_ } @keysactive } @keysim;
    elog_debug(0, "Delete: ", scalar(@delete));
    #print Dumper(\@delete);
}

__END__
=head1 NAME

imq330update - Update Q330 IP addresses and station attributes in Intermapper

=head1 SYNOPSIS

F<imq330update> [-v] [-d] [-f <parameterfile>]

=head1 OPTIONS

=over 8

=item B<-f (--pf)>

Specify the Antelope parameter file to use. Defaults to imq330update.pf

=item B<-h (--help)>

Print a help message and exit

=item B<-V (--version)>

Print the version of this script

=back

=head1 DESCRIPTION

B<IMq330update> is designed to read the q330comms table of an Antelope DBMaster and update a map in Intermapper with station details. It adds and updates changing Q330 IP addresses and station attributes, and will automatically delete decertified stations that are listed in the deployments table.

=head1 EXAMPLES

Normal usage in an Antelope real-time system:

 IMq330update

=head1 BUGS AND CAVEATS

Does not currently handle changing Comm type or Comm provider for a station.

Does not use the HTTP API for interacting with Intermapper

=head1 AUTHOR

Originally written by Brian Battistuz as part of the Transportable Array
project.

Complete re-write by Geoff Davis to handle more networks, use the Intermapper
HTTP interfaces, and only use the dbmaster instead of the orb.

=head1 SUPPORT

Contributed: NO BRTT support -- please contact author.

=cut

# vim:ft=perl
