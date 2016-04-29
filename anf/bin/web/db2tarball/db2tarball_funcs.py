# Bunch of functions that we don't need on the
# main document.


def zipped_tarball(this_tmp_dir):
    """
    Generate and return the path to the new file
    """
    from __main__ import tarfile

    tgz_name = "%s.tar.gz" % this_tmp_dir

    tar = tarfile.open(tgz_name, 'w:gz')

    tar.add( this_tmp_dir )

    tar.close()

    return tgz_name

def parse_pf_db( raw_text ):
    """
    The parameter file will give us a long
    string that we need to cut into a 2-tuple
    or 3-tuple.
    Example:
    'ta-events     /anf/shared/dbcentral/dbcentral     usarray_rt'
    'ta-events     /anf/db/dbops'
    """

    obj = {}

    temp = raw_text.split()

    if len(temp) == 3:
        obj['name'] = temp[0]
        obj['db'] = temp[1]
        obj['nickname'] = temp[2]
    elif len(temp) == 2:
        obj['name'] = temp[0]
        obj['db'] = temp[1]
        obj['nickname'] = None

    return obj
