<p align="center">
  <a href="README.md">English</a> | <strong>日本語</strong> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer ロゴ" width="280" />
</p>

<p align="center">
  SessionStart hook を使って MCP サーバーのヘルスチェックを行い、壊れたサーバーを隔離し、復旧したら自動で元に戻すツール。
</p>

<p align="center">
  <a href="#なぜ必要か">なぜ必要か</a> &middot;
  <a href="#仕組み">仕組み</a> &middot;
  <a href="#クイックスタート">クイックスタート</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#ライセンス">ライセンス</a>
</p>

---

## なぜ必要か

`.mcp.json` に設定された MCP サーバーは、動作するかどうかに関わらずセッション開始時にロードされます。壊れたサーバーはコンテキストトークンを無駄に消費し（ツール一覧には表示され続ける）、ツール呼び出しの失敗を引き起こし、Claude を開くたびに赤い警告を表示します。壊れたサーバーを検知してスキップする仕組みは標準では用意されていません。

MCP Bouncer は各セッションの開始前に動作し、すべてのサーバーを確認して、正常なものだけを通過させます。

## 仕組み

```
セッション開始
  -> Bouncer が .mcp.json（有効）と .mcp.health.json（隔離済み）を読み込む
  -> すべてのサーバーを並列でヘルスチェック
  -> 異常な有効サーバー -> 隔離（.mcp.health.json に保存）
  -> 回復した隔離済みサーバー -> .mcp.json に復元
  -> セッションにサマリーを記録
```

### ヘルスチェック

各サーバーに対して Bouncer は以下を行います：

1. コマンドのバイナリを解決する（`shutil.which` / 絶対パスの確認）
2. 設定された引数と環境変数でプロセスを起動する
3. 2 秒待機 — プロセスがまだ動いていれば合格

これにより最も一般的な障害を検出できます：バイナリの欠落、依存関係の破損、import エラー、起動時クラッシュなど。高速で信頼性が高く、プロトコルレベルの不安定さもありません。

### 隔離

壊れたサーバーは完全な設定を保持したまま `.mcp.health.json` に移動されます：

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

セッションごとに隔離済みサーバーは再テストされます。チェックに合格すると、自動的に `.mcp.json` に復元されます — 手動での操作は不要です。

## クイックスタート

### オプションA: pip install（推奨）

```bash
pip install mcp-bouncer
```

Claude Code の設定ファイル（`settings.local.json` または `.claude/settings.json`）に追加します：

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

### オプションB: リポジトリをクローン

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

Claude Code の設定ファイル（`settings.local.json` または `.claude/settings.json`）に追加します：

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

### 完了

次のセッションから Bouncer が自動的に動作します。壊れたサーバーは隔離され、正常なものはそのまま残ります。セッションログに以下のようなサマリーが表示されます：

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

診断用に直接実行することもできます：

```bash
# 有効なサーバーと隔離済みサーバーを表示
mcp-bouncer status

# ヘルスチェックを今すぐ実行（hook と同じ動作）
mcp-bouncer check

# 隔離済みのサーバーをすべて強制復元
mcp-bouncer restore
```

すべてのコマンドはオプションでパスを指定できます（省略時はカレントディレクトリの `.mcp.json` を使用）：

```bash
mcp-bouncer status /path/to/.mcp.json
```

## 設計上の判断

- **依存ゼロ** — 標準ライブラリのみ使用。Python 3.10 以上があればどこでも動作します
- **フェイルセーフ** — Bouncer 自体がクラッシュしても `.mcp.json` は変更されません
- **構造を保持** — `mcpServers` キーのみ操作し、`$schema`、`defaults`、その他のキーはそのまま残します
- **並列チェック** — ワーカー数 5 の `ThreadPoolExecutor` を使用し、hook のタイムアウト 10 秒以内に余裕で完了します
- **1 セッション遅延** — セッション中に壊れたサーバーは次のセッション開始時に隔離されます（Claude Code はセッション中の設定変更をサポートしていないため）

## ファイル構成

```
mcp-bouncer/
├── src/mcp_bouncer/        # パッケージ（pip でインストール）
│   ├── bouncer.py          # コア: ヘルスチェック、隔離、復元、CLI
│   └── hook.py             # SessionStart hook エントリーポイント
├── bouncer.py              # クローン利用時のラッパー
└── hooks/
    └── on_session_start.py # クローン利用時のラッパー
```

## ライセンス

[MIT](LICENSE)
