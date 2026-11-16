# Design: CodeFlow Multilanguage Support

## Context

CodeFlow 0.2 accepts two first-class input types:
1. **Markdown specifications** (.md, typically SPEC.md) – represents intended behavior via flowchart notation
2. **Python source code** (.py) – analyzes actual implementation control flow

Current architecture tightly couples Python AST analysis logic within `report_generator.py` and `cli.py`. Rendering components (SVG layout, HTML generation) are language-agnostic and reusable; only the parsing step is language-specific.

Current structure:
- `codeflow/cli.py`: Routes based on file extension (.py → Python analysis, .md → Markdown specification parsing)
- `codeflow/report_generator.py`: Hardcoded `analyze_python_file()` call for .py files
- `codeflow/graph.py`: CFG representation (language-agnostic)
- `codeflow/render/`, `codeflow/layout/`: Rendering and layout (language-agnostic)
- `codeflow/analyzers/python_analyzer.py`: Python-specific AST walking
- `codeflow/specification.py`: Markdown specification handling

**Regression Baseline**: 41 Python and SPEC.md regression tests across 5+ test files; all must pass unchanged (primary validation gate for backward compatibility).

## Goals / Non-Goals

**Goals:**
- Add Rust (.rs) and PHP (.php) as third and fourth first-class input types equal to SPEC.md and Python
- Each input type (SPEC.md, Python, Rust, PHP) produces:
  - Native CodeFlow SVG/HTML flowchart using existing rendering conventions
  - Optional human-readable document (Markdown or Word, where dependencies permit)
- Introduce a pluggable analyzer architecture enabling new language support without core CLI/ReportGenerator changes
- Support Rust-specific constructs: if/else, match expressions with patterns/guards, loops, error propagation (?), function boundaries
- Support PHP-specific constructs: functions, classes, methods, namespaces, if/else, switch/match, loops, exceptions, calls; multi-file projects via include/require and Composer
- Support project-level analysis for Python, Rust, and PHP with entry-point discovery and cross-file relationships
- Preserve Python and SPEC.md analysis behavior exactly; all 41 regression tests pass unchanged
- Unified optional documentation generation (Markdown/Word) for SPEC.md, Python, Rust, and PHP
- Source traceability: preserve specification IDs, Python/Rust/PHP file/line references
- Support optional comparison/traceability as a review aid (not equivalence proof)
- Maintain CLI backward compatibility; existing commands work unchanged
- Clearly distinguish specification intent, implementation behavior, unverified assumptions, and dynamic/uncertain behavior
- Document all new dependencies (tree-sitter with Rust and PHP grammars, python-docx) and how they will be included in the Software Factory container

**Non-Goals:**
- Async/await analysis beyond basic structural representation (Rust) or beyond basic detection (PHP)
- Macro expansion or procedural macro analysis (Rust)
- Complex generic constraint resolution (Rust)
- Closure capture analysis beyond basic detection (Rust)
- Full Rust edition support details (focus on common patterns)
- Dynamic code execution analysis or full reflection resolution (PHP)
- Framework-specific routing or dispatcher resolution (PHP)
- Behavioral equivalence proof between specification and implementation
- Performance profiling or optimization suggestions
- IDE integration or real-time/incremental analysis
- Modify Software Factory core or rebuild container during planning
- Support for all PHP versions; focus on PHP 7.4+ (current LTS)

## Decisions

### D1: Pluggable Analyzer Architecture via Analyzer Protocol/ABC

**Decision:** Define an `Analyzer` abstract base class (or protocol for type-checking) with a standard interface. Language-specific analyzers (Python, Rust, Markdown) implement this interface and register themselves by file extension.

**Rationale:**
- Separates language-specific parsing from the generic report generation pipeline
- Allows new languages to be added without touching `cli.py` or `report_generator.py`
- Maintains backward compatibility; Python analyzer is refactored into the new structure but behavior is identical
- Reduces code duplication if future languages need similar CFG construction

**Alternatives Considered:**
- A1a: Single large conditional in `ReportGenerator.generate_report()` checking file extension and calling language-specific functions. *Rejected*: Violates separation of concerns; scales poorly; every new language requires core changes.
- A1b: Factory method pattern without a common base class. *Rejected*: Less type-safe; harder to ensure interface compliance.

