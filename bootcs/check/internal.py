"""
Additional check50 internals exposed to extension writers.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

import importlib

from .. import lib50
from . import _exceptions


def _(s):
    """Translation function - returns string as-is for now."""
    return s


#: Directory containing the check and its associated files
check_dir = None

#: Temporary directory in which the current check is being run
run_dir = None

#: Temporary directory that is the root (parent) of all run_dir(s)
run_root_dir = None

#: Directory check50 was run from
student_dir = None

#: Boolean that indicates if a check is currently running
check_running = False

#: The user specified slug used to identifies the set of checks
slug = None

#: The current programming language being checked
_current_language = None

#: Config loader for bootcs
CONFIG_LOADER = lib50.config.Loader("bootcs")
CONFIG_LOADER.scope("files", "include", "exclude", "require")


class Register:
    """
    Class with which functions can be registered to run before / after checks.
    """

    def __init__(self):
        self._before_everies = []
        self._after_everies = []
        self._after_checks = []

    def after_check(self, func):
        """Run func once at the end of the check, then discard func."""
        if not check_running:
            raise _exceptions.Error(
                "cannot register callback to run after check when no check is running"
            )
        self._after_checks.append(func)

    def after_every(self, func):
        """Run func at the end of every check."""
        if check_running:
            raise _exceptions.Error(
                "cannot register callback to run after every check when check is running"
            )
        self._after_everies.append(func)

    def before_every(self, func):
        """Run func at the start of every check."""
        if check_running:
            raise _exceptions.Error(
                "cannot register callback to run before every check when check is running"
            )
        self._before_everies.append(func)

    def __enter__(self):
        for f in self._before_everies:
            f()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only run 'afters' when check has passed
        if exc_type is not None:
            return

        # Run and remove all checks registered to run after a single check
        while self._after_checks:
            self._after_checks.pop()()

        for f in self._after_everies:
            f()


#: Sole instance of the Register class
register = Register()


def load_config(check_dir):
    """
    Load configuration file from ``check_dir / ".cs50.yaml"``, applying
    defaults to unspecified values.
    """

    # Defaults for top-level keys
    options = {"checks": "__init__.py", "dependencies": None, "translations": None}

    # Defaults for translation keys
    translation_options = {
        "localedir": "locale",
        "domain": "messages",
    }

    # Get config file
    try:
        config_file = lib50.config.get_config_filepath(check_dir)
    except lib50.Error:
        raise _exceptions.Error(_("Invalid slug for check50. Did you mean something else?"))

    # Load config
    with open(config_file) as f:
        try:
            config = CONFIG_LOADER.load(f.read())
        except lib50.InvalidConfigError:
            raise _exceptions.Error(_("Invalid slug for check50. Did you mean something else?"))

    # Update the config with defaults
    if isinstance(config, dict):
        options.update(config)

    # Apply translations
    if options["translations"]:
        if isinstance(options["translations"], dict):
            translation_options.update(options["translations"])
        options["translations"] = translation_options

    return options


def import_file(name, path):
    """
    Import a file given a raw file path.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_current_language():
    """
    Get the current programming language being checked.

    Returns:
        str: Current language (e.g., 'c', 'python', 'java'), or None if not set.
    """
    return _current_language


def set_current_language(language):
    """
    Set the current programming language being checked.

    Args:
        language (str): Language identifier (e.g., 'c', 'python', 'java').
    """
    global _current_language
    _current_language = language


def get_problem_name():
    """
    Extract the problem name from the current slug.

    For slug format "{courseSlug}/{stageSlug}", returns stageSlug.
    For example: "cs50/hello" -> "hello"

    Returns:
        str: The problem/stage name, or None if slug is not set.
    """
    if slug is None:
        return None

    parts = slug.split("/")
    if len(parts) >= 2:
        return parts[-1]  # Return last part as problem name
    return slug


def _yes_no_prompt(prompt):
    """
    Raise a prompt, returns True if yes is entered, False if no is entered.
    """
    return _("yes").startswith(input(_("{} [Y/n] ").format(prompt)).lower())
