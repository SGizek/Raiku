"""
Raiku global constants.

All path, URL, and ecosystem-wide constants are defined here.
Never hard-code these values anywhere else in the codebase.
"""
import os
from pathlib import Path

# -------------------------------------------------------------------
# Filesystem layout
# -------------------------------------------------------------------
RAIKU_HOME: Path = Path(os.environ.get("RAIKU_HOME", Path.home() / ".raiku"))
CACHE_DIR: Path = RAIKU_HOME / "cache"
INDEX_CACHE_PATH: Path = RAIKU_HOME / "index.json"
CONFIG_PATH: Path = RAIKU_HOME / "config.toml"
TRUST_DB_PATH: Path = RAIKU_HOME / "trusted.json"

# -------------------------------------------------------------------
# Remote locations
# -------------------------------------------------------------------
REPO_OWNER: str = "SGizek"
REPO_NAME: str = "Raiku"
REPO_BASE_URL: str = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
RAW_BASE_URL: str = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"
INDEX_URL: str = f"{RAW_BASE_URL}/index/index.json"

# Individual package file URLs — format with package_path
RAIKU_TOML_URL: str = RAW_BASE_URL + "/{package_path}/raiku.toml"
VERSION_YML_URL: str = RAW_BASE_URL + "/{package_path}/version.yml"
README_URL: str = RAW_BASE_URL + "/{package_path}/README.md"

# -------------------------------------------------------------------
# Ecosystem
# -------------------------------------------------------------------
SUPPORTED_LANGUAGES: list[str] = [
    "Python",
    "Rust",
    "C",
    "CPP",
    "Zig",
    "Java",
    "CSharp",
    "Go",
]

LANGUAGE_ALIASES: dict[str, str] = {
    "python": "Python",
    "py": "Python",
    "rust": "Rust",
    "rs": "Rust",
    "c": "C",
    "cpp": "CPP",
    "c++": "CPP",
    "zig": "Zig",
    "java": "Java",
    "csharp": "CSharp",
    "c#": "CSharp",
    "cs": "CSharp",
    "go": "Go",
    "golang": "Go",
}

# -------------------------------------------------------------------
# Package manifest filenames
# -------------------------------------------------------------------
RAIKU_TOML: str = "raiku.toml"
VERSION_YML: str = "version.yml"
README_MD: str = "README.md"
SRC_DIR: str = "src"

REQUIRED_FILES: tuple[str, ...] = (RAIKU_TOML, VERSION_YML, README_MD, SRC_DIR)

# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------
HASH_ALGORITHM: str = "sha256"

# Build commands that are explicitly forbidden (security blocklist)
FORBIDDEN_BUILD_PATTERNS: list[str] = [
    "rm -rf",
    "rmdir /s",
    "del /f",
    "format ",
    ":(){:|:&};:",
    "dd if=",
    "mkfs",
    "wget http",
    "curl http://",
    "> /dev/sd",
    "chmod 777",
    "sudo rm",
    "DROP TABLE",
    "__import__",
    "exec(",
    "eval(",
    "os.system",
    "subprocess.call",
    "subprocess.Popen",
]

# -------------------------------------------------------------------
# Stability levels
# -------------------------------------------------------------------
STABILITY_LEVELS: tuple[str, ...] = ("stable", "beta", "alpha", "experimental")

# -------------------------------------------------------------------
# Misc
# -------------------------------------------------------------------
VERSION: str = "1.0.0"
CLI_NAME: str = "raiku"
