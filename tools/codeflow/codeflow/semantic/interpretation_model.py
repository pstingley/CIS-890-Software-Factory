"""Data model for semantic interpretation of analyzed code.

Represents hierarchical understanding of software systems with evidence linking.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
import json
from codeflow.semantic.claim_types import ClaimType, EvidenceType


@dataclass
class EvidenceReference:
    """Traceable link from semantic claim to source code location."""

    file_path: str
    """Path to source file (relative to project root)."""

    function_name: Optional[str] = None
    """Function containing the evidence (None if file-level)."""

    line_range: Optional[Tuple[int, int]] = None
    """Line range (start, end) containing evidence (1-based)."""

    code_snippet: Optional[str] = None
    """Actual code text from the evidence location."""

    reference_type: EvidenceType = EvidenceType.OTHER
    """Classification of this evidence (function_definition, control_flow, etc.)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        d = asdict(self)
        d["reference_type"] = str(self.reference_type)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvidenceReference":
        """Deserialize from dictionary."""
        d = dict(d)
        if isinstance(d.get("reference_type"), str):
            try:
                d["reference_type"] = EvidenceType(d["reference_type"])
            except ValueError:
                d["reference_type"] = EvidenceType.OTHER
        return cls(**d)


@dataclass
class SemanticClaim:
    """Single behavioral claim with evidence linking and confidence."""

    statement: str
    """The behavioral claim being made (e.g., 'is_winner() checks three-in-a-row patterns')."""

    claim_type: ClaimType
    """Classification: VERIFIED, INFERRED, or UNCERTAIN."""

    evidence: List[EvidenceReference] = field(default_factory=list)
    """List of source code locations supporting this claim."""

    reasoning: Optional[str] = None
    """Explanation of why we believe this claim (especially for INFERRED/UNCERTAIN)."""

    confidence: float = 1.0
    """Confidence level 0.0-1.0 (1.0 = fully confident, 0.0 = guess)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "statement": self.statement,
            "claim_type": str(self.claim_type),
            "evidence": [e.to_dict() for e in self.evidence],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SemanticClaim":
        """Deserialize from dictionary."""
        d = dict(d)
        if isinstance(d.get("claim_type"), str):
            try:
                d["claim_type"] = ClaimType(d["claim_type"])
            except ValueError:
                d["claim_type"] = ClaimType.UNCERTAIN
        d["evidence"] = [EvidenceReference.from_dict(e) for e in d.get("evidence", [])]
        return cls(**d)


@dataclass
class Capability:
    """Major application capability with evidence."""

    name: str
    """Name of the capability (e.g., 'Move validation')."""

    description: str
    """Plain-English description of what this capability does."""

    related_functions: List[str] = field(default_factory=list)
    """Names of functions implementing this capability."""

    evidence: List[EvidenceReference] = field(default_factory=list)
    """Source code evidence supporting this capability."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "related_functions": self.related_functions,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Capability":
        """Deserialize from dictionary."""
        d = dict(d)
        d["evidence"] = [EvidenceReference.from_dict(e) for e in d.get("evidence", [])]
        return cls(**d)


@dataclass
class Workflow:
    """Typical usage pattern or operational scenario."""

    name: str
    """Name of the workflow (e.g., 'Playing a game')."""

    steps: List[str] = field(default_factory=list)
    """Ordered steps in the workflow (plain English)."""

    related_functions: List[str] = field(default_factory=list)
    """Functions involved in this workflow."""

    evidence: List[EvidenceReference] = field(default_factory=list)
    """Control-flow evidence supporting this workflow."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "steps": self.steps,
            "related_functions": self.related_functions,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Workflow":
        """Deserialize from dictionary."""
        d = dict(d)
        d["evidence"] = [EvidenceReference.from_dict(e) for e in d.get("evidence", [])]
        return cls(**d)


@dataclass
class InputChannel:
    """Data input interface."""

    name: str
    """Input source name (e.g., 'User keyboard input', 'Config file')."""

    description: str
    """Description of what data is accepted."""

    data_type: Optional[str] = None
    """Type of input (string, int, file, network, etc.)."""


@dataclass
class OutputChannel:
    """Data output interface."""

    name: str
    """Output destination name (e.g., 'Terminal display', 'Log file')."""

    description: str
    """Description of what data is output."""

    data_type: Optional[str] = None
    """Type of output (string, int, file, network, etc.)."""


@dataclass
class InputOutputSpec:
    """Specification of system inputs, outputs, and data transformations."""

    inputs: List[InputChannel] = field(default_factory=list)
    """Input channels."""

    outputs: List[OutputChannel] = field(default_factory=list)
    """Output channels."""

    data_transformations: List[str] = field(default_factory=list)
    """High-level data transformations through system."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "inputs": [asdict(i) for i in self.inputs],
            "outputs": [asdict(o) for o in self.outputs],
            "data_transformations": self.data_transformations,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InputOutputSpec":
        """Deserialize from dictionary."""
        return cls(
            inputs=[InputChannel(**i) for i in d.get("inputs", [])],
            outputs=[OutputChannel(**o) for o in d.get("outputs", [])],
            data_transformations=d.get("data_transformations", []),
        )


