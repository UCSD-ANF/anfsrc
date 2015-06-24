#!/usr/bin/env python

"""
Print a configuration file for the orb2rrdc script.

USAGE:
    ./create_rrd_config.py
"""

def rra_string(RRA,types):
    string = ''
    for twin in RRA:
        for cf in types:
            string += 'RRA:%s:0.5:%s:%s ' % (cf, RRA[twin],twin)
    return string

#
# Not using some of the values that I see on the q3302orb conf file
# Some may report strings.
#
#ax0     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 0 (first conversion)
#ax1     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 1 (second conversion)
#ax2     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 2 (third conversion)
#ax3     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 3 (fourth conversion)
#ax4     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 4 (fifth conversion)
#ax5     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 5 (sixth conversion)
#ax6     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 6 (seventh conversion)
#ax7     GAUGE:&status_heartbeat_sec:U:U &all_rra       # auxiliary channel 7 (eighth conversion)
#s0t     GAUGE:&status_heartbeat_sec:U:U &all_rra       # temperature for seismometer 0 (reported every 10 seconds)
#s1t     GAUGE:&status_heartbeat_sec:U:U &all_rra       # temperature for seismometer 1 (reported every 10 seconds)
#cala    GAUGE:&status_heartbeat_sec:U:U &all_rra       # calibration abort occurred flag (reported as needed)
#cals    GAUGE:&status_heartbeat_sec:U:U &all_rra       # calibration status (reported as needed)
#spv     GAUGE:&status_heartbeat_sec:U:U &all_rra       # analog unregulated positive supply voltage (reported every 10 seconds)
#spn     GAUGE:&status_heartbeat_sec:U:U &all_rra       # analog unregulated negative supply voltage (currently not implemented)
#sc0     GAUGE:&status_heartbeat_sec:U:U &all_rra       # data from serial interface 0 (configurable report interval)
#sc1     GAUGE:&status_heartbeat_sec:U:U &all_rra       # data from serial interface 1 (configurable report interval)
#sc2     GAUGE:&status_heartbeat_sec:U:U &all_rra       # data from serial interface 2 (configurable report interval)
#sc3     GAUGE:&status_heartbeat_sec:U:U &all_rra       # data from serial interface 3 (configurable report interval)
#gps     GAUGE:&status_heartbeat_sec:U:U &all_rra       # clock (GPS) quality (reported every 1 second)
#sp      GAUGE:&status_heartbeat_sec:U:U &all_rra       # main system spare analog input (reported every 10 seconds)
#stp     GAUGE:&status_heartbeat_sec:U:U &all_rra       # main system status port value (configurable reporting interval)
#opt     GAUGE:&status_heartbeat_sec:U:U &all_rra       # main system opto inputs (reported every 10 seconds)
#gpss    GAUGE:&status_heartbeat_sec:U:U &all_rra       # GPS status (reported as needed)
#gpsc    GAUGE:&status_heartbeat_sec:U:U &all_rra       # reason for GPS cold-start (reported as needed)
#cnpp    GAUGE:&status_heartbeat_sec:U:U &all_rra       # CNP error port number (reported as needed)
#cnpc    GAUGE:&status_heartbeat_sec:U:U &all_rra       # CNP error code number (reported as needed)
#slpc    GAUGE:&status_heartbeat_sec:U:U &all_rra       # slave processor error code number (reported as needed)
#dig     GAUGE:&status_heartbeat_sec:U:U &all_rra       # digitizer phase change (reported as needed)
#digw    GAUGE:&status_heartbeat_sec:U:U &all_rra       # reason for digitizer phase change (reported as needed)
#bu      GAUGE:&status_heartbeat_sec:U:U &all_rra       # saving daily configuration backup flag (reported as needed)
#rec     GAUGE:&status_heartbeat_sec:U:U &all_rra       # recording window change (reported as needed)
#leap    GAUGE:&status_heartbeat_sec:U:U &all_rra       # leap second detected flag (reported as needed)
#powp    GAUGE:&status_heartbeat_sec:U:U &all_rra       # power supply phase change (reported as needed)
#anlf    GAUGE:&status_heartbeat_sec:U:U &all_rra       # analog fault (reported as needed)
#cale    GAUGE:&status_heartbeat_sec:U:U &all_rra       # calibration error (reported as needed)
#plld    GAUGE:&status_heartbeat_sec:U:U &all_rra       # PLL drift over last 10 minutes (reported as needed)
#drf     GAUGE:&status_heartbeat_sec:U:U &all_rra       # time offset for phase out of range, Q330 will re-sync (reported as needed)

