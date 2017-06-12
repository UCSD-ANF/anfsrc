"""
ANF functions for Antelope
"""
#
# Some generic Python function
# to make generic operations easy
# to implement and speed up the
# development process.
#
# Split each function into a new file
# and import in this proxy object.
#
# Juan Reye
# reyes@ucsd.edu
#


import logging_helper
# Example:
#   anf.logging_helper.getLogger()
#   anf.logging_helper.getLogger( self.__class__.__name__ )
#   anf.logging_helper.getLogger( 'my_function' )

import anfpf
# Example:
#   anf.anfpf.open_verify( pf )
#   anf.anfpf.open_verify( pf, min_valid_time )

import anftr


import anfstock


import anfdb
#   verify_table()
#       Open database and verify table
#   get_all_fields()
#       At a given database pointer to a particular record query for valid
#       table fields and pull all values.
#
#       Return a dictionary (key=>value) with the values.
#

import anfdb_collections
#    Class for maintaining a Datascope view in memory.
#
#    Open the database while declaring the object. You can
#    specify the table of interest on the argument list and
#    let the init process verify that it's valid and has
#    some data. In example:
#        sites = anf.Collection( database, 'site' )
#
#    Then you can make a second call to "get_view" and extract
#    all valid entries and have the cached in memory in the
#    object.
#
#    Submit a list of db operations to subset your table before
#    pull the values into memory. In example:
#
#        origins = anf.Collection( database, 'origin' )
#        steps = ['dbopen origin']
#        steps.extend([ 'dbsubset evid == %s' % self.evid ])
#
#        origins.get_view( steps, key='origin.orid' )
#

import deep_auto_convert

import str2bool



