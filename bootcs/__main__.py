"""
BootCS CLI - Main entry point

Usage:
    bootcs check <slug>
    bootcs submit <slug>
"""

import argparse
import json
import os
import sys
from pathlib import Path

import termcolor

from . import __version__
from .check import internal
from .check.runner import CheckRunner
from . import lib50


def main():
    """Main entry point for bootcs CLI."""
    parser = argparse.ArgumentParser(
        prog="bootcs",
        description="BootCS CLI - Check and submit your code"
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check your code against tests")
    check_parser.add_argument("slug", help="The check slug (e.g., cs50/mario-less)")
    check_parser.add_argument("-o", "--output", choices=["ansi", "json"], default="ansi",
                              help="Output format (default: ansi)")
    check_parser.add_argument("--log", action="store_true", help="Show detailed log")
    check_parser.add_argument("--target", action="append", metavar="check",
                              help="Run only the specified check(s)")
    check_parser.add_argument("-L", "--language",
                              help="Language for checks (auto-detected from files if not specified)")
    check_parser.add_argument("-u", "--update", action="store_true",
                              help="Force update checks from remote")
    check_parser.add_argument("--local", metavar="PATH", help="Path to local checks directory")
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit your code")
    submit_parser.add_argument("slug", help="The submission slug (e.g., cs50/hello)")
    submit_parser.add_argument("-m", "--message", help="Commit message")
    submit_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    submit_parser.add_argument("-L", "--language", help="Language of submission (auto-detected if not specified)")
    submit_parser.add_argument("--local", metavar="PATH", help="Path to local checks directory (for file list)")
    
    # Auth commands
    subparsers.add_parser("login", help="Log in with GitHub")
    subparsers.add_parser("logout", help="Log out")
    subparsers.add_parser("whoami", help="Show logged in user")
    
    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage checks cache")
    cache_parser.add_argument("action", choices=["clear", "list"],
                              help="Action to perform")
    cache_parser.add_argument("slug", nargs="?",
                              help="Specific course or course/stage slug (optional)")
    cache_parser.add_argument("-L", "--language",
                              help="Specific language (optional)")
    
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
    '.c': 'c',
    '.h': 'c',
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.ts': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
}


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
            if item.is_file() and not item.name.startswith('.'):
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
    return 'c'


