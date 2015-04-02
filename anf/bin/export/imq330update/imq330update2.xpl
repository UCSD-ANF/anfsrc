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
use URI::Encode qw(uri_encode uri_decode);

our($params, $imhttp, $quit);

# Constants
our $AUTHOR = "Geoff Davis";
our $VERSION = '0.1';
our $PROGNAME = basename ($0);
our $EXIT_CODE_FAILURE = 1;
our $EXIT_CODE_SUCCESS = 0;
our %ESCAPES = (
    n => "\n",
    t => "\t",
);

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

# interpolate known variables inside of a string
# from http://www.perlmonks.org/?node_id=452647
sub interpolate {
    local *_ = \$_[0]; # Alias $_ to $_[0].
    my $symtab = $_[1];

    my $interpolated = '';

    for (;;) {
        if (/\G \$(\w+) /gcsx || /\G \${(\w+)} /gcsx) {
            if(!exists($symtab->{$1})) {
                $interpolated .= "[unknown symbol \$$1]";
            } elsif (!defined($symtab->{$1})) {
                $interpolated .= "[undefined symbol \$$1]";
            } else {
                $interpolated .= $symtab->{$1};
            }
            next;
        }

        if (/\G \\(.) /gcsx) {
            $interpolated .= exists($ESCAPES{$1}) ? $ESCAPES{$1} : $1;
            next;
        }

        /\G
            (
                .           # Catchall.

                (?:         # These four lines are optional.
                    (?!\\)  # They are here to speed things up
                    (?!\$)  # by avoiding adding individual
                .)*         # characters to the $interpolated.
            )
        /gcsx && do { $interpolated .= $1; next; };

        last;
    }

    return $interpolated;
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
# NOTE: was the original inner part of the loop sub
sub process {
    my @export_fields = qw( mappath id name address latitude
        longitude comment shape);
    elog_notify("Getting export of Intermapper data...");
    my $export_data_ref = intermapper_export(@export_fields);
    unless ($export_data_ref) {
        elog_complain("Couldn't get export data from Intermapper server.");
        elog_complain("No updates will take place.");
        return $EXIT_CODE_FAILURE;
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
    #print Dumper($im_records);

    elog_notify(0, "Querying db ", $params->{db}, " for station data...");
    my $current_stations_ref = db_query();
    elog_notify("Query complete");
    #print Dumper($current_stations_ref);

    elog_notify("Checking for stations to delete from Intermapper...");
    delete_stations($im_records, $current_stations_ref);

    elog_notify("Checking for stations to insert into Intermapper...");
    insert_stations($im_records, $current_stations_ref);

    return $EXIT_CODE_SUCCESS;
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

# Process the data from the intermapper_export function
# Returns a hash, keyed by the name field.
#
# NOTE: assumes that the first field is always 'mappath'
# NOTE: requires that name is one of the fields
# NOTE: field names are downcased for the purposes of the hash.
sub process_export_data {

    my ($export_data_ref, @fields) = @_;
    my @lcfields = map {lc($_)}@fields;
    my %im_records;

    elog_debug("process_export_data fields: " . join(" ", @fields));

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

    # Get only active entries in the site table (needed for CEUSN)
    $query = '(ondate != NULL && ondate <= now()) && (offdate == NULL || offdate >= now())';
    my @siteactive = dbsubset(@dbsite, $query);

    # Join certified stations to active sites
    my @certsite = dbjoin(@cert,@siteactive);
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

        # hash slice trick to "zip" (merge) two arrays into a hash
        # http://www.perlmonks.org/?node_id=4402
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
    # Use array slices to determine what items in keysim are not in keysactive
    my @keysdelete = grep { my $x = $_; not grep { $x eq $_ } @keysactive } @keysim;
    elog_debug(
        0, "Delete ", scalar(@keysdelete), " items: ", join(" ", @keysdelete)
    );

    my %deletes;
    for my $key (@keysdelete) {
        $deletes{$key}=$im_stations->{$key};
    }

    return delete_from_im(\%deletes);
}

sub delete_from_im {
    my $ref = shift;
    my %deletes = %{$ref};

    unless (scalar(keys(%deletes)) == 0) {
        my $retval = create_import_file("delete", $ref);
        if (defined($retval)) {
            $retval = intermapper_import();
            if ($retval == $Intermapper::HTTPClient::IM_OK) {
                elog_notify("Delete of station(s) confirmed in Intermapper");
                return 1;
            } else {
                elog_alert("Delete of station(s) failed in Intermapper");
                return -1;
            }
        }
        else {
            elog_alert("Errors writing import file");
            return -1;
        }
    }

    return 1;
}

sub insert_stations {
    my ($im_stations,$active_stations) = @_;

    my @keysim = keys(%{$im_stations});
    my @keysactive = keys(%{$active_stations});
    elog_debug(0, "IM: " . scalar(@keysim) . " ACTIVE: " . scalar(@keysactive));
    # Use array slices to determine what items in keysactive are not in keysim
    my @keysinsert = grep { my $x = $_; not grep { $x eq $_ } @keysim } @keysactive;
    elog_debug(
        0, "Insert ", scalar(@keysinsert), " items: ", join(" ", @keysinsert)
    );

    my %inserts;
    for my $key(@keysinsert) {
        $inserts{$key}=$active_stations->{$key};
        my @inp_parts = split /:/, $inserts{$key}{inp};
        $inserts{$key}{'ip'}=$inp_parts[0] if defined $inp_parts[1];
        my $shape = get_shape(
            $inserts{$key}{commtype},
            $inserts{$key}{provider});
        $inserts{$key}{shape}=$shape;
    }

    return insert_into_im(\%inserts);
}

sub insert_into_im {
    my $ref = shift;
    my %inserts = %{$ref};

    unless(scalar(keys(%inserts)) == 0) {
        my $retval = create_import_file('insert', $ref);
        if (defined($retval)) {
            $retval = intermapper_import();
            if ($retval == $Intermapper::HTTPClient::IM_OK) {
                elog_notify("Insert of station(s) confirmed in Intermapper");
                return 1;
            } else {
                elog_alert("Insert of station(s) failed in Intermapper");
                return -1;
            }
        }
        else {
            elog_alert("Errors writing import file");
            return -1;
        }
    }

    return 1;
}

sub create_import_file {

    # Need symbolic references to expand variables in improbe string from pf file
    no strict 'refs';
    my ($directive,$ref) = @_;
    my $map      = $params->{mappath};
    my $probe    = $params->{probe};
    my $timeout  = $params->{timeout};
    my $mapas    = "END SYSTEM";
    my $resolve  = "NONE";
    my $labelpos = $params->{labelpos};
    my $labelvis = $params->{labelvis};

    # Set default values
    my $ipdefault      = "10.0.0.1";
    my $ssidentdefault = "Unknown datalogger serial";
    my $latdefault     = "90";
    my $londefault     = "0";


    # Create the import file
    my $fopen_res = open(IMPORTFILE, "> $import_file");
    unless ($fopen_res) {
        elog_complain("Couldn't open file $import_file for writing: $!");
        return;
    }

    if ($directive eq "insert") {
        my ($count) = 0;
        print IMPORTFILE "# format=tab table=devices fields=mappath,address,dnsname,probe,improbe,timeout,latitude,longitude,resolve,comment,labelposition,labelvisible,shape\n";
        foreach my $record (keys %{$ref}) {

            my ($ssident,$lat,$lon,$decert_time,$pollinterval,$improbe,
                $sta,$ip);

            $count++;
            elog_debug(0, "Generating import record for ", $record);
            elog_debug(Dumper($ref->{$record}));

            # If found a recent station record in q330comm, use it's values
            # Otherwise, set defaults
            if (defined($ref->{$record}{ip})) {
                $sta     = $record;
                $ip      = $ref->{$record}{ip};
                $ssident = $ref->{$record}{ssident};
                $lat     = $ref->{$record}{lat};
                $lon     = $ref->{$record}{lon};
            }
            elsif ($params->{plot_no_comms}) {
                $sta     = $record;
                $ip      = $ipdefault;
                $ssident = $ssidentdefault;
                $lat     = $latdefault;
                $lon     = $londefault;
                elog_notify("Inserting $sta with default parameters for ip, ssident, lat, and long");
            }
            else {
                #skip this record
                elog_notify("Skipping $sta due to lack of comms");
                next;
            }

            my $commtype = $ref->{$record}{commtype};
            my $provider = $ref->{$record}{provider};
            my $shape    = $ref->{$record}{shape};
            my $vnet     = $ref->{$record}{vnet};
            elog_notify("Inserting $sta with parameters $ip, $lat, $lon, $ssident, $shape");

            # URL encode spaces for improbe and add quotes because Intermapper
            # is really bad about handling parameters with spaces

            # Expand variables in improbe pf string
            # Should look like this:
            # improbe     improbe://${ip}/edu.ucsd.cmd.tastation?orb=${writeorb}&dlsta=${sta}&commtype=${commtype}&provider=${provider}
            #

            my $writeorb = $params->{writeorb}{default};
            if (defined($params->{writeorb}{$vnet})) {
                $writeorb = $params->{writeorb}{$vnet} ;
            }

            my %symtab = (
                ip  => $ip,
                sta => $sta,
                commtype => $ref->{$record}{commtype},
                provider => $ref->{$record}{provider},
                writeorb => $writeorb,
            );

            $improbe = $params->{improbe};
            $improbe = interpolate($improbe, \%symtab);
            $improbe = uri_encode($improbe);

            print IMPORTFILE "$map\t$ip\t$sta\t$probe\t$improbe\t$timeout\t$lat\t$lon\t$resolve\t$ssident\t$labelpos\t$labelvis\t$shape\n";
        }
        elog_notify("Intermapper import file $import_file updated with $count new record(s) for insertion");

    }
    elsif ($directive eq "update") {
        my ($count) = 0;
        print IMPORTFILE "# format=tab table=devices fields=mappath,address,dnsname,latitude,longitude,comment ";
        print IMPORTFILE "modify=address,latitude,longitude,comment match=mappath,dnsname\n";
        foreach my $record (keys %{$ref}) {
            $count++;
            my $sta =                  $record;
            my $ip =                   $ref->{$record}{address};
            my $ssident =          $ref->{$record}{ssident};
            my $lat =                  $ref->{$record}{lat};
            my $lon =                  $ref->{$record}{lon};
            #my $shape =               $ref->{$record}{shape};

            print IMPORTFILE "$map\t$ip\t$sta\t$lat\t$lon\t$ssident\n";
            elog_notify("Updating $sta with parameters $ip, $lat, $lon, $ssident");

        }
        elog_notify("Intermapper import file $import_file updated with $count record(s) to be updated");

    }
    elsif ($directive eq "delete") {
        my ($count) = 0;
        #print IMPORTFILE "# format=tab table=devices fields=mappath,dnsname delete=mappath,dnsname\n";
        print IMPORTFILE "# format=tab table=devices fields=mappath,dnsname,id delete=id\n";
        foreach my $record (keys %{$ref}) {
            $count++;
            my $sta =               $record;
            my $id  = $ref->{$record}{id};
            #my $decert_time = $ref->{$record}{decert_time};

            my $line = "$map\t$sta\t$id\n";
            elog_debug(0, "Delete line: ", $line);
            print IMPORTFILE $line;
            #elog_notify("Deleting $sta. Decertfication time is $decert_time");

        }
        elog_notify("Intermapper import file $import_file updated with $count record(s) for deletion");

    }
    else {
        elog_alert("Undetermined import directive, no update will take place");
        close (IMPORTFILE);
        return;
    }
    close (IMPORTFILE);
    return 0;
}

sub intermapper_import {

    #my ($retval,@output) = $imcli->import_data("$import_file");
    #if ($retval > 0) {
    my ($retval,@output) = $imhttp->import_data($import_file);
    if ($retval != $Intermapper::HTTPClient::IM_OK) {
        elog_complain($output[0]);
    }
    else {
        elog_notify($output[0]);
    }
    elog_debug("Intermapper return value: $retval");
    return $retval;
}

# Set the Intermapper device shape (icon) based on the station comms
sub get_shape {

    my $commtype = shift;
    my $provider = shift;
    #Set a default shape
    my $shape = $params->{shape}{default};

    my $commtype_shape = $params->{shape}{$commtype};
    my $provider_shape = $params->{shape}{$provider};

    # Use the provider shape if listed in the pf file. If not listed, use the
    # commtype shape if listed in the pf file. If neither listed, use default.
    if ( defined($provider_shape) ) {
        $shape = $provider_shape;
    }
    elsif ( defined($commtype_shape) ) {
        $shape = $commtype_shape;
    }

    elog_debug("Using shape $shape, for params $commtype, $provider");
    return $shape;
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
