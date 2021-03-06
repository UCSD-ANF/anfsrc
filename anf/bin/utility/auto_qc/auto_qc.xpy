"""
Usage: auto_qc -i dbin -o dbout -p pf -m emails

This program provides the ability to run user-defined quality control
tests and send e-mail reports based on the results of these tests.

The tests to be run are user defined via a Python module.
The restrictions for defining a QC test are as follows:
- All QC tests must be defined within a single Python module.
- Each QC tests must be be returned (with appropriate format) from
a function.
- That function must accept as input a Trace4.1 schema trace object and
a (potentially empty) user-defined dictionary of parameters.
- The format of the return value from that function must be a
dictionary (or list of dictionaries) whose keys correspond to fields in the
CSS3.0 schema wfmeas table and whose values will be stored in those fields.
- At a minimum the return dictionary must contain 'meastype' and 'val1' keys
with corresponding values.
- For each failure of a QC test, one dictionary should be returend. Multiple
dictionaries are returned in a list of dictionaries.
So long as these basic restrictions are met, anything that is legal in
Python, is legal here.

Eg.
#An acceptable QC test definition
#For more examples see default QC test definitions in
#qc_tests.py
def DC_offset(tr,params):
    d = tr.data()
    m = sum(d)/len(d)
    ret = []
    if m > params['thresh']:
        ret.append({'meastype': 'mean', 'val1': m, 'units1': 'cts'})
    return ret

The rest of the configuration of any QC test is done via two
parameter files.

The auto_qc.pf parameter file.
In this parameter file, each QC test can be turned
on or off, and a dictionary of parameters can be defined. This
dictionary of parameters will be passed, as is, to the corresponding
test function. See the default
auto_qc.pf file for further explanation and examples.

Last edited: Wed Jan 8, 2014
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego

"""
class QC_Obj:

    """
    Contain data to run QC tests for single station/channel.

    Behaviour:
    Contain all data needed to run QC tests for single
    station/channel and provide functionality to initiate those
    tests.

    Public Instance Variables:
    dbin
    dbout
    sta
    chan
    tstart
    tend
    qc_tests
    tr

    Public Functions:
    run_qc_tests
    load_trace

    """

    def __init__(self, params):
        """
        Constructor method. Initialize QC_Obj instance.

        Behaviour:
        Store input parameters, create a list of QC_Test objects.

        Arguments:
        params - All parameters <dict>
        params['dbin'] - Input database <str>
        params['dbout'] - Output database <str>
        params['sta'] - Station <str>
        params['chan'] - Channel <str>
        params['tstart'] - Epoch start time <float>
        params['tend'] - Epoch end time <float>
        params['tests'] - test parameters <dict>

        Return Values:
        <instance> QC_Obj

        """
        self.dbin = params['dbin']
        self.dbout = params['dbout']
        self.sta = params['sta']
        self.chan = params['chan']
        self.tstart = params['tstart']
        self.tend = params['tend']
        self.qc_tests = []
        self.tr = None
        for test in params['tests'].keys():
            if params['tests'][test]['run']:
                test_params = params['tests'][test]
                test_params['parent'] = self
                self.qc_tests.append(QC_Test(test_params))

    def run_qc_tests(self):
        """
        Initiate QC tests.

        Behaviour:
        Initiate QC tests.

        Side Effects: +
        Load Trace4.1 schema Trace object into public instance
        variable self.tr.

        """
        try:
            self.load_trace()
            for test in self.qc_tests:
                test.run()
        except LoadTrace_Error as err:
            print err.message
        self.tr.trdestroy()

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
                        '%s' % (self.sta, self.chan))
                    return 0
            vw_wf = vw_wf.list2subset(recs)
        tr = vw_wf.loadchan(self.tstart, self.tend, self.sta, self.chan)
        tr.record = 0
        self.tr = tr
        db.close()

class QC_Test:

    """
    Contain functionality/parameters to run single QC test.

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
        <instance> QC_Test

        """
        self.test_function = params['function']
        self.params = params['params_in']
        self.parent = params.pop('parent')

    def run(self):
        """Run QC test and initiate logging of results."""
        self.log(self.test_function(self.parent.tr, self.params))

    def log(self,params):
        """Record results of QC test to output database."""
        from antelope.datascope import dbopen
        db = dbopen(self.parent.dbout, 'r+')
        vw_wfmeas = db.lookup(table='wfmeas')
        if isinstance(params, dict):
            vw_wfmeas.record = vw_wfmeas.addnull()
            vw_wfmeas.putv('sta', self.parent.sta, 'chan', self.parent.chan, \
                'time', self.parent.tstart, 'endtime', self.parent.tend)
            for k in params:
                vw_wfmeas.putv('%s' % k, params[k])
        elif isinstance(params, list):
            for p in params:
                vw_wfmeas.record = vw_wfmeas.addnull()
                vw_wfmeas.putv('sta', self.parent.sta, 'chan', \
                    self.parent.chan, 'time', self.parent.tstart, 'endtime', \
                    self.parent.tend)
                for k in p:
                    vw_wfmeas.putv('%s' % k, p[k])
        elif params == None: pass
        else:
            print 'Invalid return type - %s - in function - %s' \
                % (type(params), self.test_function)
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

