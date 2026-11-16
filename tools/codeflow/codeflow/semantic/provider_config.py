"""Configuration classes for LLM providers."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import os


@dataclass
class ClaudeConfig:
    """Configuration for Claude LLM provider."""

    model: str = "claude-3-5-sonnet-20241022"
    """Claude model identifier."""

    api_key: Optional[str] = None
    """API key (defaults to ANTHROPIC_API_KEY environment variable)."""

    max_tokens: int = 4096
    """Maximum tokens in response."""

    temperature: float = 0.7
    """Sampling temperature (0.0-1.0)."""

    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment."""
        return self.api_key or os.getenv("ANTHROPIC_API_KEY")

    def validate(self) -> bool:
        """Validate configuration."""
        return bool(self.get_api_key())


@dataclass
class GPTConfig:
    """Configuration for OpenAI GPT LLM provider."""

    model: str = "gpt-4-turbo"
    """GPT model identifier."""

    api_key: Optional[str] = None
    """API key (defaults to OPENAI_API_KEY environment variable)."""

    max_tokens: int = 4096
    """Maximum tokens in response."""

    temperature: float = 0.7
    """Sampling temperature (0.0-1.0)."""

    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment."""
        return self.api_key or os.getenv("OPENAI_API_KEY")

    def validate(self) -> bool:
        """Validate configuration."""
        return bool(self.get_api_key())


@dataclass
class LocalConfig:
    """Configuration for local LLM provider (vLLM/Ollama)."""

    endpoint_url: str = "http://localhost:8000"
    """HTTP endpoint for local LLM server."""

    model: str = "mistral"
    """Model name on local server."""

    max_tokens: int = 4096
    """Maximum tokens in response."""

    temperature: float = 0.7
    """Sampling temperature (0.0-1.0)."""

    timeout_seconds: int = 60
    """Request timeout in seconds."""

    def validate(self) -> bool:
        """Validate configuration (basic)."""
        return bool(self.endpoint_url) and bool(self.model)


@dataclass
class LLMProviderConfig:
    """Configuration for semantic interpretation LLM provider selection."""

    provider: str = "mock"
    """Provider type: 'claude', 'gpt', 'local', or 'mock'."""

    claude: ClaudeConfig = None
    """Claude configuration."""

    gpt: GPTConfig = None
    """GPT configuration."""

    local: LocalConfig = None
    """Local LLM configuration."""

    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.claude is None:
            self.claude = ClaudeConfig()
        if self.gpt is None:
            self.gpt = GPTConfig()
        if self.local is None:
            self.local = LocalConfig()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "provider": self.provider,
            "claude": asdict(self.claude),
            "gpt": asdict(self.gpt),
            "local": asdict(self.local),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LLMProviderConfig":
        """Deserialize from dictionary."""
        return cls(
            provider=d.get("provider", "mock"),
            claude=ClaudeConfig(**d.get("claude", {})) if "claude" in d else None,
            gpt=GPTConfig(**d.get("gpt", {})) if "gpt" in d else None,
            local=LocalConfig(**d.get("local", {})) if "local" in d else None,
        )

    @classmethod
    def from_env(cls) -> "LLMProviderConfig":
        """Create configuration from environment variables."""
        provider = os.getenv("CODEFLOW_SEMANTIC_PROVIDER", "mock")

        config = cls(provider=provider)

        # Claude config from env
        if os.getenv("ANTHROPIC_API_KEY"):
            config.claude = ClaudeConfig(
                model=os.getenv(
                    "CODEFLOW_CLAUDE_MODEL", "claude-3-5-sonnet-20241022"
                ),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )

        # GPT config from env
        if os.getenv("OPENAI_API_KEY"):
            config.gpt = GPTConfig(
                model=os.getenv("CODEFLOW_GPT_MODEL", "gpt-4-turbo"),
                api_key=os.getenv("OPENAI_API_KEY"),
            )

        # Local config from env
        if os.getenv("CODEFLOW_LOCAL_ENDPOINT"):
            config.local = LocalConfig(
                endpoint_url=os.getenv(
                    "CODEFLOW_LOCAL_ENDPOINT", "http://localhost:8000"
                ),
                model=os.getenv("CODEFLOW_LOCAL_MODEL", "mistral"),
            )

        return config

    def validate(self) -> bool:
        """Validate that selected provider is configured."""
        if self.provider == "claude":
            return self.claude.validate()
        elif self.provider == "gpt":
            return self.gpt.validate()
        elif self.provider == "local":
            return self.local.validate()
        elif self.provider == "mock":
            return True  # Always valid
        return False
