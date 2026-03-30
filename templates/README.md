# AI Dev CLI Templates

Pre-built templates for common SaaS projects.

## Available Templates

### 1. Tweet Summarizer (`tweet-summarizer`)
**What:** SaaS that summarizes Twitter threads
**Stack:** Next.js, OpenAI API, Stripe, Vercel
**Price Point:** $9/mo
**Files:** 12

### 2. AI Dashboard (`ai-dashboard`)
**What:** Admin dashboard with AI insights
**Stack:** React, OpenAI API, Tailwind, Vercel
**Price Point:** $19/mo
**Files:** 15

### 3. API Wrapper (`api-wrapper`)
**What:** REST API wrapper around LLM
**Stack:** FastAPI, OpenAI, Render
**Price Point:** $29/mo
**Files:** 8

## Usage

```bash
# Build from template
ai-dev build "Tweet summarizer" --template tweet-summarizer

# List templates
ai-dev templates

# Show template details
ai-dev templates --show tweet-summarizer
```

## Creating Custom Templates

1. Create folder in `templates/your-template/`
2. Add `manifest.json` with metadata
3. Add file templates (`.txt` or `.jinja2`)
4. Test with `ai-dev build --template your-template`
