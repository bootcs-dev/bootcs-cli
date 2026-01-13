"""
Core API functions for lib50 compatibility layer.

Based on lib50 by CS50 (https://github.com/cs50/lib50)
Licensed under GPL-3.0
"""

import contextlib
import glob
import os
import shutil
import tempfile
from pathlib import Path

from . import _
from ._errors import Error, MissingFilesError, TooManyFilesError

__all__ = ["working_area", "cd", "files"]

DEFAULT_FILE_LIMIT = 10000


@contextlib.contextmanager
def working_area(files, name=""):
    """
    A contextmanager that copies all files to a temporary directory (the working area)

    :param files: all files to copy to the temporary directory
    :type files: list of string(s) or pathlib.Path(s)
    :param name: name of the temporary directory
    :type name: str, optional
    :return: path to the working area
    :type: pathlib.Path
    """
    with tempfile.TemporaryDirectory() as dir:
        dir = Path(Path(dir) / name)
        dir.mkdir(exist_ok=True)

        for f in files:
            dest = (dir / f).absolute()
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, dest)
        yield dir


@contextlib.contextmanager
def cd(dest):
    """
    A contextmanager for temporarily changing directory.

    :param dest: the path to the directory
    :type dest: str or pathlib.Path
    :return: dest unchanged
    :type: str or pathlib.Path
    """
    origin = os.getcwd()
    try:
        os.chdir(dest)
        yield dest
    finally:
        os.chdir(origin)


def _is_relative_to(path, base):
    """Check if path is relative to base. Compatible with Python < 3.9."""
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _glob(pattern, limit=DEFAULT_FILE_LIMIT):
    """
    Glob for pattern, returning up to limit results.
    Raises TooManyFilesError if limit is exceeded.
    """
    results = set()
    for path in glob.iglob(pattern, recursive=True):
        # Skip hidden files/directories
        if any(part.startswith(".") for part in Path(path).parts):
            continue
        if os.path.isfile(path):
            results.add(path)
        if len(results) > limit:
            raise TooManyFilesError(limit)
    return results


def files(
    patterns,
    require_tags=("require",),
    include_tags=("include",),
    exclude_tags=("exclude",),
    root=".",
    limit=DEFAULT_FILE_LIMIT,
):
    """
    Based on a list of patterns determine which files should be included and excluded.
    """
    require_tags = list(require_tags)
    include_tags = list(include_tags)
    exclude_tags = list(exclude_tags)

    # Ensure tags do not start with !
    for tags in [require_tags, include_tags, exclude_tags]:
        for i, tag in enumerate(tags):
            tags[i] = tag[1:] if tag.startswith("!") else tag

    with cd(root):
        # Include everything but hidden paths by default
        included = _glob("*", limit=limit)
        excluded = set()

        if patterns:
            missing_files = []

            for pattern in patterns:
                if not _is_relative_to(Path(pattern.value).expanduser().resolve(), Path.cwd()):
                    raise Error(
                        _(
                            "Cannot include/exclude paths outside the current "
                            "directory, but such a path ({}) was specified."
                        ).format(pattern.value)
                    )

                # Include all files that are tagged with !require
                if pattern.tag in require_tags:
                    file = str(Path(pattern.value))
                    if not Path(file).exists():
                        missing_files.append(file)
                    else:
                        try:
                            excluded.remove(file)
                        except KeyError:
                            pass
                        included.add(file)

                # Include all files that are tagged with !include
                elif pattern.tag in include_tags:
                    new_files = _glob(pattern.value, limit=limit)
                    excluded -= new_files
                    included |= new_files

                # Exclude all files that are tagged with !exclude
                elif pattern.tag in exclude_tags:
                    new_files = _glob(pattern.value, limit=limit)
                    included -= new_files
                    excluded |= new_files

            if missing_files:
                raise MissingFilesError(missing_files)

    return included, excluded
