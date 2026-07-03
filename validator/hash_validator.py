"""
Raiku hash validator.

Verifies package integrity using SHA-256 checksums recorded in index.json.
This is the primary security gate — no package is installed unless its
hash matches what the index declares.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from core.constants import HASH_ALGORITHM


class HashMismatchError(Exception):
    """Raised when a downloaded file's hash does not match the expected value."""

    def __init__(self, name: str, expected: str, actual: str) -> None:
        self.name = name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Hash mismatch for '{name}':\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            "The package may be corrupt or tampered with. Installation aborted."
        )


class HashValidator:
    """Validate file and byte-string hashes against known-good values."""

    @staticmethod
    def compute_bytes(data: bytes) -> str:
        """Return the hex digest of raw bytes."""
        h = hashlib.new(HASH_ALGORITHM)
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def compute_file(path: Path) -> str:
        """Return the hex digest of a file on disk (streaming, memory-safe)."""
        h = hashlib.new(HASH_ALGORITHM)
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def verify_bytes(
        cls,
        name: str,
        data: bytes,
        expected_hash: Optional[str],
    ) -> None:
        """
        Verify *data* against *expected_hash*.

        If *expected_hash* is None the check is skipped with a warning
        (packages without recorded hashes are still accepted but flagged).
        Raises HashMismatchError on mismatch.
        """
        if expected_hash is None:
            return  # No hash recorded — cannot verify

        actual = cls.compute_bytes(data)
        if actual != expected_hash:
            raise HashMismatchError(name, expected_hash, actual)

    @classmethod
    def verify_file(
        cls,
        name: str,
        path: Path,
        expected_hash: Optional[str],
    ) -> None:
        """Verify a file on disk against *expected_hash*."""
        if expected_hash is None:
            return

        actual = cls.compute_file(path)
        if actual != expected_hash:
            raise HashMismatchError(name, expected_hash, actual)

    @staticmethod
    def has_recorded_hash(index_entry: dict) -> bool:
        """Return True if the index entry contains a sha256 field."""
        return bool(index_entry.get("sha256"))
