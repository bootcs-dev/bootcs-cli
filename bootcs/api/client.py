"""
API Client for bootcs-api.

Provides HTTP client with authentication and error handling.
"""

import os
from typing import Dict, Any, Optional

import requests


# Default API base URL
DEFAULT_API_BASE = "https://api.bootcs.dev"


def get_api_base() -> str:
    """Get the API base URL from environment or default."""
    return os.environ.get("BOOTCS_API_URL", DEFAULT_API_BASE)


class APIError(Exception):
    """Exception raised for API errors."""
    
    def __init__(self, code: str, message: str, status_code: int = 0):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class APIClient:
    """HTTP client for bootcs-api."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            token: Authentication token. If not provided, will try to load from credentials.
        """
        self.base_url = get_api_base()
        self._token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        if self._token:
            self.session.headers["Authorization"] = f"Bearer {self._token}"
    
    @property
    def token(self) -> Optional[str]:
        """Get the current token."""
        return self._token
    
    @token.setter
    def token(self, value: str):
        """Set the token and update headers."""
        self._token = value
        if value:
            self.session.headers["Authorization"] = f"Bearer {value}"
        else:
            self.session.headers.pop("Authorization", None)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response.
        
        Args:
            response: The HTTP response.
        
        Returns:
            Parsed JSON response data (unwrapped from { success, data } envelope).
        
        Raises:
            APIError: If the response indicates an error.
        """
        try:
            data = response.json()
        except ValueError:
            raise APIError(
                code="INVALID_RESPONSE",
                message="Invalid JSON response from API",
                status_code=response.status_code
            )
        
        # Check for error in response
        if not response.ok:
            error = data.get("error", {})
            raise APIError(
                code=error.get("code", "UNKNOWN_ERROR"),
                message=error.get("message", "Unknown error"),
                status_code=response.status_code
            )
        
        # API returns { success: true, data: {...} } format
        # Unwrap and return just the data portion for convenience
        if "data" in data:
            return data["data"]
        
        return data
    
    def post(self, path: str, data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """
        Make a POST request.
        
        Args:
            path: API path (e.g., "/api/submit")
            data: Request body data
            timeout: Request timeout in seconds
        
        Returns:
            Response data.
        
        Raises:
            APIError: If the request fails.
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.session.post(url, json=data, timeout=timeout)
            return self._handle_response(response)
        except requests.RequestException as e:
            raise APIError(
                code="NETWORK_ERROR",
                message=f"Network error: {e}"
            )
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Make a GET request.
        
        Args:
            path: API path (e.g., "/api/submissions/123")
            params: Query parameters
            timeout: Request timeout in seconds
        
        Returns:
            Response data.
        
        Raises:
            APIError: If the request fails.
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            return self._handle_response(response)
        except requests.RequestException as e:
            raise APIError(
                code="NETWORK_ERROR",
                message=f"Network error: {e}"
            )
