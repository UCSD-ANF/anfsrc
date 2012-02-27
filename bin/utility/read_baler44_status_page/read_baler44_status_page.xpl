#
# Script to read Baler44 status page 
# using http protocol. 
#
# The original script was written by 
# Allan Sauter and emailed to Juan Reyes
# on 5/19/2011. 
#
# usage: Baler44Check.pl baler44List.txt 20091229
#  where 20091229 is the current firmware version date
#   baler44List.txt is a page capture of https://anf.ucsd.edu/admin/tools/dlstats/balerinfo.php
#   This program checks each baler page for gone-haywire thumbdrives, correct firmware, present ops, and speed

#use strict;
use warnings;
use LWP;
use archive;
use sysinfo;
use Datascope;
use File::Copy;
use Pod::Usage;
use Getopt::Std;
use URI::Escape;
# this program uses the file: ($ARGV[0]) 


elog_init($0,@ARGV);
$start = now();


unless ( &getopts('dhvm:s:r:f:') && scalar @ARGV == 2 ) { 
    pod2usage({-exitval => 2, -verbose => 2});
}

#
# Print help text and exit
#
pod2usage({-exitval => 2, -verbose => 2}) if $opt_h;

#
# directory to store the 
# databases for each station
#
$out_dir   = $ARGV[0];
$dbmaster = $ARGV[1];

#
# implicit flags
#
$opt_v = $opt_d ? $opt_d : $opt_v;

#
# Verify access to directory
#
elog_die("Cannot access dir => $out_dir.") unless -e $out_dir;

#
# Initialize  mail
#
if ($opt_m){
    elog_notify("Initialize mail") if $opt_v;
    savemail();
}


elog_notify('');
elog_notify("$0 @ARGV");
elog_notify("Starting execution at ".epoch2str(now(),'%Y-%m-%d %H:%M:%S')." on ".my_hostname());
elog_notify('');
elog_notify('');

#
# Verify Database
#
elog_notify("Opening $dbmaster:") if $opt_v;

@db = dbopen( $dbmaster, "r" ) or elog_die("Can't open DB: $dbmaster");

# Open table for list of valid stations 
elog_debug('Lookup deployment table...') if $opt_d;
@db_on = dblookup(@db, "", "deployment" , "", "");
elog_debug('Test deployment table...') if $opt_d;
table_check(\@db_on);

# Open table for list of station types ie 'PacketBaler44'
elog_debug('Lookup stabaler table...') if $opt_d;
@db_sta = dblookup(@db, "", "stabaler", "", "");
elog_debug('Test stabaler table...') if $opt_d;
table_check(\@db_sta);

# Open table for list of current ips
elog_debug('Lookup staq330 table...') if $opt_d;
@db_ip = dblookup(@db, "", "staq330" , "", "");
elog_debug('Test staq330 table...') if $opt_d;
table_check(\@db_ip);

elog_debug('Get list of stations:') if $opt_d;
$stations = get_stations_from_db(); 

#
# Global file with all JSON files concatenated...
#
$global_json = "$out_dir/global.json";
$global_json_temp = "$out_dir/global_temp.json";
unlink $global_json_temp if -e $global_json_temp;
open TEMPGLOBAL, ">", $global_json_temp or elog_die("Could not open file [$global_json_temp] :$!");

print TEMPGLOBAL "{\n";


