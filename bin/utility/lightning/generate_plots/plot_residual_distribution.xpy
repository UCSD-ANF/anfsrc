def main():
    """Main function."""
    from antelope.datascope import dbopen
    args = parse_args()
    db = dbopen(args.input_database[0], 'r')
    db_arr = db.lookup(table='arrival')
    resids = []
    for db_arr.record in range(db_arr.nrecs()):
        resids.append(db_arr.getv('auth')[0])
    resids = [eval(r) for r in filter(lambda r: r != '-', resids)]
    plot_residuals_distribution(resids, args)
    db.close()

def parse_args():
    """Parse command line options."""
    import argparse
    parser = argparse.ArgumentParser(description="Plot the distribution of "
        "time residuals for input database.")
    parser.add_argument('input_database', nargs=1, type=str, help="Input "
        "database.")
    parser.add_argument('-i', '--ignore_unmoved', action='store_true',
        help="Ignore arrivals with 0.0 residual.")
    parser.add_argument('-bw', '--bin_width', nargs=1, type=float,
        help="Bin width [seconds].")
    parser.add_argument('-s', '--save_as', nargs=1, type=str,
        help="Save plot as.")
    parser.add_argument('-t', '--title', nargs=1, type=str, help="Title")
    parser.add_argument('-tfs', '--title_fontsize', nargs=1, type=int,
        help="Title font size.")
    parser.add_argument('-x', '--x_label', nargs=1, type=str, 
        help="X-axis label.")
    parser.add_argument('-xfs', '--xlabel_fontsize', nargs=1, type=int,
        help="X-label font size.")
    parser.add_argument('-y', '--y_label', nargs=1, type=str,
        help="Y-axis label.")
    parser.add_argument('-yfs', '--ylabel_fontsize', nargs=1, type=int,
        help="Y-axis label font size.")
    args = parser.parse_args()
    if not os.path.isfile(args.input_database[0]):
        sys.exit("Descriptor file %s does not exist."
            % args.input_database[0])
    return args

def plot_residuals_distribution(resids, args):
    import matplotlib.pyplot as plt
    from numpy import arange, digitize, zeros
    if args.bin_width: bin_width = args.bin_width[0]
    else: bin_width = 0.25
    if args.ignore_unmoved: resids = filter(lambda r: r != 0.0, resids)
    m = max([abs(r) for r in resids])
    m = m - (m % bin_width) + bin_width*1.5
    bin_edges = arange(-m, m+bin_width, bin_width)
    inds = digitize(resids, bin_edges)
    counts = [len(filter(lambda ind: i+1 == ind, inds)) for i in 
        range(len(bin_edges))]
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(bin_edges, counts, bin_width)
    if args.title:
        if args.title_fontsize: fs = args.title_fontsize[0]
        else: fs = 16
        fig.suptitle(args.title[0], fontsize=fs)
    if args.x_label:
        if args.xlabel_fontsize: fs = args.xlabel_fontsize[0]
        else: fs = 12
        ax.set_xlabel(args.x_label[0], fontsize=fs)
    if args.y_label:
        if args.ylabel_fontsize: fs = args.ylabel_fontsize[0]
        else: fs = 12
        ax.set_ylabel(args.y_label[0], fontsize=fs)
    if args.save_as: plt.savefig("%s.png" % args.save_as[0], format='png')
    plt.show()

if __name__ == '__main__': sys.exit(main())
else: print "Not a module to import!"
