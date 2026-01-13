"""
Unit tests for bootcs API module.
"""

import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bootcs.api.client import APIClient, APIError
from bootcs.api.submit import collect_files


class TestAPIClient(unittest.TestCase):
    """Test API client."""

    def test_init_with_token(self):
        """Test client initialization with token."""
        client = APIClient(token="test_token")
        self.assertEqual(client.token, "test_token")
        self.assertIn("Authorization", client.session.headers)

    def test_init_without_token(self):
        """Test client initialization without token."""
        client = APIClient()
        self.assertIsNone(client.token)
        self.assertNotIn("Authorization", client.session.headers)

    def test_set_token(self):
        """Test setting token after init."""
        client = APIClient()
        client.token = "new_token"
        self.assertEqual(client.token, "new_token")
        self.assertEqual(client.session.headers["Authorization"], "Bearer new_token")

    @patch("bootcs.api.client.requests.Session.post")
    def test_post_success(self, mock_post):
        """Test successful POST request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "data": {"submissionId": "123", "status": "EVALUATING"},
        }
        mock_post.return_value = mock_response

        client = APIClient(token="token")
        result = client.post("/api/submit", {"slug": "test/hello"})

        self.assertEqual(result["submissionId"], "123")

    @patch("bootcs.api.client.requests.Session.post")
    def test_post_error(self, mock_post):
        """Test POST request with error response."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {"code": "UNAUTHORIZED", "message": "Invalid token"}
        }
        mock_post.return_value = mock_response

        client = APIClient(token="bad_token")

        with self.assertRaises(APIError) as ctx:
            client.post("/api/submit", {"slug": "test/hello"})

        self.assertEqual(ctx.exception.code, "UNAUTHORIZED")
        self.assertEqual(ctx.exception.status_code, 401)


class TestCollectFiles(unittest.TestCase):
    """Test file collection."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create test files
        (self.root / "hello.c").write_text("#include <stdio.h>\nint main() { return 0; }")
        (self.root / "large.txt").write_bytes(b"x" * 100)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_collect_single_file(self):
        """Test collecting a single file."""
        files = collect_files(["hello.c"], root=self.root)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].path, "hello.c")

        # Verify content is base64 encoded
        decoded = base64.b64decode(files[0].content).decode()
        self.assertIn("#include <stdio.h>", decoded)

    def test_collect_multiple_files(self):
        """Test collecting multiple files."""
        files = collect_files(["hello.c", "large.txt"], root=self.root)

        self.assertEqual(len(files), 2)
        paths = [f.path for f in files]
        self.assertIn("hello.c", paths)
        self.assertIn("large.txt", paths)

    def test_file_not_found(self):
        """Test error when file not found."""
        with self.assertRaises(ValueError) as ctx:
            collect_files(["nonexistent.c"], root=self.root)

        self.assertIn("not found", str(ctx.exception))

    def test_file_too_large(self):
        """Test error when file exceeds size limit."""
        # Create a file larger than limit
        (self.root / "huge.bin").write_bytes(b"x" * 1000)

        with self.assertRaises(ValueError) as ctx:
            collect_files(["huge.bin"], root=self.root, max_file_size=500)

        self.assertIn("too large", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
