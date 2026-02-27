<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/mcp-bouncer/readme.png" width="400" />
</p>

<p align="center">
  A SessionStart hook that health-checks your MCP servers, quarantines broken ones, and auto-restores them when they come back online.
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-bouncer/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-bouncer/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://pypi.org/project/mcp-bouncer/"><img src="https://img.shields.io/pypi/v/mcp-bouncer" alt="PyPI" /></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/mcp-bouncer"><img src="https://img.shields.io/codecov/c/github/mcp-tool-shop-org/mcp-bouncer" alt="Coverage" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-bouncer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-bouncer" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-bouncer/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

---

## Why

MCP servers configured in `.mcp.json` load at session start whether they work or not. A broken server wastes context tokens (its tools still appear), causes failed tool calls, and throws red warnings every time you open Claude. There's no built-in way to detect and skip broken servers.

MCP Bouncer runs before each session, checks every server, and only lets healthy ones through.

## How It Works

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### Health Check

For each server, Bouncer:

1. Resolves the command binary (`shutil.which` / absolute path check)
2. Spawns the process with its configured args and env
3. Waits 2 seconds — if the process is still running, it passes

This catches the most common failures: missing binaries, broken dependencies, import errors, and crash-on-startup bugs. Fast, reliable, no protocol-level fragility.

### Quarantine

Broken servers are moved to `.mcp.health.json` with their full config preserved:

```json
{
  "quarantined": {
    "voice-soundboard": {
      "config": { "command": "voice-soundboard-mcp", "args": ["--backend=python"] },
      "reason": "Command not found: voice-soundboard-mcp",
      "quarantined_at": "2026-02-21T10:30:00Z",
      "last_checked": "2026-02-21T12:00:00Z",
      "fail_count": 3
    }
  }
}
```

Every session, quarantined servers are re-tested. When they pass, they're automatically restored to `.mcp.json` — no manual intervention needed.

## Quick Start

### Option A: pip install (recommended)

```bash
pip install mcp-bouncer
```

Then register the hook in your Claude Code settings (`settings.local.json` or `.claude/settings.json`):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "mcp-bouncer-hook",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Option B: Clone the repo

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/mcp-bouncer/hooks/on_session_start.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Done

Next session, Bouncer runs automatically. Broken servers get quarantined, healthy ones stay. You'll see a summary line in the session log:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

Run directly for diagnostics:

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

All commands accept an optional path argument (defaults to `.mcp.json` in the current directory):

```bash
mcp-bouncer status /path/to/.mcp.json
```

## Design Decisions

- **No dependencies** — stdlib only, runs anywhere Python 3.10+ lives
- **Fail-safe** — if Bouncer itself crashes, `.mcp.json` is unchanged
- **Preserves structure** — only touches the `mcpServers` key, leaves `$schema`, `defaults`, and other keys intact
- **Parallel checks** — `ThreadPoolExecutor` with 5 workers, completes well within the 10-second hook timeout
- **One-session delay** — a server that breaks mid-session gets quarantined at the start of the next session (Claude Code doesn't support mid-session config changes)

## Files

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## Security & Data Scope

MCP Bouncer is **local-only** with zero network activity.

- **Data touched:** reads and writes `.mcp.json` and `.mcp.health.json` in the project directory. Spawns MCP server processes briefly (2s timeout) to verify they start.
- **Data NOT touched:** no network requests, no user content, no API keys or tokens. Does not read server output beyond stderr on crash.
- **No telemetry:** collects nothing, sends nothing. All operations are local.
- **Fail-safe:** if Bouncer itself crashes, `.mcp.json` is unchanged.

## Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| A. Security | 10/10 | SECURITY.md, local-only, no telemetry, fail-safe |
| B. Error Handling | 10/10 | Structured results, clean stderr logging |
| C. Operator Docs | 10/10 | README, CHANGELOG, CLI usage |
| D. Shipping Hygiene | 10/10 | CI + tests, coverage, dep-audit, verify script |
| E. Identity | 10/10 | Logo, translations, landing page |
| **Total** | **50/50** | |

## License

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