dls_vars = """
    acok    GAUGE:&status_heartbeat_sec:0:1         &all_rra         # Reserve battery status
    ins1    GAUGE:&status_heartbeat_sec:0:1         &all_rra         # Pump existence
    ins2    GAUGE:&status_heartbeat_sec:0:1         &all_rra         # Pump activity
    api     GAUGE:&status_heartbeat_sec:0:1         &all_rra         # Wiring error
    ti      GAUGE:&status_heartbeat_sec:0:1         &all_rra         # Baler44 to VIE connection status
    btmp    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Modem board temperature
    ecio    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Ec/I0 (Ratio of pilot energy to total power spectral density)
    netc    GAUGE:&status_heartbeat_sec:U:U         &all_rra
    plos    GAUGE:&status_heartbeat_sec:0:100       &all_rra
    prta    GAUGE:&status_heartbeat_sec:U:U         &all_rra
    pwin    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Board power in
    rset    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # System resets
    rssi    GAUGE:&status_heartbeat_sec:-125:-50    &all_rra
    dv      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # main system voltage (reported every 10 seconds)
    dt      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # main system temperature (reported every 10 seconds)
    da      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # main system current (reported every 10 seconds)
    aa      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # antenna current (reported every 10 seconds)
    vco     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # voltage controlled oscillator value (reported every 10 seconds)
    pb      GAUGE:&status_heartbeat_sec:0:100       &all_rra       # percentage packet buffer full (reported every 10 seconds)
    clq     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # clock phase lock loop status (reported every 1 second)
    clt     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # time since GPS lock was lost (reported every 1 second)
    cld     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # clock drift (reported every 1 second)
    lcq     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # clock quality percentage (reported every 1 second)
    m0      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 0 (reported every 10 seconds)
    m1      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 1 (reported every 10 seconds)
    m2      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 2 (reported every 10 seconds)
    m3      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 3 (reported every 10 seconds)
    m4      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 4 (reported every 10 seconds)
    m5      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 5 (reported every 10 seconds)
    bt      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery temperature (configurable reporting interval)
    bc      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery capacity (configurable reporting interval)
    bd      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery depth of discharge (configurable reporting interval)
    bg      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery charging phase change (configurable reporting interval)
    bv      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery voltage (configurable reporting interval)
    iv      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery input voltage (configurable reporting interval)
    ba      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # battery current (configurable reporting interval)
    dr      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # current total input+output data rate - bits per second
    thr     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # current throttle setting - bits per second
    ce      GAUGE:&status_heartbeat_sec:0:100       &all_rra       # overall communications efficiency - percent
    dg      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # data gaps - second
    rtm     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # current run time - second
    dlt     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # current data latency - second
    pkp     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of packets processed
    pkse    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of packets with wrong sizes
    pkce    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of packets with checksum errors
    br24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of bytes read in last 24 hours
    bw24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of bytes written in last 24 hours
    gp24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of data gaps in last 24 hours
    gp1     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of data gaps in last 1 hour
    nl24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of comm link cycles in last 24 hours
    nr24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of Q330 reboots in last 24 hours
    np24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of POCs received in last 24 hours
    ni24    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # total number of datalogger ip-address changes in last 24 hours
    tput    GAUGE:&status_heartbeat_sec:U:U         &all_rra       # ration of seconds read to real-time clock
    pbr     GAUGE:&status_heartbeat_sec:0:100       &all_rra       # logical port buffer percent full from real-time status
"""

heartbeat = '1h'

step = '1m'

prelim_rra = {
    '2d': '1m',
    '2m': '40m',
}

rra = {
    '2d': '1m',
    '1m': '20m',
    '1y': '4h',
    '2y': '8h'
}

ALL_RRA = ['MIN', 'MAX', 'AVERAGE']
MAX_RRA = ['MAX']
MINMAX_RRA = ['MIN','MAX']


rra_all =  rra_string(rra,ALL_RRA)
rra_max =  rra_string(rra,MAX_RRA)
rra_minmax =  rra_string(rra,MINMAX_RRA)

prelim_rra_all =  rra_string(prelim_rra,ALL_RRA)
prelim_rra_max =  rra_string(prelim_rra,MAX_RRA)
prelim_rra_minmax =  rra_string(prelim_rra,MINMAX_RRA)


print 'rrdtool        /usr/bin/rrdtool'
print '\n'
print 'status_stepsize_sec    %s' % step
print '\n'
print 'rrdfile_pattern    %{net}/%{sta}/%{net}_%{sta}_%{rrdvar}.rrd'
print '\n'
print 'default_network &ref(site,default_seed_network)'
print '\n'
print 'status_heartbeat_sec     %s' %  heartbeat
print '\n'
print 'all_rra %s' %  rra_all
print '\n'
print 'max_rra %s' %  rra_max
print '\n'
print 'minmax_rra %s' %  rra_minmax
print '\n'
print 'prelim_all_rra %s' %  prelim_rra_all
print '\n'
print 'prelim_max_rra %s' %  prelim_rra_max
print '\n'
print 'prelim_minmax_rra %s' %  prelim_rra_minmax
print '\n'
print 'dls_vars &Tbl{ %s }' %  dls_vars


