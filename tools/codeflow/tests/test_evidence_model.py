"""Tests for evidence linking and validation."""

import pytest
import tempfile
from pathlib import Path

from codeflow.semantic.evidence_model import EvidenceValidator, EvidenceExtractor
from codeflow.semantic.interpretation_model import (
    EvidenceReference,
    SemanticClaim,
)
from codeflow.semantic.claim_types import ClaimType, EvidenceType
from codeflow.graph import AnalysisResult, CFG, SourceLocation


class MockAnalysisResult:
    """Mock AnalysisResult for testing."""

    def __init__(self, source_path: str):
        self.file_path = source_path
        self.language = "python"
        self.functions = {
            "main": CFG(
                name="main",
                source_location=SourceLocation("game.py", 1, 50),
            ),
            "is_winner": CFG(
                name="is_winner",
                source_location=SourceLocation("game.py", 20, 30),
            ),
            "display_board": CFG(
                name="display_board",
                source_location=SourceLocation("game.py", 35, 48),
            ),
        }
        self.errors = []
        self.warnings = []
        self.success = True
        self.analysis_incomplete = False


class TestEvidenceValidator:
    """Test EvidenceValidator class."""

    def test_validator_creation(self):
        """Test creating an evidence validator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test file\nprint('Hello')\n" * 50)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            assert validator.analysis == analysis

    def test_validate_valid_evidence(self):
        """Test validating valid evidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test file\nprint('Hello')\n" * 50)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="game.py",
                function_name="main",
                line_range=(1, 10),
            )

            assert validator.validate_evidence(evidence)

    def test_validate_missing_file(self):
        """Test validating evidence with missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="nonexistent.py",
                function_name="main",
                line_range=(1, 10),
            )

            assert not validator.validate_evidence(evidence)

    def test_validate_missing_function(self):
        """Test validating evidence with function not in analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="game.py",
                function_name="nonexistent_function",
                line_range=(1, 10),
            )

            assert not validator.validate_evidence(evidence)

    def test_validate_line_range_exceeds_file(self):
        """Test validating evidence with line range exceeding file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)  # 10 lines

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="game.py",
                function_name="main",
                line_range=(1, 100),  # Exceeds file size
            )

            assert not validator.validate_evidence(evidence)

    def test_validate_invalid_line_range(self):
        """Test validating evidence with invalid line range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="game.py",
                function_name="main",
                line_range=(10, 5),  # start > end
            )

            assert not validator.validate_evidence(evidence)

    def test_validate_claim(self):
        """Test validating a semantic claim."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 50)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="game.py",
                function_name="is_winner",
                line_range=(20, 30),
            )

            claim = SemanticClaim(
                statement="is_winner() checks for winning condition",
                claim_type=ClaimType.VERIFIED,
                evidence=[evidence],
            )

            assert validator.validate_claim(claim)

    def test_validate_claim_with_invalid_evidence(self):
        """Test validating a claim with invalid evidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            evidence = EvidenceReference(
                file_path="game.py",
                function_name="nonexistent",
                line_range=(1, 10),
            )

            claim = SemanticClaim(
                statement="Some claim",
                claim_type=ClaimType.VERIFIED,
                evidence=[evidence],
            )

            assert not validator.validate_claim(claim)

    def test_extract_code_snippet(self):
        """Test extracting code snippet from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
            test_file.write_text(content)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            snippet = validator.extract_code_snippet("game.py", (2, 4))

            assert "line 2" in snippet
            assert "line 3" in snippet
            assert "line 4" in snippet
            assert "line 1" not in snippet

    def test_extract_code_snippet_out_of_range(self):
        """Test extracting code snippet with out-of-range lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            validator = EvidenceValidator(analysis)

            snippet = validator.extract_code_snippet("game.py", (1, 100))

            assert snippet is None


class TestEvidenceExtractor:
    """Test EvidenceExtractor class."""

    def test_extractor_creation(self):
        """Test creating an evidence extractor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            assert extractor.analysis == analysis

    def test_extract_function_evidence(self):
        """Test extracting evidence for a specific function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 50)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            evidence = extractor.extract_function_evidence("is_winner")

            assert evidence is not None
            assert evidence.function_name == "is_winner"
            assert evidence.line_range == (20, 30)
            assert evidence.reference_type == EvidenceType.FUNCTION_DEFINITION

    def test_extract_function_evidence_not_found(self):
        """Test extracting evidence for non-existent function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            evidence = extractor.extract_function_evidence("nonexistent")

            assert evidence is None

    def test_extract_entry_point_evidence(self):
        """Test extracting evidence for entry points."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 50)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            evidence_list = extractor.extract_entry_point_evidence()

            assert len(evidence_list) > 0
            assert evidence_list[0].function_name == "main"
            assert evidence_list[0].reference_type == EvidenceType.ENTRY_POINT

    def test_extract_all_function_evidence(self):
        """Test extracting evidence for all functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 50)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            evidence_list = extractor.extract_all_function_evidence()

            assert len(evidence_list) == len(analysis.functions)

    def test_find_functions_matching_pattern(self):
        """Test finding functions matching a pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            matches = extractor.find_functions_matching_pattern("display")

            assert len(matches) == 1
            assert "display_board" in matches

    def test_find_functions_matching_pattern_case_insensitive(self):
        """Test that pattern matching is case-insensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            matches_lower = extractor.find_functions_matching_pattern("winner")
            matches_upper = extractor.find_functions_matching_pattern("WINNER")

            assert len(matches_lower) > 0
            assert len(matches_upper) > 0
            assert matches_lower == matches_upper

    def test_find_functions_no_matches(self):
        """Test finding functions with no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "game.py"
            test_file.write_text("# Test\n" * 10)

            analysis = MockAnalysisResult(str(test_file))
            extractor = EvidenceExtractor(analysis)

            matches = extractor.find_functions_matching_pattern("nonexistent")

            assert len(matches) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
