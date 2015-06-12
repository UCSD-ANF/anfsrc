import sys
import os
import matplotlib.pyplot as plt
sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
from antelope.datascope import closing,\
                               dbopen
from antelope.stock import epoch2str,\
                           pfin,\
                           pfread
from argparse import ArgumentParser
from numpy import arange
from scipy.signal import resample

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('sta1', type=str, help='station 1')
    parser.add_argument('chan1', type=str, help='channel 1')
    parser.add_argument('db1', type=str, help='database 1')
    parser.add_argument('sta2', type=str, help='station 2')
    parser.add_argument('chan2', type=str, help='channel 2')
    parser.add_argument('db2', type=str, help='database 2')
    parser.add_argument('time', type=float, help='start time')
    parser.add_argument('endtime', type=float, help='end time')
    parser.add_argument('-p', '--pfile', type=str, help='parameter file')
    return parser.parse_args()

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

def get_data():
    global args, pfile
    try:
        with closing(dbopen(args.db1, 'r')) as db1:
            tbl_wfdisc1 = db1.lookup(table='wfdisc')
            tr1 = tbl_wfdisc1.trloadchan(args.time,
                                         args.endtime,
                                         args.sta1,
                                         args.chan1)
        with closing(dbopen(args.db2, 'r')) as db2:
            tbl_wfdisc2 = db2.lookup(table='wfdisc')
            tr2 = tbl_wfdisc2.trloadchan(args.time,
                                         args.endtime,
                                         args.sta2,
                                         args.chan2)
    except Exception:
        #actually do something here.
        raise
    return (tr1, tr2)

def process_data(data):
    global args, pfile
    tr1, tr2 = data
    tr1.trapply_calib()
    tr2.trapply_calib()
    freq_filter = "BW {} {} {} {}".format(pfile['freq_band_lco'],
                                          pfile['freq_band_lco_order'],
                                          pfile['freq_band_uco'],
                                          pfile['freq_band_uco_order'])
    tr1.trfilter("DEMEAN; DIF; {}".format(freq_filter))
    tr2.trfilter("DEMEAN; {}".format(freq_filter))
    tr1.record, tr2.record = 0, 0
    tr1, tr2 = tr1.trdata(), tr2.trdata()
    if len(tr1) > len(tr2):
        tr1 = resample(tr1, len(tr2))
    elif len(tr2) > len(tr1):
        tr2 = resample(tr2, len(tr1))
    return (tr1, tr2)

def plot_data(data):
    global args, pfile
    tr1, tr2 = data
    fig = plt.figure(figsize=(24, 12))
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
    pfile = parse_pf(args.pfile)
    plot_data(process_data(get_data()))

if __name__ == '__main__':
    main()
