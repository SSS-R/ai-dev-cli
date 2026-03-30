#!/usr/bin/env python3
"""
AI Dev CLI — Main Entry Point

Commands:
  init      Initialize configuration
  cost      Track LLM spending
  prompt    Test prompts (single or A/B)
  batch     Run batch operations from CSV
"""

import sys
import json
import csv
from pathlib import Path
import click
from datetime import datetime

from . import __version__
from .providers import (
    load_config, get_costs, log_cost, CostEntry,
    get_provider, OpenAIProvider, AnthropicProvider, OllamaProvider
)
from .agent import AIAgent

# Config directory
CONFIG_DIR = Path.home() / ".ai-dev"
CONFIG_FILE = CONFIG_DIR / "config.json"


@click.group()
@click.version_option(version=__version__)
def cli():
    """AI Dev CLI — Workflow-First CLI for AI Developers.
    
    Track costs, test prompts, run batches — all from one CLI.
    Local-first, zero-config.
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
    click.echo("\nNext steps:")
    click.echo("  ai-dev cost       — View your spending")
    click.echo("  ai-dev prompt     — Test a prompt")
    click.echo("  ai-dev --help     — See all commands")


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
            # Default to OpenAI for short model names
            if model_name.startswith('gpt') or model_name.startswith('o'):
                provider_name = 'openai'
            elif model_name.startswith('claude'):
                provider_name = 'anthropic'
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
@click.option('--no-approval', is_flag=True, help='Skip approval prompt (not recommended)')
@click.option('--verbose', is_flag=True, help='Show detailed progress')
def build(description, name, template, output_dir, no_approval, verbose):
    """Build a complete software project autonomously.
    
    Agent will: Plan → Code → Test → Deploy
    
    Example:
      ai-dev build "Tweet summarizer SaaS with Stripe"
      ai-dev build "AI dashboard" --name my-dashboard
    """
    import random
    from pathlib import Path
    
    click.echo("🤖 AI Dev Agent — Autonomous Build")
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
    click.echo("=" * 60)
    
    try:
        # Create agent
        agent = AIAgent(
            project_name=name,
            description=description,
            output_dir=output_path
        )
        
        # PHASE 1: Plan
        click.echo("\n⏳ PHASE 1: Planning...")
        plan = agent.plan_build()
        
        if verbose:
            click.echo(f"\n📊 Plan Summary:")
            click.echo(f"   Files: {len(plan.files)}")
            click.echo(f"   Tech Stack: {', '.join(plan.tech_stack)}")
            click.echo(f"   APIs: {', '.join(plan.apis_needed)}")
            click.echo(f"   Est. Time: {plan.estimated_time_min} min")
            click.echo(f"   Est. Cost: ${plan.estimated_cost_usd:.2f}")
        
        # PHASE 2-5: Execute (with approval)
        click.echo("\n⏳ PHASE 2-5: Building...")
        result = agent.execute_build(require_approval=not no_approval)
        
        # Display results
        click.echo("\n" + "=" * 60)
        if result.success:
            click.echo("✅ BUILD COMPLETE")
            click.echo("=" * 60)
            click.echo(f"📁 Project Path: {result.project_path}")
            click.echo(f"📄 Files Created: {result.files_created}")
            click.echo(f"✅ Tests Passed: {result.tests_passed}")
            click.echo(f"❌ Tests Failed: {result.tests_failed}")
            if result.deployed_url:
                click.echo(f"🌐 Deployed: {result.deployed_url}")
            click.echo(f"⏱️  Total Time: {result.total_time_sec:.1f}s")
            click.echo(f"💰 Total Cost: ${result.total_cost_usd:.4f}")
        else:
            click.echo("❌ BUILD FAILED")
            click.echo("=" * 60)
            click.echo(f"Error: {result.error}")
            click.echo(f"💰 Cost (so far): ${result.total_cost_usd:.4f}")
        
        # Log final cost
        if result.success:
            cost_entry = CostEntry(
                timestamp=datetime.now().isoformat(),
                provider="openai",
                model="gpt-4o",
                prompt_tokens=0,  # Agent tracks internally
                completion_tokens=0,
                total_tokens=0,
                cost_usd=result.total_cost_usd,
                project=name
            )
            # Don't log - agent already tracked
        
    except Exception as e:
        click.echo(f"\n❌ Build failed: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--show', default=None, help='Show details for a specific template')
def templates(show):
    """List available build templates."""
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
