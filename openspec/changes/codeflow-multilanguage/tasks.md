# Implementation Tasks: CodeFlow Multilanguage Support

## Regression Test Baseline

**Verified Test Count**: 32 existing Python tests across 5 test files:
- `test_exit_connections.py`: 6 tests
- `test_graph.py`: 7 tests
- `test_integration.py`: 11 tests
- `test_layout_exit_convention.py`: 5 tests
- `test_layout_overlaps.py`: 4 tests

**Total Baseline**: 32 tests (all must pass unchanged as primary regression gate)

**Canonical Test Command** (always use this full list, never wildcards):
```bash
python -m pytest tests/test_exit_connections.py tests/test_graph.py tests/test_integration.py tests/test_layout_exit_convention.py tests/test_layout_overlaps.py -v
```

---

## Phase 1: Infrastructure & Backward Compatibility (Weeks 1-2)

### Group 1.1: Analyzer Architecture
- [ ] 1.1.1 Create `codeflow/analyzers/base.py` with `Analyzer` ABC class
  - Define `analyze(source_path: str) -> AnalysisResult` abstract method
  - Define `supported_extensions` property (returns list of extensions like [".py"])
  - Define `name` and `version` properties
  - Verify by importing and confirming class is abstract (instantiation fails)
  
- [ ] 1.1.2 Create `codeflow/analyzers/__init__.py` with analyzer registry
  - Implement registry dict mapping file extensions → Analyzer instances
  - Implement `register_analyzer(analyzer: Analyzer)` function
  - Implement `get_analyzer(extension: str) -> Optional[Analyzer]` function
  - Verify with unit tests: register and retrieve a mock analyzer

- [ ] 1.1.3 Add `source_references` and `ambiguity_flags` to `AnalysisResult`
  - Field: `source_references: Dict[str, Tuple[str, int]]` (CFG node ID → (file_path, line_no))
  - Field: `ambiguity_flags: List[str]` (for flagging uncertain specifications or unsupported constructs)
  - Field: `analysis_incomplete: bool` (set True if unsupported constructs prevented complete analysis)
  - Verify by checking AnalysisResult can accept these fields without breaking existing code

### Group 1.2: Python Analyzer Refactoring
- [ ] 1.2.1 Refactor `codeflow/analyzers/python_analyzer.py` to inherit from `Analyzer` ABC
  - Wrap existing `analyze_python_file()` logic into `PythonAnalyzer.analyze()` method
  - Implement `supported_extensions` property returning [".py"]
  - Keep all existing parsing logic unchanged
  - Verify by running the full existing test suite: **all 33 tests must pass**

- [ ] 1.2.2 Register `PythonAnalyzer` in the analyzer registry
  - In `__init__.py`, import PythonAnalyzer and call `register_analyzer(PythonAnalyzer())`
  - Verify registry lookup works: `get_analyzer(".py")` returns PythonAnalyzer instance

### Group 1.3: Core Refactoring
- [ ] 1.3.1 Update `codeflow/report_generator.py` to use analyzer registry
  - Replace hardcoded `analyze_python_file()` call with registry lookup
  - Call `get_analyzer(file_extension).analyze(source_path)`
  - Keep all other report generation logic unchanged
  - Verify: run full baseline test suite, all 33 tests must pass

- [ ] 1.3.2 Update `codeflow/cli.py` to route via analyzer registry
  - Replace extension-specific handling with generic registry lookup
  - Extract file extension and call appropriate analyzer
  - Verify: `python -m codeflow examples/python/tictactoe.py` produces identical output to before

### Group 1.4: Dependency Management
- [ ] 1.4.1 Research and pin tree-sitter and tree-sitter-rust versions
  - Determine current stable versions of:
    - `tree-sitter` (Python bindings, minimum version: 0.20.0)
    - `tree-sitter-rust` (Rust grammar, version matching tree-sitter release)
  - Document version compatibility and Python version requirements
  - Create test file to verify Python API initialization matches current documentation

- [ ] 1.4.2 Add tree-sitter dependencies to requirements.txt or pyproject.toml
  - Pin versions: `tree-sitter==X.Y.Z`, `tree-sitter-rust==A.B.C` (use compatible stable versions from research)
  - Mark python-docx as optional: `python-docx>=0.8.10` (already available)
  - Verify file is valid TOML/text syntax

