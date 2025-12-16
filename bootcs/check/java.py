"""
Java language support for bootcs check.

Provides compile() and run() functions for Java programs.
"""

import os
import re
import shutil
from pathlib import Path

from ._api import run as _run, log, Failure, exists


def _(s):
    """Translation function - returns string as-is for now."""
    return s


#: Default Java compiler
JAVAC = "javac"

#: Default Java runtime
JAVA = "java"

#: Default compiler options
JAVAC_OPTIONS = {
    "encoding": "UTF-8",
}


def _check_java_installed():
    """Check if Java is installed and available."""
    if not shutil.which(JAVAC):
        raise Failure(_("javac not found. Make sure Java JDK is installed."))
    if not shutil.which(JAVA):
        raise Failure(_("java not found. Make sure Java JRE is installed."))


def compile(*files, javac=JAVAC, classpath=None, **options):
    """
    Compile Java source files.

    :param files: Java source files to compile
    :param javac: Java compiler to use (default: javac)
    :param classpath: classpath for compilation (optional)
    :param options: additional compiler options
    :raises Failure: if compilation fails

    Example usage::

        import bootcs.check as check
        from bootcs.check import java

        @check.check()
        def compiles():
            java.compile("Hello.java")

        @check.check()
        def compiles_multiple():
            java.compile("Main.java", "Helper.java")
    """
    _check_java_installed()

    # Ensure all files exist
    for file in files:
        exists(file)

    # Merge default options with provided options
    opts = {**JAVAC_OPTIONS, **options}

    # Build command
    cmd_parts = [javac]

    # Add classpath if provided
    if classpath:
        cmd_parts.extend(["-cp", classpath])

    # Add options
    for key, value in opts.items():
        if value is True:
            cmd_parts.append(f"-{key}")
        elif value is not False and value is not None:
            cmd_parts.extend([f"-{key}", str(value)])

    # Add source files
    cmd_parts.extend(files)

    cmd = " ".join(cmd_parts)
    log(_("compiling {} with {}...").format(", ".join(files), javac))

    # Run compilation and wait for it to complete
    proc = _run(cmd)
    proc._wait(timeout=60)  # Wait for compilation to finish

    # Check for compilation errors
    if proc.exitcode != 0:
        # Log compilation errors
        output = proc.process.before if proc.process.before else ""
        if output:
            log(_("compilation errors:"))
            for line in output.splitlines()[:20]:  # Limit error output
                log(f"  {line}")

        raise Failure(_("code failed to compile. See log for details."))

    return proc


def run(classname, *args, java=JAVA, classpath=None):
    """
    Run a compiled Java class.

    :param classname: Name of the class to run (without .class extension)
    :param args: Command-line arguments to pass to the program
    :param java: Java runtime to use (default: java)
    :param classpath: classpath for execution (optional)
    :return: Process object for chaining (stdin, stdout, exit, etc.)

    Example usage::

        import bootcs.check as check
        from bootcs.check import java

        @check.check("compiles")
        def prints_hello():
            java.run("Hello").stdout("hello, world")

        @check.check("compiles")
        def accepts_input():
            java.run("Hello").stdin("David").stdout("hello, David")

        @check.check("compiles")
        def with_args():
            java.run("Main", "arg1", "arg2").exit(0)
    """
    _check_java_installed()

    # Build command
    cmd_parts = [java]

    # Add classpath if provided
    if classpath:
        cmd_parts.extend(["-cp", classpath])

    # Add classname
    cmd_parts.append(classname)

    # Add arguments
    cmd_parts.extend(str(arg) for arg in args)

    cmd = " ".join(cmd_parts)
    log(_("running {}...").format(classname))

    return _run(cmd)


def version():
    """
    Get Java version information.

    :return: tuple of (java_version, javac_version)
    :raises Failure: if Java is not installed

    Example usage::

        java_ver, javac_ver = java.version()
        print(f"Java: {java_ver}, Javac: {javac_ver}")
    """
    _check_java_installed()

    # Get java version (java -version outputs to stderr)
    import subprocess
    try:
        result = subprocess.run([JAVA, "-version"], capture_output=True, text=True)
        java_version = result.stderr.splitlines()[0] if result.stderr else "unknown"
    except Exception:
        java_version = "unknown"

    # Get javac version
    try:
        result = subprocess.run([JAVAC, "-version"], capture_output=True, text=True)
        javac_version = result.stdout.strip() or result.stderr.strip() or "unknown"
    except Exception:
        javac_version = "unknown"

    return java_version, javac_version


def clean(*patterns):
    """
    Remove compiled .class files.

    :param patterns: file patterns to clean (default: all .class files in current directory)

    Example usage::

        java.clean()  # Remove all .class files
        java.clean("*.class", "bin/*.class")  # Remove specific patterns
    """
    if not patterns:
        patterns = ["*.class"]

    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                log(_("removing {}...").format(path))
                path.unlink()
