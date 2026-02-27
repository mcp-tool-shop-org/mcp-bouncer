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

## なぜ

`.mcp.json`で設定されたMCPサーバーは、セッション開始時に、動作するかどうかに関わらずロードされます。正常に動作しないサーバーは、コンテキストのトークンを無駄にし（ツールは依然として表示されます）、ツール呼び出しの失敗を引き起こし、Claudeを開くたびに赤い警告を表示します。正常に動作しないサーバーを検出し、スキップする方法は組み込まれていません。

MCP Bouncerは、各セッションの前に実行され、すべてのサーバーをチェックし、正常に動作するサーバーのみを許可します。

## 仕組み

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### ヘルスチェック

各サーバーについて、Bouncerは以下の処理を行います。

1. コマンドの実行ファイルを解決します（`shutil.which` / 絶対パスチェック）。
2. 設定された引数と環境変数を使用してプロセスを起動します。
3. 2秒待ちます。プロセスがまだ実行中の場合、正常と判断されます。

これにより、最も一般的な問題（実行ファイルの欠落、依存関係の破損、インポートエラー、起動時のクラッシュなど）を検出できます。高速で信頼性が高く、プロトコルレベルでの脆弱性はありません。

### 隔離

正常に動作しないサーバーは、設定情報がすべて保持された状態で`.mcp.health.json`に移動されます。

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

各セッションで、隔離されたサーバーは再テストされます。正常に動作するようになると、自動的に`.mcp.json`に復元されます。手動での操作は不要です。

## クイックスタート

### オプションA：pip install（推奨）

```bash
pip install mcp-bouncer
```

次に、Claude Codeの設定（`settings.local.json`または`.claude/settings.json`）で、このフックを登録します。

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

### オプションB：リポジトリをクローン

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

### 完了です

次のセッションでは、Bouncerが自動的に実行されます。正常に動作しないサーバーは隔離され、正常に動作するサーバーはそのままです。セッションログに概要が表示されます。

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## コマンドラインインターフェース（CLI）

診断のために直接実行します。

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

すべてのコマンドは、オプションでパス引数を受け取ります（デフォルトは現在のディレクトリの`.mcp.json`）。

```bash
mcp-bouncer status /path/to/.mcp.json
```

## 設計上の決定事項

- **依存関係なし**：標準ライブラリのみを使用し、Python 3.10以降が動作する環境であればどこでも実行できます。
- **安全策**：Bouncer自体がクラッシュした場合でも、`.mcp.json`は変更されません。
- **構造の保持**：`mcpServers`キーのみを変更し、`$schema`、`defaults`、およびその他のキーは変更しません。
- **並列チェック**：5つのワーカーを使用した`ThreadPoolExecutor`を使用しており、10秒のフックタイムアウト内に完了します。
- **1セッションの遅延**：セッション中にクラッシュしたサーバーは、次のセッションの開始時に隔離されます（Claude Codeはセッション中に設定を変更できません）。

## ファイル

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## セキュリティとデータ範囲

MCP Bouncerは、**ローカルでのみ**動作し、ネットワーク通信は一切ありません。

- **アクセスするデータ**：プロジェクトディレクトリ内の`.mcp.json`と`.mcp.health.json`を読み書きします。MCPサーバーのプロセスを一時的に起動して（2秒のタイムアウト）、起動を確認します。
- **アクセスしないデータ**：ネットワークリクエストは行いません。ユーザーコンテンツ、APIキー、トークンも使用しません。クラッシュ時にサーバーからの出力（標準エラー出力以外）は読み込みません。
- **テレメトリーなし**：何も収集せず、何も送信しません。すべての操作はローカルで行われます。
- **安全策**：Bouncer自体がクラッシュした場合でも、`.mcp.json`は変更されません。

## 評価

| カテゴリ | 評価 | 備考 |
|----------|-------|-------|
| A. セキュリティ | 10/10 | SECURITY.md、ローカルでのみ動作、テレメトリーなし、安全策 |
| B. エラー処理 | 10/10 | 構造化された結果、クリーンな標準エラー出力ログ |
| C. 運用ドキュメント | 10/10 | README、CHANGELOG、CLIの使用方法 |
| D. ソフトウェアの品質 | 10/10 | CI + テスト、カバレッジ、依存関係監査、検証スクリプト |
| E. 識別 | 10/10 | ロゴ、翻訳、紹介ページ |
| **Total** | **50/50** | |

## ライセンス

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
