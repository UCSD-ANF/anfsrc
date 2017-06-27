from __main__ import *

class Origin():
    def __init__(self, db, orid):
        self.logging = getLogger('Origin')
        self.db = db
        self.orid = None
        self.depth = None
        self.strtime = None
        self.strdate = None
        self.time = None
        self.lat = None
        self.lon = None

        self.get_origin(orid)

    def get_origin(self, orid):
        steps = ['dbopen origin']
        steps.extend(['dbsubset orid==%s' % orid ])

        self.logging.debug( 'Database query for origin info:' )
        self.logging.debug( ', '.join(steps) )
        dbview = self.db.process(steps)

        if not dbview.record_count:
            # This failed. Lets see what we have in the db
            self.logging.error( 'No origins after subset for orid [%s]' % self.orid )

        #we should only have 1 here
        for temp in dbview.iter_record():

            (orid,time,lat,lon,depth) = \
                    temp.getv('orid','time','lat','lon','depth')
            self.logging.info( "orid=%s" % orid )

            self.logging.info( "time:%s (%s,%s)" % (time,lat,lon) )
            self.orid = orid
            self.depth = depth
            self.strtime = stock.strtime(time)
            self.strdate = stock.strdate(time)
            self.time = time
            self.lat  = lat
            self.lon  = lon


class Stations():
    def __init__(self, select, ref_sta, db, time, logging, event_data=None):
        self.db = db
        self.select = select
        self.ref_sta = ref_sta
        self.logging = logging
        self.stations = {}

        #try:
        #    self.db = datascope.dbopen( self.databasename, "r+" )
        #except Exception,e:
        #    self.logging.error('Problems opening database: %s %s' % (self.db,e) )


        try:
            self.sitetable = self.db.lookup(table='site')
        except Exception,e:
            self.logging.error('Problems opening site table: %s %s' % (self.db,e) )
       
        self.get_stations(time, event_data)

    def get_ref_sta(self, time):
        
        yearday = stock.epoch2str(time, '%Y%j')

        steps = ['dbopen site']
        steps.extend(['dbsubset ondate <= %s && (offdate >= %s || offdate == NULL)' % (yearday,yearday)])
        steps.extend(['dbsort sta'])

        if self.select:
            steps.extend( ['dbsubset sta =~ /%s/' % self.ref_sta ])

        self.logging.info( 'Database query for stations:' )
        self.logging.info( ', '.join(steps) )
    
        with datascope.freeing(self.db.process( steps )) as dbview:
            for temp in dbview.iter_record():
                self.logging.info( 'Extracting sites for origin from db' )
                (self.ref_lat,self.ref_lon) = temp.getv('lat','lon')
    
    def get_stations(self, time, event_data=None):
        self.get_ref_sta(time)

        yearday = stock.epoch2str(time, '%Y%j')


        steps = ['dbopen site']
        steps.extend(['dbsubset ondate <= %s && (offdate >= %s || offdate == NULL)' % (yearday,yearday)])
        steps.extend(['dbsort sta'])

        if self.select:
            steps.extend( ['dbsubset sta =~ /%s|%s/' % (self.ref_sta, self.select) ])

        self.logging.info( 'Database query for stations:' )
        self.logging.info( ', '.join(steps) )

        with datascope.freeing(self.db.process( steps )) as dbview:
            for temp in dbview.iter_record():
                self.logging.info( 'Extracting sites for origin from db' )
                (sta,lat,lon) = temp.getv('sta','lat','lon')
                
                if event_data:
                    seaz = "%0.1f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                                    (lat,lon,event_data.lat,event_data.lon) )
                    esaz = "%0.1f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                                    (event_data.lat,event_data.lon,lat,lon) )

                    ssaz = "%0.1f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                                    (self.ref_lat,self.ref_lon,lat,lon) )
                    
                    delta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
                                                    (event_data.lat,event_data.lon,lat,lon) )
                    ssdelta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
                                                    (self.ref_lat,self.ref_lon,lat,lon) )
                    ssdistance = temp.ex_eval('deg2km(%s)' % ssdelta)

                    realdistance = temp.ex_eval('deg2km(%s)' % delta)
                    # round to nearest distance step. from velocity model

                    pdelay = int(temp.ex_eval('pphasetime(%s,%s)' % (delta,event_data.depth)))
                    if pdelay > 0:
                        pdelay -= 1
                    else:
                        pdelay = 0

                    ptime = time + pdelay
                else:
                    seaz = None
                    esaz = None
                    delta = None
                    realdistance = None
                    pdelay = None
                    ptime = None

                self.stations[sta] = {
                            'lat': lat,
                            'lon': lon,
                            'delta': delta,
                            'realdistance': realdistance,
                            'pdelay': pdelay,
                            'ptime': ptime,
                            'seaz': seaz,
                            'esaz': esaz,
                            'ssaz': ssaz,
                            'ssdistance': round(ssdistance, 2)
                            }
    
    def station_list(self):
        stations = []
        for sta in self.stations:
            stations.append(sta)
        return stations



