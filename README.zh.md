<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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
  <a href="https://github.com/mcp-tool-shop-org/mcp-bouncer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-bouncer" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-bouncer/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

---

## 为什么？

在 `.mcp.json` 文件中配置的 MCP 服务器，无论是否正常工作，都会在会话开始时被加载。一个损坏的服务器会浪费上下文令牌（其工具仍然会显示），导致工具调用失败，并在每次打开 Claude 时显示红色警告。目前没有内置的方法来检测并跳过损坏的服务器。

MCP Bouncer 在每个会话之前运行，检查每个服务器，只允许健康的服务器通过。

## 工作原理

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### 健康检查

对于每个服务器，Bouncer 执行以下操作：

1. 查找命令二进制文件（使用 `shutil.which` 或绝对路径检查）。
2. 启动进程，并使用其配置的参数和环境变量。
3. 等待 2 秒 — 如果进程仍在运行，则认为该服务器状态良好。

这可以检测到最常见的故障：缺少二进制文件、依赖项损坏、导入错误以及启动时崩溃的错误。 速度快，可靠性高，且不受协议层面的问题影响。

### 隔离

损坏的服务器会被移动到 `.mcp.health.json` 文件中，其完整的配置信息会被保留。

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

在每个会话中，隔离的服务器会被重新测试。 如果它们通过测试，则会自动恢复到 `.mcp.json` 文件中，无需手动干预。

## 快速开始

### 选项 A：使用 pip 安装（推荐）

```bash
pip install mcp-bouncer
```

然后，在 Claude Code 的设置中注册该钩子（`settings.local.json` 或 `.claude/settings.json`）：

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

### 选项 B：克隆代码仓库

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

### 完成

在下一次会话中，Bouncer 会自动运行。 损坏的服务器会被隔离，健康的服务器会继续运行。 您将在会话日志中看到一个摘要行：

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## 命令行工具

直接运行以进行诊断：

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

所有命令都接受一个可选的路径参数（默认为当前目录下的 `.mcp.json` 文件）：

```bash
mcp-bouncer status /path/to/.mcp.json
```

## 设计决策

- **无依赖项** — 仅使用标准库，可在任何安装了 Python 3.10+ 的环境中运行。
- **安全可靠** — 如果 Bouncer 本身崩溃，`.mcp.json` 文件不会被修改。
- **保留结构** — 仅修改 `mcpServers` 键，保留 `$schema`、`defaults` 和其他键不变。
- **并行检查** — 使用 `ThreadPoolExecutor`，包含 5 个工作线程，可以在 10 秒的钩子超时时间内完成检查。
- **单会话延迟** — 如果服务器在会话过程中出现故障，则会在下一次会话开始时将其隔离（Claude Code 不支持会话中进行的配置更改）。

## 文件

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## 许可证

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
