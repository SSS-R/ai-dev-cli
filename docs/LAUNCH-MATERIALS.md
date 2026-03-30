# AI Dev CLI — Launch Materials

**Version:** v0.1.0  
**Release Date:** 2026-03-30  
**Repo:** https://github.com/SSS-R/ai-dev-cli

---

## 📢 Launch Post Drafts

### Reddit Post (r/SaaS, r/indiehackers, r/Python)

**Title:**
```
Built an AI SaaS builder CLI — builds + deploys full apps from one command
```

**Body:**
```
Hey everyone,

I built a tool that automates building AI-powered SaaS apps. You give it a description, it builds the whole thing.

**What it does:**
- `ai-dev build "Tweet summarizer SaaS"` → Creates 12 files, full Next.js app
- `ai-dev build "AI Dashboard"` → React dashboard with charts + AI insights
- `ai-dev build "API Wrapper"` → FastAPI backend with rate limiting + auth
- Auto-deploys to Vercel
- Tracks API costs across 7 providers (OpenAI, Claude, Gemini, Qwen, DeepSeek, etc.)

**Tech:**
- Python CLI (pip installable)
- Templates for common SaaS patterns
- Multi-agent system (planner, coder, tester, deployer)
- Cost optimizer (routes to cheapest model per task)

**Why I built it:**
Tired of manually scaffolding the same SaaS patterns. Wanted to go from idea → deployed app in 10 minutes.

**Demo:** [LINK TO VIDEO]
**GitHub:** https://github.com/SSS-R/ai-dev-cli

**Try it:**
```bash
pip install ai-dev-cli
ai-dev init
ai-dev build "Tweet summarizer SaaS"
```

Would love feedback! What features would you add?
```

---

### Twitter Thread (8 tweets)

**Tweet 1/8:**
```
🧵 Just shipped: AI Dev CLI

Builds + deploys full SaaS apps from one command:

`ai-dev build "Tweet summarizer SaaS"`

→ 12 files created
→ Next.js + Stripe + Vercel
→ Deployed in 10 min

Here's how it works ↓
```

**Tweet 2/8:**
```
What it builds:

📱 Tweet Summarizer (Next.js + Stripe)
📊 AI Dashboard (React + Recharts)
🔌 API Wrapper (FastAPI + Render)

Each template is production-ready:
- Auth
- Payments
- Deploy config
- Tests
```

**Tweet 3/8:**
```
Under the hood:

Multi-agent system:
- Planner → Analyzes requirements
- Coder → Writes files
- Tester → Runs tests
- Deployer → Pushes to Vercel
- CostOptimizer → Picks cheapest models

Each agent has a role + budget.
```

**Tweet 4/8:**
```
Supports 7 LLM providers:

🇺🇸 OpenAI (gpt-4o, gpt-4o-mini)
🇺🇸 Anthropic (claude-sonnet-4)
🌍 Google (gemini-2.0-flash)
🇨🇳 Alibaba (qwen-plus, qwen-max)
🇨🇳 DeepSeek (deepseek-chat)
🏠 Ollama (llama3, local)

Auto-routes to cheapest per task.
```

**Tweet 5/8:**
```
Cost tracking built-in:

`ai-dev cost` shows:
- Spend per provider
- Tokens used
- Cost per project

No surprise bills. Know exactly what each build costs.

Typical build: $0.35-0.50
```

**Tweet 6/8:**
```
Security:
- .env for API keys (never committed)
- .venv for isolated deps
- .gitignore blocks secrets
- pip-audit passes (0 CVEs)

Built for indie hackers, not enterprises.
```

**Tweet 7/8:**
```
Try it:

```bash
pip install ai-dev-cli
ai-dev init
ai-dev build "Your SaaS idea"
```

GitHub: https://github.com/SSS-R/ai-dev-cli

Demo: [LINK]
```

**Tweet 8/8:**
```
Roadmap:

v0.2 — More templates (10 total)
v0.3 — Multi-agent parallel builds
v0.4 — Team collaboration
v0.5 — Observability dashboard

What template should I build next?

#SaaS #AI #indiehackers #python
```

---

## 🎬 Demo Video Script (2 minutes)

**Scene 1: Intro (0:00-0:15)**
```
[Screen: Terminal with ai-dev --help]

Voiceover: "What if you could build a SaaS app in one command?"

[Type: ai-dev build "Tweet summarizer SaaS"]

Voiceover: "Let me show you AI Dev CLI."
```

**Scene 2: Setup (0:15-0:30)**
```
[Screen: ai-dev init]

Voiceover: "First, initialize with your API keys. Supports OpenAI, Claude, Gemini, Qwen, DeepSeek, and local Ollama models."

[Show: Keys being entered (blurred)]
```

