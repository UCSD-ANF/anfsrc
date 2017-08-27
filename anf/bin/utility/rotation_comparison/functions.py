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

class Site():
    
    def __init__(self, db, logging):
        self.db = db
        self.logging = logging
        self.stations = {}

        steps = ['dbopen site']
        steps.extend(['dbjoin sitechan'])
        
        self.logging.info( 'Database query for stations:' )
        self.logging.info( ', '.join(steps) )
    

        self.table = self.db.process(steps)
 
    def get_stations(self, regex, time, reference=False, event_data=None):
                
        yearday = stock.epoch2str(time, '%Y%j')

        steps = ['dbsubset ondate <= %s && (offdate >= %s || offdate == NULL)' % (yearday,yearday)]
        steps.extend(['dbsort sta'])

        steps.extend( ['dbsubset %s' % regex ])

        self.logging.info( 'Database query for stations:' )
        self.logging.info( ', '.join(steps) )
    
        with datascope.freeing(self.table.process( steps )) as dbview:
            self.logging.info( 'Extracting sites for origin from db' )
            

            strings = []
            for temp in dbview.iter_record():
                (sta, lat, lon, chan) = temp.getv('sta','lat','lon','chan')
                
                if len(chan)>3:
                    chan_code = chan[:2] + "._."
                else:
                    chan_code = chan[:2]
                
                string = sta + chan_code

                if string not in strings:
                    strings.append(string)
                    
                    try:
                        self.stations[sta].append_chan(chan_code)
                    except Exception,e:
                        self.stations[sta] = Records(sta, lat, lon)                
                        self.stations[sta].append_chan(chan_code)
                        if (reference and sta!=reference):
                            ssaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                                            (self.stations[reference].lat, self.stations[reference].lon, lat, lon) )
                            ssdelta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
                                                            (self.stations[reference].lat, self.stations[reference].lon, lat, lon) )
                            ssdistance = round(temp.ex_eval('deg2km(%s)' % ssdelta), 2)
                            
                            self.stations[sta].set_ss(ssaz, ssdelta, ssdistance)

                        if event_data:
                            seaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                                            (lat,lon,event_data.lat,event_data.lon) )
                            esaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                                            (event_data.lat,event_data.lon,lat,lon) )
                            delta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
                                                            (event_data.lat,event_data.lon,lat,lon) )
                            realdistance = temp.ex_eval('deg2km(%s)' % delta)
                            # round to nearest distance step. from velocity model

                            pdelay = int(temp.ex_eval('pphasetime(%s,%s)' % (delta,event_data.depth)))
                            if pdelay > 0:
                                pdelay -= 1
                            else:
                                pdelay = 0

                            ptime = time + pdelay

                            self.stations[sta].set_es(seaz, esaz, delta, realdistance, pdelay, ptime)
                    #else:
                        #self.stations[sta].append_chan(chan_code)
 
                                                
        return self.stations

class Records():
    """
    Class for tracking info from a single sta
    """

    def __init__(self, sta, lat, lon):
        self.sta = sta
        self.chans = []
        self.lat = lat 
        self.lon = lon
        self.delta = False
        self.realdistance = False
        self.esaz = False
        self.ssaz = False
        self.ssdistance = False
        self.ssdelta = False
        self.pdelay = False
        self.ptime = False
    
    def append_chan(self, chan):
        self.chans.append(chan)
       
    def set_ss(self, az, delta, distance):
        self.ssaz = float(az)
        self.ssdistance = float(distance) 
        self.ssdelta = float(delta)
        
    def set_es(self, seaz, esaz, delta, realdistance, pdelay, ptime):
        self.seaz = float(seaz)
        self.esaz = float(esaz)
        self.delta = float(delta)
        self.realdistance = float(realdistance)
        self.pdelay = float(pdelay)
        self.ptime = float(ptime)






