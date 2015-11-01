''' get_airtime.py
Talk to the BGAN airlink website, get the BGAN usage, email a report

initial checkin by jmeyer, 2015-10-01
'''

# Import python built-ins
import datetime, json, logging, re, requests, smtplib, urllib, urllib3
from optparse import OptionParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Bring in Antleopey things
import antelope.stock

def get_airtime(start_date,end_date,username,password,
        baseuri='https://airtime.globecommsa.com'):
    '''Login to the Airtime website and collect our data'''

    postdata = urllib.urlencode({ 'username':username,'password':password })

    # urllib3 will complain a lot with verify=False
    with requests.Session() as s:
        # Login
        uri = '%s/pages/index.php?action=login' % baseuri
        r = s.post(uri,verify=False, data=postdata, headers={
            'Content-Type':'application/x-www-form-urlencoded'})

        # Make sure we're not getting failure messages and are getting
        # text for airtime reports.
        logging.debug(r.headers)
        logging.debug(r.text)
        assert 'failed' not in r.text
        assert 'Airtime Reports' in r.text

        # We're in.  Get the "groupDashboard" formatted data, which is
        # a JavaScript var declaration.
        r = s.get('%s/pages/mod_interactive_report/getData.php?' % baseuri + \
                urllib.urlencode({
                    'format'   :'groupDashboard',
                    'startDate':start_date,
                    'endDate'  :end_date,
                }),
                verify=False)

        # Hack that .js text to get it to convert to JSON...
        jsonstr = '{ "data":' + re.split(
                '[=;]',r.text)[1].replace("'",'"') + '}'

        # Logout
        s.get('%s/pages/index.php?action=logout' % baseuri, verify=False)

        logging.debug(jsonstr)

    # We don't really want the whole data structure, just a section...
    return json.loads(jsonstr)['data'][1:]

def do_report(mylist,days,start_date,end_date,threshold):
    '''Take our array of arrays of data and make a readable report'''

    # Take list of lists and make into dict
    dayuse = {}
    for i in mylist:
        assert type(i) == list
        assert len(i)  == 6
        owner = i[4]
        imsi  = i[2]
        day   = i[0]
        if not dayuse.has_key(imsi): dayuse[imsi] = {}
        if not dayuse[imsi].has_key(day): dayuse[imsi][day] = 0.0
        # We may get SMS or Background IP data, but we just want the sum of MB
        dayuse[imsi][day] += i[5]

    mytext = "%s BGAN IMSI data use for the past %d days (%s -> %s)\n" % (
            owner,days,start_date,end_date)
    myhtml = "<h1>%s BGAN IMSI data use</h1>\n" % owner + \
             "<p>for the past %d days (%s -> %s)</p>\n" % (
                     days,start_date,end_date)
    mysubj = mytext
    mytext += "\n"
    bstyle = 'border:1px solid grey'
    tablestyle = '; '.join(sorted([bstyle] + list([':'.join([k,v]) for k,v in {
        'border-collapse':'collapse',
        'border'         :'1px solid grey',
        'width'          :'100%',
        'margin-left'    :'auto',
        'margin-right'   :'auto',
        }.items()])))
    mbstyle = '; '.join([bstyle] + list(sorted([':'.join([k,v]) for k,v in {
        'font-family':'monospace',
        'text-align' :'right',
        }.items()])))

    myhtml += "<table style='%s'>\n<tr>\n" % tablestyle
    myhtml += "<th style='%s'>IMSI</th>\n"                   % bstyle +\
            "<th style='%s'>Total MB</th>\n"                 % bstyle +\
            "<th style='%s'>Number of Days on Record</th>\n" % bstyle + \
            "<th style='%s'>Average MB/day</th>\n"           % bstyle + \
            "<th style='%s'>First day</th>\n"                % bstyle + \
            "<th style='%s'>First day MB</th>\n"             % bstyle +\
            "<th style='%s'>Last day</th>\n"                 % bstyle + \
            "<th style='%s'>Last day MB</th>\n"              % bstyle + \
            "<th style='%s'>Usage</th>\n</tr>\n"             % bstyle
    for k,v in sorted(dayuse.items()):
        # Show avergage day use
        days  = len(dayuse[k])
        mymb  = sum(dayuse[k].values())
        avgmb = mymb/days

        mytext += "%-16s: %0.2f MB in %i days (%0.2f MB/day)" % (
                k,mymb,days,avgmb)
        myhtml += "<tr><td style='%s; text-align:right'>%s</td>\n" % (bstyle,k)
        myhtml += "<td style='%s'>%0.2f</td>\n"  % (mbstyle,mymb)
        myhtml += "<td style='%s; text-align:center'>%i</td>\n"    % (bstyle,days)
        myhtml += "<td style='%s'>%0.2f</td>\n"  % (mbstyle,avgmb)

        # Show the day usage for start and end days
        daystrs   = []
        mykeys    = sorted(v.keys())
        begin,end = mykeys[0],mykeys[-1]
        daystrs.append("%s: %0.2f MB" % (begin,v[begin]))
        daystrs.append("%s: %0.2f MB" % (end,v[end]))
        mytext += "\t" + "\t".join(daystrs) + "\n"

        myhtml += "<td style='%s; text-align:center'>%s</td>\n" % (bstyle,begin)
        myhtml += "<td style='%s'>%0.2f</td>\n"  % (mbstyle,v[begin])
        myhtml += "<td style='%s; text-align:center'>%s</td>\n" % (bstyle,end)
        myhtml += "<td style='%s'>%0.2f</td>\n"  % (mbstyle,v[end])

        # Append alert
        if avgmb > threshold:
            mytext += ' <-- HIGH USE!'
            myhtml += "<td style='%s; color:red'>over "   % bstyle
        else:
            myhtml += "<td style='%s; color:blue'>under " % bstyle

        myhtml += "<span style='font-family:monospace'>%0.2f</span> " %\
                threshold + "MB/day</td>\n</tr>\n"

    myhtml += "</table>\n"
    return [mysubj,mytext,myhtml]

