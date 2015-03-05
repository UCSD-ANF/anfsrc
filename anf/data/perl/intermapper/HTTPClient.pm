package Intermapper::HTTPClient;

use warnings;
use strict;
use LWP::UserAgent;
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
use Scalar::Util qw(reftype);
use Carp;
use File::Basename;
use HTTP::Request::Common;

$VERSION = 0.01;
@ISA = qw(Exporter);
@EXPORT = qw(new command version import_data export_data);
@EXPORT_OK = qw(new command version import_data export_data);
%EXPORT_TAGS = ( Functions => [ qw(
        new
        command
        version
        import_data
        export_data
        ) ] );

# Constants

our $def_proto = 'http';
our %def_port  = (
    'http'  => 8018,
    'https' => 8443,
);
our $IM_OK = 200;

# Global config (can be set from other scripts)
our $VERBOSE=1;

sub _baseurl {
    my $self = shift;
    print "_baseurl self is $self\n" if $VERBOSE;
    my $url  = $self->{'proto'} . '://';
    $url    .= $self->{'host'} . ':' . $self->{'port'};
    return $url;
}

# Retrieve data with an HTTP GET.
# Inserts the host port username and password for you
# Required param:
#   path - everything after the proto://hostname:port part of the url
sub _get_data {
    my ($self,
        $path, # Required
    ) = @_;
    print STDERR "path is \"$path\"\n" if $VERBOSE;
    print STDERR "self is $self\n" if $VERBOSE;
    croak("Must specify path") unless defined($path);

    my $url = $self->_baseurl();
    $url .= $path;
    print STDERR "url is $url\n" if $VERBOSE;
    my $req = HTTP::Request->new('GET', $url);
    if (defined($self->{'username'})) {
        print STDERR "using basic authorization with username $self->{'username'}\n" if $VERBOSE;
        $req->authorization_basic($self->{'username'}, $self->{'password'});
    }
    my $res = $self->{'ua'}->request($req);
    print STDERR $res->status_line if $VERBOSE;
    return $res;
}

# Post data with an HTTP POST.
# An external program can also import table information with an HTTP POST
# operation by including the table data as the payload.
#
# http://imserver:port/~import/filename
# The filename in this URL is written to the log file, but is otherwise
# ignored. It is not used to determine the data to import, nor is it used to
# specify where the data goes. InterMapper examines the directive line of the
# attached file to determine what information is imported from the file. It
# follows the same logic that is used when importing data using the
# Import->Data File... command available from InterMapper RemoteAccess's File
# menu.
#
# A sample curl command line to import map data should take this form:
#
# $  curl --user admin:Pa55w0rd --data-binary @/path/to/import/file http://imserver:port/~import/file
#
# Note that this is NOT an RFC 1867 "Form-based File Upload" because that would
# be too easy.
sub _post_data {
    my ($self,
        $path, # Required
        $data, # Required
    ) = @_;
    print STDERR "path is \"$path\"\n" if $VERBOSE;
    print STDERR "data is \"$data\"\n" if $VERBOSE;
    croak("Must specify path") unless defined($path);
    croak("Must specify data") unless defined($data);

    my $url = $self->_baseurl();
    $url .= $path;
    print STDERR "url is $url\n" if $VERBOSE;
    #my $req = HTTP::Request->new('GET', $url);
    my $req = POST($url, Content => $data);
    if (defined($self->{'username'})) {
        print STDERR "using basic authorization with username $self->{'username'}\n" if $VERBOSE;
        $req->authorization_basic($self->{'username'}, $self->{'password'});
    }
    my $res = $self->{'ua'}->request($req);
    print STDERR $res->status_line if $VERBOSE;
    return $res;
}

# Constructor - requires the host. Optional parameters may be specified for the protocol to use (http or https), the port (defaults to 8018 for http, 8443 for https, the http username, and the http password.
sub new {
    my ($this,
        $host,
        $proto,     # Optional protocol (http or https, default http)
        $port,      # Optional port, 8018 for http, 8443 for https
        $username,  # Optional http username
        $password,  # Optional http password
    ) = @_;
    my $class = ref($this) || $this;
    my $self = {};

    $host = 'localhost' unless $host;
    $self->{'host'} = $host;

    $proto = $def_proto unless $proto;
    croak('Protocol for HTTPClient must be "http" or "https"') unless $proto =~ m/^(http|https)$/;
    $self->{'proto'} = $proto;

    $port = $def_port{$proto} unless $port;
    croak('Port must be numeric for HTTPClient') unless (0 < $port || $port < 65535);
    $self->{'port'} = $port;

    $self->{'username'} = $username;
    $self->{'password'} = $password;

    my $ua = LWP::UserAgent->new();
    $ua->env_proxy();
    $self->{'ua'} = $ua;

    bless($self, $class);
    return ($self);
}

sub import_data {
    my ($this,
        $filename, # only the last part of the path is used
        $data,     # if undef, the contents of filename are sent as the payload.. If defined, the filename parameter is only used to construct the URL, and the value in data is used.
    ) = @_;

    croak "filename must be specified" unless $filename;

    my $short_filename = basename($filename);
    my $url_path = "/~import/$short_filename";
    unless (defined($data)) {
        open FILE, "<$filename";
        $data = do { local $/; <FILE> };
    }
    my $res = $this->_post_data($url_path, $data);
    return ($res->code, $res->message) unless ($res->is_success());
    return ($IM_OK, split("\n", $res->decoded_content()));
}
sub export_data {
    my ($this,
        $format,     # default 'tab'
        $table,      # default 'devices'
        $fields_ref, # Optional refernce to an array of field names
    ) = @_;
    $format = 'tab' unless $format;
    $table  = 'devices' unless $table;

    croak('format must be one of "tab", "html", "csv", or "xml"')
        unless $format =~ m/^(tab|html|csv|xml)$/i;

    croak('table must be one of "Devices", "Interfaces", "Vertices", "Maps", "Notifiers", "Users", or "Schema"')
        unless $table =~ m/^(Devices|Interfaces|Vertices|Maps|Notifiers|Users|Schema)$/i;

    my @fields = [];
    if (defined($fields_ref)) {
        croak('fields must be an array reference') unless (reftype($fields_ref) eq 'ARRAY');
        @fields = @{ $fields_ref };
    }

    my $path="/~export/${table}.${format}";
    if (scalar(@fields) > 0) {
        $path .= '?fields=';
        $path .= join(',',@fields);
    }
    my $res = $this->_get_data($path);
    return ($res->code, $res->message) unless ($res->is_success());

    return ($IM_OK, split("\n", $res->decoded_content()));
}
