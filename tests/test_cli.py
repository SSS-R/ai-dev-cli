"""
Tests for AI Dev CLI

Run with: pytest tests/ -v
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test fixtures
@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config file."""
    config_dir = tmp_path / ".ai-dev"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    
    config = {
        "providers": {
            "openai": {"api_key": "sk-test123", "default_model": "gpt-4o"},
            "anthropic": {"api_key": "sk-ant-test", "default_model": "claude-sonnet-4"},
            "ollama": {"base_url": "http://localhost:11434", "default_model": "llama3"}
        },
        "defaults": {"project": "test"}
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f)
    
    # Patch home directory
    with patch('ai_dev_cli.providers.Path.home', return_value=tmp_path):
        yield config


class TestProviders:
    """Test provider integrations."""
    
    def test_openai_provider_init(self):
        """Test OpenAI provider initialization."""
        from ai_dev_cli.providers import OpenAIProvider
        
        provider = OpenAIProvider(api_key="sk-test", default_model="gpt-4o")
        assert provider.api_key == "sk-test"
        assert provider.default_model == "gpt-4o"
    
    def test_anthropic_provider_init(self):
        """Test Anthropic provider initialization."""
        from ai_dev_cli.providers import AnthropicProvider
        
        provider = AnthropicProvider(api_key="sk-ant-test", default_model="claude-sonnet-4")
        assert provider.api_key == "sk-ant-test"
        assert provider.default_model == "claude-sonnet-4"
    
    def test_ollama_provider_init(self):
        """Test Ollama provider initialization."""
        from ai_dev_cli.providers import OllamaProvider
        
        provider = OllamaProvider(base_url="http://localhost:11434", default_model="llama3")
        assert provider.base_url == "http://localhost:11434"
        assert provider.default_model == "llama3"
    
    @patch('requests.post')
    def test_openai_chat(self, mock_post):
        """Test OpenAI chat completion."""
        from ai_dev_cli.providers import OpenAIProvider
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Hello!'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}
        }
        mock_post.return_value = mock_response
        
        provider = OpenAIProvider(api_key="sk-test")
        response = provider.chat("Test prompt")
        
        assert response.content == "Hello!"
        assert response.total_tokens == 15
        assert response.provider == "openai"
    
    def test_cost_calculation_openai(self):
        """Test OpenAI cost calculation."""
        from ai_dev_cli.providers import OpenAIProvider
        
        provider = OpenAIProvider(api_key="sk-test")
        cost = provider._calculate_cost("gpt-4o", 1000, 500)
        
        # gpt-4o: $0.0025/1K prompt, $0.0075/1K completion
        expected = (1000/1000) * 0.0025 + (500/1000) * 0.0075
        assert abs(cost - expected) < 0.0001


class TestCostTracking:
    """Test cost tracking functionality."""
    
    def test_log_cost(self, tmp_path):
        """Test logging cost entries."""
        from ai_dev_cli.providers import CostEntry, log_cost, COST_DB
        
        # Patch database path
        with patch('ai_dev_cli.providers.COST_DB', tmp_path / "costs.jsonl"):
            entry = CostEntry(
                timestamp="2026-03-30T12:00:00",
                provider="openai",
                model="gpt-4o",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=0.001,
                project="test"
            )
            log_cost(entry)
            
            # Verify file was created
            assert (tmp_path / "costs.jsonl").exists()
    
    def test_get_costs(self, tmp_path):
        """Test retrieving cost entries."""
        from ai_dev_cli.providers import CostEntry, log_cost, get_costs, COST_DB
        
        # Patch database path
        with patch('ai_dev_cli.providers.COST_DB', tmp_path / "costs.jsonl"):
            # Add test entries
            entry1 = CostEntry(
                timestamp="2026-03-30T12:00:00",
                provider="openai",
                model="gpt-4o",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=0.001,
                project="test"
            )
            log_cost(entry1)
            
            # Retrieve
            costs = get_costs()
            assert len(costs) == 1
            assert costs[0]['provider'] == "openai"


class TestCLI:
    """Test CLI commands."""
    
    def test_cli_version(self):
        """Test CLI version command."""
        from click.testing import CliRunner
        from ai_dev_cli.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output
    
    def test_init_command(self, tmp_path):
        """Test init command."""
        from click.testing import CliRunner
        from ai_dev_cli.cli import cli, CONFIG_FILE
        
        # Patch config file path
        with patch('ai_dev_cli.cli.CONFIG_FILE', tmp_path / ".ai-dev" / "config.json"):
            runner = CliRunner()
            result = runner.invoke(cli, ['init'], input='sk-test123\nsk-ant-test\n')
            
            assert result.exit_code == 0
            assert (tmp_path / ".ai-dev" / "config.json").exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
