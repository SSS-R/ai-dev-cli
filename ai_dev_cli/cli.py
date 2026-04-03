#!/usr/bin/env python3
"""
AI Dev CLI — Command Line Interface

Multi-Agent SaaS Builder for Indie Hackers
"""

import sys
import json
import csv
from datetime import datetime
from pathlib import Path
import click

from . import __version__
from .providers import (
    load_config, get_costs, log_cost, CostEntry,
    get_provider, OpenAIProvider, AnthropicProvider, OllamaProvider
)
from .agent import AIAgent  # Legacy
from .multi_agent import OrchestratorAgent  # Multi-agent system
from .trust_metrics import load_trust_metrics, update_trust_metrics

# Config directory
CONFIG_DIR = Path.home() / ".ai-dev"
CONFIG_FILE = CONFIG_DIR / "config.json"


@click.group()
@click.version_option(version=__version__)
def cli():
    """AI Dev CLI — Multi-Agent SaaS Builder.
    
    5 AI agents (Planner, Builder, Tester, Fixer, Deployer) work together
    to build + deploy your app. For indie hackers who ship.
    """
    pass


@cli.command()
def init():
    """Initialize configuration and store API keys securely."""
    click.echo("🤖 AI Dev CLI — Initialization")
    click.echo("=" * 40)
    
    # Create config directory
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # Load existing config or create new
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        click.echo(f"✓ Found existing config at {CONFIG_FILE}")
    else:
        config = {
            "providers": {
                "openai": {"api_key": "", "default_model": "gpt-4o"},
                "anthropic": {"api_key": "", "default_model": "claude-sonnet-4-20250514"},
                "gemini": {"api_key": "", "default_model": "gemini-2.0-flash"},
                "bailian": {"api_key": "", "default_model": "qwen-plus"},
                "deepseek": {"api_key": "", "default_model": "deepseek-chat"},
                "ollama": {"base_url": "http://localhost:11434", "default_model": "llama3"}
            },
            "defaults": {
                "project": "default",
                "output_format": "table"
            }
        }
        click.echo("✓ Creating new config")
    
    # Prompt for API keys
    click.echo("\n📝 Enter your API keys (press Enter to skip):")
    
    openai_key = click.prompt("OpenAI API Key", default=config["providers"]["openai"]["api_key"], hide_input=True)
    if openai_key:
        config["providers"]["openai"]["api_key"] = openai_key
        click.echo("✓ OpenAI key saved")
    
    anthropic_key = click.prompt("Anthropic API Key", default=config["providers"]["anthropic"]["api_key"], hide_input=True)
    if anthropic_key:
        config["providers"]["anthropic"]["api_key"] = anthropic_key
        click.echo("✓ Anthropic key saved")
    
    gemini_key = click.prompt("Google Gemini API Key", default=config["providers"].get("gemini", {}).get("api_key", ""), hide_input=True)
    if gemini_key:
        if "gemini" not in config["providers"]:
            config["providers"]["gemini"] = {"api_key": "", "default_model": "gemini-2.0-flash"}
        config["providers"]["gemini"]["api_key"] = gemini_key
        click.echo("✓ Gemini key saved")
    
    bailian_key = click.prompt("Alibaba Bailian (Qwen) API Key", default=config["providers"].get("bailian", {}).get("api_key", ""), hide_input=True)
    if bailian_key:
        if "bailian" not in config["providers"]:
            config["providers"]["bailian"] = {"api_key": "", "default_model": "qwen-plus"}
        config["providers"]["bailian"]["api_key"] = bailian_key
        click.echo("✓ Bailian (Qwen) key saved")
    
    deepseek_key = click.prompt("DeepSeek API Key", default=config["providers"].get("deepseek", {}).get("api_key", ""), hide_input=True)
    if deepseek_key:
        if "deepseek" not in config["providers"]:
            config["providers"]["deepseek"] = {"api_key": "", "default_model": "deepseek-chat"}
        config["providers"]["deepseek"]["api_key"] = deepseek_key
        click.echo("✓ DeepSeek key saved")
    
    # Save config
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"\n✅ Configuration saved to {CONFIG_FILE}")
    click.echo("\n⚠️  WARNING: Config is plain text. Don't share this file or commit to git.")
    click.echo("\nNext steps:")
    click.echo("  ai-dev build \"Your SaaS idea\"  — Build with multi-agent system")
    click.echo("  ai-dev cost                      — View spending")
    click.echo("  ai-dev prompt \"...\"              — Test a prompt")