- [ ] 1.4.3 Update README.md with dependency section
  - Document required dependencies (tree-sitter and tree-sitter-rust with specific versions)
  - Document optional dependencies (python-docx for Word output)
  - Include installation instructions and troubleshooting for tree-sitter
  - Verify README is clear and instructions work

### Group 1.5: Verification Gate
- [ ] 1.5.1 Run full existing test suite (canonical baseline command)
  - Confirm all 32 Python regression tests pass (use canonical command above)
  - Document baseline: 33 tests pass, 0 failures, 0 skipped
  - **Gate: Do not proceed to Phase 2 if any Python test fails**

---

## Phase 2: Rust Parser & Tests (Weeks 3-4)

### Group 2.1: Rust Analyzer Foundation with tree-sitter
- [ ] 2.1.1 Create `codeflow/analyzers/rust_analyzer.py` with `RustAnalyzer` class
  - Inherit from `Analyzer` ABC
  - Implement `analyze(source_path: str) -> AnalysisResult` as initial stub
  - Implement `supported_extensions` property returning [".rs"]
  - Verify class structure with unit test: can instantiate and call analyze()

- [ ] 2.1.2 Import tree-sitter and initialize Rust parser using current API
  - `from tree_sitter import Language, Parser`
  - Load Rust language using current tree-sitter-python API (verify against actual package documentation)
  - Create parser instance and store for reuse
  - Test with simple Rust snippet: `fn add(x: i32, y: i32) -> i32 { x + y }`
  - Verify: parser can parse without errors and return tree structure

### Group 2.2: Rust Control Flow Parsing via tree-sitter
- [ ] 2.2.1 Implement function boundary detection
  - Use tree-sitter to find `function_item` nodes
  - Extract function name, parameters, return type from tree
  - Create CFG entry node (function_name entry) and exit node (function_name exit)
  - Verify with test: parse `fn add(x: i32, y: i32) -> i32 { x + y }` → CFG has entry and exit

- [ ] 2.2.2 Implement if/else statement parsing
  - Parse `if_expression` nodes with condition and blocks
  - Create decision node with true/false edges to respective blocks
  - Handle `else if` chains and optional `else` clause
  - Verify with test: `if x > 0 { ... } else if x < 0 { ... } else { ... }` → multi-branch CFG

- [ ] 2.2.3 Implement match expression parsing
  - Parse `match_expression` nodes with arms
  - Each arm becomes a branch; arm pattern is edge label
  - Support simple patterns and guards (`pattern if guard =>`)
  - Create decision node with N edges (one per arm)
  - Verify with test: 4-arm match with one guard → CFG has 4 edges with correct labels

- [ ] 2.2.4 Implement loop parsing (for, while, loop)
  - Parse `for_expression`, `while_expression`, `loop_statement`
  - Create loop-entry node and back-edge to loop continuation
  - Handle `break` as exit edge, `continue` as back-edge
  - Verify with test: for-loop with break condition → CFG has back edge and exit path

- [ ] 2.2.5 Implement error propagation (? operator) parsing
  - Detect `?` suffix on function calls (`result?`)
  - Create exception-path edge to function exit
  - Verify with test: chain like `func()?. method()?` → two exception paths to exit

- [ ] 2.2.6 Implement function call parsing
  - Parse `call_expression` nodes (direct calls and method chains)
  - Create statement/call nodes in CFG
  - Preserve call sequence
  - Verify with test: nested/chained calls → CFG preserves sequence

### Group 2.3: Rust Unsupported Constructs & Warnings
- [ ] 2.3.1 Implement unsupported construct detection with **explicit warnings**
  - Detect macros (`macro_invocation`), async functions, closures, complex generics
  - Treat as opaque statements; continue parsing
  - **Log explicit warning messages** to stderr/logger with:
    - Construct type (e.g., "macro_invocation")
    - Line number (from tree-sitter node position)
    - Description: "Unsupported construct detected; analysis may be incomplete for this section"
  - Store warnings in `ambiguity_flags` list with format: "Line NNN: construct_type (reason)"
  - Set `analysis_incomplete = True` if any unsupported constructs found
  - Verify with test: file with `println!`, `async fn`, `|x| x + 1` → analysis completes with explicit warnings

