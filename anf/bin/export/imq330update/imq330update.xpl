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
our $VERSION = '4.0.1';
our $PROGNAME = basename ($0);
our $EXIT_CODE_FAILURE = 1;
our $EXIT_CODE_SUCCESS = 0;
our %ESCAPES = (
    n => "\n",
    t => "\t",
);

# Defaults
our $PFNAME = $PROGNAME;
our $PF_REVISION_TIME = 1428091288;

our $import_file = "/tmp/import.$$.tab";

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
        if (/\G \$(\w+) /gcsx || /\G \$\{(\w+)\} /gcsx) {
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

# Loop routine: deletes, adds and updates stations in Intermapper.
# Subroutine never exits unless the process is signaled.
sub loop {

    until($quit) {
        elog_debug("Starting loop");

        process();

        elog_debug(0, 'Sleeping for ', $params->{delay}, ' seconds');
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
        longitude comment shape improbe);
    elog_notify("Getting export of Intermapper data...");
    my $export_data_ref = intermapper_export(@export_fields);
    unless ($export_data_ref && ref($export_data_ref) eq 'ARRAY') {
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
    my $active_stations = db_query();
    elog_notify("Query complete");
    #print Dumper($active_stations);

    elog_notify("Checking for stations to delete from Intermapper...");
    # Note that this will have the side effect of modifying the im_records list
    # to remove the deleted stations. Thus, delete_stations must be called
    # before update_stations is called
    my $res = delete_stations($im_records, $active_stations);
    return $EXIT_CODE_FAILURE unless $res >= 0;

    elog_notify("Checking for stations to insert into Intermapper...");
    $res = insert_stations($im_records, $active_stations);
    return $EXIT_CODE_FAILURE unless $res >= 0;

    elog_notify("Checking for stations to update in Intermapper...");
    $res = update_stations($im_records, $active_stations);
    return $EXIT_CODE_FAILURE unless $res >= 0;

    return $EXIT_CODE_SUCCESS;
}

# Retrieve the current contents of the InterMapper map from the server
sub intermapper_export {
    my @export_fields = @_;

    my $export_table = 'devices';
    my $export_format = 'tab';
    my ($retval,@output) = $imhttp->export_data(
        $export_format,
        $export_table,
        \@export_fields,
    );

    elog_debug("Intermapper return value: $retval");
    if ($retval != $Intermapper::HTTPClient::IM_OK) {
        elog_complain($output[0]);
        return;
    }
    else {
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
        0, "Delete ", scalar(@keysdelete), " items: [ ",
        join(" ", @keysdelete),
        " ]"
    );

    my %deletes;
    my $count = 0;
    for my $key (@keysdelete) {
        #$deletes{$key}=$im_stations->{$key};
        $deletes{$key}={};
        $deletes{$key}{dnsname} = $key;
        $deletes{$key}{id}      = $im_stations->{$key}{id};
        # Remove this item from the current im_stations hash
        delete($im_stations->{$key});
        $count++;
    }

    return 0 unless $count;
    my $res = update_im('delete', \%deletes);
    return scalar(@keysdelete) if $res;
    return -1;
}

sub insert_stations {
    my ($im_stations,$active_stations) = @_;

    my @keysim = keys(%{$im_stations});
    my @keysactive = keys(%{$active_stations});
    elog_debug(0, "IM: " . scalar(@keysim) . " ACTIVE: " . scalar(@keysactive));
    # Use array slices to determine what items in keysactive are not in keysim
    my @keysinsert = grep { my $x = $_; not grep { $x eq $_ } @keysim } @keysactive;
    elog_debug(
        0, "Insert ", scalar(@keysinsert), " items: [ ",
        join(" ", @keysinsert), " ]",
    );

    my %inserts;
    my $count=0;
    for my $key (@keysinsert) {
        unless (
            (
                defined($active_stations->{$key}{inp}) &&
                $active_stations->{$key}{inp} ne ""
            ) ||
            $params->{plot_no_comms}
        ) {
            elog_notify("Skipping $key due to lack of comms");
            next;
        }

        $count++;

        elog_debug(0, 'Generating insert record for ', $key);

        # Create a new hash for $key
        $inserts{$key}={};
        $inserts{$key}{dnsname} = $key;

        if (defined($active_stations->{$key}{inp}) && $active_stations->{$key}{inp} ne '') {
            my @inp_parts = split (/:/, $active_stations->{$key}{inp});
            $inserts{$key}{address}      = $inp_parts[0];
            $inserts{$key}{comment} = $active_stations->{$key}{ssident};
            $inserts{$key}{latitude}     = $active_stations->{$key}{lat};
            $inserts{$key}{longitude}     = $active_stations->{$key}{lon};
        } else {
            # Don't set fields, defaults will apply in create_import_file
            elog_notify("Inserting station $key without comms");
        }

        $inserts{$key}{shape} = get_shape(
            $active_stations->{$key}{commtype},
            $active_stations->{$key}{provider}
        );


        my $vnet = $active_stations->{$key}{vnet};
        my $writeorb = get_writeorb($vnet);

        my %improbesymtab = (
            sta => $key,
            ip  => $inserts{$key}{address},
            commtype => $active_stations->{$key}{commtype},
            provider => $active_stations->{$key}{provider},
            writeorb => $writeorb,
        );

        $inserts{$key}{improbe}=get_improbe(\%improbesymtab);

        #elog_debug(Dumper($inserts{$key}));
    }

    # Bail out early if no records
    return 0 unless $count;

    # Perform the update
    my $res = update_im('insert', \%inserts);
    return $count if $res;
    return -1;
}

sub update_stations {
    my $im_stations     = shift;
    my $active_stations = shift;
    my %updates;

    my @keysim = keys(%{$im_stations});

    my $count = 0;

    for my $sta (@keysim) {
        my @inp_parts = split (/:/, $active_stations->{$sta}{inp});
        my $ip = $inp_parts[0];

        my $vnet = $active_stations->{$sta}{vnet};
        my $writeorb=get_writeorb($vnet);

        my $p='%.3f';
        my $latround = sprintf($p,$active_stations->{$sta}{lat});
        my $lonround = sprintf($p,$active_stations->{$sta}{lon});
        my $imlatround = sprintf($p,$im_stations->{$sta}{latitude});
        my $imlonround = sprintf($p,$im_stations->{$sta}{longitude});
        my $ssident = $active_stations->{$sta}{ssident};
        my $shape = get_shape($active_stations->{$sta}{commtype},
            $active_stations->{$sta}{provider});
        my %improbesymtab = (
            sta => $sta,
            ip  => $ip,
            commtype => $active_stations->{$sta}{commtype},
            provider => $active_stations->{$sta}{provider},
            writeorb => $writeorb,
        );
        my $improbe = get_improbe(\%improbesymtab);

        # See if anything changed
        my $update_record = 0;
        if ($im_stations->{$sta}{address} ne $ip) {
            elog_notify(0,
                'IP for ', $sta, ' changed from ',
                $im_stations->{$sta}{address},
                ' to ', $ip,
            );
            $update_record = 1;
        }

        if ($im_stations->{$sta}{comment} ne $ssident) {
            elog_notify(0,
                'Datalogger for ', $sta, ' changed from ',
                $im_stations->{$sta}{comment},
                ' to ', $active_stations->{$sta}{ssident},
            );
            $update_record = 1;
        }
        # Intermapper rounds lat/lon if beyond a certain precision. For
        # comparision purposes we round the actual and intermapper numbers to
        # three places of precision and just want them to be close.
        if (abs($imlatround - $latround) >= 0.002) {
            elog_notify("Latitude for $sta changed from $imlatround to $latround");
            $update_record = 1;
        }
        if (abs($imlonround - $lonround) >= 0.002) {
            elog_notify("Longitude for $sta changed from $imlonround to $lonround");
            $update_record = 1;
        }
        if ($im_stations->{$sta}{shape} ne $shape) {
            elog_notify("Icon for $sta changed from $im_stations->{$sta}{shape} to $shape");
            $update_record = 1;
        }

        # Update changed data
        if ($update_record) {
            $updates{$sta} = {
                id        => $im_stations->{$sta}{id},
                address   => $ip,
                dnsname   => $sta,
                comment   => $ssident,
                latitude  => $active_stations->{$sta}{lat},
                longitude => $active_stations->{$sta}{lon},
                shape     => $shape,
                improbe   => $improbe,
            };
            $count++;
        }
        else {
            next;
        }
    }

    # Bail out early if no records
    unless ($count) {
        elog_notify("All station data is current, nothing to update");
        return 0;
    }

    # Perform the update
    my $res = update_im('update',\%updates);
    return $count if $res;
    return -1;
}

# Update intermapper with map changes
#
# directive: one of insert, delete, or update
#
# data: reference to a hash of hashes, keyed by station name, then by
# Intermapper field name.
sub update_im {
    my $directive = shift;
    my $data = shift;

    unless ($directive =~ m/^(insert|delete|update)$/){
        elog_complain("update_im: bad directive \"$directive\"");
        return -1;
    }

    my $records = scalar(keys(%{$data}));

    if ($records == 0) {
        elog_complain("update_im: no data provided. Not performing $directive");
        return 0;
    }

    my $retval = create_import_file($directive, $data);
    if($retval) {
        $retval = intermapper_import();
        if ($retval == $Intermapper::HTTPClient::IM_OK) {
            elog_notify("$directive of $records records confirmed by Intermapper");
            return $records;
        } else {
            elog_alert("$directive failed in Intermapper");
            return -1;
        }
    } elsif ($retval == 0) {
        elog_notify("No entries written to import file. Skipping import.");
        return 0;
    } else {
        elog_alert("Errors writing import file");
        return -1;
    }
}


# Interpolate variables in improbe pf string
# Pf string should look like this:
# improbe://${ip}/edu.ucsd.cmd.tastation?orb=${writeorb}&dlsta=${sta}&commtype=${commtype}&provider=${provider}
#
sub get_improbe {
    my $symtab = shift;
    my $improbe = $params->{improbe};

    $improbe = interpolate($improbe, $symtab);
    $improbe = uri_encode($improbe);
    return $improbe;
}

# Create an import file suitable for import by intermapper
#
# directive: one of insert, delete, update
#
# data: hash of hashes containing data to be inserted, keyed by station name
# TODO: turn this into an array of hashes, since the station name is in the
# data hash itself
sub create_import_file {

    my ($directive,$data) = @_;

    return -1 unless defined $data && ref $data eq 'HASH';

    # Set default values for output fields
    my %defaults = (
        ip            => "10.0.0.1",
        comment       => "Unknown datalogger serial",
        latitude      => "90",
        longitude     => "0",
        mappath       => $params->{mappath},
        probe         => $params->{probe},
        timeout       => $params->{timeout},
        mapas         => "END SYSTEM",
        resolve       => "NONE",
        labelposition => $params->{labelpos},
        labelvisible  => $params->{labelvis},
    );
    elog_debug(0, "defaults hash: ", Dumper(\%defaults));

    # Create the import file
    my $fopen_res = open(IMPORTFILE, "> $import_file");
    unless ($fopen_res) {
        elog_complain("Couldn't open file $import_file for writing: $!");
        return;
    }

    my $count=0; # record counter
    my @outfields; # set in the directive block below
    if ($directive eq "insert") {
        @outfields = qw(
            mappath address dnsname improbe timeout
            latitude longitude resolve comment labelposition
            labelvisible shape
        );

        #print IMPORTFILE "# format=tab table=devices fields=mappath,address,dnsname,probe,improbe,timeout,latitude,longitude,resolve,comment,labelposition,labelvisible,shape\n";
        #
        # output fileheader
        print IMPORTFILE "# format=tab table=devices fields=";
        print IMPORTFILE join(',', @outfields);
        print IMPORTFILE "\n";

    }
    elsif ($directive eq "update") {
        @outfields    = qw(mappath id address dnsname latitude longitude
                           comment improbe shape);
        my @outmatch  = qw(mappath id);
        my @nomodify  = @outmatch;
        # Use items from outfields that are not in nomodify
        my @outmodify = grep { my $x = $_; not grep { $x eq $_ } @nomodify } @outfields;

        # output file header
        print IMPORTFILE "# format=tab table=devices fields=";
        print IMPORTFILE join(',', @outfields);
        print IMPORTFILE " modify=";
        print IMPORTFILE join(',', @outmodify);
        print IMPORTFILE " match=";
        print IMPORTFILE join(',', @outmatch);
        print IMPORTFILE "\n";
        #print IMPORTFILE "# format=tab table=devices fields=mappath,address,dnsname,latitude,longitude,comment ";
        #print IMPORTFILE "modify=address,latitude,longitude,comment match=mappath,dnsname\n";
    }
    elsif ($directive eq 'delete') {
        @outfields    = qw(mappath dnsname id);
        my @outdelete = qw(id);
        #print IMPORTFILE "# format=tab table=devices fields=mappath,dnsname delete=mappath,dnsname\n";
        #print IMPORTFILE "# format=tab table=devices fields=mappath,dnsname,id delete=id\n";
        print IMPORTFILE '# format=tab table=devices fields=';
        print IMPORTFILE join(',', @outfields);
        print IMPORTFILE " delete=";
        print IMPORTFILE join(',', @outdelete);
        print IMPORTFILE "\n";
    }
    else {
        elog_alert(0,
            'Undetermined import directive "',
            $directive,
            '", no update will take place'
        );
        close (IMPORTFILE);
        return -1;
    }

    # output each individual record
    OUTLINE: foreach my $record (keys %{$data}) {
        # Output the import file line
        my %outdata = (%defaults);
        # Apply defaults with perl hash slice trick
        @outdata{keys %{$data->{$record}}} = values %{$data->{$record}};

        #elog_debug(0, "Outdata for $record: ", Dumper(\%outdata));
        # make sure we have all of the necessary hash elements in data
        for my $field (@outfields) {
            unless (defined($outdata{$field})) {
                elog_complain(0,
                    'create_import_file: ',
                    "Missing field $field for output record $record",
                    ', skipping record'
                );
                next OUTLINE;
            }
        }

                # Generate the tab-delimited line based on outfields
        my $outline = join("\t", map { $outdata{$_} } @outfields);
        #elog_debug("inserting line: $outline");
        $count++;
        print IMPORTFILE $outline . "\n";
    }
    close (IMPORTFILE);

    elog_notify(0,
        'Intermapper import file ', $import_file,
        ' updated with ', $count, ' new record(s) for ',
        $directive
    );

    return $count;
}

sub intermapper_import {

    #my ($retval,@output) = $imcli->import_data("$import_file");
    #if ($retval > 0) {
    my ($retval,@output) = $imhttp->import_data($import_file);
    if ($retval != $Intermapper::HTTPClient::IM_OK) {
        elog_complain($output[0]);
    }
    else {
        #elog_notify($output[0]);
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

    #elog_debug("Using shape $shape, for params $commtype, $provider");
    return $shape;
}

sub get_writeorb {
    my $vnet = shift;

    my $writeorb;
    if (defined($params->{writeorb}{$vnet})) {
        $writeorb = $params->{writeorb}{$vnet} ;
    } else {
        $writeorb = $params->{writeorb}{default};
    }
}


__END__
=head1 NAME

imq330update - Update Q330 IP addresses and station attributes in Intermapper

=head1 SYNOPSIS

F<imq330update> [-V] [-f <parameterfile>]

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

B<IMq330update> is designed to read the q330comms table of an Antelope DBMaster
and update a map in Intermapper with station details. It adds and updates
changing Q330 IP addresses and station attributes, and will automatically
delete decertified stations that are listed in the deployments table.

=head1 EXAMPLES

Normal usage in an Antelope real-time system:

 imq330update

=head1 BUGS AND CAVEATS

Requires the q330comms table

=head1 AUTHOR

Originally written by Brian Battistuz as part of the Transportable Array
project.

Complete re-write by Geoff Davis to handle more networks, use the Intermapper
HTTP interfaces, and only use the dbmaster instead of the orb.

=head1 SUPPORT

Contributed: NO BRTT support -- please contact author at anf-admins@ucsd.edu

=cut

# vim:ft=perl
