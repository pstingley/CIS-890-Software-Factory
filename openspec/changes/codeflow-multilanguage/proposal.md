# Proposal: CodeFlow Multilanguage Support with PHP

## Why

CodeFlow 0.2 currently accepts two first-class input types:
1. **Markdown specifications** (.md) – document intended behavior via flowchart notation (SPEC.md)
2. **Python source code** (.py) – analyze implementation control flow via Python AST

The Software Factory needs CodeFlow to accept **Rust source code** (.rs) and **PHP source code** (.php) as third and fourth first-class input types while maintaining complete backward compatibility with existing Python and Markdown workflows. This enables developers to:

1. Visualize Rust and PHP control flow using the same SVG/HTML rendering conventions as Python flowcharts
2. Compare implementation behavior across specification, Python, Rust, and PHP implementations
3. Support structured parsing of Rust's decision-making constructs (match expressions with patterns/guards, if/else, loops, error propagation via ? operator) with proper CFG representation
4. Support structured parsing of PHP's control flow constructs (functions, classes, methods, namespaces, if/else, switch/match, loops, returns, exceptions, calls) including multi-file projects with include/require and Composer autoloading
5. Generate optional human-readable documentation (Markdown or Word) for specifications, Python, Rust, and PHP implementations
6. Maintain complete source traceability: specification requirement IDs, and Python/Rust/PHP file/line references
7. Support project-level analysis for Python, Rust, and PHP with application entry-point discovery and cross-file relationships
8. Preserve all existing workflows: SPEC.md flowcharts, existing Word walkthroughs, and Python analysis remain unchanged

## What Changes

- **Four First-Class Input Types**: SPEC.md, Python, Rust, and PHP are equal inputs. Each generates:
  - A native CodeFlow SVG/HTML flowchart using the existing layout and rendering conventions
  - Two mandatory human-readable prose documents:
    1. **Functional Description**: What the application does, suitable for business analysts and stakeholders
    2. **Technical Description**: How the application works, suitable for software engineers and developers
  - Both prose views are traceable to analyzed source files and explicitly label uncertainties
  
- **Parser Infrastructure**: Introduce a pluggable analyzer architecture that separates language-specific parsing from graph construction and rendering

- **Rust Analysis**: Implement a structured Rust parser (using tree-sitter with Rust grammar) supporting:
  - Decision statements (if/else, match expressions with guard patterns)
  - Loop constructs (for, while, loop with break/continue)
  - Function entry/exit and return statements
  - Error propagation (? operator, Result/Option handling)
  - Call sequences and basic block identification
  - Graceful degradation for unsupported constructs with warning/degradation flags

