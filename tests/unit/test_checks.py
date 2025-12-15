"""
Unit tests for language detection and checks management.
"""

import base64
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from bootcs.__main__ import detect_language, LANGUAGE_EXTENSIONS
from bootcs.api.checks import ChecksManager, CACHE_TTL
from bootcs.api.client import APIError


class TestDetectLanguage(unittest.TestCase):
    """Test language detection from files."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_explicit_override(self):
        """Explicit language always wins."""
        (self.root / "hello.c").touch()
        lang = detect_language(self.root, explicit="python")
        self.assertEqual(lang, "python")

    def test_detect_c(self):
        """Detect C from .c file."""
        (self.root / "main.c").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "c")

    def test_detect_c_header(self):
        """Detect C from .h file."""
        (self.root / "header.h").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "c")

    def test_detect_python(self):
        """Detect Python from .py file."""
        (self.root / "script.py").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "python")

    def test_detect_javascript(self):
        """Detect JavaScript from .js file."""
        (self.root / "app.js").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "javascript")

    def test_detect_go(self):
        """Detect Go from .go file."""
        (self.root / "main.go").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "go")

    def test_detect_rust(self):
        """Detect Rust from .rs file."""
        (self.root / "main.rs").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "rust")

    def test_most_common_wins(self):
        """When multiple languages, most common wins."""
        (self.root / "main.c").touch()
        (self.root / "util.c").touch()
        (self.root / "helper.c").touch()
        (self.root / "script.py").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "c")

    def test_python_wins_when_more(self):
        """Python wins when more Python files."""
        (self.root / "main.py").touch()
        (self.root / "util.py").touch()
        (self.root / "helper.c").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "python")

    def test_empty_directory_defaults_to_c(self):
        """Empty directory defaults to C."""
        lang = detect_language(self.root)
        self.assertEqual(lang, "c")

    def test_no_recognized_files_defaults_to_c(self):
        """Unknown extensions default to C."""
        (self.root / "readme.txt").touch()
        (self.root / "data.json").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "c")

    def test_hidden_files_ignored(self):
        """Hidden files (starting with .) are ignored."""
        (self.root / ".hidden.py").touch()
        (self.root / "main.c").touch()
        lang = detect_language(self.root)
        self.assertEqual(lang, "c")

    def test_none_directory_uses_cwd(self):
        """None directory uses current working directory."""
        # Just verify it doesn't crash
        lang = detect_language(None)
        self.assertIsInstance(lang, str)


class TestLanguageExtensions(unittest.TestCase):
    """Test language extension mapping completeness."""

    def test_all_common_extensions_covered(self):
        """Common programming extensions are mapped."""
        expected = ['.c', '.h', '.py', '.js', '.go', '.rs']
        for ext in expected:
            self.assertIn(ext, LANGUAGE_EXTENSIONS)

    def test_extension_values_are_strings(self):
        """All extension values are language strings."""
        for ext, lang in LANGUAGE_EXTENSIONS.items():
            self.assertIsInstance(lang, str)
            self.assertTrue(len(lang) > 0)


class TestChecksManager(unittest.TestCase):
    """Test ChecksManager caching logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)
        self.manager = ChecksManager(token="test_token", cache_dir=self.cache_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_cache_dir_created(self):
        """Cache directory is created on init."""
        self.assertTrue(self.cache_dir.exists())

    def test_invalid_slug_format(self):
        """Invalid slug format raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.manager.get_checks("invalid-slug")
        self.assertIn("Invalid slug format", str(ctx.exception))

    @patch.object(ChecksManager, 'get_all_checks')
    def test_uses_cache_when_valid(self, mock_get_all):
        """Uses cache when valid, doesn't call API."""
        # Pre-populate cache
        cache_path = self.cache_dir / "cs50" / "c" / "hello"
        cache_path.mkdir(parents=True)
        (cache_path / "__init__.py").write_text("# check")
        (cache_path / ".version").write_text("abc123")

        result = self.manager.get_checks("cs50/hello", language="c")

        self.assertEqual(result, cache_path)
        mock_get_all.assert_not_called()

    @patch.object(ChecksManager, 'get_all_checks')
    def test_force_update_ignores_cache(self, mock_get_all):
        """force_update=True ignores cache and calls API."""
        # Pre-populate cache
        cache_path = self.cache_dir / "cs50" / "c" / "hello"
        cache_path.mkdir(parents=True)
        (cache_path / "__init__.py").write_text("# check")
        (cache_path / ".version").write_text("abc123")

        self.manager.get_checks("cs50/hello", language="c", force_update=True)

        mock_get_all.assert_called_once()

    def test_clear_all_cache(self):
        """Clear all cache removes everything."""
        # Create some cache
        (self.cache_dir / "cs50" / "c" / "hello").mkdir(parents=True)
        (self.cache_dir / "cs50" / "c" / "hello" / "test.py").touch()

        self.manager.clear_cache()

        # Directory should be empty (recreated)
        self.assertEqual(list(self.cache_dir.iterdir()), [])

    def test_clear_course_cache(self):
        """Clear cache for specific course."""
        # Create cache for two courses
        (self.cache_dir / "cs50" / "c" / "hello").mkdir(parents=True)
        (self.cache_dir / "other" / "c" / "test").mkdir(parents=True)

        self.manager.clear_cache(slug="cs50")

        self.assertFalse((self.cache_dir / "cs50").exists())
        self.assertTrue((self.cache_dir / "other").exists())

    def test_list_cache_empty(self):
        """List empty cache returns empty list."""
        result = self.manager.list_cache()
        self.assertEqual(result, [])

    def test_list_cache_with_entries(self):
        """List cache returns cached entries."""
        # Create cache entry
        cache_path = self.cache_dir / "cs50" / "c" / "hello"
        cache_path.mkdir(parents=True)
        (cache_path / ".version").write_text("abc12345")

        result = self.manager.list_cache()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["course"], "cs50")
        self.assertEqual(result[0]["language"], "c")
        self.assertEqual(result[0]["stage"], "hello")

    def test_write_stage_cache(self):
        """Write stage cache correctly decodes base64."""
        stage_path = self.cache_dir / "cs50" / "c" / "test"
        files = [
            {"path": "check.py", "content": base64.b64encode(b"# test check").decode()},
            {"path": ".bootcs.yml", "content": base64.b64encode(b"checks: check.py").decode()},
        ]

        self.manager._write_stage_cache(stage_path, files)

        self.assertTrue((stage_path / "check.py").exists())
        self.assertEqual((stage_path / "check.py").read_text(), "# test check")
        self.assertTrue((stage_path / ".bootcs.yml").exists())


