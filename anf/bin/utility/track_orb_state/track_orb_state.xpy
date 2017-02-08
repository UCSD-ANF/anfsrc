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

    cmd = subprocess.Popen('orbstat -vc %s' % eachOrb, shell=True, stdout=subprocess.PIPE)

    readline = 0
    inGroupStat = 15
    timeValue = False
    timeUnits = False
    requestType = False
    nowName = False
    thread = None
    name = ''
    errors = 0
    self_group = 1

    json_cache[ eachOrb ] = { 'status': 'unknown', 'orbs': [] }

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
            if re.search("started", line): continue
            if re.search("^$", line): continue

            if requestType and thread and name and timeValue and timeUnits:

                if re.search("second", timeUnits):
                    output_line( "\t[%s][%s %s]    %s" % ( thread, timeValue, timeUnits, name ) )
                    state = 'ok'
                elif re.search("minute", timeUnits):
                    output_line( "\t[\x1B[91m[%s]%s %s]    %s\x1B[0m" %(  thread, timeValue, timeUnits, name ) )
                    state = 'watch'
                elif re.search("hour", timeUnits):
                    output_line( "\t[\x1B[41m[%s]%s %s]    %s\x1B[0m" %(  thread, timeValue, timeUnits, name ) )
                    state = 'warning'
                else:
                    output_line( "\t[\x1B[5m\x1B[41m\x1B[37m[%s]%s %s]    %s\x1B[0m" %(  thread, timeValue, timeUnits, name ) )
                    state = 'error'

                json_cache[ eachOrb ][ 'orbs' ].append(
                        {
                            'thread': thread,
                            'errors': errors,
                            'type': requestType,
                            'state': state,
                            'orbname': name,
                            'time': timeValue,
                            'timeUnits': timeUnits
                        }
                        )

                timeValue = False
                timeUnits = False
                thread = None
                errors = 0
                requestType = False


            if len(line.split()) == inGroupStat:

                parts = line.split()

                thread = parts[0]
                timeValue = parts[-3]
                timeUnits = parts[-2]
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