- **PHP Analysis**: Implement a structured PHP parser (using tree-sitter PHP with Python bindings) supporting:
  - Function definitions, class definitions, methods, namespaces
  - Control flow (if/else, switch/match, loops, break/continue, return)
  - Exception handling (try/catch/finally, throw)
  - Function and method calls, chained calls
  - Multi-file project discovery via **include/require/include_once/require_once** statements with preserved failure semantics
  - Composer metadata parsing and PSR-4 autoloading (MVP scope; defer advanced framework-specific autoloading)
  - Statically identifiable application entry points (index.php, public/*.php, configured routing roots)
  - Graceful handling of mixed PHP/HTML files, dynamic includes, reflection, and unresolved calls
  - Explicit four-category ambiguity reporting: **dynamic behavior**, **unsupported syntax**, **parsing errors**, and **incomplete analysis**
  - PHP-specific include/require semantics: distinguish require/include failure modes and report explicitly

- **Source Traceability**: Track and preserve:
  - Specification requirement IDs or section references
  - Python and Rust source file paths and line numbers in generated reports

- **Documentation Generation**: Mandatory unified two-part narrative generation for SPEC.md, Python, Rust, and PHP:
  1. **Functional Description** (business analyst view): What the application/module does, intended behavior, user-facing features
  2. **Technical Description** (software engineer view): How the application/module works, implementation patterns, control flow logic, error handling
  - Markdown output (Markdown specification for all four input types)
  - Word output (where dependencies permit, preserving existing SPEC.md Word functionality)
  - Both views must be traceable to analyzed source files (with file paths, line numbers, function names)
  - Both views must explicitly label uncertainties: dynamic behavior, unsupported constructs, unresolved references, incomplete analysis
  - Language-neutral prose templates with language-specific customization (e.g., Rust's match/? patterns, PHP's namespace/autoloading, Python's exception handling)

- **Comparison & Traceability**: Optional cross-reference capability between specification, Python, Rust, and PHP implementations (review aid, not proof of equivalence)

- **CLI Compatibility**: Extend the existing command-line interface:
  - `codeflow <file>` - Existing single-file analysis (Python, Rust, PHP, SPEC.md)
  - `codeflow project <directory>` - New project-level analysis command (Python, Rust, PHP projects)
  - Both commands remain backward compatible

- **Project-Level Analysis**: Support analysis beyond single files for Python, Rust, and PHP:
  - Discover related source files within a project directory
  - Identify application entry points (main.py for Python, main.rs for Rust, index.php/configured roots for PHP)
  - Map cross-file function/method calls and dependencies
  - Produce project-level overview flowcharts showing module/file relationships

- **Test Coverage**: Preserve all 41 existing Python and SPEC.md regression tests (unchanged); add regression and new test suites for:
  - SPEC.md specification files and flowchart rendering
  - Rust parsing and CFG generation
  - PHP parsing, CFG generation, multi-file discovery, and project analysis
  - Narrative generation (Markdown and Word output) - **mandatory capability**
  - Project-level analysis (Python, Rust, PHP)
  - Multilanguage workflows

- **Error Handling & Ambiguity**: Document unsupported constructs for each language and degrade gracefully with explicit warnings. Distinguish four categories:
  1. **Dynamic Behavior**: Constructs that cannot be statically analyzed (PHP: `include($var)`, `$this->$method()`; Rust: macros; Python: `exec()`, `eval()`)
  2. **Unsupported Syntax**: Language features outside current analyzer scope (Rust: complex generics, async/await patterns; PHP: reflection APIs; Python: decorators with complex arguments)
  3. **Parsing Errors**: Syntax errors or malformed code that prevents analysis
  4. **Incomplete Analysis**: Partial analysis due to unresolved dependencies (cross-file references, missing includes, Composer autoloading edge cases)
  - For PHP specifically: preserve include/require/include_once/require_once semantics including failure modes and distinguish from dynamic includes

## Capabilities

### New Capabilities

- `code-analysis/rust-parsing`: Structured parser for Rust source files (using tree-sitter with Rust grammar) generating CFG nodes and edges representing control flow. Supports if/else, match expressions with patterns and guards, loops (for/while/loop), returns, error propagation (?), and function boundaries. Reports unsupported constructs (macros, closures with captures, complex async, complex generics) with degradation flags; analysis continues with warnings.

- `code-analysis/php-parsing`: Structured parser for PHP source files (using tree-sitter PHP with Python bindings) generating CFG nodes and edges representing control flow. Supports functions, classes, methods, namespaces, if/else, switch/match expressions, loops (for/while/foreach/do-while), returns, exception handling (try/catch/finally, throw), and function/method calls. Preserves include/require/include_once/require_once semantics including failure modes. Supports PSR-4 autoloading discovery via Composer metadata (MVP scope). Flags dynamic includes, variable function calls, reflection, and unresolved cross-file references with explicit four-category reporting (dynamic behavior, unsupported syntax, parsing errors, incomplete analysis). Handles mixed PHP/HTML files where the parser supports them, with documentation of framework routing and runtime-dependent behavior limitations.

- `code-analysis/php-documentation`: Mandatory CodeFlow 0.3 capability - Two-part human-readable documentation generation for PHP implementations (Functional Description and Technical Description). Accepts PHP source (single-file or project-level) and produces Markdown or Word output explaining program behavior from business and technical perspectives. Includes traceability to source files (file paths, line numbers, function names) and explicitly labels uncertainties (dynamic behavior, unsupported syntax, unresolved references, incomplete analysis). Leverages Claude Code integration where available; generates clearly-labeled statistics-based summary if unavailable.

- `code-analysis/python-documentation`: Mandatory CodeFlow 0.3 capability - Two-part human-readable documentation generation for Python implementations (Functional Description and Technical Description). Accepts Python source and produces Markdown or Word output describing control flow logic, program behavior, and error handling from business and technical perspectives. Includes source traceability and explicit uncertainty labeling. Leverages Claude Code integration where available; generates clearly-labeled statistics-based summary if unavailable.

- `code-analysis/rust-documentation`: Mandatory CodeFlow 0.3 capability - Two-part human-readable documentation generation for Rust implementations (Functional Description and Technical Description). Accepts Rust source and produces Markdown or Word output explaining control flow logic, Rust idioms (match, ?, ownership), error handling patterns, and overall behavior from business and technical perspectives. Includes source traceability and explicit uncertainty labeling. Leverages Claude Code integration where available; generates clearly-labeled statistics-based summary if unavailable.

- `code-analysis/specification-documentation`: Mandatory CodeFlow 0.3 capability - Two-part human-readable documentation generation for SPEC.md specifications (Functional Description and Technical Description). Produces Markdown or Word output synthesizing the flowchart intent into prose from both business and technical perspectives. Leverages Claude Code integration where available; generates clearly-labeled statistics-based summary if unavailable.

- `visualization/multilanguage-rendering`: Native CodeFlow SVG and HTML rendering for flowcharts from any supported language (Python, Rust, PHP, SPEC.md) using the existing SVG layout, shapes, connector conventions, and HTML output format. No Mermaid or alternate rendering; preserves CodeFlow's established visual conventions. Includes optional language-specific metadata (file paths, line numbers, ambiguity flags).

- `traceability/source-references`: Maintains source traceability across all inputs:
  - Specification: requirement IDs, section references
  - Python/Rust/PHP: source file paths, line numbers, function/method boundaries
  - Exportable as metadata in HTML/JSON reports

- `analyzer-plugin-system`: Pluggable architecture allowing analyzers to register for file extensions (.py, .rs, .php, .md) and be discovered/invoked by the CLI and report generator without core changes.

- `comparison-traceability`: Optional (MVP) cross-reference feature showing alignment between specification, Python implementation, Rust implementation, and PHP implementation. Defines comparison as a review and traceability aid, not as proof of behavioral equivalence. Includes optional divergence detection and coverage metrics (e.g., which specification paths have implementation in each language, which paths diverge).

- `project-discovery`: Shared multi-file project discovery infrastructure for Python, Rust, and PHP:
  - Identify project root and related source files (Python packages/modules, Rust crates, PHP namespaces/PSR-4 structure)
  - Discover application entry points (main.py, main.rs, index.php, configured routing roots)
  - Map multi-file dependencies: include/require chains (PHP), use/mod statements (Rust), import statements (Python)
  - Support Composer metadata parsing (PHP), Cargo.toml parsing (Rust), setup.py parsing (Python)
  - Produce project-level overview reports showing file relationships and cross-file call graphs

### Modified Capabilities

- None. The Python specification behavior is preserved; SPEC.md workflows unchanged; all changes are additive or internal refactoring.

## Impact

- **Code**: `tools/codeflow/` package (CodeFlow scoped; no Software Factory core changes):
  - `codeflow/analyzers/`: New `rust_analyzer.py` using tree-sitter Python bindings; new `php_analyzer.py` using tree-sitter PHP Python bindings; refactor `python_analyzer.py` to inherit from common `Analyzer` ABC
  - `codeflow/cli.py`: Extended to accept .rs and .php files and route to appropriate analyzer via registry
  - `codeflow/report_generator.py`: Refactored to use pluggable analyzer discovery (no hardcoded analyzer calls)
  - `codeflow/render/`, `codeflow/layout/`: Preserved; no changes needed (already language-agnostic)
  - `codeflow/project_discoverer.py` (new): Multi-file project discovery for Python, Rust, and PHP; entry-point identification; dependency mapping
  - `codeflow/documentation_generator.py` (new, optional): Unified narrative generation for Python, Rust, PHP, and SPEC.md
  - `codeflow/comparison.py` (new, optional): Optional MVP comparison and traceability across all four input types
  - `tests/`: New test suites for Rust parsing, PHP parsing and project discovery, SPEC.md rendering, narrative generation, project-level analysis, and multilanguage workflows

- **APIs**: 
  - New `Analyzer` abstract base class with `analyze(source_path: str) -> AnalysisResult` method
  - Extension of `ReportGenerator` to support analyzer plugin discovery (no breaking changes to existing interface)
  - CLI accepts .rs files and routes based on file extension registry

- **Dependencies**: 
  - **tree-sitter** (Python bindings) + **tree-sitter-rust** grammar: Core requirement for Rust parsing (pinned versions documented)
  - **tree-sitter** (Python bindings) + **tree-sitter-php** grammar: Core requirement for PHP parsing (pinned versions documented)
  - **python-docx** (optional): Already available for Word output; condition-checked at import time
  - No new required dependencies for core Python/SPEC.md workflows
  - Dependency manifest (requirements.txt or pyproject.toml) updated with tree-sitter, tree-sitter-rust, and tree-sitter-php versions
  - Container Dockerfile updated to include tree-sitter dependencies if needed; documented how to verify installation

- **Backward Compatibility**: 
  - All existing Python analysis behavior unchanged; Python analyzer refactored into ABC pattern but produces identical CFG
  - All existing SPEC.md workflows unchanged; SVG/HTML rendering unchanged; Mermaid import support preserved
  - All 32 existing Python regression tests continue to pass (primary validation gate)
  - CLI remains backward compatible (existing commands work unchanged; new .rs/.md flags are additive)
  - New flags/options are additive only (no breaking changes)

- **Testing**:
  - Preserve 41 existing Python and SPEC.md tests (pass/fail criteria unchanged) ← Primary regression gate
  - Add ~20-25 tests for Rust parsing (basic syntax, control flow, edge cases, error cases, unsupported constructs with explicit warnings)
  - Add ~25-30 tests for PHP parsing (functions, classes, control flow, exceptions, function/method calls)
  - Add ~15-20 tests for PHP project discovery and multi-file analysis
  - Add ~10-15 integration tests for multilanguage CLI workflows
  - Add ~10-15 tests for project-level analysis (Python, Rust, PHP entry-point discovery and cross-file relationships)
  - Add ~10-15 tests for narrative generation (Markdown and Word output; validate clear labeling of fallback vs. full narratives when dependencies available/unavailable)
  - Add ~5-10 tests for optional comparison/traceability features (confidence levels, limitations)
  - Total: 130+ tests ensuring correctness and full regression prevention
  - Test examples: simple Rust functions, match with multiple arms, nested loops, error handling with ?; PHP functions, classes with methods, include/require chains, exception handling, multi-file projects

- **Documentation**:
  - Update README.md to document .rs and .php input options, Tree-sitter dependencies for both languages, and language-specific limitations
  - Document unsupported Rust constructs (macros, closures with captures, complex async patterns, complex generics) with specific examples of degradation
  - Document PHP-specific limitations: mixed PHP/HTML files, dynamic includes, reflection, unresolved calls, framework routing and runtime-dependent dispatch
  - Add Rust examples to `examples/rust/` directory (TicTacToe equivalent or similar flow logic)
  - Add PHP examples to `examples/php/` directory (project-level example with multiple files, Composer autoloading, entry points)
  - Document source traceability: how specification IDs, file paths, and line numbers are captured and exported
  - Document project-level analysis: how entry points are discovered, cross-file relationships are mapped, and dependencies are visualized
  - Document comparison mode limitations: comparison is a review aid, not proof of equivalence
  - Clearly flag ambiguous specifications, dynamic behavior, and how unsupported constructs are reported
