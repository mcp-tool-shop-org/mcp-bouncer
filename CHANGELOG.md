# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-02-27

### Added
- SECURITY.md with real data scope (process spawning, .mcp.json writes)
- README Security & Data Scope section
- SHIP_GATE.md and SCORECARD.md (Shipcheck compliance)
- Makefile with `verify` target (lint + typecheck + test)
- Dependency audit job in CI workflow (pip-audit)
- Codecov coverage upload in CI
- pytest-cov and pip-audit in dev dependencies

### Changed
- Scorecard 37/50 → 50/50

## [1.0.0] - 2026-02-26

### Added
- Initial release
- SessionStart hook for Claude Code — health-checks MCP servers at session start
- Parallel health checks with ThreadPoolExecutor (5 workers, 2s timeout)
- Quarantine system: broken servers moved to `.mcp.health.json` with metadata
- Auto-restore: quarantined servers re-tested each session, restored when healthy
- CLI commands: `status`, `check`, `restore`
- Zero dependencies — stdlib only, runs on Python 3.10+
- Fail-safe design: `.mcp.json` unchanged if Bouncer crashes
- Preserves non-mcpServers keys in `.mcp.json`
- README translations (7 languages)
- Landing page via @mcptoolshop/site-theme
