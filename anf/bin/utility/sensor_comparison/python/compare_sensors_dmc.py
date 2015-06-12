import sys
import os
sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
import matplotlib.pyplot as plt
from antelope.datascope import closing,\
                               dbopen
from antelope.stock import epoch2str
from argparse import ArgumentParser
from numpy import arange,\
                  array
from obspy.fdsn.client import Client
from obspy.core.utcdatetime import UTCDateTime
from scipy.signal import resample

freq_band_lco = 1
freq_band_uco = 10

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('net1', type=str, help='network 1')
    parser.add_argument('sta1', type=str, help='station 1')
    parser.add_argument('chan1', type=str, help='channel 1')
    parser.add_argument('net2', type=str, help='network 2')
    parser.add_argument('sta2', type=str, help='station 2')
    parser.add_argument('chan2', type=str, help='channel 2')
    parser.add_argument('dbmaster', type=str, help='dbmaster')
    parser.add_argument('time', type=float, help='start time')
    parser.add_argument('endtime', type=float, help='end time')
    parser.add_argument('-p', '--pfile', type=str, help='parameter file')
    return parser.parse_args()

'''
def parse_pf(pfile):
    if pfile:
        pfile = os.path.abspath(pfile)
        if os.path.splitext(pfile)[1] == '.pf':
            pfile = pfin(pfile)
        else:
            pfile = pfin(pfile)
    else:
        pfile = pfread('compare_sensors_ant')
    return eval_dict(pfile.pf2dict())

def eval_dict(my_dict):
    for key in my_dict:
        if isinstance(my_dict[key], dict):
            eval_dict(my_dict[key])
        else:
            if key in locals():
                continue
            try:
                my_dict[key] = eval(my_dict[key])
            except (NameError, SyntaxError):
                pass

    return my_dict
'''

def get_data():
    global args, pfile
    try:
        client = Client("IRIS")
        time = UTCDateTime(args.time)
        endtime = UTCDateTime(args.endtime)
        loc1 = "*" if args.chan1[3:] == "" else args.chan1[3:]
        loc2 = "*" if args.chan2[3:] == "" else args.chan2[3:]
        args.chan1 = args.chan1[:3]
        args.chan2 = args.chan2[:3]
        st = client.get_waveforms_bulk([(args.net1, args.sta1, loc1, args.chan1, time, endtime),
                                        (args.net2, args.sta2, loc2, args.chan2, time, endtime)
                                       ]
                                      )
    except Exception:
        #actually do something here.
        raise
    return (st[0], st[1])

def process_data(data):
    global args, pfile
    tr1, tr2 = data
    calib1, calib2 = get_calib_values()
    print calib1, calib2
    if calib1 != 1.0:
        tr1.data = array([x * calib1 for x in tr1.data])
    if calib2 != 1.0:
        tr2.data = array([x * calib2 for x in tr2.data])
    tr1.detrend('demean')
    tr1.differentiate()
    tr1.filter('bandpass',
               freqmin=freq_band_lco,
               freqmax=freq_band_uco,
               corners=3)
    tr2.detrend('demean')
    tr2.filter('bandpass',
               freqmin=freq_band_lco,
               freqmax=freq_band_uco,
               corners=3)
    tr1, tr2 = tr1.data, tr2.data
    if len(tr1) > len(tr2):
        tr1 = resample(tr1, len(tr2))
    elif len(tr2) > len(tr1):
        tr2 = resample(tr2, len(tr1))
    return (tr1, tr2)

def get_calib_values():
    with closing(dbopen(args.dbmaster)) as db:
        tbl_sitechan = db.lookup(table='sitechan')
        view = tbl_sitechan.subset('sta =~ /{}/ && chan =~ '\
                '/{}/ && ondate < _{}_ && '\
                '(offdate > _{}_ || offdate == -1)'.format(args.sta1,
                                                           args.chan1,
                                                           args.time,
                                                           args.endtime))
        view_ = view.join('sensor')
        view.free()
        view = view_
        view_ = view.join('instrument')
        view.free()
        view = view_
        view.record = 0
        calib1 = view.getv('ncalib')[0]
        view.free()
        view = tbl_sitechan.subset('sta =~ /{}/ && chan =~ '\
                '/{}/ && ondate < _{}_ && '\
                '(offdate > _{}_ || offdate == -1)'.format(args.sta2,
                                                           args.chan2,
                                                           args.time,
                                                           args.endtime))
        view_ = view.join('sensor')
        view.free()
        view = view_
        view_ = view.join('instrument')
        view.free()
        view = view_
        view.record = 0
        calib2 = view.getv('ncalib')[0]
    return calib1, calib2

def plot_data(data):
    global args, pfile
    tr1, tr2 = data
    fig = plt.figure(figsize=(12, 6))
    axs = [fig.add_subplot(3, 1, i) for i in (1, 2, 3)]
    axs[0].plot(tr1, 'b')
    axs[1].plot(tr2, 'r', linestyle='--')
    axs[2].plot(tr1, 'b')
    axs[2].plot(tr2, 'r', linestyle='--')
    axs[0].set_ylabel("{} : {}".format(args.sta1, args.chan1), fontsize=16)
    axs[1].set_ylabel("{} : {}".format(args.sta2, args.chan2), fontsize=16)
    xticks = arange(0, len(tr1), len(tr1) / 4)
    dt = (args.endtime - args.time) / len(tr1)
    xtick_labels = [epoch2str(t, "%Y%j %H:%M:%S.%s") for t in\
            [args.time + x * dt for x in xticks]]
    for i in range(len(axs)):
        axs[i].set_xticks(xticks)
        axs[i].set_xticklabels(xtick_labels)
    plt.show()

def main():
    global args, pfile
    args = parse_args()
    #pfile = parse_pf(args.pfile)
    pfile = None
    plot_data(process_data(get_data()))

if __name__ == '__main__':
    main()
