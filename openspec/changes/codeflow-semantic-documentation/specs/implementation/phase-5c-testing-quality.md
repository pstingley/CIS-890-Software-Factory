# Phase 5c: Quality, Testing & Acceptance (1-2 weeks)

## Overview

Phase 5c implements comprehensive acceptance and regression testing to validate DOC-002 quality, verifies semantic accuracy, measures performance, and completes documentation for user adoption.

**Key Deliverables:**
- Complete acceptance test suite (AT-1 through AT-7)
- Performance benchmarking and optimization
- Regression test suite (Python, Rust, PHP)
- User documentation and examples
- Quality metrics and reporting

**Success Criteria:**
- All acceptance tests passing
- Semantic accuracy ≥95%
- Cross-language consistency within ±10%
- Document generation < 15 seconds per file
- Zero regressions in existing CodeFlow functionality

---

## Tasks

### 5c-1: Acceptance Test Suite Implementation (3-4 days)

**Goal:** Implement comprehensive acceptance tests from requirements (AT-1 through AT-7).

**Deliverables:**
- `tools/codeflow/tests/test_acceptance_doc002.py`

**Acceptance Tests:**

**AT-1: Non-Technical Reader Comprehension Test**

Objective: Verify that Functional_Description.docx is readable by non-technical stakeholders.

Implementation:
```python
def test_at1_functional_doc_comprehension():
    """
    Non-technical reader should be able to identify:
    1. What the application does
    2. Who should use it
    3. Major capabilities
    4. How to get started

    Without needing to read source code or technical jargon.
    """
    # Generate Functional_Description.docx for tic-tac-toe
    # Read document text
    # Verify: mentions "game", "players", "board", "win"
    # Verify: no jargon like "graph", "node", "CFG"
    # Verify: no statistics like "15 nodes and 23 edges"
    # Count comprehension indicators (simple language score)
    assert comprehension_score >= 0.80  # 80% clear statements
```

**AT-2: Engineer Technical Accuracy Test**

Objective: Verify that Technical_Description.docx accurately describes architecture for engineers.

Implementation:
```python
def test_at2_technical_doc_accuracy():
    """
    Engineer should be able to understand:
    1. Application architecture
    2. Major components and interactions
    3. Control flow and algorithms
    4. Error handling

    Descriptions must match the actual CFG and analysis results.
    """
    # Generate Technical_Description.docx for tic-tac-toe
    # Verify: identifies main() as entry point
    # Verify: describes game-loop architecture correctly
    # Verify: mentions decision nodes (win/draw checks)
    # Compare against CFG structure
    # Check evidence references are valid
    assert technical_accuracy_score >= 0.95  # 95% accurate
```

**AT-3: Evidence Traceability Audit**

Objective: 100% of VERIFIED claims must have valid evidence; ≥95% of INFERRED claims must be marked.

Implementation:
```python
def test_at3_evidence_traceability():
    """
    All behavioral claims must be traceable to source code.
    """
    interpretation = generate_interpretation(tic_tac_toe_analysis)

    verified_count = 0
    verified_valid = 0
    inferred_count = 0
    inferred_marked = 0

    for claim in interpretation.all_claims:
        if claim.claim_type == ClaimType.VERIFIED:
            verified_count += 1
            # Validate evidence
            if validate_evidence(claim.evidence, analysis):
                verified_valid += 1
        elif claim.claim_type == ClaimType.INFERRED:
            inferred_count += 1
            # Verify claim is marked as inference
            if "inferred" in claim.statement.lower() or claim.reasoning:
                inferred_marked += 1

    # 100% of verified claims must have valid evidence
    assert verified_valid == verified_count or verified_count == 0

    # ≥95% of inferred claims must be explicitly marked
    if inferred_count > 0:
        assert inferred_marked / inferred_count >= 0.95
```

**AT-4: No Template Repetition**

Objective: Regenerated documents must NOT contain meaningless statistics.

Implementation:
```python
def test_at4_no_template_repetition():
    """
    Documents must describe behavior, not graph statistics.
    """
    func_doc = generate_functional_description(tic_tac_toe_analysis)
    tech_doc = generate_technical_description(tic_tac_toe_analysis)

    # Count anti-patterns
    forbidden_patterns = [
        r"\d+\s+statement\s+nodes?",
        r"\d+\s+decision\s+nodes?",
        r"contains\s+\d+\s+nodes? and \d+\s+edges?",
        r"has\s+\d+\s+function[s]?",
        r"graph has.*CFG",
    ]

    for doc in [func_doc, tech_doc]:
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, doc.text, re.IGNORECASE)
            # Allow ≤2 mentions per 10 pages (legitimate technical descriptions)
            page_count = len(doc.paragraphs) / 50  # rough estimate
            max_allowed = 2 * (page_count / 10)
            assert len(matches) <= max_allowed, \
                f"Found {len(matches)} template repetitions in {len(doc.paragraphs)} paragraphs"
```

**AT-5: Behavioral Accuracy**

