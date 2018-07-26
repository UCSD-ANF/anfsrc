from __main__ import *


class Origin():
    """Class for creating origin objects."""
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
        """Get origin info from database."""
        steps = ['dbopen origin']
        steps.extend(['dbsubset orid==%s' % orid ])

        self.logging.debug('Database query for origin info:')
        self.logging.debug(', '.join(steps))
        dbview = self.db.process(steps)

        if not dbview.record_count:
            self.logging.error('No origin after subset for orid [%s]' % self.orid)

        for temp in dbview.iter_record():
            (orid,time,lat,lon,depth) = \
                    temp.getv('orid','time','lat','lon','depth')
            
            self.logging.info("orid=%s" % orid)
            self.logging.info("time:%s (%s,%s)" % (time,lat,lon))
            
            self.orid = orid
            self.depth = depth
            self.strtime = stock.strtime(time)
            self.strdate = stock.strdate(time)
            self.time = time
            self.lat  = lat
            self.lon  = lon

class Site():
    """Class to track site info."""    
    def __init__(self, db, logging):
        self.db = db
        self.logging = logging
        self.stations = {}

        steps = ['dbopen site']
        steps.extend(['dbjoin sitechan'])
        
        self.logging.info('Database query for stations:')
        self.logging.info(', '.join(steps))
    

        self.table = self.db.process(steps)
 
    def get_stations(self, regex, time, reference=False, event_data=None):
        """Get site info for each station."""        
        yearday = stock.epoch2str(time, '%Y%j')

        steps = ['dbsubset ondate <= %s && (offdate >= %s || offdate == NULL)' % \
                (yearday,yearday)]
        
        steps.extend(['dbsort sta'])
        steps.extend(['dbsubset %s' % regex ])

        self.logging.info('Database query for stations:')
        self.logging.info(', '.join(steps))
    
        with datascope.freeing(self.table.process(steps)) as dbview:
            self.logging.info('Extracting sites for origin from db')

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
                                    (self.stations[reference].lat, self.stations[reference].lon, lat, lon))
                            ssdelta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
                                (self.stations[reference].lat, self.stations[reference].lon, lat, lon))
                            ssdistance = round(temp.ex_eval('deg2km(%s)' % ssdelta), 2)
                            
                            self.stations[sta].set_ss(ssaz, ssdelta, ssdistance)

                        if event_data:
                            seaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                    (lat,lon,event_data.lat,event_data.lon))
                            esaz = "%0.2f" % temp.ex_eval('azimuth(%s,%s,%s,%s)' % \
                                    (event_data.lat,event_data.lon,lat,lon))
                            delta = "%0.4f" % temp.ex_eval('distance(%s,%s,%s,%s)' % \
                                    (event_data.lat,event_data.lon,lat,lon))
                            realdistance = temp.ex_eval('deg2km(%s)' % delta)

                            pdelay = int(temp.ex_eval('pphasetime(%s,%s)' % \
                                    (delta,event_data.depth)))
                            
                            if pdelay > 0:
                                pdelay -= 1
                            else:
                                pdelay = 0

                            ptime = time + pdelay

                            self.stations[sta].set_es(
                                    seaz, esaz, delta, realdistance, pdelay, ptime)
 
                                                
        return self.stations

class Records():
    """Class for tracking info from a single sta"""
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
        """Append channel to existing channels"""
        self.chans.append(chan)
       
    def set_ss(self, az, delta, distance):
        """Assign station-station data to class objects."""
        self.ssaz = float(az)
        self.ssdistance = float(distance) 
        self.ssdelta = float(delta)
        
    def set_es(self, seaz, esaz, delta, realdistance, pdelay, ptime):
        """Assign station info to class objects."""
        self.seaz = float(seaz)
        self.esaz = float(esaz)
        self.delta = float(delta)
        self.realdistance = float(realdistance)
        self.pdelay = float(pdelay)
        self.ptime = float(ptime)


