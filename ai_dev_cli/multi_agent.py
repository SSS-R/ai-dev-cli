"""
AI Dev CLI — Multi-Agent System

Roles:
- OrchestratorAgent: Routes tasks, tracks success
- PlannerAgent: Analyzes requirements, creates build plan
- BuilderAgent: Writes code files
- TesterAgent: Runs tests, reports failures
- FixerAgent: Auto-fixes test failures
- DeployerAgent: Checks deployment config (manual deployment)

Loop: Plan → Build → Test → [FAIL?] → Fix → Retest (max 3 retries) → Deploy
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field

from .providers import load_config, get_provider, LLMResponse, CostEntry, log_cost


@dataclass
class AgentRole:
    """Base class for all agent roles."""
    name: str
    description: str
    model_preference: str = "qwen-plus"  # Default to Bailian
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this agent's task. Override in subclasses."""
        raise NotImplementedError


@dataclass
class PlannerAgent(AgentRole):
    """Analyzes requirements and creates detailed build plan."""
    name: str = "Planner"
    description: str = "Creates architecture and file structure"
    model_preference: str = "qwen-turbo"  # Cheap for planning
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are an expert software architect. Create a build plan for:

**Project:** {context.get('project_name', 'Unknown')}
**Description:** {context.get('description', 'No description')}

Create a detailed plan with:
1. Tech stack (frameworks, libraries, databases)
2. File structure (all files with paths and descriptions)
3. External APIs needed
4. Estimated time (minutes) and cost (USD)

Respond in JSON:
{{
  "tech_stack": ["Next.js", "OpenAI API", "Stripe"],
  "files": [
    {{"path": "package.json", "description": "Dependencies"}},
    {{"path": "src/app/page.tsx", "description": "Main page"}}
  ],
  "apis_needed": ["OpenAI", "Stripe"],
  "estimated_time_min": 10,
  "estimated_cost_usd": 0.35
}}
"""
        # Execute with preferred model
        llm = get_provider(context.get('provider', 'bailian'), context['provider_config'])
        response = llm.chat(prompt)
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        plan_data = json.loads(json_match.group()) if json_match else {}
        
        return {
            "success": True,
            "plan": plan_data,
            "tokens_used": response.total_tokens,
            "cost_usd": response.cost_usd
        }


@dataclass
class BuilderAgent(AgentRole):
    """Writes code files based on plan."""
    name: str = "Builder"
    description: str = "Writes all code files"
    model_preference: str = "qwen-plus"  # Balanced for coding
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        plan = context.get('plan', {})
        output_dir = Path(context.get('output_dir', '.'))
        files_created = []
        errors = []
        total_cost = 0.0
        
        llm = get_provider(context.get('provider', 'bailian'), context['provider_config'])
        
        for file_info in plan.get('files', []):
            file_path = output_dir / file_info['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            prompt = f"""Write the complete content for this file:

**Project:** {context.get('project_name', 'Unknown')}
**File:** {file_info['path']}
**Description:** {file_info['description']}
**Tech Stack:** {', '.join(plan.get('tech_stack', []))}

