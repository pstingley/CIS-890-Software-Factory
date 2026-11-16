"""LLM provider abstraction for semantic interpretation.

Supports Claude, GPT, local models (vLLM/Ollama), and mock (heuristic-based) providers.
"""

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from codeflow.analyzers.base import AnalysisResult
from codeflow.semantic.interpretation_model import (
    SemanticInterpretation,
    SemanticClaim,
    Capability,
    Workflow,
    ComponentDescription,
    AlgorithmDescription,
)
from codeflow.semantic.claim_types import ClaimType
from codeflow.semantic.provider_config import (
    LLMProviderConfig,
    ClaudeConfig,
    GPTConfig,
    LocalConfig,
)

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract interface for LLM-backed semantic interpretation."""

    @abstractmethod
    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """
        Interpret AnalysisResult into semantic understanding.

        Args:
            analysis: Control-flow analysis result to interpret.

        Returns:
            SemanticInterpretation with application purpose, capabilities, workflows, etc.

        Raises:
            Exception: If interpretation fails and no fallback available.
        """
        pass


class ClaudeLLMProvider(LLMProvider):
    """Uses Anthropic Claude API for semantic interpretation."""

    def __init__(self, config: Optional[ClaudeConfig] = None):
        """Initialize Claude provider.

        Args:
            config: Claude configuration (uses default if None).
        """
        if config is None:
            config = ClaudeConfig()
        self.config = config
        self.api_key = config.get_api_key()

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Set environment variable or provide in config."
            )

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package required for Claude provider. Install: pip install anthropic")

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """Interpret analysis using Claude API."""
        logger.info("Interpreting analysis with Claude LLM")

        # Build prompt from analysis
        prompt = self._build_prompt(analysis)

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            interpretation = self._parse_response(response_text, analysis)
            logger.info(f"Claude interpretation successful: {len(interpretation.major_capabilities)} capabilities")
            return interpretation

        except Exception as e:
            logger.error(f"Claude interpretation failed: {e}")
            raise

    def _build_prompt(self, analysis: AnalysisResult) -> str:
        """Build prompt for Claude from analysis result."""
        # Infer language from file path extension
        file_path = analysis.file_path or ""
        if file_path.endswith(".py"):
            language = "python"
        elif file_path.endswith(".rs"):
            language = "rust"
        elif file_path.endswith(".php"):
            language = "php"
        else:
            language = "unknown"

        functions_summary = []
        for func_name, func_cfg in analysis.functions.items():
            if func_cfg.source_location:
                functions_summary.append(f"- {func_name} (lines {func_cfg.source_location.start_line}-{func_cfg.source_location.end_line})")
            else:
                functions_summary.append(f"- {func_name}")

        prompt = f"""Analyze this software system based on its control-flow analysis:

**Source Language:** {language}
**Source Path:** {analysis.file_path}

**Functions Analyzed:**
{chr(10).join(functions_summary)}

**Task:** Based ONLY on the analyzed functions and control flow, generate a semantic interpretation.

**Instructions:**
1. Identify the APPLICATION PURPOSE - what does this software do? (plain English, 1-2 sentences)
2. Identify TARGET USERS - who uses this software? Use ONLY information evident in the code (e.g., user input patterns, entry points). Do NOT infer user demographics, organizational purpose, or business intent without code evidence.
3. List MAJOR CAPABILITIES - what can users do with this software?
4. Describe PRIMARY WORKFLOWS - typical usage patterns and sequences.
5. Specify INPUTS/OUTPUTS - what data enters and leaves the system.
6. Identify KEY COMPONENTS - major architectural parts.
7. Mark claims as VERIFIED (supported by code), INFERRED (derived from patterns), or UNCERTAIN (dynamic/runtime).

