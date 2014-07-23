"""
Given an API key and an API secret, use the Python Flickr API to generate an
API token with write permissions. This can be used to then populate the 'token'
field in flickerdownload.pf
"""

import sys
from optparse import OptionParser

try:
    import flickrapi
except ImportError:
    sys.exit('Import Error: Do you have the Python Flicker API module '
             'installed correctly?')

def configure():
    """Parse command line arguments"""

    global verbose
    usage = "Usage: %prog [options] api_key api_secret"
    parser = OptionParser(usage=usage)
    #parser.add_option('-k', '--key', action='store', dest='api_key',
    #                  help='Flickr API Key')
    #parser.add_option('-s', '--secret', action='store', dest='api_secret',
    #                  help='Secret for the specified Flickr API Key')
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="verbose output", default=False)
    (options, args) = parser.parse_args()

    verbose = options.verbose

    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    options.api_key = args[0]
    options.api_secret = args[1]

    if verbose:
        print options

    return options

def main():
    """get the key"""

    global verbose

    options = configure()

    flickr = flickrapi.FlickrAPI(options.api_key, options.api_secret)

    (token, frob) = flickr.get_token_part_one(perms='write')
    if not token:
        raw_input("Press ENTER after you authorize this program")
    flickr.get_token_part_two((token, frob))

    print "Your token is:\n%s\n" % token

    return 0

if __name__ == '__main__':
    sys.exit(main())
