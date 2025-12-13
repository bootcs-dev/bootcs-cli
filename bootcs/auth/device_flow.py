"""
GitHub Device Flow implementation for bootcs CLI.

Device Flow allows CLI authentication without browser redirect.
See: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow
"""

import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

import requests


class DeviceFlowError(Exception):
    """Exception raised during device flow authentication."""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class DeviceCodeResponse:
    """Response from device code request."""
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@dataclass  
class TokenResponse:
    """Response from successful token request."""
    token: str
    user: Dict[str, Any]


# Default API base URL - can be overridden via environment
DEFAULT_API_BASE = "https://bootcs-api.vercel.app"


def get_api_base() -> str:
    """Get the API base URL from environment or default."""
    import os
    return os.environ.get("BOOTCS_API_URL", DEFAULT_API_BASE)


def start_device_flow() -> DeviceCodeResponse:
    """
    Start the device flow authentication.
    
    Returns:
        DeviceCodeResponse with device_code, user_code, verification_uri, etc.
    
    Raises:
        DeviceFlowError: If the request fails.
    """
    api_base = get_api_base()
    url = f"{api_base}/api/auth/device/code"
    
    try:
        response = requests.post(url, timeout=30)
        data = response.json()
        
        # Check for error response
        if not response.ok:
            error = data.get("error", {})
            raise DeviceFlowError(
                code=error.get("code", "UNKNOWN_ERROR"),
                message=error.get("message", "Failed to start device flow")
            )
        
        # API returns data directly (not wrapped in success/data)
        return DeviceCodeResponse(
            device_code=data["deviceCode"],
            user_code=data["userCode"],
            verification_uri=data["verificationUri"],
            expires_in=data["expiresIn"],
            interval=data.get("interval", 5),
        )
    except requests.RequestException as e:
        raise DeviceFlowError(
            code="NETWORK_ERROR",
            message=f"Network error: {e}"
        )


def poll_for_token(
    device_code: str, 
    interval: int = 5, 
    timeout: int = 300
) -> TokenResponse:
    """
    Poll for authentication token.
    
    Args:
        device_code: The device code from start_device_flow
        interval: Polling interval in seconds (default: 5)
        timeout: Maximum time to wait in seconds (default: 300)
    
    Returns:
        TokenResponse with token and user info.
    
    Raises:
        DeviceFlowError: If authentication fails or times out.
    """
    api_base = get_api_base()
    url = f"{api_base}/api/auth/device/token"
    
    start_time = time.time()
    current_interval = interval
    
    while time.time() - start_time < timeout:
        time.sleep(current_interval)
        
        try:
            response = requests.post(
                url,
                json={"deviceCode": device_code},
                timeout=30
            )
            data = response.json()
            
            # Check for error response
            error = data.get("error", {})
            error_code = error.get("code", "")
            
            if error_code:
                # Handle error cases
                if error_code == "authorization_pending":
                    # User hasn't authorized yet, keep polling
                    continue
                elif error_code == "slow_down":
                    # Increase interval
                    current_interval += 5
                    continue
                elif error_code == "expired_token":
                    raise DeviceFlowError(
                        code="expired_token",
                        message="Device code has expired. Please try again."
                    )
                elif error_code == "access_denied":
                    raise DeviceFlowError(
                        code="access_denied",
                        message="Authorization was denied."
                    )
                else:
                    raise DeviceFlowError(
                        code=error_code or "UNKNOWN_ERROR",
                        message=error.get("message", "Authentication failed")
                    )
            
            if response.ok and "token" in data:
                # Success! API returns data directly
                return TokenResponse(
                    token=data["token"],
                    user=data.get("user", {})
                )
                
        except requests.RequestException as e:
            # Network error, retry
            continue
    
    raise DeviceFlowError(
        code="timeout",
        message="Authentication timed out. Please try again."
    )
