"""
Error classes for lib50 compatibility layer.

Based on lib50 by CS50 (https://github.com/cs50/lib50)
Licensed under GPL-3.0
"""

import os

from . import _

__all__ = [
    "Error",
    "InvalidSlugError",
    "MissingFilesError",
    "TooManyFilesError",
    "InvalidBranchError",
    "InvalidConfigError",
    "MissingToolError",
    "TimeoutError",
    "ConnectionError",
]


class Error(Exception):
    """
    A generic lib50 Error.

    :ivar dict payload: arbitrary data
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payload = {}


class InvalidSlugError(Error):
    """A lib50.Error signalling that a slug is invalid."""

    pass


class MissingFilesError(Error):
    """
    A lib50.Error signaling that files are missing.
    This error's payload has a ``files`` and ``dir`` key.
    """

    def __init__(self, files, dir=None):
        if dir is None:
            dir = os.path.expanduser(os.getcwd())

        super().__init__(
            "{}\n{}\n{}".format(
                _("You seem to be missing these required files:"),
                "\n".join(files),
                _(
                    "You are currently in: {}, did you perhaps intend another directory?".format(
                        dir
                    )
                ),
            )
        )
        self.payload.update(files=files, dir=dir)


class TooManyFilesError(Error):
    """
    A lib50.Error signaling that too many files were attempted to be included.
    """

    def __init__(self, limit, dir=None):
        if dir is None:
            dir = os.path.expanduser(os.getcwd())

        super().__init__(
            "{}\n{}".format(
                _("Looks like you are in a directory with too many (> {}) files.").format(limit),
                _(
                    "You are currently in: {}, did you perhaps intend another directory?".format(
                        dir
                    )
                ),
            )
        )
        self.payload.update(limit=limit, dir=dir)


class InvalidBranchError(Error):
    """A lib50.Error signalling that a branch prefix is invalid."""

    pass


class InvalidConfigError(Error):
    """A lib50.Error signalling that a config is invalid."""

    pass


class MissingToolError(InvalidConfigError):
    """A lib50.InvalidConfigError signalling that an entry for a tool is missing in the config."""

    pass


class TimeoutError(Error):
    """A lib50.Error signalling a timeout has occured."""

    pass


class ConnectionError(Error):
    """A lib50.Error signalling a connection has errored."""

    pass