@cli.command()
@click.option('--today', is_flag=True, help='Show only today\'s spending')
@click.option('--project', default=None, help='Filter by project name')
def cost(today, project):
    """View your LLM spending across providers."""
    click.echo("💰 Cost Tracking")
    click.echo("=" * 40)
    
    # Check if config exists
    if not CONFIG_FILE.exists():
        click.echo("❌ Not initialized. Run 'ai-dev init' first.")
        sys.exit(1)
    
    # Get costs from database
    entries = get_costs(today=today, project=project)
    
    if not entries:
        click.echo("\n📊 No API calls recorded yet.")
        click.echo("   Run 'ai-dev prompt' to start tracking.")
        return
    
    # Calculate totals
    total_cost = sum(e['cost_usd'] for e in entries)
    total_tokens = sum(e['total_tokens'] for e in entries)
    
    # Group by provider
    by_provider = {}
    for entry in entries:
        provider = entry['provider']
        if provider not in by_provider:
            by_provider[provider] = {'cost': 0.0, 'tokens': 0, 'calls': 0}
        by_provider[provider]['cost'] += entry['cost_usd']
        by_provider[provider]['tokens'] += entry['total_tokens']
        by_provider[provider]['calls'] += 1
    
    # Display table
    click.echo("\n📊 Spending Summary")
    if today:
        click.echo("   (Today only)")
    if project:
        click.echo(f"   (Project: {project})")
    
    click.echo("┌─────────────┬──────────────┬─────────┬──────────┐")
    click.echo("│ Provider    │ Calls        │ Tokens  │ Cost     │")
    click.echo("├─────────────┼──────────────┼─────────┼──────────┤")
    
    for provider, stats in sorted(by_provider.items()):
        click.echo(f"│ {provider.capitalize():<11} │ {stats['calls']:<12} │ {stats['tokens']:<7} │ ${stats['cost']:<8.4f} │")
    
    click.echo("├─────────────┴──────────────┴─────────┴──────────┤")
    click.echo(f"│ Total                              │ ${total_cost:<8.4f} │")
    click.echo("└─────────────────────────────────────────────────┘")


