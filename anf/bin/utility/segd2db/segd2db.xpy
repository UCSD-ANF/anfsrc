#
# @authors:
# Juan Reyes <reyes@ucsd.edu>
# Malcolm White <mcwhite@ucsd.edu>
#
# @usage:
#   Create:
#      element = segd(path)             # Default mode
#      element = segd(path,debug=True)  # Enable Debug mode. Verbose output
#   Access:
#      print element                           # Nice print of values
#      element.info                            # return string value of description
#      element.path                            # return string value for path
#      element.file                            # return string value for filename
#      element.list()                          # return list of databases
#      element.purge(db)                       # cleanup object.
#
#   Note:
#
#

from __main__ import *

class SegDException(Exception):
    """
    New exception for the SEGD class.
    Just empty for now.
    """
    pass

class SegD:

    def __init__(self, path, debug=False):
        self.type = False
        self.path = os.path.abspath(path)
        self.nickname = nickname
        self.debug = debug

        # Create dictionary to hold all the values
        self.dbs = {}

        # Load the dbs
        self._get_list()


    def __str__(self):
        """
        end-user/application display of content using print() or log.msg()
        """
        return ''.join(["\n*dbcentral*:\t%s: %s" % (value,self.path[value]) for value in sorted(self.path.keys())])


    def info(self):
        """
        Method to print nicely the information contained in the object.
        """

        print "*segd*:\tsegd.type() => %s" % self.type
        print "*segd*:\tsegd.path() => %s" % self.path
        print "*segd*:\tsegd.list() => %s" % self.list()
        for element in sorted(self.dbs):
            print "*segd*:\t%s => %s" % (element,self.dbs[element]['times'])


    def __call__(self)):
        """
        Method to intercepts data requests.
        """

        self.info()
        return False


    def __del__(self):
        """
        Method to clean database objects.
        """

        self.dbs = {}


    def _problem(self, log):
        """
        Method to print problems and raise exceptions
        """
        raise SegDException('*segd*: ERROR=> %s' % log)


    def _get_list(self):
        """
        Private method.
        """
        pass


    def list(self):
        """
        Method to list items.
        """

        try:
            return self.dbs.keys()
        except:
            raise dbcentralException('*segd*: ERROR=> Cannot check content of list!')


    def purge(self,tbl=None):
        """
        Method to clean object.
        """
        pass


if __name__ == '__main__':
    """
    This will run if the file is called directly.
    """

    segdobject = SegD('./my_segd_file.segd')

    print 'segdobject = segd("%s")' % (segdobject.path)
    print ''
    print '%s' % segdobject
    print ''
    print 'segdobject.list() => %s' % segdobject.list()
    print ''
    try:
        segdobject.purge()
    except Exception, e:
        print 'segdobject.purge() => %s' % e

    print ''
