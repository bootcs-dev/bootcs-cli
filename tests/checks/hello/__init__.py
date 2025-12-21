"""
Hello Check - Multi-language support using adapters

Supports: C, Java, Python
Tests prompting for name and outputting the name (CS50's hello problem)

Uses standard_compile_check helper to reduce boilerplate.
"""

from bootcs.check import check, get_adapter
from bootcs.check.helpers import standard_compile_check


@check()
def exists():
    """source file exists"""
    get_adapter().require_exists()


# Use helper function for standard compilation pattern
compiles = check(exists)(standard_compile_check("hello"))


@check(compiles)
def emma():
    """responds to name Emma"""
    get_adapter().run().stdin("Emma").stdout("Emma").exit(0)


@check(compiles)
def rodrigo():
    """responds to name Rodrigo"""
    get_adapter().run().stdin("Rodrigo").stdout("Rodrigo").exit(0)

