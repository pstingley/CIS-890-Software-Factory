# Spec Delta: Rust Parsing

## Purpose

Provides structured parsing of Rust source files to extract control flow information, generating control-flow graph (CFG) nodes and edges that represent function entry/exit, decision statements, loops, and error propagation, with documented degradation for unsupported constructs.

## ADDED Requirements

### Requirement: Parse Rust function entry and exit
CodeFlow SHALL identify Rust function boundaries (fn declaration and return point) and represent them as CFG entry and exit nodes.

#### Scenario: Simple function with explicit return
- **WHEN** parsing a Rust function with an explicit `return` statement
- **THEN** the CFG contains one entry node (function name) and one exit node (return target)

#### Scenario: Function with implicit return
- **WHEN** parsing a Rust function where the last expression is the implicit return value
- **THEN** the CFG contains an entry node and an exit node where the final expression flows to exit

#### Scenario: Function with multiple return paths
- **WHEN** parsing a Rust function with multiple `return` statements in different branches
- **THEN** the CFG contains one entry node and multiple paths that converge on a single exit node

### Requirement: Parse if/else decision statements
CodeFlow SHALL parse Rust if, else if, and else blocks as decision nodes with two or more branches.

#### Scenario: Simple if-else
- **WHEN** parsing `if condition { ... } else { ... }`
- **THEN** the CFG contains a decision node with two outgoing edges labeled "true" and "false"

#### Scenario: if-else-if chain
- **WHEN** parsing `if c1 { ... } else if c2 { ... } else { ... }`
- **THEN** the CFG contains nested decision nodes representing each condition in sequence

#### Scenario: if without else
- **WHEN** parsing an `if condition { ... }` without an else block
- **THEN** the CFG contains a decision node with true and false branches; the false branch merges with continuation after the if

### Requirement: Parse match expressions with multiple arms
CodeFlow SHALL parse Rust `match` expressions as multi-branch decision nodes, with each arm as a separate path.

#### Scenario: Match with literal patterns
- **WHEN** parsing `match value { 1 => {...}, 2 => {...}, _ => {...} }`
- **THEN** the CFG contains a decision node with three outgoing edges (one per arm)

#### Scenario: Match with guard clauses
- **WHEN** parsing `match value { Some(x) if x > 0 => {...}, _ => {...} }`
- **THEN** the CFG represents the guard condition and shows the conditional path

#### Scenario: Nested match expressions
- **WHEN** parsing a match arm containing another match statement
- **THEN** the CFG nests decision nodes appropriately, preserving arm structure

### Requirement: Parse loop constructs
CodeFlow SHALL parse Rust for, while, and loop statements as loop-entry nodes with back edges and exit paths.

#### Scenario: For loop with range
- **WHEN** parsing `for i in 0..10 { ... }`
- **THEN** the CFG contains a loop-entry node and a back edge from the loop body to the condition, with an exit edge when the loop terminates

#### Scenario: While loop with condition
- **WHEN** parsing `while condition { ... }`
- **THEN** the CFG contains a decision node (the condition) with a back edge to itself (loop) and an exit edge (break/end)

#### Scenario: Infinite loop with break
- **WHEN** parsing `loop { if condition { break; } ... }`
- **THEN** the CFG contains a loop node with an exit edge at the break statement

#### Scenario: Break and continue in loop
- **WHEN** parsing a loop with `break` and `continue` statements
- **THEN** the CFG shows break edges exiting the loop and continue edges looping back to the loop condition

### Requirement: Parse error propagation with ? operator
CodeFlow SHALL parse Rust's `?` error propagation operator and Result/Option handling as exception-path edges.

#### Scenario: Function call with ? operator
- **WHEN** parsing `result_value?` or `function_that_returns_result()?`
- **THEN** the CFG creates an exception path (edge) from the operation to the function exit, representing early return on error

#### Scenario: Nested ? operators in expression
- **WHEN** parsing `first()?.second()?.third()?`
- **THEN** the CFG chains exception paths through the sequence

#### Scenario: if let pattern with error
- **WHEN** parsing `if let Ok(value) = risky_operation() { ... }`
- **THEN** the CFG shows the Ok branch (true) and implicit error exit (false/exception)

### Requirement: Parse function call sequences as statement nodes
CodeFlow SHALL recognize function calls and represent them as statement nodes in the call sequence.

#### Scenario: Direct function call
- **WHEN** parsing a line with a function call `func()`
- **THEN** the CFG contains a call node (or statement node labeled with the function name)

#### Scenario: Chained method calls
- **WHEN** parsing `obj.method1().method2().method3()`
- **THEN** the CFG represents the sequence as connected statement nodes

#### Scenario: Nested function calls
- **WHEN** parsing `outer(inner(x))`
- **THEN** the CFG shows the inner call followed by the outer call in sequence

### Requirement: Document and degrade unsupported Rust constructs with explicit warnings
CodeFlow SHALL accept files with unsupported constructs, represent the surrounding control flow, and report unsupported features with **explicit warning messages to stderr** and degradation flags in the analysis result. Warnings shall include line numbers and construct types; analysis shall NOT silently degrade.

#### Scenario: File contains macro invocation
- **WHEN** parsing a Rust file with macro calls (e.g., `println!`, `vec!`)
- **THEN** CodeFlow:
  - Treats the macro call as an opaque statement and continues parsing
  - Logs to stderr: "WARNING: Unsupported construct detected at line NNN: macro_invocation (Analysis may be incomplete for this section)"
  - Stores warning in AnalysisResult.ambiguity_flags: "Line NNN: macro_invocation (not fully analyzed)"
  - Sets AnalysisResult.analysis_incomplete = True

