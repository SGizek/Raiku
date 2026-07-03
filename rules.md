# Raiku Package Rules

Version: 1.0.0  
Status: Enforced

All packages submitted to the Raiku repository must comply with every rule in this document.
Non-compliant submissions will be rejected during CI validation and code review.

---

## 1. Folder Structure Rules

Every package must live under the correct language subdirectory:

```
UserSub/
  <Language>/
    <package-name>/
      raiku.toml       ← REQUIRED
      version.yml      ← REQUIRED
      README.md        ← REQUIRED
      src/             ← REQUIRED (non-empty directory)
```

Supported language directories:

| Directory | Language |
|-----------|----------|
| `Python`  | Python   |
| `Rust`    | Rust     |
| `C`       | C        |
| `CPP`     | C++      |
| `Zig`     | Zig      |
| `Java`    | Java     |
| `CSharp`  | C#       |
| `Go`      | Go       |

Rules:
- Each package occupies **exactly one directory** under the appropriate language folder.
- Nesting beyond `UserSub/<Language>/<package-name>/` is not permitted at the package root level.
- The `src/` entry must be a **directory**, not a file, and must contain at least one source file.
- No files may be placed directly inside `UserSub/<Language>/` — only package subdirectories.

---

## 2. Naming Rules

### Package Names
- Must be **lowercase**.
- Must start with a **letter** (a–z).
- May contain **letters, digits, hyphens (`-`), and underscores (`_`)** only.
- Maximum length: **64 characters**.
- Must be **globally unique** within the Raiku index.
- Examples of valid names: `fast-math`, `blazing_vec`, `http2_client`, `z80emu`
- Examples of invalid names: `FastMath`, `2fast`, `my package`, `fast.math`, `__init__`

### File and Directory Names
- All manifest files must use the exact names: `raiku.toml`, `version.yml`, `README.md`.
- Source files inside `src/` follow the naming conventions of the target language.
- No spaces in any file or directory name anywhere in the package tree.

---

## 3. Required Files

The following files are mandatory in every package. The CLI validator will reject any
package missing any of these:

| File / Dir   | Purpose                               | Notes                          |
|-------------|---------------------------------------|--------------------------------|
| `raiku.toml` | Package manifest                      | Must pass schema validation    |
| `version.yml`| Version and changelog manifest        | Must pass schema validation    |
| `README.md`  | Human-readable documentation          | Must be non-empty              |
| `src/`       | Package source code                   | Must contain ≥1 source file    |

---

## 4. raiku.toml Requirements

```toml
name = "<package-name>"        # required — see naming rules
version = "<semver>"           # required — e.g. 1.0.0
language = "<Language>"        # required — must match language directory
author = "<name or handle>"    # required
build_command = "<command>"    # required — see build command rules
description = "..."            # recommended
license = "MIT"                # recommended — SPDX identifier
homepage = "https://..."       # optional
dependencies = []              # optional — list of Raiku package name strings
```

All required fields must be present. Unknown fields are rejected.

---

## 5. version.yml Requirements

```yaml
version: "1.0.0"               # required — must match raiku.toml version exactly
release_date: "YYYY-MM-DD"     # required — ISO 8601 date
stability_level: stable        # required — one of: stable, beta, alpha, experimental
changelog:                     # required — string or list of strings
  - "Initial release"
```

- The `version` field in `version.yml` **must exactly match** the `version` field in `raiku.toml`.
- `release_date` must be a valid calendar date in `YYYY-MM-DD` format.
- `changelog` must describe what changed in this version — empty changelog is rejected.

---

## 6. Versioning Rules

