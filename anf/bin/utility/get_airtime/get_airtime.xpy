''' get_airtime.py
Talk to the BGAN airlink website, get the BGAN usage, email a report

initial checkin by jmeyer, 2015-10-01
'''

# Import python built-ins
import datetime, json, logging, re, requests, smtplib, urllib, urllib3
from optparse import OptionParser
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
        assert 'failed' not in r.text
        assert 'Airtime Reports' in r.text

        # We're in.  Get the "groupDashboard" formatted data, which is
        # a JavaScript var declaration.
        r = s.get('%s/pages/mod_interactive_report/getData.php?' % baseuri +
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
        dayuse[imsi][day] = i[5]

    mystr = "%s BGAN IMSI data use for the past %d days (%s -> %s)\n" % (
            owner,days,start_date,end_date)
    mysubj = mystr
    mystr += "\n"
    for k,v in sorted(dayuse.items()):
        # Show avergage day use
        days = len(dayuse[k])
        mymb = sum(dayuse[k].values())
        avg  = mymb/days
        if avg > threshold:
            alert = ' <-- HIGH USE!'
        else:
            alert = ''
        mystr += "%-16s: %0.2f MB in %i days (%0.2f MB/day)%s" % (
                k,mymb,days,avg,alert)

        # Show the day usage for start and end days
        daystrs   = []
        mykeys    = sorted(v.keys())
        begin,end = mykeys[0],mykeys[-1]
        daystrs.append("%s: %0.2f MB" % (begin,v[begin]))
        daystrs.append("%s: %0.2f MB" % (end,v[end]))
        mystr += "\t" + "\t".join(daystrs) + "\n"
    return [mysubj,mystr]

def do_email(subject,email_from,email_to,text,smtphost):
    '''Email a string to somebody'''
    msg = MIMEText(text)
    to = [x.strip() for x in email_to.split(',')]

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = subject
    msg['From']    = email_from
    msg['To']      = ','.join(to)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
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
    mysubject,myreport = do_report(myairtime,days,date1,date2,mbthreshold)
    logger.debug('mysubject: %s' % mysubject)
    logger.debug('myreport: %s' % myreport)

    logger.info('Emailing report...')
    do_email(mysubject,email_from,email_to,myreport,smtphost)

    logger.info('Done.')

if __name__ == '__main__':
    main()
