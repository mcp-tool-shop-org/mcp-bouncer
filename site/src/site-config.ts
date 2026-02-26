import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'MCP Bouncer',
  description: 'Health-check your MCP servers, quarantine broken ones, auto-restore when they recover.',
  logoBadge: 'MB',
  brandName: 'mcp-bouncer',
  repoUrl: 'https://github.com/mcp-tool-shop-org/mcp-bouncer',
  footerText: 'MIT Licensed — built by <a href="https://github.com/mcp-tool-shop-org" style="color:var(--color-muted);text-decoration:underline">mcp-tool-shop-org</a>',

  hero: {
    badge: 'Session Hook',
    headline: 'Health-check servers',
    headlineAccent: 'before they waste tokens.',
    description: 'A SessionStart hook that checks every MCP server at startup, quarantines broken ones, and auto-restores them when they come back online.',
    primaryCta: { href: '#quick-start', label: 'Get started' },
    secondaryCta: { href: '#how-it-works', label: 'How it works' },
    previews: [
      { label: 'Install', code: 'pip install mcp-bouncer' },
      { label: 'Status', code: 'mcp-bouncer status\n# 3/4 healthy, quarantined: voice-soundboard' },
      { label: 'Check', code: 'mcp-bouncer check\n# Re-tests all servers now' },
    ],
  },

  sections: [
    {
      kind: 'features',
      id: 'features',
      title: 'Features',
      subtitle: 'Automatic server hygiene for every session.',
      features: [
        { title: 'Health checks', desc: 'Resolves binaries, spawns each server, and verifies it stays alive for 2 seconds. Catches missing binaries, broken deps, and crash-on-startup bugs.' },
        { title: 'Auto-quarantine', desc: 'Broken servers are moved to .mcp.health.json with full config preserved. No tools leak into context, no red warnings on session start.' },
        { title: 'Auto-restore', desc: 'Every session, quarantined servers are re-tested. When they pass, they\'re automatically restored to .mcp.json — zero manual intervention.' },
      ],
    },
    {
      kind: 'features',
      id: 'how-it-works',
      title: 'How It Works',
      subtitle: 'One hook, fully automatic.',
      features: [
        { title: 'Session starts', desc: 'Bouncer reads .mcp.json (active) and .mcp.health.json (quarantined), then health-checks ALL servers in parallel.' },
        { title: 'Broken → quarantined', desc: 'Servers that fail are moved out of .mcp.json into quarantine with reason, timestamp, and fail count preserved.' },
        { title: 'Recovered → restored', desc: 'Quarantined servers that pass are moved back into .mcp.json automatically. Summary logged to session.' },
      ],
    },
    {
      kind: 'code-cards',
      id: 'quick-start',
      title: 'Quick Start',
      cards: [
        {
          title: 'pip install',
          code: 'pip install mcp-bouncer\n\n# settings.local.json or .claude/settings.json\n{\n  "hooks": {\n    "SessionStart": [{\n      "hooks": [{\n        "type": "command",\n        "command": "mcp-bouncer-hook",\n        "timeout": 10\n      }]\n    }]\n  }\n}',
        },
        {
          title: 'CLI commands',
          code: '# Show active vs quarantined\nmcp-bouncer status\n\n# Run health checks now\nmcp-bouncer check\n\n# Force-restore all quarantined\nmcp-bouncer restore\n\n# Custom .mcp.json path\nmcp-bouncer status /path/to/.mcp.json',
        },
      ],
    },
    {
      kind: 'features',
      id: 'design',
      title: 'Design',
      subtitle: 'Built for reliability.',
      features: [
        { title: 'Zero dependencies', desc: 'Stdlib only — runs anywhere Python 3.10+ lives. No pip dependency tree to manage.' },
        { title: 'Fail-safe', desc: 'If Bouncer itself crashes, .mcp.json is unchanged. Only touches the mcpServers key, preserves $schema and defaults.' },
        { title: 'Parallel checks', desc: 'ThreadPoolExecutor with 5 workers. All servers checked simultaneously, well within the 10-second hook timeout.' },
      ],
    },
  ],
};
