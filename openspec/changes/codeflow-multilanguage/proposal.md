# Proposal: CodeFlow Multilanguage Support

## Why

CodeFlow 0.2 currently accepts two first-class input types:
1. **Markdown specifications** (.md) – document intended behavior via flowchart notation (SPEC.md)
2. **Python source code** (.py) – analyze implementation control flow via Python AST

The Software Factory needs CodeFlow to accept **Rust source code** (.rs) as a third first-class input type while maintaining complete backward compatibility with existing Python and Markdown workflows. This enables developers to:

1. Visualize Rust control flow using the same SVG/HTML rendering conventions as Python flowcharts
2. Compare implementation behavior across specification, Python, and Rust implementations
3. Support structured parsing of Rust's decision-making constructs (match expressions with patterns/guards, if/else, loops, error propagation via ? operator) with proper CFG representation
4. Generate optional human-readable documentation (Markdown or Word) for specifications, Python, and Rust implementations
5. Maintain complete source traceability: specification requirement IDs, and Python/Rust file/line references
6. Preserve all existing workflows: SPEC.md flowcharts, existing Word walkthroughs, and Python analysis remain unchanged

## What Changes

- **Three First-Class Input Types**: SPEC.md, Python, and Rust are equal inputs. Each generates:
  - A native CodeFlow SVG/HTML flowchart using the existing layout and rendering conventions
  - An optional human-readable document (Markdown or Word format)
  
- **Parser Infrastructure**: Introduce a pluggable analyzer architecture that separates language-specific parsing from graph construction and rendering

- **Rust Analysis**: Implement a structured Rust parser (using tree-sitter with Rust grammar) supporting:
  - Decision statements (if/else, match expressions with guard patterns)
  - Loop constructs (for, while, loop with break/continue)
  - Function entry/exit and return statements
  - Error propagation (? operator, Result/Option handling)
  - Call sequences and basic block identification
  - Graceful degradation for unsupported constructs with warning/degradation flags

- **Source Traceability**: Track and preserve:
  - Specification requirement IDs or section references
  - Python and Rust source file paths and line numbers in generated reports

- **Documentation Generation**: Unified optional narrative generation for SPEC.md, Python, and Rust:
  - Markdown output (Markdown specification for all three input types)
  - Word output (where dependencies permit, preserving existing SPEC.md Word functionality)
  - Language-neutral prose templates with language-specific customization

- **Comparison & Traceability**: Optional cross-reference capability between specification, Python implementation, and Rust implementation (review aid, not proof of equivalence)

- **CLI Compatibility**: Extend the existing command-line interface to accept .rs files alongside .py and .md

- **Test Coverage**: Preserve all 33 existing Python regression tests (unchanged); add regression and new test suites for:
  - SPEC.md specification files and flowchart rendering
  - Rust parsing and CFG generation
  - Narrative generation (Markdown and Word output) - **mandatory capability**
  - Multilanguage workflows

- **Error Handling & Ambiguity**: Document unsupported Rust constructs (macros, closures with captures, complex async patterns, complex generics) and degrade gracefully with warnings. Clearly distinguish:
  - Specification intent (what SPEC.md says should happen)
  - Implementation behavior (what Python/Rust code actually does)
  - Unverified assumptions (ambiguous specifications or unsupported syntax)

## Capabilities

### New Capabilities

- `code-analysis/rust-parsing`: Structured parser for Rust source files (using tree-sitter with Rust grammar) generating CFG nodes and edges representing control flow. Supports if/else, match expressions with patterns and guards, loops (for/while/loop), returns, error propagation (?), and function boundaries. Reports unsupported constructs (macros, closures with captures, complex async, complex generics) with degradation flags; analysis continues with warnings.

- `code-analysis/python-documentation`: Mandatory CodeFlow 0.3 capability - Optional human-readable documentation generation for Python implementations. Accepts Python source and produces Markdown or Word output describing control flow paths, decisions, error handling, and exits. Reuses existing Claude Code integration where available; generates clearly-labeled statistics-based summary if Claude Code unavailable.

- `code-analysis/rust-documentation`: Mandatory CodeFlow 0.3 capability - Optional human-readable documentation generation for Rust implementations. Accepts Rust source and produces Markdown or Word output explaining control flow logic, Rust idioms (match, ?, ownership), and error handling patterns. Reuses existing Claude Code integration where available; generates clearly-labeled statistics-based summary if Claude Code unavailable.

- `code-analysis/specification-documentation`: Mandatory CodeFlow 0.3 capability - Optional human-readable documentation generation for SPEC.md specifications. Produces Markdown or Word output synthesizing the flowchart intent into prose. Reuses existing Claude Code integration where available; generates clearly-labeled statistics-based summary if Claude Code unavailable.

