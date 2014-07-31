"""
ANF functions for Antelope
"""

def deep_auto_convert(data):
    """
    call stock.auto_convert on all entries in a dict or array.

    the stock.ParameterFile.get() routine in the Antelope 5.3+ python bindings
    calls stock.auto_convert, but that routine doesn't recursively auto-convert
    all of the entries in a pf Arr object or a Tbl object.
    """

    if type(data) is dict:
        for i in data.keys():
            data[i] = deep_auto_convert(data[i])
    elif type(data) is list:
        for i in range(len(data)):
            data[i] = deep_auto_convert(data[i])
    elif type(data) is str:
        data = stock.auto_convert(data)
    else:
        pass # no-op on unrecognized items

    return data

pass
