# AI Dev CLI — Multi-Agent SaaS Builder

[![GitHub](https://img.shields.io/github/stars/SSS-R/ai-dev-cli)](https://github.com/SSS-R/ai-dev-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Multi-Agent SaaS Builder.** 5 AI agents (Planner, Builder, Tester, Fixer, Deployer) work together to build + deploy your app. For indie hackers who ship.

---

## Why This Exists

LiteLLM is enterprise-grade. Simon's `llm` is model-focused. **AI Dev CLI** is for **individual developers** who want to:

- ✅ Build SaaS apps autonomously (5 AI agents work together)
- ✅ Test prompts with cloud + local models (7 providers supported)
- ✅ Track costs across providers (no proxy server needed)
- ✅ Run batch operations with CSV export
- ✅ Zero-config setup

---

## Quick Start

```bash
# Install
pip install ai-dev-cli

# Initialize (stores API keys securely)
ai-dev init

# Build a SaaS app (multi-agent system)
ai-dev build "Tweet summarizer SaaS"

# Track your spending
ai-dev cost

# Test prompts
ai-dev prompt "Hello, world!" --model gpt-4o
ai-dev prompt "Hello, world!" --model ollama/llama3 --compare

# Run batches
ai-dev batch input.csv --output results.csv
```

---

## Commands

### `ai-dev init`
Initialize configuration and store API keys securely.

```bash
ai-dev init
# Prompts for: OpenAI, Anthropic, Gemini, Bailian (Qwen), DeepSeek API keys
# Stores in: ~/.ai-dev/config.json
# ⚠️ Plain text - don't share this file
```

### `ai-dev cost`
View your LLM spending across providers.

```bash
ai-dev cost                    # All-time spending
ai-dev cost --today            # Today only
ai-dev cost --project my-app   # Filter by project
```

### `ai-dev prompt`
Test prompts with single or multiple models.

```bash
# Single model
ai-dev prompt "Write a haiku about coding" --model gpt-4o

# A/B comparison
ai-dev prompt "Write a haiku" --model gpt-4o --compare claude-sonnet-4 --compare ollama/llama3

# Output formats
ai-dev prompt "..." --json      # JSON output
ai-dev prompt "..." --verbose   # Show token counts, timing
```

### `ai-dev batch`
Run prompts in bulk from CSV.

```bash
# Input CSV format: prompt,model,expected_output (optional)
ai-dev batch prompts.csv --output results.csv

# With concurrency
ai-dev batch prompts.csv --workers 4 --output results.json
```

### `ai-dev build` 🆕
Build a complete SaaS app with multi-agent system.

```bash
# Uses 5 AI agents: Planner → Builder → Tester → Fixer → Deployer
ai-dev build "Tweet summarizer SaaS"

# Specify provider (default: bailian for agentic work)
ai-dev build "AI Dashboard" --provider bailian

# Adjust retry limit for auto-fix
ai-dev build "API Wrapper" --max-retries 5

# Verbose output
ai-dev build "My App" --verbose
```

**What happens:**
1. **PlannerAgent** — Creates architecture (12 files, tech stack)
2. **BuilderAgent** — Writes all code files
3. **TesterAgent** — Runs tests, reports failures
4. **FixerAgent** — Auto-fixes test failures (max 3 retries)
5. **DeployerAgent** — Deploys to Vercel/Render

**Templates available:**
- Tweet Summarizer (Next.js + Stripe)
- AI Dashboard (React + Recharts)
- API Wrapper (FastAPI + Render)

### `ai-dev templates`
List available SaaS templates.

```bash
ai-dev templates
ai-dev templates --show tweet-summarizer
```

---

## Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 OrchestratorAgent                           │
│  - Routes tasks to specialist agents                        │
│  - Tracks success rate, retries, costs                      │
│  - Enforces full loop: Plan → Build → Test → Fix → Deploy   │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┬───────────────────┬──────────────┐
        ↓                   ↓                   ↓              ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐  ┌──────────────┐
│ PlannerAgent │ → │ BuilderAgent │ → │ TesterAgent │  │ FixerAgent   │
│ (qwen-turbo) │   │ (qwen-plus)  │   │ (qwen-turbo)│  │ (qwen-plus)  │
│ - Analyzes   │   │ - Writes     │   │ - Runs      │  │ - Auto-fixes │
│ - Creates    │   │ - Scaffolds  │   │ - Reports   │  │ - Retries   │
│ - Plans      │   │ - Commits    │   │ - Fails     │  │ - Repairs   │
└──────────────┘   └──────────────┘   └──────────────┘  └──────────────┘
                                                      ↓
                                              ┌──────────────┐
                                              │DeployerAgent │
                                              │ (qwen-turbo) │
                                              │ - Vercel     │
                                              │ - Render     │
                                              └──────────────┘
```

### Enforced Loop

```
Plan → Build → Test → [FAIL?] → Fix → Retest (max 3 retries) → Deploy
```

**Success tracking:**
- Tracks retries per build
- Tracks success rate
- Fails gracefully after max retries
- Reports what worked/failed

---

## Installation

### From PyPI (Recommended)
```bash
pip install ai-dev-cli
```

### From Source
```bash
git clone https://github.com/SSS-R/ai-dev-cli.git
cd ai-dev-cli
pip install -e .

# Run
python3 -m ai_dev_cli.cli --help
```

### Requirements
- Python 3.10+
- API keys for providers you use (OpenAI, Anthropic, Gemini, Bailian, DeepSeek)
- Ollama (optional, for local models)

---

## Configuration

Config stored in `~/.ai-dev/config.json`:

```json
{
  "providers": {
    "openai": {
      "api_key": "sk-...",
      "default_model": "gpt-4o"
    },
    "anthropic": {
      "api_key": "sk-ant-...",
      "default_model": "claude-sonnet-4-20250514"
    },
    "gemini": {
      "api_key": "...",
      "default_model": "gemini-2.0-flash"
    },
    "bailian": {
      "api_key": "...",
      "default_model": "qwen-plus"
    },
    "deepseek": {
      "api_key": "...",
      "default_model": "deepseek-chat"
    },
    "ollama": {
      "base_url": "http://localhost:11434",
      "default_model": "llama3"
    }
  },
  "defaults": {
    "project": "default",
    "output_format": "table"
  }
}
```

### Provider Fallback

AI Dev CLI automatically falls back through providers:
```
bailian → openai → gemini
```

If one provider fails, it tries the next. No manual intervention needed.

---

## Security

### API Key Storage
- **Location:** `~/.ai-dev/config.json`
- **Format:** Plain text JSON
- **⚠️ Warning:** Don't share this file or commit to git
- **Protection:** Added to `.gitignore` by default

### What's Protected
- ✅ API keys never logged
- ✅ Keys sent directly to providers (no third-party)
- ✅ Local-first (no cloud sync unless you enable it)

### What's NOT Protected
- ❌ Config file is NOT encrypted (plain text)
- ❌ Anyone with file access can read keys
- ❌ Backup your keys securely

---

## Supported Providers

| Provider | Models | Pricing |
|----------|--------|---------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | $0.0025-0.01/1K tokens |
| **Anthropic** | claude-sonnet-4, claude-3-opus | $0.003-0.015/1K tokens |
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro | $0.000075-0.00125/1K |
| **Bailian (Qwen)** | qwen-plus, qwen-max, qwen-turbo | $0.0002-0.005/1K tokens |
| **DeepSeek** | deepseek-chat, deepseek-coder | $0.00027-0.0011/1K tokens |
| **Ollama** | llama3, mistral (local) | Free (local) |

---

## Project Structure

```
ai-dev-cli/
├── ai_dev_cli/
│   ├── __init__.py           # Version, author
│   ├── cli.py                # CLI commands (6 commands)
│   ├── providers.py          # LLM provider integrations
│   ├── multi_agent.py        # Multi-agent system (6 agents)
│   └── agent_refine.py       # Auto-fix logic for test failures
├── docs/
│   ├── MULTI-AGENT.md        # Architecture documentation
│   └── LAUNCH-MATERIALS.md   # Reddit/Twitter launch posts
├── tests/
│   └── test_cli.py           # Test suite (8/9 passing)
├── templates/
│   ├── tweet-summarizer/     # Next.js + Stripe template
│   ├── ai-dashboard/         # React + Recharts template
│   └── api-wrapper/          # FastAPI + Render template
├── README.md
├── pyproject.toml
├── LICENSE
├── .gitignore
└── .env.example
```

---

## Roadmap

### v0.2 (Current)
- ✅ Multi-agent system (6 role-based agents)
- ✅ Enforced refine loop (plan→build→test→fix→deploy)
- ✅ Provider-agnostic (bailian → openai → gemini)
- ✅ Success tracking (retries, success rate, cost)
- ✅ Security fixes (honest about plain text config)

### v0.3 (Next)
- [ ] Parallel agent execution
- [ ] Cost optimization dashboard
- [ ] Team collaboration

### v0.4 (Future)
- [ ] Observability SDK
- [ ] Custom agent roles
- [ ] Enterprise SSO

---

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests (pytest)
4. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Inspired by:
- [simonw/llm](https://github.com/simonw/llm) — Beautiful CLI design
- [BerriAI/litellm](https://github.com/BerriAI/litellm) — Multi-provider support
- [AgentScope](https://github.com/agentscope-ai/agentscope) — Multi-agent architecture
- [agency-agents](https://github.com/msitarzewski/agency-agents) — Role-based agents

---

**Built for indie hackers who ship.** 🚀
