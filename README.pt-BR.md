<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
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

## Por que

Os servidores MCP configurados no arquivo `.mcp.json` são carregados no início da sessão, independentemente de estarem funcionando ou não. Um servidor com problemas desperdiça tokens de contexto (suas ferramentas ainda aparecem), causa falhas nas chamadas de ferramentas e exibe avisos vermelhos sempre que você abre o Claude. Não existe uma maneira integrada de detectar e ignorar servidores com problemas.

O MCP Bouncer é executado antes de cada sessão, verifica cada servidor e permite apenas que os servidores que estão funcionando corretamente sejam acessados.

## Como Funciona

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### Verificação de Saúde

Para cada servidor, o Bouncer:

1. Resolve o arquivo executável do comando (`shutil.which` / verificação de caminho absoluto)
2. Inicia o processo com seus argumentos e variáveis de ambiente configurados
3. Aguarda 2 segundos — se o processo ainda estiver em execução, ele é considerado válido

Isso detecta as falhas mais comuns: arquivos executáveis ausentes, dependências corrompidas, erros de importação e bugs que causam travamentos na inicialização. É rápido, confiável e não depende de protocolos complexos.

### Quarentena

Servidores com problemas são movidos para o arquivo `.mcp.health.json`, com sua configuração completa preservada:

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

A cada sessão, os servidores em quarentena são retestados. Quando passam no teste, eles são automaticamente restaurados para o arquivo `.mcp.json` — não é necessária intervenção manual.

## Como Começar

### Opção A: Instalação via pip (recomendado)

```bash
pip install mcp-bouncer
```

Em seguida, registre o hook nas configurações do Claude Code (`settings.local.json` ou `.claude/settings.json`):

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

### Opção B: Clone o repositório

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

### Pronto

Na próxima sessão, o Bouncer será executado automaticamente. Servidores com problemas serão colocados em quarentena, e os servidores que estiverem funcionando corretamente permanecerão ativos. Você verá uma linha de resumo no log da sessão:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## Interface de Linha de Comando (CLI)

Execute diretamente para fins de diagnóstico:

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

Todos os comandos aceitam um argumento de caminho opcional (o padrão é `.mcp.json` no diretório atual):

```bash
mcp-bouncer status /path/to/.mcp.json
```

## Decisões de Design

- **Sem dependências** — usa apenas a biblioteca padrão, funciona em qualquer lugar onde o Python 3.10 ou superior esteja instalado.
- **Seguro** — se o próprio Bouncer falhar, o arquivo `.mcp.json` não será alterado.
- **Preserva a estrutura** — modifica apenas a chave `mcpServers`, mantendo as chaves `$schema`, `defaults` e outras intactas.
- **Verificações paralelas** — usa um `ThreadPoolExecutor` com 5 processos, completando bem dentro do tempo limite de 10 segundos do hook.
- **Atraso de uma sessão** — um servidor que falha durante uma sessão é colocado em quarentena no início da próxima sessão (o Claude Code não suporta alterações de configuração durante a sessão).

## Arquivos

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## Licença

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
