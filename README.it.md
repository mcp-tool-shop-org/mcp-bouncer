<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <strong>Italiano</strong> | <a href="README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer logo" width="280" />
</p>

<h1 align="center">mcp-bouncer</h1>

<p align="center">
  Un hook SessionStart che controlla lo stato dei tuoi server MCP, mette in quarantena quelli difettosi e li ripristina automaticamente quando tornano online.
</p>

<p align="center">
  <a href="#perché">Perché</a> &middot;
  <a href="#come-funziona">Come funziona</a> &middot;
  <a href="#avvio-rapido">Avvio rapido</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#licenza">Licenza</a>
</p>

---

## Perché

I server MCP configurati in `.mcp.json` si avviano all'inizio di ogni sessione, che funzionino o meno. Un server difettoso spreca token di contesto (i suoi strumenti appaiono comunque), causa chiamate agli strumenti fallite e mostra avvisi rossi ogni volta che apri Claude. Non esiste un meccanismo nativo per rilevare e saltare i server non funzionanti.

MCP Bouncer si esegue prima di ogni sessione, controlla ogni server e lascia passare solo quelli in buona salute.

## Come funziona

```
La sessione si avvia
  -> Bouncer legge .mcp.json (attivi) + .mcp.health.json (in quarantena)
  -> Controlla lo stato di TUTTI i server in parallelo
  -> Server attivi difettosi -> in quarantena (salvati in .mcp.health.json)
  -> Server in quarantena ripristinati -> restituiti a .mcp.json
  -> Riepilogo registrato nella sessione
```

### Controllo dello stato

Per ogni server, Bouncer:

1. Risolve il binario del comando (`shutil.which` / controllo del percorso assoluto)
2. Avvia il processo con gli argomenti e le variabili d'ambiente configurati
3. Attende 2 secondi — se il processo è ancora in esecuzione, il controllo è superato

Questo rileva i guasti più comuni: binari mancanti, dipendenze rotte, errori di importazione e crash all'avvio. Veloce, affidabile, senza fragilità a livello di protocollo.

### Quarantena

I server difettosi vengono spostati in `.mcp.health.json` con la configurazione completa preservata:

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

Ad ogni sessione, i server in quarantena vengono testati di nuovo. Quando superano il controllo, vengono automaticamente ripristinati in `.mcp.json` — nessun intervento manuale necessario.

## Avvio rapido

### 1. Clone

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

### 2. Registra il hook

Aggiungi alle impostazioni di Claude Code (`settings.local.json` o `.claude/settings.json`):

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

### 3. Fatto

Dalla sessione successiva, Bouncer si esegue automaticamente. I server difettosi vengono messi in quarantena, quelli sani rimangono attivi. Vedrai una riga di riepilogo nel log di sessione:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

Esegui direttamente per la diagnostica:

```bash
# Mostra cosa è attivo vs in quarantena
python bouncer.py status

# Esegui i controlli di stato ora (identico a ciò che fa il hook)
python bouncer.py check

# Forza il ripristino di tutti i server in quarantena
python bouncer.py restore
```

Tutti i comandi accettano un argomento percorso opzionale (predefinito: `.mcp.json` nella directory corrente):

```bash
python bouncer.py status /path/to/.mcp.json
```

## Scelte di progettazione

- **Nessuna dipendenza** — solo stdlib, funziona ovunque ci sia Python 3.10+
- **Fail-safe** — se Bouncer stesso va in crash, `.mcp.json` rimane invariato
- **Struttura preservata** — tocca solo la chiave `mcpServers`, lascia intatte `$schema`, `defaults` e le altre chiavi
- **Controlli paralleli** — `ThreadPoolExecutor` con 5 worker, termina ampiamente entro il timeout del hook di 10 secondi
- **Ritardo di una sessione** — un server che si rompe a metà sessione viene messo in quarantena all'inizio della sessione successiva (Claude Code non supporta modifiche alla configurazione a sessione attiva)

## File

```
mcp-bouncer/
├── bouncer.py              # Core: controllo stato, quarantena, ripristino, CLI
└── hooks/
    └── on_session_start.py # Punto di ingresso del hook SessionStart
```

## Licenza

[MIT](LICENSE)
