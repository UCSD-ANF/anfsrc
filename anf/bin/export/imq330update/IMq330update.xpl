#
# Copyright (c) 2008 The Regents of the University of California
# All Rights Reserved
#
# Permission to use, copy, modify and distribute any part of this software for
# educational, research and non-profit purposes, without fee, and without a
# written agreement is hereby granted, provided that the above copyright
# notice, this paragraph and the following three paragraphs appear in all
# copies.
#
# Those desiring to incorporate this software into commercial products or use
# for commercial purposes should contact the Technology Transfer Office,
# University of California, San Diego, 9500 Gilman Drive, La Jolla, CA
# 92093-0910, Ph: (858) 534-5815.
#
# IN NO EVENT SHALL THE UNIVESITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
# LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF THE UNIVERSITY
# OF CALIFORNIA HAS BEEN ADIVSED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
# CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
# ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF CALIFORNIA MAKES NO
# REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EITHER IMPLIED OR
# EXPRESS, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT THE USE OF THE
# SOFTWARE WILL NOT INFRINGE ANY PATENT, TRADEMARK OR OTHER RIGHTS.
#
#   This code was created as part of the USArray project.
#   See http://anf.ucsd.edu/
#
#   Written By: Brian Battistuz 8/29/2008
#   Antelope-ized by: Geoff Davis 2/23/2015
#

use strict ;
use Pod::Usage;
use Datascope ;
use orb ;
use archive ;
use Getopt::Long;
use POSIX;
use File::Basename;
use Intermapper::Cli;
use Intermapper::HTTPClient;
use nagios_antelope_utils qw(&print_version);

our($params, $import_file, $imcli, $quit, $db,
    $commtype, $provider, $sta, $ip, $writeorb);
our $imhttp;

# Constants
our $AUTHOR   = "Brian Battistuz and Geoff Davis";
our $VERSION  = '3.07';
our $PROGNAME = basename($0);

# Defaults
our $VERBOSE = 0;
our $DEBUG   = 0;
our $PFNAME           = $PROGNAME;
our $PF_REVISION_TIME = 1425573334; # parameter file must be newer than this

# Changes in this version
# Adopted stations would not delete from map and multiplied. Needed to add
# vnet == '_US-TA' to dbsubsetting of certified and decertified stas to fix.

$quit =                 0;
$import_file =  "/tmp/import.tab";

MAIN:
{
    # Set signals to call &sig_handle
    $SIG{INT} = $SIG{TERM} = $SIG{HUP} = $SIG{KILL} = \&sig_handle;

    # Start log
    elog_init($0,@ARGV);

    check_args();

    elog_notify("Starting $PROGNAME.");
    loop();

}

sub check_args()
{
    ### Options ###

    my ($opt_version, $opt_v, $opt_d, $opt_help, $opt_f);
    our ($VERBOSE, $DEBUG);
    # Do some parameter checking
    Getopt::Long::Configure("bundling");
    GetOptions(
        "V" => \$opt_version, "version" => \$opt_version,
        "v" => \$opt_v, "verbose" => \$opt_v,
        'd' => \$opt_d,   "debug"   => \$opt_d,
        "h" => \$opt_help,    "help"    => \$opt_help,
        "f=s" => \$opt_f, "pf=s" => \$opt_f,
    ) || pod2usage(-verbose => 0, -exitval => 1);

    if ($opt_version) {
        print_version($VERSION, $AUTHOR);
        exit 0;
    }

    if ($opt_v) {
        $VERBOSE = 1;
    }

    if ($opt_d) {
        $DEBUG = 1;
    }

    $PFNAME = $opt_f if $opt_f;

    if ($opt_help)
    {
        pod2usage({-exitval => 0, -verbose => 2, -input => \*DATA});
    }

    # Check pf file
    pfrequire($PFNAME, $PF_REVISION_TIME);
    $params = pfget($PFNAME, "");

    $db    = $params->{db};
    #$imcli = new Intermapper::Cli($params->{impath});
    $imhttp = new Intermapper::HTTPClient(
        $params->{intermapper_host},
        $params->{intermapper_proto},
        $params->{intermapper_port},
        $params->{intermapper_username},
        $params->{intermapper_password},
    );
}

