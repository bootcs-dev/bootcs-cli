"""
Unit tests for parse_slug function (Phase 0 MVP simplification).
"""

import unittest

from bootcs.__main__ import parse_slug


class TestParseSlug(unittest.TestCase):
    """Test slug parsing with new 2-part format."""

    def test_standard_two_part_slug(self):
        """Standard 2-part slug: course/stage."""
        course, stage = parse_slug("cs50/hello")
        self.assertEqual(course, "cs50")
        self.assertEqual(stage, "hello")

    def test_hyphenated_stage_name(self):
        """Stage name can contain hyphens."""
        course, stage = parse_slug("cs50/mario-less")
        self.assertEqual(course, "cs50")
        self.assertEqual(stage, "mario-less")

    def test_different_course(self):
        """Works with different course slugs."""
        course, stage = parse_slug("bootcamp/fizzbuzz")
        self.assertEqual(course, "bootcamp")
        self.assertEqual(stage, "fizzbuzz")

    def test_single_part_slug(self):
        """Single part treated as stage only."""
        course, stage = parse_slug("hello")
        self.assertIsNone(course)
        self.assertEqual(stage, "hello")

    def test_nested_slug_three_parts(self):
        """3+ parts: first is course, rest is stage."""
        course, stage = parse_slug("course/week1/hello")
        self.assertEqual(course, "course")
        self.assertEqual(stage, "week1/hello")

    def test_deeply_nested_slug(self):
        """Deeply nested slug."""
        course, stage = parse_slug("course/week1/day1/hello")
        self.assertEqual(course, "course")
        self.assertEqual(stage, "week1/day1/hello")

    def test_numeric_course(self):
        """Course can be numeric."""
        course, stage = parse_slug("cs50/week1")
        self.assertEqual(course, "cs50")
        self.assertEqual(stage, "week1")

    def test_underscores_in_names(self):
        """Underscores are preserved."""
        course, stage = parse_slug("my_course/my_stage")
        self.assertEqual(course, "my_course")
        self.assertEqual(stage, "my_stage")

    def test_uppercase_names(self):
        """Case is preserved."""
        course, stage = parse_slug("CS50/Hello")
        self.assertEqual(course, "CS50")
        self.assertEqual(stage, "Hello")

    def test_empty_string(self):
        """Empty string returns None and empty."""
        course, stage = parse_slug("")
        self.assertIsNone(course)
        self.assertEqual(stage, "")


class TestParseSlugBackwardCompatibility(unittest.TestCase):
    """Test that new format doesn't break existing usages."""

    def test_common_cs50_problems(self):
        """Test common CS50 problem slugs."""
        test_cases = [
            ("cs50/hello", ("cs50", "hello")),
            ("cs50/mario-less", ("cs50", "mario-less")),
            ("cs50/mario-more", ("cs50", "mario-more")),
            ("cs50/cash", ("cs50", "cash")),
            ("cs50/credit", ("cs50", "credit")),
            ("cs50/readability", ("cs50", "readability")),
            ("cs50/caesar", ("cs50", "caesar")),
            ("cs50/substitution", ("cs50", "substitution")),
        ]

        for slug, expected in test_cases:
            with self.subTest(slug=slug):
                result = parse_slug(slug)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
