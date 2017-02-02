"""
Print a configuration file for the orb2rrdc script.

USAGE:
    # for pf/st packets
    create_rrd_config

    # for pf/im packets
    create_rrd_config im

All the configuration parameters are hardcoded

"""

def rra_string(days, points_day, total_points, types):
    string = ''
    for d in days:
        rrastep = int( (points_day * d) / total_points ) + 1
        for cf in types:
            string += 'RRA:%s:0.5:%s:%s ' % (cf, rrastep, total_points)
    return string

dls_vars_im = """
    btmp    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Modem board temperature
    ecio    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Ec/I0 (Ratio of pilot energy to total power spectral density)
    netc    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # CDMA network channel
    plos    GAUGE:&status_heartbeat_sec:-1:101      &all_rra    # Percetage of packet loss
    prta    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Round triop average of poing packets millisec
    pwin    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Modem board power in
    rset    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Modem system resets
    rssi    GAUGE:&status_heartbeat_sec:U:U         &all_rra    # Modem recive signal strength
    """

dls_vars_st = """
    acok    GAUGE:&status_heartbeat_sec:-1:2        &all_rra         # OPT = Reserve battery status
    isp1    GAUGE:&status_heartbeat_sec:-1:2        &all_rra         # OPT = Pump existence
    isp2    GAUGE:&status_heartbeat_sec:-1:2        &all_rra         # OPT = Pump activity
    api     GAUGE:&status_heartbeat_sec:-1:2        &all_rra         # OPT = Wiring error
    ti      GAUGE:&status_heartbeat_sec:-1:2        &all_rra         # OPT = Baler44 to VIE connection status
    dv      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # main system voltage (reported every 10 seconds)
    dt      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # main system temperature (reported every 10 seconds)
    da      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # main system current (reported every 10 seconds)
    aa      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # antenna current (reported every 10 seconds)
    vco     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # voltage controlled oscillator value (reported every 10 seconds)
    pb      GAUGE:&status_heartbeat_sec:-1:101       &all_rra       # percentage packet buffer full (reported every 10 seconds)
    clt     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # time since GPS lock was lost (reported every 1 second)
    cld     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # clock drift (reported every 1 second)
    lcq     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # clock quality percentage (reported every 1 second)
    m0      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 0 (reported every 10 seconds)
    m1      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 1 (reported every 10 seconds)
    m2      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 2 (reported every 10 seconds)
    m3      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 3 (reported every 10 seconds)
    m4      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 4 (reported every 10 seconds)
    m5      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # mass position for channel 5 (reported every 10 seconds)
    dr      GAUGE:&status_heartbeat_sec:U:U         &all_rra       # current total input+output data rate - bits per second
    thr     GAUGE:&status_heartbeat_sec:U:U         &all_rra       # current throttle setting - bits per second
    ce      GAUGE:&status_heartbeat_sec:-1:101      &all_rra       # overall communications efficiency - percent
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
    pbr     GAUGE:&status_heartbeat_sec:-1:101      &all_rra       # logical port buffer percent full from real-time status
"""


heartbeat = 600

step = 1

points_per_day = 86400

points_in_total = 3000

dls_vars = dls_vars_st

# number of days
rra = [ 9, 40, 390, 740 ]
prelim_rra =  [ 9, 40 ]

if len(sys.argv) > 1 and sys.argv[1] == 'im':
    heartbeat = 3600
    step = 600

    points_per_day = 240

    points_in_total = 3000

    dls_vars = dls_vars_im
    # need 2days, 1month, 1year and 2years
    # number of days: points/day
    # around 120 per day
    rra = [ 9 , 40, 390, 740 ]
    prelim_rra = [ 9, 40 ]


print 'rrdtool        /usr/bin/rrdtool'
print '\n'
print 'suppress_OK    1'
print '\n'
print 'suppress_egrep  (OK)'
print '\n'
print 'status_stepsize_sec    %s' % step
print '\n'
print 'rrdfile_pattern    %{net}/%{sta}/%{net}_%{sta}_%{rrdvar}.rrd'
print '\n'
print 'default_network &ref(site,default_seed_network)'
print '\n'
print 'status_heartbeat_sec     %s' %  heartbeat
print '\n'

ALL_RRA = ['MIN', 'MAX', 'AVERAGE']
rra_all =  rra_string( rra, points_per_day, points_in_total, ALL_RRA )
prelim_rra_all =  rra_string( prelim_rra, points_per_day, points_in_total, ALL_RRA )


print 'all_rra %s' %  rra_all
print '\n'
print 'prelim_all_rra %s' %  prelim_rra_all
print '\n'
print 'dls_vars &Tbl{ %s }' %  dls_vars


