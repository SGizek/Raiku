# Raiku CLI Changelog

All notable changes to the Raiku CLI tool itself are documented here.
Package changelogs live inside each package's `version.yml`.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

### Added
- `raiku upgrade` — upgrade the Raiku CLI itself from GitHub
- `raiku search --interactive` — TUI package browser
- `raiku lint` — static analysis on `raiku.toml` beyond schema validation
- `raiku bench` — run package benchmarks (auto-detects criterion/timeit/testing.B)
- `raiku repair` — scan and clean broken/incomplete cache entries
- `raiku info --deps-tree` — recursive dependency tree display
- Verified package badge system (`verified` flag in index + search display)
- Package namespacing (`@username/package-name` format)
- Retry logic with exponential backoff on network errors
- Parallel dependency fetching via `concurrent.futures`
- Full `pytest` test suite under `tests/`

---

## [1.0.0] — 2026-07-04

### Added — Batch 3
- `raiku run <package> <cmd>` — execute commands inside installed packages (like npx)
- `raiku from-lock` — install exact versions from `raiku.lock`
- `raiku diff <package>` — compare installed vs latest with changelog
- `raiku test <package>` — run package test suite (auto-detects pytest/cargo/go test/zig)
- `raiku why <package>` — show whether package is direct or a dependency
- `raiku graph` — ASCII dependency graph of installed packages
- `raiku export` — dump installed packages to `requirements.raiku`
- `raiku import` — install from `requirements.raiku`
- `raiku verify <package>` — re-verify a single package's hash
- `raiku rollback <package>` — revert to previous cached version
- `raiku login` / `raiku whoami` / `raiku logout` — GitHub token management
- `raiku publish --submit` — auto-open PR on GitHub using stored token
- `raiku info --changelog` — display formatted changelog
- `raiku search --sort latest` — sort results by release date
- `readonly` config key — prevent all cache writes
- Resumable downloads via HTTP Range headers
- `raiku search --tag` — filter search by tag

### Added — Batch 2
- `raiku init` — interactive wizard with per-language source templates
- `raiku outdated` — report packages with newer versions available
- `raiku stats` — global ecosystem + local cache statistics
- `raiku pin add/remove/list` — prevent packages from auto-updating
- `raiku audit` — verify all cached package hashes against index
- `raiku completion` — shell completions for bash/zsh/fish/PowerShell
- Dependency resolver with circular-dependency detection
- Lock file (`raiku.lock`) for reproducible installs
- Real-time streaming download progress bars

### Added — Batch 1
- `raiku list` — show all installed packages
- `raiku uninstall` — remove from cache with confirmation
- `raiku info` — full package details
- `raiku update [--all]` — update packages (respects pins)
- `raiku index --rebuild/--stats/--check` — index management
- `raiku cache --info/--clear` — cache management
- `raiku doctor` — build tool availability checker
- `raiku config list/get/set/reset` — configuration management
- `raiku trust add/remove/list/clear` — persistent build trust
- `raiku search --tag` — tag-based filtering
- Auto-rebuild index GitHub Action workflow

### Initial Release — Core Features
- `raiku sync` — pull latest index from GitHub
- `raiku search` — search package index
- `raiku install` — fetch, validate, cache, and build packages
- `raiku publish` — validate and prepare PR contributions
- `raiku validate` — schema + structural compliance checking
- SHA-256 hash verification for all packages
- Safe mode — build commands require explicit approval
- Forbidden pattern scan — blocks dangerous build commands
- Restricted subprocess environment for builds
- 300-second build timeout
- Schema validation via Cerberus (`schemas/schema.yml`)
- 8-language support: Python, Rust, C, C++, Zig, Java, C#, Go
- Example packages for all 8 languages

---

## Version Policy

- `MAJOR` — breaking changes to CLI interface or package format
- `MINOR` — new commands or backwards-compatible features
- `PATCH` — bug fixes, security patches, documentation updates

Pre-release suffixes: `-alpha`, `-beta`, `-rc.N`