@cli.command()
@click.argument('prompt_text')
@click.option('--model', default='gpt-4o', help='Model to use')
@click.option('--compare', multiple=True, help='Compare with additional models')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Show token counts and timing')
@click.option('--project', default='default', help='Project name for cost tracking')
def prompt(prompt_text, model, compare, output_json, verbose, project):
    """Test prompts with single or multiple models."""
    click.echo("🧪 Prompt Testing")
    click.echo("=" * 40)
    
    # Check if config exists
    if not CONFIG_FILE.exists():
        click.echo("❌ Not initialized. Run 'ai-dev init' first.")
        sys.exit(1)
    
    # Load config
    config = load_config()
    
    # Parse model name to get provider
    def get_provider_for_model(model_name: str):
        if '/' in model_name:
            provider_name = model_name.split('/')[0]
            model = model_name
        else:
            # Default to provider based on model name
            if model_name.startswith('gpt') or model_name.startswith('o'):
                provider_name = 'openai'
            elif model_name.startswith('claude'):
                provider_name = 'anthropic'
            elif model_name.startswith('gemini'):
                provider_name = 'gemini'
            elif model_name.startswith('qwen'):
                provider_name = 'bailian'
            elif model_name.startswith('deepseek'):
                provider_name = 'deepseek'
            elif model_name.startswith('llama') or model_name.startswith('mistral'):
                provider_name = 'ollama'
            else:
                provider_name = 'openai'
            model = model_name
        return provider_name, model
    
    # Get all models to test
    all_models = [model] + list(compare)
    results = []
    
    for model_name in all_models:
        provider_name, model = get_provider_for_model(model_name)
        
        if provider_name not in config["providers"]:
            click.echo(f"⚠️  Skipping {model_name}: Provider not configured")
            continue
        
        provider_config = config["providers"][provider_name]
        
        try:
            # Get provider instance
            provider = get_provider(provider_name, provider_config)
            
            # Make API call
            click.echo(f"\n⏳ Calling {model_name}...")
            response = provider.chat(prompt_text, model=model)
            
            # Log cost
            cost_entry = CostEntry(
                timestamp=datetime.now().isoformat(),
                provider=provider_name,
                model=model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.total_tokens,
                cost_usd=response.cost_usd,
                project=project
            )
            log_cost(cost_entry)
            
            results.append({
                'model': model_name,
                'response': response,
                'provider': provider_name
            })
            
        except Exception as e:
            click.echo(f"❌ Error with {model_name}: {str(e)}")
            continue
    
    if not results:
        click.echo("\n❌ No successful responses.")
        sys.exit(1)
    
    # Display results
    if output_json:
        output = {
            'prompt': prompt_text,
            'results': [
                {
                    'model': r['model'],
                    'content': r['response'].content,
                    'tokens': r['response'].total_tokens,
                    'cost': r['response'].cost_usd,
                    'latency_ms': r['response'].latency_ms
                }
                for r in results
            ]
        }
        click.echo(json.dumps(output, indent=2))
    else:
        # Table format
        click.echo(f"\n📝 Prompt: {prompt_text}")
        
        if len(results) == 1:
            # Single result
            r = results[0]
            click.echo(f"\n🤖 {r['model']} ({r['provider']})")
            click.echo("-" * 40)
            click.echo(r['response'].content)
            
            if verbose:
                click.echo(f"\n📊 Stats:")
                click.echo(f"  Tokens: {r['response'].total_tokens} (prompt: {r['response'].prompt_tokens}, completion: {r['response'].completion_tokens})")
                click.echo(f"  Time: {r['response'].latency_ms/1000:.2f}s")
                click.echo(f"  Cost: ${r['response'].cost_usd:.6f}")
        else:
            # Comparison mode
            click.echo("\n🔀 Model Comparison")
            click.echo("=" * 60)
            
            for i, r in enumerate(results, 1):
                click.echo(f"\n{i}. {r['model']} ({r['provider']})")
                click.echo("-" * 40)
                click.echo(r['response'].content[:500] + ("..." if len(r['response'].content) > 500 else ""))
                
                if verbose:
                    click.echo(f"   Tokens: {r['response'].total_tokens} | Time: {r['response'].latency_ms/1000:.2f}s | Cost: ${r['response'].cost_usd:.6f}")


