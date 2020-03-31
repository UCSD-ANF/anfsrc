"""Errors and Exceptions for poc2mongo."""


class Poc2MongoError(Exception):
    """Base exception for poc2mongo errors."""

    pass


class Poc2MongoAuthError(Poc2MongoError):
    """Authentication errors with MongoDB."""

    pass


class Poc2MongoConfigError(Poc2MongoError):
    """Configuration error for poc2mongo."""

    pass