class Records():
    def __init__(self):
        self.rotated = None
        self.original = None
        self.azimuth = None
        self.xcorr = None
   
    def set_data(self, original, rotated, azimuth, xcorr):
        self.set_rotated(rotated)
        self.set_original(original)
        self.set_azimuth(azimuth)
        self.set_xcorr(xcorr)

    def set_rotated(self, data):
        self.rotated = data
            
    def set_original(self, data):
        self.original = data

    def set_azimuth(self, azimuth):
        self.azimuth = azimuth

    def set_xcorr(self, xcorr):
        self.xcorr = xcorr

 
class Plot():
    def __init__(self, width, height, result, reference, ref_sta, sta, start, end, result_dir, debug_plot):
        self.width = width
        self.height = height
        fig = plt.figure(figsize = (width, height))
        axs = [fig.add_subplot(3, 3, j) for j in range(1,10)]
        
        plt.tight_layout()
        fig.subplots_adjust(top=0.9, bottom=0.05)
        fig.suptitle("Station %s relative to %s corrected for event-station azimuth" % (sta, ref_sta), fontsize=18)
    
        self.plot_data(axs, result, reference, ref_sta, sta, start, end)
        
        if debug_plot:
            plt.show()            
        else: 
            filename = "xcorr_rot%s_ref%s_%s.png" % (sta, ref_sta, epoch2str(start, "%Y%j_%H_%M_%S.%s"))
            path = "/".join([result_dir, filename])
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            fig.savefig(path)
    
    def plot_data(self, axs, result, reference, ref_sta, sta, start, end):
        for i,chan in enumerate(result):
            if i==0: ind = 0
            if i==1: ind = 1
            if i==2: ind = 2

            #axs[ind].plot(reference[chan], 'b')
            #axs[ind].plot(result[chan].original, 'r')
            axs[ind].plot(reference[chan], 'b')
            axs[ind].plot(result[chan].original, 'r')
            #axs[ind+9].plot(result[chan].rotated, 'r')
            axs[ind+3].plot(reference[chan], 'b')
            axs[ind+3].plot(result[chan].rotated, 'r')
           
            axs[ind+6].xaxis.set_visible(False)
            axs[ind+6].yaxis.set_visible(False)
            axs[ind+6].patch.set_alpha(0.0)
            axs[ind+6].axis('off')

            # add command line argument to plot 
            text = "Angle: %s\n" % result[chan].azimuth
            text += "Xcorr: %s\n" % round(result[chan].xcorr, 3) 

            axs[ind+6].annotate(unicode(text, "utf-8"), (0.5,0.7), xycoords="axes fraction", va="center", ha="center", fontsize=8, bbox=dict(edgecolor='white', boxstyle='round, pad=0.5', fc="w"), size=16)

            # y-axis labels
            if i == 0:
                #axs[ind].set_ylabel("%s" % ref_sta, fontsize=12)
                #axs[ind+3].set_ylabel("%s" % sta, fontsize=12)
                axs[ind].set_ylabel("both", fontsize=12)
                #axs[ind+9].set_ylabel("rot %s" % sta, fontsize=12)
                axs[ind+3].set_ylabel("rot both", fontsize=12)
            
            axs[ind].set_yticks([])
            axs[ind+3].set_yticks([])
            #axs[ind+6].set_yticks([])
            #axs[ind+9].set_yticks([])
            #axs[ind+12].set_yticks([])
               
            axs[ind].set_xticks([])
            axs[ind+3].set_xticks([])
            #axs[ind+6].set_xticks([])
            #axs[ind+9].set_xticks([])
            #axs[ind+12].set_xticks([])
            
            # xticks and xtick labels 
            tw = end - start
            dt = tw/len(reference[chan])
            xticks = arange(0, len(reference[chan]), len(reference[chan]) / 4)
            xtick_labels = [epoch2str(t, "%Y%j %H:%M:%S.%s") for t in\
                    [start + x * dt for x in xticks]]
            xtick_labels = xticks*dt - 2
            axs[ind+3].set_xticks(xticks)
            axs[ind+3].set_xticklabels(xtick_labels)
            axs[ind+3].set_xlabel("time since predicated first-arrival (s)")
            
            axs[ind].set_title("Channel %s" % chan)
             

