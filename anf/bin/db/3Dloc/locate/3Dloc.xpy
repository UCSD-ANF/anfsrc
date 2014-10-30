def _configure_logging(logfile='3Dloc.log', level=None):
    import logging
    if level == None:
        level = logging.INFO
    elif level.upper() == 'DEBUG':
        level = logging.DEBUG
    else:
        level = logging.INFO
    for name in (__name__,
                 'anf.loctools3D.core',
                 'anf.loctools3D.ant',
                 'anf.loctools3D.scec'):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        if level == logging.DEBUG:
            formatter = logging.Formatter(fmt='%(asctime)s::%(levelname)s::'\
                    '%(name)s::%(funcName)s():: %(message)s',
                                          datefmt='%Y%j %H:%M:%S')
        else:
            formatter = logging.Formatter(fmt='%(asctime)s::%(levelname)s::'\
                    ' %(message)s',
                                          datefmt='%Y%j %H:%M:%S')
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

def _main():
    """
    Standard main() function. Execution control begins here.
    """
    from logging import getLogger
    from anf.loctools3D.ant import pfile_2_cfg,\
                                   create_event_list,\
                                   write_origin
    from anf.loctools3D.core import Locator,\
                                    parse_cfg,\
                                    verify_config_file

    from antelope.datascope import closing, dbopen
    args = _parse_command_line()
    if args.verbose:
        logging_level = 'DEBUG'
    else:
        logging_level = None
    _configure_logging(level=logging_level)
    logger = getLogger(__name__)
    pfile_2_cfg(args.pfile, '3Dloc')
    cfg_dict = verify_config_file(parse_cfg('3Dloc.cfg'))
    locator = Locator(cfg_dict)
    with closing(dbopen(args.db, 'r+')) as db:
        tbl_event = db.schema_tables['event']
        if args.subset:
            view = tbl_event.join('origin')
            tmp = view.subset(args.subset)
            view.free()
            view = tmp
            tbl_event.free()
            tbl_event = view.separate('event')
        for record in tbl_event.iter_record():
            evid = record.getv('evid')[0]
            tmp = tbl_event.subset('evid == %d' % evid)
#            view.free()
            view = tmp
            event_list = create_event_list(view)
            for event in event_list:
                origin = event.preferred_origin
                logger.info('Relocating evid %d'
                        % event.evid)
                origin = locator.locate_eq(origin)
                if origin == None:
                    logger.info('Could not relocate orid: %d' \
                            % event.preferred_origin.orid)
                    continue
                origin.update_predarr_times(cfg_dict)
                write_origin(origin, db)
    return 0

def _parse_command_line():
    """
    Parse command line arguments. Return dictionary-like object
    containing results.
    """
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('db', type=str, help='input/output database')
    parser.add_argument('-s', '--subset', type=str, help='subset expression')
    parser.add_argument('-p', '--pfile', type=str, help='parameter file')
    parser.add_argument('-l', '--logfile', type=str, help='log file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase verbosity')
    args = parser.parse_args()
    if args.logfile:
        if os.path.splitext(args.logfile)[1] != '.log':
            logfile = '%s.log' % args.logfile
    return args

if __name__ == '__main__': sys.exit(_main())
else: raise ImportError
