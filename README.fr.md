<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <strong>Français</strong> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer logo" width="280" />
</p>

<p align="center">
  Un hook SessionStart qui vérifie l'état de santé de vos serveurs MCP, met en quarantaine ceux qui sont défaillants, et les restaure automatiquement dès qu'ils reviennent en ligne.
</p>

<p align="center">
  <a href="#pourquoi">Pourquoi</a> &middot;
  <a href="#comment-ça-fonctionne">Comment ça fonctionne</a> &middot;
  <a href="#démarrage-rapide">Démarrage rapide</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#licence">Licence</a>
</p>

---

## Pourquoi

Les serveurs MCP configurés dans `.mcp.json` se chargent au démarrage de la session, qu'ils fonctionnent ou non. Un serveur défaillant gaspille des tokens de contexte (ses outils apparaissent quand même), provoque des appels d'outils en échec, et affiche des avertissements rouges à chaque ouverture de Claude. Il n'existe aucun mécanisme natif pour détecter et ignorer les serveurs défaillants.

MCP Bouncer s'exécute avant chaque session, vérifie chaque serveur, et ne laisse passer que ceux qui sont en bonne santé.

## Comment ça fonctionne

```
Démarrage de la session
  -> Bouncer lit .mcp.json (actifs) + .mcp.health.json (en quarantaine)
  -> Vérifie l'état de santé de TOUS les serveurs en parallèle
  -> Serveurs actifs défaillants -> mis en quarantaine (sauvegardés dans .mcp.health.json)
  -> Serveurs en quarantaine rétablis -> restaurés dans .mcp.json
  -> Résumé enregistré dans la session
```

### Vérification de santé

Pour chaque serveur, Bouncer :

1. Résout le binaire de la commande (`shutil.which` / vérification du chemin absolu)
2. Lance le processus avec ses arguments et variables d'environnement configurés
3. Attend 2 secondes — si le processus est toujours en cours d'exécution, le test est réussi

Cela détecte les pannes les plus courantes : binaires manquants, dépendances cassées, erreurs d'import, et plantages au démarrage. Rapide, fiable, sans fragilité au niveau du protocole.

### Quarantaine

Les serveurs défaillants sont déplacés vers `.mcp.health.json` avec leur configuration complète préservée :

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

À chaque session, les serveurs en quarantaine sont re-testés. Lorsqu'ils passent le test, ils sont automatiquement restaurés dans `.mcp.json` — aucune intervention manuelle n'est nécessaire.

## Démarrage rapide

### Option A : pip install (recommandé)

```bash
pip install mcp-bouncer
```

Ajoutez ceci à vos paramètres Claude Code (`settings.local.json` ou `.claude/settings.json`) :

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

### Option B : Cloner le dépôt

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

Ajoutez ceci à vos paramètres Claude Code (`settings.local.json` ou `.claude/settings.json`) :

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

### C'est prêt

Dès la prochaine session, Bouncer s'exécute automatiquement. Les serveurs défaillants sont mis en quarantaine, les serveurs sains restent actifs. Un résumé apparaît dans le journal de session :

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

Exécutez directement pour un diagnostic :

```bash
# Afficher ce qui est actif vs en quarantaine
mcp-bouncer status

# Lancer les vérifications de santé maintenant (identique au hook)
mcp-bouncer check

# Forcer la restauration de tous les serveurs en quarantaine
mcp-bouncer restore
```

Toutes les commandes acceptent un argument de chemin optionnel (par défaut `.mcp.json` dans le répertoire courant) :

```bash
mcp-bouncer status /path/to/.mcp.json
```

## Choix de conception

- **Aucune dépendance** — stdlib uniquement, fonctionne partout où Python 3.10+ est installé
- **Sécurité en cas de panne** — si Bouncer lui-même plante, `.mcp.json` reste inchangé
- **Structure préservée** — ne touche que la clé `mcpServers`, laisse `$schema`, `defaults` et les autres clés intactes
- **Vérifications parallèles** — `ThreadPoolExecutor` avec 5 workers, se termine bien avant le délai d'expiration du hook de 10 secondes
- **Délai d'une session** — un serveur qui tombe en panne en cours de session est mis en quarantaine au démarrage de la session suivante (Claude Code ne prend pas en charge les changements de configuration en cours de session)

## Fichiers

```
mcp-bouncer/
├── src/mcp_bouncer/        # Paquet (installé via pip)
│   ├── bouncer.py          # Noyau : vérification de santé, quarantaine, restauration, CLI
│   └── hook.py             # Point d'entrée du hook SessionStart
├── bouncer.py              # Wrapper pour utilisation via clone
└── hooks/
    └── on_session_start.py # Wrapper pour utilisation via clone
```

## Licence

[MIT](LICENSE)