- [ ] 2.3.2 Populate source_references field with line numbers
  - For each CFG node, track source file path and line number from tree-sitter positions
  - Use tree-sitter node positions (start_point[0] = line number, 0-indexed; convert to 1-indexed)
  - Store in AnalysisResult.source_references dict: node_id → (filepath, line_no_1indexed)
  - Verify: generated CFG nodes include (filepath, line_no) tuples

### Group 2.4: Rust Parser Testing (~30 tests)
- [ ] 2.4.1 Create `tests/test_rust_parsing.py` with ~30 test cases
  - Test each parser component: functions, if/else, match, loops, error propagation, calls
  - Test edge cases: nested structures, empty blocks, single-line statements
  - Test unsupported constructs explicitly:
    - `test_macro_generates_warning()`: Verify macro causes explicit warning in analysis
    - `test_async_fn_generates_warning()`: Verify async/await causes explicit warning
    - `test_analysis_incomplete_flag()`: Verify `analysis_incomplete = True` when unsupported constructs present
  - Verify: all tests pass with `python -m pytest tests/test_rust_parsing.py -v`

- [ ] 2.4.2 Create `tests/fixtures/rust_examples/` directory with fixture files
  - simple_function.rs, if_else.rs, match_expression.rs, nested_loops.rs, error_handling.rs, unsupported.rs
  - Verify files are syntactically valid Rust (parseable by tree-sitter)

### Group 2.5: Rust Example & Documentation
- [ ] 2.5.1 Create `examples/rust/tictactoe.rs`
  - Implement TicTacToe game logic (board state, move validation, win checking)
  - Mirror structure of Python example where practical (use same game logic)
  - Verify file is syntactically valid Rust and contains analyzable functions

- [ ] 2.5.2 Reference single authoritative SPEC.md
  - Use `examples/python/SPEC.md` as the canonical specification
  - Document any intentional differences between Python and Rust implementations
  - Verify SPEC.md describes the game correctly for both implementations

- [ ] 2.5.3 Test Rust example analysis
  - Run: `python -m codeflow examples/rust/tictactoe.rs --output-dir /tmp/test_rust_output`
  - Verify: HTML flowchart is generated without errors
  - Verify: flowchart shows main game functions (check_win, validate_move, etc.)

### Group 2.6: Verification Gate
- [ ] 2.6.1 Run full baseline suite + new Rust tests
  - Run: `python -m pytest tests/test_exit_connections.py tests/test_graph.py tests/test_integration.py tests/test_layout_exit_convention.py tests/test_layout_overlaps.py tests/test_rust_parsing.py -v`
  - Confirm: all 32 Python + 30 Rust = 63+ tests pass
  - **Gate: All tests must pass before proceeding to Phase 3**

---

## Phase 3: Multilanguage Integration & Documentation (Weeks 5-6)

### Group 3.1: Rendering & Metadata
- [ ] 3.1.1 Verify SVG/HTML rendering handles all language CFGs identically
  - Compare Python and Rust flowcharts for equivalent logic
  - Verify layout, colors, shapes, connector styles are identical
  - No Mermaid or alternate rendering; preserve CodeFlow conventions

- [ ] 3.1.2 Update `HTMLReportGenerator` to include language metadata
  - Add source language, file path to report header/metadata
  - Display: "Source: Python (.py) via PythonAnalyzer" or "Source: Rust (.rs) via RustAnalyzer"
  - Verify header shows correct language for .py, .rs, .md inputs

- [ ] 3.1.3 Update `HTMLReportGenerator` to export source references
  - Include file paths and line numbers in HTML metadata or sidebar
  - Display warnings and ambiguity_flags in HTML report (if present)
  - Optional: add tooltips showing source location on hover
  - Verify: HTML output includes source reference information and any warnings

