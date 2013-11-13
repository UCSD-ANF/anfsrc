#######################################################################

class QC_Obj:
    """An object class containing all data and functionality necessary\
    for running QC tests on a give station-channel."""
    def __init__(self,params):
        """A constructor method."""
        #Store input parameters in this <QC_obj> instance's namespace.
        self.dbpath = params['dbpath']
        self.sta = params['sta']
        self.chan = params['chan']
        self.time_lag = params['time_lag']
        self.time_window = params['time_window']
        self.RMS_bool = params['RMS_bool']
        self.RMS_max = params['RMS_max']
        self.RMS_flatline = params['RMS_flatline']
        self.DC_offset_bool = params['DC_offset_bool']
        self.DC_offset_max = params['DC_offset_max']
        self.linear_trend_bool = params['linear_trend_bool']
        self.linear_trend_max = params['linear_trend_max']
        self.skewness_bool = params['skewness_bool']
        self.skewness_max = params['skewness_max']
        self.QC_network_report = params['QC_network_report']

    def runQC(self):
        """A method to call various QC testing methods"""
        #Let STDOUT know what's happening.
        print '%s:%s - processing...' % (self.sta, self.chan)
        try:
            #Load a trace object to run tests on.
            self.load_trace()
        except LoadTrace_Error as err:
            #Except an error by raising a new error.
            raise RunQC_Error(err.message)
        #Run the appropriate QC tests.
        if self.DC_offset_bool: self.DC_offset_test()
        if self.RMS_bool: self.RMS_test()        
        if self.linear_trend_bool: self.linear_trend_test()
        if self.skewness_bool: self.skewness_test()
        self.trace.trdestroy()

    def plot(self):
        """A plotting method useful for verifying validity of QC tests\
        during development"""
        import matplotlib.pyplot as plt
        self.load_trace()
        d = self.trace.data()
        m = fsum(d)/len(d)
        rms = sqrt(fsum([pow(val-m,2) for val in d])/len(d))
        
        time,endtime,nsamp = self.trace.getv('time','endtime','nsamp')
        x = np.arange(time,endtime,(endtime-time)/nsamp)
        M,b = np.polyfit(x,d,1)

        plt.plot(x,d,'b-',x,[M*X + b for X in x],'r-')
        plt.show()
        self.trace.trdestroy()
        
    def load_trace(self):
        """Return a Trace4.1 schema trace object. Waveform data \
        returned is in raw counts."""
        #Open input databse.
        db = dbopen(self.dbpath,'r')
        #Look up wfdisc table
        vw_wf = db.lookup(table='wfdisc')
        #Calculate start time and end times, for which to request data
        #based on the current time, and the time_lag/time_window
        #parameters specified in the parameter file.
        ts = str2epoch(epoch2str(now(),'%Y%j')) - self.time_lag
        te = ts + self.time_window
        #An optimization: try to find a single wfdisc row that contains
        #the entire segment of data to be requested.
        i = vw_wf.find('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime\
            >= _%f_' % (self.sta, self.chan, ts, te),vw_wf.nrecs(),
            reverse=True)
        #If such a single row is found, subset that row and proceed
        #to request data.
        if not i < 0:
            vw_wf = vw_wf.list2subset(i)
        #If a single row was not found, find all rows which contain
        #some portion of the data segment to be requested and
        #subset these rows. Begin search from end of wfdisc
        #because if this program is being run regularly for
        #recently acquired data, rows will be at the end of
        #wfdisc table.
        else:
            i = vw_wf.nrecs()
            recs = []
            while not i < 0:
                i = vw_wf.find('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ &&\
                    endtime >= _%f_' % (self.sta,self.chan,te,ts),i,
                    reverse=True)
                if not i < 0:
                    recs.append(i)
                #If no records were found, raise an error stating that
                #data was unretrievable
                elif len(recs) == 0:
                    raise LoadTrace_Error('No records found in wfdisc for %s:\
                        %s' % (self.sta, self.chan))
                    return 0
            vw_wf = vw_wf.list2subset(recs)
        #Now that the wfdisc has been appropriatel subsetted, load
        #data into a trace object
        tr = vw_wf.loadchan(ts,te,self.sta,self.chan)
        tr.record = 0
        self.trace = tr
        #Close the input database
        db.close()

    def DC_offset_test(self):
        """A test for DC offset greater than some threshold."""
        #Extract waveform data fom self-contained trace object.            
        d = self.trace.data()
        #Compute the mean
        m = fsum(d)/len(d)
        #If the mean is outside the acceptable threshold, report
        #QC issue
        if m < -self.DC_offset_max or m > self.DC_offset_max:
            params['message'] = 'DC offset test failed. DC offset = %.3f' % m
            params['sta'] = self.sta
            params['chan'] = self.chan
            self.QC_network_report.add_issue(QC_Issue(params))

    def RMS_test(self):
        """A test for RMS greater than some threshold (noisy) or below\
        some threshold (flatline)."""
        #Extract waveform data fom self-contained trace object.
        d = self.trace.data()
        #Compute the mean.
        m = fsum(d)/len(d)
        #Compute the demeaned RMS
        rms = sqrt(fsum([pow(val-m,2) for val in d])/len(d))
        #If the RMS is above the acceptable threshold (noisy),
        #report QC issue.
        if rms > self.RMS_max:
            params['message'] = 'RMS test failed. RMS = %.3f' % rms
            params['sta'] = self.sta
            params['chan'] = self.chan
            self.QC_network_report.add_issue(QC_Issue(params))
        #If the RMS is below some other threshod (flatlining),
        #report QC issue.
        elif rms < self.RMS_flatline:
            params['message'] = 'RMS flatline test failed. RMS = %.3f' % rms
            params['sta'] = self.sta
            params['chan'] = self.chan
            self.QC_network_report.add_issue(QC_Issue(params))

    def linear_trend_test(self):
        """A test for a linear trend in data with slope greather than\
        some threshold."""
        #Extract waveform data fom self-contained trace object.
        d = self.trace.data()
        #Retrieve data time, endtime and nsamp values
        time,endtime,nsamp = self.trace.getv('time','endtime','nsamp')
        #Find the line which best fits the data in the least squares
        #sense.
        m,b = np.polyfit(np.arange(time,endtime,(endtime-time)/nsamp),d,1)
        #If the slope is outside the acceptable threshold, report a
        #QC issue.
        if m < -self.linear_trend_max or m > self.linear_trend_max:
            params['message'] = 'Linear trend test failed. Slope = %.3f' % m
            params['sta'] = self.sta
            params['chan'] = self.chan
            self.QC_network_report.add_issue(QC_Issue(params))
        
    def skewness_test(self):
        """A test for standard deviation greater than some threshold\
        ."""
        #Create a copy of self-contained trace object.
        tr = self.trace.trcopy()
        #Bandpass filter the data between 0.05 an 1 Hz
        tr.filter('BW 0.05 4 1.0 4')
        #Extract waveform data
        d = tr.data()
        #Destroy the trace object copy.
        tr.trdestroy()
        #Calculate the standard deviation (using 64-bit floating
        #point precision)
        std = np.std(d,dtype=np.float64)
        #If the standard deviation is greater than the acceptable
        #threshold, repor a QC issue.
        if std > self.skewness_max:
            params['message'] = 'Skewness test failed. STD = %.3f' % std
            params['sta'] = self.sta
            params['chan'] = self.chan
            self.QC_network_report.add_issue(QC_Issue(params))
        
