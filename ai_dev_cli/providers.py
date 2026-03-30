"""
AI Dev CLI — LLM Provider Integrations

Supports: OpenAI, Anthropic, Ollama, Google Gemini, Bailian (Qwen), DeepSeek
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# Cost tracking database
COST_DB = Path.home() / ".ai-dev" / "costs.jsonl"


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    model: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    provider: str
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CostEntry:
    """Single cost tracking entry."""
    timestamp: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    project: str
    
    def to_dict(self) -> dict:
        return asdict(self)


def load_config() -> dict:
    """Load configuration from ~/.ai-dev/config.json with .env fallback."""
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv(Path.home() / ".ai-dev" / ".env")
    load_dotenv(Path.cwd() / ".env")
    
    config_file = Path.home() / ".ai-dev" / "config.json"
    if not config_file.exists():
        # Fallback to environment variables only
        config = {
            "providers": {
                "openai": {"api_key": os.getenv("OPENAI_API_KEY", ""), "default_model": os.getenv("DEFAULT_MODEL", "gpt-4o")},
                "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY", ""), "default_model": "claude-sonnet-4-20250514"},
                "gemini": {"api_key": os.getenv("GEMINI_API_KEY", ""), "default_model": "gemini-2.0-flash"},
                "bailian": {"api_key": os.getenv("BAILIAN_API_KEY", ""), "default_model": os.getenv("DEFAULT_MODEL", "qwen-plus")},
                "deepseek": {"api_key": os.getenv("DEEPSEEK_API_KEY", ""), "default_model": "deepseek-chat"},
                "ollama": {"base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), "default_model": "llama3"}
            },
            "defaults": {"project": os.getenv("DEFAULT_PROJECT", "default")}
        }
        return config
    
    with open(config_file) as f:
        base_config = json.load(f)
    
    # Override with environment variables if set
    for provider in base_config["providers"]:
        env_key = f"{provider.upper()}_API_KEY"
        if os.getenv(env_key):
            base_config["providers"][provider]["api_key"] = os.getenv(env_key)
    
    return base_config


def log_cost(entry: CostEntry):
    """Append cost entry to JSONL database."""
    COST_DB.parent.mkdir(exist_ok=True)
    with open(COST_DB, 'a') as f:
        f.write(json.dumps(entry.to_dict()) + '\n')


def get_costs(today: bool = False, project: Optional[str] = None) -> List[Dict]:
    """Retrieve cost entries, optionally filtered."""
    if not COST_DB.exists():
        return []
    
    entries = []
    with open(COST_DB) as f:
        for line in f:
            entry = json.loads(line.strip())
            
            # Filter by date
            if today:
                entry_date = entry['timestamp'][:10]
                today_date = datetime.now().strftime('%Y-%m-%d')
                if entry_date != today_date:
                    continue
            
            # Filter by project
            if project and entry['project'] != project:
                continue
            
            entries.append(entry)
    
    return entries


class OpenAIProvider:
    """OpenAI API integration."""
    
    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://api.openai.com/v1"
    
    def chat(self, prompt: str, model: Optional[str] = None) -> LLMResponse:
        """Send chat completion request to OpenAI."""
        import requests
        
        model = model or self.default_model
        start = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        latency = (time.time() - start) * 1000
        
        usage = data['usage']
        content = data['choices'][0]['message']['content']
        
        # Calculate cost (approximate, based on public pricing)
        cost = self._calculate_cost(model, usage['prompt_tokens'], usage['completion_tokens'])
        
        return LLMResponse(
            model=model,
            content=content,
            prompt_tokens=usage['prompt_tokens'],
            completion_tokens=usage['completion_tokens'],
            total_tokens=usage['total_tokens'],
            latency_ms=latency,
            cost_usd=cost,
            provider="openai"
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate approximate cost based on model pricing."""
        # Pricing per 1K tokens (approximate 2026 rates)
        pricing = {
            "gpt-4o": {"prompt": 0.0025, "completion": 0.0075},
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        }
        
        rates = pricing.get(model, pricing["gpt-4o"])
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]
        
        return round(prompt_cost + completion_cost, 6)


class AnthropicProvider:
    """Anthropic API integration."""
    
    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://api.anthropic.com/v1"
    
    def chat(self, prompt: str, model: Optional[str] = None) -> LLMResponse:
        """Send message to Anthropic Claude."""
        import requests
        
        model = model or self.default_model
        start = time.time()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        latency = (time.time() - start) * 1000
        
        usage = data.get('usage', {})
        content = data['content'][0]['text']
        
        prompt_tokens = usage.get('input_tokens', 0)
        completion_tokens = usage.get('output_tokens', 0)
        total_tokens = prompt_tokens + completion_tokens
        
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        return LLMResponse(
            model=model,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency,
            cost_usd=cost,
            provider="anthropic"
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate approximate cost based on model pricing."""
        # Pricing per 1K tokens (approximate 2026 rates)
        pricing = {
            "claude-sonnet-4-20250514": {"prompt": 0.003, "completion": 0.015},
            "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
        }
        
        rates = pricing.get(model, pricing["claude-sonnet-4-20250514"])
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]
        
        return round(prompt_cost + completion_cost, 6)


class OllamaProvider:
    """Ollama local model integration."""
    
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3"):
        self.base_url = base_url
        self.default_model = default_model
    
    def chat(self, prompt: str, model: Optional[str] = None) -> LLMResponse:
        """Send chat request to local Ollama instance."""
        import requests
        
        model = model or self.default_model
        start = time.time()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        data = response.json()
        latency = (time.time() - start) * 1000
        
        content = data.get('response', '')
        # Ollama doesn't always provide token counts
        prompt_tokens = data.get('prompt_eval_count', 0)
        completion_tokens = data.get('eval_count', 0)
        total_tokens = prompt_tokens + completion_tokens
        
        # Ollama is free (local)
        cost = 0.0
        
        return LLMResponse(
            model=model,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency,
            cost_usd=cost,
            provider="ollama"
        )


def get_provider(name: str, config: dict) -> Any:
    """Factory function to get provider instance."""
    if name == "openai":
        return OpenAIProvider(
            api_key=config["api_key"],
            default_model=config.get("default_model", "gpt-4o")
        )
    elif name == "anthropic":
        return AnthropicProvider(
            api_key=config["api_key"],
            default_model=config.get("default_model", "claude-sonnet-4-20250514")
        )
    elif name == "ollama":
        return OllamaProvider(
            base_url=config.get("base_url", "http://localhost:11434"),
            default_model=config.get("default_model", "llama3")
        )
    elif name == "gemini":
        from .providers_gemini import GeminiProvider
        return GeminiProvider(
            api_key=config["api_key"],
            default_model=config.get("default_model", "gemini-2.0-flash")
        )
    elif name == "bailian":
        from .providers_chinese import BailianProvider
        return BailianProvider(
            api_key=config["api_key"],
            default_model=config.get("default_model", "qwen-plus")
        )
    elif name == "deepseek":
        from .providers_chinese import DeepSeekProvider
        return DeepSeekProvider(
            api_key=config["api_key"],
            default_model=config.get("default_model", "deepseek-chat")
        )
    else:
        raise ValueError(f"Unknown provider: {name}")
