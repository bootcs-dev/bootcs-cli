"""
Base language adapter for bootcs check system.

Provides the abstract interface that all language adapters must implement.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class LanguageAdapter(ABC):
    """
    Abstract base class for language adapters.

    Each language adapter abstracts the details of compiling, running,
    and testing programs in a specific programming language.

    Attributes:
        problem (str): The problem name (e.g., "hello", "mario-less")
        language (str): The programming language (e.g., "c", "python", "java")
    """

    def __init__(self, problem: str, language: Optional[str] = None):
        """
        Initialize the language adapter.

        Args:
            problem: Problem name (e.g., "hello")
            language: Programming language (auto-detected if None)
        """
        self.problem = problem
        self.language = language or self._detect_language()

    @abstractmethod
    def _detect_language(self) -> str:
        """
        Detect the programming language from available files.

        Returns:
            Detected language string (e.g., "c", "python", "java")
        """
        pass

    @abstractmethod
    def get_source_file(self) -> Path:
        """
        Get the main source file path for this problem.

        Returns:
            Path to the source file (e.g., hello.c, Hello.java, hello.py)

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        pass

    @abstractmethod
    def compile(self, *args, **kwargs) -> Optional[object]:
        """
        Compile the source code (if needed for this language).

        For interpreted languages, this may be a no-op or perform validation.
        For compiled languages, this compiles the source to executable/bytecode.

        Args:
            *args: Language-specific compilation arguments
            **kwargs: Language-specific compilation options

        Raises:
            CompileError: If compilation fails

        Returns:
            Optional process object for validation languages
        """
        pass

    @abstractmethod
    def run(self, *args, stdin=None, **kwargs) -> object:
        """
        Run the compiled/interpreted program.

        Args:
            *args: Command-line arguments to pass to the program
            stdin: Standard input to provide to the program
            **kwargs: Language-specific execution options

        Returns:
            The result object from the execution (depends on implementation)
        """
        pass

    def exists(self) -> bool:
        """
        Check if the source file exists.

        Returns:
            True if source file exists, False otherwise
        """
        try:
            source = self.get_source_file()
            return source.exists()
        except FileNotFoundError:
            return False

    def require_exists(self):
        """
        Ensure source file exists, raise Failure if not.

        This is a convenience method for check implementations.
        Instead of: if not adapter.exists(): raise Failure(...)
        Use: adapter.require_exists()

        Raises:
            Failure: If source file doesn't exist
        """
        from .. import Failure

        if not self.exists():
            raise Failure("Expected source file")

    def __repr__(self):
        """String representation of the adapter."""
        return f"{self.__class__.__name__}(problem={self.problem!r}, language={self.language!r})"
