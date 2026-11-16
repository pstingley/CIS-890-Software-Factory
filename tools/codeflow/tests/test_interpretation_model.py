"""Tests for semantic interpretation data model."""

import pytest
import json
from codeflow.semantic.interpretation_model import (
    SemanticClaim,
    EvidenceReference,
    Capability,
    Workflow,
    InputChannel,
    OutputChannel,
    InputOutputSpec,
    ErrorHandlingSpec,
    ComponentDescription,
    AlgorithmDescription,
    SemanticInterpretation,
)
from codeflow.semantic.claim_types import ClaimType, EvidenceType


class TestEvidenceReference:
    """Test EvidenceReference dataclass."""

    def test_create_basic_evidence(self):
        """Test creating a basic evidence reference."""
        evidence = EvidenceReference(
            file_path="src/game.py",
            function_name="is_winner",
            line_range=(20, 30),
            code_snippet="def is_winner(board):",
            reference_type=EvidenceType.FUNCTION_DEFINITION,
        )

        assert evidence.file_path == "src/game.py"
        assert evidence.function_name == "is_winner"
        assert evidence.line_range == (20, 30)
        assert evidence.reference_type == EvidenceType.FUNCTION_DEFINITION

    def test_evidence_serialization(self):
        """Test serialization and deserialization."""
        evidence = EvidenceReference(
            file_path="src/game.py",
            function_name="is_winner",
            line_range=(20, 30),
            reference_type=EvidenceType.CONTROL_FLOW,
        )

        data = evidence.to_dict()
        evidence2 = EvidenceReference.from_dict(data)

        assert evidence2.file_path == evidence.file_path
        assert evidence2.function_name == evidence.function_name
        assert evidence2.line_range == evidence.line_range
        assert evidence2.reference_type == evidence.reference_type

    def test_evidence_with_no_function(self):
        """Test evidence at file level (no function)."""
        evidence = EvidenceReference(
            file_path="src/config.py",
            line_range=(1, 10),
            reference_type=EvidenceType.OTHER,
        )

        assert evidence.function_name is None
        assert evidence.file_path == "src/config.py"


class TestSemanticClaim:
    """Test SemanticClaim dataclass."""

    def test_create_verified_claim(self):
        """Test creating a verified claim."""
        evidence = EvidenceReference(
            file_path="src/game.py",
            function_name="is_winner",
            line_range=(20, 30),
        )

        claim = SemanticClaim(
            statement="is_winner() checks for three-in-a-row patterns",
            claim_type=ClaimType.VERIFIED,
            evidence=[evidence],
            confidence=1.0,
        )

        assert claim.claim_type == ClaimType.VERIFIED
        assert len(claim.evidence) == 1
        assert claim.confidence == 1.0

    def test_create_inferred_claim(self):
        """Test creating an inferred claim."""
        claim = SemanticClaim(
            statement="The game supports two players",
            claim_type=ClaimType.INFERRED,
            reasoning="Observed two player input loops in control flow",
            confidence=0.8,
        )

        assert claim.claim_type == ClaimType.INFERRED
        assert claim.reasoning is not None
        assert claim.confidence == 0.8

    def test_create_uncertain_claim(self):
        """Test creating an uncertain claim."""
        claim = SemanticClaim(
            statement="Network communication uses SSL",
            claim_type=ClaimType.UNCERTAIN,
            reasoning="Cannot determine SSL configuration at static analysis time",
            confidence=0.3,
        )

        assert claim.claim_type == ClaimType.UNCERTAIN
        assert claim.confidence == 0.3

    def test_claim_serialization(self):
        """Test claim JSON round-trip."""
        evidence = EvidenceReference(
            file_path="src/game.py",
            function_name="is_winner",
            line_range=(20, 30),
        )

        claim = SemanticClaim(
            statement="is_winner() checks for winning conditions",
            claim_type=ClaimType.VERIFIED,
            evidence=[evidence],
            confidence=1.0,
        )

        data = claim.to_dict()
        claim2 = SemanticClaim.from_dict(data)

        assert claim2.statement == claim.statement
        assert claim2.claim_type == claim.claim_type
        assert len(claim2.evidence) == 1


