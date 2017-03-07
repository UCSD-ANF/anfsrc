# We want a simple script that will track a few orbs
# and output the information in them in a condensed form.
#
# Juan Reyes
# reyes@ucsd.edu

import subprocess
import re
import json
from optparse import OptionParser


usage = '\nUSAGE:\n\t%s [-v] [-j] orb1 [orb2] [orb3] ... \n\n' % __file__

parser = OptionParser()

parser.add_option("-v",  dest="verbose", help="Verbose output",
                    action="store_true",default=False)
parser.add_option("-j",  dest="json", help="JSON data output",
                    action="store_true",default=False)

(options, ORBS) = parser.parse_args()

if len(ORBS) < 1:
    parser.print_help()
    sys.exit( 'Need name of ORB(s).')



def output_line( text ):
    if options.json: return
    else: print text


json_cache = {}

# Loop over each orb listed on the configuration
for eachOrb in ORBS:

    # Find the packet id information for this orb
    cmd = subprocess.Popen('orbstat -i %s range' % eachOrb, shell=True, stdout=subprocess.PIPE)

    oldid = False
    newid = False
    delta = False
    maxid = False
    rangeid = False

    for line in cmd.stdout:

        line = line.rstrip()
        line = line.lstrip()
        #print "[%s]" % line

        m = re.match( r"oldest=\s*(\d+)\s*newest=\s*(\d+)\s*maxpktid=\s*(\d+)\s*range=\s*(\d+)", line)

        #print m.groups()
        #print m.groupdict()

        try:
            if len(m.groups(3)) == 4:
                oldid = int(m.group(1))
                newid = int(m.group(2))
                maxid = int(m.group(3))
                rangeid = int(m.group(4))
                if oldid > newid:
                    delta = maxid - oldid
                else:
                    delta = -1 * oldid
        except Exception, e:
            #print "Problem. %s:%s" % (Exception, e)
            pass

    #print 'oldid = [%f]' % oldid
    #print 'newid = [%f]' % newid
    #print 'maxid = [%f]' % maxid
    #print 'rangeid = [%f]' % rangeid
    #print 'delta = [%f]' % delta



    cmd = subprocess.Popen('orbstat -vc %s' % eachOrb, shell=True, stdout=subprocess.PIPE)

    readline = 0
    inGroupStat = 15
    orblag = False
    pcktid = False
    timeValue = False
    timeUnits = False
    requestType = False
    nowName = False
    pid = None
    host = None
    name = ''
    errors = 0
    self_group = 1

    json_cache[ eachOrb ] = {
            'status': 'unknown',
            'orbs': [],
            'oldid': oldid,
            'newid': newid,
            'maxid': maxid,
            'delta': delta,
            'rangeid': rangeid,
            }
    for line in cmd.stdout:

        readline += 1

        if not line: continue

        line = line.rstrip()
        line = line.lstrip()

        if re.search("fatal", line):
            output_line( "\x1B[5m\x1B[41m\x1B[37m%s => %s\x1B[0m" %( eachOrb, line ) )
            json_cache[ eachOrb ][ 'status' ] = line
            break


        if readline < 4: continue
        if readline == 4:
            parts = line.split()
            output_line( "\x1B[42m%s => %s\x1B[0m" % ( eachOrb, ' '.join( parts[3:] ) ) )
            json_cache[ eachOrb ][ 'status' ] = ' '.join( parts[3:] )
            continue

        if readline > 18:

            # we want to avoid tracking this same process
            if re.search("-vc", line):
                self_group = 1
                continue
            if self_group > 0:

                if self_group > 3:
                    self_group = 0
                else:
                    self_group += 1

                continue

            if re.search("Total", line): continue
            if re.search("nbytes", line): continue
            if re.search("selecting", line): continue
            if re.search("rejecting", line): continue
            if re.search("hostname", line): continue
            if re.search("^$", line): continue

            if host and requestType and pid and name and timeValue and timeUnits:

                orbplace = '-'
                if delta:
                    try:
                        orbplace = "%0.1f" % ( 100.0 * ( (float(pcktid) + float(delta)) / float(rangeid) ) )
                        #print "( 100 * (%f + %f) / %f )  = %s" % ( pcktid, delta, rangeid,  orbplace)
                    except Exception,e:
                        print "Problem. %s:%s" % (Exception, e)
                        orbplace = '-'
                else:
                    try:
                        orbplace = 1.0 - float(orblag)
                    except Exception,e:
                        print "Problem. %s:%s" % (Exception, e)
                        orbplace = '-'

                if re.search("second", timeUnits):
                    output_line( "\t[%s][%s %s](%s%%)    %s" % ( pid, timeValue, timeUnits, orblag, name ) )
                    state = 'ok'
                elif re.search("minute", timeUnits):
                    output_line( "\t[\x1B[91m[%s]%s %s](%s%%)    %s\x1B[0m" %(  pid, timeValue, timeUnits, orblag, name ) )
                    state = 'watch'
                elif re.search("hour", timeUnits):
                    output_line( "\t[\x1B[41m[%s]%s %s](%s%%)    %s\x1B[0m" %(  pid, timeValue, timeUnits, orblag, name ) )
                    state = 'warning'
                else:
                    output_line( "\t[\x1B[5m\x1B[41m\x1B[37m[%s]%s %s](%s%%)    %s\x1B[0m" %(  pid, timeValue, timeUnits, orblag, name ) )
                    state = 'error'

                json_cache[ eachOrb ][ 'orbs' ].append(
                        {
                            'pid': pid,
                            'host': host,
                            'errors': errors,
                            'type': requestType,
                            'state': state,
                            'orbplace': orbplace,
                            'orblag': orblag,
                            'pcktid': pcktid,
                            'orbname': name,
                            'time': timeValue,
                            'timeUnits': timeUnits
                        }
                        )

                orblag = False
                pcktid = False
                timeValue = False
                timeUnits = False
                pid = None
                errors = 0
                host = None
                requestType = False

            if re.search("started", line):
                parts = line.split()
                host = parts[1]
                continue

            if len(line.split()) == inGroupStat:

                parts = line.split()

                pid = parts[0]
                pcktid = int(parts[-4])
                timeValue = parts[-3]
                timeUnits = parts[-2]
                orblag = parts[-1]
                nowName = True

                continue

            if len(line.split()) == inGroupStat + 2:

                parts = line.split()

                pid = parts[0]
                pcktid = int(parts[-6])
                timeValue = parts[-5]
                timeUnits = parts[-4]
                orblag = parts[-1]
                nowName = True

                continue


            if nowName:

                name = line
                nowName = False

                continue



            if re.search("errors", line):
                parts = line.split()

                errors = int(parts[0])
                requestType = parts[3].split('=')[1]
                continue



            # CANNOT GET TO THIS POINT
            output_line( 'UNKNOWN LINE [%s]' % line )



if options.json:
    print "\n%s\n" % json.dumps(json_cache, indent=4, separators=(',', ': '))
