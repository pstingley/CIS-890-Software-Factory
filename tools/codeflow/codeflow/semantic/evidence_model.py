"""Evidence linking and validation for semantic claims."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from codeflow.analyzers.base import AnalysisResult
from codeflow.semantic.interpretation_model import (
    EvidenceReference,
    SemanticClaim,
)
from codeflow.semantic.claim_types import EvidenceType

logger = logging.getLogger(__name__)


class EvidenceValidator:
    """Validates that evidence references exist in source code and analysis result."""

    def __init__(self, analysis: AnalysisResult):
        """Initialize validator with analysis result.

        Args:
            analysis: ControlFlowAnalysis result containing functions and CFGs.
        """
        self.analysis = analysis
        # AnalysisResult uses file_path, not source_path
        self.source_root = Path(analysis.file_path).parent if analysis.file_path else Path.cwd()

    def validate_evidence(self, evidence: EvidenceReference) -> bool:
        """
        Validate that an evidence reference exists.

        Args:
            evidence: EvidenceReference to validate.

        Returns:
            True if evidence is valid and exists, False otherwise.
        """
        # Check file exists
        file_path = self.source_root / evidence.file_path
        if not file_path.exists():
            logger.warning(f"Evidence file not found: {file_path}")
            return False

        # Check function exists (if specified)
        if evidence.function_name:
            # analysis.functions is a dict: {name -> CFG}
            func_found = evidence.function_name in self.analysis.functions
            if not func_found:
                logger.warning(
                    f"Function {evidence.function_name} not found in analysis"
                )
                return False

        # Check line range is reasonable
        if evidence.line_range:
            start, end = evidence.line_range
            if start <= 0 or end <= 0 or start > end:
                logger.warning(f"Invalid line range: {evidence.line_range}")
                return False

            # Try to validate against file
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    total_lines = len(f.readlines())
                if end > total_lines:
                    logger.warning(
                        f"Line range {evidence.line_range} exceeds file length {total_lines}"
                    )
                    return False
            except Exception as e:
                logger.warning(f"Could not validate line range: {e}")
                return False

        return True

    def validate_claim(self, claim: SemanticClaim) -> bool:
        """
        Validate that all evidence in a claim is valid.

        Args:
            claim: Semantic claim to validate.

        Returns:
            True if all evidence references are valid.
        """
        if not claim.evidence:
            return True  # Claims without evidence are allowed

        for evidence in claim.evidence:
            if not self.validate_evidence(evidence):
                return False

        return True

    def extract_code_snippet(
        self, file_path: str, line_range: Tuple[int, int]
    ) -> Optional[str]:
        """
        Extract source code snippet from file.

        Args:
            file_path: Path to source file (relative to project root).
            line_range: Tuple of (start_line, end_line) in 1-based numbering.

        Returns:
            Code snippet or None if file/lines not found.
        """
        try:
            full_path = self.source_root / file_path
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            start, end = line_range
            if start < 1 or end < 1 or start > len(lines) or end > len(lines):
                return None

            # 1-based to 0-based conversion
            snippet_lines = lines[start - 1 : end]
            return "".join(snippet_lines).strip()

        except Exception as e:
            logger.warning(f"Could not extract code snippet: {e}")
            return None


class EvidenceExtractor:
    """Extracts evidence anchors from AnalysisResult for semantic interpretation."""

    def __init__(self, analysis: AnalysisResult):
        """Initialize extractor with analysis result.

        Args:
            analysis: Control-flow analysis result.
        """
        self.analysis = analysis

    def extract_function_evidence(self, function_name: str) -> Optional[EvidenceReference]:
        """
        Extract evidence reference for a specific function.

        Args:
            function_name: Name of the function to find evidence for.

        Returns:
            EvidenceReference for function definition, or None if not found.
        """
        # analysis.functions is a dict: {name -> CFG}
        if function_name in self.analysis.functions:
            func_cfg = self.analysis.functions[function_name]
            # Convert source_location to line_range if needed
            line_range = None
            if func_cfg.source_location:
                line_range = (func_cfg.source_location.start_line, func_cfg.source_location.end_line)

            return EvidenceReference(
                file_path=func_cfg.source_location.file if func_cfg.source_location else "unknown",
                function_name=function_name,
                line_range=line_range,
                code_snippet=function_name,
                reference_type=EvidenceType.FUNCTION_DEFINITION,
            )

        return None

    def extract_entry_point_evidence(self) -> List[EvidenceReference]:
        """
        Extract evidence for all entry points.

        Returns:
            List of EvidenceReference for entry points.
        """
        evidence = []
        # analysis.functions is a dict: {name -> CFG}
        for func_name, func_cfg in self.analysis.functions.items():
            # Heuristic: check if function name suggests entry point (main, run, start, etc.)
            is_entry = func_name in ("main", "__main__") or func_name.startswith("run_") or func_name.endswith("_main")
            if is_entry:
                line_range = None
                if func_cfg.source_location:
                    line_range = (func_cfg.source_location.start_line, func_cfg.source_location.end_line)

                evidence.append(
                    EvidenceReference(
                        file_path=func_cfg.source_location.file if func_cfg.source_location else "unknown",
                        function_name=func_name,
                        line_range=line_range,
                        code_snippet=func_name,
                        reference_type=EvidenceType.ENTRY_POINT,
                    )
                )

        return evidence

    def extract_all_function_evidence(self) -> List[EvidenceReference]:
        """
        Extract evidence references for all analyzed functions.

        Returns:
            List of all function evidence references.
        """
        evidence = []
        # analysis.functions is a dict: {name -> CFG}
        for func_name, func_cfg in self.analysis.functions.items():
            is_entry = func_name in ("main", "__main__") or func_name.startswith("run_") or func_name.endswith("_main")

            line_range = None
            if func_cfg.source_location:
                line_range = (func_cfg.source_location.start_line, func_cfg.source_location.end_line)

            evidence.append(
                EvidenceReference(
                    file_path=func_cfg.source_location.file if func_cfg.source_location else "unknown",
                    function_name=func_name,
                    line_range=line_range,
                    code_snippet=func_name,
                    reference_type=(
                        EvidenceType.ENTRY_POINT
                        if is_entry
                        else EvidenceType.FUNCTION_DEFINITION
                    ),
                )
            )

        return evidence

    def find_functions_matching_pattern(self, pattern: str) -> List[str]:
        """
        Find function names matching a pattern.

        Args:
            pattern: Substring to search for in function names (case-insensitive).

        Returns:
            List of matching function names.
        """
        pattern_lower = pattern.lower()
        # analysis.functions is a dict: {name -> CFG}
        return [
            func_name for func_name in self.analysis.functions
            if pattern_lower in func_name.lower()
        ]
