import os
import antelope.stock as stock
from soh2mongo.logging_class import getLogger

class stateFileException(Exception):
    """Exceptions thrown by this class"""
    pass

class stateFile:
    """
    Track some information from the realtime process into
    a STATEFILE.
    Save value of pktid in file.
    """
    def __init__(self, filename=False, name='default', start=0):

        self.logging = getLogger('stateFile')

        self.logging.debug( "stateFile.init()" )

        self.filename = filename
        self.name = name
        self.id = start
        self.time = 0
        self.strtime = 'n/a'
        self.latency = 'n/a'
        self.pid = 'PID %s' % os.getpid()

        if not filename: return

        self.directory, self.filename = os.path.split(filename)

        if self.directory and not os.path.isdir( self.directory ):
            os.makedirs( self.directory )

        self.file = os.path.join( self.directory, "%s_%s" % ( self.name,self.filename ) )


        self.logging.debug( 'Open file for STATE tracking [%s]' % self.file )
        if os.path.isfile( self.file ):
            self.open_file('r+')
            self.read_file()
        else:
            self.open_file('w+')

        if not os.path.isfile( self.file ):
            raise stateFileException( 'Cannot create STATE file %s' % self.file )


    def last_id(self):
        self.logging.info( 'last id:%s' % self.id )
        return self.id


    def last_time(self):
        self.logging.info( 'last time:%s' % self.time )
        return self.time


    def read_file(self):
        self.pointer.seek(0)

        if not self.filename: return

        try:
            temp = self.pointer.read().split('\n')
            self.logging.info( 'Previous STATE file %s' % self.file )
            self.logging.info( temp )

            self.id = float(temp[0])
            self.time = float(temp[1])
            self.strtime = temp[2]
            self.latency = temp[3]

            self.logging.info( 'Previous - %s ID:%s TIME:%s LATENCY:%s' % \
                        (self.pid, self.id, self.time, self.latency) )

            if not float(self.id): raise
        except:
            self.logging.warning( 'Cannot find previous state on STATE file [%s]' % self.file )


    def set(self, id, time):

        if not self.filename: return

        self.logging.debug( 'set %s to %s' % (self.filename, id) )

        self.id = id
        self.time = time
        self.strtime = stock.strlocalydtime(time).strip()
        self.latency = stock.strtdelta( stock.now()-time ).strip()

        #self.logging.debug( 'latency: %s' % self.latency )

        try:
            self.pointer.seek(0)
            self.pointer.write( '%s\n%s\n%s\n%s\n%s\n' % \
                    (self.id,self.time,self.strtime,self.latency,self.pid) )
        except Exception as e:
            raise stateFileException( 'Problems while writing to state file: %s %s' % (self.file,e) )


    def open_file(self, mode):
        try:
            self.pointer = open(self.file, mode, 0)
        except Exception as  e:
            raise stateFileException( 'Problems while opening state file: %s %s' % (self.file,e) )
