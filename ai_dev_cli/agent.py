"""
AI Dev CLI — Autonomous Agent Loop

Agent Loop: Plan → Act → Observe → Refine → Deploy
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
        
        # Get LLM provider
        provider_config = self.config["providers"].get("openai", {})
        if provider_config:
            self.llm = get_provider("openai", provider_config)
        else:
            raise ValueError("OpenAI provider required for agent")
    
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
        
        return self.plan
    
    def execute_build(self, require_approval: bool = True) -> BuildResult:
        """
        PHASE 2-5: Execute the build (Act → Observe → Refine → Deploy).
        """
        if not self.plan:
            raise ValueError("Must call plan_build() first")
        
        if require_approval:
            # Show plan for approval
            print("\n📋 BUILD PLAN")
            print("=" * 60)
            print(f"Project: {self.plan.project_name}")
            print(f"Description: {self.plan.description}")
            print(f"Tech Stack: {', '.join(self.plan.tech_stack)}")
            print(f"Files: {len(self.plan.files)}")
            print(f"APIs: {', '.join(self.plan.apis_needed)}")
            print(f"Est. Time: {self.plan.estimated_time_min} min")
            print(f"Est. Cost: ${self.plan.estimated_cost_usd:.2f}")
            print("=" * 60)
            
            approve = input("\nProceed with build? [y/N]: ").strip().lower()
            if approve != 'y':
                self.state = AgentState.FAILED
                return BuildResult(
                    success=False,
                    project_path=str(self.output_dir),
                    files_created=0,
                    tests_passed=0,
                    tests_failed=0,
                    deployed_url=None,
                    total_cost_usd=self.total_cost,
                    total_time_sec=time.time() - (self.start_time or time.time()),
                    error="User cancelled"
                )
        
        # Create project directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # PHASE 2: Act (Write files)
        self.state = AgentState.CODING
        files_created = 0
        
        for file_info in self.plan.files:
            file_path = self.output_dir / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate file content
            content = self._generate_file_content(file_info)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            files_created += 1
            self.results.append(f"✅ Created {file_info['path']}")
        
        # PHASE 3: Observe (Run tests if available)
        self.state = AgentState.TESTING
        tests_passed = 0
        tests_failed = 0
        
        # Check for test script
        test_script = self.output_dir / "test.sh"
        if test_script.exists():
            import subprocess
            try:
                result = subprocess.run(
                    ["bash", "test.sh"],
                    cwd=self.output_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    tests_passed = 1
                    self.results.append("✅ Tests passed")
                else:
                    tests_failed = 1
                    self.errors.append(f"❌ Tests failed: {result.stderr}")
            except Exception as e:
                tests_failed = 1
                self.errors.append(f"❌ Test error: {str(e)}")
        else:
            self.results.append("ℹ️  No test script found (skipping tests)")
        
        # PHASE 4: Refine (Fix test failures)
        if tests_failed > 0:
            self.state = AgentState.REFINING
            # TODO: Implement auto-fix loop
            self.results.append("⚠️  Test failures detected (manual fix required)")
        
        # PHASE 5: Deploy (Optional)
        self.state = AgentState.DEPLOYING
        deployed_url = None
        
        # Check for Vercel deployment
        vercel_json = self.output_dir / "vercel.json"
        if vercel_json.exists():
            # TODO: Implement Vercel deployment
            self.results.append("ℹ️  Vercel deployment ready (run `vercel` to deploy)")
        
        # Create build result
        total_time = time.time() - (self.start_time or time.time())
        self.state = AgentState.COMPLETE
        
        result = BuildResult(
            success=True,
            project_path=str(self.output_dir),
            files_created=files_created,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            deployed_url=deployed_url,
            total_cost_usd=self.total_cost,
            total_time_sec=total_time,
            error=None
        )
        
        self.results.append(f"✅ Build complete in {total_time:.1f}s, ${self.total_cost:.4f}")
        
        return result
    
    def _generate_file_content(self, file_info: Dict[str, str]) -> str:
        """Generate content for a single file."""
        prompt = f"""Generate the complete content for this file:

**Project:** {self.plan.project_name}
**File Path:** {file_info['path']}
**Description:** {file_info['description']}
**Tech Stack:** {', '.join(self.plan.tech_stack)}

Write the complete, production-ready file content. No explanations, just the code.
"""
        
        response = self.llm.chat(prompt)
        self.total_cost += response.cost_usd
        
        # Clean up response (remove markdown code blocks if present)
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])  # Remove first and last line
        
        return content
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "state": self.state.value,
            "project_name": self.project_name,
            "plan_created": self.plan is not None,
            "files_created": len(self.results),
            "errors": len(self.errors),
            "total_cost_usd": self.total_cost,
            "results": self.results[-5:],  # Last 5 results
            "errors_recent": self.errors[-3:]  # Last 3 errors
        }