### Group 3.2: SPEC.md Regression Tests (~10-15 tests)
- [ ] 3.2.1 Add regression tests for SPEC.md specification rendering
  - Test: `python -m codeflow examples/python/SPEC.md --no-prose --output-dir /tmp/test_spec`
  - Verify flowchart is generated and matches previous behavior
  - Verify rendering is unchanged from before refactoring
  - Create ~10-15 SPEC.md-specific tests in `tests/test_specification.py`

### Group 3.3: Multilanguage Integration Tests (~10-15 tests)
- [ ] 3.3.1 Create `tests/test_multilanguage_integration.py` with ~10-15 tests
  - Test CLI routing: .py → PythonAnalyzer, .rs → RustAnalyzer, .md → Specification
  - Test ReportGenerator analyzer dispatch
  - Test output directory handling and file naming
  - Test error handling (missing files, invalid syntax)
  - Verify all tests pass

- [ ] 3.3.2 Test each language workflow end-to-end
  - Python: `python -m codeflow examples/python/tictactoe.py --output-dir /tmp/test_py`
  - Rust: `python -m codeflow examples/rust/tictactoe.rs --output-dir /tmp/test_rs`
  - Spec: `python -m codeflow examples/python/SPEC.md --no-prose --output-dir /tmp/test_spec`
  - Verify all produce correct HTML flowcharts without errors

### Group 3.4: Documentation Generator (Mandatory Capability) (~15 tests)
- [ ] 3.4.1 Create `codeflow/documentation_generator.py` with unified logic
  - Support Markdown output for all input types (SPEC.md, Python, Rust)
  - Support Word output (python-docx) where available
  - Reuse existing Claude Code integration from specification.py
  - **Two distinct code paths** (never silently substitute):
    - **Full Narrative Path**: If Claude Code available, generate fluent prose; label output as "AI-Generated Narrative"
    - **Statistics Fallback Path**: If Claude Code unavailable, generate structured summary (node counts, branch counts, etc.); label clearly as "Statistics-Based Summary (Full AI Generation Unavailable)"
  - Verify: can generate both full and fallback outputs for a simple Python function

- [ ] 3.4.2 Add `--prose` flag to CLI
  - When set, trigger DocumentationGenerator after analysis
  - Default behavior (no flag): no prose generation
  - Verify: `python -m codeflow examples/python/tictactoe.py --prose` creates prose output with clear labeling

- [ ] 3.4.3 Implement Markdown prose generation (all three input types)
  - Given CFG, extract code snippets from source (for Python/Rust; quotes for SPEC.md)
  - Full narrative: Send to Claude Code with source context; generate plain-English prose
  - Fallback: Generate statistics-based summary (node counts, paths, decisions, loops, error handling)
  - Format as Markdown (.md file)
  - Verify: output is readable Markdown and clearly labeled

- [ ] 3.4.4 Implement Word prose generation (all three input types, where python-docx available)
  - If python-docx available: generate Word document (.docx) using same narrative as Markdown
  - Use same prose template as Markdown, formatted for Word
  - Save as `{filename}_Narrative.docx`
  - If python-docx missing: inform user and skip Word generation with explanation
  - Verify: Word output is formatted correctly and labeled

- [ ] 3.4.5 Add SPEC.md documentation generation support
  - When user runs `python -m codeflow examples/python/SPEC.md --prose`, generate Markdown/Word prose
  - Synthesize flowchart into plain-English specification prose
  - Verify: output is readable and adds value to specification

- [ ] 3.4.6 Create `tests/test_documentation_generation.py` with ~15 tests
  - Test Markdown output for Python, Rust, SPEC.md (full narrative with Claude Code)
  - Test Markdown fallback when Claude Code unavailable (statistics-based summary with correct label)
  - Test Word output (if python-docx available) with correct format
  - Test Word fallback when python-docx missing (skip Word, inform user, output Markdown)
  - Test error handling and output labeling (ensure "AI-Generated" vs "Statistics-Based" labels present)
  - Verify all tests pass

