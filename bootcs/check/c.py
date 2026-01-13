"""
C language support for check50.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

import os
import re
import tempfile
import xml.etree.cElementTree as ET
from pathlib import Path

from . import internal
from ._api import Failure, log, run


def _(s):
    """Translation function - returns string as-is for now."""
    return s


#: Default compiler for compile()
CC = "clang"

#: Default CFLAGS for compile()
CFLAGS = {"std": "c11", "ggdb": True, "lm": True}

#: Library paths to search for static/dynamic libraries
LIB_PATHS = ["/usr/local/lib", "/opt/homebrew/lib"]

#: Static libraries to prefer (avoids runtime dynamic library issues)
#: Format: flag_name -> static_library_filename
STATIC_LIBS = {
    "lcs50": "libcs50.a",
}


def _find_static_lib(lib_name):
    """Find static library file path, return None if not found."""
    for lib_path in LIB_PATHS:
        static_path = os.path.join(lib_path, lib_name)
        if os.path.isfile(static_path):
            return static_path
    return None


def compile(*files, exe_name=None, cc=CC, max_log_lines=50, **cflags):
    """
    Compile C source files.

    :param files: filenames to be compiled
    :param exe_name: name of resulting executable
    :param cc: compiler to use (CC by default)
    :param cflags: additional flags to pass to the compiler
    :raises check50.Failure: if compilation failed
    :raises RuntimeError: if no filenames are specified
    """

    if not files:
        raise RuntimeError(_("compile requires at least one file"))

    if exe_name is None and files[0].endswith(".c"):
        exe_name = Path(files[0]).stem

    files_str = " ".join(files)

    flags = CFLAGS.copy()
    flags.update(cflags)
    flags = " ".join(
        (f"-{flag}" + (f"={value}" if value is not True else "")).replace("_", "-")
        for flag, value in flags.items()
        if value
    )

    out_flag = f" -o {exe_name} " if exe_name is not None else " "

    # Check for static libraries to use instead of dynamic ones
    # This avoids runtime library loading issues on different systems
    static_lib_flags = ""  # noqa: F841

    for flag, value in list(flags.items()) if isinstance(flags, dict) else []:
        pass  # flags is already a string at this point

    # Parse flags string and replace -lXXX with static library paths where available
    flag_parts = flags.split()
    final_flags = []
    for part in flag_parts:
        if part.startswith("-l"):
            lib_flag = part[1:]  # e.g., "lcs50"
            if lib_flag in STATIC_LIBS:
                static_lib = _find_static_lib(STATIC_LIBS[lib_flag])
                if static_lib:
                    static_lib_flags += f" {static_lib}"
                    continue  # Skip this flag, use static lib instead
        final_flags.append(part)

    flags = " ".join(final_flags)

    # Add library paths for any remaining dynamic libraries
    lib_flags = ""
    for lib_path in LIB_PATHS:
        if os.path.isdir(lib_path):
            lib_flags += f" -L{lib_path}"
            break  # Use first available path

    process = run(f"{cc} {files_str}{out_flag}{flags}{lib_flags}{static_lib_flags}")

    # Strip out ANSI codes
    stdout = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", process.stdout())

    # Log max_log_lines lines of output in case compilation fails
    if process.exitcode != 0:
        lines = stdout.splitlines()

        if len(lines) > max_log_lines:
            lines = lines[: max_log_lines // 2] + lines[-(max_log_lines // 2) :]

        for line in lines:
            log(line)

        raise Failure("code failed to compile")


def valgrind(command, env={}):
    """
    Run a command with valgrind.

    :param command: command to be run
    :type command: str
    :param env: environment in which to run command
    :type env: str
    :raises check50.Failure: if valgrind reports any errors
    """
    xml_file = tempfile.NamedTemporaryFile()
    internal.register.after_check(lambda: _check_valgrind(xml_file))

    valgrind_cmd = (
        f"valgrind --show-leak-kinds=all --xml=yes --xml-file={xml_file.name} -- {command}"
    )
    return run(valgrind_cmd, env=env)


def _check_valgrind(xml_file):
    """Log and report any errors encountered by valgrind."""
    log(_("checking for valgrind errors..."))

    xml = ET.ElementTree(file=xml_file)

    reported = set()
    for error in xml.iterfind("error"):
        kind = error.find("kind").text
        what = error.find("xwhat/text" if kind.startswith("Leak_") else "what").text

        msg = ["\t", what]

        for frame in error.iterfind("stack/frame"):
            obj = frame.find("obj")
            if obj is not None and internal.run_dir in Path(obj.text).parents:
                file, line = frame.find("file"), frame.find("line")
                if file is not None and line is not None:
                    msg.append(f": ({_('file')}: {file.text}, {_('line')}: {line.text})")
                break

        msg = "".join(msg)
        if msg not in reported:
            log(msg)
            reported.add(msg)

    if reported:
        raise Failure(_("valgrind tests failed; see log for more information."))