- Versions must follow **Semantic Versioning** ([semver.org](https://semver.org)):
  `MAJOR.MINOR.PATCH` with an optional pre-release suffix, e.g. `1.0.0`, `2.1.3-beta.1`.
- `MAJOR` bumps indicate breaking changes.
- `MINOR` bumps add functionality in a backward-compatible manner.
- `PATCH` bumps are backward-compatible bug fixes.
- Version numbers may only **increase** — a published package version can never be overwritten.
- Pre-release suffixes (`-alpha`, `-beta`, `-rc.1`) must be accompanied by the corresponding
  `stability_level` in `version.yml`.
- `0.x.x` versions are acceptable for early-stage packages but must use `alpha` or `beta`
  stability level.

---

## 7. Security Constraints

### 7.1 Build Command Restrictions

The following patterns are **absolutely forbidden** in `build_command`:

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Destructive filesystem operation |
| `rmdir /s`, `del /f` | Windows destructive operations |
| `format ` | Disk formatting |
| `:(){:|:&};:` | Fork bomb |
| `dd if=` | Raw disk write |
| `mkfs` | Filesystem creation |
| `wget http://`, `curl http://` | Unencrypted network fetch |
| `> /dev/sd*` | Raw device write |
| `chmod 777` | Dangerous permission change |
| `sudo rm` | Privileged destructive operation |
| `DROP TABLE` | SQL injection attempt |
| `__import__`, `exec(`, `eval(` | Python code injection |
| `os.system`, `subprocess.call`, `subprocess.Popen` | Indirect execution |

Any build command containing a forbidden pattern will be rejected at validation time
and will never be executed by the Raiku installer.

### 7.2 Safe Mode

- By default, Raiku operates in **safe mode** (`safe_mode = true`).
- In safe mode, the user is shown the exact `build_command` and must explicitly approve it
  before execution.
- Safe mode can be bypassed per-install with `--trust` flag (user responsibility).
- Safe mode **cannot** be disabled globally for untrusted packages.

### 7.3 Hash Validation

- Every package in `index.json` should include a `sha256` field containing the
  SHA-256 hex digest of the package's `raiku.toml` file.
- The Raiku installer verifies this hash after download. A mismatch **aborts installation**.
- Packages without a recorded hash trigger a visible warning but are not blocked
  (to allow local/development packages).

### 7.4 Forbidden File Types in Package Root

The following file types are **never permitted** in the package root directory:

- Pre-compiled binaries: `.exe`, `.dll`, `.so`, `.dylib`
- Shell scripts: `.sh`, `.bat`, `.cmd`, `.ps1` (must be inside `src/`)
- Credentials: `.key`, `.pem`, `.p12`, `.pfx`
- Environment files: `.env`

### 7.5 Trust Flag System

- A package can be flagged as **trusted** by the user via `--trust` at install time.
- Trusted packages skip the interactive build-command confirmation prompt.
- Trust is never granted automatically — it is always an explicit user decision.
- Trust records are stored locally in `~/.raiku/trusted.json` and are per-machine.

---

## 8. Contribution Rules

### 8.1 Submitting a Package

1. Fork the Raiku repository: `https://github.com/SGizek/Raiku`
2. Create your package directory under the appropriate `UserSub/<Language>/` folder.
3. Ensure your package passes `raiku validate` with zero errors.
4. Run `raiku publish` to generate the index entry and contribution instructions.
5. Add your package's index entry to `index/index.json`.
6. Open a Pull Request against the `main` branch.

### 8.2 PR Requirements

- PR title: `add(<language>): <package-name> v<version>`  
  Example: `add(Rust): blazing-vec v1.0.0`
- PR body must include:
  - Brief description of the package
  - The output of `raiku validate --dir <your-package-dir>`
  - Language and build requirements (compiler version, runtime, etc.)
- All CI checks must pass before merge.

### 8.3 Updating an Existing Package

- Bump both `version` fields (in `raiku.toml` and `version.yml`) following semver.
- Update the `changelog` in `version.yml` with a description of changes.
- Update `index/index.json` with the new version and updated `sha256`.
- Open a PR with title: `update(<language>): <package-name> v<new-version>`

### 8.4 Removing a Package

- Packages are never deleted from the repository history.
- To deprecate a package, set `stability_level: experimental` and add a changelog entry
  noting deprecation.
- Contact a maintainer to remove a package from the active index if required.

### 8.5 Code of Conduct

- All contributions must comply with the Raiku Code of Conduct.
- Packages must not contain offensive, discriminatory, or harmful content.
- Packages that violate security rules will be removed and the contributor banned.

---

## 9. Index Rules

- `index/index.json` is the **single source of truth** for all package resolution.
- No package exists in Raiku unless it has an entry in `index.json`.
- Each entry must include: `name`, `version`, `language`, `path`, and ideally `sha256`.
- The `path` field must follow the pattern `UserSub/<Language>/<package-name>`.
- Duplicate package names are not permitted.
- The index must remain valid JSON at all times — broken JSON blocks all installs.

---

## 10. Language and Ecosystem Rules

| Language | Required Toolchain | Recommended Build Command Pattern |
|----------|--------------------|----------------------------------|
| Python   | Python ≥ 3.10     | `pip install -e .`               |
| Rust     | Rust stable + Cargo | `cargo build --release`          |
| C        | GCC ≥ 11 or Clang ≥ 14 | `gcc -O2 -o <out> src/<main>.c` |
| C++      | GCC ≥ 11 / Clang ≥ 14 / MSVC | `cmake -S src -B build && cmake --build build` |
| Zig      | Zig ≥ 0.12        | `zig build`                      |
| Java     | JDK ≥ 17          | `javac -d out src/**/*.java`     |
| C#       | .NET SDK ≥ 8.0    | `dotnet build src/<proj>.csproj -c Release` |
| Go       | Go ≥ 1.21         | `go build ./...`                 |

- Build commands should be **reproducible** and **deterministic**.
- Build commands must not require interactive input.
- Build commands must complete within **300 seconds** (5 minutes); longer builds will be timed out.
- Network access during build is permitted but discouraged — prefer vendored dependencies.
