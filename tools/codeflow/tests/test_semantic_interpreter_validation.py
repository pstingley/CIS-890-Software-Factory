"""Test strict evidence validation in SemanticInterpreter."""

import tempfile
from pathlib import Path

import pytest

from codeflow.graph import AnalysisResult, CFG, SourceLocation
from codeflow.semantic.semantic_interpreter import SemanticInterpreter
from codeflow.semantic.interpretation_model import (
    SemanticInterpretation,
    SemanticClaim,
    EvidenceReference,
)
from codeflow.semantic.claim_types import ClaimType, EvidenceType
from codeflow.semantic.llm_provider import MockLLMProvider


class MockAnalysisResult:
    """Mock AnalysisResult for testing."""

    def __init__(self, file_path: str = "test.py"):
        self.language = "python"
        self.file_path = file_path
        self.functions = {
            "main": CFG(
                name="main",
                source_location=SourceLocation(file_path, 1, 10),
            ),
            "helper": CFG(
                name="helper",
                source_location=SourceLocation(file_path, 12, 20),
            ),
        }
        self.errors = []
        self.warnings = []
        self.success = True
        self.analysis_incomplete = False


class TestSemanticInterpreterValidation:
    """Test evidence validation in semantic interpreter."""

    def test_valid_evidence_accepted(self):
        """Test that claims with valid evidence are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # Create interpretation with valid evidence
            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
                all_claims=[
                    SemanticClaim(
                        statement="Application has a main function",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[
                            EvidenceReference(
                                file_path=str(test_file),
                                function_name="main",
                                line_range=(1, 2),
                                code_snippet="def main():",
                                reference_type=EvidenceType.FUNCTION_DEFINITION,
                            )
                        ],
                    )
                ],
            )

            # Mock the provider to return our interpretation
            original_interpret = interpreter.provider.interpret_analysis
            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Valid claim should be kept
            assert len(result.all_claims) > 0
            verified_claims = [c for c in result.all_claims if c.claim_type == ClaimType.VERIFIED]
            assert len(verified_claims) > 0

    def test_missing_evidence_marked_uncertain(self):
        """Test that VERIFIED claims without evidence are marked UNCERTAIN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # Create interpretation with VERIFIED claim but no evidence
            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
                all_claims=[
                    SemanticClaim(
                        statement="Application supports multiplayer",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[],  # No evidence!
                    )
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Claim should be marked UNCERTAIN
            unsupported_claims = [
                c for c in result.all_claims
                if "no evidence" in str(c.statement).lower()
            ]
            assert len(unsupported_claims) > 0, "Claim without evidence should be marked UNCERTAIN"

    def test_incorrect_source_locations_marked_uncertain(self):
        """Test that claims with invalid source locations are marked UNCERTAIN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # Create interpretation with invalid line range
            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
                all_claims=[
                    SemanticClaim(
                        statement="Application processes data",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[
                            EvidenceReference(
                                file_path=str(test_file),
                                function_name="nonexistent_function",  # Invalid function
                                line_range=(1, 2),
                                code_snippet="def nonexistent():",
                                reference_type=EvidenceType.FUNCTION_DEFINITION,
                            )
                        ],
                    )
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Claim with invalid evidence should be marked UNCERTAIN
            uncertain_claims = [c for c in result.all_claims if c.claim_type == ClaimType.UNCERTAIN]
            assert len(uncertain_claims) > 0, "Claims with invalid source should be marked UNCERTAIN"

    def test_unsupported_demographic_inference_rejected(self):
        """Test that unsupported demographic inferences are marked UNCERTAIN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            # Note: "student" is NOT in the source code
            test_file.write_text("def main():\n    play_game()\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # Create interpretation with unsupported demographic inference
            interp = SemanticInterpretation(
                application_purpose="A game for students and casual gamers",
                target_users=["Students", "Casual Gamers"],
                all_claims=[
                    SemanticClaim(
                        statement="Designed for students and casual gamers",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[],  # No evidence for demographics
                    )
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Claim with unsupported demographic should be marked UNCERTAIN or rejected
            unsupported_claims = [
                c for c in result.all_claims
                if c.claim_type == ClaimType.UNCERTAIN and "student" in c.statement.lower()
            ]
            # Either marked uncertain or removed
            assert len(result.all_claims) == 0 or len(unsupported_claims) > 0

    def test_nonempty_entry_point_evidence_added(self):
        """Test that entry-point evidence is extracted and added."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # Create basic interpretation
            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Entry-point evidence should be added
            entry_point_claims = [
                c for c in result.all_claims
                if "entry point" in c.statement.lower()
            ]
            assert len(entry_point_claims) > 0, "Entry-point claims should be added"
            # Entry points should be VERIFIED
            assert all(
                c.claim_type == ClaimType.VERIFIED for c in entry_point_claims
            ), "Entry points should be VERIFIED"

    def test_llm_incorrectly_labeling_unsupported_verified(self):
        """Test that LLM incorrectly marking unsupported claims VERIFIED are corrected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def play_game():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # LLM incorrectly marks a business intent claim as VERIFIED without evidence
            interp = SemanticInterpretation(
                application_purpose="A game for students",
                target_users=["Students"],
                all_claims=[
                    SemanticClaim(
                        statement="Designed for students to learn strategy",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[],  # No evidence
                    )
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Claim should be downgraded to UNCERTAIN
            assert any(
                c.claim_type == ClaimType.UNCERTAIN and "UNCERTAIN" in c.statement
                for c in result.all_claims
            ), "Unsupported VERIFIED claim should be marked UNCERTAIN"

    def test_validation_summary_exposed(self):
        """Test that validation results are exposed for downstream use."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
                all_claims=[
                    SemanticClaim(
                        statement="Valid claim",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[
                            EvidenceReference(
                                file_path=str(test_file),
                                function_name="main",
                                line_range=(1, 2),
                                code_snippet="def main():",
                                reference_type=EvidenceType.FUNCTION_DEFINITION,
                            )
                        ],
                    ),
                    SemanticClaim(
                        statement="Invalid claim with no evidence",
                        claim_type=ClaimType.VERIFIED,
                        evidence=[],
                    ),
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # Validation summary should be attached
            assert hasattr(result, "_validation_summary"), "Validation summary should be exposed"
            assert "valid_claims" in result._validation_summary
            assert "invalid_claims" in result._validation_summary
            assert "rejected_reasons" in result._validation_summary

    def test_inferred_claims_accepted_without_evidence(self):
        """Test that INFERRED claims without evidence are accepted (they're hypothetical)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            # INFERRED claims don't require evidence
            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
                all_claims=[
                    SemanticClaim(
                        statement="Likely handles user input from stdin",
                        claim_type=ClaimType.INFERRED,
                        evidence=[],  # No evidence needed for INFERRED
                    )
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # INFERRED claim should be kept
            inferred = [c for c in result.all_claims if c.claim_type == ClaimType.INFERRED]
            assert len(inferred) > 0, "INFERRED claims should be accepted"

    def test_uncertain_claims_accepted_with_reason(self):
        """Test that UNCERTAIN claims are explicitly marked with reasons."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def main():\n    pass\n")

            analysis = MockAnalysisResult(str(test_file))
            interpreter = SemanticInterpreter(provider=MockLLMProvider())

            interp = SemanticInterpretation(
                application_purpose="A test application",
                target_users=["Users"],
                all_claims=[
                    SemanticClaim(
                        statement="Application may use network I/O",
                        claim_type=ClaimType.UNCERTAIN,
                        evidence=[],
                    )
                ],
            )

            interpreter.provider.interpret_analysis = lambda a: interp

            result = interpreter.interpret_analysis(analysis)

            # UNCERTAIN claims should be in results
            uncertain = [c for c in result.all_claims if c.claim_type == ClaimType.UNCERTAIN]
            assert len(uncertain) > 0, "UNCERTAIN claims should be preserved"
