# 
#   Perl script to produce Q330-compatible NMEA-0183 time telegrams 
#          based on the PC system clock. 
# 
#      We assume that NTP is used to discipline the PC clock. 
# 
#      For timing the Q330HR need also a 1pps signal which has 
#           to be dealt with separately. 
# 
#      Every second we generate 6 telegrams: 
#           one $GPZDA, $GPGGA, $GPGSA and three $GPGSV 
#         ( For the meaning of these telegrams see: 
#              http://home.mira.net/~gnb/gps/nmea.html ) 
# 
#                          Rudolf Widmer-Schnidrig, BFO, 13.3.2008 

#
# Modifications by Steve Foley, 14 Jan 2010
#  Changes include:
#   * Serial port parameter tweaks
#   * NTP lock check
#   * Tweaks to run under Antelope on a Marmot
#
# For best results on a broadcast NTP connection, the NTP daemon may want
# the following config added to the ntp.conf file:
#   - "broadcastclient" -- for listening to broadcasts.
#   - "driftfile <path to driftfile>"
#   - "tinker panic 1500" -- in case of a big jump
#   - "server <IP of server to listen to>"
# And the ntpd startup options to include:
#   - "-g" to set time to any value at startup

# 
$\ = "\n";              # set output record separator 
# 
# load Perl module HiRes for high resolution time manipulation. 
# 
use Time::HiRes qw( usleep gettimeofday ); 

# Serial port constants
$SERIAL_PORT = "/dev/ttyS3";
$SERIAL_BAUD_RATE = "4800";
$SERIAL_MODE = "raw";
$SERIAL_BITS = "cs8";
$STTY = "/bin/stty";
$NTPQ = "/usr/bin/ntpq";

# 
require "flush.pl";         # Perl module to permit instant flushing of buffers 

MAIN:
{
    &setup_serial_port();
# 
# station coordinates for BFO: these will be communicated to the Q330HR 
#    and might show up in some SEED header. Change as needed. 
# 
      $lat  = "4819.7681";  # 48deg 19.7681'N 
      $NS   = "N"; 
      $lon  = "00819.3761"; #  8deg 19.3761'E 
      $EW   = "E"; 
      $elev = "665.9";      # elevation in meters 
      $gpgga = sprintf("GPGGA,,%s,%s,%s,%s,1,08,,%s,M,,M,,",$lat,$NS,$lon,$EW,$elev); 
      $line0 = sprintf("\$%s*%02X",$gpgga,&CHECKSUM($gpgga)); 
# 
#  Enter some arbitrary GPS satelite constellation. 
#    View the constellation under Willard -> Status -> GPS Satellites 
#         Here: Polaris and Big Dipper constellation 
# 
      $gpgsa =sprintf("GPGSA,A,3,1,2,3,4,5,6,7,8,,,,,,,"); 
      $line1 =sprintf("\$%s*%02X",$gpgsa,&CHECKSUM($gpgsa)); 
      $gpgsv =sprintf("GPGSV,3,1,9,01,47,0,45,02,61,45,26,03,62,56,10,04,54,59,26"); 
      $line2 =sprintf("\$%s*%02X",$gpgsv,&CHECKSUM($gpgsv)); 
      $gpgsv =sprintf("GPGSV,3,2,9,05,52,52,26,06,46,51,26,07,42,50,26,08,37,54,26"); 
      $line3 =sprintf("\$%s*%02X",$gpgsv,&CHECKSUM($gpgsv)); 
      $gpgsv =sprintf("GPGSV,3,3,9,09,62,56,26"); 
      $line4 =sprintf("\$%s*%02X",$gpgsv,&CHECKSUM($gpgsv)); 
# 
#  work through this while loop once every second 
# 
while (1) 
 { 
#
# Make sure we have a good sync from the last pause before we send a string
#
 if (&check_sync)
  {
  
# get time of day 
      $t0 = [gettimeofday]; 
      ($seconds, $microseconds) = gettimeofday; 
##      printf("Ready to go to sleep at %d usec.\n",$microseconds); 
# 
#  send next time telegram 50ms after the full second 
# 
      $sleep_for = 1000* (1000 + 15) - $microseconds; 
# 
#  sleep now 
# 
      usleep ($sleep_for); 
# 
#  did you wake up at the right time? 
# 
#      $t0 = [gettimeofday]; 
#      ($seconds, $microseconds) = gettimeofday; 
##      printf("Waking up %d usec after the full second.\n",$microseconds); 

# 
#  get UT time from PC clock and generate new telegram 
# 

      ($sec,$mn,$hr,$day,$mon,$yr,$wday,$jday,$dst) = gmtime; 
      $mon++; # NMEA months are 1-based, perl are 0-based
      $yr = $yr+1900; # y2k
# 
#   manipulate time string just for testing 
# 
      $ss  = ((3600 * $hr) + 60 * $mn ) + $sec; 
#     $ss  = $ss + 10; 
      $hr  = int( $ss / 3600 ); 
      $ss  = $ss - 3600*$hr; 
      $mn  = int( $ss / 60 ); 
      $ss  = $ss - 60*$mn; 
      $now = sprintf("%02d%02d%02d.00",$hr,$mn,$ss); 
      $gpzda = sprintf("GPZDA,%s,%02d,%02d,%4d,00,00",$now,$day,$mon,$yr); 
      printf SERIAL ("\$%s*%02X\n",$gpzda,&CHECKSUM($gpzda)); 
      printf SERIAL ("%s\n%s\n%s\n%s\n%s",$line0,$line1,$line2,$line3,$line4); 
      &flush(SERIAL);
   }
 }
}
  
# 
#  subroutine to compute checksum of GPS telegram according to NMEA 
# 
sub CHECKSUM { 
      
        local($string) = $_[0]; 
        local($len, $i, $offset, $a); 
        $chksum = 0; 
        $len    = length($string); 
        for ( $i = 1 ; $i <= $len ; $i++ ) 
          { 
            $offset = $i - 1; 
            $a = vec($string, $offset, 8); 
            $chksum = $chksum ^ $a;         #  bitwise XOR operator 
          } 
        return ($chksum); 
       }
    
#
# Check to see if our clock is in sync using the NTPQ program
#   
sub check_sync
{
    my ($line, $sync_status);
    open (NTPQ, "$NTPQ -c rv |");
    $line = <NTPQ>;

    ($sync_status) = ($line =~ /\s(sync_\w*),\s/);

    close (NTPQ); 

    if (($sync_status eq "sync_ntp")
        || ($sync_status eq "sync_pps")
        || ($sync_status eq "sync_other")
        )
    { 
        return 1;
    }
    else
    { 
        return 0;
    }
}

#
# Configure the serial port for auto flush and the correct term parameters
#
sub setup_serial_port
{
    # Make sure we have stty
    (-x $STTY) or die "Cannot find $STTY!\n";

    # make serial port settings here
   !system("$STTY -F $SERIAL_PORT $SERIAL_BAUD_RATE $SERIAL_MODE $SERIAL_BITS")
        or die "Cannot configure $SERIAL_PORT with $STTY: $SERIAL_BAUD_RATE $SERIAL_MODE $SERIAL_BITS !\n";

    # Instead, just turn on autoflush after the nodelay open -saf
    open( SERIAL, ">$SERIAL_PORT") or die " Error while opening $device: $SERIAL_PORT\n";
    select((select(SERIAL), $| = 1)[0]) or die "Cannot set output to autoflush!\n";

}
