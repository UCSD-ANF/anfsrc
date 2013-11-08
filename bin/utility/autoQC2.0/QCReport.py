# -*- coding: utf-8 -*-
"""
Function to generate and distribute network QC report.

Exported Classes:
Classes in this module are not intended to be exported.

Classes:
QC_Issue - Representsa QC issue.
QC_Station_Report - Contains and summarizes QC issues for a station.
QC_Network_Report - Contains/summarzes/distributes QC issues for a network.

Exported Functions:
generate_report - Initializes QC testing and report creation/distribution

The remaining functions should are not intended to be exported.
Remaining Functions:
parse_pf - Parse parameter file.
run_tests - Initiate QC tests (control sequence).
get_thresholds - Return acceptble thresholds for a quantity at a station.
check_thresholds - Check if quantity has acceptable value.
eval_recursive - Recursively eval() <dict> values.


Last edited: Thursday Nov 7, 2013
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego
  
"""
class QC_Issue():
    
    """
    Contain data pertaining to a QC issue.

    Public Instance Variables:
    message - A message describing the QC issue <str>
    sta - Station <str>
    chan - Channel <str>
    
    """

    def __init__(self, params):
        """
        Constructor method. Initialize QC_Issue instance.

        Behaviour:
        Store input parameters.
        
        Arguments:
        params - All parameters <dict>
        params['message'] - Message describing QC issue <str>
        params['sta'] - Station <str>
        params['chan'] - Channel <str>

        Return Values:
        <instance> QC_Issue

        """
        self.message = params['message']
        self.sta = params['sta']
        self.chan = params['chan']
        
     
class QC_Station_Report():

    """
    Contain all QC issues pertaining to a station.

    Behaviour:
    Provide functionality to append a new QC issue to list of existing
    QC issues. Provide functionality to create a summar of all QC
    issues for station.
    
    Public Instance Variables:
    sta
    qc_issues
    
    Public Methods:
    append_issue
    summarize
    
    """

    def __init__(self, qc_issue):
        """
        Constructor method. Initialize QC_Station_Report instance.

        Behaviour:
        Store input QC issue and station.
        
        Arguments:
        qc_issue - QC_Issue <instance>

        Return Values:
        <instance> QC_Station_Report

        """
        self.sta = qc_issue.sta
        self.qc_issues = [qc_issue]
        
    def append_issue(self, qc_issue):
        """
        Append QC_Issue <instance> to list.
        """
        self.qc_issues.append(qc_issue)
        
    def summarize(self):
        """
        Return summary of QC issues pertaining to station.

        Behaviour:
        Create and return a summary of all QC issues pertaining to 
        station.
        
        Return Values:
        <str> containing summary

        """
        summary = '%s\n' % self.sta
        current_chan = ''
        for qc_issue in self.qc_issues:
            if not qc_issue.chan == current_chan:
                summary = '%s\t%s\n' % (summary, qc_issue.chan)
                current_chan = qc_issue.chan
            summary = '%s\t\t%s' % (summary, qc_issue.message)
        return summary