class Results():
    """Class for tracking x-correlation result"""
    def __init__(self):
        self.rotated = None
        self.original = None
        self.azimuth = None
        self.xcorr = None
   
    def set_data(self, original, rotated, azimuth, xcorr):
        """Set waveform and x-corr data""" 
        self.set_rotated(rotated)
        self.set_original(original)
        self.set_azimuth(azimuth)
        self.set_xcorr(xcorr)

    def set_rotated(self, data):
        """Create rotated waveform data object."""
        self.rotated = data
            
    def set_original(self, data):
        """Create original waveform data object."""
        self.original = data

    def set_azimuth(self, azimuth):
        """Create azimuth object."""
        self.azimuth = azimuth

    def set_xcorr(self, xcorr):
        """Create xcorr object."""
        self.xcorr = xcorr

 
class Plot():
    """Class for all plotting functions."""
    def __init__(self, width, height, result, reference, ref_sta, ref_chan, sta,
            start, end, result_dir, debug_plot, orid=None):
        total = len(result) 
        self.width = width
        self.height = height * total
        fig = plt.figure(figsize = (width, height))
        axs = [fig.add_subplot(3*total, 3, j) for j in range(1, (3*3*total)+1)]
         
 
        plt.tight_layout()
        fig.subplots_adjust(top=0.9, bottom=0.05)
    
        self.plot_data(axs, result, reference, ref_sta, ref_chan, sta, start, end)
        
        if debug_plot:
            plt.show()            
        else:
            if not orid: 
                filename = "%s_%s_%s.pdf" % \
                        (ref_sta, sta, epoch2str(start, "%Y%j_%H_%M_%S.%s"))
            else:
                filename = "%s_%s_%s.pdf" % (ref_sta, sta, orid)
            
            path = "/".join([result_dir, filename])
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            fig.savefig(path, bbox_inches='tight', pad_inches=0.5, dpi=100)
    
    def plot_data(self, axs, result, reference, ref_sta, ref_chan, sta, start, end):
        """Plot data.""" 
        k = 0 
        for code in result:
            for i,chan in enumerate(result[code]):
                data = result[code][chan]

                if i==0: ind = 0 + k 
                if i==1: ind = 1 + k
                if i==2: ind = 2 + k

                axs[ind].plot(reference[chan], 'b', label='%s_%s%s' % \
                        (ref_sta, ref_chan, chan))
                axs[ind].plot(data.original, 'r', label='%s_%s%s' % \
                        (sta, code, chan))
                axs[ind+3].plot(reference[chan], 'b')
                axs[ind+3].plot(data.rotated, 'r')
             
                axs[ind].legend(loc='upper left', prop={'size': 6})
                
                axs[ind+6].xaxis.set_visible(False)
                axs[ind+6].yaxis.set_visible(False)
                axs[ind+6].patch.set_alpha(0.0)
                axs[ind+6].axis('off')

                text = "Angle: %s\n" % data.azimuth
                text += "Xcorr: %s\n" % round(data.xcorr, 3) 

                axs[ind+6].annotate(unicode(text, "utf-8"), (0.5,0.7),
                        xycoords="axes fraction", va="top", ha="center",
                        fontsize=6, bbox=dict(edgecolor='white',
                        boxstyle='round, pad=0.5', fc="w"), size=12)

                # y-axis labels
                if i == 0:
                    axs[ind].set_ylabel("original", fontsize=12)
                    axs[ind+3].set_ylabel("rotated", fontsize=12)
                
                axs[ind].set_yticks([])
                axs[ind+3].set_yticks([])
                   
                axs[ind].set_xticks([])
                axs[ind+3].set_xticks([])
                
                # xticks and xtick labels 
                tw = end - start
                dt = tw/len(reference[chan])
                xticks = arange(0, len(reference[chan]), len(reference[chan]) / 4)
                xtick_labels = [
                        epoch2str(t, "%Y%j %H:%M:%S.%s")
                        for t in [start + x * dt for x in xticks]
                        ]
                xtick_labels = xticks*dt - 2
                axs[ind+3].set_xticks(xticks)
                axs[ind+3].set_xticklabels(xtick_labels)
                axs[ind+3].set_xlabel("time since predicated first-arrival (s)")
                
                if i==1:
                    axs[ind].set_title("%s_%s compared to %s_%s" % \
                            (ref_sta, ref_chan, sta, code), fontsize=12)
            k+=9 



def free_tr(tr):
    tr.table = datascope.dbALL
    tr.trdestroy()


def tr2vec(tr, record):
    tr.record = record
    data = tr.trdata()
    return data


