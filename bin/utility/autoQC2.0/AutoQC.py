# -*- coding: utf-8 -*-
"""
Usage: AutoQC -i dbin -o dbout -p pf -m emails

This program provides the ability to run user-defined quality control
tests and send e-mail reports base on the results of these tests.

A QC test is here viewed as consisting of two steps. The calculation of
some quantity useful for QC, and a test to see if that value falls
within an acceptable range. So, creation of QC tests is broken into two 
components. QC test definition and configuration is spread aross three 
files. 

The quantities to be calculated are user defined via a Python module.
The restrictions for defining a QC quantity are as follows:
- All QC quantities must be defined within a single Python module.
- Each QC quantity must be be returned (with appropriate format) from 
a function.
- The name of that function will be bound to that QC quantity in 
parameter files and must not overflow the meastype field of the wfmeas
table (ie. 10 characters).
- That function must accept as input a Trace4.1 schema trace object and 
a (potentially empty) user-defined dictionary of parameters.
- The format of the return value from that function must be a 
dictionary whose keys correspond to fields in the CSS3.0 schema wfmeas
table and whose values will be stored in those fields.
- At a minimum the return value must contain 'meastype' and 'val1' keys
with corresponding values.
So long as these basic restrictions are met, anything that is legal in
Python, is legal here.

Eg.
#An acceptable QC quantity definition
#For more examples see default QC quantity definitions in
#QCQuantities.py
def DC_offset(tr,params):
    d = tr.data()
    m = sum(d)/len(d)
    return {'meastype': 'mean', 'val1': m, 'units1': 'cts'}

The rest of the configuration of any QC test is done via two
parameter files.

The AutoQC.pf parameter file.
In this parameter file, calculation of each QC quantity can be turned 
on or off, and a dictionary of parameters can be defined. This 
dictionary of parameters will be passed, as is, to the corresponding 
function responsible for calculating that quantity. See the default
AutoQC.pf file for further explanation and examples.

The QCReport.pf parameter file.
In this parameter file, the acceptable range for a given QC quantity
is defined along with parameters for configuring e-mail reporting.
Through this parameter file it is possible to define acceptable
QC quantity ranges on a per station basis. See the default QCReport.pf
file for further explanation and examples.  

Last edited: Thursday Nov 7, 2013
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego
        
"""
class QC_Obj:
    
    """
    Contain data to calculate QC quantities for single station/channel.

    Behaviour:
    Contain all data needed to calculate QC quantities for single 
    station/channel and provide functionality to initiate those 
    calculations.
    
    Public Instance Variables:
    dbin
    dbout
    sta
    chan
    tstart
    tend
    qc_quantities
    tr
    
    Public Functions:
    calculate_qc_quantities
    load_trace
    
    """    
    
    def __init__(self, params):
        """
        Constructor method. Initialize QC_Obj instance.

        Behaviour:
        Store input parameters, create a list of QC_Quantity objects.
        
        Arguments:
        params - All parameters <dict>
        params['dbin'] - Input database <str>
        params['dbout'] - Output database <str>
        params['sta'] - Station <str>
        params['chan'] - Channel <str>
        params['tstart'] - Epoch start time <float>
        params['tend'] - Epoch end time <float>
        params['quantities'] - Quantity calculation parameters <dict>

        Return Values:
        <instance> QC_Obj

        """
        self.dbin = params['dbin']
        self.dbout = params['dbout']
        self.sta = params['sta']
        self.chan = params['chan']
        self.tstart = params['tstart']
        self.tend = params['tend']
        self.qc_quantities = []
        self.tr = None
        for quantity in params['quantities'].keys():
            if params['quantities'][quantity]['calculate']:
                quantity_params = params['quantities'][quantity]
                quantity_params['parent'] = self
                self.qc_quantities.append(QC_Quantity(quantity_params))
        
    def calculate_qc_quantities(self):
        """
        Initiate QC tests.
        
        Behaviour:
        Initiate QC tests.
        
        Side Effects:
        Load Trace4.1 schema Trace object into public instance 
        variable self.tr.
                
        """
        try:
            self.load_trace()
            for quantity in self.qc_quantities:
                quantity.calculate()
        except LoadTrace_Error as err:
            print err.message

    def load_trace(self):
        """
        Load Trace4.1 schema Trace object.
        
        Behaviour:
        Load Trace4.1 schema Trace object into public instance
        variable self.tr.
        
        Exceptons Raised:
        LoadTrace_Error

        """
        from antelope.datascope import dbopen
        db = dbopen(self.dbin, 'r')
        vw_wf = db.lookup(table='wfdisc')
        #An optimization: try to find a single wfdisc row that contains
        #the entire segment of data to be requested.
        i = vw_wf.find('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime\
            >= _%f_' % (self.sta, self.chan, self.tstart, self.tend), \
            vw_wf.nrecs(), reverse=True)
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
                    endtime >= _%f_' % (self.sta, self.chan, self.tend, \
                    self.tstart), i, reverse=True)
                if not i < 0:
                    recs.append(i)
                #If no records were found, raise an error stating that
                #data was unretrievable
                elif len(recs) == 0:
                    raise LoadTrace_Error('No records found in wfdisc for %s:'\
                        ' %s' % (self.sta, self.chan))
                    return 0
            vw_wf = vw_wf.list2subset(recs)
        tr = vw_wf.loadchan(self.tstart, self.tend, self.sta, self.chan)
        tr.record = 0
        self.tr = tr
        db.close()
    
