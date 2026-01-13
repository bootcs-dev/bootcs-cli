"""
BootCS CLI - Main entry point

Usage:
    bootcs check <slug>
    bootcs submit <slug>
"""

import argparse
import enum
import json
import logging
import os
import sys
import time
from pathlib import Path

import termcolor

from . import __version__, lib50
from .check import internal
from .check.runner import CheckRunner

LOGGER = logging.getLogger(__name__)


class LogLevel(enum.IntEnum):
    """Log levels aligned with check50."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


class ColoredFormatter(logging.Formatter):
    """Colored log formatter aligned with check50."""

    COLORS = {
        "ERROR": "red",
        "WARNING": "yellow",
        "DEBUG": "cyan",
        "INFO": "magenta",
    }

    def __init__(self, fmt, use_color=True):
        super().__init__(fmt=fmt)
        self.use_color = use_color

    def format(self, record):
        msg = super().format(record)
        return (
            msg
            if not self.use_color
            else termcolor.colored(msg, getattr(record, "color", self.COLORS.get(record.levelname)))
        )


def setup_logging(level):
    """
    Setup logging system aligned with check50.

    Args:
        level: Log level string (debug, info, warning, error)
    """
    for logger in (logging.getLogger("lib50"), LOGGER):
        logger.setLevel(level.upper())
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            ColoredFormatter("(%(levelname)s) %(message)s", use_color=sys.stderr.isatty())
        )
        logger.addHandler(handler)


def main():
    """Main entry point for bootcs CLI."""
    parser = argparse.ArgumentParser(
        prog="bootcs", description="BootCS CLI - Check and submit your code"
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check your code against tests")
    check_parser.add_argument("slug", help="The check slug (e.g., cs50/mario-less)")
    check_parser.add_argument(
        "-o",
        "--output",
        choices=["ansi", "json"],
        default="ansi",
        help="Output format (default: ansi)",
    )
    check_parser.add_argument(
        "--log", action="store_true", help="Show detailed log (deprecated, use --log-level info)"
    )
    check_parser.add_argument(
        "--log-level",
        action="store",
        choices=[level.name.lower() for level in LogLevel],
        type=str.lower,
        help="warning: displays usage warnings.\n"
        "info: adds all commands run and log messages.\n"
        "debug: adds output of all commands run.",
    )
    check_parser.add_argument(
        "--target", action="append", metavar="check", help="Run only the specified check(s)"
    )
    check_parser.add_argument(
        "-L", "--language", help="Language for checks (auto-detected from files if not specified)"
    )
    check_parser.add_argument(
        "-u", "--update", action="store_true", help="Force update checks from remote"
    )
    check_parser.add_argument(
        "-d",
        "--dev",
        metavar="PATH",
        help="Development mode: PATH is interpreted as a literal path to checks directory",
    )

    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit your code")
    submit_parser.add_argument("slug", help="The submission slug (e.g., cs50/hello)")
    submit_parser.add_argument("-m", "--message", help="Commit message")
    submit_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    submit_parser.add_argument(
        "-L", "--language", help="Language of submission (auto-detected if not specified)"
    )
    submit_parser.add_argument(
        "-d",
        "--dev",
        metavar="PATH",
        help="Development mode: PATH is literal path to checks directory (for file list)",
    )
    submit_parser.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Don't wait for evaluation result (return immediately)",
    )
    submit_parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds to wait for evaluation (default: 60)",
    )

    # Auth commands
    subparsers.add_parser("login", help="Log in with GitHub")
    subparsers.add_parser("logout", help="Log out")
    subparsers.add_parser("whoami", help="Show logged in user")

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage checks cache")
    cache_parser.add_argument("action", choices=["clear", "list"], help="Action to perform")
    cache_parser.add_argument(
        "slug", nargs="?", help="Specific course or course/stage slug (optional)"
    )
    cache_parser.add_argument("-L", "--language", help="Specific language (optional)")

    args = parser.parse_args()

    if args.command == "check":
        return run_check(args)
    elif args.command == "submit":
        return run_submit(args)
    elif args.command == "login":
        return run_login(args)
    elif args.command == "logout":
        return run_logout(args)
    elif args.command == "whoami":
        return run_whoami(args)
    elif args.command == "cache":
        return run_cache(args)
    else:
        parser.print_help()
        return 1


# Language extension mapping
LANGUAGE_EXTENSIONS = {
    ".c": "c",
    ".h": "c",
    ".py": "python",
    ".java": "java",
    ".sql": "sql",
}

# Supported languages for slug parsing
SUPPORTED_LANGUAGES = {"c", "python", "java", "sql"}


def parse_slug(slug: str):
    """
    Parse a slug into course and stage components.

    MVP: Only supports 2-part format "cs50/hello"
    Language is determined separately via CLI flag or auto-detection.

    Returns:
        tuple: (course_slug, stage_slug)
    """
    parts = slug.split("/")
    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        # Single part, treat as stage only
        return None, parts[0]
    else:
        # Multi-part, treat first as course, last as stage
        return parts[0], "/".join(parts[1:])


def detect_language(directory: Path = None, explicit: str = None) -> str:
    """
    Detect programming language from files in directory.

    Priority:
    1. Explicit parameter (user specified -L)
    2. Files in current directory
    3. Default to 'c'

    Args:
        directory: Directory to scan for files (defaults to cwd)
        explicit: Explicitly specified language (highest priority)

    Returns:
        Detected language string (e.g., 'c', 'python')
    """
    # 1. User explicitly specified
    if explicit:
        return explicit

    # 2. Detect from files in directory
    if directory is None:
        directory = Path.cwd()

    # Count files by language
    lang_counts = {}
    try:
        for item in directory.iterdir():
            if item.is_file() and not item.name.startswith("."):
                ext = item.suffix.lower()
                if ext in LANGUAGE_EXTENSIONS:
                    lang = LANGUAGE_EXTENSIONS[ext]
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
    except OSError:
        pass

    # Return the most common language
    if lang_counts:
        return max(lang_counts, key=lang_counts.get)

    # 3. Default
    return "c"


def run_check(args):
    """Run the check command."""
    slug = args.slug
    force_update = getattr(args, "update", False)

    # Dev mode implies log level "info" if not overwritten (like check50)
    if args.dev:
        if not args.log_level:
            args.log_level = "info"

    # Setup logging
    if not args.log_level:
        args.log_level = "warning"
    setup_logging(args.log_level)

    # Legacy --log flag support
    if args.log and not args.log_level:
        args.log_level = "info"
        setup_logging(args.log_level)

    # Parse slug (MVP: only 2-part format)
    course_slug, stage_slug = parse_slug(slug)

    # Determine language via explicit flag or auto-detection
    explicit_lang = getattr(args, "language", None)
    language = detect_language(directory=Path.cwd(), explicit=explicit_lang)

    # Determine check directory
    if args.dev:
        # Development mode: combine dev path with slug (e.g., /path/to/checks + cs50/hello)
        check_dir = Path(args.dev).resolve() / slug
    else:
        # Try remote download first, then fall back to local search
        check_dir = find_check_dir(slug, language=language, force_update=force_update)

    if not check_dir or not check_dir.exists():
        termcolor.cprint(f"Error: Could not find checks for '{slug}'", "red", file=sys.stderr)
        termcolor.cprint(
            "Use --dev to specify a checks directory for development.", "yellow", file=sys.stderr
        )
        return 1

    # Debug info in dev mode
    if args.dev:
        LOGGER.info("Dev mode enabled")
        LOGGER.info(f"Check directory: {check_dir}")
        LOGGER.info(f"Language: {language}")

    # Set internal state
    internal.check_dir = check_dir
    internal.slug = slug

    # Load config
    try:
        config = internal.load_config(check_dir)
    except lib50.Error as e:
        termcolor.cprint(f"Error: {e}", "red", file=sys.stderr)
        return 1

    checks_file = check_dir / config["checks"]
    if not checks_file.exists():
        termcolor.cprint(
            f"Error: Checks file '{config['checks']}' not found in {check_dir}",
            "red",
            file=sys.stderr,
        )
        return 1

    # Dev mode: show config details
    if args.dev:
        LOGGER.info(f"Config file: {config.get('checks', '__init__.py')}")
        LOGGER.info(f"Files pattern: {config.get('files', [])}")

    # Get list of files to include
    cwd = Path.cwd()
    try:
        included, excluded = lib50.files(config.get("files", []), root=cwd)
    except lib50.Error as e:
        termcolor.cprint(f"Error: {e}", "red", file=sys.stderr)
        return 1

    if not included:
        termcolor.cprint("Warning: No files found to check", "yellow", file=sys.stderr)

    # Print header (skip in JSON mode for clean output)
    if args.output != "json":
        print()
        lang_indicator = f" ({language})" if language != "c" else ""
        termcolor.cprint(f"🔍 Running checks for {slug}{lang_indicator}...", "cyan", attrs=["bold"])
        print()

    # Run checks
    targets = args.target if hasattr(args, "target") and args.target else None

    try:
        with CheckRunner(checks_file, list(included), language=language) as runner:
            results = runner.run(targets=targets)
    except Exception as e:
        termcolor.cprint(f"Error running checks: {e}", "red", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1

    # Output results
    if args.output == "json":
        output_json(results, args.log)
    else:
        output_ansi(results, args.log)

    # Return 0 if all checks passed, 1 otherwise
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    if passed == total:
        return 0
    else:
        return 1


def output_ansi(results, show_log=False):
    """Output results in ANSI format (colored terminal output)."""
    for result in results:
        if result.passed is True:
            emoji = "✅"
            color = "green"
        elif result.passed is False:
            emoji = "❌"
            color = "red"
        else:
            emoji = "⏭️"
            color = "yellow"

        termcolor.cprint(f"{emoji} {result.description}", color)

        # Show cause for failed checks (passed=False)
        if result.cause and result.passed is False:
            rationale = result.cause.get("rationale", "")
            if rationale:
                print(f"   └─ {rationale}")
            help_msg = result.cause.get("help")
            if help_msg:
                termcolor.cprint(f"   💡 {help_msg}", "cyan")

        # In dev mode or with --log, also show error info for skipped checks (passed=None)
        if result.cause and result.passed is None and show_log:
            error_info = result.cause.get("error")
            if error_info:
                error_type = error_info.get("type", "Error")
                error_value = error_info.get("value", "")
                termcolor.cprint(f"   ⚠️  {error_type}: {error_value}", "yellow")
            else:
                rationale = result.cause.get("rationale", "")
                if rationale and rationale != "can't check until a frown turns upside down":
                    termcolor.cprint(f"   ⚠️  {rationale}", "yellow")

        if show_log and result.log:
            print("   Log:")
            for line in result.log:
                print(f"      {line}")

    print()

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if r.passed is False)
    skipped = sum(1 for r in results if r.passed is None)

    summary = f"Results: {passed} passed"
    if failed:
        summary += f", {failed} failed"
    if skipped:
        summary += f", {skipped} skipped"

    if failed == 0:
        termcolor.cprint(f"🎉 {summary}", "green", attrs=["bold"])
    else:
        termcolor.cprint(summary, "yellow")


def output_json(results, show_log=False):
    """Output results in JSON format."""
    output = {"slug": internal.slug, "version": __version__, "results": []}

    for result in results:
        r = {
            "name": result.name,
            "description": result.description,
            "passed": result.passed,
        }
        if result.cause:
            r["cause"] = result.cause
        if show_log:
            r["log"] = result.log
        if result.data:
            r["data"] = result.data
        if result.dependency:
            r["dependency"] = result.dependency
        output["results"].append(r)

    print(json.dumps(output, indent=2))


def find_check_dir(slug, language: str = "c", force_update: bool = False):
    """
    Find the check directory for a given slug.

    MVP: Only supports 2-part format "cs50/hello"
    Language is determined separately and not part of the path.

    Priority:
    1. BOOTCS_CHECKS_PATH environment variable (for evaluator)
    2. Remote API download (with local cache)
    3. Local directories (for development)
    """
    # Parse slug (MVP: only 2-part format)
    course_slug, stage_name = parse_slug(slug)

    # 1. Check environment variable first (used by evaluator)
    if "BOOTCS_CHECKS_PATH" in os.environ:
        checks_path = Path(os.environ["BOOTCS_CHECKS_PATH"])
        # Try with course/stage structure (e.g., checks/cs50/hello)
        if course_slug:
            path = checks_path / course_slug / stage_name
            if path.exists():
                return path
        # Fallback: try with full slug
        if course_slug:
            path = checks_path / slug
            if path.exists():
                return path
        # Try stage name only
        path = checks_path / stage_name
        if path.exists():
            return path

    # 2. Try remote download (if slug has course/stage format)
    if course_slug:
        try:
            from .api.checks import get_checks_manager

            manager = get_checks_manager()
            # API expects 2-part slug (course/stage), convert if needed
            api_slug = f"{course_slug}/{stage_name}"
            check_path = manager.get_checks(api_slug, language=language, force_update=force_update)
            if check_path.exists():
                return check_path
        except Exception as e:
            # Log error but continue to local fallback
            import sys

            print(f"Warning: Could not download checks: {e}", file=sys.stderr)

    # 3. Local directories fallback (for development)
    search_paths = [
        Path.cwd() / "checks" / slug,
        Path.cwd() / "checks" / stage_name,
        Path.cwd().parent / "checks" / slug,
        Path.cwd().parent / "checks" / stage_name,
        Path.home() / ".local" / "share" / "bootcs" / slug,
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


# Spinner characters for polling animation
SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def wait_for_result(submission_id: str, token: str, timeout: int = 60):
    """
    Poll for submission evaluation result.

    Args:
        submission_id: The submission ID to poll.
        token: Authentication token.
        timeout: Maximum time to wait in seconds.

    Returns:
        Submission result dict, or None if timeout.
    """
    from .api.client import APIClient, APIError

    client = APIClient(token=token)
    start_time = time.time()
    poll_count = 0

    while True:
        elapsed = time.time() - start_time

        # Timeout check
        if elapsed > timeout:
            return None

        # Show spinner
        spinner_char = SPINNER[poll_count % len(SPINNER)]
        elapsed_int = int(elapsed)
        sys.stdout.write(f"\r⏳ Evaluating... {spinner_char} ({elapsed_int}s)  ")
        sys.stdout.flush()

        try:
            result = client.get(f"/api/submissions/{submission_id}")
            status = result.get("status")

            # Terminal states
            if status in ["SUCCESS", "FAILURE", "ERROR", "TIMEOUT"]:
                sys.stdout.write("\r" + " " * 40 + "\r")  # Clear line
                sys.stdout.flush()
                return result
        except APIError:
            pass  # Continue polling on error

        poll_count += 1
        # First 5 polls: 1s interval (fast feedback)
        # After that: 2s interval (reduce load)
        interval = 1 if poll_count <= 5 else 2
        time.sleep(interval)


def display_result(result: dict):
    """
    Display evaluation result.

    Args:
        result: Submission result dict from API.
    """
    status = result.get("status")
    eval_result = result.get("result", {})
    test_results = eval_result.get("results", [])
    passed = sum(1 for r in test_results if r.get("passed"))
    total = len(test_results)

    print()
    if status == "SUCCESS":
        termcolor.cprint("🎉 Evaluation Complete!", "green", attrs=["bold"])
        print()
        termcolor.cprint("   Status:  SUCCESS", "green")
    elif status == "FAILURE":
        termcolor.cprint("❌ Some tests failed", "red", attrs=["bold"])
        print()
        termcolor.cprint("   Status:  FAILURE", "red")
    elif status == "ERROR":
        termcolor.cprint("⚠️  Evaluation error", "yellow", attrs=["bold"])
        print()
        termcolor.cprint("   Status:  ERROR", "yellow")
    elif status == "TIMEOUT":
        termcolor.cprint("⏰ Evaluation timeout", "yellow", attrs=["bold"])
        print()
        termcolor.cprint("   Status:  TIMEOUT", "yellow")

    if total > 0:
        color = "green" if passed == total else "red"
        termcolor.cprint(f"   Passed:  {passed}/{total}", color)

    # Show individual test results
    if test_results:
        print()
        for r in test_results:
            name = r.get("name", "unknown")
            is_passed = r.get("passed", False)
            description = r.get("description", "")

            if is_passed:
                icon = termcolor.colored("✅", "green")
            else:
                icon = termcolor.colored("❌", "red")

            if description:
                print(f"   {icon} {name} - {description}")
            else:
                print(f"   {icon} {name}")
    print()


def run_submit(args):
    """Run the submit command."""
    from .api import APIError
    from .api.submit import collect_files, submit_files
    from .auth import get_token, is_logged_in

    slug = args.slug

    # Parse slug (MVP: only 2-part format)
    course_slug, stage_slug = parse_slug(slug)

    # Determine language via explicit flag or auto-detection
    explicit_lang = getattr(args, "language", None)
    language = detect_language(directory=Path.cwd(), explicit=explicit_lang)

    # Check if logged in
    if not is_logged_in():
        termcolor.cprint("❌ Not logged in.", "red")
        print("Use 'bootcs login' to log in with GitHub first.")
        return 1

    token = get_token()

    # Determine check directory for file list
    if args.dev:
        check_dir = Path(args.dev).resolve()
    else:
        check_dir = find_check_dir(slug, language=language)

    if not check_dir or not check_dir.exists():
        termcolor.cprint(f"Error: Could not find config for '{slug}'", "red", file=sys.stderr)
        termcolor.cprint(
            "Use --dev to specify the checks directory for development.", "yellow", file=sys.stderr
        )
        return 1

    # Load config to get file list
    try:
        config = internal.load_config(check_dir)
    except lib50.Error as e:
        termcolor.cprint(f"Error: {e}", "red", file=sys.stderr)
        return 1

    # Get list of files to include
    cwd = Path.cwd()
    try:
        included, excluded = lib50.files(config.get("files", []), root=cwd)
    except lib50.Error as e:
        termcolor.cprint(f"Error: {e}", "red", file=sys.stderr)
        return 1

    if not included:
        termcolor.cprint("❌ No files found to submit.", "red")
        return 1

    file_list = sorted(included)

    # Show files to submit
    print()
    lang_indicator = f" ({language})" if language != "c" else ""
    termcolor.cprint(f"📦 Submitting {slug}{lang_indicator}", "cyan", attrs=["bold"])
    print()
    termcolor.cprint("Files to submit:", "white")
    for f in file_list:
        print(f"  • {f}")
    print()

    # Confirm unless -y flag
    if not args.yes:
        try:
            confirm = input("Submit these files? [Y/n] ").strip().lower()
            if confirm and confirm not in ("y", "yes"):
                termcolor.cprint("Submission cancelled.", "yellow")
                return 0
        except KeyboardInterrupt:
            print()
            termcolor.cprint("Submission cancelled.", "yellow")
            return 0

    # Collect and encode files
    try:
        files = collect_files(file_list, root=cwd)
    except ValueError as e:
        termcolor.cprint(f"❌ Error: {e}", "red")
        return 1

    # Submit
    print("Submitting...", end="", flush=True)
    try:
        result = submit_files(
            slug=slug,
            files=files,
            token=token,
            message=args.message,
            language=language,  # Pass language if specified
        )
        print()
        print()

        if result.status == "ERROR":
            termcolor.cprint(
                f"⚠️  {result.message or 'Submission saved but evaluation failed'}", "yellow"
            )
        else:
            termcolor.cprint("✅ Submitted successfully!", "green", attrs=["bold"])

        print(f"   Submission ID: {result.submission_id}")
        print(f"   Short Hash:    {result.short_hash}")

        # If async mode or not evaluating, just show status and return
        if args.async_mode or result.status != "EVALUATING":
            print(f"   Status:        {result.status}")
            if result.status == "EVALUATING":
                print()
                termcolor.cprint("💡 Your code is being evaluated. Check results at:", "cyan")
                print(f"   https://bootcs.dev/submissions/{result.submission_id}")
            return 0

        # Wait for evaluation result (polling mode)
        print()
        eval_result = wait_for_result(result.submission_id, token, timeout=args.timeout)

        if eval_result is None:
            # Timeout
            print()
            termcolor.cprint(
                f"⏰ Evaluation taking longer than expected ({args.timeout}s)", "yellow"
            )
            print()
            print("   Your submission is still being processed.")
            termcolor.cprint("   Check results at:", "cyan")
            print(f"   https://bootcs.dev/submissions/{result.submission_id}")
            print()
            termcolor.cprint(
                f"   Or wait longer with: bootcs submit {slug} --timeout {args.timeout * 2}",
                "white",
            )
            return 0

        # Display final result
        display_result(eval_result)

        # Return exit code based on result
        if eval_result.get("status") == "SUCCESS":
            return 0
        else:
            return 1

    except APIError as e:
        print()
        termcolor.cprint(f"❌ Submission failed: {e.message}", "red")
        if e.code == "UNAUTHORIZED":
            print("Try 'bootcs logout' then 'bootcs login' to refresh your session.")
        return 1
    except Exception as e:
        print()
        termcolor.cprint(f"❌ Unexpected error: {e}", "red")
        return 1


def run_login(args):
    """Run the login command."""
    from .auth import (
        DeviceFlowError,
        get_user,
        is_logged_in,
        poll_for_token,
        save_token,
        save_user,
        start_device_flow,
    )

    # Check if already logged in
    if is_logged_in():
        user = get_user()
        if user:
            termcolor.cprint(f"Already logged in as {user.get('username', 'unknown')}", "yellow")
            print("Use 'bootcs logout' to log out first.")
            return 0

    print()
    termcolor.cprint("🔐 Logging in with GitHub...", "cyan", attrs=["bold"])
    print()

    try:
        # Start device flow
        device_info = start_device_flow()

        # Show user code and verification URL
        termcolor.cprint("Please visit:", "white")
        termcolor.cprint(f"  {device_info.verification_uri}", "cyan", attrs=["underline"])
        print()
        termcolor.cprint("And enter this code:", "white")
        termcolor.cprint(f"  {device_info.user_code}", "green", attrs=["bold"])
        print()
        print("Waiting for authorization...", end="", flush=True)

        # Poll for token
        token_response = poll_for_token(
            device_info.device_code, interval=device_info.interval, timeout=device_info.expires_in
        )

        print()  # New line after waiting

        # Save credentials
        save_token(token_response.token)
        save_user(token_response.user)

        username = token_response.user.get("username", "unknown")
        print()
        termcolor.cprint(f"✅ Successfully logged in as {username}!", "green", attrs=["bold"])
        return 0

    except DeviceFlowError as e:
        print()  # New line if we were waiting
        termcolor.cprint(f"❌ Login failed: {e.message}", "red")
        return 1
    except KeyboardInterrupt:
        print()
        termcolor.cprint("Login cancelled.", "yellow")
        return 1


def run_logout(args):
    """Run the logout command."""
    from .auth import clear_token, get_user, is_logged_in

    if not is_logged_in():
        termcolor.cprint("Not logged in.", "yellow")
        return 0

    user = get_user()
    username = user.get("username", "unknown") if user else "unknown"

    clear_token()
    termcolor.cprint(f"✅ Logged out from {username}", "green")
    return 0


def run_whoami(args):
    """Run the whoami command."""
    from .auth import get_user, is_logged_in

    if not is_logged_in():
        termcolor.cprint("Not logged in.", "yellow")
        print("Use 'bootcs login' to log in with GitHub.")
        return 1

    user = get_user()
    if user:
        print()
        termcolor.cprint("👤 Logged in as:", "cyan")
        print(f"   Username: {user.get('username', 'unknown')}")
        if user.get("id"):
            print(f"   User ID:  {user.get('id')}")
        if user.get("githubId"):
            print(f"   GitHub ID: {user.get('githubId')}")
        print()
    else:
        print("Logged in (no user info available)")

    return 0


def run_cache(args):
    """Run the cache command."""
    from .api.checks import get_checks_manager

    action = args.action
    slug = getattr(args, "slug", None)
    language = getattr(args, "language", None)

    manager = get_checks_manager()

    if action == "list":
        # List cached checks
        cached = manager.list_cache()

        if not cached:
            termcolor.cprint("No cached checks.", "yellow")
            return 0

        print()
        termcolor.cprint("📦 Cached Checks:", "cyan", attrs=["bold"])
        print()
        print(f"  {'Course':<10} {'Stage':<20} {'Version':<10} {'Age':<6}")
        print(f"  {'-' * 10} {'-' * 20} {'-' * 10} {'-' * 6}")

        for item in cached:
            print(
                f"  {item['course']:<10} {item['stage']:<20} {item['version']:<10} {item['age']:<6}"
            )

        print()
        print(f"  Total: {len(cached)} cached checks (language-agnostic)")
        print(f"  Location: {manager.cache_dir}")
        print()
        return 0

    elif action == "clear":
        # Clear cache
        try:
            manager.clear_cache(slug=slug, language=language)

            if slug:
                termcolor.cprint(f"✅ Cleared cache for '{slug}'", "green")
            else:
                termcolor.cprint("✅ Cleared all cached checks", "green")

            return 0
        except ValueError as e:
            termcolor.cprint(f"❌ Error: {e}", "red")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