class Results():
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
    def __init__(self, width, height, result, reference, ref_sta, ref_chan, sta, start, end, result_dir, debug_plot, orid=None):
        total = len(result)    
        self.width = width
        self.height = height * total
        fig = plt.figure(figsize = (width, height))
        axs = [fig.add_subplot(3*total, 3, j) for j in range(1, (3*3*total)+1)]
         
 
        plt.tight_layout()
        fig.subplots_adjust(top=0.9, bottom=0.05)
        #fig.suptitle("Station %s compared to %s" % (ref_sta, sta), fontsize=16)
    
        self.plot_data(axs, result, reference, ref_sta, ref_chan, sta, start, end)
        
        if debug_plot:
            plt.show()            
        else:
            if not orid: 
                filename = "%s_%s_%s.png" % (ref_sta, sta, epoch2str(start, "%Y%j_%H_%M_%S.%s"))
            else:
                filename = "%s_%s_%s.png" % (ref_sta, sta, orid)
            
            path = "/".join([result_dir, filename])
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            fig.savefig(path, bbox_inches='tight', pad_inches=0.5, dpi=100)
    
    def plot_data(self, axs, result, reference, ref_sta, ref_chan, sta, start, end):
       
        k = 0 
        for code in result:
            for i,chan in enumerate(result[code]):
                data = result[code][chan]

                if i==0: ind = 0 + k 
                if i==1: ind = 1 + k
                if i==2: ind = 2 + k
                #axs[ind].plot(reference[chan], 'b')
                #axs[ind].plot(result[chan].original, 'r')
                axs[ind].plot(reference[chan], 'b', label='%s_%s%s' % (ref_sta, ref_chan, chan))
                axs[ind].plot(data.original, 'r', label='%s_%s%s' % (sta, code, chan))
                #axs[ind+9].plot(result[chan].rotated, 'r')
                axs[ind+3].plot(reference[chan], 'b')
                axs[ind+3].plot(data.rotated, 'r')
             
                axs[ind].legend(loc='upper left', prop={'size': 6})   
                
                axs[ind+6].xaxis.set_visible(False)
                axs[ind+6].yaxis.set_visible(False)
                axs[ind+6].patch.set_alpha(0.0)
                axs[ind+6].axis('off')

                # add command line argument to plot 
                text = "Angle: %s\n" % data.azimuth
                text += "Xcorr: %s\n" % round(data.xcorr, 3) 

                axs[ind+6].annotate(unicode(text, "utf-8"), (0.5,0.7), xycoords="axes fraction", va="top", ha="center", fontsize=6, bbox=dict(edgecolor='white', boxstyle='round, pad=0.5', fc="w"), size=12)

                # y-axis labels
                if i == 0:
                    #axs[ind].set_ylabel("%s" % ref_sta, fontsize=12)
                    #axs[ind+3].set_ylabel("%s" % sta, fontsize=12)
                    axs[ind].set_ylabel("original", fontsize=12)
                    #axs[ind+9].set_ylabel("rot %s" % sta, fontsize=12)
                    axs[ind+3].set_ylabel("rotated", fontsize=12)
                
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
                
                if i==1:
                    axs[ind].set_title("%s_%s compared to %s_%s" % (ref_sta, ref_chan, sta, code), fontsize=12)
                #axs[ind].set_title("Channel %s" % chan)
            k+=9 

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


def save_results(ref_sta, ref_chan, sta, chan, result_dir, ref_esaz, ssaz, distance, esaz, azimuth1, azimuth2):
    filename = "rotation_comparison.csv"
    path = "/".join([result_dir, filename])
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    new_row = [ref_sta, ref_chan, sta, chan, ssaz, distance, ref_esaz, esaz, azimuth1, azimuth2]
    if not(os.path.isfile(path)):
        logging.info("No rotation_comparison table -- GENERATING TABLE")
        f = open(path, 'wt')
        writer = csv.writer(f)
        writer.writerow(["ref", "chan", "sta", "chan",  "ssaz", "ssdist", "ref esaz", "esaz", "azimuth T", "azimuth R"])
        writer.writerow(new_row)
        f.close()
    else:
        with open(path, mode='r') as ifile:
            existingRows = [row for row in csv.reader(ifile)]
        
        with open(path, mode='a') as ofile:
            if new_row not in existingRows:
                csv.writer(ofile).writerow(new_row)
                
def plot_tr(tr, sta, chan, label, fig=False, style='r', delay=0, jump=1, display=False):
    
    if not fig:
        fig = plt.figure()
        fig.suptitle('%s-%s' % (sta, chan))

    this = 1
    for rec in tr.iter_record():
        data = rec.trdata()

        add_trace_to_plot(data, style=style, label=label, count=tr.record_count, item=this)
    
        this += 1

    return fig


