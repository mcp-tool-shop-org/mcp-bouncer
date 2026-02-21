"""MCP Bouncer — health-check MCP servers, quarantine broken ones, auto-restore."""

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

STARTUP_TIMEOUT = 2  # seconds to let process start before checking
MAX_WORKERS = 5


def _log(msg: str) -> None:
    print(f"[mcp-bouncer] {msg}", file=sys.stderr)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_command(command: str) -> str | None:
    """Check if a command is resolvable on PATH or is an absolute path."""
    if os.path.isabs(command) and os.path.isfile(command):
        return command
    return shutil.which(command)


def health_check(name: str, config: dict) -> dict:
    """Health-check a single MCP server by verifying it can start.

    Checks:
    1. Command binary exists and is resolvable
    2. Process starts without immediately crashing (survives STARTUP_TIMEOUT)

    Returns {"name": ..., "healthy": bool, "reason": str | None}.
    """
    command = config.get("command", "")
    args = config.get("args", [])
    env_overrides = config.get("env", {})

    # Step 1: can we even find the binary?
    resolved = _resolve_command(command)
    if not resolved:
        return {"name": name, "healthy": False, "reason": f"Command not found: {command}"}

    # Step 2: spawn and check it doesn't crash immediately
    env = {**os.environ, **env_overrides}
    full_cmd = [resolved, *args]
    proc = None

    try:
        proc = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=config.get("cwd"),
        )

        # Wait and check if the process crashes during startup
        try:
            proc.wait(timeout=STARTUP_TIMEOUT)
            # Process exited within timeout — that's a crash
            stderr_out = proc.stderr.read().decode(errors="replace").strip()
            reason = stderr_out[:200] if stderr_out else f"Process exited with code {proc.returncode}"
            return {"name": name, "healthy": False, "reason": reason}
        except subprocess.TimeoutExpired:
            # Process is still running after timeout — healthy!
            return {"name": name, "healthy": True, "reason": None}

    except FileNotFoundError:
        return {"name": name, "healthy": False, "reason": f"Command not found: {command}"}
    except PermissionError:
        return {"name": name, "healthy": False, "reason": f"Permission denied: {command}"}
    except Exception as e:
        return {"name": name, "healthy": False, "reason": f"{type(e).__name__}: {e}"}
    finally:
        if proc:
            try:
                proc.kill()
            except Exception:
                pass


def run(mcp_json_path: str) -> dict:
    """Run health checks on all servers. Returns summary dict."""
    mcp_path = Path(mcp_json_path)
    health_path = mcp_path.parent / ".mcp.health.json"

    # Read current configs
    if not mcp_path.exists():
        _log(f"No .mcp.json found at {mcp_path}")
        return {"status": "skip", "message": "No .mcp.json found"}

    with open(mcp_path, "r") as f:
        mcp_data = json.load(f)

    active_servers = mcp_data.get("mcpServers", {})

    # Read quarantined servers
    quarantined = {}
    if health_path.exists():
        try:
            with open(health_path, "r") as f:
                health_data = json.load(f)
            quarantined = health_data.get("quarantined", {})
        except (json.JSONDecodeError, KeyError):
            quarantined = {}

    # Nothing to check
    all_servers = {**active_servers, **{k: v["config"] for k, v in quarantined.items()}}
    if not all_servers:
        _log("No servers to check")
        return {"status": "ok", "message": "No servers configured", "healthy": 0, "quarantined": 0}

    _log(f"Checking {len(all_servers)} server(s)...")

    # Health-check all servers in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(health_check, name, config): name for name, config in all_servers.items()}
        for future in as_completed(futures):
            result = future.result()
            results[result["name"]] = result

    # Partition into healthy and broken
    new_active = {}
    new_quarantined = {}

    for name, config in all_servers.items():
        check = results[name]
        if check["healthy"]:
            new_active[name] = config
            if name in quarantined:
                _log(f"  RESTORED: {name}")
        else:
            existing_q = quarantined.get(name, {})
            new_quarantined[name] = {
                "config": config,
                "reason": check["reason"],
                "quarantined_at": existing_q.get("quarantined_at", _now_iso()),
                "last_checked": _now_iso(),
                "fail_count": existing_q.get("fail_count", 0) + 1,
            }
            if name in active_servers:
                _log(f"  QUARANTINED: {name} — {check['reason']}")
            else:
                _log(f"  STILL DOWN: {name} — {check['reason']}")

    # Write updated .mcp.json (preserve non-mcpServers keys)
    mcp_data["mcpServers"] = new_active
    with open(mcp_path, "w") as f:
        json.dump(mcp_data, f, indent=2)
        f.write("\n")

    # Write health file
    q_names = list(new_quarantined.keys())
    healthy_count = len(new_active)
    summary = f"{healthy_count}/{len(all_servers)} healthy"
    if q_names:
        summary += f", quarantined: {', '.join(q_names)}"

    health_out = {
        "quarantined": new_quarantined,
        "last_run": _now_iso(),
        "summary": summary,
    }

    with open(health_path, "w") as f:
        json.dump(health_out, f, indent=2)
        f.write("\n")

    _log(summary)
    return {
        "status": "ok",
        "message": summary,
        "healthy": healthy_count,
        "quarantined": len(new_quarantined),
        "quarantined_names": q_names,
    }
