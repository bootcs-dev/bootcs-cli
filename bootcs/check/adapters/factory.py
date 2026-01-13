"""
Factory function for creating language adapters.

Provides the main entry point for creating language-specific adapters
with automatic detection and convention-based configuration.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

from typing import Optional

from .. import internal
from .base import LanguageAdapter
from .compiled import CompiledLanguageAdapter, InterpretedLanguageAdapter

# Mapping of languages to their adapter types
COMPILED_LANGUAGES = {"c", "cpp", "c++", "java"}
INTERPRETED_LANGUAGES = {"python", "py", "javascript", "js", "typescript", "ts"}


def create_adapter(
    problem: Optional[str] = None, language: Optional[str] = None, adapter_type: str = "auto"
) -> LanguageAdapter:
    """
    Create a language adapter for the given problem.

    This is the main entry point for using language adapters in checks.
    It automatically detects the problem name and language if not provided,
    and returns the appropriate adapter type.

    Args:
        problem: Problem name (e.g., "hello", "mario-less")
                If None, extracts from internal.slug
        language: Programming language (e.g., "c", "java", "python")
                 If None, uses internal.get_current_language()
        adapter_type: Type of adapter to create:
                     - 'auto': Automatically choose based on language (default)
                     - 'compiled': Force CompiledLanguageAdapter
                     - 'interpreted': Force InterpretedLanguageAdapter

    Returns:
        Appropriate LanguageAdapter instance for the problem and language

    Raises:
        ValueError: If problem or language cannot be determined

    Examples:
        >>> # Simple usage (auto-detection)
        >>> adapter = create_adapter()  # Uses internal state

        >>> # Explicit problem name
        >>> adapter = create_adapter("hello")

        >>> # Explicit language
        >>> adapter = create_adapter("hello", language="java")

        >>> # Force adapter type
        >>> adapter = create_adapter("hello", language="python", adapter_type="interpreted")
    """
    # Auto-detect problem name from internal slug if not provided
    if problem is None:
        problem = internal.get_problem_name()
        if problem is None:
            raise ValueError(
                "Problem name not specified and could not be detected from slug. "
                "Either pass problem parameter or ensure internal.slug is set."
            )

    # Auto-detect language from internal state if not provided
    if language is None:
        language = internal.get_current_language()
        if language is None:
            raise ValueError(
                "Language not specified and could not be detected. "
                "Either pass language parameter or ensure "
                "internal.set_current_language() was called."
            )

    language = language.lower()

    # Determine adapter type
    if adapter_type == "auto":
        if language in COMPILED_LANGUAGES:
            adapter_type = "compiled"
        elif language in INTERPRETED_LANGUAGES:
            adapter_type = "interpreted"
        else:
            # Default to compiled for unknown languages
            adapter_type = "compiled"

    # Create and return appropriate adapter
    if adapter_type == "compiled":
        return CompiledLanguageAdapter(problem, language)
    elif adapter_type == "interpreted":
        return InterpretedLanguageAdapter(problem, language)
    else:
        raise ValueError(
            f"Invalid adapter_type: {adapter_type}. Must be 'auto', 'compiled', or 'interpreted'"
        )


def get_adapter_for_language(language: str) -> type:
    """
    Get the adapter class for a specific language.

    Args:
        language: Programming language name

    Returns:
        Adapter class (CompiledLanguageAdapter or InterpretedLanguageAdapter)

    Examples:
        >>> AdapterClass = get_adapter_for_language("java")
        >>> adapter = AdapterClass("hello", "java")
    """
    language = language.lower()

    if language in COMPILED_LANGUAGES:
        return CompiledLanguageAdapter
    elif language in INTERPRETED_LANGUAGES:
        return InterpretedLanguageAdapter
    else:
        # Default to compiled
        return CompiledLanguageAdapter


def is_compiled_language(language: str) -> bool:
    """
    Check if a language is compiled.

    Args:
        language: Programming language name

    Returns:
        True if language is compiled, False if interpreted

    Examples:
        >>> is_compiled_language("c")
        True
        >>> is_compiled_language("python")
        False
    """
    return language.lower() in COMPILED_LANGUAGES


def is_interpreted_language(language: str) -> bool:
    """
    Check if a language is interpreted.

    Args:
        language: Programming language name

    Returns:
        True if language is interpreted, False if compiled

    Examples:
        >>> is_interpreted_language("python")
        True
        >>> is_interpreted_language("java")
        False
    """
    return language.lower() in INTERPRETED_LANGUAGES
