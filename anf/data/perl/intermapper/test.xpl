use Intermapper::Cli;

$imcli = new Intermapper::Cli("/opt/intermapper");
($retval,@output) = $imcli->export_data("format=tab table=devices fields=*");
print "@output\n";
print "$retval\n";