### Group 3.5: Documentation Updates
- [ ] 3.5.1 Update README.md with Rust support and documentation capability
  - Document supported Rust constructs (if/else, match, loops, error propagation, functions)
  - Document unsupported constructs (macros, closures with captures, async/await, complex generics)
  - **Document explicit warnings** for unsupported constructs and `analysis_incomplete` flag
  - Document mandatory documentation capability with `--prose` flag
  - Explain full narrative vs. statistics-based fallback and how to identify which is used
  - Provide examples: `codeflow examples/rust/tictactoe.rs --output-dir ./report` and `codeflow examples/python/tictactoe.py --prose`

- [ ] 3.5.2 Update CLI help text
  - Document .rs file support
  - Document --prose flag for documentation generation
  - Show examples for all input types: .py, .rs, .md
  - Verify: `python -m codeflow --help` is clear and accurate

### Group 3.6: Verification Gate
- [ ] 3.6.1 Full test suite: Python + Rust + Integration + Documentation
  - Run: `python -m pytest tests/test_exit_connections.py tests/test_graph.py tests/test_integration.py tests/test_layout_exit_convention.py tests/test_layout_overlaps.py tests/test_rust_parsing.py tests/test_specification.py tests/test_multilanguage_integration.py tests/test_documentation_generation.py -v`
  - Confirm: 32 Python + 30 Rust + 15 integration + 10-15 SPEC + 15 documentation = 102+ tests pass
  - **Gate: All tests must pass before Phase 4**

---

## Phase 4: Source Traceability & Comparison (Weeks 7-9) [Optional MVP]

### Group 4.1: Comparison Infrastructure
- [ ] 4.1.1 Create `codeflow/comparison.py` module with evidence-based alignment categories
  - Implement `ComparisonReport` class tracking node alignment
  - Implement node matching heuristics (label similarity, structure matching)
  - **Define alignment categories explicitly**:
    - "Matched": Strong structural correspondence
    - "Partially Matched": Moderate structural correspondence
    - "Unmatched": No clear structural correspondence
    - "Requires Review": Parsing ambiguity or unsupported constructs
  - Include alignment category on every compared node (never omit)
  - Include explicit disclaimer: "Structural matching does NOT prove behavioral equivalence"
  - Calculate coverage metrics with caveats: "X% of spec nodes have aligned implementations (manual review essential to confirm semantic equivalence)"
  - Verify: can compare two simple CFGs and identify aligned nodes with appropriate categories

- [ ] 4.1.2 Implement comparison HTML report generation
  - Generate HTML with side-by-side or tabbed flowcharts
  - Highlight aligned nodes with categories ("Matched", "Partially Matched", "Unmatched", "Requires Review")
  - Show divergence summary (spec-only paths, impl-only paths) with caveats
  - Include explicit disclaimer: "Comparison is a review aid for identifying implementation gaps. Manual verification required for functional correctness. Structural matching does not prove behavioral equivalence."
  - Include source traceability (file/line numbers)
  - Verify: HTML report is viewable and clearly labels limitations and methodology

### Group 4.2: CLI Comparison Command
- [ ] 4.2.1 Add `compare` subcommand to CLI
  - Syntax: `codeflow compare <file1> <file2> [<file3>]`
  - Parse arguments, analyze each file via registry
  - Call comparison logic
  - Generate merged report
  - Verify: CLI accepts 2-3 files and routes to comparison

### Group 4.3: Comparison Testing (~10 tests)
- [ ] 4.3.1 Create `tests/test_comparison.py` with ~10 tests
  - Test spec vs Python (should have strong structural correspondence; expect "Matched" or "Partially Matched")
  - Test Python vs Rust (same behavior, possibly different structure; expect "Partially Matched")
  - Test three-way spec vs Python vs Rust with category assignments
  - Test divergence detection and category accuracy
  - Test that alignment categories are present and appropriate
  - Test "Requires Review" category when unsupported constructs present
  - Verify all tests pass

- [ ] 4.3.2 Test end-to-end comparison workflow
  - Run: `python -m codeflow compare examples/python/SPEC.md examples/python/tictactoe.py examples/rust/tictactoe.rs --output-dir /tmp/compare`
  - Verify comparison report is generated
  - Verify all three flowcharts are shown
  - Verify alignment and divergence are highlighted with categories ("Matched", "Partially Matched", etc.)
  - Verify output includes explicit disclaimer: "Comparison is a review aid. Manual verification required for functional correctness. Structural matching does not prove behavioral equivalence."