Objective: ≥95% of claims must accurately reflect CFG analysis.

Implementation:
```python
def test_at5_behavioral_accuracy():
    """
    Document claims must match actual control-flow behavior.
    """
    interpretation = generate_interpretation(tic_tac_toe_analysis)

    # Verify specific claims against CFG
    claims_to_verify = [
        # Format: (claim_text_pattern, expected_cfgs_to_find, claim_object)
        (r"game.*loop", ["main -> display_board -> get_move -> validate"], ...),
        (r"win.*condition", ["is_winner"], ...),
        (r"draw", ["no more empty spaces"], ...),
    ]

    correct = 0
    for claim_pattern, expected_patterns, claim_obj in claims_to_verify:
        found = False
        for expected in expected_patterns:
            if cfgs_match_pattern(tic_tac_toe_analysis, expected):
                found = True
        if found:
            correct += 1

    accuracy = correct / len(claims_to_verify)
    assert accuracy >= 0.95, f"Behavioral accuracy {accuracy} < 95%"
```

**AT-6: Cross-Language Consistency**

Objective: Document quality within ±10% across Python, Rust, PHP.

Implementation:
```python
def test_at6_cross_language_consistency():
    """
    Semantic interpretation quality should be consistent across languages.
    """
    # Analyze equivalent programs in Python, Rust, PHP
    py_interp = generate_interpretation(py_analysis)
    rs_interp = generate_interpretation(rs_analysis)
    php_interp = generate_interpretation(php_analysis)

    # Compare key metrics
    metrics = [
        ("capability_count", [len(py_interp.major_capabilities),
                             len(rs_interp.major_capabilities),
                             len(php_interp.major_capabilities)]),
        ("workflow_count", [...]),
        ("error_handling_completeness", [...]),
    ]

    for metric_name, values in metrics:
        mean = statistics.mean(values)
        for value in values:
            variance_pct = abs(value - mean) / mean * 100
            assert variance_pct <= 10, \
                f"{metric_name} variance {variance_pct}% > 10% across languages"
```

**AT-7: Performance Benchmarking**

Objective: Semantic interpretation and document generation complete in reasonable time.

Implementation:
```python
def test_at7_performance_benchmarking():
    """
    Performance targets for DOC-002 generation.
    """
    source_file = "tic_tac_toe.py"

    # Measure semantic interpretation time (using mock provider)
    start = time.time()
    interpretation = generate_interpretation(tic_tac_toe_analysis)
    interp_time = time.time() - start

    # Measure document generation
    start = time.time()
    func_doc = generate_functional_description(interpretation, tic_tac_toe_analysis)
    tech_doc = generate_technical_description(interpretation, tic_tac_toe_analysis)
    doc_time = time.time() - start

    # Performance targets
    assert interp_time <= 5.0, f"Interpretation time {interp_time}s > 5s"
    assert doc_time <= 10.0, f"Document generation {doc_time}s > 10s"

    # With real LLM provider (e.g., Claude), expect ~15s total
    # This test uses mock provider for <5s interpretation
```

**Additional Regression Tests:**

```python
def test_tic_tac_toe_complete_pipeline():
    """Full pipeline: Python → analysis → interpretation → documents."""
    # Verify no crashes
    # Verify all outputs created
    # Verify cross-file consistency

def test_rust_complete_pipeline():
    """Full pipeline: Rust → analysis → interpretation → documents."""

def test_php_complete_pipeline():
    """Full pipeline: PHP → analysis → interpretation → documents."""

def test_existing_codeflow_regression():
    """Verify no breaking changes to existing functionality."""
    # Verify HTML output unchanged
    # Verify JSON export unchanged
    # Verify DOC-001 generation still works
    # Verify SPEC.md generation still works
```

---

### 5c-2: Quality Metrics and Reporting (2-3 days)

**Goal:** Implement metrics collection and reporting framework.

**Deliverables:**
- `tools/codeflow/codeflow/semantic/quality_metrics.py`
  - Metrics collection classes
  - Reporting interface

```python
class QualityMetrics:
    """Collect DOC-002 quality metrics."""

    def __init__(self):
        self.metrics = {}

    def report_comprehension_score(self, language: str, score: float):
        """Non-technical comprehension score (0.0-1.0)"""
        self.metrics[f"comprehension_{language}"] = score

    def report_technical_accuracy(self, language: str, accuracy: float):
        """Technical accuracy score (0.0-1.0)"""
        self.metrics[f"accuracy_{language}"] = accuracy

    def report_evidence_coverage(self, language: str,
                                verified_valid: int, verified_total: int,
                                inferred_marked: int, inferred_total: int):
        """Evidence traceability metrics"""
        self.metrics[f"verified_coverage_{language}"] = verified_valid / verified_total if verified_total > 0 else 1.0
        self.metrics[f"inferred_marked_{language}"] = inferred_marked / inferred_total if inferred_total > 0 else 1.0

    def report_performance(self, language: str,
                          interpretation_time: float,
                          document_time: float):
        """Performance metrics"""
        self.metrics[f"interpretation_time_{language}"] = interpretation_time
        self.metrics[f"document_time_{language}"] = document_time

    def to_report(self) -> str:
        """Generate human-readable report."""
        report = []
        report.append("DOC-002 Quality Metrics Report")
        report.append("=" * 50)

        for key, value in sorted(self.metrics.items()):
            if isinstance(value, float):
                report.append(f"{key}: {value:.2%}" if key.endswith("_coverage") or key.endswith("_marked") else f"{key}: {value:.2f}s")
            else:
                report.append(f"{key}: {value}")

        return "\n".join(report)
```