$count = 0; 
foreach $temp_sta ( sort keys %$stations ) {
#{{{
    print TEMPGLOBAL ",\n" if $count;
    $count += 1;
    $old_problems = '';
    $new_problems = '';
    $temp_1 = '"-"';
    $temp_2 = '"-"';
    $temp_3 = '"-"';
    $temp_4 = '"-"';
    $temp_5 = '"-"';

    $ip     = $stations->{$temp_sta}->{ip};
    $net    = $stations->{$temp_sta}->{net};

    elog_notify("$temp_sta");

    $url = "http://$ip:5381/stats.html";
    elog_debug("$temp_sta:\turl: $url") if $opt_d;

    $json = "$out_dir/$temp_sta.json";
    elog_debug("$temp_sta:\tjson: $json") if $opt_d;

    $raw = "$out_dir/$temp_sta.html";
    elog_debug("$temp_sta:\traw: $raw") if $opt_d;

    $error = "$out_dir/$temp_sta.error";
    elog_debug("$temp_sta:\terror: $error") if $opt_d;

    if ($opt_d) {
        elog_debug("$temp_sta:  RAW:\t\t$_") foreach @text;
    }

    elog_notify("$temp_sta:\tPrepare ERROR file: $json") if $opt_v;
    if ( -e $error ){
        open FILE, "<", $error or elog_die("Could not read file [$error] :$!");
        foreach ( <FILE> ) {
            $old_problems .= $_ unless /timeout/;
        }
        #$old_problems .= $_ foreach <FILE>;
        close FILE;
    }
    unlink $error if -e $error;

    ($content, $status, $success) = do_GET($temp_sta,$url);

    if ( $success ) {
        elog_debug("$temp_sta:\tStatus:\t$status") if $opt_d;
        elog_debug("$temp_sta:\tIs Success:\t$success") if $opt_d;
        elog_debug("$temp_sta:\tContent:") if $opt_d;
    }
    else {
        elog_complain("$temp_sta:");
        elog_complain("$temp_sta:\tERROR getting status page!");
        elog_complain("$temp_sta:\tStatus:\t$status");
        elog_complain("$temp_sta:");
        #$new_problems .= epoch2str(now(),'%Y-%m-%d %H:%M:%S')."$temp_sta ERROR: [$url]=>[$status]\n";
    }

    @text =  split '\n', $content;

    #
    # Read old JSON file
    #
    elog_notify("$temp_sta:\tRead old JSON file: $json") if $opt_v;
    if ( -e $json ){
        open FILE, "<", $json or elog_die("Could not read file [$json] :$!");
        foreach (<FILE>){
            chomp;
            s/^\s+//;
            next unless /:/;
            if (/^"(\S+)":"(.*)",?$/){ ${$1} = $2;}
            elsif (/^"(\S+)":(\d*\.?\d*),?$/){ ${$1} = $2;}
            elsif (/^"(\S+)":(.*),?$/){ ${$1} = $2;}
            else { elog_complain("ERROR PARSING: [$_]"); }
            elog_notify("$temp_sta:\t[$1=>$2]") if defined $1 and defined $2;
        }
        close FILE;
    }

    #
    # If we get a page!
    #
    if ( $success ) {
#{{{
        #
        # Clean JSON file
        #
        unlink $json if -e $json;

        open FILE, ">", $json or elog_die("Could not open file [$json] :$!");
        print FILE "{\n";
        print FILE "\t\"station\":\"$temp_sta\",\n";
        print FILE "\t\"updated\":\"" . epoch2str(now(),'%Y-%m-%d %H:%M:%S') . "\",\n";
        print FILE "\t\"updated_epoch\":\"".now()."\",\n";

        # Station name
        if ( $text[2] =~ /- Station (\w+-\w+)</ ){
            $temp_1 = $1
        } else {
            $temp_1 = '-';
        }
        elog_notify("$temp_sta:\t$text[2]") if $opt_v;
        elog_notify("$temp_sta:\tname: $temp_1") if $opt_v;
        if ($name and $name ne $temp_1) {
            $new_problems .= epoch2str(now(),'%Y-%m-%d %H:%M:%S')."$temp_sta ERROR: name:[$name]=>[$temp_1]\n";
        }
        print FILE "\t\"name\":\"$temp_1\",\n";

        #
        # Look for "ILLEGAL MEDIA FILE NAMES" 
        #
        $illegal = 0;
        for ($line=0; $line < scalar @text; $line++){
            if ( $text[$line] =~ m/.*ILLEGAL MEDIA FILE NAMES.*/ ) {
                print FILE "\t\"illegal_file_names\":\"$text[$line]\",\n";
                $illegal = 1;
            }
        }
        print FILE "\t\"illegal_file_names\":\"\",\n" unless $illegal ;

        #
        # Look for "Baler Information" section
        #
        for ($line=0; $line < scalar @text; $line++){
            last if $text[$line] =~ m/^<H4>Baler Information<\/H4>$/;
        }

        if ($line < scalar @text ) {
#{{{
            # Baler firmware version
            $line += 2;
            if ( $text[$line] =~ /Inc\. (\w+)-(\w+)-(\w+) tag (\d+) at (.+)$/ ) {
                $temp_1 = $1;
                $temp_2 = $2;
                $temp_3 = $3;
                $temp_4 = $4;
                $temp_5 = $5;
            } else {
                $temp_1 = '-';
                $temp_2 = '-';
                $temp_3 = '-';
                $temp_4 = '-';
                $temp_5 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tfirmware:$temp_1-$temp_2-$temp_3 $temp_4 $temp_5") if $opt_v;
            if ($firmware and $firmware ne $temp_2) {
                $new_problems .= epoch2str(now(),'%Y-%m-%d %H:%M:%S')."$temp_sta ERROR: firmware:[$firmware]=>[$temp_2]\n";
            }
            print FILE "\t\"full_tag\":\"$temp_1-$temp_2-$temp_3\",\n";
            print FILE "\t\"firmware\":\"$temp_2\",\n";
            print FILE "\t\"tag\":\"$temp_4\",\n";
            print FILE "\t\"tag_date\":\"$temp_5\",\n";

            # Baler last reboot
            $line++;
            if ( $text[$line] =~ /^last baler reboot:\s+(.+)\s+reboots:\s+(\d+)\s+runtime:\s+(.+)$/) {
                $temp_1 = $1;
                $temp_2 = $2;
                $temp_3 = $3;
            }else {
                $temp_1 = '-';
                $temp_2 = '-';
                $temp_3 = '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\treboots:$1 $2 $3") if $opt_v;
            print FILE "\t\"reboot\":\"$temp_1\",\n";
            print FILE "\t\"reboot_total\":\"$temp_2\",\n";
            if ( $temp_3 =~ /.*d/ ) {
                $temp_3 = sprintf("%0.2f", substr($temp_3, 0, -1)) || '"-"';
            }
            else {
                $temp_3 = '"-"';
            }
            print FILE "\t\"runtime\":$temp_3,\n";

            # MEDIA status
            $line++;
            $temp_1 = $text[$line];
            chomp $temp_1;
            if ($media_status and $media_status ne $temp_1) {
                $new_problems .= epoch2str(now(),'%Y-%m-%d %H:%M:%S')."$temp_sta ERROR: media_status:[$media_status]=>[$temp_1]\n";
            }
            elog_notify("$temp_sta:\t$temp_1") if $opt_d;
            elog_notify("$temp_sta:\tmedia_status:$temp_1") if $opt_v;
            print FILE "\t\"media_status\":\"$temp_1\",\n";

            # MEDIA 1
            for ($line=0; $line < scalar @text; $line++){
                last if $text[$line] =~ m/^MEDIA site 1.*$/;
            }
            if ($line < scalar @text ) {

                if ( $text[$line] =~ /^MEDIA site 1 crc=(\w+) (.+) state: (\w+)\s+capacity=(\S+)\s+free=(\S+)$/ ){
                    $temp_1 = $1;
                    $temp_2 = $2;
                    $temp_3 = $3;
                    $temp_4 = $4;
                    $temp_5 = $5;
                } else {
                    $temp_1 = '-';
                    $temp_2 = '-';
                    $temp_3 = '-';
                    $temp_4 = '"-"';
                    $temp_5 = '"-"';
                }
                if ( $temp_4 =~ /Mb/ ) {
                    $temp_4 = sprintf("%0.2f", substr($temp_4, 0, -2)) || '"-"';
                }
                if ( $temp_5 =~ /%/ ) {
                    $temp_5 = sprintf("%0.3f", substr($temp_5, 0, -1)) || '"-"';
                }
                elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
                elog_notify("$temp_sta:\tmedia_1:$temp_1 $temp_2 $temp_3 $temp_4 $temp_5") if $opt_v;
            }
            else {
                elog_complain("$temp_sta:\tERROR getting MEDIA site 1!") if $opt_d;
                $temp_1 = '-';
                $temp_2 = '-';
                $temp_3 = '-';
                $temp_4 = '"-"';
                $temp_5 = '"-"';
            }

            print FILE "\t\"media_1\":\"$temp_1\",\n";
            print FILE "\t\"media_1_name\":\"$temp_2\",\n";
            print FILE "\t\"media_1_state\":\"$temp_3\",\n";
            print FILE "\t\"media_1_capacity\":$temp_4,\n";
            print FILE "\t\"media_1_free\":$temp_5,\n";


            # MEDIA 2
            for ($line=0; $line < scalar @text; $line++){
                last if $text[$line] =~ m/^MEDIA site 2.*$/;
            }
            if ($line < scalar @text ) {

                if ( $text[$line] =~ /^MEDIA site 2 crc=(\w+) (.+) state: (\w+)\s+capacity=(\S+)\s+free=(\S+)$/ ){
                    $temp_1 = $1;
                    $temp_2 = $2;
                    $temp_3 = $3;
                    $temp_4 = $4;
                    $temp_5 = $5;
                } else {
                    $temp_1 = '-';
                    $temp_2 = '-';
                    $temp_3 = '-';
                    $temp_4 = '"-"';
                    $temp_5 = '"-"';
                }
                if ( $temp_4 =~ /Mb/ ) {
                    $temp_4 = sprintf("%0.2f", substr($temp_4, 0, -2)) || '"-"';
                }
                if ( $temp_5 =~ /%/ ) {
                    $temp_5 = sprintf("%0.3f", substr($temp_5, 0, -1)) || '"-"';
                }
                elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
                elog_notify("$temp_sta:\tmedia_2:$temp_1 $temp_2 $temp_3 $temp_4 $temp_5") if $opt_v;
            }
            else {
                elog_complain("$temp_sta:\tERROR getting MEDIA site 2!") if $opt_d;
                $temp_1 = '-';
                $temp_2 = '-';
                $temp_3 = '-';
                $temp_4 = '"-"';
                $temp_5 = '"-"';
            }
            print FILE "\t\"media_2\":\"$temp_1\",\n";
            print FILE "\t\"media_2_name\":\"$temp_2\",\n";
            print FILE "\t\"media_2_state\":\"$temp_3\",\n";
            print FILE "\t\"media_2_capacity\":$temp_4,\n";
            print FILE "\t\"media_2_free\":$temp_5,\n";

            # Baler voltage and temp
            for ($line=0; $line < scalar @text; $line++){
                last if $text[$line] =~ m/^upsvolts=.*$/;
            }
            if ( $text[$line] =~ /^upsvolts=(\S+)\s+primaryvolts=(\S+)\s+degc=(\S+)$/) {
                $temp_1 = $1;
                $temp_2 = $2;
                $temp_3 = $3;
            } else {
                $temp_1 = '"-"';
                $temp_2 = '"-"';
                $temp_3 = '"-"';
            }
            if ( $temp_1 =~ /\d+\.\d+/ ) {
                $temp_1 = sprintf("%0.3f", $temp_1) || '"-"';
            }
            if ( $temp_2 =~ /\d+\.\d+/ ) {
                $temp_2 = sprintf("%0.3f", $temp_2) || '"-"';
            }
            if ( $temp_3 =~ /\d+\.\d+/ ) {
                $temp_3 = sprintf("%0.3f", $temp_3) || '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tvolts and temp:$temp_1 $temp_2 $temp_3") if $opt_v;
            print FILE "\t\"upsvolts\":$temp_1,\n";
            print FILE "\t\"primaryvolts\":$temp_2,\n";
            print FILE "\t\"degc\":$temp_3,\n";

            # Baler config options
            $line++;
            if ( $text[$line] =~ /^baler cfg options:\s+(.+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tcfg:$temp_1") if $opt_v;
            print FILE "\t\"cfg\":\"$temp_1\",\n";

            # Baler cpu speed
            $line++;
            if ( $text[$line] =~ /^cpu speed\s+(.+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tcpu:$temp_1") if $opt_v;
            if ( $temp_1 =~ /\d+/ ) {
                $temp_1 = sprintf("%0d", $temp_1) || '"-"';
            }
            print FILE "\t\"cpu\":$temp_1,\n";

            # Baler mseed records
            $line++;
            if ( $text[$line] =~ /^mseed record generator at (\d+) and last flush at (\d+)$/ ) {
                $temp_1 = $1;
                $temp_2 = $2;
            } else {
                $temp_1 = '"-"';
                $temp_2 = '"-"';
            }
            if ( $temp_1 =~ /\d+/ ) {
                $temp_1 = sprintf("%0d", $temp_1) || '"-"';
            }
            if ( $temp_2 =~ /\d+/ ) {
                $temp_2 = sprintf("%0d", $temp_2) || '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tmseed:$temp_1 $temp_2") if $opt_v;
            print FILE "\t\"record_generator\":$temp_1,\n";
            print FILE "\t\"last_flush\":$temp_2,\n";

            # Baler records
            $line += 2;
            if ( $text[$line] =~ /^routing turnons=\d+\s+primary records written=(\d+)\s+secondary records written=(\d+)$/ ) {
                $temp_1 = $1;
                $temp_2 = $2;
            } else  {
                $temp_1 = '"-"';
                $temp_2 = '"-"';
            }
            if ( $temp_1 =~ /\d+/ ) {
                $temp_1 = sprintf("%0d", $temp_1) || '"-"';
            }
            if ( $temp_2 =~ /\d+/ ) {
                $temp_2 = sprintf("%0d", $temp_2) || '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\trecords:$temp_1 $temp_2") if $opt_v;
            print FILE "\t\"records_primary\":$temp_1,\n";
            print FILE "\t\"records_secondary\":$temp_2,\n";

            # Baler last file
            $line++;
            if ( $text[$line] =~ /^media last write time: (.+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tlast_file_time:$temp_1") if $opt_v;
            print FILE "\t\"last_file_time\":\"$temp_1\",\n";
            $line++;
            if ( $text[$line] =~ /^last media file written: (.+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tlast_file:$temp_1") if $opt_v;
            @temp_array =  split '/', $temp_1;
            if ( $temp_array[-1] =~ /\S+/ ) {
                $temp_1 = $temp_array[-1];
            }
            else {
                $temp_1 = join '/', @temp_array;
            }
            print FILE "\t\"last_file\":\"$temp_1\",\n";

            # Q330 connection
            $line++;
            if ( $text[$line] =~ /^(\S+) Q330 connection$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq330:$temp_1") if $opt_v;
            print FILE "\t\"q330_connection\":\"$temp_1\",\n";

            # Baler proxy port
            $line += 2;
            if ( $text[$line] =~ /^proxy base port:\s+(\d+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tproxy_port:$temp_1") if $opt_v;
            print FILE "\t\"proxy_port\":\"$temp_1\",\n";

            # Baler public IP
            $line++;
            if ( $text[$line] =~ /^public ip discovered:\s+(\S+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_v;
            elog_notify("$temp_sta:\tpublic_ip:$temp_1") if $opt_v;
            print FILE "\t\"public_ip\":\"$temp_1\",\n";

            # Baler mac
            $line += 11;
            if ( $text[$line] =~ /HWaddr\s+(\S+)\s*$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tmac:$temp_1") if $opt_v;
            print FILE "\t\"mac\":\"$temp_1\",\n";

#}}}
        }
        else {
            elog_complain("Cannot find section for 'Baler Information'");
        }

        #
        # Look for "Q330 Information" section
        #
        for ($line=0; $line < scalar @text; $line++){
            last if $text[$line] =~ m/^<H4>Q330 Information<\/H4>$/;
        }

        if ($line < scalar @text ) {
#{{{
            # Q330 last boot
            for ($line=0; $line < scalar @text; $line++){
                last if $text[$line] =~ m/^Time of Last Boot:.*$/;
            }
            if ( $text[$line] =~ /^Time of Last Boot:\s+(.*)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq33o_last_boot:$temp_1") if $opt_v;
            print FILE "\t\"q330_last_boot\":\"$temp_1\",\n";

            # Q330 total boots
            $line++;
            if ( $text[$line] =~ /^Total Number of Boots:\s+(\d+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            if ( $temp_1 =~ /\d+/ ) {
                $temp_1 = sprintf("%0d", $temp_1) || '"-"';
            }
            else {
                $temp_1 = '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq330_total_boots:$temp_1") if $opt_v;
            print FILE "\t\"q330_total_boots\":$temp_1,\n";

            # Q330 last sync
            $line++;
            if ( $text[$line] =~ /^Time of Last Re-Sync:\s+(.*)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq330_last_sync:$temp_1") if $opt_v;
            print FILE "\t\"q330_last_sync\":\"$temp_1\",\n";

            # Q330 total syncs
            $line++;
            if ( $text[$line] =~ /^Total Number of Re-Syncs:\s+(\d+)$/ ) {
                $temp_1 = $1;
            } else {
                $temp_1 = '-';
            }
            if ( $temp_1 =~ /\d+/ ) {
                $temp_1 = sprintf("%0d", $temp_1) || '"-"';
            }
            else {
                $temp_1 = '"-"';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq330_total_syncs:$temp_1") if $opt_v;
            print FILE "\t\"q330_total_syncs\":$temp_1,\n";

            # Q330 calibration
            $line += 53;
            if ( $text[$line] =~ /^\s+1:(\S+), (\S+)\s+2:(\S+), (\S+)\s+3:(\S+), (\S+)\s+$/ ) {
                $temp_1 = $1;
                $temp_2 = $2;
                $temp_3 = $3;
                $temp_4 = $4;
                $temp_5 = $5;
                $temp_6 = $6;
            } else {
                $temp_1 = '-';
                $temp_2 = '-';
                $temp_3 = '-';
                $temp_4 = '-';
                $temp_5 = '-';
                $temp_6 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq330_calib: 1)$temp_1,$temp_2 2)$temp_3,$temp_4 3)$temp_5,$temp_6") if $opt_v;
            print FILE "\t\"q330_calib_1_v\":\"$temp_1\",\n";
            print FILE "\t\"q330_calib_1_r\":\"$temp_2\",\n";
            print FILE "\t\"q330_calib_2_v\":\"$temp_3\",\n";
            print FILE "\t\"q330_calib_2_r\":\"$temp_4\",\n";
            print FILE "\t\"q330_calib_3_v\":\"$temp_5\",\n";
            print FILE "\t\"q330_calib_3_r\":\"$temp_6\",\n";

            $line++;
            if( $text[$line] =~ /^\s+4:(\S+), (\S+)\s+5:(\S+), (\S+)\s+6:(\S+), (\S+)\s+$/ ){
                $temp_1 = $1;
                $temp_2 = $2;
                $temp_3 = $3;
                $temp_4 = $4;
                $temp_5 = $5;
                $temp_6 = $6;
            } else {
                $temp_1 = '-';
                $temp_2 = '-';
                $temp_3 = '-';
                $temp_4 = '-';
                $temp_5 = '-';
                $temp_6 = '-';
            }
            elog_notify("$temp_sta:\t$text[$line]") if $opt_d;
            elog_notify("$temp_sta:\tq330_calib: 4)$temp_1,$temp_2 5)$temp_3,$temp_4 6)$temp_5,$temp_6") if $opt_v;
            print FILE "\t\"q330_calib_4_v\":\"$temp_1\",\n";
            print FILE "\t\"q330_calib_4_r\":\"$temp_2\",\n";
            print FILE "\t\"q330_calib_5_v\":\"$temp_3\",\n";
            print FILE "\t\"q330_calib_5_r\":\"$temp_4\",\n";
            print FILE "\t\"q330_calib_6_v\":\"$temp_5\",\n";
            print FILE "\t\"q330_calib_6_r\":\"$temp_6\",\n";
#}}}
        }
        else {
            elog_complain("Cannot find section for 'Q330 Information'");
        }

        #
        # Look for "EP Information" section
        #
        for ($line=0; $line < scalar @text; $line++){
            last if $text[$line] =~ m/^<H4>Environmental Processor Information<\/H4>$/;
        }

        if ($line < scalar @text ) {
#{{{
            # Environmental Processor Info 
            $line += 3;
            $text[$line] =~ /^MEMS Temperature.*:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => mems_temp:$1") if $opt_v;
            print FILE "\t\"mems_temp\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Humidity.*:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => humidity:$1") if $opt_v;
            print FILE "\t\"humidity\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^MEMS Pressure.*:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => pressure:$1") if $opt_v;
            print FILE "\t\"pressure\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Analog Input 1:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => analog_1:$1") if $opt_v;
            print FILE "\t\"analog_1\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Analog Input 2:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => analog_2:$1") if $opt_v;
            print FILE "\t\"analog_2\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Analog Input 3:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => analog_3:$1") if $opt_v;
            print FILE "\t\"analog_3\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^EP Input Voltage:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_voltage:$1") if $opt_v;
            print FILE "\t\"ep_voltage\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Secs Since EP Boot:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_secs_boot:$1") if $opt_v;
            print FILE "\t\"ep_secs_boot\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Secs Since EP Re-Sync:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_secs_sync:$1") if $opt_v;
            print FILE "\t\"ep_secs_sync\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Re-Sync Count:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_sync:$1") if $opt_v;
            print FILE "\t\"ep_sync\":\"$1\",\n";

            $line += 3;
            $text[$line] =~ /^EP Time Error:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_time_error:$1") if $opt_v;
            print FILE "\t\"ep_time_error\":\"$1\",\n";

            $line += 5;
            $text[$line] =~ /^SDI Devs, Aux I\/O:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_sdi:$1") if $opt_v;
            print FILE "\t\"ep_sdi\":\"$1\",\n";

            $line += 2;
            $text[$line] =~ /^Processor ID:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_id:$1") if $opt_v;
            print FILE "\t\"ep_id\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Models:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_models:$1") if $opt_v;
            print FILE "\t\"ep_models\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Versions.+:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => ep_version:$1") if $opt_v;
            print FILE "\t\"ep_version\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Base S\/N:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => base_serial:$1") if $opt_v;
            print FILE "\t\"base_serial\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^ADC S\/N:\s+(\S+)\s*$/;
            elog_notify("$temp_sta:\t$text[$line] => adc_serial:$1") if $opt_v;
            print FILE "\t\"adc_serial\":\"$1\",\n";
#}}}
        }
        else {
            elog_complain("Cannot find section for 'Environmental Processor Information'");
        }

        #
        # Look for "Baler-Q330 Connection Status" section
        #
        for ($line=0; $line < scalar @text; $line++){
            last if $text[$line] =~ m/^<H4>Baler-Q330 Connection Status<\/H4>$/;
        }

        if ($line < scalar @text ) {
#{{{
            # Baler-Q330 Connection Statue
            $line += 2;
            $text[$line] =~ /^Last Data Received:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => baler-q330_last_data:$1") if $opt_v;
            print FILE "\t\"baler-q330_last_data\":\"$1\",\n";

            $line += 7;
            $text[$line] =~ /^Time Connected:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => baler-q330_time_con:$1") if $opt_v;
            print FILE "\t\"baler-q330_time_con\":\"$1\",\n";

            $line += 2;
            $text[$line] =~ /^Total Data Gaps:\s+(.+)*$/;
            elog_notify("$temp_sta:\t$text[$line] => baler-q330_data_gaps:$1") if $opt_v;
            print FILE "\t\"baler-q330_data_gaps\":\"$1\",\n";
#}}}
        }
        else {
            elog_complain("Cannot find section for 'Environmental Processor Information'");
        }

        #
        # Look for "Extended Media Identification" section
        #
        for ($line=0; $line < scalar @text; $line++){
            last if $text[$line] =~ m/^<H4>Extended Media Identification<\/H4>$/;
        }

        if ($line < scalar @text ) {
#{{{
            $line += 3;
            $text[$line] =~ /^ Vendor identification:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_1_vendor_id:$1") if $opt_v;
            print FILE "\t\"media_1_vendor_id\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^ Product identification:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_1_product_id:$1") if $opt_v;
            print FILE "\t\"media_1_product_id\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^ Product revision level:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_1_product_revision:$1") if $opt_v;
            print FILE "\t\"media_1_product_revision\":\"$1\",\n";

            $line += 2;
            $text[$line] =~ /^\s+Vendor:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_1_vendor:$1") if $opt_v;
            print FILE "\t\"media_1_vendor\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^\s+Product:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_1_product:$1") if $opt_v;
            print FILE "\t\"media_1_product\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Serial Number:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_1_serial:$1") if $opt_v;
            print FILE "\t\"media_1_serial\":\"$1\",\n";

            $line += 2;
            $text[$line] =~ /^ Vendor identification:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_2_vendor_id:$1") if $opt_v;
            print FILE "\t\"media_2_vendor_id\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^ Product identification:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_2_product_id:$1") if $opt_v;
            print FILE "\t\"media_2_product_id\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^ Product revision level:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_2_product_revision:$1") if $opt_v;
            print FILE "\t\"media_2_product_revision\":\"$1\",\n";

            $line += 2;
            $text[$line] =~ /^\s+Vendor:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_2_vendor:$1") if $opt_v;
            print FILE "\t\"media_2_vendor\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^\s+Product:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_2_product:$1") if $opt_v;
            print FILE "\t\"media_2_product\":\"$1\",\n";

            $line++;
            $text[$line] =~ /^Serial Number:\s+(.+)$/;
            elog_notify("$temp_sta:\t$text[$line] => media_2_serial:$1") if $opt_v;
            print FILE "\t\"media_2_serial\":\"$1\",\n";
#}}}
        }
        else {
            elog_complain("Cannot find section for 'Extended Media Identification'");
        }
        #
        # Finish JSON file here
        #
        print FILE "\t\"page\":\"$url\"\n";
        print FILE "}\n";
        close FILE;

        #
        # Read new JSON file and copy data to global file
        #
        open FILE, "<", $json or elog_die("Could not read file [$json] :$!");
        print TEMPGLOBAL "\n\"$temp_sta\":";
        print TEMPGLOBAL $_ foreach (<FILE>);
        close FILE;

        #
        # Dump raw html into a file if we have one
        #
        elog_notify("$temp_sta:\tPrepare RAW file: $raw") if $opt_v;
        unlink $raw if -e $raw;
        open FILE, ">", $raw or elog_die("Could not open file [$raw] :$!");
        print FILE $content;
        close FILE;


#}}}
    } else {
#{{{
        #
        # Read old JSON file
        #
        elog_notify("$temp_sta:\tTry to read old JSON file: $json") if $opt_v;
        if ( -e $json ){
            open FILE, "<", $json or elog_die("Could not read file [$json] :$!");
            foreach (<FILE>){
                chomp;
                print TEMPGLOBAL "\n$_\n";
            }
            close FILE;
        } else {
            #
            # Set to NULL values
            #
            print TEMPGLOBAL "\n\"$temp_sta\":{";
            print TEMPGLOBAL "\t\"station\":\"$temp_sta\",\n";
            print TEMPGLOBAL "\t\"updated\":\"$updated\",\n";
            print TEMPGLOBAL "\t\"updated_epoch\":\"".str2epoch($updated)."\",\n";
            print TEMPGLOBAL "\t\"public_ip\":\"$public_ip\",\n";
            print TEMPGLOBAL "\t\"page\":\"$url\"\n";
            print TEMPGLOBAL "}\n";
        }
#}}}
    }

    #
    # Write error file if needed
    #
    if ( $new_problems or $old_problems ) {
        open FILE, ">", $error or elog_die("Could not open file [$error] :$!");
        print FILE $new_problems;
        print FILE $old_problems;
        close FILE;
    }

#}}}
}

print TEMPGLOBAL "}\n";
close TEMPGLOBAL;
unlink $global_json if -e $global_json;
move($global_json_temp, $global_json);

sub get_stations_from_db {
#{{{
    my ($dlsta,$vnet,$net,$sta,$time,$endtime);
    my %sta_hash;
    my (@active,@db_1);
    my $nrecords;
    my $ip;
    
    #
    # Get stations with baler44s
    #
    elog_debug("dbsubset ( stablaler.model =~ /Packet Baler44/)") if $opt_d;
    @db_1 = dbsubset ( @db_sta, "stabaler.model =~ /PacketBaler44/ && endtime == NULL");

    $nrecords = dbquery(@db_1,dbRECORD_COUNT) or elog_die("No records to work with after dbsubset()");
    elog_debug("dbsubset => nrecords = $nrecords") if $opt_d;

    
    for ( $db_1[3] = 0 ; $db_1[3] < $nrecords ; $db_1[3]++ ) {

        ($dlsta,$net,$sta) = dbgetv(@db_1, qw/dlsta net sta/);
    
        elog_debug("[$sta] [$net] [$dlsta]") if $opt_d;

        $sta_hash{$sta}{dlsta}      = $dlsta;
        $sta_hash{$sta}{net}        = $net;
        $sta_hash{$sta}{status}     = 'Decom';
        $sta_hash{$sta}{ip}         = 0; 

    }

    #
    # Build JSON file in directory with list of all valid stations
    #
    elog_debug("Prepare JSON file: $out_dir/baler44_status.json") if $opt_d;

    unlink "$out_dir/baler44_status.json" if -e "$out_dir/baler44_status.json";

    open FILE, ">", "$out_dir/baler44_status.json" or elog_die("Could not create file [$out_dir/baler44_status.json] :$!");

    print FILE "{\n";
    print FILE "\t\"updated\":\"". epoch2str(now(),'%Y-%m-%d %H:%M:%S') . "\",\n";
    print FILE "\t\"stations\":[\"". join('","', keys %sta_hash) . "\"]\n";
    print FILE "}\n";

    close FILE;

    #
    # Subset stations
    #
    foreach $sta (sort keys %sta_hash) {

        if ( $opt_s ) {
            if ( $sta !~ /($opt_s)/ ) {
                elog_debug("Remove $sta from list") if $opt_d;
                delete $sta_hash{$sta};
            }
        }
        if ( $opt_r ) {
            if ( $sta =~ /($opt_s)/ ) {
                elog_debug("Remove $sta from list") if $opt_d;
                delete $sta_hash{$sta};
            }
        }
    }

    elog_die("No stations to work with after subset(s:[$opt_s] r:[$opt_r])") unless scalar keys %sta_hash;

    foreach $sta (sort keys %sta_hash) {

        $dlsta = $sta_hash{$sta}{dlsta};
        $net   = $sta_hash{$sta}{net};

        elog_debug("Test status and ip of [$sta] ") if $opt_d;

        #
        # Test if station is active
        #
        $sta_hash{$sta}{status} = 'Active' if ( dbfind(@db_on, "sta =~ /$sta/ && snet =~ /$net/ && endtime == NULL", -1)>= 0);

        next if $sta_hash{$sta}{status} eq 'Decom';

        elog_debug("$sta set to 'Active'") if $opt_d;

        push @active, $sta;

        #
        # Get ip for station
        #
        $db_ip[3] = dbfind ( @db_ip, " dlsta =~ /$dlsta/ && endtime == NULL",-1);

        if ( $db_ip[3] >= 0 ) {

            $ip = dbgetv(@db_ip, qw/inp/);

            elog_debug("$sta inp=>[$ip] ") if $opt_d;

            # regex for the ip
            $ip =~ /([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})/;
            problem("Failed grep on IP $dbmaster.stabaler{inp}->(ip'$ip',dlsta'$dlsta')") unless $1;
            $sta_hash{$sta}{ip} = $1 if $1; 

        }

        elog_notify("$dlsta $sta_hash{$sta}{status} $sta_hash{$sta}{ip}") if $opt_v;

    }

    #
    # Close database pointers
    #
    eval { dbclose(@db_sta); };
    eval { dbclose(@db_ip);  };
    eval { dbclose(@db_on);  };
    eval { dbclose(@db); };


    return \%sta_hash;
#}}}
}

sub do_GET {
#{{{
    my $sta = shift;
    my $url = shift;
    my ($browser, $resp);

    elog_debug("$sta:\tLWP::UserAgent->new") if $opt_d;
    $browser = LWP::UserAgent->new;

    elog_notify("$sta:\tLWP::UserAgent->timeout(60)") if $opt_v;
    $resp = $browser->timeout(60);

    elog_notify("$sta:\tLWP::UserAgent->get($url)") if $opt_v;
    $resp = $browser->get($url);

    elog_notify("$sta:\tLWP::UserAgent problem creating object $url") unless $resp;
    return unless $resp; 

    elog_notify("$sta:\t($url)is_success->(" . $resp->is_success . ")") if $opt_v;
    return ($resp->content, $resp->status_line, $resp->is_success);

#}}}
}

sub table_check {
#{{{
    my $db = shift;

    elog_debug("Verify Database: ".dbquery(@$db,"dbDATABASE_NAME") ) if $opt_d;

    elog_die( dbquery(@$db,"dbTABLE_NAME")." table not available.") unless dbquery(@$db,"dbTABLE_PRESENT");

    elog_debug("\t".dbquery(@$db,"dbDATABASE_NAME")."{ ".dbquery(@$db,"dbTABLE_NAME")." }: --> OK") if $opt_d;

#}}}
}

__END__
#{{{
=pod

=head1 NAME

read_baler44_status_page - Sync a remote baler status page to local directory

=head1 SYNOPSIS

rsync_baler [-h] [-v] [-f date] [-s sta_regex] [-r sta_regex] [-m email,email] directory database

=head1 ARGUMENTS

Recognized flags:

=over 2

=item B<-h> 

Help. Produce this documentation

=item B<-v> 

Produce verbose output while running

=item B<-d> 

Produce debuggin output while running

=item B<-s regex>

Select station regex. ('STA1|STA2' or 'A...|B.*')

=item B<-r regex>

Reject station regex. ('STA1|STA2' or 'A...|B.*')

=item B<-m email,email,email>

List of emails to send output

=back

=head1 DESCRIPTION

This script  creates and maintains a local directory with the contents
of the status.html page on the baler44 http server.
The script is simple and may fail if used outside ANF-TA installation. 

=head1 AUTHOR

Juan C. Reyes <reyes@ucsd.edu>

=head1 SEE ALSO

Perl(1).

=cut
#}}}
