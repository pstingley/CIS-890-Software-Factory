"""Semantic interpretation infrastructure for CodeFlow.

This package provides language-independent semantic understanding of analyzed code,
with evidence-linked claims and configurable LLM providers.
"""

from codeflow.semantic.interpretation_model import (
    SemanticInterpretation,
    SemanticClaim,
    EvidenceReference,
    Capability,
    Workflow,
    InputOutputSpec,
    OutputChannel,
    InputChannel,
    ErrorHandlingSpec,
    ComponentDescription,
    AlgorithmDescription,
)
from codeflow.semantic.claim_types import ClaimType, EvidenceType
from codeflow.semantic.llm_provider import (
    LLMProvider,
    ClaudeLLMProvider,
    GPTLLMProvider,
    LocalLLMProvider,
    MockLLMProvider,
    SemanticInterpreterFactory,
)
from codeflow.semantic.provider_config import (
    LLMProviderConfig,
    ClaudeConfig,
    GPTConfig,
    LocalConfig,
)
from codeflow.semantic.evidence_model import (
    EvidenceValidator,
    EvidenceExtractor,
)
from codeflow.semantic.semantic_interpreter import SemanticInterpreter

__all__ = [
    "SemanticInterpretation",
    "SemanticClaim",
    "EvidenceReference",
    "Capability",
    "Workflow",
    "InputOutputSpec",
    "InputChannel",
    "OutputChannel",
    "ErrorHandlingSpec",
    "ComponentDescription",
    "AlgorithmDescription",
    "ClaimType",
    "EvidenceType",
    "LLMProvider",
    "ClaudeLLMProvider",
    "GPTLLMProvider",
    "LocalLLMProvider",
    "MockLLMProvider",
    "SemanticInterpreterFactory",
    "LLMProviderConfig",
    "ClaudeConfig",
    "GPTConfig",
    "LocalConfig",
    "EvidenceValidator",
    "EvidenceExtractor",
    "SemanticInterpreter",
]