class TestCapability:
    """Test Capability dataclass."""

    def test_create_capability(self):
        """Test creating a capability."""
        evidence = EvidenceReference(
            file_path="src/game.py",
            function_name="display_board",
            line_range=(42, 48),
        )

        capability = Capability(
            name="Display board state",
            description="Shows the current game board to players",
            related_functions=["display_board"],
            evidence=[evidence],
        )

        assert capability.name == "Display board state"
        assert len(capability.related_functions) == 1
        assert len(capability.evidence) == 1

    def test_capability_serialization(self):
        """Test capability serialization."""
        capability = Capability(
            name="Validate moves",
            description="Checks if a move is legal",
            related_functions=["is_valid_move"],
        )

        data = capability.to_dict()
        capability2 = Capability.from_dict(data)

        assert capability2.name == capability.name
        assert capability2.description == capability.description


class TestWorkflow:
    """Test Workflow dataclass."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = Workflow(
            name="Playing a game",
            steps=[
                "Initialize board",
                "Display board",
                "Get player move",
                "Validate move",
                "Update board",
                "Check for winner",
                "Switch player",
                "Repeat until game over",
            ],
            related_functions=["main", "display_board", "is_valid_move"],
        )

        assert workflow.name == "Playing a game"
        assert len(workflow.steps) == 8
        assert len(workflow.related_functions) == 3

    def test_workflow_serialization(self):
        """Test workflow serialization."""
        workflow = Workflow(
            name="Initialize game",
            steps=["Create empty board", "Set first player"],
            related_functions=["__init__"],
        )

        data = workflow.to_dict()
        workflow2 = Workflow.from_dict(data)

        assert workflow2.name == workflow.name
        assert len(workflow2.steps) == len(workflow.steps)


class TestInputOutputSpec:
    """Test InputOutputSpec dataclass."""

    def test_create_io_spec(self):
        """Test creating an I/O specification."""
        input_chan = InputChannel(
            name="User keyboard input",
            description="Player moves via terminal",
            data_type="string",
        )

        output_chan = OutputChannel(
            name="Terminal display",
            description="Game board and status output",
            data_type="text",
        )

        io_spec = InputOutputSpec(
            inputs=[input_chan],
            outputs=[output_chan],
            data_transformations=["User input → game move → board update"],
        )

        assert len(io_spec.inputs) == 1
        assert len(io_spec.outputs) == 1
        assert len(io_spec.data_transformations) == 1

    def test_io_spec_serialization(self):
        """Test I/O spec serialization."""
        io_spec = InputOutputSpec(
            inputs=[InputChannel("Test input", "Test data")],
            outputs=[OutputChannel("Test output", "Test results")],
        )

        data = io_spec.to_dict()
        io_spec2 = InputOutputSpec.from_dict(data)

        assert len(io_spec2.inputs) == 1
        assert len(io_spec2.outputs) == 1


class TestErrorHandlingSpec:
    """Test ErrorHandlingSpec dataclass."""

    def test_create_error_spec(self):
        """Test creating an error handling specification."""
        error_spec = ErrorHandlingSpec(
            error_types=["Invalid move", "Invalid board state"],
            detection_mechanisms=["Move validation check", "Board consistency check"],
            recovery_strategies=["Reject move and re-prompt", "Reset board"],
            related_functions=["is_valid_move", "validate_board"],
        )

        assert len(error_spec.error_types) == 2
        assert len(error_spec.detection_mechanisms) == 2
        assert len(error_spec.recovery_strategies) == 2

    def test_error_spec_serialization(self):
        """Test error spec serialization."""
        error_spec = ErrorHandlingSpec(
            error_types=["Test error"],
        )

        data = error_spec.to_dict()
        error_spec2 = ErrorHandlingSpec.from_dict(data)

        assert len(error_spec2.error_types) == 1


class TestComponentDescription:
    """Test ComponentDescription dataclass."""

    def test_create_component(self):
        """Test creating a component description."""
        component = ComponentDescription(
            name="Game Logic",
            description="Core game rules and state management",
            functions=["is_winner", "is_valid_move", "make_move"],
            responsibilities=[
                "Enforce game rules",
                "Maintain game state",
                "Determine game outcome",
            ],
        )

        assert component.name == "Game Logic"
        assert len(component.functions) == 3
        assert len(component.responsibilities) == 3


class TestAlgorithmDescription:
    """Test AlgorithmDescription dataclass."""

    def test_create_algorithm(self):
        """Test creating an algorithm description."""
        algorithm = AlgorithmDescription(
            name="Minimax",
            description="Game tree search for optimal move selection",
            related_functions=["minimax", "evaluate_position"],
            complexity="O(b^d) where b is branching factor, d is depth",
        )

        assert algorithm.name == "Minimax"
        assert algorithm.complexity is not None


class TestSemanticInterpretation:
    """Test SemanticInterpretation dataclass."""

    def test_create_basic_interpretation(self):
        """Test creating a basic semantic interpretation."""
        interpretation = SemanticInterpretation(
            application_purpose="A terminal-based two-player Tic-Tac-Toe game",
            target_users=["Two human players using a terminal interface"],
            major_capabilities=[
                Capability(
                    name="Display game board",
                    description="Shows board state to players",
                ),
                Capability(
                    name="Validate player moves",
                    description="Checks if a move is legal",
                ),
            ],
        )

        assert interpretation.application_purpose is not None
        assert len(interpretation.target_users) == 1
        assert len(interpretation.major_capabilities) == 2

    def test_interpretation_serialization(self):
        """Test interpretation JSON serialization."""
        interpretation = SemanticInterpretation(
            application_purpose="Test application",
            target_users=["Test users"],
            major_capabilities=[
                Capability(name="Test capability", description="Does testing")
            ],
        )

        json_str = interpretation.to_json()
        interpretation2 = SemanticInterpretation.from_json(json_str)

        assert interpretation2.application_purpose == interpretation.application_purpose
        assert len(interpretation2.major_capabilities) == 1

    def test_interpretation_dict_round_trip(self):
        """Test dict serialization round-trip."""
        interpretation = SemanticInterpretation(
            application_purpose="Test app",
            target_users=["Users"],
            unsupported_areas=["Network I/O"],
            uncertain_behaviors=["Dynamic imports"],
        )

        data = interpretation.to_dict()
        interpretation2 = SemanticInterpretation.from_dict(data)

        assert interpretation2.application_purpose == interpretation.application_purpose
        assert len(interpretation2.unsupported_areas) == 1
        assert len(interpretation2.uncertain_behaviors) == 1

    def test_interpretation_with_all_fields(self):
        """Test interpretation with all fields populated."""
        interpretation = SemanticInterpretation(
            application_purpose="Terminal-based Tic-Tac-Toe",
            target_users=["Two human players"],
            major_capabilities=[
                Capability("Display", "Show board"),
                Capability("Validate", "Check moves"),
            ],
            primary_workflows=[
                Workflow("Play game", ["Start", "Play", "End"])
            ],
            architecture="Game loop with player alternation",
            main_components=[
                ComponentDescription("Game Logic", "Core game rules")
            ],
            key_algorithms=[
                AlgorithmDescription("Win detection", "Check 3-in-a-row")
            ],
        )

        # Serialize and deserialize
        json_str = interpretation.to_json()
        interpretation2 = SemanticInterpretation.from_json(json_str)

        assert interpretation2.application_purpose == interpretation.application_purpose
        assert len(interpretation2.major_capabilities) == 2
        assert len(interpretation2.primary_workflows) == 1
        assert len(interpretation2.main_components) == 1
        assert len(interpretation2.key_algorithms) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
