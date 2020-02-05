"""Match the provided string to a valid boolean value.

@author Jon Meyer
@email  support@anf.ucsd.edu
"""


def str2bool(v):
    """Parse text as boolean.

    There are many ways for us to define True or False from
    the Antelope Parameter Files. Some of the most common
    alternatives are here. Default will return False.
    """

    return str(v).lower() in ("yes", "true", "t", "y", "1")
