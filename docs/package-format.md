# Raiku Package Format

Authoritative specification for the Raiku package format. Every package submitted to the repository must comply exactly.

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
# -----------------------------------------------------------------------
# REQUIRED
# -----------------------------------------------------------------------

name = "package-name"
# Type    : string
# Rules   : lowercase, starts with a letter, [a-z0-9_-], max 64 chars
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

build_command = "pip install -e ."
# Type    : string, 1–512 characters
# Rules   : must not contain forbidden patterns (see rules.md §7.1)
#           must be non-interactive, must complete within 300 seconds

# -----------------------------------------------------------------------
# OPTIONAL (but recommended)
# -----------------------------------------------------------------------

description = "One sentence describing the package."
# Type    : string, max 512 characters

license = "MIT"
# Type    : string, max 64 characters — SPDX identifier preferred

homepage = "https://github.com/you/your-project"
# Type    : string, max 256 characters

tags = ["math", "vectors", "utils"]
# Type    : list of strings
# Purpose : Enables raiku search --tag filtering
# Convention : lowercase, hyphenated (e.g. "data-structures", "linear-algebra")

dependencies = ["other-package", "another-package"]
# Type    : list of strings
# Rules   : each entry must be a valid Raiku package name present in the index
# Behaviour: Raiku resolves transitive deps and installs them in order before
#            installing this package. Circular deps are detected and rejected.
```

---

## version.yml — Full Specification

```yaml
# -----------------------------------------------------------------------
# REQUIRED
# -----------------------------------------------------------------------

version: "1.0.0"
# Type    : string
# Rules   : must exactly match version in raiku.toml
# Format  : semantic version

release_date: "2026-07-04"
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
# Note    : When updating, add new entries — do not remove old ones
```

---

## src/ Directory

- Must contain at least one file.
- Subdirectories are permitted.
- No pre-compiled binaries (`.exe`, `.dll`, `.so`, `.dylib`) allowed anywhere in the package.

### Generated layouts by language (from `raiku init`)

| Language | Typical `src/` content |
|----------|------------------------|
| Python   | `<name>.py`, `pyproject.toml` |
| Rust     | `lib.rs`, `Cargo.toml` |
| C        | `<name>.c`, `<name>.h` |
| C++      | `<name>.hpp`, `<name>.cpp`, `CMakeLists.txt` |
| Zig      | `<name>.zig`, `build.zig` |
| Java     | `dev/raiku/<name>/<Name>.java` |
| C#       | `<Name>.cs`, `<name>.csproj` |
| Go       | `<name>.go`, `<name>_test.go`, `go.mod` |

---

## index.json Entry

When a package is published via `raiku publish`, an entry is added to `index/index.json`. You can also run `raiku index --rebuild` to regenerate the whole file automatically.

```json
{
  "name": "package-name",
  "version": "1.0.0",
  "language": "Python",
  "author": "Your Name",
  "description": "One sentence description.",
  "path": "UserSub/Python/package-name",
  "license": "MIT",
  "tags": ["utils", "math"],
  "dependencies": [],
  "sha256": "<64-hex-char SHA-256 of raiku.toml>"
}
```

The `sha256` is computed automatically by `raiku publish`. It must be updated every time `raiku.toml` changes.

---

## raiku.lock

Run `raiku install <pkg> --lock` to create or update `raiku.lock` in the current directory:

```json
{
  "lock_version": "1",
  "generated_at": 1751673600,
  "packages": {
    "fast-math": {
      "version": "1.0.0",
      "language": "Python",
      "path": "UserSub/Python/fast-math",
      "sha256": "e3b0c44...",
      "installed_at": 1751673600
    }
  }
}
```

Commit `raiku.lock` to ensure reproducible installs across machines. The lock file records exact versions — if a package is in the lock file, that version is always installed regardless of what the index currently lists as latest.

---

## Scaffolding with raiku init

Instead of creating files manually, use the interactive wizard:

```bash
raiku init
```

It prompts for all fields and generates a complete, valid package with language-appropriate source templates. Run `raiku validate` afterwards to confirm everything passes.

---

## Validation Checklist

Run this before opening a PR:

```bash
raiku validate --dir UserSub/<Language>/<package-name>
```

- [ ] `raiku.toml` present and parseable
- [ ] `version.yml` present and parseable
- [ ] `README.md` present
- [ ] `src/` directory is non-empty
- [ ] All required `raiku.toml` fields present
- [ ] All required `version.yml` fields present
- [ ] `version` matches between both files
- [ ] `language` matches the parent directory name
- [ ] Package `name` is lowercase and valid (`[a-z][a-z0-9_-]*`)
- [ ] `build_command` has no forbidden patterns
- [ ] No forbidden file types in package root
- [ ] `stability_level` is one of: `stable`, `beta`, `alpha`, `experimental`
- [ ] `release_date` is YYYY-MM-DD format
- [ ] Each `dependencies` entry is a valid Raiku package name
