"""
BootCS Check Module - Compatible with check50 API

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

__version__ = "2.0.0"


def _(s):
    """Translation function - returns string as-is for now."""
    return s


from ._api import (
    import_checks,
    data, _data,
    exists,
    hash,
    include,
    run,
    log, _log,
    hidden,
    Failure, Mismatch, Missing
)

from . import regex
from . import c
from . import java
from . import internal
from .runner import check
from pexpect import EOF

__all__ = ["import_checks", "data", "exists", "hash", "include", "regex",
           "run", "log", "Failure", "Mismatch", "Missing", "check", "EOF",
           "c", "java", "internal", "hidden"]
