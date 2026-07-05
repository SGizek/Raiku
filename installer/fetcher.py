"""
Raiku package fetcher.

Downloads only the files needed for a specific package from GitHub's
raw content API. No full repository clone is ever performed.

Files fetched per package:
  - raiku.toml
  - version.yml
  - README.md

Features:
  - Resumable downloads via HTTP Range headers
  - Exponential-backoff retry on transient network errors
  - Parallel multi-file fetching via concurrent.futures
"""
from __future__ import annotations

import time
import concurrent.futures
from pathlib import Path
from typing import Any, Optional

import requests

from core.constants import (
    RAW_BASE_URL,
    RAIKU_TOML,
    VERSION_YML,
    README_MD,
    CACHE_DIR,
)


class FetchError(Exception):
    """Raised on network or HTTP errors during package fetching."""


class PackageFetcher:
    """Fetches individual package files from the Raiku GitHub repository."""

    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 1.5   # seconds; doubles each retry

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
        parallel: bool = True,
    ) -> dict[str, bytes]:
        """
        Fetch all standard files for the package at *package_path*.

        When *parallel* is True (default), all files are fetched concurrently.
        Returns a dict mapping relative filename → raw bytes.
        Raises FetchError on any non-optional download failure.
        """
        all_files = list(self.STANDARD_FILES)

        if parallel:
            return self._fetch_parallel(package_path, all_files, progress_callback)
        else:
            return self._fetch_sequential(package_path, all_files, progress_callback)

    def _fetch_parallel(
        self,
        package_path: str,
        filenames: list[str],
        progress_callback: Optional[Any],
    ) -> dict[str, bytes]:
        """Fetch files concurrently using a thread pool."""
        fetched: dict[str, bytes] = {}

        def _fetch_one(filename: str) -> tuple[str, bytes | None]:
            url = f"{self.raw_base_url}/{package_path}/{filename}"
            try:
                data = self._get_with_retry(url, progress_callback=progress_callback,
                                            label=filename)
                return filename, data
            except FetchError:
                if filename == README_MD:
                    return filename, None  # optional
                raise

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_fetch_one, f): f for f in filenames}
            for future in concurrent.futures.as_completed(futures):
                filename, data = future.result()
                if data is not None:
                    fetched[filename] = data

        return fetched

    def _fetch_sequential(
        self,
        package_path: str,
        filenames: list[str],
        progress_callback: Optional[Any],
    ) -> dict[str, bytes]:
        """Fetch files one at a time (fallback)."""
        fetched: dict[str, bytes] = {}
        for filename in filenames:
            url = f"{self.raw_base_url}/{package_path}/{filename}"
            try:
                data = self._get_with_retry(url, progress_callback=progress_callback,
                                            label=filename)
                fetched[filename] = data
            except FetchError as exc:
                if filename == README_MD:
                    continue
                raise FetchError(
                    f"Failed to fetch '{filename}' for '{package_path}': {exc}"
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
    # Low-level HTTP — with resumable download support
    # ------------------------------------------------------------------

    def _get_with_retry(
        self,
        url: str,
        progress_callback: Optional[Any] = None,
        label: str = "",
    ) -> bytes:
        """
        Fetch *url* with exponential-backoff retry on transient errors.
        Raises FetchError after MAX_RETRIES failed attempts.
        """
        last_exc: Exception | None = None
        delay = self.RETRY_BACKOFF

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return self._get(url, progress_callback=progress_callback, label=label)
            except FetchError as exc:
                # 404 is definitive — no point retrying
                if "404" in str(exc):
                    raise
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    time.sleep(delay)
                    delay *= 2

        raise FetchError(
            f"Failed after {self.MAX_RETRIES} attempts: {last_exc}"
        ) from last_exc

    def _get(self, url: str, progress_callback: Optional[Any] = None, label: str = "") -> bytes:
        """GET a URL, streaming with optional progress. Raises FetchError on failure."""
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT, stream=True)
        except requests.RequestException as exc:
            raise FetchError(f"Network error fetching {url}: {exc}") from exc

        if resp.status_code == 404:
            raise FetchError(f"Not found (404): {url}")
        if not resp.ok:
            raise FetchError(f"HTTP {resp.status_code} fetching {url}: {resp.reason}")

        total = int(resp.headers.get("content-length", 0))
        chunks: list[bytes] = []
        downloaded = 0

        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)
                if progress_callback and callable(progress_callback):
                    try:
                        progress_callback(downloaded, total, label)
                    except TypeError:
                        try:
                            progress_callback(label)
                        except Exception:
                            pass

        return b"".join(chunks)

    def _get_resumable(
        self,
        url: str,
        dest: Path,
        progress_callback: Optional[Any] = None,
        label: str = "",
    ) -> bytes:
        """
        Download *url* to *dest* with resume support.

        If a partial file exists at dest.with_suffix('.partial'), resumes
        from where it left off using the HTTP Range header.
        Returns the complete bytes and writes them to *dest*.
        """
        partial = dest.with_suffix(dest.suffix + ".partial")
        resume_pos = partial.stat().st_size if partial.exists() else 0

        headers: dict[str, str] = {}
        if resume_pos > 0:
            headers["Range"] = f"bytes={resume_pos}-"

        try:
            resp = self.session.get(
                url, headers=headers, timeout=self.TIMEOUT, stream=True
            )
        except requests.RequestException as exc:
            raise FetchError(f"Network error fetching {url}: {exc}") from exc

        # 206 = partial content (resume), 200 = full (server ignored Range)
        if resp.status_code == 404:
            raise FetchError(f"Not found (404): {url}")
        if resp.status_code not in (200, 206):
            raise FetchError(f"HTTP {resp.status_code} fetching {url}: {resp.reason}")

        if resp.status_code == 200:
            # Server didn't honour Range — restart from scratch
            resume_pos = 0
            if partial.exists():
                partial.unlink()

        total = int(resp.headers.get("content-length", 0)) + resume_pos
        downloaded = resume_pos

        dest.parent.mkdir(parents=True, exist_ok=True)
        mode = "ab" if resume_pos > 0 else "wb"

        with open(partial, mode) as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and callable(progress_callback):
                        try:
                            progress_callback(downloaded, total, label)
                        except TypeError:
                            try:
                                progress_callback(label)
                            except Exception:
                                pass

        # Rename .partial → final destination
        partial.replace(dest)
        return dest.read_bytes()

    def check_reachable(self) -> bool:
        """Return True if the raw base URL is reachable."""
        try:
            resp = self.session.head(self.raw_base_url, timeout=5)
            return resp.ok
        except Exception:
            return False
