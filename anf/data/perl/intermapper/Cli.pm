package Intermapper::Cli;

use strict;

use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);

$VERSION     = 1.00;
@ISA = qw(Exporter);
@EXPORT = qw(new command version import_data export_data);
@EXPORT_OK = qw(new command version import_data export_data show_cli_params);
%EXPORT_TAGS = ( Functions => [ qw(new
																	 command
																	 version
																	 import_data
																	 export_data) ] );

# Constructor - requires the location of the Intermapper install
sub new {
	my $class 	= $_[0];
	my $im_home = $_[1] || "/usr/local/intermapper";
	my $im_cli = "$im_home/share/intermapper/intermapper.jar";

	if ( -e $im_cli) {
			unless (-x $im_cli) {
				print "Intermapper CLI needs execute permissions.\n";
				print "Attempting to set execute permissions.\n";
				my $chmod_success = chmod(0555, $im_cli);
				if ($chmod_success) {
						print "Intermapper CLI permissions changed to 555.\n";
				}
				else {
						die "Couldn't change Intermapper CLI file pemissions.\n" ;
				}
			}
	}
	else {
		die "client $im_cli not found: $!\n";
	}

	my $self = {
				im_home => $im_home,
				im_cli => $im_cli
			   };

	bless $self, $class;
	return $self;
}

# Show the instance paramters
sub show_cli_params {
	my $self = shift;
	foreach my $param (keys(%{$self})) {
		print "$param\t\t$self->{$param}\n";
	}
}

# Generic command interface to Intermapper client
sub command {
	my $self = shift;
	my $param_string = shift;
	my @output;
	open (IMCLI, "$self->{im_cli} $param_string -ignore-cert-check 2> /dev/null |") or @output = "Couldn't execute $self->{im_cli}: $!\n" && return ($? >> 8,@output);
	while (<IMCLI>) {
		chomp($_);
		push @output,$_;
  	}
  	close IMCLI;
  	my $retval = $? >> 8;
  	return ($retval,@output);
}

# Echo version
sub version{
	my $self = shift;
	my ($retval,@output) = $self->command("-version");
	return ($retval,@output);
}

# Import data to Intermapper
sub import_data {
	my $self = shift;
	my $import_params = shift; # Import parameter can be a file

	#die "Import parameters not defined.\n" if (!defined($import_params));

	my ($retval,@output) = $self->command("-import \"$import_params\"");
  	return ($retval,@output);
}

# Export Intermapper data
sub export_data {
	my $self = shift;
	my $export_params = shift; # Export always exports data from all maps

	#die "Export parameters not defined.\n" if (!defined($export_params));

	my ($retval,@output) = $self->command("-export \"$export_params\"");
  return ($retval,@output);
}

1;
