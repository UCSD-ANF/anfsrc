"""poc2mongo main module.

Implements the main function of the poc2mongo program.
"""

from os.path import basename

from anf.logutil import getAppLogger, getLogger

from . import Poc2MongoApp
from .error import Poc2MongoError

logger = getLogger(__name__)


def main(argv=None):
    """Run the program."""

    logger = getAppLogger(argv=argv)
    app = Poc2MongoApp(argv)
    logger.setLevel(app.options.loglevel)

    logger = getLogger(basename(argv[0]))
    logger.notify("Loglevel set to %s", app.options.loglevel)
    try:
        app.run()
    except Poc2MongoError as e:
        logger.error(str(e))
        return -1
    except Exception:
        logger.exception("failed with an unknown exception.")
        return -1

    logger.debug("Exiting normally.")
    return 0
