"""
Unit tests for bootcs auth module.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestCredentials(unittest.TestCase):
    """Test credentials management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "bootcs" / "credentials.yaml"

        # Patch get_credentials_path to use temp directory
        self.patcher = patch(
            "bootcs.auth.credentials.get_credentials_path", return_value=self.config_path
        )
        self.patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_save_and_get_token(self):
        """Test saving and retrieving token."""
        from bootcs.auth.credentials import get_token, save_token

        save_token("test_token_123")
        self.assertEqual(get_token(), "test_token_123")

    def test_clear_token(self):
        """Test clearing token."""
        from bootcs.auth.credentials import clear_token, get_token, save_token

        save_token("test_token_456")
        self.assertEqual(get_token(), "test_token_456")

        clear_token()
        self.assertIsNone(get_token())

    def test_save_and_get_user(self):
        """Test saving and retrieving user info."""
        from bootcs.auth.credentials import get_user, save_user

        user_info = {"username": "testuser", "id": "123"}
        save_user(user_info)

        retrieved = get_user()
        self.assertEqual(retrieved["username"], "testuser")
        self.assertEqual(retrieved["id"], "123")

    def test_is_logged_in(self):
        """Test login status check."""
        from bootcs.auth.credentials import clear_token, is_logged_in, save_token

        self.assertFalse(is_logged_in())

        save_token("token")
        self.assertTrue(is_logged_in())

        clear_token()
        self.assertFalse(is_logged_in())

    def test_credentials_file_permissions(self):
        """Test that credentials file has secure permissions."""
        from bootcs.auth.credentials import save_token

        save_token("secret_token")

        # Check file exists
        self.assertTrue(self.config_path.exists())

        # Check permissions (should be 0o600)
        mode = os.stat(self.config_path).st_mode & 0o777
        self.assertEqual(mode, 0o600)


class TestDeviceFlow(unittest.TestCase):
    """Test Device Flow authentication."""

    @patch("bootcs.auth.device_flow.requests.get")
    def test_start_device_flow_success(self, mock_get):
        """Test successful device flow start."""
        from bootcs.auth.device_flow import start_device_flow

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "device_code": "abc123",
                "user_code": "ABCD-1234",
                "verification_uri": "https://github.com/login/device",
                "expires_in": 900,
                "interval": 5,
            },
        }
        mock_get.return_value = mock_response

        result = start_device_flow()

        self.assertEqual(result.device_code, "abc123")
        self.assertEqual(result.user_code, "ABCD-1234")
        self.assertEqual(result.verification_uri, "https://github.com/login/device")
        self.assertEqual(result.expires_in, 900)
        self.assertEqual(result.interval, 5)

    @patch("bootcs.auth.device_flow.requests.get")
    def test_start_device_flow_error(self, mock_get):
        """Test device flow start with error."""
        from bootcs.auth.device_flow import DeviceFlowError, start_device_flow

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.json.return_value = {
            "error": {"code": "NETWORK_ERROR", "message": "Connection failed"}
        }
        mock_get.return_value = mock_response

        with self.assertRaises(DeviceFlowError) as ctx:
            start_device_flow()

        self.assertEqual(ctx.exception.code, "NETWORK_ERROR")


if __name__ == "__main__":
    unittest.main()
