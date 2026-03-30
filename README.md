# AI Dev CLI — Workflow-First CLI for AI Developers

[![GitHub](https://img.shields.io/github/stars/SSS-R/ai-dev-cli)](https://github.com/SSS-R/ai-dev-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Your AI development workflow, unified.** Track costs, test prompts, run batches — all from one CLI. Local-first, zero-config.

---

## Why This Exists

LiteLLM is enterprise-grade. Simon's `llm` is model-focused. **AI Dev CLI** is for **individual developers** who want:

- ✅ Cost tracking without a proxy server
- ✅ Prompt testing with cloud + local models
- ✅ Batch operations with CSV export
- ✅ Zero-config setup

---

## Quick Start

```bash
# Install
pip install ai-dev-cli

# Initialize (stores API keys securely)
ai-dev init

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
# Prompts for: OpenAI API key, Anthropic API key (optional)
# Stores in: ~/.ai-dev/config.json (encrypted)
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

### `ai-dev workflow` (Coming Soon)
Chain commands together.

```bash
ai-dev workflow run my-workflow.yaml
```

### `ai-dev sync` (Coming Soon - Paid)
Sync costs and prompts across machines.

```bash
ai-dev sync enable    # Enable cloud sync ($5/mo)
ai-dev sync status    # Check sync status
```

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
- API keys for providers you use (OpenAI, Anthropic)
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
    "ollama": {
      "base_url": "http://localhost:11434",
      "default_model": "llama3"
    }
  },
  "defaults": {
    "project": "my-app",
    "output_format": "table"
  }
}
```

---

## Examples

### Track Daily Spending
```bash
$ ai-dev cost --today

┌─────────────┬──────────────┬─────────┬──────────┐
│ Provider    │ Model        │ Tokens  │ Cost     │
├─────────────┼──────────────┼─────────┼──────────┤
│ OpenAI      │ gpt-4o       │ 12,450  │ $0.15    │
│ Anthropic   │ claude-3-5   │ 8,230   │ $0.08    │
│ Ollama      │ llama3       │ 5,000   │ $0.00    │
├─────────────┴──────────────┴─────────┴──────────┤
│ Total                              │ $0.23     │
└─────────────────────────────────────────────────┘
```

### A/B Test Prompts
```bash
$ ai-dev prompt "Explain quantum entanglement" \
    --model gpt-4o \
    --compare claude-sonnet-4 \
    --compare ollama/llama3 \
    --verbose

┌─────────────────────────────────────────────────────────────┐
│ Model Comparison                                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│ gpt-4o          │ claude-sonnet-4 │ ollama/llama3           │
├─────────────────┼─────────────────┼─────────────────────────┤
│ [Response 1]    │ [Response 2]    │ [Response 3]            │
│ Tokens: 234     │ Tokens: 256     │ Tokens: 289             │
│ Time: 1.2s      │ Time: 1.5s      │ Time: 0.8s              │
│ Cost: $0.003    │ Cost: $0.002    │ Cost: $0.00             │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Batch Processing
```bash
# Input: prompts.csv
prompt,model
"Write a tweet about AI","gpt-4o"
"Write a tweet about ML","gpt-4o"
"Write a tweet about DL","gpt-4o"

# Run
$ ai-dev batch prompts.csv --output results.csv

# Output: results.csv
prompt,model,output,tokens,cost,status
"Write a tweet about AI","gpt-4o","AI is...","45","$0.001","success"
...
```

---

## Roadmap

### v0.1 (Current) — MVP
- ✅ `ai-dev init` — Configuration setup
- ✅ `ai-dev cost` — Cost tracking
- ✅ `ai-dev prompt` — Single + A/B testing
- ✅ `ai-dev batch` — Batch operations

### v0.2 (Next) — Workflow Automation
- [ ] `ai-dev workflow` — Chain commands
- [ ] `ai-dev retry` — Retry wrapper for CLI commands
- [ ] Project-based cost filtering

### v0.3 (Planned) — Cloud Sync (Paid)
- [ ] `ai-dev sync` — Sync across machines ($5/mo)
- [ ] Team sharing ($9/mo)
- [ ] Web dashboard

---

## Privacy & Security

- **API keys** stored locally in `~/.ai-dev/config.json`
- **No cloud sync** unless you enable paid tier
- **No telemetry** — we don't collect your prompts or usage
- **Open source** — audit the code yourself

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

Built with ❤️ for AI developers who ship.
