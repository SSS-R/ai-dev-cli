# AI Dev CLI — Multi-Agent System

**Version:** v0.2.0 (2026-04-01)

---

## 🤖 Multi-Agent Architecture

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

---

## 🔄 Enforced Loop

```
Plan → Build → Test → [FAIL?] → Fix → Retest → [PASS?] → Deploy
                         ↑___________|
                         (max 3 retries)
```

**If tests fail:**
1. TesterAgent reports error
2. FixerAgent analyzes + generates fix
3. TesterAgent retests
4. Repeat until pass OR max retries reached

**Success criteria:**
- ✅ Plan created
- ✅ All files built
- ✅ Tests pass (or max retries reached)
- ✅ Deploy config ready

**Success rate tracked:** `(successful_steps / 4) * 100`

---

## 📊 Agent Roles

| Agent | Model | Cost | Responsibility |
|-------|-------|------|----------------|
| **Planner** | qwen-turbo | $0.0002/1K | Architecture, file structure |
| **Builder** | qwen-plus | $0.0005/1K | Write all code files |
| **Tester** | qwen-turbo | $0.0002/1K | Run tests, report failures |
| **Fixer** | qwen-plus | $0.0005/1K | Auto-fix test failures |
| **Deployer** | qwen-turbo | $0.0002/1K | Vercel/Render deployment |

**Total cost per build:** ~$0.35-0.50 (varies by project size)

---

## 🎯 Success Metrics

Tracked per build:

```json
{
  "total_cost": 0.42,
  "total_tokens": 15420,
  "retries": 2,
  "success_rate": 0.85,
  "agents_used": ["Planner", "Builder", "Tester", "Fixer", "Deployer"]
}
```

**Good build:**
- Success rate ≥ 75%
- Retries ≤ 2
- Cost ≤ $0.50

---

## 🧪 Testing with Your Agentic Key

```bash
cd /home/noahsr/projects/ai-dev-cli
source .venv/bin/activate

# Initialize with your Bailian key
ai-dev init
# Paste: Alibaba Bailian API Key: [your-agentic-key]

# Test multi-agent build
ai-dev build "Tweet summarizer SaaS" --provider bailian --max-retries 3 --verbose

# Check results
ai-dev cost --today
```

**Expected output:**
```
🤖 AI Dev Multi-Agent System
============================================================
📋 Project: tweet-summarizer-saas
🤖 Agents: Planner → Builder → Tester → Fixer → Deployer
🔄 Max retries: 3
============================================================

🚀 Starting multi-agent workflow...

📋 PHASE 1: Planning...
✅ Plan created: 12 files

🔨 PHASE 2: Building...
✅ Built 12 files

🧪 PHASE 3: Testing (max 3 retries)...
✅ Tests passed

🚀 PHASE 4: Deploying...
✅ Vercel config found

============================================================
✅ BUILD COMPLETE in 145.2s
💰 Total cost: $0.42
🔄 Retries: 1
📊 Success rate: 100%
🤖 Agents Used: Planner, Builder, Tester, Deployer
============================================================
```

---

## 🔧 Customization

### Change Provider
```bash
# Use OpenAI instead
ai-dev build "..." --provider openai

# Use Gemini
ai-dev build "..." --provider gemini
```

### Adjust Retry Limit
```bash
# More retries for complex projects
ai-dev build "..." --max-retries 5

# Fewer retries for speed
ai-dev build "..." --max-retries 1
```

### Verbose Output
```bash
# See step-by-step log
ai-dev build "..." --verbose
```

---

## 📈 Roadmap

### v0.2 (Current)
- ✅ Multi-agent system
- ✅ Enforced refine loop
- ✅ Success tracking
- ✅ Provider-agnostic

### v0.3 (Next)
- [ ] Parallel agent execution
- [ ] Cost optimization dashboard
- [ ] Team collaboration

### v0.4 (Future)
- [ ] Observability SDK
- [ ] Custom agent roles
- [ ] Enterprise SSO

---

**Built for reliability, not just speed.** 🚀