#######################################################################

class LoadTrace_Error(Exception):
    """An exception raised by the load_trace() method of a <QC_obj> \
    object."""
    def __init__(self,message):
        """A constructor method."""
        self.message = message
        
#######################################################################

class RunQC_Error(Exception):
    """An exception raices by the runQC() method of a <QC_obj> object\
    ."""
    def __init__(self,message):
        """A constructor method."""
        self.message = message

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
            summary = '%s\t\t%s\n' % (summary,QC_issue.message)
        return summary
            

#######################################################################

class QC_Network_Report():
    """A class containing all QC station reports for the network and \
    method to create a network report."""
    def __init__(self,params):
        """A constructor method."""
        self.QC_station_reports = []
        self.email = params['email']
        self.send_email = params['send_email']
        
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
        summary = 'QC Report for NETWORK - DATE\n\n'
        #For each station report in self-contained list, add lines
        #for that report.
        for QC_station_report in self.QC_station_reports:
            summary = '%s%s\n' % (summary,QC_station_report.summarize())
        return summary
    
    def report(self):
        """Decides whether to print network report to STDOUT or to\
        send e-mail based on 'send_email' flag."""
        if self.send_email: self.send()
        else: print self.summarize()
    
    def send(self):
        """Sends network report to given e-mail addresses."""
        #Import library to provide mail functionality.
        import smtplib
        #Create an anonymous sender. This should probably be done in a
        #more appropriate fashion.
        sender = 'autoQC-noreply@gmail.com'
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
            smtpObj = smtplib.SMTP('smtp.ucsd.edu')
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

