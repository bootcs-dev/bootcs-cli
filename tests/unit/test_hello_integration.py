"""
Integration tests for hello problem using language adapters (Phase 2).

Tests the complete flow: adapter creation → compilation → execution
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bootcs.check import internal


class TestHelloIntegration(unittest.TestCase):
    """Test hello problem with real compilation and execution."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.checks_dir = (
            Path(__file__).parent.parent.parent.parent / "bootcs-checks" / "cs50" / "hello"
        )
        cls.test_data_dir = Path(__file__).parent.parent / "integration"

        # Verify checks directory exists
        if not cls.checks_dir.exists():
            raise FileNotFoundError(f"Checks directory not found: {cls.checks_dir}")

    def setUp(self):
        """Set up for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Reset internal state
        internal.slug = "cs50/hello"
        internal._current_language = None

    def tearDown(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Clean up compiled files
        for pattern in ["*.class", "a.out", "*.pyc"]:
            for f in Path(self.original_cwd).glob(pattern):
                f.unlink(missing_ok=True)

    def _run_check(self, student_dir: Path, language: str) -> subprocess.CompletedProcess:
        """
        Run bootcs check command.

        Args:
            student_dir: Directory containing student code
            language: Programming language

        Returns:
            CompletedProcess with result
        """
        os.chdir(student_dir)

        # Use sys.executable to ensure we use the same Python interpreter
        cmd = [
            sys.executable,
            "-m",
            "bootcs",
            "check",
            "cs50/hello",
            "-L",
            language,
            "-d",
            str(self.checks_dir.parent.parent),
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        return subprocess.run(cmd, capture_output=True, text=True, env=env)

    def test_hello_c_passes(self):
        """Hello in C should pass all checks."""
        student_dir = self.test_data_dir / "hello-c"
        self.assertTrue(student_dir.exists(), f"Test data not found: {student_dir}")

        result = self._run_check(student_dir, "c")

        # Check output contains success indicators
        self.assertIn(
            "passed",
            result.stdout.lower(),
            f"Expected 'passed' in output. stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Check failed. stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def test_hello_java_passes(self):
        """Hello in Java should pass all checks."""
        student_dir = self.test_data_dir / "hello-java"
        self.assertTrue(student_dir.exists(), f"Test data not found: {student_dir}")

        result = self._run_check(student_dir, "java")

        self.assertIn(
            "passed",
            result.stdout.lower(),
            f"Expected 'passed' in output. stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Check failed. stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def test_hello_python_passes(self):
        """Hello in Python should pass all checks."""
        student_dir = self.test_data_dir / "hello-python"
        self.assertTrue(student_dir.exists(), f"Test data not found: {student_dir}")

        result = self._run_check(student_dir, "python")

        self.assertIn(
            "passed",
            result.stdout.lower(),
            f"Expected 'passed' in output. stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Check failed. stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


class TestAdapterDirectUsage(unittest.TestCase):
    """Test adapters can be used directly in check scripts."""

    def setUp(self):
        """Set up test state."""
        internal.slug = "cs50/hello"
        self.test_data_dir = Path(__file__).parent.parent / "integration"

    def tearDown(self):
        """Clean up."""
        internal._current_language = None

    def test_c_adapter_direct(self):
        """Can create and use C adapter directly."""
        from bootcs.check import create_adapter

        os.chdir(self.test_data_dir / "hello-c")
        internal.set_current_language("c")

        adapter = create_adapter()
        self.assertEqual(adapter.problem, "hello")
        self.assertEqual(adapter.language, "c")
        self.assertTrue(adapter.exists())

    def test_java_adapter_direct(self):
        """Can create and use Java adapter directly."""
        from bootcs.check import create_adapter

        os.chdir(self.test_data_dir / "hello-java")
        internal.set_current_language("java")

        adapter = create_adapter()
        self.assertEqual(adapter.problem, "hello")
        self.assertEqual(adapter.language, "java")
        self.assertTrue(adapter.exists())

    def test_python_adapter_direct(self):
        """Can create and use Python adapter directly."""
        from bootcs.check import create_adapter

        os.chdir(self.test_data_dir / "hello-python")
        internal.set_current_language("python")

        adapter = create_adapter()
        self.assertEqual(adapter.problem, "hello")
        self.assertEqual(adapter.language, "python")
        self.assertTrue(adapter.exists())


if __name__ == "__main__":
    unittest.main()
