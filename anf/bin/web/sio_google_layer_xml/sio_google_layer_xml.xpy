"""
@author Geoff Davis
"""

import sys
import os
import glob
from optparse import OptionParser

from antelope import datascope, stock, elog

from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, ElementTree

from time import time
from six import string_types

DEFAULTS = dict(
  webroot = '/anf/web/vhosts/anf.ucsd.edu',
  icon_dir  = '/images/icons/google_earth/snet',
  top_pick_suffix = 'jpg'
)

class Config(object):

  def __init__(self, options):
    self.verbose = options.verbose
    self.detail = options.detail

    confpf = stock.pfread(options.parameter_file)
    #[self.set_val(k,confpf,options) for k in DEFAULTS.iterkeys()]
    [setattr(self, k, v) for k,v in DEFAULTS.iteritems()]
    self.webdir =     confpf['WEBROOT']
    self.cachexml =   confpf['CACHEXML']
    self.db =         confpf['USARRAY_DBMASTER']
    self.photos_dir = confpf['CACHE_TOP_PICK']

    stationspf = stock.pfread(options.stations_pf)
    self.networks = stationspf['network']

    # Set the output filename
    if hasattr(options, 'outfile') and \
    getattr(options, 'outfile') is not None:
      self.outfile = options.outfile
    else:
      suffix = '_detail' if self.detail else ""
      self.outfile = "%s/stations/sio_google_layer%s.xml" % (
        self.cachexml, suffix)
    self.bufferfile = '%s+' % self.outfile

  def set_val(self, k, pf, options=None):
    """ Sets the attribute 'k'.

    Look first in options, then in pf.

    Always convert type to int if at all possible, which is kludgy, but
    acceptable at the moment.
    """
    v = None
    if options is not None:
      try:
        v = getattr(options, k)
      except AttributeError:
        pass
      if v is None:
        v = pf.get(k, DEFAULTS[k])
      try:
        v = int(v)
      except (ValueError, TypeError):
        pass
      setattr(self, k, v)

class SnetsNode(object):
  """Object representing a group of SnetNode objects"""
  def __init__(self, snets):
    """snets is a list of SnetNode objects"""
    self.snets = snets

  def get_xml_element(self,detail=False):
    element = Element('snets')
    for snet in self.snets:
      child = snet.get_xml_element(detail)
      element.append(child)
    return element

class SnetNode(object):
  """Object representing a SEED snet"""
  def __init__(self, code, name):
    self.code = code
    self.name = name

  def get_xml_element(self,detail=False):
    element = Element('snet')
    element.set('id',self.code)
    element.text = '%s: %s' % (self.code, self.name)
    return element

class StationsNode(object):
  """Object representing a group of stations"""
  def __init__(self, stations):
    """stations is a list of StationNodes"""
    self.stations = stations

  def get_xml_element(self,detail=False):
    element = Element('stations')
    for sta in self.stations:
      child = sta.get_xml_element(detail)
      element.append(child)
    return element


class StationNode(object):
  """Object representing a SEED station"""
  fieldmappings = {
    'elev' : 'Elevation',
    'snet' : 'Network',
    'lat' : 'Latitude',
    'lon' : 'Longitude',
    'staname' : 'Name',
    'commtype' : 'Communications_Type',
    'provider' : 'Communications_Provider',
    'time' : 'Station_Ontime',
    'endtime': 'Station_Endtime',
  }

  def __init__(self, sta, snet, staname, lat, lon, elev, commtype,
               provider, insname, time, endtime):
    self.sta = sta
    self.snet = snet
    self.staname = staname
    self.lat = lat
    self.lon = lon
    self.elev = elev
    self.commtype = commtype
    self.provider = provider
    self.insname = insname
    self.time = time
    self.endtime = endtime
    self.photo = None

  def get_xml_element(self,detail=False):
    top = Element('station')
    top.set ( 'name', self.sta)
    for k,v in self.fieldmappings.iteritems():
      value = getattr(self,k)
      child = SubElement(top,v)
      if k in ('lat', 'lon'):
        if detail:
          formatstr='%.5f'
        else:
          formatstr='%.2f'
        formatted_value = formatstr % value
      elif k in ('time', 'endtime'):
        if value > time() or value < 0:
          formatted_value = 'N/A'
        else:
          formatted_value = stock.epoch2str( value, '%Y-%m-%d %T UTC' )
      else:
        if isinstance(value, string_types):
          formatted_value = value
        else:
          formatted_value = '%r' % value
      child.text = formatted_value

    # define Timespan
    ts = SubElement(top, 'TimeSpan')
    if self.time > 0:
      child = SubElement(ts, 'begin')
      child.text = stock.epoch2str(self.time, '%Y-%m-%dT%H:%M:%SZ')
    if self.endtime < time() and self.endtime > 0:
      child = SubElement(ts, 'end')
      child.text = stock.epoch2str(self.endtime, '%Y-%m-%dT%H:%M:%SZ')

    # define Photo
    if self.photo is not None:
      child = SubElement(ts, 'topPickPhoto')
      child.text = self.photo

    return top

class StationListNode(object):
  def __init__(self, snet_nodes, station_nodes):
    self.snets = SnetsNode(snet_nodes)
    self.stations = StationsNode(station_nodes)

  def get_xml_element(self,detail=False):
    element = Element('station_list')
    lm = SubElement(element, 'last_modified')
    lm.text = '%d' % time()
    element.append(self.snets.get_xml_element())
    element.append(self.stations.get_xml_element())
    return element

