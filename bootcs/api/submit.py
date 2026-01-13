"""
Submit functionality for bootcs CLI.

Handles file collection, encoding, and submission to API.
"""

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import APIClient


@dataclass
class SubmitFile:
    """A file to be submitted."""

    path: str  # Relative path
    content: str  # Base64 encoded content
    size: int  # Original size in bytes


@dataclass
class SubmitResult:
    """Result of a submission."""

    submission_id: str
    status: str
    short_hash: str
    created_at: str
    message: Optional[str] = None


def collect_files(
    file_paths: List[str],
    root: Optional[Path] = None,
    max_file_size: int = 1024 * 1024,  # 1MB
    max_total_size: int = 10 * 1024 * 1024,  # 10MB
) -> List[SubmitFile]:
    """
    Collect and encode files for submission.

    Args:
        file_paths: List of file paths to collect (relative to root)
        root: Root directory (defaults to cwd)
        max_file_size: Maximum size per file in bytes
        max_total_size: Maximum total size in bytes

    Returns:
        List of SubmitFile objects.

    Raises:
        ValueError: If file validation fails.
    """
    if root is None:
        root = Path.cwd()

    files = []
    total_size = 0

    for file_path in file_paths:
        full_path = root / file_path

        if not full_path.exists():
            raise ValueError(f"File not found: {file_path}")

        if not full_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Check file size
        size = full_path.stat().st_size
        if size > max_file_size:
            raise ValueError(f"File too large: {file_path} ({size} bytes, max {max_file_size})")

        total_size += size
        if total_size > max_total_size:
            raise ValueError(f"Total size exceeds limit ({total_size} bytes, max {max_total_size})")

        # Read and encode file
        try:
            content = full_path.read_bytes()
            encoded = base64.b64encode(content).decode("ascii")
        except Exception as e:
            raise ValueError(f"Failed to read file {file_path}: {e}")

        files.append(
            SubmitFile(
                path=file_path,
                content=encoded,
                size=size,
            )
        )

    return files


def submit_files(
    slug: str,
    files: List[SubmitFile],
    token: str,
    message: Optional[str] = None,
    language: Optional[str] = None,
) -> SubmitResult:
    """
    Submit files to bootcs API.

    Args:
        slug: The submission slug (e.g., "cs50/hello")
        files: List of files to submit
        token: Authentication token
        message: Optional commit message
        language: Optional language (auto-detected from files if not provided)

    Returns:
        SubmitResult with submission details.

    Raises:
        APIError: If the submission fails.
    """
    client = APIClient(token=token)

    # Prepare request data
    request_data: Dict[str, Any] = {
        "slug": slug,
        "files": [{"path": f.path, "content": f.content} for f in files],
    }

    if message:
        request_data["message"] = message

    if language:
        request_data["language"] = language

    # Make request
    response = client.post("/api/submit", request_data)

    return SubmitResult(
        submission_id=response["submissionId"],
        status=response["status"],
        short_hash=response["shortHash"],
        created_at=response["createdAt"],
        message=response.get("message"),
    )


def get_submission_status(
    submission_id: str,
    token: str,
) -> Dict[str, Any]:
    """
    Get the status of a submission.

    Args:
        submission_id: The submission ID
        token: Authentication token

    Returns:
        Submission status data.

    Raises:
        APIError: If the request fails.
    """
    client = APIClient(token=token)
    response = client.get(f"/api/submissions/{submission_id}")
    return response
