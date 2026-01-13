"""
Naming conventions for different programming languages.

Defines how source files should be named based on problem name and language.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

from pathlib import Path
from typing import Callable, Dict, Optional


def c_convention(problem: str) -> str:
    """
    C naming convention: lowercase with .c extension.

    Examples:
        hello -> hello.c
        mario-less -> mario-less.c
        fizz-buzz -> fizz-buzz.c
    """
    return f"{problem}.c"


def cpp_convention(problem: str) -> str:
    """
    C++ naming convention: lowercase with .cpp extension.

    Examples:
        hello -> hello.cpp
        mario-less -> mario-less.cpp
    """
    return f"{problem}.cpp"


def java_convention(problem: str) -> str:
    """
    Java naming convention: PascalCase with .java extension.

    Examples:
        hello -> Hello.java
        mario-less -> MarioLess.java
        fizz-buzz -> FizzBuzz.java
    """
    # Convert kebab-case to PascalCase
    parts = problem.split("-")
    class_name = "".join(word.capitalize() for word in parts)
    return f"{class_name}.java"


def python_convention(problem: str) -> str:
    """
    Python naming convention: lowercase with .py extension.

    Examples:
        hello -> hello.py
        mario-less -> mario-less.py
        fizz-buzz -> fizz-buzz.py
    """
    return f"{problem}.py"


def go_convention(problem: str) -> str:
    """
    Go naming convention: lowercase with .go extension.

    Examples:
        hello -> hello.go
        mario-less -> mario-less.go
    """
    return f"{problem}.go"


def rust_convention(problem: str) -> str:
    """
    Rust naming convention: lowercase with .rs extension.

    Examples:
        hello -> hello.rs
        mario-less -> mario-less.rs
    """
    return f"{problem}.rs"


def javascript_convention(problem: str) -> str:
    """
    JavaScript naming convention: lowercase with .js extension.

    Examples:
        hello -> hello.js
        mario-less -> mario-less.js
    """
    return f"{problem}.js"


def typescript_convention(problem: str) -> str:
    """
    TypeScript naming convention: lowercase with .ts extension.

    Examples:
        hello -> hello.ts
        mario-less -> mario-less.ts
    """
    return f"{problem}.ts"


# Registry of naming conventions by language
NAMING_CONVENTIONS: Dict[str, Callable[[str], str]] = {
    "c": c_convention,
    "cpp": cpp_convention,
    "c++": cpp_convention,
    "java": java_convention,
    "python": python_convention,
    "py": python_convention,
    "go": go_convention,
    "rust": rust_convention,
    "rs": rust_convention,
    "javascript": javascript_convention,
    "js": javascript_convention,
    "typescript": typescript_convention,
    "ts": typescript_convention,
}


def get_source_filename(problem: str, language: str) -> str:
    """
    Get the expected source filename for a problem in a given language.

    Args:
        problem: Problem name (e.g., "hello", "mario-less")
        language: Programming language (e.g., "c", "java", "python")

    Returns:
        Expected filename (e.g., "hello.c", "Hello.java", "hello.py")

    Raises:
        ValueError: If language is not supported

    Examples:
        >>> get_source_filename("hello", "c")
        'hello.c'
        >>> get_source_filename("hello", "java")
        'Hello.java'
        >>> get_source_filename("mario-less", "java")
        'MarioLess.java'
    """
    language_lower = language.lower()

    if language_lower not in NAMING_CONVENTIONS:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {', '.join(sorted(set(NAMING_CONVENTIONS.keys())))}"
        )

    convention = NAMING_CONVENTIONS[language_lower]
    return convention(problem)


def find_source_file(problem: str, language: str, search_dir: Optional[Path] = None) -> Path:
    """
    Find the source file for a problem in a given language.

    Args:
        problem: Problem name (e.g., "hello")
        language: Programming language (e.g., "c", "java")
        search_dir: Directory to search in (defaults to current directory)

    Returns:
        Path to the source file

    Raises:
        FileNotFoundError: If source file doesn't exist

    Examples:
        >>> find_source_file("hello", "c")
        Path('hello.c')
    """
    if search_dir is None:
        search_dir = Path.cwd()

    filename = get_source_filename(problem, language)
    filepath = search_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Source file not found: {filename} (expected in {search_dir})")

    return filepath
