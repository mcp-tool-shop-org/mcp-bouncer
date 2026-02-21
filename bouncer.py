"""MCP Bouncer — health-check MCP servers, quarantine broken ones, auto-restore.

This file is a thin wrapper for cloned-repo usage (python bouncer.py ...).
The real logic lives in src/mcp_bouncer/bouncer.py.
If installed via pip, use the `mcp-bouncer` command instead.
"""

import sys
from pathlib import Path

# Allow running from the repo root without pip install
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_bouncer.bouncer import cli

if __name__ == "__main__":
    cli()