# Loop routine, deletes, adds, and updates stations in Intermapper. Subroutine
# won't die unless the process is signaled.
sub loop {

  my $delay = $params->{delay};
    my ($export_data,$im_records,$decert_records,$certcomm_records);
    chdir("/") or die "Couldn't chdir: $!\n";
    umask 0;
    verify_db();
    until($quit) {
        elog_notify("Getting export of Intermapper data...") if $VERBOSE;
      $export_data = intermapper_export();
      elog_notify("Export complete.") if $VERBOSE;
      unless ($export_data) {
        elog_complain("Couldn't get export data from Intermapper server");
        elog_complain("No updates will take place");
        sleep $delay;
        next;
      }
      elog_notify("Processing Intermapper export data for map " .
          $params->{mappath} . "...") if $VERBOSE;
      $im_records = process_export_data($export_data);
      elog_notify("Processing complete.") if $VERBOSE;
      elog_notify("Querying db $db for station data...") if $VERBOSE;
      ($decert_records,$certcomm_records) = db_query();
      elog_notify("Query complete.") if $VERBOSE;
      elog_notify("Checking for stations to delete from Intermapper...") if $VERBOSE;
        delete_stations($decert_records,$im_records);
        elog_notify("Checking for stations to insert into Intermapper...") if $VERBOSE;
        insert_stations($certcomm_records,$im_records);
        elog_notify("Checking for stations that need updating in Intermapper...") if $VERBOSE;
        update_stations($certcomm_records,$im_records);
        sleep $delay;
    }
    elog_notify("$PROGNAME stopped.");
}

# Trap signals
sub sig_handle {
    $quit = 1;
    elog_notify("Received signal, stopping IMq330update...");
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

    my ($ssident,$lat,$lon,$shape,$decert_time,$pollinterval,$improbe,$vnet);

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
            $count++;

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

            $commtype = $ref->{$record}{commtype};
            $provider = $ref->{$record}{provider};
            $shape    = $ref->{$record}{shape};
            $vnet     = $ref->{$record}{vnet};
            elog_notify("Inserting $sta with parameters $ip, $lat, $lon, $ssident, $shape");

            # URL encode spaces for improbe and add quotes because Intermapper
            # is really bad about handling parameters with spaces

            # Expand variables in improbe pf string
            $improbe = $params->{improbe}; # Reset improbe string w/ iteration
            $writeorb = $params->{writeorb}{$vnet}; # Reset writeorb w/ iteration
            $writeorb =~ s/:/%3A/;   # URL encode semicolons
            $commtype =~ s/\s+/%20/; # URL encode spaces for improbe string
            $provider =~ s/\s+/%20/;

            # To do symbolic dereferencing this way, all variables must be globals if using the "strict"
            # pragma
            $improbe =~ s/\$\{(\w+)\}/${$1}/g;

            print IMPORTFILE "$map\t$ip\t$sta\t$probe\t$improbe\t$timeout\t$lat\t$lon\t$resolve\t$ssident\t$labelpos\t$labelvis\t$shape\n";
        }
        elog_notify("Intermapper import file $import_file updated with $count new record(s) for insertion") if $VERBOSE;

    }
    elsif ($directive eq "update") {
        my ($count) = 0;
        print IMPORTFILE "# format=tab table=devices fields=mappath,address,dnsname,latitude,longitude,comment ";
        print IMPORTFILE "modify=address,latitude,longitude,comment match=mappath,dnsname\n";
        foreach my $record (keys %{$ref}) {
            $count++;
            $sta =                  $record;
            $ip =                   $ref->{$record}{address};
            $ssident =          $ref->{$record}{ssident};
            $lat =                  $ref->{$record}{lat};
            $lon =                  $ref->{$record}{lon};
            #$shape =               $ref->{$record}{shape};

            print IMPORTFILE "$map\t$ip\t$sta\t$lat\t$lon\t$ssident\n";
            elog_notify("Updating $sta with parameters $ip, $lat, $lon, $ssident");

        }
        elog_notify("Intermapper import file $import_file updated with $count record(s) to be updated") if $VERBOSE;

    }
    elsif ($directive eq "delete") {
        my ($count) = 0;
        print IMPORTFILE "# format=tab table=devices fields=mappath,dnsname delete=mappath,dnsname\n";
        foreach my $record (keys %{$ref}) {
            $count++;
            $sta =               $record;
            $decert_time = $ref->{$record}{decert_time};

            print IMPORTFILE "$map\t$sta\n";
            elog_notify("Deleting $sta. Decertfication time is $decert_time");

        }
        elog_notify("Intermapper import file $import_file updated with $count record(s) for deletion") if $VERBOSE;

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
    elog_debug("Intermapper return value: $retval") if $DEBUG;
    return $retval;
}