@dataclass
class ErrorHandlingSpec:
    """Error handling and recovery specification."""

    error_types: List[str] = field(default_factory=list)
    """Types of errors handled (e.g., 'invalid move', 'file not found')."""

    detection_mechanisms: List[str] = field(default_factory=list)
    """How errors are detected (e.g., 'return code', 'exception', 'validation check')."""

    recovery_strategies: List[str] = field(default_factory=list)
    """How the system recovers (e.g., 'retry', 'default value', 'exit with error')."""

    related_functions: List[str] = field(default_factory=list)
    """Functions involved in error handling."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "error_types": self.error_types,
            "detection_mechanisms": self.detection_mechanisms,
            "recovery_strategies": self.recovery_strategies,
            "related_functions": self.related_functions,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ErrorHandlingSpec":
        """Deserialize from dictionary."""
        return cls(
            error_types=d.get("error_types", []),
            detection_mechanisms=d.get("detection_mechanisms", []),
            recovery_strategies=d.get("recovery_strategies", []),
            related_functions=d.get("related_functions", []),
        )


@dataclass
class ComponentDescription:
    """Description of a major software component."""

    name: str
    """Component name (e.g., 'Game Logic', 'User Interface')."""

    description: str
    """What this component does."""

    functions: List[str] = field(default_factory=list)
    """Functions in this component."""

    responsibilities: List[str] = field(default_factory=list)
    """Key responsibilities of this component."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "functions": self.functions,
            "responsibilities": self.responsibilities,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ComponentDescription":
        """Deserialize from dictionary."""
        return cls(
            name=d["name"],
            description=d["description"],
            functions=d.get("functions", []),
            responsibilities=d.get("responsibilities", []),
        )


@dataclass
class AlgorithmDescription:
    """Description of a major algorithm or data structure."""

    name: str
    """Algorithm name (e.g., 'Minimax', 'Binary Search')."""

    description: str
    """What this algorithm does."""

    related_functions: List[str] = field(default_factory=list)
    """Functions implementing this algorithm."""

    complexity: Optional[str] = None
    """Time/space complexity (e.g., 'O(n log n)')."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "related_functions": self.related_functions,
            "complexity": self.complexity,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AlgorithmDescription":
        """Deserialize from dictionary."""
        return cls(
            name=d["name"],
            description=d["description"],
            related_functions=d.get("related_functions", []),
            complexity=d.get("complexity"),
        )


@dataclass
class SemanticInterpretation:
    """Complete semantic understanding of analyzed code."""

    application_purpose: str
    """What the application does (plain English, non-technical)."""

    target_users: List[str]
    """Who uses the application (supported by source evidence)."""

    major_capabilities: List[Capability] = field(default_factory=list)
    """Major capabilities the application provides."""

    primary_workflows: List[Workflow] = field(default_factory=list)
    """Typical usage workflows."""

    inputs_outputs: InputOutputSpec = field(default_factory=InputOutputSpec)
    """Input/output specification."""

    architecture: str = ""
    """Architecture style (e.g., 'game-loop', 'request-response')."""

    main_components: List[ComponentDescription] = field(default_factory=list)
    """Major software components."""

    key_algorithms: List[AlgorithmDescription] = field(default_factory=list)
    """Key algorithms used."""

    constraints: List[SemanticClaim] = field(default_factory=list)
    """Constraints and limitations."""

    error_handling: ErrorHandlingSpec = field(default_factory=ErrorHandlingSpec)
    """Error handling specification."""

    unsupported_areas: List[str] = field(default_factory=list)
    """Areas not analyzed (e.g., 'Network I/O', 'File operations')."""

    uncertain_behaviors: List[str] = field(default_factory=list)
    """Behaviors that cannot be statically determined."""

    all_claims: List[SemanticClaim] = field(default_factory=list)
    """All semantic claims made during interpretation (for validation)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "application_purpose": self.application_purpose,
            "target_users": self.target_users,
            "major_capabilities": [c.to_dict() for c in self.major_capabilities],
            "primary_workflows": [w.to_dict() for w in self.primary_workflows],
            "inputs_outputs": self.inputs_outputs.to_dict(),
            "architecture": self.architecture,
            "main_components": [c.to_dict() for c in self.main_components],
            "key_algorithms": [a.to_dict() for a in self.key_algorithms],
            "constraints": [c.to_dict() for c in self.constraints],
            "error_handling": self.error_handling.to_dict(),
            "unsupported_areas": self.unsupported_areas,
            "uncertain_behaviors": self.uncertain_behaviors,
            "all_claims": [c.to_dict() for c in self.all_claims],
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SemanticInterpretation":
        """Deserialize from dictionary."""
        return cls(
            application_purpose=d["application_purpose"],
            target_users=d["target_users"],
            major_capabilities=[
                Capability.from_dict(c) for c in d.get("major_capabilities", [])
            ],
            primary_workflows=[
                Workflow.from_dict(w) for w in d.get("primary_workflows", [])
            ],
            inputs_outputs=InputOutputSpec.from_dict(d.get("inputs_outputs", {})),
            architecture=d.get("architecture", ""),
            main_components=[
                ComponentDescription.from_dict(c) for c in d.get("main_components", [])
            ],
            key_algorithms=[
                AlgorithmDescription.from_dict(a) for a in d.get("key_algorithms", [])
            ],
            constraints=[
                SemanticClaim.from_dict(c) for c in d.get("constraints", [])
            ],
            error_handling=ErrorHandlingSpec.from_dict(d.get("error_handling", {})),
            unsupported_areas=d.get("unsupported_areas", []),
            uncertain_behaviors=d.get("uncertain_behaviors", []),
            all_claims=[SemanticClaim.from_dict(c) for c in d.get("all_claims", [])],
        )

    @classmethod
    def from_json(cls, json_str: str) -> "SemanticInterpretation":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
