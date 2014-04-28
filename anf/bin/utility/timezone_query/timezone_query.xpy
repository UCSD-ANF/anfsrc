"""
uses the AskGeo webservice to determine 
the time zone of the event based on 
the event lat-lon.

Typical response from the AskGeo service:

{
    "code":0,
    "message":"ok",
    "data":[
        {"TimeZone":{
            "AskGeoId":3166,
            "IsInside":true,
            "MinDistanceKm":0.0,
            "CurrentOffsetMs":-18000000,
            "ShortName":"CDT",
            "WindowsStandardName":"Central Standard Time",
            "InDstNow":true,
            "TimeZoneId":"America/Chicago"
            }
        }
    ]
}

"""

import os
import urllib2
import json


import antelope.stock as stock


def configure():
    """Read the files with the data 
    and the API keys to use the AskGeo
    modules.
    """
    # {{{ configure

    if os.path.isfile('./locations'):
        list = './locations'
    else:
        sys.exit("File './locations' does not exist, verify README file. Exiting.")

    if os.path.isfile('./AskGeo.keys'):
        keys = './AskGeo.keys'
    else:
        sys.exit("File './AskGeo.keys' does not exist, verify README file. Exiting.")

    # Parse AskGeo API keys
    options = {}
    f = open(keys)
    for line in f:
        print "%s" % line.strip()
        option, value = line.split('=', 1)
        option = option.strip()
        value = value.strip()
        options[option] = value
        print "AskGeo.key %s => %s\n" % (option,value)

    f.close()

    if not options['APP_ID']: sys.exit('Missing APP_ID in .AskGeo.keys file. %s' % options)
    if not options['API_KEY']: sys.exit('Missing APP_KEY in .AskGeo.keys file. %s' % options)
    if not options['SERVICE']: sys.exit('Missing SERVICE in .AskGeo.keys file. %s' % options)


    # Parse events
    events = {}
    f = open(list)
    for line in f:
        print "%s" % line.strip()
        lat, long, time = line.split()
        lat = lat.strip()
        long = long.strip()
        time = time.strip()
        events[time] = (lat,long)
        print "event %s => %s" % (time,events[time])

    f.close()

    return options,events


    # }}}

def main():
    """ Get each event and output the time
    in UTC, Local and Pacific.
    """
    # {{{ main
    options, events = configure()

    SERVICE = options['SERVICE']
    APP_ID = options['APP_ID']
    API_KEY = options['API_KEY']

    for i in sorted(events.iterkeys()):


        url = "%s/%s/%s/query.json?points=%s,%s&databases=TimeZone" % (SERVICE, APP_ID, API_KEY, events[i][0], events[i][1])

        time_str = stock.epoch2str(float(i), "%Y-%m-%d %H:%M:%S")

        try:
            json_page = urllib2.Request(url)
        except urllib2.URLError:
            print urllib2.URLError
        except:
            print "Unknown urllib2 error for url '%s'" % url
        else:
            clean_json   = json.load(urllib2.urlopen(json_page))
            time_zone    = clean_json['data'][0]['TimeZone']['TimeZoneId']
            win_standard = clean_json['data'][0]['TimeZone']['WindowsStandardName']
            short_name   = clean_json['data'][0]['TimeZone']['ShortName']
            standard_name   = clean_json['data'][0]['TimeZone']['WindowsStandardName']
            id   = clean_json['data'][0]['TimeZone']['TimeZoneId']

            local_time_str = stock.epoch2str(float(i), "%Y-%m-%d %H:%M:%S", tz='%s' % id)
            pacific_time = stock.epoch2str(float(i), "%Y-%m-%d %H:%M:%S", tz='America/Los_Angeles')
            local_time = stock.str2epoch(local_time_str) 
            print "\tLat: %s, Lon: %s" % (events[i][0], events[i][1])
            print "\tTime Zone: %s" % short_name
            print "\tTZ name: %s" % standard_name
            print "\tTZ id: %s" % id
            print "\tEpoch: %s" % i
            print "\tUTC: %s" % time_str
            print "\tPT: %s" % pacific_time
            print "\tLocal: %s" % local_time_str


        print '\n'

    return 0
    # }}}

if __name__ == '__main__':
    status = main()
    sys.exit(status)
else:
    raise Exception("Not a module to be imported!")
    sys.exit()
