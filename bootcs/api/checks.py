"""
Checks Manager - Download and cache checks from remote API.

This module handles:
- Downloading checks from bootcs-api
- Caching checks locally with TTL
- Managing cache lifecycle
"""

import base64
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .client import APIClient, APIError


# Default cache location
DEFAULT_CACHE_DIR = Path.home() / ".bootcs" / "checks"

# Cache TTL: 24 hours
CACHE_TTL = 24 * 60 * 60


class ChecksManager:
    """Manages remote checks download and local caching."""

    def __init__(self, token: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize ChecksManager.

        Args:
            token: Authentication token. Required for non-free stages.
            cache_dir: Custom cache directory. Defaults to ~/.bootcs/checks
        """
        self.api = APIClient(token=token)
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_checks(
        self,
        slug: str,
        language: str = "c",
        force_update: bool = False
    ) -> Path:
        """
        Get checks directory for a stage.

        Downloads from remote API if not cached or cache is stale.
        Uses batch API to download all accessible stages at once for efficiency.

        Args:
            slug: Stage slug in format "course/stage" (e.g., "cs50/hello")
            language: Programming language (default: "c")
            force_update: Force download even if cache is valid

        Returns:
            Path to the local checks directory

        Raises:
            APIError: If download fails (network error, auth required, etc.)
            ValueError: If slug format is invalid
        """
        # Parse slug
        parts = slug.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid slug format: {slug}. Expected 'course/stage'")

        course_slug, stage_slug = parts
        cache_path = self.cache_dir / course_slug / language / stage_slug
        version_file = cache_path / ".version"

        # Check cache validity
        if not force_update and self._is_cache_valid(cache_path, version_file):
            return cache_path

        # Download all checks for this course (batch download is more efficient)
        # This will populate the cache for all accessible stages
        self.get_all_checks(course_slug, language=language, force_update=force_update)

        # Now return the specific stage's cache path
        if not cache_path.exists():
            raise APIError(
                code="STAGE_NOT_FOUND",
                message=f"Stage '{stage_slug}' not found in course '{course_slug}' or not accessible"
            )

        return cache_path

    def get_all_checks(
        self,
        course_slug: str,
        language: str = "c",
        force_update: bool = False
    ) -> Dict[str, Path]:
        """
        Download all accessible checks for a course at once.

        More efficient than downloading stage by stage.

        Args:
            course_slug: Course slug (e.g., "cs50")
            language: Programming language (default: "c")
            force_update: Force download even if cache is valid

        Returns:
            Dict mapping stage_slug to local checks directory path

        Raises:
            APIError: If download fails
        """
        course_cache = self.cache_dir / course_slug / language
        version_file = course_cache / ".course_version"

        # Check if we should use cache
        if not force_update and self._is_course_cache_valid(course_cache, version_file):
            # Return cached stage paths
            return self._get_cached_stages(course_cache)

        # Download all checks from API (batch download)
        response = self.api.get(
            f"/api/courses/{course_slug}/checks",
            params={"language": language}
        )

        # Write each stage to cache
        result = {}
        for stage_checks in response.get("checks", []):
            stage_slug = stage_checks["stageSlug"]
            stage_path = course_cache / stage_slug
            
            self._write_stage_cache(stage_path, stage_checks["files"])
            result[stage_slug] = stage_path

        # Write course version
        version = response.get("version", "unknown")
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text(version)

        return result

    def _download_checks(self, course_slug: str, stage_slug: str, language: str) -> dict:
        """Download checks from API for a single stage."""
        return self.api.get(
            f"/api/courses/{course_slug}/stages/{stage_slug}/checks",
            params={"language": language}
        )

    def _is_cache_valid(self, cache_path: Path, version_file: Path) -> bool:
        """Check if cache exists and is not stale."""
        if not cache_path.exists() or not version_file.exists():
            return False

        # Check age
        try:
            age = time.time() - version_file.stat().st_mtime
            return age < CACHE_TTL
        except OSError:
            return False

    def _is_course_cache_valid(self, course_cache: Path, version_file: Path) -> bool:
        """Check if course-level cache is valid."""
        if not course_cache.exists() or not version_file.exists():
            return False

        try:
            age = time.time() - version_file.stat().st_mtime
            return age < CACHE_TTL
        except OSError:
            return False

    def _get_cached_stages(self, course_cache: Path) -> Dict[str, Path]:
        """Get all cached stage directories for a course."""
        result = {}
        if course_cache.exists():
            for item in course_cache.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    result[item.name] = item
        return result

    def _write_cache(self, cache_path: Path, response: dict, version_file: Path):
        """Write API response to local cache."""
        # Clear existing cache
        if cache_path.exists():
            shutil.rmtree(cache_path)
        cache_path.mkdir(parents=True, exist_ok=True)

        # Write files
        for file_info in response.get("files", []):
            file_path = cache_path / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Decode base64 content
            content = base64.b64decode(file_info["content"])
            file_path.write_bytes(content)

        # Write version
        version = response.get("version", "unknown")
        version_file.write_text(version)

    def _write_stage_cache(self, stage_path: Path, files: List[dict]):
        """Write files for a single stage to cache."""
        # Clear existing
        if stage_path.exists():
            shutil.rmtree(stage_path)
        stage_path.mkdir(parents=True, exist_ok=True)

        # Write files
        for file_info in files:
            file_path = stage_path / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)

            content = base64.b64decode(file_info["content"])
            file_path.write_bytes(content)

        # Write version marker
        (stage_path / ".version").write_text(str(time.time()))

    def clear_cache(self, slug: Optional[str] = None, language: Optional[str] = None):
        """
        Clear cached checks.

        Args:
            slug: Optional. Clear cache for specific course or course/stage.
                  If None, clears all cache.
            language: Optional. Clear only cache for specific language.
        """
        if slug is None:
            # Clear all cache
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            return

        parts = slug.split("/")

        if len(parts) == 1:
            # Course-level clear
            course_slug = parts[0]
            if language:
                cache_path = self.cache_dir / course_slug / language
            else:
                cache_path = self.cache_dir / course_slug
        elif len(parts) == 2:
            # Stage-level clear
            course_slug, stage_slug = parts
            if language:
                cache_path = self.cache_dir / course_slug / language / stage_slug
            else:
                # Clear all languages for this stage
                course_path = self.cache_dir / course_slug
                if course_path.exists():
                    for lang_dir in course_path.iterdir():
                        if lang_dir.is_dir():
                            stage_path = lang_dir / stage_slug
                            if stage_path.exists():
                                shutil.rmtree(stage_path)
                return
        else:
            raise ValueError(f"Invalid slug format: {slug}")

        if cache_path.exists():
            shutil.rmtree(cache_path)

    def list_cache(self) -> List[Dict[str, str]]:
        """
        List all cached checks.

        Returns:
            List of dicts with keys: course, language, stage, version, age
        """
        result = []

        if not self.cache_dir.exists():
            return result

        for course_dir in self.cache_dir.iterdir():
            if not course_dir.is_dir() or course_dir.name.startswith("."):
                continue

            for lang_dir in course_dir.iterdir():
                if not lang_dir.is_dir() or lang_dir.name.startswith("."):
                    continue

                for stage_dir in lang_dir.iterdir():
                    if not stage_dir.is_dir() or stage_dir.name.startswith("."):
                        continue

                    version_file = stage_dir / ".version"
                    version = "unknown"
                    age = "unknown"

                    if version_file.exists():
                        try:
                            version = version_file.read_text().strip()
                            age_secs = time.time() - version_file.stat().st_mtime
                            if age_secs < 60:
                                age = f"{int(age_secs)}s"
                            elif age_secs < 3600:
                                age = f"{int(age_secs / 60)}m"
                            elif age_secs < 86400:
                                age = f"{int(age_secs / 3600)}h"
                            else:
                                age = f"{int(age_secs / 86400)}d"
                        except OSError:
                            pass

                    result.append({
                        "course": course_dir.name,
                        "language": lang_dir.name,
                        "stage": stage_dir.name,
                        "version": version[:8] if len(version) > 8 else version,
                        "age": age,
                    })

        return result


def get_checks_manager(token: Optional[str] = None) -> ChecksManager:
    """
    Get a ChecksManager instance.

    Convenience function that loads token from credentials if not provided.

    Args:
        token: Optional authentication token.

    Returns:
        ChecksManager instance.
    """
    if token is None:
        try:
            from ..auth import get_token, is_logged_in
            if is_logged_in():
                token = get_token()
        except ImportError:
            pass

    return ChecksManager(token=token)
