"""
Raiku package fetcher.

Downloads only the files needed for a specific package from GitHub's
raw content API. No full repository clone is ever performed.

Files fetched per package:
  - raiku.toml
  - version.yml
  - README.md
  - src/ (all files listed in the package manifest)
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any, Optional

import requests

from core.constants import (
    RAW_BASE_URL,
    RAIKU_TOML,
    VERSION_YML,
    README_MD,
)


class FetchError(Exception):
    """Raised on network or HTTP errors during package fetching."""


class PackageFetcher:
    """Fetches individual package files from the Raiku GitHub repository."""

    STANDARD_FILES: tuple[str, ...] = (RAIKU_TOML, VERSION_YML, README_MD)
    TIMEOUT: int = 30

    def __init__(
        self,
        raw_base_url: str = RAW_BASE_URL,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.raw_base_url = raw_base_url.rstrip("/")
        self.session = session or requests.Session()

    # ------------------------------------------------------------------
    # High-level: fetch everything for a package
    # ------------------------------------------------------------------

    def fetch_package(
        self,
        package_path: str,
        progress_callback: Optional[Any] = None,
    ) -> dict[str, bytes]:
        """
        Fetch all standard files for the package at *package_path*.

        Returns a dict mapping relative filename → raw bytes.
        Raises FetchError on any download failure.
        """
        fetched: dict[str, bytes] = {}
        all_files = list(self.STANDARD_FILES)

        for filename in all_files:
            url = f"{self.raw_base_url}/{package_path}/{filename}"
            try:
                data = self._get(url, progress_callback=progress_callback, label=filename)
                fetched[filename] = data
                if progress_callback:
                    progress_callback(filename)
            except FetchError as exc:
                if filename == README_MD:
                    # README is optional — skip silently
                    continue
                raise FetchError(
                    f"Failed to fetch '{filename}' for package at '{package_path}': {exc}"
                ) from exc

        return fetched

    def fetch_src_file(self, package_path: str, src_filename: str) -> bytes:
        """
        Fetch a single file from the package's src/ directory.
        """
        url = f"{self.raw_base_url}/{package_path}/src/{src_filename}"
        return self._get(url)

    def fetch_src_listing(self, package_path: str) -> list[str]:
        """
        Attempt to retrieve a file listing for the package's src/ directory
        using the GitHub API (not raw).

        Falls back to an empty list if unavailable (caller handles gracefully).
        """
        # Convert raw URL base to API URL
        # raw: https://raw.githubusercontent.com/OWNER/REPO/BRANCH
        # api: https://api.github.com/repos/OWNER/REPO/contents/PATH?ref=BRANCH
        try:
            parts = self.raw_base_url.replace("https://raw.githubusercontent.com/", "")
            owner_repo_branch = parts.split("/", 2)  # OWNER, REPO, BRANCH
            if len(owner_repo_branch) < 3:
                return []
            owner, repo, branch = owner_repo_branch
            api_url = (
                f"https://api.github.com/repos/{owner}/{repo}/contents/"
                f"{package_path}/src?ref={branch}"
            )
            resp = self.session.get(
                api_url,
                timeout=self.TIMEOUT,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if resp.status_code == 200:
                entries = resp.json()
                return [e["name"] for e in entries if e.get("type") == "file"]
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _get(self, url: str, progress_callback: Optional[Any] = None, label: str = "") -> bytes:
        """GET a URL and return its bytes. Raises FetchError on failure.
        Streams response and calls progress_callback(bytes_downloaded, total) if provided."""
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT, stream=True)
        except requests.RequestException as exc:
            raise FetchError(f"Network error fetching {url}: {exc}") from exc

        if resp.status_code == 404:
            raise FetchError(f"Not found (404): {url}")
        if not resp.ok:
            raise FetchError(
                f"HTTP {resp.status_code} fetching {url}: {resp.reason}"
            )

        total = int(resp.headers.get("content-length", 0))
        chunks: list[bytes] = []
        downloaded = 0

        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)
                if progress_callback and callable(progress_callback):
                    # Try calling with (downloaded, total, label) signature
                    try:
                        progress_callback(downloaded, total, label)
                    except TypeError:
                        try:
                            progress_callback(label)
                        except Exception:
                            pass

        return b"".join(chunks)

    def check_reachable(self) -> bool:
        """Return True if the raw base URL is reachable."""
        try:
            resp = self.session.head(self.raw_base_url, timeout=5)
            return resp.ok
        except Exception:
            return False
