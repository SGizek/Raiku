# Raiku CLI Reference

Complete reference for all 20 Raiku CLI commands and their flags.

---

## Global Options

```
raiku [OPTIONS] COMMAND [ARGS]...
```

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | | Print Raiku version and exit |
| `--verbose` | `-v` | Enable verbose/debug output |
| `--no-color` | | Disable ANSI color output |
| `--help` | | Show help and exit |

---

## raiku sync

```bash
raiku sync [--force]
```

Fetches the latest `index.json` from GitHub and stores it at `~/.raiku/index.json`.
Skips if the local index is less than 1 hour old unless `--force` is passed.

| Flag | Description |
|------|-------------|
| `--force` / `-f` | Sync even if the local index is fresh |

```bash
raiku sync
raiku sync --force
```

---

## raiku search

```bash
raiku search QUERY [--language LANG] [--tag TAG] [--limit N]
```

Searches the local index by name, description, or author. All matching is case-insensitive substring search.

| Flag | Default | Description |
|------|---------|-------------|
| `--language` / `-l` | all | Filter to one language |
| `--tag` / `-t` | none | Filter to packages with a specific tag |
| `--limit` / `-n` | 20 | Maximum results to display |

```bash
raiku search math
raiku search queue --language Go
raiku search utils --tag collections
raiku search sort --language Python --limit 5
```

Language aliases are accepted: `python`, `py`, `rust`, `rs`, `c`, `cpp`, `c++`, `zig`, `java`, `csharp`, `c#`, `cs`, `go`, `golang`.

---

## raiku install

```bash
raiku install PACKAGE [OPTIONS]
raiku install ./local-path [OPTIONS]
```

Installs a package from the index **or** from a local directory path.

| Flag | Description |
|------|-------------|
| `--trust` | Skip interactive build command confirmation |
| `--no-build` | Download and cache only; skip build command |
| `--force` / `-f` | Reinstall even if already cached |
| `--no-deps` | Skip dependency resolution |
| `--lock` | Write/update `raiku.lock` in the current directory |

**Remote install flow:**

1. Load `~/.raiku/index.json`
2. Resolve transitive dependencies; install them first
3. Fetch `raiku.toml`, `version.yml`, `README.md` with streaming progress bars
4. Parse and schema-validate both manifests
5. Verify SHA-256 hash against the index entry
6. Cache at `~/.raiku/cache/<Language>/<name>/<version>/`
7. Prompt to confirm build command (safe mode)
8. Execute build command in a restricted subprocess
9. Optionally update `raiku.lock`

**Local install:** validates the local package directory, copies files to cache, then runs the build command. Does not require a network connection or index entry.

```bash
raiku install fast-math
raiku install goqueue --trust
raiku install blazing-vec --no-build
raiku install cmatrix --force
raiku install fast-math --lock          # also writes raiku.lock
raiku install ./my-new-package          # install from disk
raiku install ./my-new-package --no-build
```

---

## raiku init

```bash
raiku init [NAME] [--language LANG] [--output-dir DIR] [--yes]
```

Interactive wizard that scaffolds a complete new Raiku package. Prompts for name, language, version, author, description, license, build command, and tags — then generates all required files.

| Flag | Default | Description |
|------|---------|-------------|
| `NAME` | prompted | Package name |
| `--language` / `-l` | prompted | Target language |
| `--output-dir` / `-o` | `.` | Directory to create the package in |
| `--yes` / `-y` | false | Accept all defaults without prompting |

**What gets generated:**

```
<name>/
  raiku.toml
  version.yml
  README.md
  src/
    <language-specific source files>
```

Language-specific `src/` contents:

| Language | Files created |
|----------|--------------|
| Python   | `<name>.py`, `pyproject.toml` |
| Rust     | `lib.rs`, `Cargo.toml` |
| C        | `<name>.c`, `<name>.h` |
| C++      | `<name>.hpp`, `<name>.cpp`, `CMakeLists.txt` |
| Zig      | `<name>.zig`, `build.zig` |
| Java     | `dev/raiku/<name>/<Name>.java` |
| C#       | `<Name>.cs`, `<name>.csproj` |
| Go       | `<name>.go`, `<name>_test.go`, `go.mod` |

```bash
raiku init
raiku init my-lib --language Rust
raiku init fast-sort --language Python --output-dir ./packages --yes
```

---

## raiku info

```bash
raiku info PACKAGE [--json]
```

Shows full details for a package from the index: name, version, language, author, description, tags, dependencies, SHA-256, and local install status.