class QC_Quantity:

    """
    Contain functionality/parameters to calculate single QC quantity.

    Behaviour:
    Contain parameters needed to run a single QC test and provide
    functionality to perform those tests.
    
    Public Instance Variables:
    test
    params
    parent
    
    Public Functions:
    run
    log

    """

    def __init__(self, params):
        """
        Constructor method. Initialize QC_Quantity instance.

        Behaviour:
        Store input parameters.
        
        Arguments:
        params - All parameters <dict>.
        params['function'] - a function to perform QC test <function>
        params['params_in'] - user-def input parameters <dict> 
        params['parent'] - spawning QC_Obj instance <instance>
        
        Return Values:
        <instance> QC_Quantity

        """
        self.calc_function = params['function']
        self.params = params['params_in']
        self.parent = params.pop('parent')

    def calculate(self):
        """Calculate QC quantity and initiate logging of results."""
        self.log(self.calc_function(self.parent.tr, self.params))
    
    def log(self,params):
        """Record results of QC test to output database."""
        from antelope.datascope import dbopen
        db = dbopen(self.parent.dbout, 'r+')
        vw_wfmeas = db.lookup(table='wfmeas')
        vw_wfmeas.record = vw_wfmeas.addnull()
        vw_wfmeas.putv('sta', self.parent.sta, 'chan', self.parent.chan, \
            'time', self.parent.tstart, 'endtime', self.parent.tend)
        for k in params.keys():
            vw_wfmeas.putv('%s' % k, params[k])
        db.close()


class LoadTrace_Error(Exception):

    """
    An exception raised when loading a trace object.

    Public Instance Variables:
    message

    """

    def __init__(self, message):
        """Constructor method. Initialize LoadTrace_Error instance.
        
        Behaviour:
        Store an input eror message.
        
        Arguments:
        message - an error messge
        
        Return Values:
        <instance> LoadTrace_Error
        """
        self.message = message
        
def get_stachan_dict(dbin, exclude_stachan, tstart, tend):
    """
    Return a dictionary of station:[channel_list] pairs.
    
    Behaviour:
    Generate and return a dictionary of station:[channels] pairs 
    to be QC tested.

    Arguments:
    dbin - Input database <str>
    exclude_stachan - Station:[channels] pairs not to be testsd <dict>
    tstart - Epoch start time
    tend - Epoch end time

    Return Values:
    <dict> of station:[channels] pairs to e QC tested.

    """
    from antelope.datascope import dbopen
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
        st = '%ssta !~ /%s/' % (st, key)
        if i < l: st = '%s && ' % st
        else: st = '%s)' % st
        i = i+1
    #Extend the above subset string to include all channels for
    #stations satisfying the above requirement OR the condition that
    #if the station is in the exclude_stachan dicionary, the channel
    #is not.
    for key in exclude_stachan:
        st = '%s || (sta =~ /%s/ && ' % (st, key)
        l = len(exclude_stachan[key])
        i = 1
        for chan in exclude_stachan[key]:
            st = '%schan !~ /%s/' % (st, chan)
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
            st = '%s chan !~ /%s/' % (st, chan)
            if i < l: st = '%s &&' % st
            else: st = '%s )' % st
            i = i+1
    #Open the input database.
    db = dbopen(dbin, 'r')
    #Look up the sitechan table.
    vw_sitechan = db.lookup(table='sitechan')
    #If the subset expression built above is not empty, subset for those
    #stations satisfying the subset expression which were active
    #during the time period being QC'd.
    if st:
        vw_sitechan = vw_sitechan.subset('%s && ondate < _%f_ && (offdate > \
            _%f_ || offdate == NULL)' % (st, tstart, tend))
    #Otherwise just subset for active station.
    else:
        vw_sitechan = vw_sitechan.subset('ondate < _%f_ && (offdate > \
            _%f_ || offdate == NULL)' % (tstart, tend))
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
    db.close()
    return stachan

