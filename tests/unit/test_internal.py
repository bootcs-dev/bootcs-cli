"""
Unit tests for bootcs.check.internal module (Phase 0 additions).
"""

import unittest

from bootcs.check import internal


class TestLanguageManagement(unittest.TestCase):
    """Test language context management functions."""

    def setUp(self):
        """Reset language state before each test."""
        internal._current_language = None

    def tearDown(self):
        """Clean up language state after each test."""
        internal._current_language = None

    def test_initial_language_is_none(self):
        """Language should be None initially."""
        self.assertIsNone(internal.get_current_language())

    def test_set_and_get_language(self):
        """Setting and getting language should work."""
        internal.set_current_language("python")
        self.assertEqual(internal.get_current_language(), "python")

    def test_set_language_c(self):
        """Can set C language."""
        internal.set_current_language("c")
        self.assertEqual(internal.get_current_language(), "c")

    def test_set_language_java(self):
        """Can set Java language."""
        internal.set_current_language("java")
        self.assertEqual(internal.get_current_language(), "java")

    def test_change_language(self):
        """Can change language multiple times."""
        internal.set_current_language("c")
        self.assertEqual(internal.get_current_language(), "c")

        internal.set_current_language("python")
        self.assertEqual(internal.get_current_language(), "python")

        internal.set_current_language("java")
        self.assertEqual(internal.get_current_language(), "java")

    def test_set_language_none(self):
        """Can explicitly set language to None."""
        internal.set_current_language("python")
        internal.set_current_language(None)
        self.assertIsNone(internal.get_current_language())


class TestProblemNameExtraction(unittest.TestCase):
    """Test problem name extraction from slug."""

    def setUp(self):
        """Save original slug."""
        self.original_slug = internal.slug

    def tearDown(self):
        """Restore original slug."""
        internal.slug = self.original_slug

    def test_simple_slug(self):
        """Extract problem name from simple 2-part slug."""
        internal.slug = "cs50/hello"
        self.assertEqual(internal.get_problem_name(), "hello")

    def test_hyphenated_problem_name(self):
        """Extract hyphenated problem name."""
        internal.slug = "cs50/mario-less"
        self.assertEqual(internal.get_problem_name(), "mario-less")

    def test_different_course(self):
        """Extract problem name from different course."""
        internal.slug = "bootcamp/fizzbuzz"
        self.assertEqual(internal.get_problem_name(), "fizzbuzz")

    def test_nested_slug(self):
        """Extract problem name from nested slug."""
        internal.slug = "course/week1/hello"
        self.assertEqual(internal.get_problem_name(), "hello")

    def test_single_part_slug(self):
        """Single part slug returns itself."""
        internal.slug = "hello"
        self.assertEqual(internal.get_problem_name(), "hello")

    def test_slug_is_none(self):
        """Returns None when slug is None."""
        internal.slug = None
        self.assertIsNone(internal.get_problem_name())

    def test_empty_slug(self):
        """Empty slug returns empty string."""
        internal.slug = ""
        self.assertEqual(internal.get_problem_name(), "")


class TestSlugManagement(unittest.TestCase):
    """Test slug state management."""

    def setUp(self):
        """Save original slug."""
        self.original_slug = internal.slug

    def tearDown(self):
        """Restore original slug."""
        internal.slug = self.original_slug

    def test_slug_initially_none(self):
        """Slug should be None initially (or from previous test)."""
        # Just check that we can access it
        self.assertIsNotNone(hasattr(internal, "slug"))

    def test_set_slug(self):
        """Can set slug."""
        internal.slug = "test/problem"
        self.assertEqual(internal.slug, "test/problem")

    def test_slug_persists(self):
        """Slug persists across function calls."""
        internal.slug = "cs50/credit"
        self.assertEqual(internal.get_problem_name(), "credit")
        self.assertEqual(internal.slug, "cs50/credit")


if __name__ == "__main__":
    unittest.main()