| Flag | Description |
|------|-------------|
| `--json` | Output raw JSON |

```bash
raiku info fast-math
raiku info goqueue --json
```

---

## raiku list

```bash
raiku list [--language LANG] [--json]
```

Lists all packages currently installed in `~/.raiku/cache/`.

| Flag | Description |
|------|-------------|
| `--language` / `-l` | Filter by language |
| `--json` | Output raw JSON |

```bash
raiku list
raiku list --language Rust
```

---

## raiku outdated

```bash
raiku outdated [--language LANG] [--json]
```

Shows installed packages that have newer versions available in the index. Does not install anything.

| Flag | Description |
|------|-------------|
| `--language` / `-l` | Filter by language |
| `--json` | Output raw JSON |

```bash
raiku outdated
raiku outdated --language Go
```

---

## raiku update

```bash
raiku update [PACKAGE] [--all] [--dry-run]
```

Checks the index for newer versions and reinstalls those packages. Respects pinned packages — pinned packages are skipped during `--all`.

| Flag | Description |
|------|-------------|
| `PACKAGE` | Name of a specific package to update |
| `--all` | Update every installed package |
| `--dry-run` | Show what would be updated without installing |

```bash
raiku update fast-math
raiku update --all
raiku update --all --dry-run
```

---

## raiku uninstall

```bash
raiku uninstall PACKAGE [--yes] [--version VER]
```

Removes a package from the local cache.

| Flag | Description |
|------|-------------|
| `--yes` / `-y` | Skip confirmation prompt |
| `--version` | Uninstall only a specific version (default: all versions) |

```bash
raiku uninstall fast-math
raiku uninstall goqueue --yes
raiku uninstall blazing-vec --version 1.0.0
```

---

## raiku audit

```bash
raiku audit [--language LANG] [--fix]
```

Scans all installed packages and verifies their cached `raiku.toml` SHA-256 hashes match what the index declares. Detects tampering or corruption after installation.

| Flag | Description |
|------|-------------|
| `--language` / `-l` | Audit only one language |
| `--fix` | Evict packages that fail the audit (can be cleanly reinstalled) |

```bash
raiku audit
raiku audit --language Python
raiku audit --fix
```

---

## raiku stats

```bash
raiku stats
```

Displays ecosystem-wide statistics from the index (total packages, by-language breakdown, top tags) alongside local cache statistics (installed count, disk usage).

```bash
raiku stats
```

---

## raiku pin

```bash
raiku pin add PACKAGE [VERSION] [--reason TEXT]
raiku pin remove PACKAGE
raiku pin list
```

Pins a package at a specific version, preventing it from being updated by `raiku update --all`.

| Subcommand | Description |
|------------|-------------|
| `add PACKAGE [VERSION]` | Pin at VERSION (defaults to currently installed version) |
| `remove PACKAGE` | Remove pin, allowing future updates |
| `list` | Show all pinned packages |

```bash
raiku pin add fast-math
raiku pin add fast-math 1.0.0 --reason "stable baseline"
raiku pin remove fast-math
raiku pin list
```

---

## raiku publish

```bash
raiku publish [--dir PATH] [--dry-run]
```

Validates the package in `PATH` against all schema and rules requirements, then prints the SHA-256 hash, the exact JSON entry to add to `index/index.json`, and step-by-step PR instructions. Does not push anything to GitHub.

| Flag | Default | Description |
|------|---------|-------------|
| `--dir` | `.` | Path to the package directory |
| `--dry-run` | false | Validate and print output without writing files |

```bash
raiku publish
raiku publish --dir ./UserSub/Python/fast-math
raiku publish --dry-run
```

---

## raiku validate

```bash
raiku validate [--dir PATH] [--all] [--language LANG] [--strict]
```

Validates one or all packages against schema rules and structural compliance.

| Flag | Default | Description |
|------|---------|-------------|
| `--dir` | `.` | Package directory to validate |
| `--all` | false | Validate all packages in `UserSub/` |
| `--language` / `-l` | all | With `--all`, limit to one language |
| `--strict` | false | Exit non-zero if any warnings found |

**Checks performed:**

| Check | Severity |
|-------|----------|
| `raiku.toml` exists and parses | Error |
| `version.yml` exists and parses | Error |
| All required fields present and valid | Error |
| Language is a supported value | Error |
| Version is valid semver | Error |
| Stability level is valid | Error |
| `version` matches between both manifests | Error |
| `src/` exists and is non-empty | Error |
| No forbidden file types in root | Error |
| Build command has no forbidden patterns | Error |
| Package name follows naming rules | Error |
| `README.md` exists | Warning |

