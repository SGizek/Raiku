# Raiku CLI Reference

Complete reference for all Raiku CLI commands and flags.

---

## Global Options

These options apply to every command:

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

Pulls the latest `index.json` from the Raiku GitHub repository and stores it at
`~/.raiku/index.json`. If the local index is less than 1 hour old, sync is skipped
unless `--force` is specified.

**Options**

| Flag | Description |
|------|-------------|
| `--force` / `-f` | Sync even if the local index is fresh |

**Examples**

```bash
raiku sync
raiku sync --force
raiku --verbose sync
```

**Exit codes**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Network error or remote index unreachable |

---

## raiku search

```bash
raiku search QUERY [--language LANG] [--limit N]
```

Searches the local package index for packages whose name, description, or author
contains `QUERY` (case-insensitive substring match).

**Arguments**

| Argument | Description |
|----------|-------------|
| `QUERY` | Search string (required) |

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--language` / `-l` | (all) | Filter results to one language |
| `--limit` / `-n` | 20 | Maximum results to display |

**Supported language values**

`Python`, `Rust`, `C`, `CPP`, `Zig`, `Java`, `CSharp`, `Go`
(aliases like `python`, `c++`, `c#`, `golang` are also accepted)

**Examples**

```bash
raiku search math
raiku search queue --language Go
raiku search utils --language Python --limit 5
```

**Exit codes**

| Code | Meaning |
|------|---------|
| 0 | Search completed (zero results is still exit 0) |
| 1 | Index not found — run `raiku sync` first |

---

## raiku install

```bash
raiku install PACKAGE [--trust] [--no-build] [--force]
```

Full install flow: resolves the package from the index, fetches only the required files,
validates them, caches them locally, and runs the build command.

**Arguments**

| Argument | Description |
|----------|-------------|
| `PACKAGE` | Exact package name from the index (required) |

**Options**

| Flag | Description |
|------|-------------|
| `--trust` | Skip interactive build command confirmation |
| `--no-build` | Download and cache only; do not run `build_command` |
| `--force` / `-f` | Reinstall even if the package is already cached |

**Install flow (step by step)**

1. Load `~/.raiku/index.json`
2. Find the package by exact name match
3. Check local cache — skip if already installed (unless `--force`)
4. Fetch `raiku.toml`, `version.yml`, `README.md` from GitHub raw URLs
5. Parse and schema-validate both manifests
6. Verify SHA-256 hash of `raiku.toml` against the index entry
7. Write all files to `~/.raiku/cache/<Language>/<name>/<version>/`
8. Display build command; prompt for confirmation (safe mode)
9. Execute build command in cached directory
10. Print success confirmation

**Examples**

```bash
raiku install fast-math
raiku install goqueue --trust
raiku install blazing-vec --no-build
raiku install cmatrix --force
```

**Exit codes**

| Code | Meaning |
|------|---------|
| 0 | Installed successfully |
| 1 | Package not found, hash mismatch, schema error, or build failure |

---

## raiku publish

```bash
raiku publish [--dir PATH] [--dry-run]
```

Validates the package in `PATH` (default: current directory) against all schema and
rules requirements, then prints the index entry JSON and step-by-step PR instructions.

Does not push anything to GitHub automatically — it prepares the contribution for you.

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--dir` | `.` | Path to the package directory |
| `--dry-run` | false | Validate and print output without writing files |

**What is validated**

- `raiku.toml` is parseable and passes schema validation
- `version.yml` is parseable and passes schema validation
- Version fields match between both manifests
- All required files (`raiku.toml`, `version.yml`, `README.md`, `src/`) are present
- No forbidden file types in the package root
- Package name follows naming rules
- Build command does not contain forbidden patterns

**Output**

- A summary table of package metadata
- The SHA-256 of `raiku.toml` (to add to `index.json`)
- The exact JSON block to paste into `index/index.json`
- Step-by-step PR instructions

**Examples**

```bash
raiku publish
raiku publish --dir ./my-package
raiku publish --dry-run
```

---

## raiku validate

```bash
raiku validate [--dir PATH] [--all] [--language LANG] [--strict]
```

Validates one or all packages against schema and structural rules.

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--dir` | `.` | Package directory to validate |
| `--all` | false | Validate all packages in `UserSub/` |
| `--language` / `-l` | (all) | With `--all`, limit to one language |
| `--strict` | false | Exit non-zero if any warnings found |

**Checks performed**

| Check | Error or Warning? |
|-------|-------------------|
| `raiku.toml` exists and parses | Error |
| `version.yml` exists and parses | Error |
| All required fields present | Error |
| Field types and formats correct | Error |
| Language is a supported value | Error |
| Version is valid semver | Error |
| Stability level is valid | Error |
| `version` matches between both manifests | Error |
| `src/` exists and is non-empty | Error |
| No forbidden file types in root | Error |
| Build command has no forbidden patterns | Error |
| Package name follows naming rules | Error |
| `README.md` exists | Warning |

**Examples**

```bash
raiku validate
raiku validate --dir ./UserSub/Python/fast-math
raiku validate --all
raiku validate --all --language Rust
raiku validate --all --strict
```

**Exit codes**

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more errors found (or warnings with `--strict`) |