def add_trace_to_plot(data, fig=False, style='r', label='signal', count=1, item=1, delay=0, jump=1):
    start = int(delay * jump)
    plot_axis = range(start, int(len(data) * jump) + start, int(jump))

    plt.subplot(count, 1 , item)
    plt.plot(plot_axis, data, style, label=label)
    plt.legend(loc=1)


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
#class Stations():
#    def __init__(self, select, ref_sta, db, time, logging, event_data=None):
#        self.db = db
#        self.select = select
#        self.ref_sta = ref_sta
#        self.logging = logging
#        self.stations = {}
#
#        #try:
#        #    self.db = datascope.dbopen( self.databasename, "r+" )
#        #except Exception,e:
#        #    self.logging.error('Problems opening database: %s %s' % (self.db,e) )
#
#
#        try:
#            self.sitetable = self.db.lookup(table='site')
#        except Exception,e:
#            self.logging.error('Problems opening site table: %s %s' % (self.db,e) )
#       
#        self.get_stations(time, event_data)
#
#    def get_ref_sta(self, time):
#        
#        yearday = stock.epoch2str(time, '%Y%j')
#
#        steps = ['dbopen site']
#        steps.extend(['dbsubset ondate <= %s && (offdate >= %s || offdate == NULL)' % (yearday,yearday)])
#        steps.extend(['dbsort sta'])
#
#        if self.select:
#            steps.extend( ['dbsubset sta =~ /%s/' % self.ref_sta ])
#
#        self.logging.info( 'Database query for stations:' )
#        self.logging.info( ', '.join(steps) )
#    
#        with datascope.freeing(self.db.process( steps )) as dbview:
#            for temp in dbview.iter_record():
#                self.logging.info( 'Extracting sites for origin from db' )
#                (self.ref_lat,self.ref_lon) = temp.getv('lat','lon')
#    
#    def get_stations(self, time, event_data=None):
#        self.get_ref_sta(time)
#
#        yearday = stock.epoch2str(time, '%Y%j')
#
#
#        steps = ['dbopen site']
#        steps.extend(['dbsubset ondate <= %s && (offdate >= %s || offdate == NULL)' % (yearday,yearday)])
#        steps.extend(['dbsort sta'])
#
#        if self.select:
#            steps.extend( ['dbsubset sta =~ /%s|%s/' % (self.ref_sta, self.select) ])
#        else:
#            steps.extend( ['dbsubset sta =~ /%s/' % (self.ref_sta) ])
#        
#        self.logging.info( 'Database query for stations:' )
#        self.logging.info( ', '.join(steps) )
#
#        with datascope.freeing(self.db.process( steps )) as dbview:
#            for temp in dbview.iter_record():
#                self.logging.info( 'Extracting sites for origin from db' )
#                (sta,lat,lon) = temp.getv('sta','lat','lon')
#
#                
#                ssaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
#                                                (self.ref_lat,self.ref_lon,lat,lon) )
#                ssdelta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
#                                                (self.ref_lat,self.ref_lon,lat,lon) )
#                ssdistance = round(temp.ex_eval('deg2km(%s)' % ssdelta), 2)
#                
#                if event_data:
#                    seaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
#                                                    (lat,lon,event_data.lat,event_data.lon) )
#                    esaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
#                                                    (event_data.lat,event_data.lon,lat,lon) )
#                    delta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
#                                                    (event_data.lat,event_data.lon,lat,lon) )
#                    realdistance = temp.ex_eval('deg2km(%s)' % delta)
#                    # round to nearest distance step. from velocity model
#
#                    pdelay = int(temp.ex_eval('pphasetime(%s,%s)' % (delta,event_data.depth)))
#                    if pdelay > 0:
#                        pdelay -= 1
#                    else:
#                        pdelay = 0
#
#                    ptime = time + pdelay
#                else:
#                    seaz = None
#                    esaz = None
#                    delta = None
#                    realdistance = None
#                    pdelay = None
#                    ptime = None
#
#                self.stations[sta] = {
#                            'lat': lat,
#                            'lon': lon,
#                            'delta': delta,
#                            'realdistance': realdistance,
#                            'pdelay': pdelay,
#                            'ptime': ptime,
#                            'seaz': seaz,
#                            'esaz': esaz,
#                            'ssaz': ssaz,
#                            'ssdistance': ssdistance
#                            }
#    
#    def station_list(self):
#        stations = []
#        for sta in self.stations:
#            stations.append(sta)
#        return stations
#
