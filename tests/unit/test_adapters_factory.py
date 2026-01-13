"""
Unit tests for language adapter factory (Phase 1).
"""

import unittest

from bootcs.check import internal
from bootcs.check.adapters.compiled import CompiledLanguageAdapter, InterpretedLanguageAdapter
from bootcs.check.adapters.factory import (
    COMPILED_LANGUAGES,
    INTERPRETED_LANGUAGES,
    create_adapter,
    get_adapter_for_language,
    is_compiled_language,
    is_interpreted_language,
)


class TestLanguageClassification(unittest.TestCase):
    """Test language classification functions."""

    def test_compiled_languages(self):
        """Test compiled language detection."""
        for lang in ["c", "cpp", "c++", "java"]:
            with self.subTest(lang=lang):
                self.assertTrue(is_compiled_language(lang))
                self.assertFalse(is_interpreted_language(lang))

    def test_interpreted_languages(self):
        """Test interpreted language detection."""
        for lang in ["python", "py", "javascript", "js", "typescript", "ts"]:
            with self.subTest(lang=lang):
                self.assertTrue(is_interpreted_language(lang))
                self.assertFalse(is_compiled_language(lang))

    def test_case_insensitive(self):
        """Language classification is case-insensitive."""
        self.assertTrue(is_compiled_language("C"))
        self.assertTrue(is_compiled_language("JAVA"))
        self.assertTrue(is_interpreted_language("PYTHON"))


class TestGetAdapterForLanguage(unittest.TestCase):
    """Test adapter class selection."""

    def test_compiled_language_returns_compiled_adapter(self):
        """Compiled languages return CompiledLanguageAdapter."""
        for lang in ["c", "java", "cpp"]:
            with self.subTest(lang=lang):
                adapter_class = get_adapter_for_language(lang)
                self.assertEqual(adapter_class, CompiledLanguageAdapter)

    def test_interpreted_language_returns_interpreted_adapter(self):
        """Interpreted languages return InterpretedLanguageAdapter."""
        for lang in ["python", "javascript"]:
            with self.subTest(lang=lang):
                adapter_class = get_adapter_for_language(lang)
                self.assertEqual(adapter_class, InterpretedLanguageAdapter)

    def test_unknown_language_defaults_to_compiled(self):
        """Unknown languages default to CompiledLanguageAdapter."""
        adapter_class = get_adapter_for_language("fortran")
        self.assertEqual(adapter_class, CompiledLanguageAdapter)


class TestCreateAdapter(unittest.TestCase):
    """Test create_adapter factory function."""

    def setUp(self):
        """Set up test state."""
        self.original_slug = internal.slug
        self.original_language = internal.get_current_language()

    def tearDown(self):
        """Clean up test state."""
        internal.slug = self.original_slug
        internal.set_current_language(self.original_language)

    def test_create_adapter_with_explicit_params(self):
        """Create adapter with explicit problem and language."""
        adapter = create_adapter("hello", "c")
        self.assertIsInstance(adapter, CompiledLanguageAdapter)
        self.assertEqual(adapter.problem, "hello")
        self.assertEqual(adapter.language, "c")

    def test_create_adapter_auto_detects_from_internal(self):
        """Create adapter auto-detects from internal state."""
        internal.slug = "cs50/hello"
        internal.set_current_language("python")

        adapter = create_adapter()
        self.assertIsInstance(adapter, InterpretedLanguageAdapter)
        self.assertEqual(adapter.problem, "hello")
        self.assertEqual(adapter.language, "python")

    def test_create_adapter_with_problem_only(self):
        """Create adapter with problem, language from internal."""
        internal.set_current_language("java")

        adapter = create_adapter("mario-less")
        self.assertIsInstance(adapter, CompiledLanguageAdapter)
        self.assertEqual(adapter.problem, "mario-less")
        self.assertEqual(adapter.language, "java")

    def test_create_adapter_compiled_language(self):
        """Create adapter for compiled language."""
        internal.set_current_language("c")
        adapter = create_adapter("hello")
        self.assertIsInstance(adapter, CompiledLanguageAdapter)

    def test_create_adapter_interpreted_language(self):
        """Create adapter for interpreted language."""
        internal.set_current_language("python")
        adapter = create_adapter("hello")
        self.assertIsInstance(adapter, InterpretedLanguageAdapter)

    def test_create_adapter_force_compiled(self):
        """Force CompiledLanguageAdapter even for interpreted language."""
        internal.set_current_language("python")
        adapter = create_adapter("hello", adapter_type="compiled")
        self.assertIsInstance(adapter, CompiledLanguageAdapter)

    def test_create_adapter_force_interpreted(self):
        """Force InterpretedLanguageAdapter even for compiled language."""
        internal.set_current_language("c")
        adapter = create_adapter("hello", adapter_type="interpreted")
        self.assertIsInstance(adapter, InterpretedLanguageAdapter)

    def test_create_adapter_no_problem_raises_error(self):
        """Raise error if problem cannot be determined."""
        internal.slug = None
        internal.set_current_language("c")

        with self.assertRaises(ValueError) as cm:
            create_adapter()
        self.assertIn("Problem name not specified", str(cm.exception))

    def test_create_adapter_no_language_raises_error(self):
        """Raise error if language cannot be determined."""
        internal.slug = "cs50/hello"
        internal.set_current_language(None)

        with self.assertRaises(ValueError) as cm:
            create_adapter()
        self.assertIn("Language not specified", str(cm.exception))

    def test_create_adapter_invalid_adapter_type(self):
        """Raise error for invalid adapter_type."""
        internal.slug = "cs50/hello"
        internal.set_current_language("c")

        with self.assertRaises(ValueError) as cm:
            create_adapter(adapter_type="invalid")
        self.assertIn("Invalid adapter_type", str(cm.exception))

    def test_create_adapter_all_languages(self):
        """Create adapters for all supported languages."""
        test_cases = [
            ("c", CompiledLanguageAdapter),
            ("java", CompiledLanguageAdapter),
            ("python", InterpretedLanguageAdapter),
            ("javascript", InterpretedLanguageAdapter),
        ]

        for lang, expected_class in test_cases:
            with self.subTest(lang=lang):
                internal.set_current_language(lang)
                adapter = create_adapter("hello")
                self.assertIsInstance(adapter, expected_class)
                self.assertEqual(adapter.language, lang)


class TestLanguageSets(unittest.TestCase):
    """Test language set definitions."""

    def test_compiled_languages_set(self):
        """Verify compiled languages set."""
        self.assertEqual(COMPILED_LANGUAGES, {"c", "cpp", "c++", "java"})

    def test_interpreted_languages_set(self):
        """Verify interpreted languages set."""
        self.assertEqual(
            INTERPRETED_LANGUAGES, {"python", "py", "javascript", "js", "typescript", "ts"}
        )

    def test_no_overlap_between_sets(self):
        """Compiled and interpreted sets don't overlap."""
        overlap = COMPILED_LANGUAGES & INTERPRETED_LANGUAGES
        self.assertEqual(len(overlap), 0)


if __name__ == "__main__":
    unittest.main()