**Implementation Detail:** The Analyzer interface includes:
```
class Analyzer(ABC):
    @abstractmethod
    def analyze(self, source_path: str) -> AnalysisResult:
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        # e.g., [".rs"] for Rust
        pass
    
    @property
    def name(self) -> str:
        pass
    
    @property
    def version(self) -> str:
        pass
```

Analyzers register in a module-level registry; CLI and ReportGenerator query the registry by extension.

---

### D2: Rust Parser Strategy - Tree-Sitter with Rust Grammar

**Decision:** Use the **tree-sitter** Python bindings with **tree-sitter-rust** grammar for structured Rust parsing. Pin specific versions of tree-sitter and tree-sitter-rust in the dependency manifest.

**Rationale:**
- Tree-sitter is a robust, battle-tested parser generator used by GitHub and other major projects
- tree-sitter-rust grammar handles the full Rust language specification
- Python bindings provide clean interface without C compilation overhead at runtime (grammar is pre-compiled)
- Graceful error recovery and partial parsing support unsupported constructs without halting analysis
- Documented dependency management enables reproducible container builds
- Avoids regex-based or ad hoc parsing which is fragile and unmaintainable for complex syntax

**Alternatives Considered:**
- A2a: Manual recursive descent parser for common Rust constructs. *Rejected*: Fragile; cannot reliably handle nested structures, pattern matching, or edge cases. High maintenance burden for Rust grammar updates.
- A2b: Shell out to `rustc --pretty expanded`. *Rejected*: Requires Rust toolchain on every system; external dependency; slow and unreliable.
- A2c: Regex-based tokenization. *Rejected*: Error-prone for nested constructs; cannot correctly parse match guards, closures, generics.

**Implementation Detail:**
- Add tree-sitter (pinned version) and tree-sitter-rust (pinned version) to requirements.txt or pyproject.toml
- Create `RustAnalyzer` class inheriting from `Analyzer` ABC
- Use tree-sitter Python API to parse .rs files into syntax trees
- Walk syntax tree to extract function definitions, control flow structures (if/else, match, loops)
- Generate CFG nodes and edges using the same logic as PythonAnalyzer
- Unsupported constructs (macros, closures with captures, complex async, complex generics) are marked with degradation flags; analysis continues with warnings
- Document in README.md how to verify tree-sitter installation and Rust grammar availability

---

### D3: Preserve Existing SVG/HTML Rendering Conventions & Mermaid Support

**Decision:** Extend existing SVG renderer and HTML generator to handle CFGs from any language without modification. Use consistent node colors, shapes, connector styles, and layout algorithms regardless of source language. 

Preserve existing CodeFlow support for importing embedded Mermaid flowcharts from SPEC.md files: convert imported Mermaid diagrams to native CodeFlow SVG format, and report unsupported Mermaid syntax. Do not introduce alternate rendering engines or Mermaid as primary output format.

**Rationale:**
- CodeFlow's rendering logic is already language-agnostic; operates on CFG nodes and edges
- Consistency across languages (SPEC.md, Python, Rust) reduces cognitive load when comparing implementations
- Preserves user investment in existing CodeFlow SVG/HTML output format and visual conventions
- Existing Mermaid import capability (in SPEC.md analyzer) is valuable; must continue working
- No need to fork rendering code or introduce Mermaid as primary format

**Alternatives Considered:**
- A3a: Language-specific rendering (Rust nodes colored/styled differently). *Rejected*: Defeats comparison purpose; adds visual complexity without benefit.
- A3b: Mermaid rendering as primary output for Rust. *Rejected*: Not CodeFlow's native format; changes established visual conventions; loses layout/styling control; breaks backward compatibility.

**Implementation Detail:** Add optional metadata to AnalysisResult indicating source language and file path. HTMLReportGenerator uses this to:
- Label report header ("Analyzed from: python/tictactoe.py", "Analyzed from: Rust (tictactoe.rs)")
- Include file path and line number metadata in HTML comments/headers
- Apply consistent SVG node shapes and connector styles regardless of language
- Continue importing Mermaid diagrams from SPEC.md (existing SpecificationAnalyzer behavior)

---

### D4: Unified Documentation Generation (SPEC.md, Python, Rust) - Mandatory Capability

**Decision:** Create unified `DocumentationGenerator` supporting Markdown and Word output for specifications, Python implementations, and Rust implementations. Reuse existing Claude Code integration where available; provide distinct, clearly-labeled fallback statistics-based output when Claude Code is unavailable. **Documentation generation is a mandatory CodeFlow 0.3 capability; users may choose whether to invoke it (via `--prose` flag), but the capability must be available.**

