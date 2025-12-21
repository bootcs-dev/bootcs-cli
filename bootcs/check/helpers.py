"""
Helper functions for common check patterns.

Provides reusable utilities to reduce boilerplate in check definitions.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

from functools import wraps
from typing import Optional

from . import internal
from .adapters import create_adapter


def standard_compile_check(problem: Optional[str] = None):
    """
    Create a standard compilation check function.
    
    This helper automatically handles language-specific compilation:
    - C: Compiles with lcs50=True (links cs50 library)
    - Java: Standard compilation
    - Python: Syntax validation (no-op currently)
    
    Args:
        problem: Problem name (e.g., "caesar", "hello")
                If None, will be inferred from check context
    
    Returns:
        A check function that performs compilation
    
    Usage:
        >>> from bootcs.check import check
        >>> from bootcs.check.helpers import standard_compile_check
        >>> 
        >>> @check()
        >>> def exists():
        >>>     create_adapter("caesar").require_exists()
        >>> 
        >>> # Option 1: Inline assignment
        >>> compiles = standard_compile_check("caesar")
        >>> 
        >>> # Option 2: As decorator (more explicit)
        >>> @check(exists)
        >>> def compiles():
        >>>     return standard_compile_check("caesar")()
    
    Note:
        This is a factory function that returns the actual check function.
        It's designed to reduce the repetitive compilation boilerplate across checks.
    """
    def compile_func():
        """compiles (or validates syntax)"""
        prob = problem or internal.get_problem_name()
        lang = internal.get_current_language()
        adapter = create_adapter(problem=prob)
        
        if lang == 'c':
            adapter.compile(lcs50=True)
        else:
            adapter.compile()
    
    return compile_func


def with_adapter(problem: str):
    """
    Decorator that provides a pre-created adapter to check functions.
    
    Reduces boilerplate by creating the adapter once and passing it
    to the decorated function.
    
    Args:
        problem: Problem name for adapter creation
    
    Usage:
        >>> @check(compiles)
        >>> @with_adapter("caesar")
        >>> def encrypts_a_as_b(adapter):
        >>>     adapter.run("1").stdin("a").stdout("b").exit(0)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            adapter = create_adapter(problem=problem)
            return func(adapter, *args, **kwargs)
        return wrapper
    return decorator
