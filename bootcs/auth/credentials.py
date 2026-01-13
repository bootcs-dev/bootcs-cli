"""
Credentials management for bootcs CLI.

Stores credentials in ~/.bootcs/credentials.yaml
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def get_credentials_path() -> Path:
    """Get the path to the credentials file."""
    # Support XDG_CONFIG_HOME
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        base_dir = Path(config_home) / "bootcs"
    else:
        base_dir = Path.home() / ".bootcs"

    return base_dir / "credentials.yaml"


def _load_credentials() -> Dict[str, Any]:
    """Load credentials from file."""
    path = get_credentials_path()
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save_credentials(data: Dict[str, Any]) -> None:
    """Save credentials to file."""
    path = get_credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Set restrictive permissions
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)

    # Chmod 600 for security
    os.chmod(path, 0o600)


def get_token() -> Optional[str]:
    """Get the stored authentication token."""
    creds = _load_credentials()
    return creds.get("token")


def save_token(token: str) -> None:
    """Save the authentication token."""
    creds = _load_credentials()
    creds["token"] = token
    _save_credentials(creds)


def clear_token() -> None:
    """Clear the stored token."""
    creds = _load_credentials()
    creds.pop("token", None)
    creds.pop("user", None)
    _save_credentials(creds)


def get_user() -> Optional[Dict[str, Any]]:
    """Get the stored user information."""
    creds = _load_credentials()
    return creds.get("user")


def save_user(user: Dict[str, Any]) -> None:
    """Save user information."""
    creds = _load_credentials()
    creds["user"] = user
    _save_credentials(creds)


def is_logged_in() -> bool:
    """Check if user is logged in."""
    return get_token() is not None