def parse_cmd_line():
    """
    Parse command line options and return results.

    Behaviour:
    Parse command line options and return results as a
    <class 'argparse.Namespace'> instance.

    Return Values:
    <class 'argparse.Namespace'> instance containing command line
    arguments.
    
    Side Effects:
    Produce usage line.

    """
    import argparse
    parser = argparse.ArgumentParser(description='Generate automatic, network\
        wide QC report.')
    parser.add_argument('-i', '-dbin', '--Input_Database', nargs=1, \
        help='Input database to be QC\'d. Overrides default input database \
        (parameter file).')
    parser.add_argument('-o', '-dbout', '--Output_Database', nargs=1, \
        help='Output database, overrides default output database (parameter \
        file).')
    parser.add_argument('-p', '-pf', '--Parameter_File', nargs=1, \
        help='Parameter file; overrrides default parameter file.')
    parser.add_argument('-m', '--Email', nargs=1, help='E-mail; overrides \
        default e-mail.')
    parser.add_argument('-v', '--Verbose', nargs=1, help='Verbose output.')
    return parser.parse_args()
        
def parse_params():
    """
    Initiate parsing of command line and parameter file, return results.
    """
    return parse_pf(parse_cmd_line())

def parse_pf(args):
    """Parse parameter file, return results.
    
    Behaviour:
    Parse parameter file and  return results as a dictionary. Allow
    command line arguments to override parameter file arguments.
    
    Arguments:
    args - command line arguments <class 'argparse.Namespace'>
    
    Return Values:
    <dict> of parameters

    """
    import sys
    from importlib import import_module
    from antelope.stock import pfread,str2epoch,epoch2str,now
    from math import floor
    params = {}
    if args.Parameter_File: pf = pfread(args.parameter_File)
    else: pf = pfread('AutoQC')
    for k in pf.keys():
        params[k] = pf[k]
    if args.Email: params['email'] = args.Email[0]
    if args.Input_Database: params['dbin'] = args.Input_Database
    if args.Output_Database: params['dbout'] = args.Output_Database
    params['tstart'] = str2epoch(epoch2str(now(), '%Y%j')) - \
        params.pop('time_lag')*86400
    params['tend'] = params['tstart'] + params.pop('time_window')*86400.0
    for k in params['exclude_stachan']:
        params['exclude_stachan'][k] = eval(params['exclude_stachan'][k])
    sys.path.append(params['module_path'])
    QCQuantities_module = import_module(params.pop('module_name'))
    sys.path.remove(params.pop('module_path'))
    for k in params['quantities']:
        params['quantities'][k]['calculate'] = \
            eval(params['quantities'][k]['calculate'])
        params['quantities'][k]['function'] = eval('QCQuantities_module.%s' % k)
        for l in params['quantities'][k]['params_in']:
            try:
                params['quantities'][k]['params_in'][l] = \
                    eval(params['quantities'][k]['params_in'][l])
            except (NameError, SyntaxError):
                pass    
    return params

def main():
    """
    Main function. Initiate and maintain control sequence.

    Behaviour:
    Initiate parsing of parameters, generate <instance>s of QC_Obj,
    intiate QC testing, and initiate QC report generation/distribution.

    """
    import sys
    import os
    sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
    params = parse_params()
    stachans = get_stachan_dict(params['dbin'], params.pop('exclude_stachan'),
        params['tstart'], params['tend'])
    qc_objs = []
    for sta in stachans:
        params['sta'] = sta
        for chan in stachans[sta]:
            params['chan'] = chan
            qc_objs.append(QC_Obj(params))
    for qc_obj in qc_objs:
        qc_obj.calculate_qc_quantities()
    import QCReport
    QCReport.generate_report({'dbin': params['dbout'], 'pf': 'QCReport', \
        'tstart': params['tstart'], 'tend': params['tend']})    
   
main()