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

## ¿Por qué?

Los servidores MCP configurados en `.mcp.json` se cargan al inicio de la sesión, independientemente de si funcionan o no. Un servidor defectuoso consume tokens de contexto (sus herramientas aún aparecen), causa errores en las llamadas a las herramientas y muestra advertencias rojas cada vez que abres Claude. No existe una forma integrada de detectar y omitir servidores defectuosos.

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

1. Resuelve la ruta del ejecutable (`shutil.which` / verificación de ruta absoluta).
2. Inicia el proceso con sus argumentos y variables de entorno configurados.
3. Espera 2 segundos; si el proceso aún se está ejecutando, se considera que pasa la prueba.

Esto detecta los fallos más comunes: archivos ejecutables faltantes, dependencias dañadas, errores de importación y errores de inicio. Es rápido, fiable y no depende de la fragilidad a nivel de protocolo.

### Cuarentena

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

En cada sesión, los servidores en cuarentena se vuelven a probar. Cuando pasan la prueba, se restauran automáticamente a `.mcp.json`; no se requiere intervención manual.

## Cómo empezar

### Opción A: instalación con pip (recomendada)

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

En la siguiente sesión, Bouncer se ejecuta automáticamente. Los servidores defectuosos se ponen en cuarentena, y los servidores que funcionan correctamente permanecen activos. Verás una línea de resumen en el registro de la sesión:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## Interfaz de línea de comandos (CLI)

Ejecuta directamente para diagnóstico:

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

- **Sin dependencias:** solo utiliza la biblioteca estándar, funciona en cualquier sistema donde haya Python 3.10 o superior.
- **Seguro:** si Bouncer se bloquea, `.mcp.json` no se modifica.
- **Preserva la estructura:** solo modifica la clave `mcpServers` y deja intactas las claves `$schema`, `defaults` y otras.
- **Comprobaciones en paralelo:** utiliza `ThreadPoolExecutor` con 5 procesos, lo que permite completar la operación dentro del tiempo de espera del hook de 10 segundos.
- **Retraso de una sesión:** un servidor que falla durante una sesión se pone en cuarentena al inicio de la siguiente sesión (Claude Code no admite cambios de configuración durante una sesión).

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

## Seguridad y alcance de datos

MCP Bouncer es **solo local** y no tiene ninguna actividad de red.

- **Datos accedidos:** lee y escribe `.mcp.json` y `.mcp.health.json` en el directorio del proyecto. Inicia brevemente los procesos de los servidores MCP (tiempo de espera de 2 segundos) para verificar que se inician.
- **Datos NO accedidos:** no realiza solicitudes de red, no accede al contenido del usuario, ni a claves ni tokens de API. No lee la salida del servidor más allá de `stderr` en caso de fallo.
- **Sin telemetría:** no recopila ni envía nada. Todas las operaciones son locales.
- **Seguro:** si Bouncer se bloquea, `.mcp.json` no se modifica.

## Tabla de puntuación

| Categoría | Puntuación | Notas |
|----------|-------|-------|
| A. Seguridad | 10/10 | `SECURITY.md`, solo local, sin telemetría, seguro. |
| B. Manejo de errores | 10/10 | Resultados estructurados, registro limpio de `stderr`. |
| C. Documentación para el usuario | 10/10 | `README`, `CHANGELOG`, uso de la CLI. |
| D. Higiene de la implementación | 10/10 | CI + pruebas, cobertura, auditoría de dependencias, script de verificación. |
| E. Identidad | 10/10 | Logotipo, traducciones, página de inicio. |
| **Total** | **50/50** | |

## Licencia

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