```bash
raiku validate
raiku validate --dir ./UserSub/Python/fast-math
raiku validate --all
raiku validate --all --language Rust --strict
```

---

## raiku index

```bash
raiku index --rebuild [--root DIR] [--dry-run]
raiku index --stats
raiku index --check [--root DIR]
```

Index management commands.

| Flag | Description |
|------|-------------|
| `--rebuild` | Scan `UserSub/` and regenerate `index/index.json` automatically |
| `--stats` | Show package count, language breakdown, and sync time |
| `--check` | Validate every index entry path and hash |
| `--root` | Repository root to use (default: `.`) |
| `--dry-run` | With `--rebuild`: print output without writing |

```bash
raiku index --rebuild
raiku index --rebuild --dry-run
raiku index --stats
raiku index --check
```

---

## raiku cache

```bash
raiku cache --info
raiku cache --clear [--yes]
```

Local cache management.

| Flag | Description |
|------|-------------|
| `--info` | Show disk usage, package count, and cache path |
| `--clear` | Wipe the entire cache (with confirmation) |
| `--yes` / `-y` | Skip confirmation for `--clear` |

```bash
raiku cache --info
raiku cache --clear
raiku cache --clear --yes
```

---

## raiku doctor

```bash
raiku doctor [--language LANG]
```

Checks that all build tools required for each supported language are installed and accessible, reports their versions, and flags anything missing with install hints.

Tools checked: `python`, `pip`, `gcc`, `clang`, `cmake`, `cargo`, `zig`, `javac`, `go`, `dotnet`, `git`.

| Flag | Description |
|------|-------------|
| `--language` / `-l` | Only check tools for one language |

```bash
raiku doctor
raiku doctor --language Rust
```

---

## raiku config

```bash
raiku config list
raiku config get KEY
raiku config set KEY VALUE
raiku config reset [--yes]
```

View and modify Raiku configuration stored in `~/.raiku/config.toml`.

| Subcommand | Description |
|------------|-------------|
| `list` | Show all configuration values |
| `get KEY` | Print the current value of one key |
| `set KEY VALUE` | Update a key and save to disk |
| `reset` | Restore all defaults |

**Configurable keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `safe_mode` | bool | `true` | Prompt before running build commands |
| `auto_trust` | bool | `false` | Never silently trust packages |
| `verbose` | bool | `false` | Enable verbose output by default |
| `color` | bool | `true` | Enable colored output |
| `index_url` | string | GitHub raw URL | Remote index location |
| `raw_base_url` | string | GitHub raw URL | Base URL for fetching package files |

```bash
raiku config list
raiku config get safe_mode
raiku config set safe_mode false
raiku config set verbose true
raiku config reset
```

---

## raiku trust

```bash
raiku trust add PACKAGE [--reason TEXT]
raiku trust remove PACKAGE
raiku trust list
raiku trust clear [--yes]
```

Manages the persistent trusted-packages list at `~/.raiku/trusted.json`. Trusted packages skip the interactive build command confirmation prompt on install. Trust is always an explicit user action — never automatic.

| Subcommand | Description |
|------------|-------------|
| `add PACKAGE` | Mark a package as trusted (prompts for confirmation) |
| `remove PACKAGE` | Revoke trust |
| `list` | Show all trusted packages with trust date and reason |
| `clear` | Remove all trusted packages |

```bash
raiku trust add fast-math
raiku trust add goqueue --reason "reviewed source, MIT license"
raiku trust remove fast-math
raiku trust list
raiku trust clear --yes
```

---

## raiku completion

```bash
raiku completion SHELL [--install]
```

Generates shell completion scripts for tab-completing package names and command flags.

| Argument | Values |
|----------|--------|
| `SHELL` | `bash`, `zsh`, `fish`, `powershell` |

| Flag | Description |
|------|-------------|
| `--install` | Automatically append the script to your shell config |

```bash
# Print the script
raiku completion bash

# Auto-install
raiku completion bash --install        # appends to ~/.bashrc
raiku completion zsh  --install        # appends to ~/.zshrc
raiku completion fish --install        # writes ~/.config/fish/completions/raiku.fish
raiku completion powershell --install  # appends to $PROFILE

# Manual install
raiku completion bash >> ~/.bashrc && source ~/.bashrc
```
