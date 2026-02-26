<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## क्यों?

`.mcp.json` फ़ाइल में कॉन्फ़िगर किए गए MCP सर्वर, सत्र शुरू होते ही लोड हो जाते हैं, चाहे वे ठीक से काम करें या नहीं। एक खराब सर्वर संदर्भ टोकन बर्बाद करता है (इसके उपकरण अभी भी दिखाई देते हैं), टूल कॉल विफल हो जाते हैं, और हर बार जब आप क्लाउड खोलते हैं, तो यह लाल चेतावनी दिखाता है। खराब सर्वरों का पता लगाने और उन्हें छोड़ने का कोई अंतर्निहित तरीका नहीं है।

MCP बाउन्सर प्रत्येक सत्र से पहले चलता है, प्रत्येक सर्वर की जांच करता है, और केवल स्वस्थ सर्वरों को ही आगे बढ़ने देता है।

## यह कैसे काम करता है

```
Session starts
  -> Bouncer reads .mcp.json (active) + .mcp.health.json (quarantined)
  -> Health-checks ALL servers in parallel
  -> Broken active servers -> quarantined (saved to .mcp.health.json)
  -> Recovered quarantined servers -> restored to .mcp.json
  -> Summary logged to session
```

### स्वास्थ्य जांच

प्रत्येक सर्वर के लिए, बाउन्सर:

1. कमांड बाइनरी को हल करता है (`shutil.which` / पूर्ण पथ जांच)
2. अपने कॉन्फ़िगर किए गए तर्क और वातावरण के साथ प्रक्रिया शुरू करता है
3. 2 सेकंड तक प्रतीक्षा करता है — यदि प्रक्रिया अभी भी चल रही है, तो यह पास हो जाता है

यह सबसे आम विफलताओं को पकड़ता है: गायब बाइनरी, टूटे हुए निर्भरताएं, आयात त्रुटियां, और स्टार्टअप पर होने वाली क्रैश। यह तेज़, विश्वसनीय है, और इसमें प्रोटोकॉल-स्तरीय कमजोरियां नहीं हैं।

### क्वारंटाइन

खराब सर्वरों को उनके पूर्ण कॉन्फ़िगरेशन के साथ `.mcp.health.json` में स्थानांतरित कर दिया जाता है:

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

प्रत्येक सत्र में, क्वारंटाइन किए गए सर्वरों का पुन: परीक्षण किया जाता है। जब वे पास हो जाते हैं, तो उन्हें स्वचालित रूप से `.mcp.json` में बहाल कर दिया जाता है — किसी भी मैनुअल हस्तक्षेप की आवश्यकता नहीं होती है।

## शुरुआत कैसे करें

### विकल्प A: `pip install` (अनुशंसित)

```bash
pip install mcp-bouncer
```

फिर क्लाउड कोड सेटिंग्स में हुक को पंजीकृत करें (`settings.local.json` या `.claude/settings.json`):

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

### विकल्प B: रिपॉजिटरी को क्लोन करें

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

### हो गया

अगले सत्र में, बाउन्सर स्वचालित रूप से चलेगा। खराब सर्वरों को क्वारंटाइन कर दिया जाएगा, स्वस्थ सर्वर बने रहेंगे। आपको सत्र लॉग में एक सारांश पंक्ति दिखाई देगी:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## कमांड लाइन इंटरफेस (CLI)

डायग्नोस्टिक्स के लिए सीधे चलाएं:

```bash
# Show what's active vs quarantined
mcp-bouncer status

# Run health checks now (same as hook does)
mcp-bouncer check

# Force-restore all quarantined servers
mcp-bouncer restore
```

सभी कमांड एक वैकल्पिक पथ तर्क स्वीकार करते हैं (डिफ़ॉल्ट रूप से वर्तमान निर्देशिका में `.mcp.json`):

```bash
mcp-bouncer status /path/to/.mcp.json
```

## डिज़ाइन निर्णय

- **कोई निर्भरता नहीं** — केवल मानक लाइब्रेरी, जहां भी Python 3.10+ उपलब्ध है, वहां चलता है
- **सुरक्षित** — यदि बाउन्सर स्वयं क्रैश होता है, तो `.mcp.json` अपरिवर्तित रहता है
- **संरचना को संरक्षित करता है** — केवल `mcpServers` कुंजी को छूता है, `$schema`, `defaults`, और अन्य कुंजियों को अपरिवर्तित रखता है
- **समानांतर जांच** — 5 श्रमिकों के साथ `ThreadPoolExecutor`, 10-सेकंड के हुक टाइमआउट के भीतर अच्छी तरह से पूरा हो जाता है
- **एक-सत्र विलंब** — एक सर्वर जो सत्र के दौरान खराब हो जाता है, उसे अगले सत्र की शुरुआत में क्वारंटाइन कर दिया जाता है (क्लाउड कोड सत्र के बीच कॉन्फ़िगरेशन में बदलाव का समर्थन नहीं करता है)

## फ़ाइलें

```
mcp-bouncer/
├── src/mcp_bouncer/        # Package (installed via pip)
│   ├── bouncer.py          # Core: health check, quarantine, restore, CLI
│   └── hook.py             # SessionStart hook entry point
├── bouncer.py              # Wrapper for cloned-repo usage
└── hooks/
    └── on_session_start.py # Wrapper for cloned-repo usage
```

## लाइसेंस

MIT

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
