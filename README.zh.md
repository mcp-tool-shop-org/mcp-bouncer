<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <strong>中文</strong> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer 标志" width="280" />
</p>

<p align="center">
  一个 SessionStart hook，用于对你的 MCP 服务器进行健康检查，隔离出问题的服务器，并在它们恢复正常后自动还原。
</p>

<p align="center">
  <a href="#为什么">为什么</a> &middot;
  <a href="#工作原理">工作原理</a> &middot;
  <a href="#快速开始">快速开始</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#许可证">许可证</a>
</p>

---

## 为什么

在 `.mcp.json` 中配置的 MCP 服务器会在会话启动时全部加载，不管它们是否正常工作。一个有问题的服务器会白白消耗上下文 token（它的工具仍然会显示出来），导致工具调用失败，并且每次打开 Claude 时都会抛出红色警告。目前没有内置机制来检测并跳过这些有问题的服务器。

MCP Bouncer 会在每次会话开始前运行，检查所有服务器，只让健康的服务器通过。

## 工作原理

```
会话启动
  -> Bouncer 读取 .mcp.json（活跃服务器）+ .mcp.health.json（隔离服务器）
  -> 并行对所有服务器进行健康检查
  -> 有问题的活跃服务器 -> 被隔离（保存到 .mcp.health.json）
  -> 已恢复的隔离服务器 -> 还原到 .mcp.json
  -> 将摘要信息写入会话日志
```

### 健康检查

对于每个服务器，Bouncer 会：

1. 解析命令的可执行文件路径（`shutil.which` / 绝对路径检查）
2. 使用配置的参数和环境变量启动进程
3. 等待 2 秒——如果进程仍在运行，则视为通过

这能捕获最常见的故障：缺少可执行文件、依赖损坏、导入错误以及启动即崩溃的问题。速度快、可靠，不依赖协议层的脆弱性。

### 隔离机制

有问题的服务器会被移入 `.mcp.health.json`，完整配置保留如下：

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

每次会话时，被隔离的服务器都会重新接受测试。一旦通过，它们会自动还原到 `.mcp.json`，无需任何手动操作。

## 快速开始

### 方式A：pip 安装（推荐）

```bash
pip install mcp-bouncer
```

在你的 Claude Code 配置文件（`settings.local.json` 或 `.claude/settings.json`）中添加：

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

### 方式B：克隆仓库

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

在你的 Claude Code 配置文件（`settings.local.json` 或 `.claude/settings.json`）中添加：

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

下次会话时，Bouncer 会自动运行。有问题的服务器会被隔离，健康的服务器正常保留。你会在会话日志中看到一行摘要：

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

可以直接运行进行诊断：

```bash
# 查看活跃与隔离状态
mcp-bouncer status

# 立即执行健康检查（与 hook 行为相同）
mcp-bouncer check

# 强制还原所有被隔离的服务器
mcp-bouncer restore
```

所有命令支持可选的路径参数（默认为当前目录下的 `.mcp.json`）：

```bash
mcp-bouncer status /path/to/.mcp.json
```

## 设计决策

- **无外部依赖** — 仅使用标准库，任何 Python 3.10+ 环境均可运行
- **故障安全** — 即使 Bouncer 自身崩溃，`.mcp.json` 也不会被修改
- **保留原有结构** — 只修改 `mcpServers` 键，`$schema`、`defaults` 及其他键保持原样
- **并行检查** — 使用 `ThreadPoolExecutor`（5 个工作线程），在 10 秒的 hook 超时内轻松完成
- **延迟一个会话** — 在会话中途出现问题的服务器，会在下次会话开始时被隔离（Claude Code 不支持会话中途修改配置）

## 文件结构

```
mcp-bouncer/
├── src/mcp_bouncer/        # 包（通过 pip 安装）
│   ├── bouncer.py          # 核心：健康检查、隔离、恢复、CLI
│   └── hook.py             # SessionStart hook 入口
├── bouncer.py              # 克隆仓库用的包装器
└── hooks/
    └── on_session_start.py # 克隆仓库用的包装器
```

## 许可证

[MIT](LICENSE)