def get_stachan_list(dbpath,exclude_stachan,time_lag,time_window):
    """Returns a dictionary of station:[channels] pairs to be QC'd.
    Ignore station channel pairs in exclude_stachan."""
    #If there is an exclude from all stations, handle this case
    #separately.
    if '.*' in exclude_stachan: exclude_all = exclude_stachan.pop('.*')
    else: exclude_all = None
    #Build a subset string to include all channels for all stations
    #not found in the exclud_stachan dictionary.
    l = len(exclude_stachan)
    i = 1
    st = None
    for key in exclude_stachan:
        if i == 1: st = '('
        st = '%ssta !~ /%s/' % (st,key)
        if i < l: st = '%s && ' % st
        else: st = '%s)' % st
        i = i+1
    #Extend the above subset string to include all channels for
    #stations satisfying the above requirement OR the condition that
    #if the station is in the exclude_stachan dicionary, the channel
    #is not.
    for key in exclude_stachan:
        st = '%s || (sta =~ /%s/ && ' % (st,key)
        l = len(exclude_stachan[key])
        i = 1
        for chan in exclude_stachan[key]:
            st = '%schan !~ /%s/' % (st,chan)
            if i < l: st = '%s && ' % st
            i = i+1
        st = '%s )' % st
    #Lastly, expand the subset string to include all station-channel
    #pairs satisfying the above conditions and the condition that the
    #channel is not in the 'exclude_all' list
    if exclude_all:
        l = len(exclude_all)
        i=1
        st = '(%s) && (' % st
        for chan in exclude_all:
            st = '%s chan !~ /%s/' % (st,chan)
            if i < l: st = '%s &&' % st
            else: st = '%s )' % st
            i = i+1
    #Open the input database.
    db = dbopen(dbpath,'r')
    #Look up the sitechan table.
    vw_sitechan = db.lookup(table='sitechan')
    #Calculate start time and end time, for which to search for
    #active stations based on the current time, and the 
    #time_lag/time_window parameters specified in the parameter file.
    ts = str2epoch(epoch2str(now(),'%Y%j')) - time_lag
    te = ts + time_window
    #If the subset expression built above is not empty, subset for those
    #stations satisfying the subset expression which were active
    #during the time period being QC'd.
    if st:
        vw_sitechan = vw_sitechan.subset('%s && ondate < _%f_ && (offdate > \
            _%f_ || offdate == NULL)' % (st,ts,te))
    #Otherwise just subset for active station.
    else:
        vw_sitechan = vw_sitechan.subset('ondate < _%f_ && (offdate > \
            _%f_ || offdate == NULL)' % (ts,te))
    stachan = {}
    #Create a dictionary with a key for each station in the resulting
    #subset. The value for each key is a list of the channels for that
    #station (in the subset).
    for vw_sitechan.record in range(vw_sitechan.nrecs()):
        sta = vw_sitechan.getv('sta')[0]
        if sta in stachan:
            chan = vw_sitechan.getv('chan')[0]
            if chan not in stachan[sta]:
                stachan[sta].append(vw_sitechan.getv('chan')[0])
        else:
            stachan[sta] = [vw_sitechan.getv('chan')[0]]
    #Close the input database
    db.close()
    #Retrn the dictionary
    return stachan

#######################################################################

def get_params():
    """A controlling function to read in and return dictionary of \
    parameters from command lin and parameter file."""
    #Parse command line options
    args = parse_cmd_line()
    #Parse parameter file parameters, allowing command line options
    #to override parameter file parameters.
    params = parse_parameter_file(args)
    #Return dictionary of parameters.
    return params

#######################################################################

