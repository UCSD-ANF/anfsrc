"""Utility classes and functions for soh2mongo."""
import pymongo


class soh2mongoException(Exception):
    """Base class for exceptions raised by this module."""


class MongoConfigError(soh2mongoException, pymongo.errors.ConfigurationError):
    """MongoDB configuration is not correct."""


class MongoConnectionTimeout(
    soh2mongoException, pymongo.errors.ServerSelectionTimeoutError
):
    """A timeout occurred connecting to MongoDB."""


class TooManyOrbExtractErrors(soh2mongoException):
    """The number of extract errors has been reached."""