**Rationale:**
- Python and Rust documentation can follow the same format as existing SPEC.md prose
- Single documentation pipeline for all three input types (SPEC.md, Python, Rust) reduces duplication
- Markdown is universally available; Word output is optional (requires python-docx, detected at import time)
- Claude Code integration provides flexible, maintainable prose generation
- Documentation is a valued capability; should be part of the release, not deferred as optional
- Optional invocation (via flag) respects user workflows; capability availability ensures all users can access it

**Alternatives Considered:**
- A4a: Implement rule-based documentation generator in Python. *Rejected*: Hard-coded linguistic patterns; unmaintainable; less flexible than Claude Code.
- A4b: Skip documentation generation entirely. *Rejected*: Proposal and stakeholders request this feature; important for CodeFlow 0.3 completeness.
- A4c: Make documentation optional; not part of release. *Rejected*: Reduces capability; users cannot rely on it; splits implementation effort.
- A4d: Require Claude Code for all prose (no fallback). *Rejected*: Reduces accessibility; fails gracefully if Claude Code unavailable.

**Implementation Detail:**
- When analyzing any input type (SPEC.md, Python, Rust) with `--prose` flag: Generate human-readable narrative
  - **Full Narrative Path**: If Claude Code available, send CFG + source context to Claude Code for fluent prose generation; label output as "AI-Generated Narrative"
  - **Statistics Fallback Path**: If Claude Code unavailable, generate structured summary of control flow (node counts, branch counts, loop counts, error paths); label clearly as "Statistics-Based Summary (Full AI Generation Unavailable)" with reason
- Never silently substitute fallback for full narrative; always explicitly label output with generation method
- Markdown output: Always available
- Word output (via python-docx): Check availability at import time; if unavailable, inform user that Word output requires `python-docx` and either suggest installation or skip to Markdown-only
- Output file naming conventions: `{filename}_Narrative.md`, `{filename}_Narrative.docx` (Markdown/Word based on invocation)

---

### D5: Source Traceability - Preserve Requirement IDs and Line References

**Decision:** Maintain source traceability throughout analysis and reporting:
- Specification IDs (section refs, requirement identifiers from SPEC.md)
- Python/Rust file paths and line numbers
- Function/block boundaries
- Exported in HTML metadata and JSON reports

**Rationale:**
- Enables review and verification of code-to-spec alignment
- Supports manual inspection and debugging of CFG generation
- Necessary for cross-language comparison heuristics
- Aligns with software engineering practices for requirements traceability

**Implementation Detail:**
- `AnalysisResult` includes optional `source_references` field mapping CFG node IDs to (file_path, line_no) tuples
- `Specification.parse_markdown()` extracts requirement IDs from SPEC.md headers (e.g., `## Requirement: validate_move`)
- HTML report includes file path and line number in node tooltips/metadata
- JSON export includes full source reference mapping

---

### D6: Comparison as Review Aid, Not Equivalence Proof

**Decision:** Support optional comparison mode that shows side-by-side flowcharts from specification, Python, and Rust implementations. Node alignment uses heuristic graph matching with evidence-based categories. Comparison is a review aid and traceability tool; it does NOT claim behavioral equivalence or verify implementation correctness.

**Comparison Alignment Categories** (evidence-based, explicitly labeled):
- **"Matched"**: Strong structural correspondence (same branching pattern, matching decision labels, same node sequence). Requires manual review to confirm semantic equivalence.
- **"Partially Matched"**: Moderate structural correspondence (similar branching, some label differences, Rust idioms differ from Python). Requires manual review to determine semantic relationship.
- **"Unmatched"**: No clear structural correspondence (divergent paths, different control flow). Requires manual review to explain difference or identify missing/extra implementation.
- **"Requires Review"**: Parsing ambiguity, unsupported constructs (macros, async/await, closures), or incomplete analysis detected. Cannot determine alignment without manual code inspection.

Never claim:
- "Implementations are verified to be equivalent" (matching structure does NOT prove behavioral equivalence)
- "All specification paths are covered by both implementations" (unsupported constructs hide coverage; heuristic matching cannot guarantee completeness)
- "Behavioral equivalence confirmed" (matching graph structure ≠ identical runtime behavior, error handling, performance, etc.)
- "Structural matching proves implementation correctness" (syntactic alignment ≠ functional correctness)