- `visualization/multilanguage-rendering`: Native CodeFlow SVG and HTML rendering for flowcharts from any supported language (Python, Rust, SPEC.md) using the existing SVG layout, shapes, connector conventions, and HTML output format. No Mermaid or alternate rendering; preserves CodeFlow's established visual conventions. Includes optional language-specific metadata (file paths, line numbers, ambiguity flags).

- `traceability/source-references`: Maintains source traceability across all inputs:
  - Specification: requirement IDs, section references
  - Python/Rust: source file paths, line numbers, function boundaries
  - Exportable as metadata in HTML/JSON reports

- `analyzer-plugin-system`: Pluggable architecture allowing analyzers to register for file extensions (.py, .rs, .md) and be discovered/invoked by the CLI and report generator without core changes.

- `comparison-traceability`: Optional (MVP) cross-reference feature showing alignment between specification, Python implementation, and Rust implementation. Defines comparison as a review and traceability aid, not as proof of behavioral equivalence. Includes optional divergence detection and coverage metrics (e.g., which specification paths have implementation, which paths diverge).

### Modified Capabilities

- None. The Python specification behavior is preserved; SPEC.md workflows unchanged; all changes are additive or internal refactoring.

## Impact

- **Code**: `tools/codeflow/` package (CodeFlow scoped; no Software Factory core changes):
  - `codeflow/analyzers/`: New `rust_analyzer.py` using tree-sitter Python bindings; refactor `python_analyzer.py` to inherit from common `Analyzer` ABC
  - `codeflow/cli.py`: Extended to accept .rs files and route to appropriate analyzer via registry
  - `codeflow/report_generator.py`: Refactored to use pluggable analyzer discovery (no hardcoded analyzer calls)
  - `codeflow/render/`, `codeflow/layout/`: Preserved; no changes needed (already language-agnostic)
  - `codeflow/documentation_generator.py` (new, optional): Unified narrative generation for Python, Rust, and SPEC.md
  - `codeflow/comparison.py` (new, optional): Optional MVP comparison and traceability
  - `tests/`: New test suites for Rust parsing, SPEC.md rendering, narrative generation, and multilanguage workflows

- **APIs**: 
  - New `Analyzer` abstract base class with `analyze(source_path: str) -> AnalysisResult` method
  - Extension of `ReportGenerator` to support analyzer plugin discovery (no breaking changes to existing interface)
  - CLI accepts .rs files and routes based on file extension registry

- **Dependencies**: 
  - **tree-sitter** (Python bindings) + **tree-sitter-rust** grammar: Core requirement for Rust parsing (pinned versions documented)
  - **python-docx** (optional): Already available for Word output; condition-checked at import time
  - No new required dependencies for core Python/SPEC.md workflows
  - Dependency manifest (requirements.txt or pyproject.toml) updated with tree-sitter and tree-sitter-rust versions
  - Container Dockerfile updated to include tree-sitter dependencies if needed; documented how to verify installation

- **Backward Compatibility**: 
  - All existing Python analysis behavior unchanged; Python analyzer refactored into ABC pattern but produces identical CFG
  - All existing SPEC.md workflows unchanged; SVG/HTML rendering unchanged; Mermaid import support preserved
  - All 32 existing Python regression tests continue to pass (primary validation gate)
  - CLI remains backward compatible (existing commands work unchanged; new .rs/.md flags are additive)
  - New flags/options are additive only (no breaking changes)

- **Testing**:
  - Preserve 32 existing Python tests (pass/fail criteria unchanged) ← Primary regression gate
  - Add ~10-15 tests for SPEC.md rendering and specification parsing (verify no regression in existing spec workflow)
  - Add ~25-30 tests for Rust parsing (basic syntax, control flow, edge cases, error cases, unsupported constructs with explicit warnings)
  - Add ~10-15 integration tests for multilanguage CLI workflows
  - Add ~10-15 tests for narrative generation (Markdown and Word output; validate clear labeling of fallback vs. full narratives when dependencies available/unavailable)
  - Add ~5-10 tests for optional comparison/traceability features (confidence levels, limitations)
  - Total: 82+ tests ensuring correctness and full regression prevention
  - Test examples: simple Rust functions, match with multiple arms, nested loops, error handling with ?, unsupported constructs (macros, async), divergences from spec

- **Documentation**:
  - Update README.md to document .rs input option, Tree-sitter dependency, and Rust-specific limitations
  - Document unsupported Rust constructs (macros, closures with captures, complex async patterns, complex generics) with specific examples of degradation
  - Add Rust examples to `examples/rust/` directory (TicTacToe equivalent or similar flow logic)
  - Document source traceability: how specification IDs, file paths, and line numbers are captured and exported
  - Document comparison mode limitations: comparison is a review aid, not proof of equivalence
  - Clearly flag ambiguous specifications and how unsupported constructs are reported
