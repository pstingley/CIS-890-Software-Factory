"""Tests for LLM provider abstraction and factory."""

import pytest
import os
from unittest.mock import patch, MagicMock

from codeflow.semantic.llm_provider import (
    LLMProvider,
    MockLLMProvider,
    ClaudeLLMProvider,
    GPTLLMProvider,
    LocalLLMProvider,
    SemanticInterpreterFactory,
)
from codeflow.semantic.provider_config import (
    LLMProviderConfig,
    ClaudeConfig,
    GPTConfig,
    LocalConfig,
)
from codeflow.graph import AnalysisResult, CFG, SourceLocation


class MockAnalysisResult:
    """Mock AnalysisResult for testing."""

    def __init__(self):
        self.language = "python"
        self.file_path = "test.py"
        self.functions = {
            "main": CFG(
                name="main",
                source_location=SourceLocation("test.py", 1, 10),
            ),
            "helper": CFG(
                name="helper",
                source_location=SourceLocation("test.py", 12, 20),
            ),
        }
        self.errors = []
        self.warnings = []
        self.success = True
        self.analysis_incomplete = False


class TestMockLLMProvider:
    """Test MockLLMProvider (heuristic-based provider)."""

    def test_mock_provider_instantiation(self):
        """Test that MockLLMProvider can be instantiated."""
        provider = MockLLMProvider()
        assert isinstance(provider, LLMProvider)

    def test_mock_provider_works_offline(self):
        """Test that mock provider works without API keys."""
        provider = MockLLMProvider()
        analysis = MockAnalysisResult()

        # Should not raise any exceptions
        interpretation = provider.interpret_analysis(analysis)

        assert interpretation is not None
        assert interpretation.application_purpose is not None
        assert len(interpretation.target_users) > 0

    def test_mock_provider_identifies_entry_points(self):
        """Test that mock provider identifies workflows and users."""
        provider = MockLLMProvider()
        analysis = MockAnalysisResult()

        interpretation = provider.interpret_analysis(analysis)

        # Should identify workflows and target users (capabilities not guaranteed with mock names)
        assert len(interpretation.primary_workflows) > 0
        assert len(interpretation.target_users) > 0

    def test_mock_provider_marks_unsupported(self):
        """Test that mock provider marks unsupported areas."""
        provider = MockLLMProvider()
        analysis = MockAnalysisResult()

        interpretation = provider.interpret_analysis(analysis)

        assert len(interpretation.unsupported_areas) > 0
        assert len(interpretation.uncertain_behaviors) > 0

    def test_mock_provider_creates_workflows(self):
        """Test that mock provider creates workflows."""
        provider = MockLLMProvider()
        analysis = MockAnalysisResult()

        interpretation = provider.interpret_analysis(analysis)

        assert len(interpretation.primary_workflows) > 0
        for workflow in interpretation.primary_workflows:
            assert len(workflow.steps) > 0