Always acknowledge:
- Heuristic matching can have false positives (structurally similar but semantically different nodes)
- Heuristic matching can have false negatives (semantically equivalent but structurally different Rust vs Python idioms)
- Unsupported constructs (Rust macros, closures, async/await) create blind spots in comparison
- Different implementations may have equivalent behavior despite divergent structure
- Functional correctness requires manual code review, testing, and execution validation—not graph comparison

**Rationale:**
- Automatic equivalence proof is undecidable; heuristic matching produces false positives/negatives
- Review and manual verification remain necessary
- Stakeholder expectation: "Show me what's implemented and what's missing" (not "Prove these are equal")
- Supports iterative development: implementer can see spec → impl gaps and refine
- Evidence-based categories set appropriate expectations without false confidence

**Alternatives Considered:**
- A6a: Automatic three-way merge or equivalence proof. *Rejected*: Computationally intractable; false positives mislead users.
- A6b: Percentage-based "confidence scores" (e.g., 85% match). *Rejected*: Implies false precision; heuristics cannot quantify behavioral equivalence.
- A6c: No comparison feature. *Rejected*: Reduces value for users comparing implementations.

**Implementation Detail:**
- New `ComparisonReport` tracks node alignment using heuristics (label similarity, structure matching)
- Every matched node includes explicit category: "Matched", "Partially Matched", "Unmatched", "Requires Review"
- Includes coverage/divergence metrics with caveats: "X% of spec nodes have aligned implementations (manual review essential to confirm semantic equivalence)"
- Divergence summary explains unmatched or partially matched nodes
- Includes explicit disclaimer: "Comparison is a review aid for identifying implementation gaps. Manual verification required for functional correctness. Structural matching does not prove behavioral equivalence."
- README and comparison report output document limitations and methodology clearly

---

### D7: Backward Compatibility - Preserve All 32 Python Tests

**Decision:** Keep all 32 existing Python regression tests exactly as-is (same assertions, same fixtures, same behavior). Refactor Python analyzer into `Analyzer` ABC without changing analysis logic.

**Rationale:**
- Ensures no regression in Python analysis
- Validates that refactoring preserves behavior
- Primary gate for accepting implementation: all 32 tests must pass
- Maintains user trust and stability

**Alternatives Considered:**
- A7a: Migrate all tests to a new unified test framework. *Rejected*: Risk of invalidating existing tests; unnecessary churn.

**Implementation Detail:**
- Move existing `analyze_python_file()` logic into `PythonAnalyzer` class (implements `Analyzer`)
- Register `PythonAnalyzer` for `.py` extension in analyzer registry
- CLI and ReportGenerator route .py files via registry (no logic change)
- Run full test suite before declaring Phase 1 complete; all 32 tests must pass unchanged

---

### D8: Dependencies and Container Integration

**Decision:** Document and pin all new dependencies in requirements.txt or pyproject.toml:
- **tree-sitter** (core requirement for Rust parsing)
- **tree-sitter-rust** (Rust grammar)
- **python-docx** (optional for Word output; imported with try/except)

Verify installation during CodeFlow startup. Update Dockerfile to include tree-sitter if needed.

**Rationale:**
- Reproducible builds across development, CI, and production
- Container can verify all dependencies at startup
- python-docx is optional; CodeFlow works without it (Word output unavailable)
- Clear documentation for users setting up CodeFlow in their environment

**Alternatives Considered:**
- A8a: No dependency documentation. *Rejected*: Causes reproducibility and deployment problems.
- A8b: Require all optional dependencies. *Rejected*: Reduces accessibility and adds bloat.

**Implementation Detail:**
- `requirements.txt`: tree-sitter==0.26.1, tree-sitter-rust==0.24.2 (compatible stable versions), python-docx>=0.8.10 (optional)
- **Tree-Sitter Initialization** (current Python API):
  ```python
  from tree_sitter import Language, Parser
  
  # Load Rust grammar
  RUST_LANGUAGE = Language('/path/to/tree-sitter-rust/build/languages.so', 'rust')
  # Or use pre-compiled wheels: tree-sitter.queries.RUST_LANGUAGE
  parser = Parser()
  parser.set_language(RUST_LANGUAGE)
  tree = parser.parse(source_code_bytes)
  ```
