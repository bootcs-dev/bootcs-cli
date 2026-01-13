"""
Unit tests for CheckRunner language parameter (Phase 0).
"""

import tempfile
import unittest
from pathlib import Path

from bootcs.check import internal
from bootcs.check.runner import CheckRunner


class TestCheckRunnerLanguageParameter(unittest.TestCase):
    """Test CheckRunner language parameter and backward compatibility."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checks_file = Path(self.temp_dir.name) / "__init__.py"
        self.checks_file.write_text("# Empty checks file")

        # Reset language state
        internal._current_language = None

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
        internal._current_language = None

    def test_runner_without_language_parameter(self):
        """CheckRunner works without language parameter (backward compatibility)."""
        runner = CheckRunner(self.checks_file, [])
        self.assertIsNone(runner.language)
        self.assertIsNone(internal.get_current_language())

    def test_runner_with_language_parameter(self):
        """CheckRunner accepts language parameter."""
        runner = CheckRunner(self.checks_file, [], language="python")
        self.assertEqual(runner.language, "python")

    def test_runner_sets_internal_language(self):
        """CheckRunner sets internal language state."""
        _runner = CheckRunner(self.checks_file, [], language="java")  # noqa: F841
        self.assertEqual(internal.get_current_language(), "java")

    def test_runner_with_c_language(self):
        """CheckRunner works with C language."""
        runner = CheckRunner(self.checks_file, [], language="c")
        self.assertEqual(runner.language, "c")
        self.assertEqual(internal.get_current_language(), "c")

    def test_runner_language_none_doesnt_set_internal(self):
        """CheckRunner with language=None doesn't change internal state."""
        # Set initial language
        internal.set_current_language("python")

        # Create runner without language
        runner = CheckRunner(self.checks_file, [], language=None)

        # Internal language should remain unchanged
        self.assertIsNone(runner.language)
        self.assertEqual(internal.get_current_language(), "python")

    def test_multiple_runners_different_languages(self):
        """Creating multiple runners with different languages."""
        _r1 = CheckRunner(self.checks_file, [], language="c")  # noqa: F841
        self.assertEqual(internal.get_current_language(), "c")

        _r2 = CheckRunner(self.checks_file, [], language="python")  # noqa: F841
        self.assertEqual(internal.get_current_language(), "python")

        _r3 = CheckRunner(self.checks_file, [], language="java")  # noqa: F841
        self.assertEqual(internal.get_current_language(), "java")

    def test_runner_preserves_other_parameters(self):
        """CheckRunner preserves checks_path and included_files."""
        included = [Path("hello.py"), Path("utils.py")]
        runner = CheckRunner(self.checks_file, included, language="python")

        self.assertEqual(runner.checks_path, self.checks_file)
        self.assertEqual(runner.included_files, included)
        self.assertEqual(runner.language, "python")


class TestCheckRunnerSignature(unittest.TestCase):
    """Test CheckRunner method signatures."""

    def test_init_signature_has_language(self):
        """CheckRunner.__init__ has language parameter."""
        import inspect

        sig = inspect.signature(CheckRunner.__init__)
        params = list(sig.parameters.keys())

        self.assertIn("language", params)
        self.assertIn("checks_path", params)
        self.assertIn("included_files", params)

    def test_language_parameter_is_optional(self):
        """Language parameter has default value (None)."""
        import inspect

        sig = inspect.signature(CheckRunner.__init__)
        lang_param = sig.parameters["language"]

        self.assertEqual(lang_param.default, None)


if __name__ == "__main__":
    unittest.main()