class QC_Network_Report():

    """
    Contain all QC issues for network.

    Behaviour:
    Provide funcionality to add/appen QC issue to network report, 
    to add station report to network report, to summarize network
    report. Provide functionality to send report via e-mail or print
    to STDOUT.
    
    Public Instance Variables:
    qc_station_reports
    network
    tstart
    tend
    email
    send_email
    smtp_server
    
    Public Methods:
    add_issue
    add_station_report
    append_issue
    summarize
    report
    send

    """

    def __init__(self, params):
        """
        Constructor method. Initialize QC_Network_Report instance.

        Behaviour:
        Store input parameters.
        
        Arguments:
        params - All parameters <dict>
        params['network'] - network <str>
        params['tstart'] - Epoch start time <float>
        params['tend'] - Epoch end time <float>
        params['email'] - Email(s) <list>
        params['send_email'] - Send email <bool>
        params['smtp_server'] - SMTP server <str>

        Return Values:
        <instance> QC_Network_Report

        """
        self.qc_station_reports = []
        self.network = params['network']
        self.tstart = params['tstart']
        self.tend = params['tend']
        self.email = params['email']
        self.send_email = params['send_email']
        self.smtp_server = params['smtp_server']
        
    def add_issue(self,qc_issue):
        """
        Add QC issue to appropriate station report.
        
        Behaviour:
        Add QC issue to appropriate station report. Create new 
        QC_Station_Report if necessary.

        """
        if qc_issue.sta not in [qc_sta_rep.sta for qc_sta_rep in \
            self.qc_station_reports]:
                self.add_station_report(QC_Station_Report(
                    qc_issue))
        else:
            self.append_issue(qc_issue)
                
    def add_station_report(self, qc_station_report):
        """Add QC_Station_Report instance to QC_Network_Report
        
        Behaviour:
        Add new QC_Station_Report instance to QC_Network_Report 
        instance, in alphabetical order.
        
        """
        try:
            i = 0
            while self.qc_station_reports[i].sta <= qc_station_report.sta:
                i = i+1
            self.qc_station_reports.insert(i, qc_station_report)
        except IndexError:
            self.qc_station_reports.append(qc_station_report)
    
    def append_issue(self,qc_issue):
        """
        Append QC_Issue instance to existing QC_Station_Report instance.
        
        """
        i = 0
        while not self.qc_station_reports[i].sta == qc_issue.sta: i = i+1
        self.qc_station_reports[i].append_issue(qc_issue)
    
    def summarize(self):
        """
        Return summary of all QC issues for network.

        Behaviour:
        Create and return a summary of all QC issues pertaining to 
        network.
        
        Return Values:
        <str> containing summary

        """
        import sys
        import os
        sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
        from antelope.stock import epoch2str
        sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
        summary = 'QC Report for %s\n' % self.network
        summary = '%s%s - %s\n\n' % (summary, epoch2str(self.tstart, \
            '%Y %D %H:%M:%S'), epoch2str(self.tend,'%Y %D %H:%M:%S'))
        for qc_station_report in self.qc_station_reports:
            summary = '%s%s' % (summary, qc_station_report.summarize())
        return summary
    
    def report(self):
        """Decide whether to send e-mail report to STDOUT"""
        if self.send_email: self.send()
        else: print self.summarize()
    
    def send(self):
        """Send network report to appropriate e-mail addresses.

        Behaviour:
        Send network report to appropriate e-mail addresses via SMTP
        server

        """
        import sys
        import os
        sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
        from antelope.stock import epoch2str, now
        sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
        import smtplib
        sender = 'autoQC-noreply@%s' % self.smtp_server
        from_line = 'From: %s\n' % sender
        to_line = 'To: %s' % self.email[0]
        for rec in self.email[1:]:
            to_line = '%s, %s ' % (to_line, rec)
        to_line = '%s\n' % to_line
        subject_line = 'Subject: AutoQC network report for NETWORK %s\n' % \
            epoch2str(now(),'%m/%d/%Y')
        message = '%s%s%s%s' % (from_line, to_line, subject_line,
            self.summarize())   
        try:
            smtpObj = smtplib.SMTP(self.smtp_server)
            smtpObj.sendmail(sender, self.email,message)
            print 'Network summary successfully sent.'
        except smtplib.SMTPException:
            print 'Error: unable to send e-mail.\n\n'
            print self.summarize()

def parse_pf(params):
    """Parse parameter file, return results.
    
    Arguments:
    params - All parameters <dict>
    params['pf'] - Parameter file <str>
    params['email'] - Email(s) <str>

    Side Effects:
    Converts params['email'] from <str> to <list>
    
    Return Values:
    <dict> of parameters

    """
    import sys
    import os
    sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
    from antelope.stock import pfread
    sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
    pf = pfread(params.pop('pf'))
    for k in pf.keys():
        params[k] = pf[k]
    params['email'] = params['email'].split(',')
    return eval_recursive(params)
    
def run_tests(params):
    import sys
    import os
    sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
    from antelope.datascope import dbopen
    sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
    db = dbopen(params['dbin'], 'r')
    vw_wfmeas = db.lookup(table='wfmeas')
    vw_wfmeas = vw_wfmeas.subset('time == _%f_ && endtime == _%f_' % \
        (params['tstart'], params['tend']))

    vw_wfmeas = vw_wfmeas.sort('sta')
    vw_wfmeas = vw_wfmeas.group('sta')
    for i in range(vw_wfmeas.nrecs()):
        vw_wfmeas_sta = vw_wfmeas.list2subset(i)
        vw_wfmeas_sta = vw_wfmeas_sta.ungroup()
        vw_wfmeas_sta.record = 0
        sta = vw_wfmeas_sta.getv('sta')[0]
        vw_wfmeas_sta = vw_wfmeas_sta.sort('chan')
        vw_wfmeas_sta = vw_wfmeas_sta.group('chan')
        for j in range(vw_wfmeas_sta.nrecs()):
            vw_wfmeas_stachan = vw_wfmeas_sta.list2subset(j)
            vw_wfmeas_stachan = vw_wfmeas_stachan.ungroup()
            vw_wfmeas_stachan.record = 0
            chan = vw_wfmeas_stachan.getv('chan')[0]
            vw_wfmeas_stachan = vw_wfmeas_stachan.sort('meastype')
            for vw_wfmeas_stachan.record in range(vw_wfmeas_stachan.nrecs()):
                meastype,val1 = vw_wfmeas_stachan.getv('meastype', 'val1')
                val1, val2 = None, None
                if not vw_wfmeas_stachan.getv('units1')[0] == '-':
                    val1 = vw_wfmeas_stachan.getv('val1')[0]
                if not vw_wfmeas_stachan.getv('units2')[0] == '-':
                    val2 = vw_wfmeas_stachan.getv('val2')[0]                                        
                thresholds = get_thresholds(sta, meastype, \
                    params['thresholds'], params['thresholds_per_sta'])
                message = check_thresholds(meastype, val1, val2, thresholds)
                if message:
                    params['qc_network_report'].add_issue(QC_Issue(
                        {'sta': sta, 'chan': chan, 'message': message}))
                        