- README.md: Dependencies section lists required (tree-sitter>=0.26.1, tree-sitter-rust>=0.24.2) and optional (python-docx)
- `codeflow/cli.py`: On startup, check tree-sitter availability and fail with helpful message if missing
- Dockerfile (if container rebuild needed): Includes tree-sitter system dependencies and Python packages
- `tests/test_multilanguage_integration.py` (new): ~15 test cases for CLI routing, ReportGenerator dispatch
- `tests/test_comparison.py` (new, optional): ~10 test cases for comparison mode

---

### D9: Rust Example Project - TicTacToe Equivalent

**Decision:** Create a `examples/rust/` directory with a Rust implementation of a simple game (TicTacToe or similar), mirroring the existing `examples/python/SPEC.md` and `examples/python/tictactoe.py`. Ensure both Python and Rust examples reference a single authoritative SPEC.md (in examples/python/) unless implementation differences are intentionally documented.

**Rationale:**
- Provides concrete example for users
- Enables end-to-end testing (spec → Python → Rust comparison)
- Demonstrates multilanguage capabilities

**Alternatives Considered:**
- A8a: No Rust example. *Rejected*: Users have no concrete reference; harder to understand Rust support.

**Implementation Detail:**
- `examples/rust/tictactoe.rs`: Rust implementation of TicTacToe
- `examples/rust/SPEC.md`: Specification (reuse or adapt from Python)
- Runnable example in README.md: `codeflow examples/rust/tictactoe.rs --open`

---

## Risks & Mitigations

### [Risk 1] Tree-Sitter Deployment and Installation Complexity
**Risk:** tree-sitter Python bindings require C compilation or pre-compiled wheels. Installation may fail on some systems. Rust grammar updates require managing versions.

**Mitigation:**
- Pin tree-sitter and tree-sitter-rust versions in requirements.txt for reproducibility
- Document installation process in README.md with troubleshooting guide
- Update Software Factory Dockerfile (or document how to do so) to include tree-sitter system dependencies
- Test installation in CI pipeline; fail early if tree-sitter is unavailable
- Provide clear error message during CodeFlow startup if tree-sitter is missing

### [Risk 2] Tree-Sitter May Not Perfectly Parse All Rust Constructs
**Risk:** Despite tree-sitter's robustness, some advanced Rust features (unsafe blocks, complex macros, procedural macro invocations) may not parse correctly or may be incompletely represented in the syntax tree.

**Mitigation:**
- Design Rust analyzer to gracefully degrade: unsupported constructs are logged as warnings, not hard errors
- Focus on common patterns (if/else, match, for/while, error propagation with ?) covering 80% of real-world Rust code
- Provide clear documentation of supported constructs and limitations in README.md with examples
- Add degradation flags to AnalysisResult so users see when significant portions are unparseable
- Extensive Rust parsing tests to catch edge cases early

### [Risk 3] Comparison Heuristics May Produce False Positives/Negatives
**Risk:** Automatic node matching between specification and implementations relies on structural and label similarity; two logically equivalent but differently-named nodes may fail to match, or unrelated nodes may match.

**Mitigation:**
- Keep comparison as optional MVP feature; users can review mismatches manually
- Provide manual override/linking capability in comparison report
- Include confidence/uncertainty flags on each match ("Certain" vs "Likely" vs "Unclear")
- Document clearly that comparison is a review and traceability aid, not proof of behavioral equivalence
- Extensive testing of comparison heuristics with intentional divergences

### [Risk 4] Documentation Generation Requires Claude Code
**Risk:** Optional documentation generation (`--prose` flag) depends on Claude Code availability. Without Claude Code, feature degrades or fails.

**Mitigation:**
- Make documentation feature optional; `--prose` flag is not required
- Graceful fallback: generate statistics-based summary (CFG node counts, path analysis) if Claude Code is unavailable
- Check Claude Code availability at startup; warn if unavailable
- Document that prose generation improves with Claude Code integration but is not required

### [Risk 5] Python-docx Dependency for Word Output
**Risk:** Word (.docx) output requires python-docx library, which may not be installed or available in all environments.

**Mitigation:**
- python-docx is optional dependency; imported with try/except
- If unavailable, Markdown output still works (no functional regression)
- Check availability at import time; warn users if Word output unavailable
- Document that Word output requires python-docx; provide installation instructions
- Provide clear error message guiding users to install python-docx if they request Word output

