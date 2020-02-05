"""Exceptions for deployment_map and friends."""

from anf.logutil import getLogger

logger = getLogger(__name__)


class DeployMapError(Exception):
    """General Error for this module."""


class DeployMapValueError(DeployMapError, ValueError):
    """A value is not the required type."""


class PfValidationError(DeployMapValueError):
    """The PF File failed validation."""

    def __init__(self, pfname, **args):
        """Generate a more verbose error message from a given pfname."""
        msg = "The PF File %s failed validation." % pfname
        super(PfValidationError, self).__init__(msg, args)


class YearMonthValueError(DeployMapError, ValueError):
    """The year or month supplied to YearMonth is invalid."""
