"""Errors and exceptions for ANF lib routines."""

class AnfError(Exception):
    """Base class for errors raised by anf lib."""
    pass

class AnfLibraryLoadError(AnfError):
    """Could not load a library via Ctypes."""
    pass