### [Risk 6] Specification Intent vs Implementation Behavior Ambiguity
**Risk:** Specifications (SPEC.md) may be ambiguous or incomplete. Implementations may deviate intentionally or unintentionally. Comparison may not catch these subtle differences.

**Mitigation:**
- Clearly document and flag ambiguous specifications in SPEC.md analysis
- Distinguish in reports between "specification intent" and "implementation behavior"
- Comparison mode reports divergence metrics; human review required for correctness
- Source traceability (line numbers, requirement IDs) helps manual verification
- Document that comparison is a review aid, not a correctness proof

### [Risk 7] Test Coverage for Rust and Multilanguage Scenarios
**Risk:** Adding Rust support and refactoring Python analyzer may introduce regressions. New test coverage must be comprehensive to catch edge cases.

**Mitigation:**
- Preserve all 32 existing Python tests as primary regression gate
- Add 25-30 Rust parsing tests covering common and edge case patterns
- Add 10-15 multilanguage integration tests for CLI routing and analyzer dispatch
- Add 10-15 tests for SPEC.md specification rendering (preserve existing spec workflow)
- Add tests for narrative generation (when dependencies available)
- Add 5-10 tests for comparison mode
- Total: 82+ tests ensuring correctness across all languages
- Require all tests to pass before merging implementation

### [Risk 5] Comparison Mode Adds Complexity
**Risk:** Cross-language comparison introduces additional code paths, potential bugs, and user confusion (new flag, new output format).

**Mitigation:**
- Implement comparison as optional MVP; can be deferred if complexity becomes unmanageable
- Keep default behavior (single-file analysis) unchanged
- Use `openspec compare` as a separate command, not a built-in option, to reduce CLI clutter

---

## Implementation Phases

### Phase 1: Infrastructure & Backward Compatibility (Weeks 1-2)
**Goal:** Establish analyzer architecture and confirm all 32 Python tests pass.

1. Define `Analyzer` abstract base class in new module `codeflow/analyzers/base.py`
   - `analyze(source_path: str) -> AnalysisResult` method
   - Optional `source_references` field for traceability
2. Refactor existing Python analyzer into `PythonAnalyzer` class (implements `Analyzer`)
   - Move `analyze_python_file()` logic into `PythonAnalyzer.analyze()`
   - Preserve all existing behavior exactly
3. Create analyzer registry in `codeflow/analyzers/__init__.py`
4. Update `report_generator.py` to route via analyzer registry (not hardcoded Python call)
5. Update `cli.py` to route by file extension using registry
6. Add tree-sitter and tree-sitter-rust to requirements.txt with pinned versions
7. Run existing test suite; **all 32 Python tests must pass**
8. Add ~5 integration tests verifying analyzer routing works

**Gate:** All 32 Python tests pass; no regression in Python analysis behavior.

### Phase 2: Rust Parser & Tests (Weeks 3-4)
**Goal:** Implement structured Rust parsing using tree-sitter and validate with tests.

1. Implement `RustAnalyzer` in `codeflow/analyzers/rust_analyzer.py`
   - Use tree-sitter Python bindings to parse Rust source
   - Extract function definitions, control flow (if/else, match, loops)
   - Generate CFG nodes and edges using same logic as Python analyzer
   - Detect and report unsupported constructs with degradation flags
   - Populate source_references with file paths and line numbers
2. Register `RustAnalyzer` for `.rs` extension
3. Add ~25-30 Rust parsing tests in `tests/test_rust_parsing.py`
   - Simple functions, match expressions, nested loops, error propagation
   - Unsupported constructs (macros, closures, complex generics, async/await)
4. Create `examples/rust/tictactoe.rs` with equivalent logic to `examples/python/tictactoe.py`
5. Add Rust-specific documentation in README.md (supported constructs, limitations, examples)

**Gate:** All 32 Python tests still pass; 25+ Rust tests pass.

### Phase 3: Multilanguage Rendering & Integration (Weeks 5-6)
**Goal:** Verify SVG/HTML rendering works for all input types and integrate CLI workflows.

1. Verify existing SVG renderer and HTML generator handle Rust CFGs identically to Python CFGs
2. Add optional language metadata to `AnalysisResult` (source language, file path)
3. Update `HTMLReportGenerator` to include language/file metadata in report headers
4. Add ~10-15 integration tests in `tests/test_multilanguage_integration.py`
   - CLI routing for .py, .rs, .md files
   - SVG/HTML output format consistency across languages
