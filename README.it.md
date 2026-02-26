<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## Perché

I server MCP configurati nel file `.mcp.json` vengono caricati all'avvio della sessione, indipendentemente dal fatto che funzionino o meno. Un server non funzionante spreca token di contesto (i suoi strumenti continuano a essere visualizzati), causa errori nelle chiamate agli strumenti e genera avvisi rossi ogni volta che si apre Claude. Non esiste un modo integrato per rilevare e saltare i server non funzionanti.

MCP Bouncer viene eseguito prima di ogni sessione, controlla ogni server e permette di proseguire solo a quelli che funzionano correttamente.

## Come Funziona

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### Controllo dello Stato

Per ogni server, Bouncer:

1. Risolve il percorso del file eseguibile (`shutil.which` / controllo del percorso assoluto)
2. Avvia il processo con i parametri e le variabili d'ambiente configurati
3. Attende 2 secondi: se il processo è ancora in esecuzione, viene considerato valido.

Questo permette di intercettare i problemi più comuni: file eseguibili mancanti, dipendenze corrotte, errori di importazione e bug che causano il crash all'avvio. È veloce, affidabile e non presenta fragilità a livello di protocollo.

### Isolamento

I server non funzionanti vengono spostati nel file `.mcp.health.json`, mantenendo intatta la loro configurazione completa:

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

Ad ogni sessione, i server isolati vengono ritestati. Quando superano il test, vengono automaticamente ripristinati nel file `.mcp.json` – non è necessario alcun intervento manuale.

## Guida Rapida

### Opzione A: installazione tramite pip (consigliata)

```bash
pip install mcp-bouncer
```

Successivamente, registrare l'hook nelle impostazioni di Claude Code (`settings.local.json` o `.claude/settings.json`):

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

### Opzione B: clonare il repository

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

### Fatto

Nella sessione successiva, Bouncer viene eseguito automaticamente. I server non funzionanti vengono isolati, quelli funzionanti rimangono attivi. Verrà visualizzata una riga di riepilogo nel registro della sessione:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## Interfaccia a Riga di Comando (CLI)

Eseguire direttamente per la diagnostica:

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

Tutti i comandi accettano un argomento di percorso opzionale (il valore predefinito è `.mcp.json` nella directory corrente):

```bash
mcp-bouncer status /path/to/.mcp.json
```

## Decisioni di Progettazione

- **Nessuna dipendenza** — utilizza solo la libreria standard, funziona ovunque sia installata Python 3.10 o superiore.
- **Sicurezza** — se Bouncer stesso si blocca, il file `.mcp.json` rimane invariato.
- **Preserva la struttura** — modifica solo la chiave `mcpServers`, lasciando intatte le chiavi `$schema`, `defaults` e altre.
- **Controlli paralleli** — utilizza `ThreadPoolExecutor` con 5 processi, completando l'operazione ben entro il timeout di 10 secondi dell'hook.
- **Ritardo di una sessione** — un server che si blocca durante una sessione viene isolato all'inizio della sessione successiva (Claude Code non supporta modifiche alla configurazione durante la sessione).

## File

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## Licenza

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