sub intermapper_export {

    #my $export_directive = "format=tab table=devices fields=mappath,dnsname,address,latitude,longitude,comment,shape";
    #my ($retval,@output) = $imcli->export_data("$export_directive");
    my @export_fields = qw(mappath dnsname address latitude longitude comment shape);
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
        elog_debug("Intermapper return value: $retval") if $DEBUG;
        return;
    }
    else {
        elog_debug("Intermapper return value: $retval") if $DEBUG;
        return \@output;
    }
}

# Put line records of Intermapper export data into hash
sub process_export_data {

    my $export_data = shift;
    my ($mappath,$dnsname,$address,$lat,$lon,$comment,$shape);
    my %im_records;

  # Process each line of the export output
    foreach my $record (@{$export_data}) {
      elog_debug("$record") if $DEBUG;
      if ( index($record,$params->{mappath} . "\t") == 0 ) {
            ($mappath,$dnsname,$address,$lat,$lon,$comment,$shape) = split(
                /\t/, $record);
            elog_debug("\%im_records:$mappath,$dnsname,$address,$lat,$lon,$comment,$shape") if $DEBUG;
            $im_records{$dnsname}{mappath} = $mappath;
            $im_records{$dnsname}{address} = $address;
            $im_records{$dnsname}{lat} =         $lat;
            $im_records{$dnsname}{lon}  =        $lon;
            $im_records{$dnsname}{ssident} = $comment;
            $im_records{$dnsname}{shape} =   $shape;
        }
        else {
            next;
        }
    }
    elog_debug(
        "Kept " . scalar(keys %im_records) . " of " . scalar (@{$export_data}) . "records"
    ) if $DEBUG;
    return \%im_records;
}

# Check existence of database. Good to verify it's there from time to time
# because our installation has it NFS mounted.

sub verify_db {

    unless ( -e "$db" ) {
        elog_complain("Database $db not found") && die;
    }
    unless ( -r "$db" ) {
        elog_complain("Database $db not readable") && die;
    }
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

    elog_notify("Using shape $shape, for params $commtype, $provider") if $DEBUG;
    return $shape;
}


