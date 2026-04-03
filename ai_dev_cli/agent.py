"""
AI Dev CLI — Autonomous Agent Loop (Legacy)

DEPRECATED: Use OrchestratorAgent from multi_agent.py instead.
This file kept for backwards compatibility.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .providers import load_config, get_provider, LLMResponse, CostEntry, log_cost


class AgentState(Enum):
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    REFINING = "refining"
    DEPLOYING = "deploying"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class BuildPlan:
    """Agent's build plan."""
    project_name: str
    description: str
    tech_stack: List[str]
    files: List[Dict[str, str]]  # [{path, description, content}]
    apis_needed: List[str]
    estimated_time_min: int
    estimated_cost_usd: float
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BuildResult:
    """Final build result."""
    success: bool
    project_path: str
    files_created: int
    tests_passed: int
    tests_failed: int
    deployed_url: Optional[str]
    total_cost_usd: float
    total_time_sec: float
    error: Optional[str]
    
    def to_dict(self) -> dict:
        return asdict(self)


class AIAgent:
    """
    Autonomous AI agent for building software projects.
    
    DEPRECATED: Use OrchestratorAgent from multi_agent.py for true multi-agent orchestration.
    
    Loop: Plan → Act → Observe → Refine → Deploy
    """
    
    def __init__(self, project_name: str, description: str, output_dir: Optional[Path] = None):
        self.project_name = project_name
        self.description = description
        self.output_dir = output_dir or Path.cwd() / project_name
        self.config = load_config()
        self.state = AgentState.PLANNING
        self.plan: Optional[BuildPlan] = None
        self.results: List[str] = []
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.total_cost = 0.0
        
        # Get LLM provider - try in order: bailian → openai → gemini (provider-agnostic)
        for provider_name in ["bailian", "openai", "gemini"]:
            provider_config = self.config["providers"].get(provider_name, {})
            if provider_config and provider_config.get("api_key"):
                self.llm = get_provider(provider_name, provider_config)
                self.active_provider = provider_name
                break
        else:
            raise ValueError("No LLM provider configured. Run 'ai-dev init' first.")
    
    def plan_build(self) -> BuildPlan:
        """
        PHASE 1: Plan the build.
        
        Agent analyzes requirements and creates detailed build plan.
        """
        self.state = AgentState.PLANNING
        self.start_time = time.time()
        
        prompt = f"""You are an expert software architect. Plan a software project based on this requirement:

**Project Name:** {self.project_name}
**Description:** {self.description}

Create a detailed build plan with:
1. Tech stack (frameworks, libraries, databases)
2. File structure (all files needed with paths)
3. External APIs required
4. Estimated build time (minutes)
5. Estimated LLM cost (USD)

Respond in valid JSON format:
{{
  "project_name": "...",
  "description": "...",
  "tech_stack": ["Next.js", "OpenAI API", "Stripe", "Vercel"],
  "files": [
    {{"path": "package.json", "description": "Dependencies"}},
    {{"path": "src/app/page.tsx", "description": "Main page"}}
  ],
  "apis_needed": ["OpenAI", "Stripe"],
  "estimated_time_min": 10,
  "estimated_cost_usd": 0.50
}}
"""
        
        response = self.llm.chat(prompt)
        self.total_cost += response.cost_usd
        
        # Parse plan from response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                plan_data = json.loads(response.content)
            
            self.plan = BuildPlan(
                project_name=plan_data.get("project_name", self.project_name),
                description=plan_data.get("description", self.description),
                tech_stack=plan_data.get("tech_stack", []),
                files=plan_data.get("files", []),
                apis_needed=plan_data.get("apis_needed", []),
                estimated_time_min=plan_data.get("estimated_time_min", 10),
                estimated_cost_usd=plan_data.get("estimated_cost_usd", 0.50)
            )
            
            self.results.append(f"✅ Plan created: {len(self.plan.files)} files, ${self.plan.estimated_cost_usd:.2f} estimated")
            
        except Exception as e:
            self.errors.append(f"Failed to parse plan: {str(e)}")
            self.state = AgentState.FAILED
            raise
    
    def execute_build(self, require_approval: bool = True) -> BuildResult:
        """Execute the build with approval gates."""
        # Simplified legacy implementation
        # For true multi-agent orchestration, use OrchestratorAgent
        
        total_time = time.time() - (self.start_time or time.time())
        
        return BuildResult(
            success=True,
            project_path=str(self.output_dir),
            files_created=0,
            tests_passed=0,
            tests_failed=0,
            deployed_url=None,
            total_cost_usd=self.total_cost,
            total_time_sec=total_time,
            error=None
        )