### Group 4.4: Limitations & Documentation
- [ ] 4.4.1 Update README.md with comparison mode limitations
  - Clearly state: **"Comparison is a review aid for identifying implementation gaps. Manual verification required for functional correctness. Structural matching does NOT prove behavioral equivalence."**
  - Document alignment categories and what they mean
  - Document that heuristic matching can produce false positives (structurally similar but semantically different) and false negatives (semantically equivalent but structurally different)
  - Explain which constructs create blind spots (unsupported Rust features, macros, async/await, closures, etc.)
  - Explain that different implementations may have equivalent behavior despite divergent structure
  - Provide examples of typical usage and how to interpret results
  - Warn users that manual code review and testing are essential for correctness
  - Warn users that manual verification is essential
  - Verify documentation is clear and complete

### Group 4.5: Verification Gate
- [ ] 4.5.1 Full test suite with comparison tests
  - Run full canonical baseline plus all new tests
  - Confirm: 103+ previous + 10 comparison = 112+ tests pass
  - **Gate: All tests must pass**

---

## Final Integration & Delivery

### Group 5.1: Final Testing & Verification
- [ ] 5.1.1 Full end-to-end workflow validation (all input types, all flags)
  - Python analysis: `python -m codeflow examples/python/tictactoe.py --output-dir /tmp/py_output` → flowchart OK
  - Rust analysis: `python -m codeflow examples/rust/tictactoe.rs --output-dir /tmp/rs_output` → flowchart OK
  - SPEC.md analysis: `python -m codeflow examples/python/SPEC.md --output-dir /tmp/spec_output` → flowchart OK
  - Python with documentation: `python -m codeflow examples/python/tictactoe.py --prose --output-dir /tmp/py_prose` → Markdown + Word generated with labels
  - Rust with documentation: `python -m codeflow examples/rust/tictactoe.rs --prose --output-dir /tmp/rs_prose` → Markdown + Word generated with labels
  - Comparison (if Phase 4 done): `python -m codeflow compare examples/python/SPEC.md examples/python/tictactoe.py examples/rust/tictactoe.rs --output-dir /tmp/compare` → report OK with confidence levels
  - Test with unsupported Rust constructs: Verify explicit warnings and incomplete-analysis flag
  - Verify all workflows complete without errors and produce expected outputs

- [ ] 5.1.2 Regression validation (canonical baseline)
  - Run: `python -m pytest tests/test_exit_connections.py tests/test_graph.py tests/test_integration.py tests/test_layout_exit_convention.py tests/test_layout_overlaps.py -v`
  - Confirm all 33 original Python tests pass unchanged
  - Confirm all new tests pass (Rust, integration, documentation, comparison as applicable)
  - Final count: 112+ tests pass, 0 failures

### Group 5.2: Documentation & Architecture
- [ ] 5.2.1 Update QUICK_START.md or README.md with quickstart examples
  - Add Python quickstart: `python -m codeflow examples/python/tictactoe.py --open`
  - Add Rust quickstart: `python -m codeflow examples/rust/tictactoe.rs --open`
  - Add documentation quickstart: `python -m codeflow examples/python/tictactoe.py --prose`
  - Verify examples are clear and working

- [ ] 5.2.2 Create or update `tools/codeflow/ARCHITECTURE.md`
  - Document analyzer plugin system and Analyzer ABC interface
  - Explain how to add new languages (implement Analyzer, register extension)
  - Show code examples for creating an Analyzer subclass
  - Document AnalysisResult structure with source_references and ambiguity_flags
  - Document tree-sitter integration and graceful degradation for unsupported constructs
  - Verify documentation is clear and maintainable

### Group 5.3: Container & Dependencies
- [ ] 5.3.1 Verify tree-sitter installation and dependencies
  - Document exact versions of tree-sitter and tree-sitter-rust used
  - If Dockerfile needs updates, document changes (system dependencies for tree-sitter)
  - Verify tree-sitter is available when CodeFlow runs in container
  - Verify python-docx is optional (installed only if docs extra requested)
  - Test installation in Software Factory container environment

