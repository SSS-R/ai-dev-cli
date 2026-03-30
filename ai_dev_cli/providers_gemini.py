"""
Google Gemini Provider Integration
"""

import time
import requests
from typing import Optional


class GeminiProvider:
    """Google Gemini API integration."""
    
    def __init__(self, api_key: str, default_model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def chat(self, prompt: str, model: Optional[str] = None) -> 'LLMResponse':
        """Send chat request to Google Gemini."""
        from .providers import LLMResponse
        
        model = model or self.default_model
        start = time.time()
        
        # Gemini API format
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        latency = (time.time() - start) * 1000
        
        # Extract response
        content = data['candidates'][0]['content']['parts'][0]['text']
        
        # Gemini doesn't always provide token counts
        usage_metadata = data.get('usageMetadata', {})
        prompt_tokens = usage_metadata.get('promptTokenCount', 0)
        completion_tokens = usage_metadata.get('candidatesTokenCount', 0)
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
            provider="gemini"
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate approximate cost based on model pricing."""
        # Gemini pricing per 1K tokens (approximate 2026 rates)
        pricing = {
            "gemini-2.0-flash": {"prompt": 0.000075, "completion": 0.0003},
            "gemini-2.0-flash-lite": {"prompt": 0.000075, "completion": 0.0003},
            "gemini-1.5-pro": {"prompt": 0.00125, "completion": 0.005},
            "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
        }
        
        rates = pricing.get(model, pricing["gemini-2.0-flash"])
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]
        
        return round(prompt_cost + completion_cost, 6)
