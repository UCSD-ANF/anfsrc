#use Intermapper::Cli;
use Intermapper::HTTPClient;

#$imcli = new Intermapper::Cli("/opt/intermapper");
#($retval,@output) = $imcli->export_data("format=tab table=devices fields=*");
#print "@output\n";
#print "$retval\n";
$http_user='q330update';
print "Please enter the password for user $http_user: ";
system('stty', '-echo'); # disable echoing
$password = <>;
chomp $password;
system('stty', 'echo');  # Turn it back on
print ("\n");
$imhttp = new Intermapper::HTTPClient('anfmonl.ucsd.edu', 'https', 8443, $http_user, $password);
($retval,@output) = $imhttp->export_data('tab', 'devices', ['mappath','id','name','latitude','longitude','improbe']);
print "@output\n";
print "$retval\n";