**Output Format (valid JSON):**
{{
    "application_purpose": "plain English description of what it does",
    "target_users": ["user type 1", "user type 2"],
    "major_capabilities": [
        {{"name": "...", "description": "...", "claim_type": "VERIFIED"}},
        ...
    ],
    "primary_workflows": [
        {{"name": "...", "steps": ["step 1", "step 2"], "claim_type": "VERIFIED"}},
        ...
    ],
    "inputs": ["input 1", "input 2"],
    "outputs": ["output 1", "output 2"],
    "main_components": ["component 1", "component 2"],
    "constraints": ["constraint 1", "constraint 2"],
    "uncertain_behaviors": ["behavior that cannot be statically determined"]
}}

**Critical Requirements:**
- Do NOT describe user demographics, business purpose, or use cases without direct code evidence
- Mark inferred or uncertain claims explicitly
- Focus on what the code actually does, not what it might be used for
- Include line numbers and function names as evidence
"""
        return prompt

    def _parse_response(self, response_text: str, analysis: AnalysisResult) -> SemanticInterpretation:
        """Parse Claude response into SemanticInterpretation."""
        try:
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in Claude response")

            data = json.loads(json_match.group())

            # Build capabilities
            capabilities = []
            for cap_data in data.get("major_capabilities", []):
                claim_type = ClaimType(cap_data.get("claim_type", "INFERRED"))
                capabilities.append(
                    Capability(
                        name=cap_data["name"],
                        description=cap_data["description"],
                        claim_type=claim_type,
                    )
                )

            # Build workflows
            workflows = []
            for wf_data in data.get("primary_workflows", []):
                workflows.append(
                    Workflow(
                        name=wf_data["name"],
                        steps=wf_data.get("steps", []),
                    )
                )

            return SemanticInterpretation(
                application_purpose=data.get("application_purpose", ""),
                target_users=data.get("target_users", []),
                major_capabilities=capabilities,
                primary_workflows=workflows,
                unsupported_areas=data.get("unsupported_areas", []),
                uncertain_behaviors=data.get("uncertain_behaviors", []),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            raise ValueError(f"Invalid response format from Claude: {e}")


class GPTLLMProvider(LLMProvider):
    """Uses OpenAI GPT for semantic interpretation."""

    def __init__(self, config: Optional[GPTConfig] = None):
        """Initialize GPT provider.

        Args:
            config: GPT configuration (uses default if None).
        """
        if config is None:
            config = GPTConfig()
        self.config = config
        self.api_key = config.get_api_key()

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Set environment variable or provide in config."
            )

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required for GPT provider. Install: pip install openai")

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """Interpret analysis using GPT API."""
        logger.info("Interpreting analysis with GPT LLM")

        prompt = self._build_prompt(analysis)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.choices[0].message.content
            interpretation = self._parse_response(response_text, analysis)
            logger.info(f"GPT interpretation successful: {len(interpretation.major_capabilities)} capabilities")
            return interpretation

        except Exception as e:
            logger.error(f"GPT interpretation failed: {e}")
            raise

    def _build_prompt(self, analysis: AnalysisResult) -> str:
        """Build prompt for GPT from analysis result (similar to Claude)."""
        # Infer language from file path extension
        file_path = analysis.file_path or ""
        if file_path.endswith(".py"):
            language = "python"
        elif file_path.endswith(".rs"):
            language = "rust"
        elif file_path.endswith(".php"):
            language = "php"
        else:
            language = "unknown"

        functions_summary = []
        for func_name, func_cfg in analysis.functions.items():
            functions_summary.append(f"- {func_name}")

        prompt = f"""Analyze this software system:

**Language:** {language}
**Functions:** {', '.join(functions_summary)}

Generate semantic interpretation in JSON format:
{{
    "application_purpose": "...",
    "target_users": [...],
    "major_capabilities": [{{"name": "...", "description": "..."}}],
    "primary_workflows": [{{"name": "...", "steps": [...]}}],
    "constraints": [...]
}}