**Tests:**
- Metrics collection and reporting work correctly
- Report format is clear and parseable

---

### 5c-3: User Documentation and Examples (2-3 days)

**Goal:** Create comprehensive user guide for DOC-002 feature.

**Deliverables:**
- `tools/codeflow/docs/DOC-002-user-guide.md`
  - What is DOC-002
  - How to generate semantic documentation
  - Understanding the output documents
  - Configuring LLM provider
  - Interpreting evidence references
  - Performance and cost considerations
  - Troubleshooting common issues

- `tools/codeflow/docs/examples/DOC-002-tic-tac-toe-example.md`
  - Walk-through of Tic-Tac-Toe analysis
  - Example Functional_Description.docx (PDF preview)
  - Example Technical_Description.docx (PDF preview)
  - Comparison with HTML flowchart
  - How to interpret the documents

- Configuration examples:
  - Using Claude API
  - Using GPT-4
  - Using local LLM
  - Using mock provider (testing)

**Tests:**
- Documentation completeness (all features documented)
- Example outputs generated and valid
- Instructions follow DOC-002 requirements

**Acceptance:**
- User can follow guide to generate documentation
- Guide explains all features
- Examples are helpful and clear

---

### 5c-4: Performance Optimization (1-2 days)

**Goal:** Optimize semantic interpretation and document generation for speed.

**Analysis & Optimizations:**
- Profile interpretation time (identify bottlenecks)
- Optimize LLM prompt generation (reduce tokens)
- Cache semantic interpretations
- Parallel document generation
- Optimize JSON/SVG linking

**Tests:**
- Performance benchmarks before/after optimization
- Verify ≤15 second total time

---

### 5c-5: Documentation Completion (1-2 days)

**Goal:** Complete all OpenSpec documentation for DOC-002.

**Deliverables:**
- Final review and polish of:
  - proposal.md
  - requirements.md (DOC-002-requirements.md)
  - design.md (DOC-002-architecture.md)
  - Implementation specs (Phase 5a/5b/5c)
  - User guide
  - API reference

**Acceptance:**
- All OpenSpec documents complete and consistent
- No internal contradictions
- Sufficient detail for implementation
- Clear acceptance criteria

---

## Phase 5c Success Checklist

- [ ] All 7 acceptance tests implemented and passing
- [ ] Quality metrics collection and reporting working
- [ ] Cross-language testing completed (Python, Rust, PHP)
- [ ] Performance benchmarks meet targets
- [ ] No regressions in existing CodeFlow functionality
- [ ] User documentation complete and clear
- [ ] Example outputs generated and reviewed
- [ ] Performance optimization completed
- [ ] All OpenSpec documents finalized
- [ ] Ready for Phase 5 completion and release

---

## Estimated Timeline

- Task 5c-1: Acceptance test suite — 3-4 days
- Task 5c-2: Quality metrics — 2-3 days
- Task 5c-3: User documentation — 2-3 days
- Task 5c-4: Performance optimization — 1-2 days
- Task 5c-5: Documentation completion — 1-2 days
- **Total: 1-2 weeks**

---

## Success Metrics Summary

| Metric | Target | Verification |
|--------|--------|--------------|
| Non-technical comprehension | ≥80% clear | AT-1 test |
| Technical accuracy | ≥95% | AT-2 test |
| Evidence traceability | 100% verified, ≥95% inferred marked | AT-3 test |
| Template repetition | ≤2 per 10 pages | AT-4 test |
| Behavioral accuracy | ≥95% | AT-5 test |
| Cross-language consistency | ±10% variance | AT-6 test |
| Semantic interpretation time | <5 seconds (mock) | AT-7 test |
| Document generation time | <10 seconds | AT-7 test |
| Total pipeline time | <15 seconds | Performance benchmark |
| Regression tests | 100% passing | test_acceptance_doc002.py |

---

## Post-Phase 5c

After successful completion of Phase 5c:

1. **Archive DOC-002 Change**
   - Run `openspec archive codeflow-semantic-documentation`
   - Commit all implementation code
   - Update CHANGELOG
   - Tag release version

2. **Begin Phase 6 (if planned)**
   - LLM-assisted requirement traceability
   - Automated testing recommendations
   - Other enhancements

3. **User Adoption**
   - Publish release notes
   - Present DOC-002 capabilities
   - Gather feedback for future improvements
