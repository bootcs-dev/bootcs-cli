"""
Unit tests for java module.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Skip all tests if Java is not installed
pytestmark = pytest.mark.skipif(
    not shutil.which("javac") or not shutil.which("java"), reason="Java JDK not installed"
)


class TestJavaCompile:
    """Test java.compile() function."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_compile_simple(self):
        """Test compiling a simple Java file."""
        from bootcs.check import java

        # Create a simple Java file
        with open("Hello.java", "w") as f:
            f.write("""
public class Hello {
    public static void main(String[] args) {
        System.out.println("hello, world");
    }
}
""")

        # Should compile without error
        java.compile("Hello.java")

        # Check .class file was created
        assert os.path.exists("Hello.class")

    def test_compile_error(self):
        """Test compilation failure."""
        from bootcs.check import java
        from bootcs.check._api import Failure

        # Create a Java file with syntax error
        with open("Bad.java", "w") as f:
            f.write("""
public class Bad {
    public static void main(String[] args) {
        System.out.println("missing semicolon")
    }
}
""")

        # Should raise Failure
        with pytest.raises(Failure):
            java.compile("Bad.java")

    def test_compile_file_not_exists(self):
        """Test compilation of non-existent file."""
        from bootcs.check import java
        from bootcs.check._api import Failure

        with pytest.raises(Failure):
            java.compile("NotExist.java")


class TestJavaRun:
    """Test java.run() function."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        # Create and compile a test Java file
        with open("Hello.java", "w") as f:
            f.write("""
import java.util.Scanner;

public class Hello {
    public static void main(String[] args) {
        if (args.length > 0) {
            System.out.println("hello, " + args[0]);
        } else {
            Scanner scanner = new Scanner(System.in);
            System.out.print("What is your name? ");
            String name = scanner.nextLine();
            System.out.println("hello, " + name);
            scanner.close();
        }
    }
}
""")
        os.system("javac Hello.java")

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_run_simple(self):
        """Test running a simple Java program."""
        from bootcs.check import java

        proc = java.run("Hello", "World")
        proc.stdout("hello, World")

    def test_run_with_stdin(self):
        """Test running Java program with stdin."""
        from bootcs.check import java

        proc = java.run("Hello")
        proc.stdin("David")
        proc.stdout("hello, David")


class TestJavaClean:
    """Test java.clean() function."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_class_files(self):
        """Test cleaning .class files."""
        from bootcs.check import java

        # Create some .class files
        Path("Hello.class").touch()
        Path("World.class").touch()

        assert os.path.exists("Hello.class")
        assert os.path.exists("World.class")

        java.clean()

        assert not os.path.exists("Hello.class")
        assert not os.path.exists("World.class")


class TestJavaVersion:
    """Test java.version() function."""

    def test_version(self):
        """Test getting Java version."""
        from bootcs.check import java

        java_ver, javac_ver = java.version()

        # Should return non-empty strings
        assert java_ver
        assert javac_ver
