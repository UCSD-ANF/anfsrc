"""
A module containing miscellaneous Antelope Python API convenience
functions.

Caveats:
This module is dependant on the 5.4 version of the Antelope Python
API and backwards compatibility is not guaranteed.
"""
import sys
import os
sys.path.append('%s/data/python' % os.environ['ANTELOPE'])

from antelope.datascope import Dbptr

def distance(lat1, lon1, lat2, lon2, in_km=False):
    """
    Return the distance between two geographical points.

    Arguments:
    lat1 - geographical latitude of point A
    lon1 - geographical longitude of point A
    lat2 - geographical latitude of point B
    lon2 - geographical longitude of point B

    Keyword Arguments:
    in_km - Default: False. If in_km is a value which evaluates to
        True, the distance between point A and point B is returned
        in kilometers.

    Returns:
    Returns the distance between point A and point B. By default,
    distance is returned in degrees.

    Example:
    In [1]: import antpy

    In [2]: antpy.distance(45.45, -75.7, 32.7, -117.17)
    Out[2]: 34.17313568649101

    In [3]: antpy.distance(45.45, -75.7, 32.7, -117.17, in_km=True)
    Out[3]: 3804.1522020402367
    """
    if in_km:
        return Dbptr().ex_eval('deg2km(%f)' %
            Dbptr().ex_eval('distance(%f, %f, %f, %f)'
                % (lat1, lon1, lat2, lon2)))
    else: return Dbptr().ex_eval('distance(%f ,%f ,%f, %f)'
            % (lat1, lon1, lat2, lon2))

def azimuth(lat1, lon1, lat2, lon2):
    """
    Returns the azimuth between two geographical points.

    Arguments:
    lat1 - geographical latitude of point A
    lon1 - geographical longitude of point A
    lat2 - geographical latitude of point B
    lon2 - geographical longitude of point B

    Returns:
    Returns the azimuth between point A and point B in degrees.

    Example:
    In [1]: import antpy

    In [2]: antpy.azimuth(45.45, -75.7, 32.7, -117.17)
    Out[2]: 262.80443927342213
    """
    return Dbptr().ex_eval('azimuth(%f, %f, %f, %f)'
            % (lat1, lon1, lat2, lon2))

def get_null_value(table, field):
    """
    Returns the null value of a particular field in the CSS3.0 schema.

    Arguments:
    table - A table in the CSS3.0 schema.
    field - A field in table.

    Returns:
    The null value of the field for the table from the CSS3.0 schema.

    Example:
    In [1]: import antpy

    In [2]: antpy.get_null_value('origin', 'time')
    Out[2]: -9999999999.999
    """
    nulls = {'origin': {\
                'lat': -999.0000,\
                'lon': -999.000,\
                'depth': -999.000,\
                'time': -9999999999.99900,\
                'orid': -1,\
                'evid': -1,\
                'jdate': -1,\
                'nass': -1,\
                'ndef': -1,\
                'ndp': -1,\
                'grn': -1,\
                'srn': -1,\
                'etype': '-',\
                'review': '-',\
                'depdp': -999.0000,\
                'dtype': '-',\
                'mb': -999.00,\
                'mbid': -1,\
                'ms': -999.00,\
                'msid': -1,\
                'ml': -999.00,\
                'mlid': -1,\
                'algorithm': '-',\
                'commid': -1,\
                'auth': '-',\
                'lddate': -9999999999.99900
                },\
            'arrival': {
                'sta': '-',\
                'time': -9999999999.99900,\
                'arid': -1,\
                'jdate': -1,\
                'stassid': -1,\
                'chanid': -1,\
                'chan': '-',\
                'iphase': '-',\
                'stype': '-',\
                'deltim': -1.000,\
                'azimuth': -1.00,\
                'delaz': -1.00,\
                'slow': -1.00,\
                'delslo': -1.00,\
                'ema': -1.00,\
                'rect': -1.000,\
                'amp': -1.0,\
                'per': -1.00,\
                'logat': -999.00,\
                'clip': '-',\
                'fm': '-',\
                'snr': -1,\
                'qual': '-',\
                'auth': '-',\
                'commid': -1,\
                'lddate': -9999999999.99900
                },\
            'assoc': {
                    'arid': -1,\
                    'orid': -1,\
                    'sta': '-',\
                    'phase': '-',\
                    'belief': 9.99,\
                    'delta': -1.000,\
                    'seaz': -999.00,\
                    'esaz': -999.00,\
                    'timeres': -999.000,\
                    'timedef': '-',\
                    'azres': -999.0,\
                    'azdef': '-',\
                    'slores': -999.00,\
                    'slodef': '-',\
                    'emares': -999.0,\
                    'wgt': -1.000,\
                    'vmodel': '-',\
                    'commid': -1,\
                    'lddate': -9999999999.99900
                    }
            }
    return nulls[table][field]

def eval_dict(my_dict):
    """
    Recursively typecast dictionary values of str-type to int-type
    or float-type values if appropriate.

    The method antelope.stock.ParameterFile.pf2dict returns a
    dictionary with all str-type values. This method is intended
    primarily to take such a dictionary and typecast integers to
    int-type values and floating points to float-type values.

    Arguments:
    my_dict - Dictionary to be typecast.

    Returns:
    my_dict - Typecasted dictionary.

    Example:
    In [1]: from antpy import eval_dict

    In [2]: my_dict = {'key1': '3',
       ...:           'key2': '4.5',
       ...:           'key3': {'key3A': 'A string.',
       ...:                    'key3B': 'Another string.',
       ...:                    'key3C': {'key3CA': '25',
       ...:                              'key3CB': '67.3'
       ...:                             }
       ...:                  }
       ...:          }

    In [3]: eval_dict(my_dict)
    Out[3]:
    {'key1': 3,
     'key2': 4.5,
     'key3': {'key3A': 'A string.',
              'key3B': 'Another string.',
              'key3C': {'key3CA': 25,
                        'key3CB': 67.3
                       }
              }
    }
    """
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
