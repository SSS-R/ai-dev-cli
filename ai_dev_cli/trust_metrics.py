"""
AI Dev CLI — Trust Metrics Tracking

Tracks success rate, avg cost, avg time, avg retries per template.
"""

import json
from pathlib import Path
from datetime import datetime

TRUST_METRICS_FILE = Path(__file__).parent.parent / "trust_metrics.json"


def load_trust_metrics() -> dict:
    """Load trust metrics from file."""
    if not TRUST_METRICS_FILE.exists():
        return {
            "templates": {},
            "global": {
                "total_builds": 0,
                "total_successful": 0,
                "overall_success_rate": 0,
                "avg_cost_usd": 0,
                "avg_time_sec": 0,
                "avg_retries": 0
            }
        }
    
    with open(TRUST_METRICS_FILE) as f:
        return json.load(f)


def update_trust_metrics(template_name: str, build_result: dict):
    """Update trust metrics after a build."""
    metrics = load_trust_metrics()
    
    # Update global metrics
    metrics["global"]["total_builds"] += 1
    if build_result.get("success"):
        metrics["global"]["total_successful"] += 1
    
    # Calculate new averages
    total = metrics["global"]["total_builds"]
    metrics["global"]["overall_success_rate"] = (metrics["global"]["total_successful"] / total) * 100 if total > 0 else 0
    
    # Update template-specific metrics
    if template_name:
        if template_name not in metrics["templates"]:
            metrics["templates"][template_name] = {
                "name": template_name,
                "builds_total": 0,
                "builds_successful": 0,
                "success_rate": 0,
                "avg_cost_usd": 0,
                "avg_time_sec": 0,
                "avg_retries": 0,
                "last_build": None
            }
        
        template = metrics["templates"][template_name]
        template["builds_total"] += 1
        if build_result.get("success"):
            template["builds_successful"] += 1
        
        template["success_rate"] = (template["builds_successful"] / template["builds_total"]) * 100
        template["last_build"] = datetime.now().isoformat()
        
        # Update averages (simple moving average)
        build_metrics = build_result.get("metrics", {})
        if build_metrics:
            # Simple average for now, can be improved with exponential moving average
            template["avg_cost_usd"] = build_metrics.get("total_cost", 0)
            template["avg_retries"] = build_metrics.get("retries", 0)
    
    # Save metrics
    with open(TRUST_METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