sub db_query {

    my @db =                        dbopen($db,"r");
    my @dbdep =                 dblookup(@db,"","deployment","","");
    my @dbcomm =                dblookup(@db,"","comm","","");
    # Get all records w/ decert_times
    my @decert =                dbsubset(@dbdep, "snet == '$params->{network}' && decert_time <= now()");
    my @decertv;
    my %decert_records;
    # Get all records wo/ decert_times
    my @cert =                  dbsubset(@dbdep, "snet == '$params->{network}' && decert_time > now()");
    # Get comms info for certfied stations
    my @certcomm =          dbjoin(@cert,@dbcomm,"sta");
    my @certcommv;
    my %certcomm_records;
    my $nrec_decert =       dbquery(@decert, "dbRECORD_COUNT");
    my $nrec_certcomm = dbquery(@certcomm, "dbRECORD_COUNT");

    elog_notify("Found $nrec_decert decertified stations in deployments table") if $VERBOSE;
    elog_notify("Found $nrec_certcomm non-decertified stations in deployments table") if $VERBOSE;

    # Add info of certified stations and corresponding comms to hash
    for ($certcomm[3] = 0 ; $certcomm[3] < $nrec_certcomm ; $certcomm[3]++ ) {
        @certcommv = dbgetv(@certcomm,"sta","commtype","provider","vnet");
        $certcommv[0] = "$params->{network}_"."$certcommv[0]";
        $certcomm_records{$certcommv[0]} = {
            'commtype' => $certcommv[1],
            'provider' => $certcommv[2],
            'vnet'     => $certcommv[3] };
        elog_debug("\%certcomm_records: $certcommv[0], $certcommv[1], $certcommv[2], $certcommv[3]") if $DEBUG;
    }

    # Add decertifed station names to array
    for ($decert[3] = 0 ; $decert[3] < $nrec_decert ; $decert[3]++ ) {
        @decertv = dbgetv(@decert,"sta","decert_time");
        $decertv[0] = "$params->{network}_"."$decertv[0]";

        # Here we try to reconcile for the presence of multiple records for the
        # same station name in the deployments table due to reuse in other
        # projects. We're assuming that if a record has a cert_time but no
        # decert_time then that must be the most up to date record. Any other
        # records with decert_times should be ignored so this program won't
        # continuously add and remove the station from the map on each
        # execution.
        unless (exists $certcomm_records{$decertv[0]}) {
            $decert_records{$decertv[0]} = { 'decert_time' => $decertv[1] };
            elog_debug("\%decert_records: $decertv[0], $decertv[1]") if $DEBUG;
        }
    }
    dbclose(@db);



    return (\%decert_records,\%certcomm_records);
}

# Delete decertified stations from Intermapper
sub delete_stations {

  my $decert_records = shift;
  my $im_records = shift;
    my %deletes;
    my $count = 0;

    if (scalar(keys(%{$im_records})) == 0) { # No stations to delete
        elog_notify("No stations exist on the map $params->{mappath}. Nothing to delete") if $VERBOSE;
        return;
    }
    else { # Delete decertified stations if stations exist in Intermapper
        foreach my $decert_sta (keys %{$decert_records}) {
            if (exists $im_records->{$decert_sta}) {
                $deletes{$decert_sta} = $decert_records->{$decert_sta};
                $count++;
            }
            else {
                next;
            }
        }
        elog_notify("No existing stations in Intermapper decertified. Nothing to delete") if ($VERBOSE && $count == 0);
        update_im("delete", \%deletes);
    }
}

