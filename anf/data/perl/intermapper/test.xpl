use warnings;
use strict;
use Intermapper::Cli;
use Intermapper::HTTPClient;

local $Intermapper::HTTPClient::VERBOSE=0;
our ($imhttp, $password);
our ($imcli);
our $HTTP_USER = 'q330update';
our $CLI_BASEDIR = '/opt/intermapper';

our $TABFILE = './TA.tab';

sub get_password {
    my $prompt = shift;
    print STDERR $prompt;
    system('stty', '-echo'); # disable echoing
    my $password = <>;
    chomp $password;
    system('stty', 'echo');  # Turn it back on
    print ("\n");
    return $password;
}

sub init_http {
    our $password = get_password(
        "Please enter the password for user $HTTP_USER: "
    );
    our $imhttp = new Intermapper::HTTPClient(
        'anfmonl.ucsd.edu',
        'https',
        8443,
        $HTTP_USER,
        $password,
    );
    die "Couldn't initalize Intermapper::HTTPClient" unless $imhttp;
}

sub init_cli {
    $imcli = new Intermapper::Cli($CLI_BASEDIR);
}

#($retval,@output) = $imcli->export_data("format=tab table=devices fields=*");
#print "@output\n";
#print "$retval\n";

MAIN: {
    my ($retval, @output);
    my $format = 'tab';
    my $table  = 'devices';
    my @fields = ('MapPath','Id','Name','Latitude','Longitude','IMProbe');
    my $mappath = '/Dataloggers/TA';

    #init_cli();
    init_http();

    # Export data from Intermapper to TABFILE
    ($retval,@output) = $imhttp->export_data($format, $table, \@fields);
    print "after http export, retval is $retval\n";
    die ("Couldn't export data from intermapper: ". join("\n", @output))
    #die ("Couldn't export data from intermapper: ")
        unless ($retval == $Intermapper::HTTPClient::IM_OK);

    open (my $outfh, '>', $TABFILE)
        or die ("Couldn't open $TABFILE for writing: $!");

    # Output the file preamble
    print $outfh "#format=$format table=$table fields=";
    print $outfh join(",", @fields);
    print $outfh "\n\n";

    my $outlines=0;
    foreach my $line (@output) {
        unless (index($line,$mappath) == 0) {
           #print "skipping line\n";
            next;
        }
        print $outfh "$line\n";
        $outlines++;
    }
    close($outfh);
    print STDERR "kept $outlines out of $@output\n";

    #exit(0);
    # Import data from TABFILE
    ($retval,@output) = $imhttp->import_data($TABFILE);
    print "after http import, retval is $retval\n";
    print "output: @output\n";
}

# vim ft=perl