def get_thresholds(sta, meastype, thresholds_default, thresholds_per_sta):
    """
    Return thresholds for quantity at a particular station.

    Behaviour:
    Return the acceptable range of values for a QC quantity at a 
    particular station.
    
    Arguments:
    sta - Station <str>
    meastype - Measurement (quantity) type <str>
    thresholds_default - Default thresholds (of all quantities) <dict>
    thresholds_per_sta - Station thresholds (all available) <dict> 

    Return Values:
    <dict> of acceptable thresholds for particular station and
    particular measuremen (quantity) type.

    """
    thresholds = thresholds_default[meastype]
    if sta in thresholds_per_sta:
        if 'val1' in thresholds_per_sta[sta]:
            if 'min' in thresholds_per_sta[sta]['val1']:
                thresholds['val1']['min'] = \
                   thresholds_per_sta[sta]['val1']['min']
            if 'max' in thresholds_per_sta[sta]['val1']:
                thresholds['val1']['max'] = \
                   thresholds_per_sta[sta]['val1']['max']
        if 'val2' in thresholds_per_sta[sta]:
            if 'min' in thresholds_per_sta[sta]['val2']:
                thresholds['val2']['min'] = \
                   thresholds_per_sta[sta]['val2']['min']
            if 'max' in thresholds_per_sta[sta]['val2']:
                thresholds['val2']['max'] = \
                   thresholds_per_sta[sta]['val2']['max']
    return thresholds
            
def check_thresholds(meastype, val1, val2, thresholds):
    """
    Check if QC quantity(ies) are within acceptable range.

    Behaviour:
    Check to e if QC quantity(ies) are within acceptable range.
    Return None if it(they) is(are). Return a message describing
    where the quantity(ies) fall outside the range.
    
    Arguments:
    meastype - Measurement (quantity) type <str>
    val1 - quantity (1) value <float>
    val2 = quantity (2) value <float>
    thresholds - acceptable range <dict>

    Return Values:
    None or <str> describing how QC quantity(ies) fell outside acceptable
    range.
    
    """
    message = ''
    if val1:
        if val1 < thresholds['val1']['min']:
            message = '%sMeasurement of type %s was below minimum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message, \
                    meastype, thresholds['val1']['min'], val1)
        if val1 > thresholds['val1']['max']:
            message = '%sMeasurement of type %s was above maximum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message, \
                meastype, thresholds['val1']['max'], val1)
    if val2:
        if val2 < thresholds['val2']['min']:
            message = '%sMeasurement of type %s was below minimum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message, \
                meastype, thresholds['val2']['min'], val2)
        if val2 > thresholds['val2']['max']:
            message = '%sMeasurement of type %s was above maximum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message, \
                meastype, thresholds['val2']['max'], val2)
    if message == '': return None
    else: return message

def eval_recursive(dictionary):
    """
    Recursively call eval() on <dict> values.

    Behaviour:
    Convert string values in a <dict> that look like floats to <float>
    and lists to <list>. If the value is a <dict> call this funcion
    recursively on that <dict>.
    
    Arguments:
    dictionary - dictionary to recurively be eval()'d <dict>

    Return Values:
    <dict> with eval()'d values.

    """
    for k in dictionary:
       if isinstance(dictionary[k], dict): dictionary[k] = \
           eval_recursive(dictionary[k])
       else:
           try:
               dictionary[k] = eval(dictionary[k])
           except (NameError, SyntaxError, TypeError):
               pass
    return dictionary
    
def generate_report(params):
    """
    Initiate QC tests and report generation/distribution.

    Behaviour:
    The main function intended to be called by importer. Initiates QC
    tests and report generation/disribution.
    
    Arguments:
    params - All parametrs <dict>
    params['dbin'] - Input database <str>
    params['pf'] - Parameter file <str>
    params['network'] - Network <str>
    params['tstart'] - Epoch start time <float>
    params['tend'] - Epoch end time <float>
    
    """
    params = parse_pf(params)
    qc_network_report = QC_Network_Report({'network': params['network'], \
        'tstart': params['tstart'], 'tend': params['tend'], \
        'send_email': params.pop('send_email'), 'email': params.pop('email'), \
        'smtp_server': params.pop('smtp_server')})
    params['qc_network_report'] = qc_network_report  
    run_tests(params)
    qc_network_report.report()