# Insert certified stations in intermapper
sub insert_stations {

    my $certcomm_records =  shift;
    my $im_records =                shift;
    my %inserts;
    my @db =                                dbopen($db,"r");
    my @dbq330 =                        dblookup(@db,"","q330comm","","");
    my @sta;
    my @recentip;
    my @recentipv;
    my ($shape,$inp,$ip,$ssident,$lat,$lon);
    my $count = 0;

    if (scalar(keys(%{$certcomm_records})) == 0 ) { # No stations to add
        elog_notify("No records exist for certified stations in db, nothing to insert") if $VERBOSE;
        return;
    }
    else { # Add certified stations if stations don't exist in Intermapper
        foreach my $cert_sta (keys %{$certcomm_records}) {
            unless (exists $im_records->{$cert_sta}) {

                # Find all q330comm records for station to try and get initial values
                elog_notify("Getting q330comm records for $cert_sta...") if $VERBOSE;
                @sta = dbsubset(@dbq330, "dlsta == '$cert_sta'");
                my $nrec_sta =      dbquery(@sta, "dbRECORD_COUNT");
          elog_debug("Number of records in \@sta = $nrec_sta") if $DEBUG;
                if ($nrec_sta == 0) { # No previous q330comm records for station
                  elog_notify("No q330comm records found.") if $VERBOSE;
                  elog_notify("Using default values for $cert_sta.") if $VERBOSE;
                    $ip = $ssident = $lat = $lon = undef;
                }
                else {
                  elog_notify("Found q330comm records.") if $VERBOSE;
                  elog_notify("Getting most recent...") if $VERBOSE;
                    @recentip = dbsubset(@sta, "time == max_table(time)"); # Get most recent
                    elog_notify("Found most recent.") if $VERBOSE;
                    @recentip[3] = 0;
                    ($inp,$ssident,$lat,$lon) = dbgetv(@recentip,"inp","ssident","lat","lon");
                    (undef,$ip,undef) = split /:/, $inp;
                    elog_notify("Using values $ip, $ssident, $lat, $lon for $cert_sta.\n");

                }
                $count++;
                elog_notify("Getting shape for $cert_sta...") if $VERBOSE;
                my $commtype = $certcomm_records->{$cert_sta}{commtype};
                my $provider = $certcomm_records->{$cert_sta}{provider};
                my $vnet     = $certcomm_records->{$cert_sta}{vnet};
                $shape = get_shape($commtype,$provider);
                $inserts{$cert_sta} = {
                    'shape'    => $shape,
                    'commtype' => $commtype,
                    'provider' => $provider,
                    'ip'             => $ip,
                    'ssident'  => $ssident,
                    'lat'            => $lat,
                    'lon'        => $lon,
                    'vnet'       => $vnet };
            }
            else {
                next;
            }
        }
        elog_notify(
            "All certified stations exist in Intermapper, nothing to insert"
        ) if ($VERBOSE && $count == 0);
        update_im("insert", \%inserts);
    }
    dbclose(@db);
}

