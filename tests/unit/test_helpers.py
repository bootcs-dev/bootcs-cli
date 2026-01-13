"""
Unit tests for bootcs.check.helpers module.

Tests the helper functions that reduce boilerplate in check implementations.
Follows 80/20 principle: covers critical paths and edge cases.
"""

import tempfile
import unittest
from unittest.mock import MagicMock, patch

from bootcs.check.adapters.base import LanguageAdapter
from bootcs.check.helpers import standard_compile_check, with_adapter


class TestStandardCompileCheck(unittest.TestCase):
    """Test standard_compile_check factory function."""

    def test_returns_callable(self):
        """standard_compile_check returns a callable function."""
        compile_func = standard_compile_check("hello")
        self.assertTrue(callable(compile_func))

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_c_compilation_with_lcs50(self, mock_lang, mock_create):
        """C language compilation includes lcs50=True."""
        mock_lang.return_value = "c"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("hello")
        compile_func()

        mock_create.assert_called_once_with(problem="hello")
        mock_adapter.compile.assert_called_once_with(lcs50=True)

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_java_compilation_without_lcs50(self, mock_lang, mock_create):
        """Java compilation does not include lcs50 flag."""
        mock_lang.return_value = "java"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("hello")
        compile_func()

        mock_create.assert_called_once_with(problem="hello")
        mock_adapter.compile.assert_called_once_with()

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_python_compilation(self, mock_lang, mock_create):
        """Python 'compilation' (syntax validation) works correctly."""
        mock_lang.return_value = "python"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("hello")
        compile_func()

        mock_create.assert_called_once_with(problem="hello")
        mock_adapter.compile.assert_called_once_with()

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_problem_name")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_problem_name_from_context_when_none(self, mock_lang, mock_problem, mock_create):
        """When problem is None, uses internal.get_problem_name()."""
        mock_lang.return_value = "c"
        mock_problem.return_value = "mario"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check(None)
        compile_func()

        mock_problem.assert_called_once()
        mock_create.assert_called_once_with(problem="mario")

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_problem_name_explicit(self, mock_lang, mock_create):
        """Explicit problem name is used when provided."""
        mock_lang.return_value = "c"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("caesar")
        compile_func()

        mock_create.assert_called_once_with(problem="caesar")

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_multiple_languages_same_factory(self, mock_lang, mock_create):
        """Same factory works for different languages."""
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("hello")

        # Test C
        mock_lang.return_value = "c"
        compile_func()
        mock_adapter.compile.assert_called_with(lcs50=True)

        # Test Java
        mock_adapter.reset_mock()
        mock_lang.return_value = "java"
        compile_func()
        mock_adapter.compile.assert_called_with()

        # Test Python
        mock_adapter.reset_mock()
        mock_lang.return_value = "python"
        compile_func()
        mock_adapter.compile.assert_called_with()


class TestWithAdapterDecorator(unittest.TestCase):
    """Test with_adapter decorator."""

    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_decorator_provides_adapter(self, mock_lang):
        """Decorator injects adapter as first argument."""
        mock_lang.return_value = "python"

        @with_adapter("hello")
        def my_check(adapter):
            return adapter.problem

        result = my_check()
        self.assertEqual(result, "hello")

    def test_decorator_preserves_function_name(self):
        """Decorated function preserves original name."""

        @with_adapter("hello")
        def my_custom_check(adapter):
            pass

        self.assertEqual(my_custom_check.__name__, "my_custom_check")

    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_decorator_passes_additional_args(self, mock_lang):
        """Decorator passes through additional arguments."""
        mock_lang.return_value = "python"

        @with_adapter("hello")
        def check_with_args(adapter, value, keyword=None):
            return (adapter.problem, value, keyword)

        result = check_with_args(42, keyword="test")
        self.assertEqual(result, ("hello", 42, "test"))

    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_decorator_works_with_kwargs_only(self, mock_lang):
        """Decorator works with keyword-only arguments."""
        mock_lang.return_value = "python"

        @with_adapter("caesar")
        def check_kwargs(adapter, *, key=10):
            return (adapter.problem, key)

        result = check_kwargs(key=20)
        self.assertEqual(result, ("caesar", 20))

    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_multiple_decorators_same_problem(self, mock_lang):
        """Multiple functions can use same problem name."""
        mock_lang.return_value = "python"

        @with_adapter("hello")
        def check1(adapter):
            return adapter.problem

        @with_adapter("hello")
        def check2(adapter):
            return adapter.problem

        self.assertEqual(check1(), "hello")
        self.assertEqual(check2(), "hello")

    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_decorator_different_problems(self, mock_lang):
        """Decorator works with different problem names."""
        mock_lang.return_value = "python"

        @with_adapter("hello")
        def hello_check(adapter):
            return adapter.problem

        @with_adapter("mario")
        def mario_check(adapter):
            return adapter.problem

        self.assertEqual(hello_check(), "hello")
        self.assertEqual(mario_check(), "mario")

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_adapter_created_per_call(self, mock_lang, mock_create):
        """Adapter is created fresh on each function call."""
        mock_lang.return_value = "python"
        mock_adapter1 = MagicMock()
        mock_adapter2 = MagicMock()
        mock_create.side_effect = [mock_adapter1, mock_adapter2]

        @with_adapter("hello")
        def my_check(adapter):
            return adapter

        result1 = my_check()
        result2 = my_check()

        self.assertEqual(mock_create.call_count, 2)
        self.assertIs(result1, mock_adapter1)
        self.assertIs(result2, mock_adapter2)


class TestHelpersIntegration(unittest.TestCase):
    """Integration tests combining helpers with real adapters."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_standard_compile_check_integration_c(self, mock_lang, mock_create):
        """Integration: standard_compile_check with C configuration."""
        mock_lang.return_value = "c"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("hello")
        compile_func()

        # Verify compilation was called with lcs50 flag
        mock_adapter.compile.assert_called_once_with(lcs50=True)

    @patch("bootcs.check.helpers.create_adapter")
    @patch("bootcs.check.helpers.internal.get_current_language")
    def test_standard_compile_check_integration_python(self, mock_lang, mock_create):
        """Integration: standard_compile_check with Python configuration."""
        mock_lang.return_value = "python"
        mock_adapter = MagicMock(spec=LanguageAdapter)
        mock_create.return_value = mock_adapter

        compile_func = standard_compile_check("hello")
        compile_func()

        # Verify syntax validation was called without flags
        mock_adapter.compile.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