def free_tr(tr):
    tr.table = datascope.dbALL
    tr.trdestroy()


def tr2vec(tr, record):
    tr.record = record
    data = tr.trdata()
    return data

def cross_correlation(data1, data2):
        time_shift, xcorr_value, cross_corr= xcorr(np.array(data1), np.array(data2), shift_len=10, full_xcorr=True)
        return float(time_shift), float(xcorr_value), cross_corr


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

def get_range(start, stop, step):
    x = []
    i=0
    while start + i * step < stop:
        x.append(start +  i * step)
        i += 1
    return x

def open_verify_pf(pf,mttime=False):
    '''
    Verify that we can get the file and check
    the value of PF_MTTIME if needed.
    Returns pf_object
    '''

    logging.debug( 'Look for parameter file: %s' % pf )

    if mttime:
        logging.debug( 'Verify that %s is newer than %s' % (pf,mttime) )

        PF_STATUS = stock.pfrequire(pf, mttime)
        if PF_STATUS == stock.PF_MTIME_NOT_FOUND:
            logging.warning( 'Problems looking for %s. PF_MTTIME_NOT_FOUND.' % pf )
            logging.error( 'No MTTIME in PF file. Need a new version of the %s file!!!' % pf )
        elif PF_STATUS == stock.PF_MTIME_OLD:
            logging.warning( 'Problems looking for %s. PF_MTTIME_OLD.' % pf )
            logging.error( 'Need a new version of the %s file!!!' % pf )
        elif PF_STATUS == stock.PF_SYNTAX_ERROR:
            logging.warning( 'Problems looking for %s. PF_SYNTAX_ERROR.' % pf )
            logging.error( 'Need a working version of the %s file!!!' % pf )
        elif PF_STATUS == stock.PF_NOT_FOUND:
            logging.warning( 'Problems looking for %s. PF_NOT_FOUND.' % pf )
            logging.error( 'No file  %s found!!!' % pf )

        logging.debug( '%s => PF_MTIME_OK' % pf )

    try:
        return stock.pfread( pf )
    except Exception,e:
        logging.error( 'Problem looking for %s => %s' % ( pf, e ) )

def safe_pf_get(pf,field,defaultval=False):
    '''
    Safe method to extract values from parameter file
    with a default value option.
    '''
    value = defaultval
    if pf.has_key(field):
        try:
            value = pf.get(field,defaultval)
        except Exception,e:
            logging.warning('Problems safe_pf_get(%s,%s)' % (field,e))
            pass

    logging.debug( "pf.get(%s,%s) => %s" % (field,defaultval,value) )

    return value

# split regex info list
def get_regex(site):
    regex = site.split()
    return regex


def save_results(result_dir, ref_sta, ref_esaz, sta, ssaz, distance, esaz, azimuth1, azimuth2):
    filename = "rotation_comparison.csv"
    path = "/".join([result_dir, filename])
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    new_row = [ref_sta, sta, ssaz, distance, ref_esaz, esaz, azimuth1, azimuth2]
    if not(os.path.isfile(path)):
        logging.info("No rotation_comparison table -- GENERATING TABLE")
        f = open(path, 'wt')
        writer = csv.writer(f)
        writer.writerow(["ref", "sta", "ssaz", "ssdist", "ref esaz", "esaz", "azimuth T", "azimuth R"])
        writer.writerow(new_row)
        f.close()
    else:
        with open(path, mode='r') as ifile:
            existingRows = [row for row in csv.reader(ifile)]
        
        with open(path, mode='a') as ofile:
            if new_row not in existingRows:
                csv.writer(ofile).writerow(new_row)
                


