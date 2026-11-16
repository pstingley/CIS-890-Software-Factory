"""Main SemanticInterpreter service orchestrating semantic interpretation pipeline."""

import logging
from typing import Optional, List, Tuple

from codeflow.analyzers.base import AnalysisResult
from codeflow.semantic.interpretation_model import (
    SemanticInterpretation,
    SemanticClaim,
)
from codeflow.semantic.claim_types import ClaimType, EvidenceType
from codeflow.semantic.llm_provider import (
    LLMProvider,
    SemanticInterpreterFactory,
)
from codeflow.semantic.provider_config import LLMProviderConfig
from codeflow.semantic.evidence_model import EvidenceValidator, EvidenceExtractor

logger = logging.getLogger(__name__)


class SemanticInterpreter:
    """Orchestrates semantic interpretation of control-flow analysis results."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        config: Optional[LLMProviderConfig] = None,
    ):
        """Initialize semantic interpreter.

        Args:
            provider: LLMProvider to use (creates default if None).
            config: LLMProviderConfig for provider selection (uses defaults if None).
        """
        if provider is not None:
            self.provider = provider
        elif config is not None:
            self.provider = SemanticInterpreterFactory.create(config)
        else:
            self.provider = SemanticInterpreterFactory.create()

        logger.info(f"SemanticInterpreter initialized with provider: {type(self.provider).__name__}")

    def interpret_analysis(
        self, analysis: AnalysisResult
    ) -> SemanticInterpretation:
        """
        Interpret AnalysisResult into semantic understanding with strict evidence validation.

        Args:
            analysis: Control-flow analysis result to interpret.

        Returns:
            SemanticInterpretation with validated claims and evidence traceability.

        Raises:
            Exception: If interpretation fails.
        """
        logger.info(
            f"Starting semantic interpretation for {analysis.file_path}"
        )

        # Get base interpretation from LLM provider
        try:
            interpretation = self.provider.interpret_analysis(analysis)
        except Exception as e:
            logger.error(f"Semantic interpretation failed: {e}")
            raise

        # Validate all claims and enforce evidence requirements
        validator = EvidenceValidator(analysis)
        extractor = EvidenceExtractor(analysis)

        validated_claims = []
        invalid_claims = []

        # Validate each claim from LLM
        for claim in interpretation.all_claims:
            validation_result = self._validate_claim_strict(claim, validator, analysis)

            if validation_result["valid"]:
                # Claim is valid - keep as-is or update claim type if needed
                validated_claims.append(claim)
            elif validation_result["claim_type"] == ClaimType.UNCERTAIN:
                # Mark claim as UNCERTAIN with reason
                claim.claim_type = ClaimType.UNCERTAIN
                claim.statement = f"{claim.statement} [UNCERTAIN: {validation_result['reason']}]"
                validated_claims.append(claim)
            else:
                # Reject claim entirely
                logger.warning(
                    f"Rejecting claim with invalid evidence: {claim.statement} "
                    f"(Reason: {validation_result['reason']})"
                )
                invalid_claims.append((claim, validation_result["reason"]))

        # Add entry-point evidence (always VERIFIED - from code analysis)
        entry_points = extractor.extract_entry_point_evidence()
        if entry_points:
            for ep in entry_points:
                entry_claim = SemanticClaim(
                    statement=f"Entry point: {ep.function_name}",
                    claim_type=ClaimType.VERIFIED,
                    evidence=[ep],
                )
                validated_claims.append(entry_claim)
                logger.debug(f"Added entry-point claim: {ep.function_name}")

        # Update interpretation with validated claims
        interpretation.all_claims = validated_claims

        logger.info(
            f"Semantic interpretation complete: {len(interpretation.major_capabilities)} capabilities, "
            f"{len(interpretation.primary_workflows)} workflows, {len(validated_claims)} validated claims, "
            f"{len(invalid_claims)} invalid/rejected claims"
        )

        # Store validation metadata for downstream use
        interpretation._validation_summary = {
            "total_claims_before": len(interpretation.all_claims) + len(invalid_claims),
            "valid_claims": len(validated_claims),
            "invalid_claims": len(invalid_claims),
            "rejected_reasons": [r[1] for r in invalid_claims],
        }

        return interpretation

    def _validate_claim_strict(
        self, claim: SemanticClaim, validator: EvidenceValidator, analysis: AnalysisResult
    ) -> dict:
        """
        Strictly validate a claim's evidence and claim type consistency.

        Args:
            claim: Claim to validate
            validator: Evidence validator instance
            analysis: Analysis result for context

        Returns:
            Dict with keys:
                - valid: bool (True if claim is acceptable as-is)
                - claim_type: ClaimType (suggested type if not valid)
                - reason: str (explanation if invalid)
        """
        # Rule 1: VERIFIED claims MUST have valid evidence
        if claim.claim_type == ClaimType.VERIFIED:
            if not claim.evidence:
                return {
                    "valid": False,
                    "claim_type": ClaimType.UNCERTAIN,
                    "reason": "VERIFIED claim has no evidence",
                }

            # Validate all evidence references
            all_evidence_valid = True
            invalid_evidence = []
            for evidence in claim.evidence:
                if not validator.validate_evidence(evidence):
                    all_evidence_valid = False
                    invalid_evidence.append(evidence.file_path)

            if not all_evidence_valid:
                return {
                    "valid": False,
                    "claim_type": ClaimType.UNCERTAIN,
                    "reason": f"Evidence invalid for files: {', '.join(invalid_evidence)}",
                }

        # Rule 2: Check for unsupported inferences (e.g., user demographics)
        unsupported_inferences = self._detect_unsupported_inferences(claim, analysis)
        if unsupported_inferences:
            if claim.claim_type == ClaimType.VERIFIED:
                return {
                    "valid": False,
                    "claim_type": ClaimType.UNCERTAIN,
                    "reason": f"Unsupported inference marked VERIFIED: {unsupported_inferences}",
                }
            else:
                # Already marked INFERRED/UNCERTAIN, which is correct
                pass

        # Rule 3: INFERRED claims should have some basis in evidence or analysis
        if claim.claim_type == ClaimType.INFERRED:
            if not claim.evidence and not self._has_analysis_basis(claim, analysis):
                logger.warning(f"INFERRED claim has no analysis basis: {claim.statement}")

        # Claim is valid as-is
        return {"valid": True, "claim_type": claim.claim_type, "reason": None}

    def _detect_unsupported_inferences(self, claim: SemanticClaim, analysis: AnalysisResult) -> Optional[str]:
        """
        Detect claims that make unsupported inferences about users, intent, or demographics.

        Args:
            claim: Claim to check
            analysis: Analysis result for context

        Returns:
            Description of unsupported inference, or None if claim is acceptable.
        """
        statement_lower = claim.statement.lower()

        # Detect demographic inferences not in source code
        demographic_keywords = ["student", "casual gamer", "enterprise user", "beginner", "professional"]
        for keyword in demographic_keywords:
            if keyword in statement_lower and claim.claim_type == ClaimType.VERIFIED:
                # Check if keyword is actually in source code
                found_in_source = False
                for func_cfg in analysis.functions.values():
                    if func_cfg.source_location and func_cfg.source_location.file:
                        try:
                            with open(func_cfg.source_location.file, 'r', encoding='utf-8', errors='ignore') as f:
                                source = f.read()
                                if keyword in source.lower():
                                    found_in_source = True
                                    break
                        except Exception:
                            pass

                if not found_in_source:
                    return f"Unsupported demographic inference: '{keyword}' not found in source code"

        # Detect organizational/business intent inferences
        business_keywords = ["suitable for", "intended for", "designed for", "targets"]
        for keyword in business_keywords:
            if keyword in statement_lower:
                # These should be INFERRED, not VERIFIED, unless in requirements/documentation
                if claim.claim_type == ClaimType.VERIFIED and not claim.evidence:
                    return f"Business intent claim '{keyword}' requires evidence or should be INFERRED"

        return None

    def _has_analysis_basis(self, claim: SemanticClaim, analysis: AnalysisResult) -> bool:
        """
        Check if an INFERRED claim has some basis in code analysis.

        Args:
            claim: Claim to check
            analysis: Analysis result

        Returns:
            True if claim references functions, patterns, or structural features in analysis.
        """
        # Check if claim mentions any functions in the analysis
        func_names = list(analysis.functions.keys())
        for func_name in func_names:
            if func_name in claim.statement:
                return True

        # Check if claim mentions patterns we analyze (loops, conditionals, etc.)
        pattern_keywords = ["loop", "conditional", "flow", "exception", "error", "return", "call"]
        for keyword in pattern_keywords:
            if keyword in claim.statement.lower():
                return True

        return False
