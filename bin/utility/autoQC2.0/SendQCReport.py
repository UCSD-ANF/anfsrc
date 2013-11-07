# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 18:15:25 2013

@author: mcwhite
"""

def parse_pf(params):
    import sys #necesary only for testing
    import os #necesary only for testing
    sys.path.append('%s/data/python' % os.environ['ANTELOPE']) #necesary only for testing
    from antelope.stock import pfread
    sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
    pf = pfread(params.pop('pf'))
    for k in pf.keys():
        params[k] = pf[k]
    params['email'] = params['email'].split(',')
    return eval_recursive(params)
    
def send_report(params):
    import sys
    import os
    sys.path.append('ANTELOPE')
    from antelope.datascope import dbopen
    sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
    params = parse_pf(params)
    QC_network_report = QC_Network_Report({'network': params['network'], \
        'tstart': params['tstart'], 'tend': params['tend'], \
        'send_email': params.pop('send_email'), 'email': params.pop('email'), \
        'smtp_server': params.pop('smtp_server')})
    db = dbopen(params['dbin'],'r')
    vw_wfmeas = db.lookup(table='wfmeas')
    vw_wfmeas = vw_wfmeas.subset('time == _%f_ && endtime == _%f_' %
                                 (params['tstart'],params['tend'])
                                 )
#    st = 'QC Network Report - %s\n%s - %s\n' % (params['network'],\
#        epoch2str(params['tstart'],'%Y %D %H:%M:%S'),\
#        epoch2str(params['tend'], '%Y %D %H:%M:%S'))
    vw_wfmeas = vw_wfmeas.sort('sta')
    vw_wfmeas = vw_wfmeas.group('sta')
    for i in range(vw_wfmeas.nrecs()):
        vw_wfmeas_sta = vw_wfmeas.list2subset(i)
        vw_wfmeas_sta = vw_wfmeas_sta.ungroup()
        vw_wfmeas_sta.record = 0
#        st = '%s%s\n' % (st,wfmeas_sta.getv('sta'))
        sta = vw_wfmeas_sta.getv('sta')[0]
        vw_wfmeas_sta = vw_wfmeas_sta.sort('chan')
        vw_wfmeas_sta = vw_wfmeas_sta.group('chan')
        for j in range(vw_wfmeas_sta.nrecs()):
            vw_wfmeas_stachan = vw_wfmeas_sta.list2subset(j)
            vw_wfmeas_stachan = vw_wfmeas_stachan.ungroup()
            vw_wfmeas_stachan.record = 0
#            st = '%s  %s\n' % (st,wfmeas_stachan.getv('chan'))
            chan = vw_wfmeas_stachan.getv('chan')[0]
            vw_wfmeas_stachan = vw_wfmeas_stachan.sort('meastype')
            for vw_wfmeas_stachan.record in range(vw_wfmeas_stachan.nrecs()):
                meastype,val1 = vw_wfmeas_stachan.getv('meastype','val1')
                val1,val2 = None,None
                if not vw_wfmeas_stachan.getv('units1')[0] == '-':
                    val1 = vw_wfmeas_stachan.getv('val1')[0]
                if not vw_wfmeas_stachan.getv('units2')[0] == '-':
                    val2 = vw_wfmeas_stachan.getv('val2')[0]                                        
                thresholds = get_thresholds(sta,meastype,params['thresholds'],\
                    params['thresholds_per_sta'])
                message = check_thresholds(meastype,val1,val2,thresholds)
#                if fails_QC_test(val1,val2,thresholds):
                if message:
                    QC_network_report.add_issue(QC_Issue({'sta':sta,'chan':chan,\
                        'message':message}))
    QC_network_report.report()
#                sta_thresholds = None
#                if sta in params['thresholds_per_sta']:
#                    sta_thresholds = params['thresholds_pre_sta'][sta]
#                QC_params = {'meastype':meastype,'val1':va1,'val2':val2,\
#                    'thresholds':params['thresholds'],\
#                    'sta_thresholds':sta_thresholds}
#                if fails_QC_test(QC_params):
#                    QC_network_report.add_issue(QC_issue({'sta':sta,\
#                        'chan':chan,'message':'DEFAULT MESSAGE'}))
def get_thresholds(sta,meastype,thresholds_default,thresholds_per_sta):
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

def fails_QC_test(val1,val2,thresholds):
    if val1:
        if val1 < thresholds['val1']['min'] or \
            val1 > thresholds['val1']['max']:
            return True
    if val2:
        if val2 < thresholds['val2']['min'] or \
            val2 > thresholds['val2']['max']:
            return True
            
def check_thresholds(meastype,val1,val2,thresholds):
    message = ''
    if val1:
        if val1 < thresholds['val1']['min']:
            message = '%sMeasurement of type %s was below minimum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message,meastype,
                thresholds['val1']['min'],val1)
        if val1 > thresholds['val1']['max']:
            message = '%sMeasurement of type %s was above maximum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message,meastype,
                thresholds['val1']['max'],val1)
    if val2:
        if val2 < thresholds['val2']['min']:
            message = '%sMeasurement of type %s was below minimum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message,meastype,
                thresholds['val2']['min'],val2)
        if val2 > thresholds['val2']['max']:
            message = '%sMeasurement of type %s was above maximum threshold '\
                'value. Threshold: %.1f - Observed: %.1f\n'%(message,meastype,
                thresholds['val2']['max'],val2)
    if message == '': return None
    else: return message

def eval_recursive(dictionary):
    for k in dictionary:
       if isinstance(dictionary[k],dict): dictionary[k] = eval_recursive(dictionary[k])
       else:
           try:
               dictionary[k] = eval(dictionary[k])
           except (NameError,SyntaxError,TypeError):
               pass
    return dictionary
#######################################################################

class QC_Issue():
    """A class to contain data pertaining to a generic QC issue (ie.\
    a failed QC test)."""
    def __init__(self,params):
        """A constructor method."""
        self.message = params['message']
        self.sta = params['sta']
        self.chan = params['chan']

#######################################################################
     
class QC_Station_Report():
    """A class containing all QC issues (<QC_Issue> objects) \
    pertaining to a particular station and a method to create a \
    station report."""
    def __init__(self,QC_issue):
        """A constructor method."""
        self.sta = QC_issue.sta
        self.QC_issues = [QC_issue]
        
    def append_issue(self,QC_issue):
        """Appends a QC issue (<QC_obj> object) to list of QC \
        issues."""
        self.QC_issues.append(QC_issue)
        
    def summarize(self):
        """Return a string summarizing QC issues pertainingt station, \
        grouped by channel."""
        #Add first line of station report, the station name.
        summary = '%s\n' % self.sta
        #For each QC issue at station, add a line stating issue.
        #Issues should already be grouped by channel, so label
        #each channel summary appropriately.
        current_chan = ''
        for QC_issue in self.QC_issues:
            if not QC_issue.chan == current_chan:
                summary = '%s\t%s\n' % (summary,QC_issue.chan)
                current_chan = QC_issue.chan
            summary = '%s\t\t%s' % (summary,QC_issue.message)
        return summary
            

#######################################################################

class QC_Network_Report():
    """A class containing all QC station reports for the network and \
    method to create a network report."""
    def __init__(self,params):
        """A constructor method."""
        self.QC_station_reports = []
        self.network = params['network']
        self.tstart = params['tstart']
        self.tend = params['tend']
        self.email = params['email']
        self.send_email = params['send_email']
        self.smtp_server = params['smtp_server']
        
    def add_issue(self,QC_issue):
        """Adds an QC issue (<QC_obj> object) to the appropriate \
        station report in the self-contained list of station \
        reports."""
        #If a station report has not been started for this station
        #add one.
        if QC_issue.sta not in [QC_sta_rep.sta for QC_sta_rep in \
            self.QC_station_reports]:
                self.add_station_report(QC_Station_Report(
                    QC_issue))
        #If a station report does already exist, append the issue
        #to the existng report.
        else:
            self.append_issue(QC_issue)
                
    def add_station_report(self,QC_station_report):
        """Adds a new station report to network report. Station \
        reports are stored in alphabetic order."""
        #Insert a new station report into self-contained list
        #of station reports ensuring that alphabetic order (by
        # station name) is maintained.
        try:
            i = 0
            while self.QC_station_reports[i].sta <= QC_station_report.sta:
                i = i+1
            self.QC_station_reports.insert(i,QC_station_report)
        except IndexError:
            self.QC_station_reports.append(QC_station_report)
    
    def append_issue(self,QC_issue):
        """Appends an issue to an existing station report"""
        #Find the correct station report and append issue.
        i = 0
        while not self.QC_station_reports[i].sta == QC_issue.sta: i = i+1
        self.QC_station_reports[i].append_issue(QC_issue)
    
    def summarize(self):
        """Returns a string summarizing all QC issues pertaining to \
        network. QC issues are sorted by station and channel"""
        #Add header line to network report.
        import sys
        import os
        sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
        from antelope.stock import epoch2str
        sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
        summary = 'QC Report for %s\n' % self.network
        summary = '%s%s - %s\n\n' % (summary,epoch2str(self.tstart,'%Y %D %H:%M:%S'), \
            epoch2str(self.tend,'%Y %D %H:%M:%S'))
        #For each station report in self-contained list, add lines
        #for that report.
        for QC_station_report in self.QC_station_reports:
            summary = '%s%s' % (summary,QC_station_report.summarize())
        return summary
    
    def report(self):
        """Decides whether to print network report to STDOUT or to\
        send e-mail based on 'send_email' flag."""
        if self.send_email: self.send()
        else: print self.summarize()
    
    def send(self):
        """Sends network report to given e-mail addresses."""
        #Import library to provide mail functionality.
        import sys
        import os
        sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
        from antelope.stock import epoch2str, now
        sys.path.remove('%s/data/python' % os.environ['ANTELOPE'])
        import smtplib
        #Create an anonymous sender. This should probably be done in a
        #more appropriate fashion.
        sender = 'autoQC-noreply@%s' % self.smtp_server
        #Create a 'From:' line.
        from_line = 'From: %s\n' % sender
        #Create a 'To:' line, appending each of the specified
        #e-mail addreses.
        to_line = 'To: %s' % self.email[0]
        for rec in self.email[1:]:
            to_line = '%s, %s ' % (to_line,rec)
        to_line = '%s\n' % to_line
        #Createa subject line.
        subject_line = 'Subject: AutoQC network report for NETWORK %s\n' % \
            epoch2str(now(),'%m/%d/%Y')
        #Create the payload.
        message = '%s%s%s%s' % (from_line,to_line,subject_line,
            self.summarize())
        #Try to send e-mail by...    
        try:
            #Connecting to UCSD's SMTP server. This is not a general
            #solution.
            smtpObj = smtplib.SMTP(self.smtp_server)
            #Sending the mesage.
            smtpObj.sendmail(sender,self.email,message)
            #Notify STDOUT that mail was successfully sent.
            print 'Network summary successfully sent.'
        #If mail fails to send, notify STDOUT, and print the
        #network reportto STDOUT. Writing out to a file is likely a
        #better idea.
        except smtplib.SMTPException:
            print 'Error: unable to send e-mail.\n\n'
            print self.summarize()

#######################################################################

def test():
    params = {'pf':'SendQCReport'}
    params = parse_pf(params)

test()