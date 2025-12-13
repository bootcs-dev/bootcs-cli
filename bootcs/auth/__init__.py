"""
BootCS Authentication Module

Provides authentication functionality for bootcs CLI.
"""

from .credentials import (
    get_token,
    save_token,
    clear_token,
    get_user,
    save_user,
    is_logged_in,
    get_credentials_path,
)

from .device_flow import (
    start_device_flow,
    poll_for_token,
    DeviceFlowError,
)

__all__ = [
    "get_token",
    "save_token", 
    "clear_token",
    "get_user",
    "save_user",
    "is_logged_in",
    "get_credentials_path",
    "start_device_flow",
    "poll_for_token",
    "DeviceFlowError",
]
