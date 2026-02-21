"""MCP Bouncer — SessionStart hook entry point.

This file is a thin wrapper for cloned-repo usage.
The real logic lives in src/mcp_bouncer/.
If installed via pip, use the `mcp-bouncer-hook` command instead.
"""

import sys
from pathlib import Path

# Allow running from the repo root without pip install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_bouncer.hook import main

if __name__ == "__main__":
    main()
