<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <strong>Español</strong> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer logo" width="280" />
</p>

<h1 align="center">mcp-bouncer</h1>

<p align="center">
  Un hook SessionStart que verifica el estado de tus servidores MCP, pone en cuarentena los que están rotos y los restaura automáticamente cuando vuelven a funcionar.
</p>

<p align="center">
  <a href="#por-qué">Por qué</a> &middot;
  <a href="#cómo-funciona">Cómo Funciona</a> &middot;
  <a href="#inicio-rápido">Inicio Rápido</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#licencia">Licencia</a>
</p>

---

## Por qué

Los servidores MCP configurados en `.mcp.json` se cargan al inicio de cada sesión, funcionen o no. Un servidor roto desperdicia tokens de contexto (sus herramientas siguen apareciendo), provoca llamadas fallidas y muestra advertencias en rojo cada vez que abres Claude. No existe ningún mecanismo integrado para detectar y omitir servidores rotos.

MCP Bouncer se ejecuta antes de cada sesión, verifica todos los servidores y solo deja pasar los que están en buen estado.

## Cómo Funciona

```
La sesión comienza
  -> Bouncer lee .mcp.json (activos) + .mcp.health.json (en cuarentena)
  -> Verifica el estado de TODOS los servidores en paralelo
  -> Servidores activos rotos -> cuarentena (guardados en .mcp.health.json)
  -> Servidores en cuarentena recuperados -> restaurados a .mcp.json
  -> Resumen registrado en la sesión
```

### Verificación de Estado

Para cada servidor, Bouncer:

1. Resuelve el binario del comando (`shutil.which` / verificación de ruta absoluta)
2. Lanza el proceso con sus argumentos y variables de entorno configurados
3. Espera 2 segundos — si el proceso sigue ejecutándose, pasa la verificación

Esto detecta los fallos más comunes: binarios faltantes, dependencias rotas, errores de importación y bugs que provocan un crash al arrancar. Rápido, confiable, sin fragilidades a nivel de protocolo.

### Cuarentena

Los servidores rotos se mueven a `.mcp.health.json` con toda su configuración preservada:

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

En cada sesión, los servidores en cuarentena se vuelven a probar. Cuando pasan la verificación, se restauran automáticamente a `.mcp.json` — sin necesidad de intervención manual.

## Inicio Rápido

### 1. Clonar

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

### 2. Registrar el hook

Añade esto a tu configuración de Claude Code (`settings.local.json` o `.claude/settings.json`):

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

### 3. Listo

En la próxima sesión, Bouncer se ejecuta automáticamente. Los servidores rotos quedan en cuarentena y los sanos permanecen activos. Verás una línea de resumen en el log de la sesión:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

Ejecuta directamente para diagnósticos:

```bash
# Muestra qué servidores están activos y cuáles en cuarentena
python bouncer.py status

# Ejecuta las verificaciones de estado ahora (igual que hace el hook)
python bouncer.py check

# Fuerza la restauración de todos los servidores en cuarentena
python bouncer.py restore
```

Todos los comandos aceptan un argumento de ruta opcional (por defecto usa `.mcp.json` en el directorio actual):

```bash
python bouncer.py status /path/to/.mcp.json
```

## Decisiones de Diseño

- **Sin dependencias** — solo librería estándar, funciona en cualquier lugar con Python 3.10+
- **A prueba de fallos** — si Bouncer mismo falla, `.mcp.json` no se modifica
- **Preserva la estructura** — solo toca la clave `mcpServers`, deja intactos `$schema`, `defaults` y otras claves
- **Verificaciones en paralelo** — `ThreadPoolExecutor` con 5 workers, termina bien dentro del timeout de 10 segundos del hook
- **Retraso de una sesión** — un servidor que falla a mitad de sesión queda en cuarentena al inicio de la siguiente (Claude Code no admite cambios de configuración durante la sesión)

## Archivos

```
mcp-bouncer/
├── bouncer.py              # Núcleo: verificación de estado, cuarentena, restauración, CLI
└── hooks/
    └── on_session_start.py # Punto de entrada del hook SessionStart
```

## Licencia

[MIT](LICENSE)
