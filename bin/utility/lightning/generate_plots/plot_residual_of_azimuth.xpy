def main():
    """Main function."""
    from antelope.datascope import dbopen
    args = parse_args()
    db = dbopen(args.input_database[0], 'r')
    db_arr = db.lookup(table='arrival')
    azm_resid = []
    for db_arr.record in range(db_arr.nrecs()):
        azm_resid.append(db_arr.getv('azimuth', 'auth'))
    azm_resid = [(r[0], eval(r[1])) for r in \
        filter(lambda r: r[1] != '-', azm_resid)]
    plot_residual_of_azimuth(azm_resid, args)
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

def plot_residual_of_azimuth(azm_resid, args):
    import matplotlib.pyplot as plt
    if args.ignore_unmoved: azm_resid = filter(lambda r: r[1] != 0.0,
        azm_resid)
    azm = [r[0] for r in azm_resid]
    resids = [r[1] for r in azm_resid]
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(azm, resids, 'b.')
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
