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
    check_parser.add_argument("slug", help="The check slug (e.g., course-cs50/mario-less)")
    check_parser.add_argument("-o", "--output", choices=["ansi", "json"], default="ansi",
                              help="Output format (default: ansi)")
    check_parser.add_argument("--log", action="store_true", help="Show detailed log")
    check_parser.add_argument("--target", action="append", metavar="check",
                              help="Run only the specified check(s)")
    check_parser.add_argument("--local", metavar="PATH", help="Path to local checks directory")
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit your code")
    submit_parser.add_argument("slug", help="The submission slug")
    
    # Auth commands
    subparsers.add_parser("login", help="Log in with GitHub")
    subparsers.add_parser("logout", help="Log out")
    subparsers.add_parser("whoami", help="Show logged in user")
    
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
    else:
        parser.print_help()
        return 1


def run_check(args):
    """Run the check command."""
    slug = args.slug
    
    # Determine check directory
    if args.local:
        check_dir = Path(args.local).resolve()
    else:
        # For now, look for checks in a local directory structure
        # Future: download from remote like check50 does
        check_dir = find_check_dir(slug)
    
    if not check_dir or not check_dir.exists():
        termcolor.cprint(f"Error: Could not find checks for '{slug}'", "red", file=sys.stderr)
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
    
    # Print header
    print()
    termcolor.cprint(f"🔍 Running checks for {slug}...", "cyan", attrs=["bold"])
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


def find_check_dir(slug):
    """Find the check directory for a given slug."""
    # Common locations to search
    search_paths = [
        Path.cwd() / "checks" / slug,
        Path.cwd().parent / "checks" / slug,
        Path.home() / ".local" / "share" / "bootcs" / slug,
    ]
    
    # Also check environment variable
    if "BOOTCS_CHECKS_PATH" in os.environ:
        search_paths.insert(0, Path(os.environ["BOOTCS_CHECKS_PATH"]) / slug)
    
    for path in search_paths:
        if path.exists():
            return path
    
    return None


def run_submit(args):
    """Run the submit command."""
    termcolor.cprint("Submit command not yet implemented", "yellow")
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


if __name__ == "__main__":
    sys.exit(main())