#### Scenario: File contains async/await patterns
- **WHEN** parsing Rust code with `async fn` or `.await`
- **THEN** CodeFlow:
  - Represents the function as a regular function (async keyword stripped from analysis)
  - Logs to stderr: "WARNING: Unsupported construct at line NNN: async_fn (Analysis may be incomplete)"
  - Stores warning in ambiguity_flags
  - Sets analysis_incomplete = True

#### Scenario: File contains complex generic constraints
- **WHEN** parsing functions with complex trait bounds and generic parameters
- **THEN** CodeFlow:
  - Represents the function signature and parses the body
  - Logs to stderr: "WARNING: Complex generics detected at line NNN: advanced_trait_bounds (May affect control flow analysis)"
  - Stores in ambiguity_flags as informational (does NOT set analysis_incomplete unless parsing actually failed)

#### Scenario: File contains closure with captures
- **WHEN** parsing a closure `|x| { ... }` or `move || { ... }`
- **THEN** CodeFlow:
  - Represents the closure as a callable unit
  - Logs to stderr: "WARNING: Closure with captures at line NNN: closure_capture (Capture semantics not analyzed)"
  - Stores warning in ambiguity_flags
  - Sets analysis_incomplete = True

#### Scenario: Unsupported construct does not block analysis
- **WHEN** parsing a file with multiple unsupported constructs
- **THEN** CodeFlow:
  - Completes analysis successfully
  - Generates CFG for supported portions
  - Logs multiple warnings to stderr (one per unsupported construct)
  - Lists all unsupported items in ambiguity_flags
  - Sets analysis_incomplete = True
  - Includes summary: "Analysis completed with X unsupported constructs; review HTML report for details"

### Requirement: AnalysisResult includes analysis_incomplete flag
CodeFlow SHALL include an `analysis_incomplete: bool` field in AnalysisResult. This field is set to True whenever unsupported constructs are encountered that could affect control flow analysis accuracy (macros, async/await, closures with captures); it is False when analysis is complete or when unsupported constructs are only informational (complex generics that do not prevent parsing).

#### Scenario: Analysis completeness indicated via field
- **WHEN** the Rust analyzer completes analysis of a file
- **THEN** the AnalysisResult includes:
  - `analysis_incomplete = False` if all constructs are supported or only informational
  - `analysis_incomplete = True` if macros, async/await, or capture closures were encountered

#### Scenario: HTML report includes completeness indicator
- **WHEN** generating the HTML flowchart report for a Rust file
- **THEN** the report includes a note (if `analysis_incomplete = True`): "Note: This analysis is incomplete due to unsupported constructs. Review warnings below." with a list of the warnings

### Requirement: CLI accepts .rs files and routes them to the Rust analyzer
CodeFlow's command-line interface SHALL accept Rust (.rs) files and invoke the Rust analyzer, producing flowchart output using the same format as Python analysis.

#### Scenario: User provides .rs file path
- **WHEN** user runs `codeflow analyze example.rs`
- **THEN** CodeFlow parses the Rust file and generates an HTML flowchart report named `example_codeflow.html` (or `_specflow.html` if Markdown-like)

#### Scenario: Output directory specified for .rs file
- **WHEN** user runs `codeflow analyze example.rs --output-dir ./reports`
- **THEN** CodeFlow writes the HTML report to `./reports/example_codeflow.html`

#### Scenario: .rs file extension is recognized alongside .py and .md
- **WHEN** user is prompted to choose a file and enters a .rs path
- **THEN** CodeFlow recognizes .rs as a supported extension and analyzes it

### Requirement: Backward compatibility with Python and Markdown workflows
CodeFlow's existing Python and Markdown workflows SHALL remain unchanged; all new Rust functionality is additive.

#### Scenario: Existing Python analysis produces same output
- **WHEN** running CodeFlow on a Python file that was analyzed before the upgrade
- **THEN** the output (flowchart structure, node labels, edges) is identical

#### Scenario: Existing SPEC.md workflow unchanged
- **WHEN** analyzing a Markdown specification file (SPEC.md)
- **THEN** the flowchart import, Claude Code integration, and Word walkthrough features work as before

#### Scenario: Command-line interface remains compatible
- **WHEN** using the original `python -m codeflow analyze FILE` command
- **THEN** it continues to work without modification for .py and .md files

### Requirement: Rust parser uses tree-sitter for robust grammar-based parsing
CodeFlow's Rust analyzer SHALL use tree-sitter with the tree-sitter-rust grammar for parsing instead of ad hoc regex or manual parsing.

#### Scenario: Parser dependency availability
- **WHEN** CodeFlow initializes the Rust analyzer
- **THEN** it loads tree-sitter and the Rust language grammar; if either is unavailable, CodeFlow reports a configuration error with guidance on installation

#### Scenario: Graceful handling of unsupported constructs
- **WHEN** the Rust parser encounters unsupported constructs (macros, closures with captures, async/await, complex generics)
- **THEN** it identifies them (via tree-sitter parse errors or specific node types), logs a degradation flag with line number, and continues parsing the rest of the file

#### Scenario: Parse results include ambiguity flags
- **WHEN** a Rust file is analyzed
- **THEN** the `AnalysisResult.ambiguity_flags` list documents all unsupported or uncertain constructs (e.g., "Line 42: macro_invocation (not fully analyzed)")

#### Scenario: Version consistency
- **WHEN** CodeFlow is deployed or updated
- **THEN** tree-sitter and tree-sitter-rust versions are pinned in dependencies to ensure reproducible parsing across environments