#class Parameters():
#    def __init__(self, options, logging):
#        self.logging = logging
#        # verify adequate parameter file
#        self.pf = open_verify_pf(options.pf)
#
#        # parse parameter file 
#        try:
#            self._parse_pf(options)
#        except Exception:
#            self.logging.error('ERROR: problem during parsing of pf file (%s)' % options.pf)
#
#    def _parse_pf(self, options):
#        self.origin = options.origin
#        self.image_dir = safe_pf_get(self.pf, "image_dir")
#
#        if options.ref_sta not in options.select:
#            self.select = "|".join([options.select, options.ref_sta])
#        else: self.select = options.select
#
#        if options.tw: self.tw = options.tw
#        else: self.tw = safe_pf_get(self.pf, 'time_window')
#        self.tw = float(self.tw)
# 
#        if options.filter: self.filter = options.filter
#        else: self.filter = safe_pf_get(self.pf, 'filter')
#       
#        if options.chan: self.chan = options.chan
#        else: self.chan = safe_pf_get(self.pf, 'chan')
#
#class Site:
#    def __init__(self, regex, databasename=None):
#        self.databasename = databasename
#        self.sites = []
#
#        # read all values from the site table
#        with datascope.freeing(datascope.dbopen(self.databasename, 'r')) as db:
#            try:
#                dbtable = db.lookup(table = 'site')
#            except Exception,e:
#                logging.error('Problems pointing to site table: %s %s %s' % (database,Exception, e))
#            try: 
#                dbsubset = dbtable.subset('sta=~/%s/' % regex)
#            except Exception, e:
#                logging.error('Stations %s not present in site table' % regex)  
#
#            for dbrecord in dbsubset.iter_record():
#                sta = dbrecord.getv('sta')[0]
#                self.sites.append(sta)


#def dbminmax (db, tmin=-1.e30, tmax=1.e30, gain=1.0):
#    start = db.record
#    end = db.record + 1
#    if db.record < 0:
#        start = 0
#        end = db.query ( "dbRECORD_COUNT" )
#
#    amin = None
#    amax = None
#    for db.record in range(start, end):
#        (nsamp, samprate, tstart) = db.getv ( 'nsamp', 'samprate', 'time' )
#        dt = 1.0 / samprate
#        data = db.trdata ( )
#        for i in range(0, nsamp):
#            time = tstart + i * dt
#            if time < tmin:
#                continue
#            if time > tmax:
#                break
#            if data[i] > 1.e20:
#                continue
#            if amin == None:
#                amin = data[i]
#            elif amin > data[i]:
#                amin = data[i]
#            if amax == None:
#                amax = data[i]
#            elif amax < data[i]:
#                amax = data[i]
#        if amin != None:
#            mid = 0.5*(amin+amax)
#            amin = mid - (mid-amin)*gain
#            amax = mid + (amax-mid)*gain
#
#    return (amin, amax, samprate)
#
#def trscale (vp, vpf, data, dataf, tracef, t0, t1, gain):
#    (amin, amax, sr) = dbminmax ( data, t0, t1, gain )
#    vp.configure ( xleft = t0, xright = t1, ybottom = amin, ytop = amax )
#    (amin, amax, sr) = dbminmax ( dataf, t0, t1, 1.1 )
#    (ret, xmin, xmax, amin, amax) = buvector_maxmin ( tracef, -1 )
#    mid = 0.5*(amin+amax)
#    amin = mid - (mid-amin)*gain
#    amax = mid + (amax-mid)*gain
#    vpf.configure ( xleft = t0, xright = t1, ybottom = amin, ytop = amax )
#    vp.update()
#    vpf.update()

