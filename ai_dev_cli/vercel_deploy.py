"""
Vercel Deployment Integration for AI Dev CLI

Auto-deploys built projects to Vercel after successful build.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any


class VercelDeployer:
    """Deploy projects to Vercel."""
    
    def __init__(self, project_path: Path, project_name: str):
        self.project_path = project_path
        self.project_name = project_name
        self.vercel_token: Optional[str] = None
        self.team_id: Optional[str] = None
    
    def set_auth(self, vercel_token: str, team_id: Optional[str] = None):
        """Set Vercel authentication."""
        self.vercel_token = vercel_token
        self.team_id = team_id
    
    def deploy(self, production: bool = False) -> Dict[str, Any]:
        """
        Deploy project to Vercel.
        
        Returns:
            Dict with deployment URL, status, and metadata
        """
        # Check if Vercel CLI is installed
        if not self._vercel_installed():
            return {
                "success": False,
                "error": "Vercel CLI not installed. Run: npm install -g vercel",
                "url": None
            }
        
        # Check for vercel.json
        vercel_config = self.project_path / "vercel.json"
        if not vercel_config.exists():
            # Create basic config
            self._create_vercel_config()
        
        # Run vercel deploy
        cmd = ["vercel", "--yes"]
        if production:
            cmd.append("--prod")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            if result.returncode == 0:
                # Parse deployment URL from output
                url = self._parse_deployment_url(result.stdout)
                return {
                    "success": True,
                    "url": url,
                    "output": result.stdout,
                    "production": production
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "url": None
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Deployment timed out (5 min limit)",
                "url": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": None
            }
    
    def _vercel_installed(self) -> bool:
        """Check if Vercel CLI is installed."""
        try:
            result = subprocess.run(
                ["vercel", "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _create_vercel_config(self):
        """Create basic vercel.json config."""
        config = {
            "name": self.project_name,
            "buildCommand": "npm run build" if (self.project_path / "package.json").exists() else None,
            "devCommand": "npm run dev" if (self.project_path / "package.json").exists() else None,
            "installCommand": "npm install" if (self.project_path / "package.json").exists() else None
        }
        
        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}
        
        with open(self.project_path / "vercel.json", 'w') as f:
            json.dump(config, f, indent=2)
    
    def _parse_deployment_url(self, output: str) -> Optional[str]:
        """Parse deployment URL from Vercel CLI output."""
        import re
        
        # Look for patterns like:
        # https://project-name-abc123.vercel.app
        # https://project-name.vercel.app
        patterns = [
            r'https://[a-zA-Z0-9-]+\.vercel\.app',
            r'https://[a-zA-Z0-9-]+-[a-zA-Z0-9]+\.vercel\.app'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group()
        
        return None


def deploy_to_vercel(project_path: str, project_name: str, production: bool = False) -> Dict[str, Any]:
    """
    Deploy a project to Vercel.
    
    Args:
        project_path: Path to project directory
        project_name: Project name
        production: Deploy to production (vs preview)
    
    Returns:
        Deployment result dict
    """
    deployer = VercelDeployer(Path(project_path), project_name)
    return deployer.deploy(production=production)
