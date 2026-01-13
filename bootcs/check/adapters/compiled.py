"""
Compiled language adapter for bootcs check system.

Provides adapters for compiled languages (C, C++, Java) that use
convention-based source file naming.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

from pathlib import Path
from typing import Optional

from .. import c, internal, java
from .base import LanguageAdapter
from .conventions import find_source_file


class CompiledLanguageAdapter(LanguageAdapter):
    """
    Adapter for compiled languages using naming conventions.

    This adapter uses the language-specific naming conventions to find
    source files and delegates to the appropriate language module for
    compilation and execution.

    Supported languages:
        - C: uses bootcs.check.c module
        - Java: uses bootcs.check.java module
    """

    def __init__(self, problem: str, language: Optional[str] = None):
        """
        Initialize compiled language adapter.

        Args:
            problem: Problem name (e.g., "hello", "mario-less")
            language: Programming language (e.g., "c", "java")
                     If None, will attempt to detect from internal state
        """
        # Get language from internal state if not provided
        if language is None:
            language = internal.get_current_language()

        if language is None:
            raise ValueError(
                "Language not specified and could not be detected. "
                "Either pass language parameter or ensure "
                "internal.set_current_language() was called."
            )

        super().__init__(problem, language)

    def _detect_language(self) -> str:
        """
        Detect language from internal state.

        Returns:
            Language string from internal state
        """
        lang = internal.get_current_language()
        if lang is None:
            raise ValueError("Language not set in internal state")
        return lang

    def get_source_file(self) -> Path:
        """
        Get the source file path using naming conventions.

        Returns:
            Path to source file (e.g., hello.c, Hello.java)

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        return find_source_file(self.problem, self.language)

    def compile(self, *args, **kwargs) -> Optional[object]:
        """
        Compile the source code using language-specific compiler.

        For C: delegates to bootcs.check.c.compile()
        For Java: delegates to bootcs.check.java.compile()

        Args:
            *args: Additional compilation arguments
            **kwargs: Additional compilation options

        Raises:
            CompileError: If compilation fails
        """
        source_file = self.get_source_file()

        if self.language == "c":
            # Use existing C compilation
            return c.compile(str(source_file), *args, **kwargs)
        elif self.language == "java":
            # Use existing Java compilation
            return java.compile(str(source_file), *args, **kwargs)
        else:
            raise NotImplementedError(
                f"Compilation not yet implemented for language: {self.language}"
            )

    def run(self, *args, stdin=None, **kwargs) -> object:
        """
        Run the compiled program.

        For C: executes the compiled binary
        For Java: delegates to bootcs.check.java.run()

        Args:
            *args: Command-line arguments to pass to program
            stdin: Standard input to provide
            **kwargs: Additional execution options

        Returns:
            Execution result from language-specific runner
        """
        source_file = self.get_source_file()

        if self.language == "c":
            # For C, the binary is named after the source file (without extension)
            # e.g., hello.c -> hello
            from .. import _api

            exe_name = source_file.stem
            # Build command string with arguments
            command = f"./{exe_name}"
            if args:
                command += " " + " ".join(str(arg) for arg in args)
            return _api.run(command)
        elif self.language == "java":
            # Use existing Java runner
            return java.run(str(source_file), *args)
        else:
            raise NotImplementedError(
                f"Execution not yet implemented for language: {self.language}"
            )


class InterpretedLanguageAdapter(LanguageAdapter):
    """
    Adapter for interpreted languages (Python, JavaScript, etc.)

    These languages don't need compilation but still use naming conventions.
    """

    def __init__(self, problem: str, language: Optional[str] = None):
        """
        Initialize interpreted language adapter.

        Args:
            problem: Problem name
            language: Programming language (defaults to internal state)
        """
        if language is None:
            language = internal.get_current_language()

        if language is None:
            raise ValueError("Language not specified and could not be detected")

        super().__init__(problem, language)

    def _detect_language(self) -> str:
        """Detect language from internal state."""
        lang = internal.get_current_language()
        if lang is None:
            raise ValueError("Language not set in internal state")
        return lang

    def get_source_file(self) -> Path:
        """Get source file path using naming conventions."""
        return find_source_file(self.problem, self.language)

    def compile(self, *args, **kwargs):
        """
        No-op for interpreted languages.

        Some interpreted languages might do syntax checking here.
        """
        # For Python, we could optionally check syntax
        if self.language == "python":
            self.get_source_file()
            # Optionally: py_compile.compile(source_file, doraise=True)
            pass

    def run(self, *args, stdin=None, **kwargs) -> object:
        """
        Run the interpreted program.

        Args:
            *args: Command-line arguments
            stdin: Standard input
            **kwargs: Execution options

        Returns:
            Execution result
        """
        source_file = self.get_source_file()

        if self.language in ("python", "py"):
            from .. import _api

            # Build command string with arguments
            command = f"python3 {source_file}"
            if args:
                command += " " + " ".join(str(arg) for arg in args)
            return _api.run(command)
        elif self.language in ("javascript", "js"):
            from .. import _api

            command = f"node {source_file}"
            if args:
                command += " " + " ".join(str(arg) for arg in args)
            return _api.run(command)
        else:
            raise NotImplementedError(
                f"Execution not yet implemented for language: {self.language}"
            )