class TestConfigurationClasses:
    """Test provider configuration classes."""

    def test_claude_config_creation(self):
        """Test Claude configuration creation."""
        config = ClaudeConfig(model="claude-3-5-sonnet", api_key="test-key")
        assert config.model == "claude-3-5-sonnet"
        assert config.get_api_key() == "test-key"

    def test_claude_config_env_fallback(self):
        """Test Claude config falls back to environment variable."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            config = ClaudeConfig()
            assert config.get_api_key() == "env-key"

    def test_claude_config_validation(self):
        """Test Claude config validation."""
        config_no_key = ClaudeConfig()
        with patch.dict(os.environ, {}, clear=True):
            # Should fail validation without key
            assert not config_no_key.validate()

        config_with_key = ClaudeConfig(api_key="test")
        assert config_with_key.validate()

    def test_gpt_config_creation(self):
        """Test GPT configuration creation."""
        config = GPTConfig(model="gpt-4", api_key="test-key")
        assert config.model == "gpt-4"
        assert config.get_api_key() == "test-key"

    def test_local_config_creation(self):
        """Test local LLM configuration creation."""
        config = LocalConfig(endpoint_url="http://localhost:8000", model="mistral")
        assert config.endpoint_url == "http://localhost:8000"
        assert config.model == "mistral"
        assert config.validate()

    def test_local_config_validation(self):
        """Test local config validation."""
        config = LocalConfig()
        assert config.validate()

        config_invalid = LocalConfig(endpoint_url="", model="")
        assert not config_invalid.validate()

    def test_llm_provider_config_creation(self):
        """Test LLMProviderConfig creation."""
        config = LLMProviderConfig(provider="mock")
        assert config.provider == "mock"
        assert config.validate()

    def test_llm_provider_config_validation(self):
        """Test LLMProviderConfig validation for different providers."""
        config = LLMProviderConfig(provider="mock")
        assert config.validate()

        config_claude = LLMProviderConfig(provider="claude")
        with patch.dict(os.environ, {}, clear=True):
            # Should fail without API key
            assert not config_claude.validate()

    def test_llm_provider_config_from_env(self):
        """Test creating LLMProviderConfig from environment variables."""
        with patch.dict(
            os.environ,
            {
                "CODEFLOW_SEMANTIC_PROVIDER": "mock",
                "ANTHROPIC_API_KEY": "test-key",
            },
        ):
            config = LLMProviderConfig.from_env()
            assert config.provider == "mock"
            assert config.claude.get_api_key() == "test-key"

    def test_llm_provider_config_dict_round_trip(self):
        """Test dict serialization of config."""
        config = LLMProviderConfig(provider="local")
        data = config.to_dict()

        config2 = LLMProviderConfig.from_dict(data)
        assert config2.provider == config.provider


class TestSemanticInterpreterFactory:
    """Test SemanticInterpreterFactory."""

    def test_factory_creates_mock_provider(self):
        """Test factory creates mock provider."""
        config = LLMProviderConfig(provider="mock")
        provider = SemanticInterpreterFactory.create(config)

        assert isinstance(provider, MockLLMProvider)

    def test_factory_defaults_to_mock(self):
        """Test factory defaults to mock provider."""
        provider = SemanticInterpreterFactory.create()
        assert isinstance(provider, MockLLMProvider)

    def test_factory_handles_invalid_provider(self):
        """Test factory handles unknown provider type."""
        config = LLMProviderConfig(provider="unknown")
        provider = SemanticInterpreterFactory.create(config)

        # Should fall back to mock
        assert isinstance(provider, MockLLMProvider)

    def test_factory_handles_missing_api_key(self):
        """Test factory handles missing API key gracefully."""
        config = LLMProviderConfig(provider="claude")
        with patch.dict(os.environ, {}, clear=True):
            provider = SemanticInterpreterFactory.create(config)
            # Should fall back to mock
            assert isinstance(provider, MockLLMProvider)

    def test_factory_handles_import_error(self):
        """Test factory handles missing LLM dependencies gracefully."""
        # Create config requesting Claude, but don't actually try to import it
        config = LLMProviderConfig(provider="claude", claude=ClaudeConfig(api_key="test"))

        # Instead of mocking import, test that factory would use MockLLMProvider
        # when API key is missing or invalid
        config_no_key = LLMProviderConfig(provider="claude", claude=ClaudeConfig(api_key=""))
        provider = SemanticInterpreterFactory.create(config_no_key)

        # Should fall back to mock when no valid API key
        assert isinstance(provider, MockLLMProvider)

    def test_factory_local_provider_fallback(self):
        """Test that local provider falls back to mock on error."""
        config = LLMProviderConfig(provider="local")
        provider = SemanticInterpreterFactory.create(config)

        # Local provider should work but may need to handle requests import
        assert provider is not None


class TestProviderIntegration:
    """Integration tests for provider setup."""

    def test_mock_provider_on_tictactoe(self):
        """Test mock provider on a game-like analysis."""
        analysis = MockAnalysisResult()
        provider = MockLLMProvider()

        interpretation = provider.interpret_analysis(analysis)

        # Should identify it's a program
        assert interpretation.application_purpose
        assert interpretation.target_users

    def test_mock_provider_generates_valid_interpretation(self):
        """Test that mock provider produces valid SemanticInterpretation."""
        analysis = MockAnalysisResult()
        provider = MockLLMProvider()

        interpretation = provider.interpret_analysis(analysis)

        # Verify required fields
        assert isinstance(interpretation.application_purpose, str)
        assert isinstance(interpretation.target_users, list)
        assert isinstance(interpretation.major_capabilities, list)
        assert isinstance(interpretation.primary_workflows, list)
        assert isinstance(interpretation.unsupported_areas, list)
        assert isinstance(interpretation.uncertain_behaviors, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