def parse_cmd_line():
    """Parses and returns command line options (as an \
    <argparse.Namespace> object)."""
    #Import module to parse command line arguments.
    import argparse
    #Create an argument parser object and some arugments.
    parser = argparse.ArgumentParser(description='Generate automatic, network\
        wide QC report.')
    parser.add_argument('dbpath',nargs=1,metavar='db',help='Input db to be QC\
        \'d.')
    parser.add_argument('-p','-pf','--ParameterFile',nargs=1,help='Parameter\
        file; overrrides default parameter file.')
    parser.add_argument('-m','--Email',nargs=1,help='E-mail; overrides default\
        e-mail.')
    parser.add_argument('-v','--Verbose',nargs=1,help='Verbose output.')
    #Parse arguments and return results.
    return parser.parse_args()

#######################################################################

def parse_parameter_file(args):
    """Parses and returns dictionary of parameters from parameter \
    file. Command line arguments override parameter file parameters."""
    #Create params dictionar and add dbpath from command line
    params = {}
    params['dbpath'] = args.dbpath[0]
    #Read parameter file parameters into params dicionary.
    if args.ParameterFile: pf = pfread(args.ParameterFile)
    else: pf = pfread('autoQC')
    for k in pf.keys():
        params[k] = pf[k]
    #Override parameter file parameters with command line options.
    if args.Email: params['email'] = args.Email[0]
    params['email'] = params['email'].split(',')
    #Retun params dictionary.
    return params

#######################################################################

def main():
    """Main controlling function, creates necesary <QC_obj> objects, \
    initializes QC testing and network report generation."""
    #Get parameters from command line and parameter file.
    #params - A dictionary which will be updated and passed to <QC_obj>
    #constructor method.
    params  = get_params()
    #Create a <QC_network_report> object.
    QC_network_report = QC_Network_Report({'email':params.pop('email'),
        'send_email':params.pop('send_email')})
    #Add reference to QC_network_report to params dictionary.
    params['QC_network_report'] = QC_network_report
    #Remove some parameters from params dictionary and store in the
    #main() local namespace for persistence.
    for k in ['exclude_stachan','RMS_max','RMS_default_max',\
        'RMS_flatline','RMS_default_flatline','DC_offset_max',\
        'DC_offset_default_max','linear_trend_max','linear_trend_default_max',\
        'skewness_max','skewness_default_max']:
        #Convert strings (that look like lists) to lists
        if isinstance(params[k],str): params[k] = eval(params[k])
        #Perform actualy movemet of data from params dictionary to the
        #main() local namespace
        locals()[k] = params.pop(k)
    #Get a dictionary that looks like {sta:[chan,chan,...]} where
    #each sta:chan pair is to be QC'd.
    stachan = get_stachan_list(params['dbpath'],exclude_stachan,
        params['time_lag'],params['time_window'])
    #An empy list in whic all the <QC_obj> objects wil be stored.
    objs = []
    #For each station in the stachan dictionary, update some test
    #parameters, then create <QC_obj> objects for each channel at
    #that station (as specified in stachan dictionary)
    for sta in stachan:
        params['sta'] = sta
        #If there is a RMS_max value associated with this particular
        #station, put it in the params dictionary, otherwise use
        #default
        params['RMS_max'] = RMS_max[sta] if sta in RMS_max else\
            RMS_default_max
        #Do the same for the RMS_flatline value.
        params['RMS_flatline'] = RMS_flatline[sta] if sta in RMS_flatline else\
            RMS_default_flatline
        #And the DC_offset_max value.
        params['DC_offset_max'] = DC_offset_max[sta] if sta in\
            DC_offset_max else DC_offset_default_max
        #And the linear_trend_max value.
        params['linear_trend_max'] = linear_trend_max[sta] if sta in \
            linear_trend_max else linear_trend_default_max
        #And the skewnes_max value.
        params['skewness_max'] = skewness_max[sta] if sta in skewness_max else\
            skewness_default_max
        #Enter the channel loop.
        for chan in stachan[sta]:
            params['chan'] = chan
            #Create <QC_obj> objects.
            objs.append(QC_Obj(params))
    #For each <QC_obj> created, run QC tests
    for obj in objs:
        try:
            obj.runQC()
        except RunQC_Error as err:
            print err.message
    #Create and distribute network report
    QC_network_report.report()

#######################################################################

#import various modules and methods    
import sys
import os
sys.path.append(os.environ['ANTELOPE'] + '/data/python')
from antelope.stock import pfread, str2epoch, epoch2str, now
from antelope.datascope import dbopen, dbclose, dblookup
from math import pow, fsum, sqrt
import numpy as np

main() #begin main execution