class TestChecksManagerIntegration(unittest.TestCase):
    """Integration tests for ChecksManager with mocked API."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    @patch('bootcs.api.checks.APIClient')
    def test_get_all_checks_batch_download(self, MockAPIClient):
        """get_all_checks downloads and caches all stages."""
        mock_client = MagicMock()
        mock_client.get.return_value = {
            "courseSlug": "cs50",
            "language": "c",
            "version": "abc123",
            "checks": [
                {
                    "stageSlug": "hello",
                    "files": [
                        {"path": "__init__.py", "content": base64.b64encode(b"# hello").decode()},
                    ]
                },
                {
                    "stageSlug": "mario",
                    "files": [
                        {"path": "__init__.py", "content": base64.b64encode(b"# mario").decode()},
                    ]
                },
            ]
        }
        MockAPIClient.return_value = mock_client

        manager = ChecksManager(token="test", cache_dir=self.cache_dir)
        result = manager.get_all_checks("cs50", language="c")

        self.assertEqual(len(result), 2)
        self.assertIn("hello", result)
        self.assertIn("mario", result)

        # Verify files were written
        self.assertTrue((self.cache_dir / "cs50" / "c" / "hello" / "__init__.py").exists())
        self.assertTrue((self.cache_dir / "cs50" / "c" / "mario" / "__init__.py").exists())


if __name__ == "__main__":
    unittest.main()
