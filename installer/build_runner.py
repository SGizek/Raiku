"""
Raiku build runner.

Executes a package's build_command inside its cached source directory.

Security model:
  1. All build commands are checked against FORBIDDEN_BUILD_PATTERNS before execution.
  2. In safe_mode (default), the user is shown the command and must explicitly confirm.
  3. Commands run in an isolated subprocess with a restricted environment.
  4. A configurable timeout prevents runaway builds.
  5. The trust flag system allows bypassing the confirmation prompt for trusted packages.
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional

from core.constants import FORBIDDEN_BUILD_PATTERNS


class BuildError(Exception):
    """Raised when a build command fails or is rejected."""


class BuildRunner:
    """Safely executes package build commands."""

    DEFAULT_TIMEOUT: int = 300  # 5 minutes

    def __init__(
        self,
        safe_mode: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.safe_mode = safe_mode
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        build_command: str,
        cwd: Path,
        package_name: str,
        trusted: bool = False,
        confirm_callback: Optional[callable] = None,
    ) -> int:
        """
        Execute *build_command* in *cwd*.

        Parameters
        ----------
        build_command:
            The raw build command string from raiku.toml.
        cwd:
            Working directory (the cached package directory).
        package_name:
            Human-readable package name for display/error messages.
        trusted:
            If True and safe_mode is enabled, skip confirmation prompt.
        confirm_callback:
            Optional callable(command: str) -> bool. Called in safe_mode
            to ask the user for confirmation. If None, raises BuildError.

        Returns exit code (0 = success).
        Raises BuildError on failure, rejection, or forbidden command.
        """
        self._security_check(build_command, package_name)

        if self.safe_mode and not trusted:
            confirmed = self._request_confirmation(
                build_command, package_name, confirm_callback
            )
            if not confirmed:
                raise BuildError(
                    f"Build command for '{package_name}' was rejected by the user."
                )

        return self._execute(build_command, cwd, package_name)

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def _security_check(self, command: str, package_name: str) -> None:
        """Raise BuildError if any forbidden pattern is found in the command."""
        cmd_lower = command.lower()
        for pattern in FORBIDDEN_BUILD_PATTERNS:
            if pattern.lower() in cmd_lower:
                raise BuildError(
                    f"Build command for '{package_name}' contains a forbidden pattern: "
                    f"'{pattern}'\n"
                    "This package cannot be installed. "
                    "Report this to the Raiku maintainers."
                )

    def _request_confirmation(
        self,
        command: str,
        package_name: str,
        callback: Optional[callable],
    ) -> bool:
        """Ask the user to approve the build command."""
        if callback is not None:
            return callback(command)
        # No callback provided — refuse silently in non-interactive contexts
        raise BuildError(
            f"Safe mode is active for '{package_name}' but no confirmation "
            "callback was provided. Pass --trust flag or disable safe_mode."
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _execute(self, command: str, cwd: Path, package_name: str) -> int:
        """Run the command in a restricted subprocess."""
        # Build a minimal environment — do NOT inherit full user env
        env = self._build_env(cwd)

        # Shell-split on POSIX; on Windows pass as a string through cmd
        if sys.platform == "win32":
            args = command
            use_shell = True
        else:
            try:
                args = shlex.split(command)
                use_shell = False
            except ValueError:
                args = command
                use_shell = True

        try:
            result = subprocess.run(
                args,
                cwd=str(cwd),
                env=env,
                shell=use_shell,
                timeout=self.timeout,
                capture_output=False,  # Let output flow to terminal
            )
        except subprocess.TimeoutExpired:
            raise BuildError(
                f"Build for '{package_name}' timed out after {self.timeout}s."
            )
        except FileNotFoundError as exc:
            raise BuildError(
                f"Build command not found for '{package_name}': {exc}"
            )
        except OSError as exc:
            raise BuildError(
                f"OS error running build for '{package_name}': {exc}"
            )

        if result.returncode != 0:
            raise BuildError(
                f"Build failed for '{package_name}' "
                f"(exit code {result.returncode})."
            )

        return result.returncode

    def _build_env(self, cwd: Path) -> dict[str, str]:
        """
        Construct a minimal, safe environment for build subprocess.
        Inherits PATH, HOME, and a small set of safe variables.
        """
        safe_vars = {
            "PATH", "HOME", "USER", "LOGNAME",
            "LANG", "LC_ALL", "TERM",
            # Windows
            "SYSTEMROOT", "WINDIR", "COMSPEC",
            "USERPROFILE", "APPDATA", "LOCALAPPDATA",
            "TEMP", "TMP",
            # Build tools
            "CARGO_HOME", "RUSTUP_HOME",
            "GOPATH", "GOROOT",
            "JAVA_HOME",
            "DOTNET_ROOT",
            "ZIG_HOME",
        }
        env = {k: v for k, v in os.environ.items() if k in safe_vars}
        # Ensure the package directory is accessible
        env["RAIKU_PKG_DIR"] = str(cwd)
        return env
