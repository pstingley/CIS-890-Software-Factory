"""Claim type and evidence type enumerations for semantic interpretation."""

from enum import Enum, auto


class ClaimType(Enum):
    """Classification of semantic claims based on source evidence."""

    VERIFIED = "VERIFIED"
    """Claim directly supported by source code or control-flow analysis."""

    INFERRED = "INFERRED"
    """Claim derived from code patterns but not explicitly stated."""

    UNCERTAIN = "UNCERTAIN"
    """Claim about dynamic or runtime behavior not statically determinable."""

    def __str__(self) -> str:
        return self.value


class EvidenceType(Enum):
    """Classification of evidence references linking claims to source code."""

    FUNCTION_DEFINITION = "function_definition"
    """Function signature or entire function body."""

    CONTROL_FLOW = "control_flow"
    """Control-flow graph node, branch, or path."""

    PATTERN = "pattern"
    """Code pattern detected (loop, conditional, etc.)."""

    ENTRY_POINT = "entry_point"
    """Program entry point (main, __main__, etc.)."""

    ERROR_HANDLING = "error_handling"
    """Exception handling or error recovery code."""

    API_CALL = "api_call"
    """Function call or external API invocation."""

    DATA_FLOW = "data_flow"
    """Data flow through program (variable assignment, etc.)."""

    SEMANTIC_LABEL = "semantic_label"
    """Semantic label from control-flow graph (actual code expression)."""

    OTHER = "other"
    """Other evidence type not covered above."""

    def __str__(self) -> str:
        return self.value