#class Graphics():
#    def __init__(self, width, height, results, ref_sta, ts, te):
#        #ref_orig = results[ref_sta][chan].original
#        ge = GraphicsEngine()
#
#        self.width = width 
#        self.height = height
#
#        mw = MainWindow(ge)
#        mw.geometry (2*self.width, 3*self.height)
#    
#        self.ts = ts
#        self.te = te
#       
#        layout = GridLayout (mw.getframe())
#
#        #menubar = Menubar (mw)
#        #file_menu = menubar.addmenu ("&File")
#        #quit_item = file_menu.additem ("&Quit")
#        #quit_item.registercallback ( lambda self: ge.quit() )
#        #file_menu.addseparator ()
# 
#        frame_ref_orig = self.set_frame(mw, layout, [0, 0, 1, 1])
#        frame_sta_orig = self.set_frame(mw, layout, [1, 0, 1, 1])
#        frame_both_orig = self.set_frame(mw, layout, [2, 0, 1, 1])
#
#        frame_ref_rot = self.set_frame(mw, layout, [0, 1, 1, 1])
#        frame_sta_rot = self.set_frame(mw, layout, [1, 1, 1, 1])
#        frame_both_rot = self.set_frame(mw, layout, [2, 1, 1, 1])
#
#        for sta in results:
#            for i, chan in enumerate(results[sta]):
#                record = i
#                print chan
#                ref_orig = results[ref_sta][chan].original
#                sta_orig = results[sta][chan].original
#                sta_rot = results[sta][chan].rotated
#            
#                trace_ref_orig = tr2vector(ref_orig, record)
#                trace_sta_orig = tr2vector(sta_orig, record)
#                trace_sta_rot = tr2vector(sta_rot, record)
#
#                vp_ref_orig = self.set_viewport(frame_ref_orig, ref_sta, chan, trace_ref_orig)
#                vp_sta_orig = self.set_viewport(frame_sta_orig, sta, chan, trace_sta_orig)
#                vp_both_orig = self.set_viewport(frame_both_orig, "both", chan, trace_ref_orig, trace_sta_orig)
#                
#                vp_ref_rot = self.set_viewport(frame_ref_rot, ref_sta, chan, trace_ref_orig)
#                vp_sta_rot = self.set_viewport(frame_sta_rot, sta, chan, trace_sta_rot)
#                vp_both_rot = self.set_viewport(frame_both_rot, "both", chan, trace_ref_orig, trace_sta_rot)
#
#                trscale (vp_ref_orig, vp_sta_orig, ref_orig, sta_orig, trace_sta_orig, ts, te, 1.1)
#                trscale (vp_ref_orig, vp_both_orig, ref_orig, sta_orig, trace_sta_orig, ts, te, 1.1)
#                
#                trscale (vp_ref_rot, vp_sta_rot, ref_orig, sta_rot, trace_sta_rot, ts, te, 1.1)
#                trscale (vp_ref_rot, vp_both_rot, ref_orig, sta_rot, trace_sta_rot, ts, te, 1.1)
#
#                #vp_ref_orig.update()
#
#                mw.show()
#                ge.qtmainloop()
#                ge.pymainloop()
#                #vp_ref_orig.delete()
#                #vp_sta_orig.delete()
#                #vp_both_orig.delete()
#                #vp_ref_rot.delete()
#                #vp_sta_rot.delete()
#                #vp_both_rot.delete()        
#                ge.quit()     
#        #self.ge.qtmainloop()
#        #self.ge.pymainloop()
#    
#    def set_frame(self, mw, layout, position):
#        frame = Frame(mw.getframe())
#        frame.geometry(self.width, self.height)
#        layout.addwidget(frame, position[0], position[1], position[2], position[3])
#        return frame
#
#        
#        #frame_ref_orig = Frame ( mw.getframe() )
#        #frame_ref_orig.geometry ( self.width, self.height )
#        #layout.addwidget ( frame_ref_orig, 0, 0, 1, 1 )
#
#        #frame_sta_orig = Frame ( mw.getframe() )
#        #frame_sta_orig.geometry ( self.width, self.height)
#        #layout.addwidget ( frame_sta_orig, 1, 0, 1, 1 )
#
#        #frame_both_orig = Frame ( mw.getframe() )
#        #frame_both_orig.geometry ( self.width, self.height)
#        #layout.addwidget ( frame_both_orig, 2, 0, 1, 1 )
#
#        #frame_ref_rot = Frame ( mw.getframe() )
#        #frame_ref_rot.geometry ( self.width, self.height )
#        #layout.addwidget ( frame_ref_rot, 0, 1, 1, 1 )
#
#        #frame_sta_rot = Frame ( mw.getframe() )
#        #frame_sta_rot.geometry ( self.width, self.height)
#        #layout.addwidget ( frame_sta_rot, 1, 1, 1, 1 )
#
#        #frame_both_rot = Frame ( mw.getframe() )
#        #frame_both_rot.geometry ( self.width, self.height)
#        #layout.addwidget ( frame_both_rot, 2, 1, 1, 1 )
#
#    def set_viewport(self, frame, sta, chan, trace=None, trace2=None):
#        vp = Viewport ( frame, \
#                default_event_interaction = 'no', \
#                mleft = 80, \
#                mright = 5, \
#                mbottom = 5, \
#                mtop = 5, \
#                height = 0, \
#                width = 0, \
#                fill = "#000080", \
#                fill_frame = "#f0f0ff", \
#                xmode = 'time', \
#                xleft = self.ts, \
#                xright = self.te )
#
#        Axes ( vp, \
#                ylabel = sta + ' ' + chan , \
#                xformat = 'time', \
#                yformat = 'auto', \
#                linewidth_tics = -1, \
#                linewidth_tics_small = -1, \
#                color_time_axis = "#4040ff", \
#                linewidth_grids = 2, \
#                color_grids = "#4040ff", \
#                linewidth_grids_small = -1, \
#                linewidth_grids_x = -1 )
#
#        
#        if trace:
#            Polyline ( vp, \
#                    vector = trace, \
#                    color_outline = 'yellow' )
#        
#        if trace2:
#            Polyline ( vp, \
#                    vector = trace2, \
#                    color_outline = 'red' )
#        return vp
#
#        #layout.show()
#

