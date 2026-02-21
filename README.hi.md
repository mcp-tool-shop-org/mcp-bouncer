<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <strong>हिन्दी</strong> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img src="assets/logo.jpg" alt="mcp-bouncer लोगो" width="280" />
</p>

<h1 align="center">mcp-bouncer</h1>

<p align="center">
  एक SessionStart hook जो आपके MCP सर्वर का स्वास्थ्य जाँचता है, टूटे हुए सर्वरों को क्वारंटाइन करता है, और जब वे वापस ऑनलाइन आते हैं तो उन्हें स्वचालित रूप से पुनः सक्रिय करता है।
</p>

<p align="center">
  <a href="#क्यों">क्यों</a> &middot;
  <a href="#यह-कैसे-काम-करता-है">यह कैसे काम करता है</a> &middot;
  <a href="#त्वरित-शुरुआत">त्वरित शुरुआत</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#लाइसेंस">लाइसेंस</a>
</p>

---

## क्यों

`.mcp.json` में कॉन्फ़िगर किए गए MCP सर्वर सेशन शुरू होने पर लोड होते हैं — चाहे वे काम कर रहे हों या नहीं। एक टूटा हुआ सर्वर context tokens बर्बाद करता है (उसके tools फिर भी दिखते हैं), tool calls को विफल करता है, और हर बार Claude खोलने पर लाल चेतावनियाँ दिखाता है। ऐसे टूटे हुए सर्वरों को पहचानने और छोड़ने का कोई अंतर्निहित तरीका नहीं है।

MCP Bouncer हर सेशन से पहले चलता है, हर सर्वर की जाँच करता है, और केवल स्वस्थ सर्वरों को ही आगे जाने देता है।

## यह कैसे काम करता है

```
सेशन शुरू होता है
  -> Bouncer .mcp.json (सक्रिय) + .mcp.health.json (क्वारंटाइन) पढ़ता है
  -> सभी सर्वरों की समानांतर स्वास्थ्य जाँच करता है
  -> टूटे हुए सक्रिय सर्वर -> क्वारंटाइन (.mcp.health.json में सहेजे जाते हैं)
  -> ठीक हुए क्वारंटाइन सर्वर -> .mcp.json में वापस बहाल किए जाते हैं
  -> सेशन में सारांश लॉग किया जाता है
```

### स्वास्थ्य जाँच

प्रत्येक सर्वर के लिए, Bouncer:

1. कमांड बाइनरी को resolve करता है (`shutil.which` / absolute path जाँच)
2. कॉन्फ़िगर किए गए args और env के साथ प्रक्रिया शुरू करता है
3. 2 सेकंड प्रतीक्षा करता है — यदि प्रक्रिया अभी भी चल रही है, तो वह पास हो जाती है

यह सबसे सामान्य विफलताओं को पकड़ता है: गायब binaries, टूटी हुई dependencies, import errors, और startup पर crash। तेज़, विश्वसनीय, protocol-स्तर की कमज़ोरी से मुक्त।

### क्वारंटाइन

टूटे हुए सर्वरों को `.mcp.health.json` में उनके पूरे कॉन्फ़िगरेशन के साथ सुरक्षित रखा जाता है:

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

हर सेशन में, क्वारंटाइन किए गए सर्वरों का फिर से परीक्षण होता है। जब वे पास हो जाते हैं, तो उन्हें स्वचालित रूप से `.mcp.json` में वापस बहाल कर दिया जाता है — किसी मैन्युअल हस्तक्षेप की आवश्यकता नहीं।

## त्वरित शुरुआत

### 1. Clone करें

```bash
git clone https://github.com/mcp-tool-shop-org/mcp-bouncer.git
```

### 2. Hook रजिस्टर करें

अपने Claude Code settings (`settings.local.json` या `.claude/settings.json`) में जोड़ें:

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

### 3. तैयार है

अगले सेशन से, Bouncer स्वचालित रूप से चलेगा। टूटे हुए सर्वर क्वारंटाइन हो जाएंगे, स्वस्थ सर्वर चलते रहेंगे। सेशन लॉग में एक सारांश दिखेगा:

```
MCP Bouncer: 3/4 healthy, quarantined: voice-soundboard
```

## CLI

सीधे diagnostics के लिए चलाएं:

```bash
# देखें क्या सक्रिय है बनाम क्वारंटाइन में
python bouncer.py status

# अभी स्वास्थ्य जाँच चलाएं (जैसे hook करता है)
python bouncer.py check

# सभी क्वारंटाइन सर्वरों को जबरदस्ती बहाल करें
python bouncer.py restore
```

सभी कमांड एक वैकल्पिक path argument स्वीकार करते हैं (डिफ़ॉल्ट: वर्तमान डायरेक्टरी में `.mcp.json`):

```bash
python bouncer.py status /path/to/.mcp.json
```

## डिज़ाइन निर्णय

- **कोई dependency नहीं** — केवल stdlib, जहाँ भी Python 3.10+ हो वहाँ चलता है
- **Fail-safe** — अगर Bouncer खुद crash हो जाए, `.mcp.json` अपरिवर्तित रहता है
- **संरचना सुरक्षित** — केवल `mcpServers` key को छूता है, `$schema`, `defaults`, और अन्य keys को यथावत छोड़ता है
- **समानांतर जाँच** — `ThreadPoolExecutor` के साथ 5 workers, 10-सेकंड hook timeout के भीतर पूरा हो जाता है
- **एक-सेशन की देरी** — सेशन के बीच में टूटा सर्वर अगले सेशन की शुरुआत में क्वारंटाइन होगा (Claude Code mid-session config changes को सपोर्ट नहीं करता)

## फ़ाइलें

```
mcp-bouncer/
├── bouncer.py              # Core: स्वास्थ्य जाँच, क्वारंटाइन, बहाली, CLI
└── hooks/
    └── on_session_start.py # SessionStart hook entry point
```

## लाइसेंस

[MIT](LICENSE)
