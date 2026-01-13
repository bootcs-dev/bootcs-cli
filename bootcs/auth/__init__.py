"""
BootCS Authentication Module

Provides authentication functionality for bootcs CLI.
"""

from .credentials import (
    clear_token,
    get_credentials_path,
    get_token,
    get_user,
    is_logged_in,
    save_token,
    save_user,
)
from .device_flow import (
    DeviceFlowError,
    poll_for_token,
    start_device_flow,
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