Focus on verified facts only. Mark inferred information clearly."""
        return prompt

    def _parse_response(self, response_text: str, analysis: AnalysisResult) -> SemanticInterpretation:
        """Parse GPT response into SemanticInterpretation."""
        try:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in GPT response")

            data = json.loads(json_match.group())

            capabilities = [
                Capability(name=cap["name"], description=cap["description"])
                for cap in data.get("major_capabilities", [])
            ]

            workflows = [
                Workflow(name=wf["name"], steps=wf.get("steps", []))
                for wf in data.get("primary_workflows", [])
            ]

            return SemanticInterpretation(
                application_purpose=data.get("application_purpose", ""),
                target_users=data.get("target_users", []),
                major_capabilities=capabilities,
                primary_workflows=workflows,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse GPT response: {e}")
            raise ValueError(f"Invalid response format from GPT: {e}")


class LocalLLMProvider(LLMProvider):
    """Uses local LLM via vLLM or Ollama."""

    def __init__(self, config: Optional[LocalConfig] = None):
        """Initialize local LLM provider.

        Args:
            config: Local LLM configuration (uses default if None).
        """
        if config is None:
            config = LocalConfig()
        self.config = config

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """Interpret analysis using local LLM."""
        logger.info(f"Interpreting analysis with local LLM at {self.config.endpoint_url}")

        try:
            import requests
        except ImportError:
            logger.warning("requests not available, using mock fallback")
            return MockLLMProvider().interpret_analysis(analysis)

        prompt = self._build_prompt(analysis)

        try:
            response = requests.post(
                f"{self.config.endpoint_url}/v1/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            response_text = data["choices"][0]["message"]["content"]
            interpretation = self._parse_response(response_text, analysis)
            logger.info(f"Local LLM interpretation successful")
            return interpretation

        except Exception as e:
            logger.error(f"Local LLM interpretation failed: {e}, using mock fallback")
            return MockLLMProvider().interpret_analysis(analysis)

    def _build_prompt(self, analysis: AnalysisResult) -> str:
        """Build prompt for local LLM."""
        # Infer language from file path extension
        file_path = analysis.file_path or ""
        if file_path.endswith(".py"):
            language = "python"
        elif file_path.endswith(".rs"):
            language = "rust"
        elif file_path.endswith(".php"):
            language = "php"
        else:
            language = "unknown"
        return f"Analyze this {language} code with {len(analysis.functions)} functions. Generate semantic interpretation in JSON."

    def _parse_response(self, response_text: str, analysis: AnalysisResult) -> SemanticInterpretation:
        """Parse local LLM response."""
        try:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")

            data = json.loads(json_match.group())
            return SemanticInterpretation(
                application_purpose=data.get("application_purpose", "Unknown"),
                target_users=data.get("target_users", []),
            )

        except (json.JSONDecodeError, ValueError):
            return MockLLMProvider().interpret_analysis(analysis)


class MockLLMProvider(LLMProvider):
    """Fallback heuristic-based provider that works without API keys."""

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """Generate interpretation using code heuristics only."""
        logger.info("Generating interpretation with mock (heuristic) provider")

        # Extract purpose from main/entry point
        purpose = self._infer_purpose(analysis)

        # Extract capabilities from function names
        capabilities = self._extract_capabilities(analysis)

        # Infer workflows from control flow
        workflows = self._infer_workflows(analysis)

        return SemanticInterpretation(
            application_purpose=purpose,
            target_users=self._infer_users(analysis),
            major_capabilities=capabilities,
            primary_workflows=workflows,
            unsupported_areas=[
                "Runtime behavior",
                "Dynamic imports",
                "Network I/O patterns",
            ],
            uncertain_behaviors=[
                "External API behavior",
                "File system operations",
                "User input validation edge cases",
            ],
        )

    def _infer_purpose(self, analysis: AnalysisResult) -> str:
        """Infer application purpose from code structure."""
        # Infer language from file path extension
        file_path = analysis.file_path or ""
        if file_path.endswith(".py"):
            language = "python"
        elif file_path.endswith(".rs"):
            language = "rust"
        elif file_path.endswith(".php"):
            language = "php"
        else:
            language = "unknown"

        func_names = list(analysis.functions.keys())

        # Heuristic: look for game/game-like patterns
        game_keywords = ["game", "play", "move", "board", "player", "win"]
        if any(kw in " ".join(func_names).lower() for kw in game_keywords):
            return f"A {language} application implementing a game or game-like system."

        # Heuristic: look for server/client patterns
        server_keywords = ["server", "request", "response", "listen", "accept"]
        if any(kw in " ".join(func_names).lower() for kw in server_keywords):
            return f"A {language} network server application."

        # Default
        return f"A {language} application with {len(analysis.functions)} functions."

    def _extract_capabilities(self, analysis: AnalysisResult) -> list:
        """Extract capabilities from function names and structure."""
        capabilities = []

        # Heuristic: function names hint at capabilities
        display_funcs = [n for n in analysis.functions.keys() if "display" in n.lower()]
        if display_funcs:
            capabilities.append(
                Capability(
                    name="Display/Output",
                    description=f"Outputs data to user via functions: {', '.join(display_funcs)}",
                    related_functions=display_funcs,
                )
            )

        validate_funcs = [n for n in analysis.functions.keys() if "valid" in n.lower()]
        if validate_funcs:
            capabilities.append(
                Capability(
                    name="Validation",
                    description=f"Validates user input or state via functions: {', '.join(validate_funcs)}",
                    related_functions=validate_funcs,
                )
            )

        process_funcs = [n for n in analysis.functions.keys() if "process" in n.lower() or "handle" in n.lower()]
        if process_funcs:
            capabilities.append(
                Capability(
                    name="Processing",
                    description=f"Processes data via functions: {', '.join(process_funcs)}",
                    related_functions=process_funcs,
                )
            )

        return capabilities

    def _infer_workflows(self, analysis: AnalysisResult) -> list:
        """Infer workflows from control flow patterns."""
        workflows = []

        if "main" in analysis.functions or any("main" in n.lower() for n in analysis.functions.keys()):
            workflows.append(
                Workflow(
                    name="Main workflow",
                    steps=[
                        "Start at entry point",
                        "Process main logic",
                        "Complete or loop",
                    ],
                    related_functions=list(analysis.functions.keys())[:3],
                )
            )

        return workflows

    def _infer_users(self, analysis: AnalysisResult) -> list:
        """Infer target users from code patterns."""
        users = []

        func_names = " ".join(analysis.functions.keys()).lower()

        if "player" in func_names or "move" in func_names:
            users.append("Players")
        if "admin" in func_names or "config" in func_names:
            users.append("Administrators")
        if "api" in func_names or "server" in func_names:
            users.append("Client programs")

        return users if users else ["Users"]


class SemanticInterpreterFactory:
    """Factory for creating LLM providers from configuration."""

    @staticmethod
    def create(config: Optional[LLMProviderConfig] = None) -> LLMProvider:
        """
        Create appropriate LLM provider based on configuration.

        Args:
            config: Provider configuration (uses defaults if None).

        Returns:
            LLMProvider instance ready to use.

        Raises:
            ValueError: If provider configuration is invalid or required dependencies missing.
        """
        if config is None:
            config = LLMProviderConfig.from_env()

        provider_type = config.provider.lower()

        if provider_type == "claude":
            if not config.claude.validate():
                logger.warning(
                    "Claude provider configured but ANTHROPIC_API_KEY missing, using mock"
                )
                return MockLLMProvider()
            return ClaudeLLMProvider(config.claude)

        elif provider_type == "gpt":
            if not config.gpt.validate():
                logger.warning("GPT provider configured but OPENAI_API_KEY missing, using mock")
                return MockLLMProvider()
            return GPTLLMProvider(config.gpt)

        elif provider_type == "local":
            if not config.local.validate():
                logger.warning("Local provider configuration invalid, using mock")
                return MockLLMProvider()
            return LocalLLMProvider(config.local)

        elif provider_type == "mock":
            return MockLLMProvider()

        else:
            logger.warning(f"Unknown provider type {provider_type}, using mock")
            return MockLLMProvider()