@cli.command()
@click.argument('description')
@click.option('--name', default=None, help='Project name (auto-generated if not provided)')
@click.option('--template', default=None, help='Use a pre-built template')
@click.option('--output-dir', default=None, help='Output directory (default: current directory)')
@click.option('--provider', default='bailian', help='LLM provider (bailian, openai, gemini)')
@click.option('--max-retries', default=3, help='Max auto-fix retries')
@click.option('--verbose', is_flag=True, help='Show detailed progress')
def build(description, name, template, output_dir, provider, max_retries, verbose):
    """Build a complete SaaS app with multi-agent system.
    
    Uses 5 AI agents: Planner → Builder → Tester → Fixer → Deployer
    """
    import random
    from pathlib import Path
    
    click.echo("🤖 AI Dev Multi-Agent System")
    click.echo("=" * 60)
    
    # Generate project name if not provided
    if not name:
        words = description.lower().split()[:3]
        name = "-".join(w.strip(".,!?") for w in words)
        name = name.replace(" ", "-")[:50]
    
    # Set output directory
    output_path = Path(output_dir) if output_dir else Path.cwd() / name
    
    # Load template if specified
    if template:
        click.echo(f"📦 Using template: {template}")
        # TODO: Load template manifest and merge with description
    
    click.echo(f"\n📋 Project: {name}")
    click.echo(f"📝 Description: {description}")
    click.echo(f"📁 Output: {output_path}")
    click.echo(f"🤖 Agents: Planner → Builder → Tester → Fixer → Deployer")
    click.echo(f"🔄 Max retries: {max_retries}")
    click.echo("=" * 60)
    
    try:
        # Show trust metrics before build
        click.echo("\n📊 Template Trust Metrics:")
        trust_metrics = load_trust_metrics()
        if template and template in trust_metrics.get("templates", {}):
            metrics = trust_metrics["templates"][template]
            if metrics["builds_total"] > 0:
                click.echo(f"   Template: {metrics['name']}")
                click.echo(f"   Success Rate: {metrics['success_rate']:.0f}% ({metrics['builds_successful']}/{metrics['builds_total']} builds)")
                click.echo(f"   Avg Cost: ${metrics['avg_cost_usd']:.2f}")
                click.echo(f"   Avg Time: {metrics['avg_time_sec']:.0f}s")
                click.echo(f"   Avg Retries: {metrics['avg_retries']:.1f}")
            else:
                click.echo("   No builds yet for this template")
        else:
            click.echo("   Custom build (no historical data)")
        click.echo("")
        
        # Use multi-agent system (default)
        orchestrator = OrchestratorAgent(
            project_name=name,
            description=description,
            output_dir=output_path,
            max_retries=max_retries,
            provider=provider
        )
        
        click.echo("\n🚀 Starting multi-agent workflow...")
        result = orchestrator.execute()
        
        # Update trust metrics after build
        update_trust_metrics(template, result)
        
        # Display results from multi-agent system
        click.echo("\n" + "=" * 60)
        
        # Show step-by-step results from orchestrator
        for line in result.get("results", [])[-15:]:  # Last 15 lines
            click.echo(line)
        
        metrics = result.get("metrics", {})
        click.echo(f"\n📊 Metrics:")
        click.echo(f"   Total Cost: ${metrics.get('total_cost', 0):.4f}")
        click.echo(f"   Retries: {metrics.get('retries', 0)}")
        click.echo(f"   Success Rate: {metrics.get('success_rate', 0)*100:.0f}%")
        click.echo(f"   Agents Used: {', '.join(metrics.get('agents_used', []))}")
        
        # Show agent reports (clear role separation)
        if result.get("agent_reports"):
            click.echo(f"\n📋 Agent Reports:")
            for agent_name, report in result["agent_reports"].items():
                status = "✅" if report.get("success") else "❌"
                click.echo(f"   {status} {agent_name}")
        
        if not result.get("success"):
            click.echo(f"\n❌ Build failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"\n❌ Build failed: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--show', default=None, help='Show details for a specific template')
def templates(show):
    """List available SaaS templates."""
    import os
    
    templates_dir = Path(__file__).parent.parent / "templates"
    
    if show:
        # Show specific template details
        manifest_file = templates_dir / show / "manifest.json"
        if not manifest_file.exists():
            click.echo(f"❌ Template '{show}' not found")
            sys.exit(1)
        
        with open(manifest_file) as f:
            manifest = json.load(f)
        
        click.echo(f"\n📦 Template: {manifest['name']}")
        click.echo("=" * 60)
        click.echo(f"📝 Description: {manifest['description']}")
        click.echo(f"🛠️  Stack: {', '.join(manifest['stack'])}")
        click.echo(f"💰 Price Point: {manifest['price_point']}")
        click.echo(f"📄 Files: {len(manifest['files'])}")
        click.echo(f"⏱️  Est. Time: {manifest['estimated_time_min']} min")
        click.echo(f"💵 Est. Cost: ${manifest['estimated_cost_usd']:.2f}")
        click.echo("\n📋 Files:")
        for file_info in manifest['files']:
            click.echo(f"   - {file_info['path']} ({file_info['description']})")
    else:
        # List all templates
        click.echo("📦 AI Dev CLI Templates")
        click.echo("=" * 60)
        
        if not templates_dir.exists():
            click.echo("ℹ️  No templates found")
            return
        
        for template_dir in templates_dir.iterdir():
            if template_dir.is_dir() and template_dir.name != "__pycache__":
                manifest_file = template_dir / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    click.echo(f"\n📦 {manifest['name']}")
                    click.echo(f"   {manifest['description']}")
                    click.echo(f"   Stack: {', '.join(manifest['stack'])}")
                    click.echo(f"   Files: {len(manifest['files'])} | Est: ${manifest['estimated_cost_usd']:.2f}")
        
        click.echo("\n💡 Usage:")
        click.echo("   ai-dev build \"Your idea\" --template <template-name>")
        click.echo("   ai-dev templates --show <template-name>")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', default='results.csv', help='Output file path')
@click.option('--workers', default=1, help='Number of parallel workers')
@click.option('--project', default='default', help='Project name for cost tracking')
def batch(input_file, output, workers, project):
    """Run batch operations from CSV."""
    click.echo("📦 Batch Processing")
    click.echo("=" * 40)
    
    # Check if input file exists
    if not Path(input_file).exists():
        click.echo(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    # Check if config exists
    if not CONFIG_FILE.exists():
        click.echo("❌ Not initialized. Run 'ai-dev init' first.")
        sys.exit(1)
    
    # Load config
    config = load_config()
    
    click.echo(f"📁 Input: {input_file}")
    click.echo(f"💾 Output: {output}")
    click.echo(f"👷 Workers: {workers}")
    
    # Read input CSV
    prompts = []
    with open(input_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row)
    
    click.echo(f"📝 Found {len(prompts)} prompts to process")
    
    # Process prompts
    results = []
    total_cost = 0.0
    total_tokens = 0
    
    for i, row in enumerate(prompts, 1):
        prompt_text = row.get('prompt', '')
        model = row.get('model', 'gpt-4o')
        
        click.echo(f"\n[{i}/{len(prompts)}] Processing: {prompt_text[:50]}...")
        
        try:
            # Get provider
            if '/' in model:
                provider_name = model.split('/')[0]
            else:
                provider_name = 'openai'
            
            provider_config = config["providers"].get(provider_name, {})
            if not provider_config:
                click.echo(f"  ⚠️  Skipping: Provider {provider_name} not configured")
                continue
            
            provider = get_provider(provider_name, provider_config)
            response = provider.chat(prompt_text, model=model)
            
            # Log cost
            cost_entry = CostEntry(
                timestamp=datetime.now().isoformat(),
                provider=provider_name,
                model=model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.total_tokens,
                cost_usd=response.cost_usd,
                project=project
            )
            log_cost(cost_entry)
            
            # Store result
            result_row = {**row, 'output': response.content, 'tokens': response.total_tokens, 'cost': response.cost_usd, 'status': 'success'}
            results.append(result_row)
            
            total_cost += response.cost_usd
            total_tokens += response.total_tokens
            
            click.echo(f"  ✅ Success (${response.cost_usd:.6f}, {response.total_tokens} tokens)")
            
        except Exception as e:
            result_row = {**row, 'output': '', 'tokens': 0, 'cost': 0, 'status': f'error: {str(e)}'}
            results.append(result_row)
            click.echo(f"  ❌ Error: {str(e)}")
    
    # Write output CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        click.echo(f"\n✅ Batch complete!")
        click.echo(f"   Results saved to: {output}")
        click.echo(f"   Total cost: ${total_cost:.6f}")
        click.echo(f"   Total tokens: {total_tokens}")
        click.echo(f"   Successful: {sum(1 for r in results if r['status'] == 'success')}")
        click.echo(f"   Failed: {sum(1 for r in results if r['status'] != 'success')}")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
