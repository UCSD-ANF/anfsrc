"""
A simple script to calculate and update the deltim of observed arrivals 
relative to predicted arrivas, in two separate arrival tables.
"""

def parse_args():
    """Parse and return command line arguments."""

    import argparse
    parser = argparse.ArgumentParser(description="Calculate residual of "\
        "observed arrivals")
    parser.add_argument('-v', '--verbose', action='store_true', \
        help="Verbose mode.")
    parser.add_argument('-n', '--nullrun', action='store_true', \
        help="Null run.")
    parser.add_argument('db_predicted', type=str, nargs=1, help="db with "
        "arrival table containing predicted arrivals.")
    parser.add_argument('db_observed', type=str, nargs=1, help="db with "
        "arrival table containing observed arrival.")
    return parser.parse_args()

def main():
    """
    Main function.

    Iterate through arrival table containing predicted arrivals, look
    for corresponding arrival in arrival table containing observed 
    arrivals, calculate delta and store value in 'auth' field of arrival
    table containing observed arrivals. Removed arrivals are given a NULL
    ("-") delta value.
    """

    try:
        from antelope.datascope import dbopen
        from antelope.stock import epoch2str
    except Exception as e:
        sys.exit("Problem importing Antelope datascope library. (%s)" % e)
    args = parse_args()
    verbose = args.verbose
    nullrun = args.nullrun
    if not os.path.isfile(args.db_predicted[0]):
        sys.exit("Descriptor file %s does not exist" % args.db_predicted[0])
    if not os.path.isfile(args.db_observed[0]):
        sys.exit("Descriptor file %s does not exist" % args.db_observed[0])
    db_pred = dbopen(args.db_predicted[0], 'r+')
    db_obs = dbopen(args.db_observed[0], 'r')
    pred_origin = db_pred.lookup(table='origin')
    pred_arrival = db_pred.lookup(table='arrival')
    obs_arrival = db_obs.lookup(table='arrival')
    for pred_arrival.record in range(pred_arrival.nrecs()):
        arid = pred_arrival.getv('arid')[0]
        if verbose: print "Processing arid %d" % arid
        obs_arrival.record = obs_arrival.find('arid == %d' % arid, -1)
        if obs_arrival.record == -2 or obs_arrival.getv('iphase')[0] == 'del':
            if verbose:
                print "\tarid %d not found or marked for deletion in "\
                    "%s.arrival" % (arid, args.db_observed[0])
                if nullrun:
                    print "\tNull run, not updating deltim."
                else:
                    print "\tUpdating deltim with NULL value: '-'"
                    pred_arrival.putv('auth', '-')
            elif not nullrun:
                pred_arrival.putv('auth', '-')
        else:
            obs_time = obs_arrival.getv('time')[0]
            pred_time = pred_arrival.getv('time')[0]
            deltim = obs_time - pred_time
            if verbose:
                print "\tPredicted arrival time: %s" % epoch2str(pred_time,
                    "%Y %D %H:%M:%S.%s")
                print "\tObserved arrival time: %s" % epoch2str(obs_time,
                    "%Y %D %H:%M:%S.%s")
                print "\tdeltim: %f" % deltim
                if nullrun:
                    print "\tNull run, not updating deltim."
                else:
                    print "\tUpdating deltim"
                    pred_arrival.putv('auth', str('%.4f' % deltim))
            elif not nullrun:
                pred_arrival.putv('auth', str('%.4f' % deltim))
    db_pred.close()
    db_obs.close()

if __name__ == '__main__': sys.exit(main())
else: print 'Not a module to import!'
