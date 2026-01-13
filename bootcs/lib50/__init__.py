"""
lib50 compatibility layer for bootcs-cli-v2.

This module provides a subset of lib50 functionality needed by check50,
adapted for bootcs-cli-v2.

Based on lib50 by CS50 (https://github.com/cs50/lib50)
Licensed under GPL-3.0
"""

import pathlib as _pathlib


# Internationalization - simplified, no locale support for now
def _(s):
    """Translation function - returns string as-is for now."""
    return s


_LOCAL_PATH = _pathlib.Path("~/.local/share/bootcs").expanduser().absolute()


def get_local_path():
    """Get the local path for bootcs data."""
    return _LOCAL_PATH


def set_local_path(path):
    """Set the local path for bootcs data."""
    global _LOCAL_PATH
    _LOCAL_PATH = _pathlib.Path(path).expanduser().absolute()


from . import config  # noqa: E402
from ._api import cd, files, working_area  # noqa: E402
from ._errors import (  # noqa: E402
    Error,
    InvalidConfigError,
    InvalidSlugError,
    MissingFilesError,
    MissingToolError,
    TooManyFilesError,
)

__all__ = [
    "Error",
    "InvalidSlugError",
    "MissingFilesError",
    "TooManyFilesError",
    "InvalidConfigError",
    "MissingToolError",
    "working_area",
    "cd",
    "files",
    "config",
    "get_local_path",
    "set_local_path",
]
