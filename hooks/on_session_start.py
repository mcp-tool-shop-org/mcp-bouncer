"""MCP Bouncer — SessionStart hook entry point.

Reads the .mcp.json in the current working directory, health-checks all
configured servers, quarantines broken ones, and auto-restores recovered ones.
"""

import json
import sys
from pathlib import Path

# Add parent so we can import bouncer
sys.path.insert(0, str(Path(__file__).parent.parent))

import bouncer


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    cwd = hook_input.get("cwd", ".")
    mcp_json_path = str(Path(cwd) / ".mcp.json")

    result = bouncer.run(mcp_json_path)

    # Output summary for Claude to see in the session log
    print(json.dumps({
        "status": "ok",
        "message": f"MCP Bouncer: {result.get('message', 'done')}",
    }))


if __name__ == "__main__":
    main()