5. Add regression tests for SPEC.md (.md) file rendering (ensure existing spec workflow unchanged)
6. Update README.md with:
   - Rust examples: `codeflow examples/rust/tictactoe.rs --open`
   - Supported Rust constructs and limitations
   - Tree-sitter dependency documentation and installation guide
   - Troubleshooting for tree-sitter installation issues
7. Update CLI help text to document .rs support

**Gate:** All 32 Python tests + 25 Rust tests pass; integration tests pass.

### Phase 4: Source Traceability & SPEC.md Enhancement (Weeks 7-8)
**Goal:** Add optional documentation and traceability across all input types.

1. Enhance `AnalysisResult` to track source references:
   - Specification requirement IDs (from SPEC.md headers)
   - Python/Rust source file paths and line numbers
2. Implement unified `DocumentationGenerator` for Markdown and Word output
   - Reuse existing Claude Code integration where available
   - Support all three input types (SPEC.md, Python, Rust)
   - Fallback to statistics-based summary if Claude Code unavailable
3. Add `--prose` flag to CLI (optional, defaults to no prose)
4. Update `HTMLReportGenerator` to include source references in metadata
5. Add ~10-15 tests for narrative generation (Markdown and Word when available)
6. Test with `examples/python/SPEC.md`, `examples/python/tictactoe.py`, `examples/rust/tictactoe.rs`

**Gate:** All previous tests pass; narrative tests pass; python-docx optional dependency handled gracefully.

### Phase 5: Comparison & Traceability (Weeks 9-10) [Optional MVP]
**Goal:** Optional comparison mode for review and verification.

1. Implement `ComparisonReport` class tracking node alignment
   - Structural matching heuristics (label similarity, control flow pattern matching)
   - Confidence/uncertainty flags per match
   - Coverage metrics (% of spec paths with Python/Rust implementation)
2. Add `compare` CLI command: `codeflow compare SPEC.md tictactoe.py tictactoe.rs`
3. Generate merged HTML report with:
   - Side-by-side or tabbed flowcharts
   - Alignment highlights and uncertainty flags
   - Divergence summary (paths present in spec but missing in impl; vice versa)
   - Source traceability (file/line numbers)
4. Add ~5-10 tests for comparison mode in `tests/test_comparison.py`
5. Document comparison mode limitations in README.md

**Gate:** All previous tests pass; comparison tests pass; limitations clearly documented.

### Rollback Strategy
- If tree-sitter installation proves problematic, document manual installation workaround and provide detailed troubleshooting guide
- If Rust parser encounters insurmountable edge cases with tree-sitter, fallback: implement degraded analyzer producing minimal CFG (entry, exit, middle nodes as opaque blocks) with high-confidence warnings
- If documentation generation adds too much complexity, defer Phase 4 to post-MVP and ship Rust support without prose
- If comparison mode causes regression, disable via CLI flag without affecting core single-file workflows
- All changes are additive to Python workflow; Python analysis remains independent and can roll back independently

1. **Rust Macro Handling**: Should we attempt to parse `println!`, `vec!`, etc., or treat all macros as opaque statements? *Deferrable*: Spec says unsupported; implementation can handle this iteratively.

2. **Async/Await Representation**: How should `async fn` and `.await` be represented? As regular functions, or with special async markers? *Deferrable*: Spec says basic structural representation; full async semantics is out of scope.

3. **Documentation Generation Locale**: Should prose be generated only in English, or should Claude Code support other languages? *Deferrable*: English is default; additional languages can be added via new `--language` flag post-launch.

4. **Comparison Three-Way Merging**: Should the comparison report show a three-way merge visualization (like git), or separate pairwise comparisons? *Deferrable*: Pairwise is simpler for MVP; three-way merge can be added later.

5. **Performance Benchmarking**: What is the acceptable overhead for Rust parsing? Should we set a hard latency SLA (e.g., < 500ms for typical file)? *Deferrable*: Measure first; adjust if needed.

---

## Key Assumptions

- All tests run under Python 3.11+
- Users have Rust knowledge to interpret Rust flowcharts (or read Rust documentation)
- Claude Code availability for documentation is optional, not required
- Comparison feature is "nice to have," not critical for launch
- Rust code in examples is well-formed; error recovery for malformed Rust is best-effort