def cross_correlation(data1, data2):
        time_shift, xcorr_value, cross_corr= xcorr(np.array(data1),
                np.array(data2), shift_len=10, full_xcorr=True)
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
    """Get range with non-integer steps"""
    x = []
    i=0
    while start + i * step < stop:
        x.append(start +  i * step)
        i += 1
    return x

def open_verify_pf(pf,mttime=False):
    """
    Verify that we can get the file and check
    the value of PF_MTTIME if needed.
    Returns pf_object
    """

    logging.debug('Look for parameter file: %s' % pf)

    if mttime:
        logging.debug('Verify that %s is newer than %s' % (pf,mttime))

        PF_STATUS = stock.pfrequire(pf, mttime)
        if PF_STATUS == stock.PF_MTIME_NOT_FOUND:
            logging.warning('Problems looking for %s. PF_MTTIME_NOT_FOUND.' % pf)
            logging.error('No MTTIME in PF file. Need a new version of the %s file!!!' % pf)
        elif PF_STATUS == stock.PF_MTIME_OLD:
            logging.warning('Problems looking for %s. PF_MTTIME_OLD.' % pf)
            logging.error('Need a new version of the %s file!!!' % pf)
        elif PF_STATUS == stock.PF_SYNTAX_ERROR:
            logging.warning('Problems looking for %s. PF_SYNTAX_ERROR.' % pf)
            logging.error('Need a working version of the %s file!!!' % pf)
        elif PF_STATUS == stock.PF_NOT_FOUND:
            logging.warning('Problems looking for %s. PF_NOT_FOUND.' % pf)
            logging.error('No file  %s found!!!' % pf)

        logging.debug('%s => PF_MTIME_OK' % pf)

    try:
        return stock.pfread(pf)
    except Exception,e:
        logging.error('Problem looking for %s => %s' % (pf, e))

def safe_pf_get(pf,field,defaultval=False):
    """
    Safe method to extract values from parameter file
    with a default value option.
    """
    value = defaultval
    if pf.has_key(field):
        try:
            value = pf.get(field,defaultval)
        except Exception,e:
            logging.warning('Problems safe_pf_get(%s,%s)' % (field,e))
            pass

    logging.debug("pf.get(%s,%s) => %s" % (field,defaultval,value))

    return value

# split regex info list
def get_regex(site):
    """Clean regex."""
    regex = site.split()
    return regex


def save_results(ref_sta, ref_chan, sta, chan, result_dir, ref_esaz, ssaz,
        distance, esaz, azimuth1, azimuth2):
    """Save results to file."""
    filename = "rotation_comparison.csv"
    path = "/".join([result_dir, filename])
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    new_row = [ref_sta, ref_chan, sta, chan, ssaz, distance,
            ref_esaz, esaz, azimuth1, azimuth2]
    if not(os.path.isfile(path)):
        logging.info("No rotation_comparison table -- GENERATING TABLE")
        f = open(path, 'wt')
        writer = csv.writer(f)
        writer.writerow(["ref", "chan", "sta", "chan",  "ssaz", "ssdist",
                "ref esaz", "esaz", "azimuth T", "azimuth R"])
        writer.writerow(new_row)
        f.close()
    else:
        with open(path, mode='r') as ifile:
            existingRows = [row for row in csv.reader(ifile)]
        
        with open(path, mode='a') as ofile:
            if new_row not in existingRows:
                csv.writer(ofile).writerow(new_row)
                
def plot_tr(tr, sta, chan, label, fig=False, style='r', delay=0, jump=1, display=False):
    """Set up plot trace figure.""" 
    if not fig:
        fig = plt.figure()
        fig.suptitle('%s-%s' % (sta, chan))

    this = 1
    for rec in tr.iter_record():
        data = rec.trdata()

        add_trace_to_plot(data, style=style, label=label, count=tr.record_count, item=this)
    
        this += 1

    return fig


def add_trace_to_plot(data, fig=False, style='r', label='signal', count=1,
        item=1, delay=0, jump=1):
    """Add individual trace to figure."""
    start = int(delay * jump)
    plot_axis = range(start, int(len(data) * jump) + start, int(jump))

    plt.subplot(count, 1 , item)
    plt.plot(plot_axis, data, style, label=label)
    plt.legend(loc=1)


