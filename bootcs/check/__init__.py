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

# Phase 1: Language adapters
from .adapters import LanguageAdapter, create_adapter

# Phase 2: Helper functions
from .helpers import standard_compile_check, with_adapter


def get_adapter():
    """
    Get language adapter for current check context.
    
    Automatically retrieves problem name and language from internal state.
    Convenience function to avoid repetition in check implementations.
    
    Returns:
        LanguageAdapter: Configured adapter for current problem/language
    """
    problem = internal.get_problem_name()
    language = internal.get_current_language()
    return create_adapter(problem, language)


__all__ = ["import_checks", "data", "exists", "hash", "include", "regex",
           "run", "log", "Failure", "Mismatch", "Missing", "check", "EOF",
           "c", "java", "internal", "hidden",
           # Phase 1: Adapters
           "LanguageAdapter", "create_adapter", "get_adapter"]