sub update_stations {

    my $certcomm_records = shift;
    my $im_records       = shift;
    my %updates;
    my $pfsource         = $params->{packetname};
    my $orbname          = $params->{orb};

    my ($orb,$pktid,$srcname,$net,$sta,$chan,$loc);
    my ($nbytes,$result,$pkt,$packet,$subcode,$desc,$type,$suffix,$pf,$ref);
    my ($when,$src,$pkttime);
    my ($inp,$ssident,$idtag,$lat,$lon,$elev,$thr,$endtime);
    my @sources;
    my $count = 0;

  if (scalar(keys(%{$im_records})) == 0) { # No stations to update
    elog_notify("No stations exist in Intermapper to update") if $VERBOSE;
    return;
  }

    #  open input orb
    $orb = orbopen($orbname,"r");
    if( $orb < 0 ) {
            elog_complain("Failed to open orb '$orbname' for reading") && return;
    }
    orbselect( $orb, $pfsource);
    ($when, @sources) = orbsources ( $orb );

    foreach $src (@sources) {
        $srcname = $src->srcname() ;
        orbselect ( $orb, $srcname ) ;
        ($pktid, $srcname, $pkttime, $pkt, $nbytes) = orbget ( $orb, "ORBNEWEST" ) ;
        elog_notify("Reading packet $srcname, strydtime($pkttime)") if $VERBOSE;
        if (!defined $pktid) {
            next ;
        }
        if ( $nbytes == 0 ) {
            next ;
        }
        ($result, $pkt) = unstuffPkt ( $srcname, $pkttime, $pkt, $nbytes ) ;
        if ( $result ne "Pkt_pf" ) {
            if( $VERBOSE ) {
                elog_debug("Received a $result type packet, skipping") if $DEBUG ;
            }
            next;
        }
        elog_debug("Got pf packet $srcname strydtime($pkttime)") if $DEBUG;

        ($net, $sta, $chan, $loc, $suffix, $subcode) = $pkt->parts() ;
        ($type, $desc) = $pkt->PacketType() ;

        $pf = $pkt->pf ;

        if ( defined $pf ) {
            $ref = pfget($pf, "");
            my @stas = sort keys %{$ref->{dls}};
            foreach my $sta (@stas) {
                next if ($sta !~ /^$params->{network}/);

                my @pars = sort keys %{$ref->{dls}{$sta}};
                $inp     = $ref->{dls}{$sta}{"inp"};
                $ssident = $ref->{dls}{$sta}{"sn"};
                $idtag   = $ref->{dls}{$sta}{"pt"};
                $lat     = $ref->{dls}{$sta}{"lat"};
                $lon     = $ref->{dls}{$sta}{"lon"};
                $elev    = $ref->{dls}{$sta}{"elev"};
                $thr     = $ref->{dls}{$sta}{"thr"};

                next if ( $idtag == 0 );

                # Ignore station data from decertified stations
                next unless (exists $certcomm_records->{$sta});

                # Ignore station data if the station doesn't exist in Intermapper
                next unless (exists $im_records->{$sta});

                if ( $ssident =~ /.*[a-f].*/ ) {
                        elog_debug("$srcname     $sta    $ssident        " . strydtime($pkttime) . " pktid  $pktid") if $DEBUG;
                }

                # Clean up data a bit
                $ssident     = uc($ssident);

                if ($lat eq "-" || $lon eq "-" || $elev eq "-" || abs($lat) < 0.01 || abs($lon) < 0.01) {
                  if ($im_records->{$sta}{lat} ne "90" && $im_records->{$sta}{lon} ne "0") {
                        $lat = $im_records->{$sta}{lat};
                        $lon = $im_records->{$sta}{lon};
                  }
                  else {
                    ($lat,$lon,$elev) = (90,0,0);
                  }
                }

                my $latround = sprintf("%.3f",$lat);
                my $lonround = sprintf("%.3f",$lon);
                my $imlatround = sprintf("%.3f",$im_records->{$sta}{lat});
                my $imlonround = sprintf("%.3f",$im_records->{$sta}{lon});
                my (undef,$ip,undef) = split /:/, $inp;
                my $shape = get_shape($certcomm_records->{$sta}{commtype},$certcomm_records->{$sta}{provider});

                # See if anything changed
                my $update_record = 0;
                if ($im_records->{$sta}{address} != $ip) {
                    elog_notify("IP for $sta changed from $im_records->{$sta}{address} to $ip");
                    $update_record = 1;
                }
                if ($im_records->{$sta}{ssident} != $ssident) {
                    elog_notify("Datalogger for $sta changed from $im_records->{$sta}{ssident} to $ssident");
                    $update_record = 1;
                }
                # Intermapper rounds lat/lon if beyond a certain precision. For
                # comparision purposes we round the actual and intermapper numbers to
                # three places of precision and just want them to be close.
                if (abs($imlatround - $latround) >= 0.002) {
                    #elog_notify("Latitude for $sta changed from $im_records->{$sta}{lat} to $lat");
                    elog_notify("Latitude for $sta changed from $imlatround to $latround");
                    $update_record = 1;
                }
                if (abs($imlonround - $lonround) >= 0.002) {
                    #elog_notify("Longitude for $sta changed from $im_records->{$sta}{lon} to $lon");
                    elog_notify("Longitude for $sta changed from $imlonround to $lonround");
                    $update_record = 1;
                }
                if ($im_records->{$sta}{shape} != $shape) {
                    elog_notify("Icon for $sta changed from $im_records->{$sta}{shape} to $shape");
                    $update_record = 1;
                }

                # Update changed data
                if ($update_record) {
                    $updates{$sta} = { 'address' => $ip,
                                                         'ssident' => $ssident,
                                                         'lat'     => $lat,
                                                         'lon'       => $lon,
                                                         'shape'   => $shape };
                    $count++;
                }
                else {
                    next;
                }
            }
            elog_notify("All station data is current, nothing to update") if ($VERBOSE && $count == 0);
        }
    }

  # Update Intermapper map and datascope databases
    update_im("update",\%updates);

  # Close orb
  orbclose($orb);
}

