# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 15:02:39 2013

@author: mcwhite
"""
########################################################################

class QC_Obj:
    def __init__(self,params):
        self.dbin = params['dbin']
        self.dbout = params['dbout']
        self.sta = params['sta']
        self.chan = params['chan']
        self.tstart = params['tstart']
        self.tend = params['tend']
        self.QC_tests = []
        self.tr = None
        for test in params['tests'].keys():
            if params['tests'][test]['run']:
                test_params = params['tests'][test]
                test_params['parent'] = self
                self.QC_tests.append(QC_Test(test_params))
        
    def test(self):
        """Run all QC tests and record results in output wfmeas table.\
        """
        try:
            self.tr = self.load_trace()
            for test in self.QC_tests:
                test.run()
        except LoadTrace_Error as err:
            print err.message

    def load_trace(self):
        from antelope.datascope import dbopen
        """Return a Trace4.1 schema trace object. Waveform data \
        returned is in raw counts."""
        #Open input databse.
        db = dbopen(self.dbin,'r')
        #Look up wfdisc table
        vw_wf = db.lookup(table='wfdisc')
        #An optimization: try to find a single wfdisc row that contains
        #the entire segment of data to be requested.
        i = vw_wf.find('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime\
            >= _%f_' % (self.sta, self.chan, self.tstart, self.tend),vw_wf.nrecs(),
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
                    endtime >= _%f_' % (self.sta,self.chan,self.tend,self.tstart),
                        i,reverse=True)
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
        tr = vw_wf.loadchan(self.tstart,self.tend,self.sta,self.chan)
        tr.record = 0
        #Close the input database
        db.close()
        return tr
    
########################################################################
    
class QC_Test:
    def __init__(self,params):
        self.test = params['method']
#        self.parent = params.pop('parent')
        self.params = params['input_parameters']
        self.parent = params.pop('parent')

    def run(self):
        self.log(self.test(self.parent.tr,self.params))
    
    def log(self,params):
        """Records results of QC test to output database."""
        from antelope.datascope import dbopen
        db = dbopen(self.parent.dbout,'r+')
        vw_wfmeas = db.lookup(table='wfmeas')
        vw_wfmeas.record = vw_wfmeas.addnull()
        vw_wfmeas.putv('sta',self.parent.sta,'chan',self.parent.chan,'time',
                       self.parent.tstart,'endtime',self.parent.tend)
        for k in params.keys():
            vw_wfmeas.putv('%s' % k,params[k])
        db.close()
        
#######################################################################

class LoadTrace_Error(Exception):
    """An exception raised by the load_trace() method of a <QC_obj> \
    object."""
    def __init__(self,message):
        """A constructor method."""
        self.message = message
        
########################################################################

#class RunQC_Error(Exception):
#    """An exception raices by the runQC() method of a <QC_obj> object\
#    ."""
#    def __init__(self,message):
#        """A constructor method."""
#        self.message = message

#######################################################################

def parse_params():
    return parse_pf(parse_cmd_line())

########################################################################

def parse_cmd_line():
    """Parses and returns command line options (as an \
    <argparse.Namespace> object)."""
    #Import module to parse command line arguments.
    import argparse
    #Create an argument parser object and some arugments.
    parser = argparse.ArgumentParser(description='Generate automatic, network\
        wide QC report.')
    parser.add_argument('-i','-dbin','--Input_Database',nargs=1,help='Input\
        database to be QC\'d. Overrides default input database (parameter\
        file).')
    parser.add_argument('-o','-dbout','--Output_Database',nargs=1,
        help='Output database, overrides default output database (parameter \
        file).')
    parser.add_argument('-p','-pf','--Parameter_File',nargs=1,help='Parameter\
        file; overrrides default parameter file.')
    parser.add_argument('-m','--Email',nargs=1,help='E-mail; overrides default\
        e-mail.')
    parser.add_argument('-v','--Verbose',nargs=1,help='Verbose output.')
    #Parse arguments and return results.
    return parser.parse_args()
 
########################################################################

def parse_pf(args):
    import sys
    from importlib import import_module
    from antelope.stock import pfread,str2epoch,epoch2str,now
    from math import floor
    params = {}
    if args.Parameter_File: pf = pfread(args.parameter_File)
    else: pf = pfread('autoQC2.0')
    for k in pf.keys():
        params[k] = pf[k]
    if args.Email: params['email'] = args.Email[0]
    if args.Input_Database: params['dbin'] = args.Input_Database
    if args.Output_Database: params['dbout'] = args.Output_Database
    #params['tstart'] = str2epoch('%f' % float((epoch2str(now(),'%Y%j')) -
    #    params.pop('time_lag')))
    params['tstart'] = str2epoch(epoch2str(now(),'%Y%j')) - \
        params.pop('time_lag')*86400
    params['tend'] = params['tstart'] + params.pop('time_window')*86400.0
    for k in params['exclude_stachan'].keys():
        params['exclude_stachan'][k] = eval(params['exclude_stachan'][k])
    sys.path.append(params['module_path'])
    QC_Tests_module = import_module(params.pop('module_name'))
    sys.path.remove(params.pop('module_path'))
    for k in params['tests'].keys():
        params['tests'][k]['run'] = eval(params['tests'][k]['run'])
        params['tests'][k]['method'] = eval('QC_Tests_module.%s' % k)
        for l in params['tests'][k]['input_parameters'].keys():
            try:
                params['tests'][k]['input_parameters'][l] = \
                    eval(params['tests'][k]['input_parameters'][l])
            except (NameError,SyntaxError):
                pass    
    return params

#######################################################################

def get_stachan_dict(dbin,exclude_stachan,tstart,tend):
    from antelope.datascope import dbopen
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
    db = dbopen(dbin,'r')
    #Look up the sitechan table.
    vw_sitechan = db.lookup(table='sitechan')
    #If the subset expression built above is not empty, subset for those
    #stations satisfying the subset expression which were active
    #during the time period being QC'd.
    if st:
        vw_sitechan = vw_sitechan.subset('%s && ondate < _%f_ && (offdate > \
            _%f_ || offdate == NULL)' % (st,tstart,tend))
    #Otherwise just subset for active station.
    else:
        vw_sitechan = vw_sitechan.subset('ondate < _%f_ && (offdate > \
            _%f_ || offdate == NULL)' % (tstart,tend))
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

def main():
    import sys
    import os
    sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
    params = parse_params()
    network = params.pop('network')
    stachans = get_stachan_dict(params['dbin'],params.pop('exclude_stachan'),
        params['tstart'],params['tend'])
    QC_objs = []
    for sta in stachans.keys():
        params['sta'] = sta
        for chan in stachans[sta]:
            params['chan'] = chan
            QC_objs.append(QC_Obj(params))
#    for QC_obj in QC_objs:
#        QC_obj.test()
#    i = 0
#    while i < 9:
#        i = i+1
#        QC_objs[i].test()
    import SendQCReport
    SendQCReport.send_report({'dbin': params['dbout'], 'pf': 'SendQCReport', \
        'network': network,'tstart': params['tstart'], \
        'tend': params['tend']})    
   
main()