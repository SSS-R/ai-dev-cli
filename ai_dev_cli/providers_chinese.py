"""
Chinese Model Provider Integrations

Supports: Bailian (Qwen), DeepSeek, MiniMax
"""

import time
import requests
from typing import Optional


class BailianProvider:
    """Alibaba Cloud Bailian (Qwen) API integration."""
    
    def __init__(self, api_key: str, default_model: str = "qwen-plus"):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
    
    def chat(self, prompt: str, model: Optional[str] = None) -> 'LLMResponse':
        """Send chat request to Bailian Qwen."""
        from .providers import LLMResponse
        
        model = model or self.default_model
        start = time.time()
        
        url = f"{self.base_url}/services/aigc/text-generation/generation"
        
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        latency = (time.time() - start) * 1000
        
        # Extract response
        output = data.get('output', {})
        content = output.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Extract usage
        usage = data.get('usage', {})
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
            provider="bailian"
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate approximate cost based on model pricing."""
        # Bailian Qwen pricing per 1K tokens (approximate 2026 rates)
        pricing = {
            "qwen-plus": {"prompt": 0.0005, "completion": 0.0015},
            "qwen-max": {"prompt": 0.005, "completion": 0.015},
            "qwen-turbo": {"prompt": 0.0002, "completion": 0.0006},
            "qwen2.5-72b": {"prompt": 0.0005, "completion": 0.0015},
        }
        
        rates = pricing.get(model, pricing["qwen-plus"])
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]
        
        return round(prompt_cost + completion_cost, 6)


class DeepSeekProvider:
    """DeepSeek API integration."""
    
    def __init__(self, api_key: str, default_model: str = "deepseek-chat"):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://api.deepseek.com/v1"
    
    def chat(self, prompt: str, model: Optional[str] = None) -> 'LLMResponse':
        """Send chat request to DeepSeek."""
        from .providers import LLMResponse
        
        model = model or self.default_model
        start = time.time()
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        latency = (time.time() - start) * 1000
        
        # Extract response
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {})
        
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
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
            provider="deepseek"
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate approximate cost based on model pricing."""
        # DeepSeek pricing per 1K tokens (approximate 2026 rates)
        pricing = {
            "deepseek-chat": {"prompt": 0.00027, "completion": 0.0011},
            "deepseek-coder": {"prompt": 0.00027, "completion": 0.0011},
            "deepseek-v2": {"prompt": 0.00014, "completion": 0.00028},
        }
        
        rates = pricing.get(model, pricing["deepseek-chat"])
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]
        
        return round(prompt_cost + completion_cost, 6)