sub update_im {

    my ($directive,$ref) = @_;

    if ($directive eq "insert") {
        my %inserts = %{$ref};
        # elog_debug("Num elements in inserts: $#inserts") if $DEBUG;
        unless (scalar(keys(%inserts)) == 0) {
            my $retval = create_import_file("insert",$ref);
            if (defined($retval)) {
                $retval = intermapper_import();
                if ($retval == 0) {
                    elog_notify("Insert of station(s) confirmed in Intermapper") if $VERBOSE;
                }
                else {
                    elog_alert("Insert of station(s) failed in Intermapper") if $VERBOSE;
                }
            }
            else {
                elog_alert("Errors writing import file") if $VERBOSE;
            }
        }
    }

    elsif ($directive eq "update") {
        my %updates = %{$ref};
        # elog_debug("Num elements in updates: $#updates") if $DEBUG;
        unless (scalar(keys(%updates)) == 0) {
            my $retval = create_import_file("update",$ref);
            if (defined($retval)) {
                $retval = intermapper_import();
                if ($retval == 0) {
                    elog_notify("Update of station(s) confirmed in Intermapper") if $VERBOSE;
                }
                else {
                    elog_alert("Update of station(s) failed in Intermapper") if $VERBOSE;
                }
            }
            else {
                elog_alert("Errors writing import file") if $VERBOSE;
            }
        }
    }

    elsif ($directive eq "delete") {
        my %deletes = %{$ref};
        # elog_debug("Num elements in deletes: $#deletes") if $DEBUG;
        unless (scalar(keys(%deletes)) == 0) {
            my $retval = create_import_file("delete",$ref);
            if (defined($retval)) {
                $retval = intermapper_import();
                if ($retval == 0) {
                    elog_notify("Delete of station(s) confirmed in Intermapper") if $VERBOSE;
                }
                else {
                    elog_alert("Delete of station(s) failed in Intermapper") if $VERBOSE;
                }
            }
            else {
                elog_alert("Errors writing import file") if $VERBOSE;
            }
        }
    }
    else {
        return;
    }
}

# Want to make a db query to get all information and compare that to export data
# db query should have station,ip,lat,lon,ssident,commtype,provider for particular station
# Steps
# 1. Get exported data from intermapper
# 2. Do db query for decertified station names
# 3. Diff db data from export data
# 4. Delete decertified stations still on map
# 5. Do db query for certified station names, commtype, and provider (deployments,comm)
# 6. Set default values for ip, lat, lon, ssident
# 7. Compare to export data from intermapper
# 8. Take difference of stations already on map
# 9. Add new station if not on map
# 10. Find values for ip, lat, lon, ssident from orb st packets
# 11. Update new station data if found in packets
# 12. Update existing station data if new data in packets
#

__END__
=head1 NAME

IMq330update - Update Q330 IP addresses and station attributes in Intermapper

=head1 SYNOPSIS

F<IMq330update> [-v] [-d] [-f <parameterfile>]

=head1 OPTIONS

=over 8

=item B<-f (--pf)>

Specify the Antelope parameter file to use. Defaults to IMq330update.pf

=item B<-v (--verbose)>

Verbose logging

=item B<-d (--debug)>

Debug logging

=item B<-h (--help)>

Print a help message and exit

=item B<-V (--version)>

Print the version of this script

=back

=head1 DESCRIPTION

B<IMq330update> is designed to read the q330comms table of an Antelope DBMaster and update a map in Intermapper with station details. It adds and updates changing Q330 IP addresses and station attributes, and will automatically delete decertified stations that are listed in the deployments table.

=head1 EXAMPLES

Normal usage in an Antelope real-time system:

 IMq330update -v

=head1 BUGS AND CAVEATS

Does not currently handle changing Comm type or Comm provider for a station.

Does not use the HTTP API for interacting with Intermapper

=head1 AUTHOR

Originally written by Brian Battistuz as part of the Transportable Array
project.

Modified by Geoff Davis to work with later versions of Antelope and Intermapper

=head1 SUPPORT

Contributed: NO BRTT support -- please contact author.

=cut

# vim:ft=perl