#class VpCallback (object):
#    def __init__ (self, a, results):
#        self.results = results
#        
#        self.stations=[]
#        for sta in results:
#            self.stations.append(sta)
#
#    def callback (self, pfstring, a):
#        argsd = PfSubs.pfstring2py (pfstring)
#        if argsd['bqevent']['type'] == 'mousepress':
#            ref_orig = results[ref_sta][chan].original
#            sta_orig = results[sta][chan].original
#            sta_rot = results[sta][chan].rotated
#        
#            trace_ref_orig = tr2vector(ref_orig, record)
#            trace_sta_orig = tr2vector(sta_orig, record)
#            trace_sta_rot = tr2vector(sta_rot, record)
#
#            vp_ref_orig = self.set_viewport(frame_ref_orig, ref_sta, chan, trace_ref_orig)
#            vp_sta_orig = self.set_viewport(frame_sta_orig, sta, chan, trace_sta_orig)
#            vp_both_orig = self.set_viewport(frame_both_orig, "both", chan, trace_ref_orig, trace_sta_orig)
#            
#            vp_ref_rot = self.set_viewport(frame_ref_rot, ref_sta, chan, trace_ref_orig)
#            vp_sta_rot = self.set_viewport(frame_sta_rot, sta, chan, trace_sta_rot)
#            vp_both_rot = self.set_viewport(frame_both_rot, "both", chan, trace_ref_orig, trace_sta_rot)
#
#            trscale (vp_ref_orig, vp_sta_orig, ref_orig, sta_orig, trace_sta_orig, ts, te, 1.1)
#            trscale (vp_ref_orig, vp_both_orig, ref_orig, sta_orig, trace_sta_orig, ts, te, 1.1)
#            
#            trscale (vp_ref_rot, vp_sta_rot, ref_orig, sta_rot, trace_sta_rot, ts, te, 1.1)
#            trscale (vp_ref_rot, vp_both_rot, ref_orig, sta_rot, trace_sta_rot, ts, te, 1.1)

#def tr2vector (tr, record):
#    tr.record = record
#    data = tr.trdata ()
#    (nsamp, time, samprate) = tr.getv ( 'nsamp', 'time', 'samprate' )
#    for i in range (0, nsamp):
#        if data[i] > 1.e20:
#            continue
#        break
#    nsamp -= i
#    time += i / samprate
#    vector = buvector_create_tsamp ( nsamp, time, samprate, data[i:] )
#    return vector