Write production-ready code. No explanations, just the code.
"""
            try:
                response = llm.chat(prompt)
                total_cost += response.cost_usd
                
                # Clean markdown code blocks
                content = response.content.strip()
                import re
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                files_created.append(file_info['path'])
                
            except Exception as e:
                errors.append(f"{file_info['path']}: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "files_created": files_created,
            "errors": errors,
            "total_cost": total_cost
        }


@dataclass
class TesterAgent(AgentRole):
    """Runs tests and reports failures."""
    name: str = "Tester"
    description: str = "Runs test suite, reports failures"
    model_preference: str = "qwen-turbo"  # Cheap for test running
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        output_dir = Path(context.get('output_dir', '.'))
        test_script = output_dir / "test.sh"
        
        if not test_script.exists():
            return {
                "success": False,  # HARD FAIL - no test script means we can't verify
                "tests_passed": 0,
                "tests_failed": 0,
                "error": "No test script found. Create test.sh to verify the build.",
                "skipped": True
            }
        
        import subprocess
        try:
            result = subprocess.run(
                ["bash", "test.sh"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "tests_passed": 1,
                    "tests_failed": 0,
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "tests_passed": 0,
                    "tests_failed": 1,
                    "error": result.stderr[:500],
                    "output": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tests_passed": 0,
                "tests_failed": 1,
                "error": "Test timeout (60s)"
            }
        except Exception as e:
            return {
                "success": False,
                "tests_passed": 0,
                "tests_failed": 1,
                "error": str(e)
            }


@dataclass
class FixerAgent(AgentRole):
    """Auto-fixes test failures using LLM."""
    name: str = "Fixer"
    description: str = "Analyzes errors and auto-fixes code"
    model_preference: str = "qwen-plus"  # Good for debugging
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        error_output = context.get('test_error', '')
        output_dir = Path(context.get('output_dir', '.'))
        
        prompt = f"""Tests failed. Analyze and fix the code.

**Error:**
{error_output[:1000]}

**Task:**
1. Identify what's broken
2. Write the fix
3. Return ONLY the fixed file content