def run_check(args):
    """Run the check command."""
    slug = args.slug
    force_update = getattr(args, 'update', False)
    
    # Auto-detect language from files in current directory
    explicit_lang = getattr(args, 'language', None)
    language = detect_language(directory=Path.cwd(), explicit=explicit_lang)
    
    # Determine check directory
    if args.local:
        check_dir = Path(args.local).resolve()
    else:
        # Try remote download first, then fall back to local search
        check_dir = find_check_dir(slug, language=language, force_update=force_update)
    
    if not check_dir or not check_dir.exists():
        termcolor.cprint(f"Error: Could not find checks for '{slug}'", "red", file=sys.stderr)
        termcolor.cprint("Use --local to specify a local checks directory.", "yellow", file=sys.stderr)
        return 1
    
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
        termcolor.cprint(f"Error: Checks file '{config['checks']}' not found in {check_dir}", "red", file=sys.stderr)
        return 1
    
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
        lang_indicator = f" ({language})" if language != 'c' else ""
        termcolor.cprint(f"🔍 Running checks for {slug}{lang_indicator}...", "cyan", attrs=["bold"])
        print()
    
    # Run checks
    targets = args.target if hasattr(args, 'target') and args.target else None
    
    try:
        with CheckRunner(checks_file, list(included)) as runner:
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
        
        if result.cause and result.passed is False:
            rationale = result.cause.get("rationale", "")
            if rationale:
                print(f"   └─ {rationale}")
            help_msg = result.cause.get("help")
            if help_msg:
                termcolor.cprint(f"   💡 {help_msg}", "cyan")
        
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
    output = {
        "slug": internal.slug,
        "version": __version__,
        "results": []
    }
    
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
    
    Priority:
    1. BOOTCS_CHECKS_PATH environment variable (for evaluator)
    2. Remote API download (with local cache)
    3. Local directories (for development)
    """
    # Extract parts from slug (e.g., "cs50/credit" -> course="cs50", stage="credit")
    parts = slug.split("/")
    if len(parts) == 2:
        course_slug, stage_name = parts
    else:
        stage_name = slug
        course_slug = None
    
    # 1. Check environment variable first (used by evaluator)
    if "BOOTCS_CHECKS_PATH" in os.environ:
        checks_path = Path(os.environ["BOOTCS_CHECKS_PATH"])
        # Try with language/stage structure (e.g., checks/c/hello)
        path = checks_path / language / stage_name
        if path.exists():
            return path
        # Try with full slug under language
        if course_slug:
            path = checks_path / language / slug
            if path.exists():
                return path
        # Fallback: try without language prefix
        path = checks_path / stage_name
        if path.exists():
            return path
        if course_slug:
            path = checks_path / slug
            if path.exists():
                return path
    
    # 2. Try remote download (if slug has course/stage format)
    if course_slug and "/" in slug:
        try:
            from .api.checks import get_checks_manager
            manager = get_checks_manager()
            check_path = manager.get_checks(slug, language=language, force_update=force_update)
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


def run_submit(args):
    """Run the submit command."""
    from .auth import is_logged_in, get_token
    from .api import APIError
    from .api.submit import collect_files, submit_files, SubmitFile
    
    slug = args.slug
    
    # Auto-detect language from files in current directory
    explicit_lang = getattr(args, 'language', None)
    language = detect_language(directory=Path.cwd(), explicit=explicit_lang)
    
    # Check if logged in
    if not is_logged_in():
        termcolor.cprint("❌ Not logged in.", "red")
        print("Use 'bootcs login' to log in with GitHub first.")
        return 1
    
    token = get_token()
    
    # Determine check directory for file list
    if args.local:
        check_dir = Path(args.local).resolve()
    else:
        check_dir = find_check_dir(slug, language=language)
    
    if not check_dir or not check_dir.exists():
        termcolor.cprint(f"Error: Could not find config for '{slug}'", "red", file=sys.stderr)
        termcolor.cprint("Use --local to specify the checks directory.", "yellow", file=sys.stderr)
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
    lang_indicator = f" ({language})" if language != 'c' else ""
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
            termcolor.cprint(f"⚠️  {result.message or 'Submission saved but evaluation failed'}", "yellow")
        else:
            termcolor.cprint("✅ Submitted successfully!", "green", attrs=["bold"])
        
        print(f"   Submission ID: {result.submission_id}")
        print(f"   Short Hash:    {result.short_hash}")
        print(f"   Status:        {result.status}")
        
        if result.status == "EVALUATING":
            print()
            termcolor.cprint("💡 Your code is being evaluated. Check results at:", "cyan")
            print(f"   https://bootcs.dev/submissions/{result.submission_id}")
        
        return 0
        
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
        is_logged_in,
        get_user,
        save_token,
        save_user,
        start_device_flow,
        poll_for_token,
        DeviceFlowError,
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
            device_info.device_code,
            interval=device_info.interval,
            timeout=device_info.expires_in
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
    from .auth import is_logged_in, get_user, clear_token
    
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
    from .auth import is_logged_in, get_user
    
    if not is_logged_in():
        termcolor.cprint("Not logged in.", "yellow")
        print("Use 'bootcs login' to log in with GitHub.")
        return 1
    
    user = get_user()
    if user:
        print()
        termcolor.cprint("👤 Logged in as:", "cyan")
        print(f"   Username: {user.get('username', 'unknown')}")
        if user.get('id'):
            print(f"   User ID:  {user.get('id')}")
        if user.get('githubId'):
            print(f"   GitHub ID: {user.get('githubId')}")
        print()
    else:
        print("Logged in (no user info available)")
    
    return 0


def run_cache(args):
    """Run the cache command."""
    from .api.checks import get_checks_manager
    
    action = args.action
    slug = getattr(args, 'slug', None)
    language = getattr(args, 'language', None)
    
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
        print(f"  {'Course':<10} {'Language':<10} {'Stage':<15} {'Version':<10} {'Age':<6}")
        print(f"  {'-'*10} {'-'*10} {'-'*15} {'-'*10} {'-'*6}")
        
        for item in cached:
            print(f"  {item['course']:<10} {item['language']:<10} {item['stage']:<15} {item['version']:<10} {item['age']:<6}")
        
        print()
        print(f"  Total: {len(cached)} cached checks")
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
