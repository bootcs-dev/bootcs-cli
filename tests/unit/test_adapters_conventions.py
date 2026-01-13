"""
Unit tests for language adapter conventions (Phase 1).
"""

import unittest

from bootcs.check.adapters.conventions import (
    NAMING_CONVENTIONS,
    c_convention,
    cpp_convention,
    get_source_filename,
    go_convention,
    java_convention,
    javascript_convention,
    python_convention,
    rust_convention,
    typescript_convention,
)


class TestNamingConventions(unittest.TestCase):
    """Test individual naming convention functions."""

    def test_c_convention_simple(self):
        """C convention: lowercase + .c"""
        self.assertEqual(c_convention("hello"), "hello.c")

    def test_c_convention_hyphenated(self):
        """C convention preserves hyphens."""
        self.assertEqual(c_convention("mario-less"), "mario-less.c")

    def test_cpp_convention(self):
        """C++ convention: lowercase + .cpp"""
        self.assertEqual(cpp_convention("hello"), "hello.cpp")
        self.assertEqual(cpp_convention("fizz-buzz"), "fizz-buzz.cpp")

    def test_java_convention_simple(self):
        """Java convention: PascalCase + .java"""
        self.assertEqual(java_convention("hello"), "Hello.java")

    def test_java_convention_hyphenated(self):
        """Java convention converts kebab-case to PascalCase."""
        self.assertEqual(java_convention("mario-less"), "MarioLess.java")
        self.assertEqual(java_convention("fizz-buzz"), "FizzBuzz.java")

    def test_java_convention_multiple_hyphens(self):
        """Java handles multiple hyphens."""
        self.assertEqual(java_convention("hello-world-test"), "HelloWorldTest.java")

    def test_python_convention(self):
        """Python convention: lowercase + .py"""
        self.assertEqual(python_convention("hello"), "hello.py")
        self.assertEqual(python_convention("mario-less"), "mario-less.py")

    def test_go_convention(self):
        """Go convention: lowercase + .go"""
        self.assertEqual(go_convention("hello"), "hello.go")

    def test_rust_convention(self):
        """Rust convention: lowercase + .rs"""
        self.assertEqual(rust_convention("hello"), "hello.rs")

    def test_javascript_convention(self):
        """JavaScript convention: lowercase + .js"""
        self.assertEqual(javascript_convention("hello"), "hello.js")

    def test_typescript_convention(self):
        """TypeScript convention: lowercase + .ts"""
        self.assertEqual(typescript_convention("hello"), "hello.ts")


class TestGetSourceFilename(unittest.TestCase):
    """Test get_source_filename function."""

    def test_c_filename(self):
        """Get C source filename."""
        self.assertEqual(get_source_filename("hello", "c"), "hello.c")
        self.assertEqual(get_source_filename("mario-less", "c"), "mario-less.c")

    def test_java_filename(self):
        """Get Java source filename."""
        self.assertEqual(get_source_filename("hello", "java"), "Hello.java")
        self.assertEqual(get_source_filename("mario-less", "java"), "MarioLess.java")

    def test_python_filename(self):
        """Get Python source filename."""
        self.assertEqual(get_source_filename("hello", "python"), "hello.py")
        self.assertEqual(get_source_filename("credit", "python"), "credit.py")

    def test_case_insensitive_language(self):
        """Language names are case-insensitive."""
        self.assertEqual(get_source_filename("hello", "C"), "hello.c")
        self.assertEqual(get_source_filename("hello", "JAVA"), "Hello.java")
        self.assertEqual(get_source_filename("hello", "Python"), "hello.py")

    def test_language_aliases(self):
        """Language aliases work."""
        self.assertEqual(get_source_filename("hello", "py"), "hello.py")
        self.assertEqual(get_source_filename("hello", "js"), "hello.js")
        self.assertEqual(get_source_filename("hello", "ts"), "hello.ts")

    def test_unsupported_language_raises_error(self):
        """Unsupported language raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            get_source_filename("hello", "fortran")
        self.assertIn("Unsupported language", str(cm.exception))
        self.assertIn("fortran", str(cm.exception))

    def test_all_common_languages(self):
        """Test all commonly used languages."""
        test_cases = [
            ("hello", "c", "hello.c"),
            ("hello", "cpp", "hello.cpp"),
            ("hello", "java", "Hello.java"),
            ("hello", "python", "hello.py"),
            ("hello", "go", "hello.go"),
            ("hello", "rust", "hello.rs"),
            ("hello", "javascript", "hello.js"),
            ("hello", "typescript", "hello.ts"),
        ]

        for problem, lang, expected in test_cases:
            with self.subTest(problem=problem, lang=lang):
                result = get_source_filename(problem, lang)
                self.assertEqual(result, expected)


class TestConventionRegistry(unittest.TestCase):
    """Test the naming conventions registry."""

    def test_registry_contains_all_languages(self):
        """Registry contains all supported languages."""
        expected_languages = {
            "c",
            "cpp",
            "c++",
            "java",
            "python",
            "py",
            "go",
            "rust",
            "rs",
            "javascript",
            "js",
            "typescript",
            "ts",
        }

        actual_languages = set(NAMING_CONVENTIONS.keys())
        self.assertEqual(actual_languages, expected_languages)

    def test_all_conventions_are_callable(self):
        """All conventions in registry are callable."""
        for lang, convention in NAMING_CONVENTIONS.items():
            with self.subTest(lang=lang):
                self.assertTrue(callable(convention))

    def test_all_conventions_return_strings(self):
        """All conventions return strings."""
        test_problem = "hello"
        for lang, convention in NAMING_CONVENTIONS.items():
            with self.subTest(lang=lang):
                result = convention(test_problem)
                self.assertIsInstance(result, str)
                self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()
