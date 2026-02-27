# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in mcp-bouncer, please report it responsibly.

**Email:** 64996768+mcp-tool-shop@users.noreply.github.com

**What to include:**
- Description of the vulnerability
- Steps to reproduce
- Affected version(s)
- Potential impact

**Response timeline:**
- Acknowledgement within 48 hours
- Assessment within 7 days
- Fix or mitigation within 30 days for confirmed issues

**Please do NOT:**
- Open a public GitHub issue for security vulnerabilities
- Exploit the vulnerability against other users

## Scope

MCP Bouncer is a **local-only** session hook that health-checks MCP servers.

- **Data touched:** reads and writes `.mcp.json` and `.mcp.health.json` in the project directory. Spawns MCP server processes briefly (2s timeout) to verify they start without crashing.
- **Data NOT touched:** no network requests, no user content, no API keys or tokens. Does not read server output beyond stderr on crash.
- **Process spawning:** spawns configured MCP server commands with their declared args/env. Kills spawned processes after the 2-second health check window.
- **No telemetry:** collects nothing, sends nothing. All operations are local.
- **Fail-safe:** if Bouncer itself crashes, `.mcp.json` is unchanged.