def do_email(subject,email_from,email_to,text,html,smtphost):
    '''Email a string to somebody'''
    msg = MIMEMultipart('alternative')
    to = [x.strip() for x in email_to.split(',')]

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = subject
    msg['From']    = email_from
    msg['To']      = ','.join(to)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    msg.attach(MIMEText(text,'plain'))
    msg.attach(MIMEText(html,'html'))

    s = smtplib.SMTP(smtphost)
    s.sendmail(email_from, to, msg.as_string())
    s.quit()

def main():
    parser = OptionParser()
    parser.add_option('-d','--debug',action='store_true',dest='debug',
            default=False, help='print DEBUG level messages to stderr')
    parser.add_option('-v','--verbose',action='store_true',dest='verbose',
            default=False, help='print INFO level messages to stderr')
    parser.add_option('-p', '--pf', action='store', dest='pf', type='string',
                        help='parameter file path', default='get_airtime')

    (options, args) = parser.parse_args()

    # Set up logging
    logformat = '%(asctime)s [%(levelname)s] %(message)s'
    logging.captureWarnings(True)

    if options.verbose:
        logging.basicConfig(format=logformat,level=logging.INFO)
    elif options.debug:
        logging.basicConfig(format=logformat,level=logging.DEBUG)
    else:
        logging.basicConfig(format=logformat,level=logging.CRITICAL)
    logger = logging.getLogger('get_airtime')

    # Get PF file values
    logger.info('Read parameters from pf file %s' % options.pf)
    pf = antelope.stock.pfread(options.pf)

    # Airtime's SSL certs are silly, but we don't want to hear about it
    urllib3.disable_warnings()

    # Get parameters from PF file
    days        = int(pf.get('days'))
    mbthreshold = float(pf.get('mbthreshold'))
    user        = pf.get('user')
    passwd      = pf.get('passwd')
    email_from  = pf.get('email_from')
    email_to    = pf.get('email_to')
    smtphost    = pf.get('smtphost')

    assert str == type(user)
    assert str == type(passwd)
    assert str == type(smtphost)
    assert str == type(email_from)
    assert str == type(email_to)

    # N days ago
    date1 = (datetime.datetime.now() - datetime.timedelta(days=days)
            ).strftime('%Y-%m-%d')
    # Yesterday
    date2 = (datetime.datetime.now() - datetime.timedelta(days=1)
            ).strftime('%Y-%m-%d')

    logger.info('Get airtime report data...')
    myairtime = get_airtime(date1,date2,user,passwd)
    logger.debug('myairtime: %s' % myairtime)

    logger.info('Generate email report...')
    mysubject,myreport,myhtmlreport = do_report(
            myairtime,days,date1,date2,mbthreshold)
    logger.debug('mysubject: %s' % mysubject)
    logger.debug('myreport: %s' % myreport)
    logger.debug('myhtmlreport: %s' % myhtmlreport)

    logger.info('Emailing report...')
    do_email(mysubject,email_from,email_to,myreport,myhtmlreport,smtphost)

    logger.info('Done.')

if __name__ == '__main__':
    main()
