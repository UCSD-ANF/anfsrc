"""
Class ParseOrb from db2json script.

Will be loaded into script and 
not called directly.

Juan Reyes
reyes@ucsd.edu

"""

from __main__ import *

def log(message):
    """Format our print commands

    Prepend  a timestamp and the name of the
    script to the log msg.

    """
    curtime = stock.epoch2str(stock.now(),"%d(%j)%H:%M:%S")
    print "%s db2json: %s" % (curtime, message)

class ParseOrb:
    """Parse Orb packets
    
    Methods for grabbing packet from orb
    and parse values out of them.

    """

    def __init__(self, alerts, verbose=False):
        self.alerts = alerts
        self.verbose = verbose

    def get_status(self, orbname, selection_string=False):
        """Open & select orb

        """

        orb_dict = defaultdict(dict)

        if self.verbose:
            log("Orb (%s) operations" % orbname)

        try:
            myorb = orb.orbopen(orbname, 'r')
        except Exception, e:
            sys.exit("\tException in orb_open: %s" % e)

        try:
            sources = myorb.select(selection_string)
        except Exception, e:
            sys.exit("\tException in orb_select: %s" % e)

        if self.verbose:
            log("\t%s sources selected in %s for [%s]" % (sources,orbname,selection_string))

        if sources > 0:
            when, sources = myorb.sources()
            orb_dict = self.parse_orb_sources(sources)

        try:
            myorb.close()
        except Exception, e:
            log("\tException in orbclose: %s" % e)


        return orb_dict


    def parse_orb_sources(self, sources):
        """Parse orb sources

        Return a dictionary

        """

        source_dict = defaultdict(dict)
        for s in sources:

            srcname = s['srcname']
            if self.verbose: log("Got %s" % srcname)

            parts = srcname.split('/')
            if self.verbose: log("parts %s" % parts)

            snet_sta = parts[0].split('_')
            snet = snet_sta[0]
            sta = snet_sta[1]

            latency = stock.now() - s['slatest_time']
            alert, off_on = self.orbstat_alert_level(latency)

            source_dict[sta].update(latency=latency)
            source_dict[sta].update(latency_readable=self.humanize_time(latency))
            source_dict[sta].update(snet=snet)
            source_dict[sta].update(status=off_on)
            source_dict[sta].update(alert=alert)
            source_dict[sta].update(offon=off_on)
            source_dict[sta].update(oldest=s['slatest_time'])
            source_dict[sta].update(latest=s['slatest_time'])
            source_dict[sta].update(soldest_time=stock.epoch2str(s['soldest_time'], "%Y-%m-%d %H:%M:%S"))
            source_dict[sta].update(slatest_time=stock.epoch2str(s['slatest_time'], "%Y-%m-%d %H:%M:%S"))
        return source_dict


    def orbstat_alert_level(self, secs):
        """Determine the alert level

        Get latency in seconds and return status
        """

        if secs >= int(self.alerts['offline']):
            return 'down', 0
        elif secs >= int(self.alerts['warning']):
            return 'warning', 1
        else:
            return 'ok', 1


    def humanize_time(self, secs):
        """Create human readable timestamp

        """

        return stock.strtdelta(secs)
        #secs = round(secs)
        #if secs < 60:
        #    return '%02ds' % (secs)
        #else:
        #    mins,secs = divmod(secs,60)
        #    if mins < 60:
        #        return '%02dm:%02ds' % (mins, secs)
        #    else:
        #        hours,mins = divmod(mins,60)
        #        return '%02dh:%02dm:%02ds' % (hours, mins, secs)


    #def add_orbstat(self, orbstat, sta, qtype=False):
    #    """Return station specific orbstat values

    #    """

    #    orbstat_dict = defaultdict(dict)

    #    if sta in orbstat:
    #        orbstat_dict.update(latency = orbstat[sta]['latency'])
    #        orbstat_dict.update(latest = orbstat[sta]['latest'])
    #        orbstat_dict.update(oldest = orbstat[sta]['oldest'])
    #        orbstat_dict.update(latency_readable = self.humanize_time(orbstat[sta]['latency']))
    #        orbstat_dict.update(alert = orbstat[sta]['alert'])
    #        orbstat_dict.update(status = orbstat[sta]['offon'])
    #        if qtype == 'detail':
    #            orbstat_dict.update(slatest_time = orbstat[sta]['slatest_time'])
    #            orbstat_dict.update(soldest_time = orbstat[sta]['soldest_time'])
    #    else:
    #        orbstat_dict.update(latency = -1)
    #        orbstat_dict.update(alert = 'down')
    #        orbstat_dict.update(status = 0)
    #    return orbstat_dict