class App(object):
  """ The main application"""
  def run(self, options):
    """Run the app. Options as parsed by optparse."""
    elog.notify('Starting')
    self.cfg = Config(options)
    photo_top_picks = self.getPhotoTopPicks()
    snet_nodes, station_nodes = self.readDBMaster()

    self.addTopPicksToStationNodes(photo_top_picks, station_nodes)

    # Prepare the overarching XML document
    elog.notify('Preparing the XML Element tree')
    station_list_node = StationListNode(snet_nodes, station_nodes)
    et = ElementTree(station_list_node.get_xml_element(
      self.cfg.detail))

    if self.cfg.verbose:
      elog.notify('Outputting XML to %s' % self.cfg.bufferfile)

    et.write(self.cfg.bufferfile, 'UTF-8', True)

    if self.cfg.verbose:
      elog.notify('Renaming %s to %s' % (self.cfg.bufferfile,
                                         self.cfg.outfile))
    os.rename(self.cfg.bufferfile,self.cfg.outfile)

    elog.notify('Done processing %d stations' % station_nodes.__len__())


  def addTopPicksToStationNodes(self, photo_top_picks, station_nodes):
    """If a station has a top pick photo, associate it with the station"""

    if self.cfg.verbose:
      elog.notify("Associating Top Pick Photos with Station Nodes")

    for station in station_nodes:
      if station.sta in photo_top_picks:
        station.photo = photo_top_picks[station.sta]
      #if self.cfg.verbose:
      #  print "Dumping station %s" % station.sta
      #  print prettify(station.get_xml_element())

  def getPhotoTopPicks(self):
    cfg=self.cfg

    if cfg.verbose:
      elog.notify("Finding Photo Top Picks for each station")

    top_picks = {}
    paths=glob.iglob(cfg.photos_dir + '/*_top_pick_*.' + cfg.top_pick_suffix)
    for path in paths:
      fname = os.path.basename(path)
      sta = fname.split('_top_pick_')[0]
      top_picks[sta]=fname
    return top_picks

  def readDBMaster(self):
    cfg=self.cfg

    if cfg.verbose:
      elog.notify("Processing DB %s" % cfg.db)

    with datascope.closing(datascope.dbopen(cfg.db)) as db:
      dbprocess_commands = [
        'dbopen deployment',
        'dbjoin site',
        'dbjoin snetsta',
        'dbjoin -o comm',
        'dbjoin -o sensor',
        'dbjoin -o instrument',
        'dbsubset insname != NULL',
        'dbsubset chan =~ /(B|H)HZ.*/',
        'dbsort -u vnet snet sta',
      ]
      try:
        dbactivesta = db.process(dbprocess_commands)
        dbsnet = dbactivesta.process('dbsort -u snet')
      except Exception as e:
        print ("readDBMaster: dbprocessing failed with exception: %s" % e)
        sys.exit(1)

      snet_nodes = []
      for i in range(dbsnet.query(datascope.dbRECORD_COUNT)):
        dbsnet.record = i
        snet_code = dbsnet.getv('snet')[0]
        snet_name = cfg.networks[snet_code]['name']
        snet = SnetNode(snet_code, snet_name)
        snet_nodes.append(snet)

      station_nodes = []
      for i in range(dbactivesta.query(datascope.dbRECORD_COUNT)):
        dbactivesta.record = i
        vals=dbactivesta.getv('sta','snet','staname','lat','lon','elev',
                    'commtype','provider','insname','time','endtime')
        station = StationNode(vals[0],vals[1],vals[2],vals[3],vals[4],vals[5],
                          vals[6],vals[7],vals[8],vals[9],vals[10])
        station_nodes.append(station)

    return snet_nodes, station_nodes

def process_command_line(args):
  """Return object called options"""

  # Initialize the parser object
  usage = 'Usage: %prog [-v] [-d] [-p /parameter/file] [-s stations_pf] [-o outputfile.xml]'
  parser = OptionParser(usage=usage)

  parser.add_option('-v', action='store_true', dest='verbose',
                    help='verbose output', default = False)

  parser.add_option('-d', action='store_true', dest='detail',
                    help='detailed station data', default = False)

  parser.add_option('-p', action='store', type='string',
                    dest='parameter_file', help='parameter file name',
                    default =
                    '%s/conf/common.pf' % DEFAULTS['webroot'] )
  parser.add_option('-s', action='store', type='string',
                    dest = 'stations_pf',
                    help = 'stations parameter file name',
                    default =
                    '%s/conf/stations.pf' % DEFAULTS['webroot'] )
  parser.add_option('-o', action='store', type='string',
                    dest = 'outfile',
                    help = 'output XML file' )

  options,args = parser.parse_args(args[1:])

  return options

def prettify(elem):
  """Return a pretty-printed XML string for the Element.
  """
  rough_string = ElementTree.tostring(elem, 'utf-8')
  reparsed = minidom.parseString(rough_string)
  return reparsed.toprettyxml(indent=" ")

def main(args=None):
  if args is None:
    args = sys.argv

  elog.init(args)

  options=process_command_line(args)
  app = App()
  app.run(options)

if __name__ == '__main__':
  exit(main())