def get_stachan_dict(dbin, subset, tstart, tend):
    """
    Return a dictionary of station:[channel_list] pairs.

    Behaviour:
    Generate and return a dictionary of station:[channels] pairs
    to be QC tested.

    Arguments:
    dbin - Input database <str>
    subset - Subset expression of station:channels to be QC'd <str>
    tstart - Epoch start time <float>
    tend - Epoch end time <float>

    Return Values:
    <dict> of station:[channels] pairs to e QC tested.

    """
    from antelope.datascope import dbopen
    db = dbopen(dbin, 'r')
    vw_wfdisc = db.lookup(table='wfdisc')
    if subset:
        vw_wfdisc = vw_wfdisc.subset('(%s) && time < _%f_ && endtime > _%f_' \
            % (subset, tend, tstart))
    else:
        vw_wfdisc = vw_wfdisc.subset('time < _%f_ && endtime > _%f_' % \
            (tend, tstart))
    stachan = {}
    for vw_wfdisc.record in range(vw_wfdisc.nrecs()):
        sta = vw_wfdisc.getv('sta')[0]
        if sta in stachan:
            chan = vw_wfdisc.getv('chan')[0]
            if chan not in stachan[sta]:
                stachan[sta].append(vw_wfdisc.getv('chan')[0])
        else:
            stachan[sta] = [vw_wfdisc.getv('chan')[0]]
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
    Produce usage line, help.

    """
    from os.path import exists, basename
    import argparse
    parser = argparse.ArgumentParser(description='Generate automatic, network'
        'wide QC report.')
    parser.add_argument('-i', '-I', '-dbin', '--Input_Database', nargs=1, \
        help='Input database to be QC\'d. Overrides default input database '
        '(parameter file).')
    parser.add_argument('-o', '-O', '-dbout', '--Output_Database', nargs=1, \
        help='Output database, overrides default output database (parameter '
        'file).')
    parser.add_argument('-p', '-P', '-pf', '-PF', '--Parameter_File', nargs=1,
        help='Parameter file; overrrides default parameter file.')
    parser.add_argument('-m', '-M', '--Email', nargs=1, help='E-mail; overrides'
        ' default e-mail.')
    parser.add_argument('-v', '-V', '--Verbose', action='store_true',
        help='Verbose output.')
    parser.add_argument('-t', '-T', '--Testing', nargs=1, type=int,
        help="Testing mode - run over 'Testing' stachans.")
    args = parser.parse_args()
    if not args.Parameter_File and not exists(basename('%s.pf' % sys.argv[0])):
        print 'Please provide a valid parameter file.'
        parser.print_help()
        sys.exit(-1)
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
    from os.path import basename
    from importlib import import_module
    from antelope.stock import pfread, str2epoch, epoch2str, now
    params = {}
    if args.Parameter_File: pf = pfread(args.Parameter_File[0])
    else: pf = pfread(basename(sys.argv[0]))
    for k in pf.keys():
        params[k] = pf[k]
    if args.Email: params['email'] = args.Email[0]
    if args.Input_Database: params['dbin'] = args.Input_Database
    if args.Output_Database: params['dbout'] = args.Output_Database
    if args.Testing: params['testing'] = args.Testing[0]
    params['tstart'] = str2epoch(epoch2str(now(), '%Y%j')) - \
        params.pop('time_lag')*86400
    params['tend'] = params['tstart'] + params.pop('time_window')*86400.0
    sys.path.append(params['module_path'])
    QCTests_module = import_module(params.pop('module_name'))
    sys.path.remove(params.pop('module_path'))
    for k in params['tests']:
        params['tests'][k]['run'] = \
            eval(params['tests'][k]['run'])
        params['tests'][k]['function'] = eval('QCTests_module.%s' \
            % params['tests'][k]['function'])
        for l in params['tests'][k]['params_in']:
            try:
                params['tests'][k]['params_in'][l] = \
                    eval(params['tests'][k]['params_in'][l])
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
    params = parse_params()
    stachans = get_stachan_dict(params['dbin'], params.pop('subset'),
        params['tstart'], params['tend'])
    qc_objs = []
    for sta in stachans:
        params['sta'] = sta
        for chan in stachans[sta]:
            params['chan'] = chan
            qc_objs.append(QC_Obj(params))
    if 'testing' in params:
        print 'Running in test mode'
        i=0
        while i < params['testing']:
            qc_obj = qc_objs[i]
            print '%s:%s' % (qc_obj.sta, qc_obj.chan)
            qc_obj.run_qc_tests()
            i += 1
    else:
        for qc_obj in qc_objs:
            print '%s:%s' % (qc_obj.sta, qc_obj.chan)
            qc_obj.run_qc_tests()
    import qc_report
    qc_report.generate_report({'dbin': params['dbout'], \
        'pf': params['qc_report_pf'], 'tstart': params['tstart'], \
        'tend': params['tend']})

if __name__ == '__main__': sys.exit(main())
else: sys.exit("Not a module to import!!")
