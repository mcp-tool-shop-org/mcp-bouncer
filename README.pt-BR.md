<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <strong>Português</strong>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer logo" width="280" />
</p>

<h1 align="center">mcp-bouncer</h1>

<p align="center">
  Um hook SessionStart que verifica a saúde dos seus servidores MCP, coloca em quarentena os que estão quebrados e os restaura automaticamente quando voltam a funcionar.
</p>

<p align="center">
  <a href="#por-que">Por que</a> &middot;
  <a href="#como-funciona">Como funciona</a> &middot;
  <a href="#início-rápido">Início rápido</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#licença">Licença</a>
</p>

---

## Por que

Os servidores MCP configurados em `.mcp.json` carregam no início de cada sessão, funcionando ou não. Um servidor quebrado desperdiça tokens de contexto (suas ferramentas ainda aparecem), causa falhas em chamadas de ferramentas e exibe avisos vermelhos toda vez que você abre o Claude. Não existe nenhum mecanismo nativo para detectar e ignorar servidores com problema.

O MCP Bouncer roda antes de cada sessão, verifica cada servidor e deixa passar somente os que estão saudáveis.

## Como funciona

```
A sessão inicia
  -> Bouncer lê .mcp.json (ativos) + .mcp.health.json (em quarentena)
  -> Verifica a saúde de TODOS os servidores em paralelo
  -> Servidores ativos quebrados -> quarentena (salvos em .mcp.health.json)
  -> Servidores em quarentena recuperados -> restaurados em .mcp.json
  -> Resumo registrado na sessão
```

### Verificação de saúde

Para cada servidor, o Bouncer:

1. Resolve o binário do comando (`shutil.which` / verificação de caminho absoluto)
2. Inicia o processo com os args e env configurados
3. Aguarda 2 segundos — se o processo ainda estiver rodando, ele passa

Isso captura as falhas mais comuns: binários ausentes, dependências quebradas, erros de importação e crashes na inicialização. Rápido, confiável, sem fragilidade no nível do protocolo.

### Quarentena

Servidores quebrados são movidos para `.mcp.health.json` com toda a configuração preservada:

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

A cada sessão, os servidores em quarentena são testados novamente. Quando passam, são restaurados automaticamente para `.mcp.json` — sem necessidade de intervenção manual.

## Início rápido

### 1. Clone

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

### 2. Registre o hook

Adicione às suas configurações do Claude Code (`settings.local.json` ou `.claude/settings.json`):

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

### 3. Pronto

Na próxima sessão, o Bouncer roda automaticamente. Servidores com problema vão para a quarentena, os saudáveis permanecem ativos. Você verá uma linha de resumo no log da sessão:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

Execute diretamente para diagnósticos:

```bash
# Mostrar o que está ativo vs em quarentena
python bouncer.py status

# Rodar as verificações de saúde agora (igual ao que o hook faz)
python bouncer.py check

# Forçar a restauração de todos os servidores em quarentena
python bouncer.py restore
```

Todos os comandos aceitam um argumento de caminho opcional (padrão: `.mcp.json` no diretório atual):

```bash
python bouncer.py status /path/to/.mcp.json
```

## Decisões de design

- **Sem dependências** — apenas stdlib, roda em qualquer lugar com Python 3.10+
- **Fail-safe** — se o próprio Bouncer travar, `.mcp.json` permanece inalterado
- **Estrutura preservada** — toca apenas a chave `mcpServers`, deixa `$schema`, `defaults` e outras chaves intactas
- **Verificações paralelas** — `ThreadPoolExecutor` com 5 workers, termina com folga dentro do timeout de 10 segundos do hook
- **Atraso de uma sessão** — um servidor que quebra no meio de uma sessão é colocado em quarentena no início da sessão seguinte (o Claude Code não suporta alterações de configuração durante a sessão)

## Arquivos

```
mcp-bouncer/
├── bouncer.py              # Core: verificação de saúde, quarentena, restauração, CLI
└── hooks/
    └── on_session_start.py # Ponto de entrada do hook SessionStart
```

## Licença

[MIT](LICENSE)