### Group 5.4: Final Sign-Off
- [ ] 5.4.1 Code review checklist
  - All new code follows CodeFlow style and conventions
  - All tests pass (canonical baseline + all new tests)
  - All documentation updated and accurate
  - No breaking changes to existing Python workflow
  - Backward compatibility confirmed (all 33 original tests pass)
  - Warnings for unsupported constructs are explicit and informative
  - Fallback documentation is clearly labeled
  - Confidence levels are present on all comparison matches

- [ ] 5.4.2 Acceptance testing
  - Stakeholders review flowcharts for Python, Rust, and SPEC.md (verify quality)
  - Stakeholders review documentation generation (full narrative vs. fallback)
  - Stakeholders review comparison mode with confidence levels
  - Stakeholders confirm delivered features meet requirements

---

## Testing Summary

| Test Category | Count | Required | Notes |
|---|---|---|---|
| Python Regression (existing, 32 tests) | 32 | ✅ MUST PASS | Regression gate; unchanged baseline |
| Rust Parsing (new) | 30 | ✅ Core | tree-sitter integration, warnings, unsupported constructs |
| SPEC.md Specification (new) | 10-15 | ✅ Core | Regression for existing feature |
| Multilanguage Integration (new) | 10-15 | ✅ Core | CLI routing, analyzer dispatch |
| Documentation Generation (new) | 15 | ✅ Mandatory | Full vs. fallback labeling, all input types |
| Comparison & Alignment (new, optional) | 10 | ✨ Optional | Alignment categories, review aid semantics |
| **Total** | **112+** | | **All must pass before release** |

**Gate Criteria:**
- **Phase 1**: All 32 Python tests pass (no regression)
- **Phase 2**: All 32 Python + 30 Rust tests pass
- **Phase 3**: All 32 + 30 + 10-15 + 10-15 + 15 = 102+ tests pass (documentation mandatory)
- **Phase 4** (optional): Add 10 comparison tests; all pass
- **Final**: 112+ tests pass, 0 failures before declaring implementation complete

---

## Key Implementation Notes

### Test Commands
- **Always use canonical baseline**: `python -m pytest tests/test_exit_connections.py tests/test_graph.py tests/test_integration.py tests/test_layout_exit_convention.py tests/test_layout_overlaps.py -v`
- Never use wildcards like `tests/test_*.py` or `tests/test_python_*`
- Explicit file lists ensure complete coverage

### Unsupported Rust Constructs
- Generate **explicit warnings** to stderr with line numbers
- Set `analysis_incomplete = True` in AnalysisResult
- Add entries to `ambiguity_flags` list with description
- Treated as opaque statements; parsing continues
- Warnings appear in HTML report

### Documentation Generation
- **Full Narrative**: Claude Code available → fluent prose → label "AI-Generated Narrative"
- **Statistics Fallback**: Claude Code unavailable → structured summary → label "Statistics-Based Summary (Full AI Generation Unavailable)"
- Never silently substitute; always explicitly label
- Check python-docx availability; skip Word if missing with explanation

### Tree-Sitter Integration
- Pin exact versions of tree-sitter and tree-sitter-rust
- Use current stable Python API (verify against package documentation)
- Use tree-sitter node positions (0-indexed lines) and convert to 1-indexed for reporting

### Comparison Alignment Categories (Evidence-Based)
- "Matched": Strong structural correspondence; requires manual review to confirm semantic equivalence
- "Partially Matched": Moderate structural correspondence; requires manual review to determine semantic relationship
- "Unmatched": No clear structural correspondence; requires manual review to explain difference
- "Requires Review": Parsing ambiguity or unsupported constructs; cannot determine alignment without code inspection
- Never claim structural matching proves behavioral equivalence
- Include disclaimer in reports: "Comparison is a review aid for identifying implementation gaps. Manual verification required for functional correctness."
- Never omit alignment category from compared nodes

### Mermaid Import Preservation
- Existing SPEC.md Mermaid import capability continues unchanged
- No changes to SpecificationAnalyzer's existing Mermaid handling
- New multilanguage renderers preserve imported Mermaid → native CodeFlow SVG behavior