Respond with:
FILE: path/to/file.py
```python
# fixed code here
```
"""
        llm = get_provider(context.get('provider', 'bailian'), context['provider_config'])
        
        try:
            response = llm.chat(prompt)
            
            # Parse response
            import re
            file_match = re.search(r'FILE:\s*(\S+)', response.content)
            code_match = re.search(r'```(?:python)?\n(.*?)```', response.content, re.DOTALL)
            
            if file_match and code_match:
                file_path = output_dir / file_match.group(1)
                if file_path.exists():
                    with open(file_path, 'w') as f:
                        f.write(code_match.group(1))
                    
                    return {
                        "success": True,
                        "file_fixed": file_match.group(1),
                        "cost_usd": response.cost_usd
                    }
            
            return {
                "success": False,
                "error": "Could not parse fix from LLM response"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


@dataclass
class DeployerAgent(AgentRole):
    """Checks deployment config (manual deployment required)."""
    name: str = "Deployer"
    description: str = "Checks deployment config (manual deployment)"
    model_preference: str = "qwen-turbo"  # Cheap for deployment
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Check if deployment config exists
        output_dir = Path(context.get('output_dir', '.'))
        vercel_config = output_dir / "vercel.json"
        render_config = output_dir / "render.yaml"
        
        if vercel_config.exists():
            return {
                "success": True,
                "message": "Vercel config found. Run 'vercel' CLI to deploy manually.",
                "deployed": False,
                "platform": "vercel",
                "manual_steps": ["Run 'vercel' to deploy"]
            }
        elif render_config.exists():
            return {
                "success": True,
                "message": "Render config found. Push to Git to trigger deploy.",
                "deployed": False,
                "platform": "render",
                "manual_steps": ["Push to Git repository"]
            }
        else:
            return {
                "success": True,
                "message": "No deployment config found. Manual deployment required.",
                "deployed": False,
                "platform": None,
                "manual_steps": ["Create deployment config or deploy manually"]
            }


@dataclass
class OrchestratorAgent:
    """
    Orchestrates multi-agent workflow.
    
    Loop: Plan → Build → Test → [FAIL?] → Fix → Retest (max 3 retries) → Deploy
    
    HARD FAIL: If tests fail after max retries, build fails with specific error.
    """
    project_name: str
    description: str
    output_dir: Optional[Path] = None
    max_retries: int = 3
    provider: str = "bailian"  # Default to Bailian (agentic)
    
    def __post_init__(self):
        self.config = load_config()
        self.output_dir = self.output_dir or Path.cwd() / self.project_name
        self.results: List[str] = []
        self.errors: List[str] = []
        self.metrics = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "retries": 0,
            "success_rate": 0.0,
            "agents_used": [],
            "fixer_costs": []
        }
        
        # Get provider config - try bailian first, then fallback
        self.provider_config = self.config["providers"].get(self.provider, {})
        if not self.provider_config or not self.provider_config.get("api_key"):
            # Fallback to next provider
            for fallback in ["openai", "gemini"]:
                self.provider_config = self.config["providers"].get(fallback, {})
                if self.provider_config and self.provider_config.get("api_key"):
                    self.provider = fallback
                    self.results.append(f"⚠️  {self.provider} not configured, falling back to {fallback}")
                    break
            else:
                raise ValueError("No LLM provider configured. Run 'ai-dev init' first.")
    
    def execute(self) -> Dict[str, Any]:
        """Execute full multi-agent workflow with HARD FAIL on test failures."""
        start_time = time.time()
        
        self.results.append(f"🚀 Starting multi-agent build: {self.project_name}")
        self.results.append(f"🤖 Using provider: {self.provider}")
        
        # PHASE 1: PLAN
        self.results.append("\n📋 PHASE 1: Planning...")
        planner = PlannerAgent()
        plan_result = planner.execute({
            "project_name": self.project_name,
            "description": self.description,
            "provider": self.provider,
            "provider_config": self.provider_config
        })
        
        if not plan_result.get("success"):
            return self._fail("Planning failed", plan_result)
        
        self.metrics["total_cost"] += plan_result.get("cost_usd", 0)
        self.metrics["total_tokens"] += plan_result.get("tokens_used", 0)
        self.metrics["agents_used"].append("Planner")
        self.results.append(f"✅ Plan created: {len(plan_result.get('plan', {}).get('files', []))} files")
        
        # PHASE 2: BUILD
        self.results.append("\n🔨 PHASE 2: Building...")
        builder = BuilderAgent()
        build_result = builder.execute({
            "project_name": self.project_name,
            "plan": plan_result.get("plan", {}),
            "output_dir": str(self.output_dir),
            "provider": self.provider,
            "provider_config": self.provider_config
        })
        
        if not build_result.get("success"):
            self.results.append(f"⚠️  Build had errors: {build_result.get('errors', [])}")
        
        self.metrics["total_cost"] += build_result.get("total_cost", 0)
        self.metrics["agents_used"].append("Builder")
        self.results.append(f"✅ Built {len(build_result.get('files_created', []))} files")
        
        # PHASE 3: TEST → FIX LOOP (with HARD FAIL)
        self.results.append(f"\n🧪 PHASE 3: Testing (max {self.max_retries} retries)...")
        tester = TesterAgent()
        fixer = FixerAgent()
        
        test_result = tester.execute({
            "output_dir": str(self.output_dir)
        })
        
        # Auto-fix loop - retry until success OR hard fail
        while not test_result.get("success") and not test_result.get("skipped") and self.metrics["retries"] < self.max_retries:
            self.metrics["retries"] += 1
            self.results.append(f"🔧 Retry {self.metrics['retries']}/{self.max_retries}: Fixing...")
            
            fix_result = fixer.execute({
                "test_error": test_result.get("error", ""),
                "output_dir": str(self.output_dir),
                "provider": self.provider,
                "provider_config": self.provider_config
            })
            
            if fix_result.get("success"):
                self.results.append(f"✅ Fixed: {fix_result.get('file_fixed', 'unknown')}")
                self.metrics["total_cost"] += fix_result.get("cost_usd", 0)
                self.metrics["fixer_costs"].append({"cost_usd": fix_result.get("cost_usd", 0)})
                self.metrics["agents_used"].append("Fixer")
                
                # Retest
                test_result = tester.execute({"output_dir": str(self.output_dir)})
            else:
                self.results.append(f"❌ Fix failed: {fix_result.get('error', 'unknown')}")
                break
        
        self.metrics["agents_used"].append("Tester")
        
        # HARD FAIL if tests failed after max retries
        if test_result.get("skipped"):
            self.results.append("⚠️  No test script found (skipped)")
            # Still count as failure - we can't verify without tests
        elif test_result.get("success"):
            self.results.append("✅ Tests passed")
        else:
            # HARD FAIL with specific error
            self.results.append(f"❌ Tests FAILED after {self.metrics['retries']} retries")
            self.errors.append(f"TesterAgent: {test_result.get('error', 'Unknown test failure')}")
        
        # PHASE 4: DEPLOY (manual)
        self.results.append("\n🚀 PHASE 4: Deploying...")
        deployer = DeployerAgent()
        deploy_result = deployer.execute({"output_dir": str(self.output_dir)})
        
        self.metrics["agents_used"].append("Deployer")
        self.results.append(f"   {deploy_result.get('message', 'Deployment check complete')}")
        
        # Calculate success rate
        total_steps = 4  # Plan, Build, Test, Deploy
        successful_steps = sum([
            1 if plan_result.get("success") else 0,
            1 if build_result.get("success") else 0,
            1 if test_result.get("success") else 0,  # Must pass tests
            1 if deploy_result.get("success") else 0
        ])
        self.metrics["success_rate"] = successful_steps / total_steps
        
        # HARD FAIL if tests failed (no skip allowed)
        overall_success = (
            plan_result.get("success", False) and
            build_result.get("success", False) and
            test_result.get("success", False)  # Must pass tests, no skip
        )
        
        # Final summary
        total_time = time.time() - start_time
        self.results.append(f"\n{'='*60}")
        if overall_success:
            self.results.append(f"✅ BUILD COMPLETE in {total_time:.1f}s")
        else:
            self.results.append(f"❌ BUILD FAILED in {total_time:.1f}s")
        self.results.append(f"💰 Total cost: ${self.metrics['total_cost']:.4f}")
        self.results.append(f"🔄 Retries: {self.metrics['retries']}")
        self.results.append(f"📊 Success rate: {self.metrics['success_rate']*100:.0f}%")
        self.results.append(f"{'='*60}")
        
        # Return structured results with clear role separation
        return {
            "success": overall_success,
            "project_path": str(self.output_dir),
            "metrics": self.metrics,
            "results": self.results,
            "errors": self.errors,
            "deployment": deploy_result,
            # Clear role separation - each agent reports independently
            "agent_reports": {
                "PlannerAgent": {
                    "success": plan_result.get("success", False),
                    "files_planned": len(plan_result.get("plan", {}).get("files", [])),
                    "cost_usd": plan_result.get("cost_usd", 0),
                    "tokens_used": plan_result.get("tokens_used", 0)
                },
                "BuilderAgent": {
                    "success": build_result.get("success", False),
                    "files_created": build_result.get("files_created", []),
                    "errors": build_result.get("errors", []),
                    "cost_usd": build_result.get("total_cost", 0)
                },
                "TesterAgent": {
                    "success": test_result.get("success", False),
                    "tests_passed": test_result.get("tests_passed", 0),
                    "tests_failed": test_result.get("tests_failed", 0),
                    "error": test_result.get("error") if not test_result.get("success") else None,
                    "skipped": test_result.get("skipped", False)
                },
                "FixerAgent": {
                    "fixes_applied": self.metrics.get("agents_used", []).count("Fixer"),
                    "cost_usd": sum(m.get("cost_usd", 0) for m in self.metrics.get("fixer_costs", []))
                },
                "DeployerAgent": {
                    "config_found": deploy_result.get("platform") is not None,
                    "platform": deploy_result.get("platform"),
                    "manual_steps_required": True,
                    "manual_steps": deploy_result.get("manual_steps", [])
                }
            }
        }
    
    def _fail(self, reason: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failure."""
        self.errors.append(reason)
        return {
            "success": False,
            "error": reason,
            "partial_result": result,
            "metrics": self.metrics
        }