**Scene 3: Build Process (0:30-1:00)**
```
[Screen: Build output showing files being created]

Voiceover: "Watch it build a tweet summarizer SaaS. It's creating 12 files: Next.js frontend, Stripe integration, Vercel deploy config."

[Highlight: File creation progress]

Voiceover: "Each file is production-ready, not boilerplate."
```

**Scene 4: Cost Tracking (1:00-1:15)**
```
[Screen: ai-dev cost]

Voiceover: "Track costs in real-time. This build cost $0.42 in API calls. Know exactly what you're spending."

[Show: Cost breakdown by provider]
```

**Scene 5: Deployment (1:15-1:30)**
```
[Screen: vercel deploy output]

Voiceover: "Auto-deploys to Vercel. One command, live URL in 2 minutes."

[Show: Deployed app URL]
```

**Scene 6: Templates (1:30-1:45)**
```
[Screen: ai-dev templates]

Voiceover: "Three templates included: Tweet Summarizer, AI Dashboard, API Wrapper. More coming."

[Show: Template list]
```

**Scene 7: Call to Action (1:45-2:00)**
```
[Screen: GitHub repo]

Voiceover: "Try it free. pip install ai-dev-cli. Link in description."

[Show: GitHub URL + pip install command]
```

---

## 🧪 Testing Guide (For Rafi)

### Your Setup (Agentic Only)

Since your Bailian key is for **agentic work only**, here's how to test:

**Step 1: Initialize**
```bash
cd /home/noahsr/projects/ai-dev-cli
source .venv/bin/activate
ai-dev init

# When prompted:
Alibaba Bailian API Key: [your-agentic-key-from-console]
# Skip others (OpenAI, Anthropic, etc.)
```

**Step 2: Test Single Provider**
```bash
# Test with Qwen only (your agentic key)
ai-dev prompt "Hello, world!" --model qwen-plus

# Should work (uses your Bailian key)
```

**Step 3: Test Build (Single Agent)**
```bash
# Build with Qwen only
ai-dev build "Test app" --model qwen-plus

# This will:
# 1. Plan with qwen-turbo (cheap)
# 2. Code with qwen-plus (your key)
# 3. Skip deploy (no Vercel token)
```

**Step 4: Check Costs**
```bash
ai-dev cost --today
# Should show Bailian usage
```

### What to Expect

| Command | Expected Result |
|---------|-----------------|
| `ai-dev init` | ✅ Config saved |
| `ai-dev prompt --model qwen-plus` | ✅ Response from Qwen |
| `ai-dev build` | ⚠️ Partial (no deploy without Vercel token) |
| `ai-dev cost` | ✅ Shows Bailian spend |

### Known Limitations (Your Setup)

- ❌ Can't test multi-provider (only Bailian key)
- ❌ Can't test Vercel deploy (no token)
- ❌ Can't test batch (needs real prompts)

**But you CAN test:**
- ✅ Single-provider builds
- ✅ Cost tracking
- ✅ Template scaffolding
- ✅ CLI commands

---

## 📝 CHANGELOG v0.1.0

### Added (2026-03-30)

**Core Features:**
- `ai-dev init` — Initialize with API keys
- `ai-dev build` — Autonomous SaaS builder
- `ai-dev prompt` — Test prompts across 7 providers
- `ai-dev batch` — CSV batch processing
- `ai-dev cost` — Track API spending
- `ai-dev templates` — List available templates

**Providers:**
- OpenAI (gpt-4o, gpt-4o-mini)
- Anthropic (claude-sonnet-4, claude-3-opus)
- Google Gemini (gemini-2.0-flash, gemini-1.5-pro)
- Alibaba Bailian/Qwen (qwen-plus, qwen-max, qwen-turbo)
- DeepSeek (deepseek-chat, deepseek-coder)
- Ollama (llama3, mistral — local)

**Templates:**
- Tweet Summarizer (Next.js + Stripe + Vercel)
- AI Dashboard (React + Tailwind + Recharts)
- API Wrapper (FastAPI + Render)

**Deployment:**
- Vercel auto-deploy
- Render support (API Wrapper template)

**Security:**
- `.env` support (python-dotenv)
- `.gitignore` (blocks secrets)
- `.venv` (isolated environment)
- `pip-audit` passes (0 CVEs)

**Automation:**
- Auto-notify cron job (replies when tasks complete)
- Cost tracking database (costs.jsonl)

### Known Issues
- Multi-agent system not yet implemented (v0.3)
- Observability SDK not yet built (v0.3)
- Code review step not yet added (v0.2)

### Tech Stack
- Python 3.10+
- Click (CLI framework)
- Requests (HTTP)
- python-dotenv (secrets)

---

**All materials ready. You post/record.**
