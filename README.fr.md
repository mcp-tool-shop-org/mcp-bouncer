<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## Pourquoi

Les serveurs MCP configurés dans le fichier `.mcp.json` sont chargés au démarrage de la session, qu'ils fonctionnent ou non. Un serveur défectueux gaspille des jetons de contexte (ses outils restent affichés), provoque des erreurs lors de l'utilisation des outils et affiche des avertissements rouges à chaque fois que vous ouvrez Claude. Il n'existe aucun moyen intégré de détecter et de contourner les serveurs défectueux.

MCP Bouncer s'exécute avant chaque session, vérifie chaque serveur et ne permet que les serveurs fonctionnels de démarrer.

## Fonctionnement

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### Vérification de l'état

Pour chaque serveur, Bouncer :

1. Résout le chemin du fichier exécutable (`shutil.which` / vérification du chemin absolu)
2. Lance le processus avec ses arguments et variables d'environnement configurés.
3. Attend 2 secondes : si le processus est toujours en cours d'exécution, il est considéré comme valide.

Cela permet de détecter les erreurs les plus courantes : fichiers exécutables manquants, dépendances corrompues, erreurs d'importation et bogues entraînant un plantage au démarrage. Rapide, fiable, sans fragilité au niveau du protocole.

### Mise en quarantaine

Les serveurs défectueux sont déplacés vers le fichier `.mcp.health.json`, leur configuration complète étant conservée :

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

À chaque session, les serveurs en quarantaine sont retestés. Lorsqu'ils passent les tests, ils sont automatiquement restaurés dans le fichier `.mcp.json` – aucune intervention manuelle n'est nécessaire.

## Démarrage rapide

### Option A : Installation via pip (recommandée)

```bash
pip install mcp-bouncer
```

Ensuite, enregistrez le hook dans les paramètres de Claude Code (`settings.local.json` ou `.claude/settings.json`) :

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

### Option B : Clonage du dépôt

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

### C'est tout

Lors de la prochaine session, Bouncer s'exécute automatiquement. Les serveurs défectueux sont mis en quarantaine, les serveurs fonctionnels restent actifs. Vous verrez une ligne récapitulative dans le journal de la session :

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## Interface en ligne de commande (CLI)

Exécutez-le directement pour le diagnostic :

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

Toutes les commandes acceptent un argument de chemin facultatif (par défaut, il pointe vers `.mcp.json` dans le répertoire courant) :

```bash
mcp-bouncer status /path/to/.mcp.json
```

## Choix de conception

- **Pas de dépendances** — Utilise uniquement les bibliothèques standard, fonctionne partout où Python 3.10 ou supérieur est installé.
- **Sécurité** — Si Bouncer lui-même plante, le fichier `.mcp.json` n'est pas modifié.
- **Préserve la structure** — Ne modifie que la clé `mcpServers`, laissant intactes les clés `$schema`, `defaults` et autres.
- **Vérifications parallèles** — Utilise un `ThreadPoolExecutor` avec 5 processus, ce qui permet de terminer les vérifications bien avant le délai d'expiration de 10 secondes du hook.
- **Délai d'une session** — Un serveur qui tombe en panne pendant une session est mis en quarantaine au début de la session suivante (Claude Code ne prend pas en charge les modifications de configuration pendant une session).

## Fichiers

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## Licence

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
