<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## ¿Por qué?

Los servidores MCP configurados en `.mcp.json` se cargan al inicio de la sesión, independientemente de si funcionan o no. Un servidor defectuoso desperdicia tokens de contexto (sus herramientas aún aparecen), causa errores en las llamadas a las herramientas y muestra advertencias rojas cada vez que abres Claude. No existe una forma integrada de detectar y omitir servidores defectuosos.

MCP Bouncer se ejecuta antes de cada sesión, verifica cada servidor y solo permite que los servidores que funcionan correctamente continúen.

## ¿Cómo funciona?

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### Comprobación de estado

Para cada servidor, Bouncer:

1. Resuelve el archivo ejecutable del comando (`shutil.which` / verificación de ruta absoluta).
2. Inicia el proceso con sus argumentos y variables de entorno configurados.
3. Espera 2 segundos; si el proceso aún se está ejecutando, se considera que funciona correctamente.

Esto detecta los fallos más comunes: archivos ejecutables faltantes, dependencias dañadas, errores de importación y errores que provocan que el programa se cierre al inicio. Es rápido, fiable y no depende de protocolos complejos.

### Aislamiento

Los servidores defectuosos se mueven a `.mcp.health.json` con su configuración completa preservada:

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

En cada sesión, los servidores aislados se vuelven a probar. Cuando funcionan correctamente, se restauran automáticamente a `.mcp.json` sin necesidad de intervención manual.

## Inicio rápido

### Opción A: instalación con pip (recomendado)

```bash
pip install mcp-bouncer
```

Luego, registra el hook en la configuración de Claude Code (`settings.local.json` o `.claude/settings.json`):

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

### Opción B: clonar el repositorio

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

### ¡Listo!

En la siguiente sesión, Bouncer se ejecuta automáticamente. Los servidores defectuosos se aíslan, y los servidores que funcionan correctamente permanecen activos. Verás una línea de resumen en el registro de la sesión:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## Interfaz de línea de comandos (CLI)

Ejecútalo directamente para obtener información de diagnóstico:

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

Todos los comandos aceptan un argumento de ruta opcional (por defecto, `.mcp.json` en el directorio actual):

```bash
mcp-bouncer status /path/to/.mcp.json
```

## Decisiones de diseño

- **Sin dependencias** — solo utiliza la biblioteca estándar, funciona en cualquier lugar donde haya Python 3.10 o superior.
- **Seguro** — si Bouncer se bloquea, `.mcp.json` no se modifica.
- **Preserva la estructura** — solo modifica la clave `mcpServers`, dejando intactas las claves `$schema`, `defaults` y otras.
- **Comprobaciones en paralelo** — utiliza `ThreadPoolExecutor` con 5 procesos, completándose bien dentro del tiempo de espera del hook de 10 segundos.
- **Retraso de una sesión** — un servidor que falla durante una sesión se aísla al inicio de la siguiente sesión (Claude Code no admite cambios de configuración durante la sesión).

## Archivos

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## Licencia

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
