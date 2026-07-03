# Raiku Package Format

This document is the authoritative specification for the Raiku package format.

---

## Directory Layout

```
<package-name>/
  raiku.toml       ← Package manifest (REQUIRED)
  version.yml      ← Version manifest  (REQUIRED)
  README.md        ← Documentation     (REQUIRED)
  src/             ← Source code       (REQUIRED, non-empty)
```

All four entries must be present. The validator rejects any package missing any of them.

---

## raiku.toml — Full Specification

```toml
# ---------------------------------------------------------------
# REQUIRED fields
# ---------------------------------------------------------------

name = "package-name"
# Type    : string
# Rules   : lowercase, starts with letter, [a-z0-9_-], max 64 chars
# Example : "fast-math", "blazing_vec", "goqueue"

version = "1.0.0"
# Type    : string
# Rules   : semantic version — MAJOR.MINOR.PATCH[pre-release]
# Example : "1.0.0", "0.2.1-beta.1"

language = "Python"
# Type    : string (case-sensitive)
# Allowed : Python | Rust | C | CPP | Zig | Java | CSharp | Go

author = "Your Name"
# Type    : string, 1–128 characters
# Example : "Ada Lovelace", "gh:username"

build_command = "pip install -e ."
# Type    : string, 1–512 characters
# Rules   : must not contain any forbidden pattern (see rules.md §7.1)
#           must be non-interactive, must complete within 300 seconds

# ---------------------------------------------------------------
# OPTIONAL fields
# ---------------------------------------------------------------

description = "One sentence describing the package."
# Type    : string, max 512 characters (recommended)

license = "MIT"
# Type    : string, max 64 characters
# Format  : SPDX identifier preferred (MIT, Apache-2.0, GPL-3.0, etc.)

homepage = "https://github.com/you/your-project"
# Type    : string, max 256 characters

dependencies = ["other-package", "another-package"]
# Type    : list of strings
# Each entry must be a valid Raiku package name
# Dependencies are resolved from the Raiku index
```

---

## version.yml — Full Specification

```yaml
# ---------------------------------------------------------------
# REQUIRED fields
# ---------------------------------------------------------------

version: "1.0.0"
# Type    : string
# Rules   : must exactly match version in raiku.toml
# Format  : semantic version

release_date: "2026-07-03"
# Type    : string
# Format  : YYYY-MM-DD (ISO 8601 date)

stability_level: stable
# Type    : string
# Allowed : stable | beta | alpha | experimental

changelog:
  - "Initial release"
  - "Added feature X"
# Type    : string OR list of strings
# Rules   : must not be empty
# Purpose : Describes what changed in this version
#           When updating, add a new entry — do not remove old entries
```

---

## src/ Directory

- Must contain at least one file.
- File types and structure follow the conventions of the target language.
- Subdirectories inside `src/` are permitted.
- No pre-compiled binaries (`.exe`, `.dll`, `.so`, `.dylib`) are allowed anywhere in the package.

### Recommended source file layouts by language

| Language | Typical `src/` content |
|----------|------------------------|
| Python   | `<module>.py` or `<package>/__init__.py` |
| Rust     | `lib.rs` or `main.rs` + `Cargo.toml` |
| C        | `<name>.c` + `<name>.h` |
| C++      | `<name>.hpp` (header-only) or `.cpp` + `CMakeLists.txt` |
| Zig      | `<name>.zig` + `build.zig` |
| Java     | `<reverse.domain>/<name>/*.java` |
| C#       | `<name>.csproj` + `*.cs` |
| Go       | `go.mod` + `*.go` |

---

## index.json Entry

When a package is published, an entry is added to `index/index.json`:

```json
{
  "name": "package-name",
  "version": "1.0.0",
  "language": "Python",
  "author": "Your Name",
  "description": "One sentence description.",
  "path": "UserSub/Python/package-name",
  "sha256": "<64-hex-char SHA-256 of raiku.toml>"
}
```

The `sha256` field is computed automatically by `raiku publish` and must be kept
up to date when the package is updated.

---

## Validation Checklist

Before opening a PR, verify that your package passes:

```bash
raiku validate --dir UserSub/<Language>/<package-name>
```

All items in this list must show no errors:

- [ ] `raiku.toml` present and parseable
- [ ] `version.yml` present and parseable
- [ ] `README.md` present
- [ ] `src/` directory is non-empty
- [ ] All required `raiku.toml` fields present
- [ ] All required `version.yml` fields present
- [ ] `version` matches between both files
- [ ] `language` matches the parent directory
- [ ] Package `name` is lowercase and valid
- [ ] `build_command` has no forbidden patterns
- [ ] No forbidden file types in package root
- [ ] `stability_level` is a valid value
- [ ] `release_date` is YYYY-MM-DD format
