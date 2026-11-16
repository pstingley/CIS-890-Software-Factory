# Spec Delta: Cross-Language Comparison

## Purpose

Enables optional side-by-side comparison and traceability between flowcharts derived from specifications, Python implementations, and Rust implementations, allowing developers to identify alignment or divergence between intended behavior and actual code paths.

## ADDED Requirements

### Requirement: CLI supports comparison mode for multiple files
CodeFlow SHALL accept an optional comparison flag to analyze multiple source files (spec + implementations) and produce a comparative report.

#### Scenario: Compare spec with Python implementation
- **WHEN** user runs `codeflow compare SPEC.md tictactoe.py`
- **THEN** CodeFlow generates a comparison report showing both flowcharts and alignment analysis

#### Scenario: Compare Python and Rust implementations
- **WHEN** user runs `codeflow compare tictactoe.py tictactoe.rs`
- **THEN** CodeFlow generates a comparison report highlighting similarities and differences

#### Scenario: Three-way comparison (spec + Python + Rust)
- **WHEN** user runs `codeflow compare SPEC.md tictactoe.py tictactoe.rs`
- **THEN** CodeFlow generates a three-way comparison showing all three sources and their relationships

### Requirement: Comparison report shows side-by-side flowcharts
CodeFlow's comparison report SHALL display flowcharts from multiple sources in a readable layout (side-by-side or tabbed).

#### Scenario: Two flowcharts displayed together
- **WHEN** comparing two sources
- **THEN** the HTML report shows both flowcharts visible simultaneously, allowing visual comparison

#### Scenario: Three flowcharts with navigation
- **WHEN** comparing three sources
- **THEN** the report uses tabs or accordion sections to navigate between sources while keeping alignment markers visible

#### Scenario: Flowcharts are independently interactive
- **WHEN** clicking a node in one flowchart
- **THEN** that node is highlighted in its flowchart, and any corresponding node in other flowcharts is also highlighted (if alignment is tracked)

### Requirement: Comparison identifies matching execution paths
CodeFlow SHALL attempt to match equivalent paths across implementations and specifications, marking them as corresponding.

#### Scenario: Both implementations follow the spec
- **WHEN** a Python and Rust implementation both follow the same control flow as the specification
- **THEN** corresponding nodes are visually linked (e.g., with color coding, connecting lines, or labels)

#### Scenario: One implementation diverges
- **WHEN** a Python implementation has an extra decision or path not in the specification
- **THEN** that path is marked as "divergence from spec" with a warning or highlight

#### Scenario: Both implementations diverge in different ways
- **WHEN** Python and Rust implementations differ from each other and the specification
- **THEN** each divergence is noted, and the comparison report flags discrepancies

### Requirement: Comparison report includes alignment summary
CodeFlow's comparison report SHALL include a summary section quantifying coverage and divergence.

#### Scenario: Coverage percentage
- **WHEN** viewing comparison summary
- **THEN** it displays "80% of spec paths are covered by both implementations" or similar metric

#### Scenario: Divergence list
- **WHEN** implementations differ from the specification
- **THEN** a list of divergences is provided with location information (line number or node reference)

#### Scenario: Missing implementation paths
- **WHEN** the specification describes a path not present in either implementation
- **THEN** the report flags missing or incomplete implementation paths

### Requirement: Comparison supports source traceability
CodeFlow SHALL provide line numbers or source references for each node, enabling developers to locate corresponding code.

#### Scenario: Node references spec section
- **WHEN** a specification flowchart node has a source reference (e.g., "§7.1")
- **THEN** the comparison report shows this reference, and implementations can cross-reference it

#### Scenario: Python node shows line number
- **WHEN** a Python flowchart node represents a specific function or statement
- **THEN** the node label includes the line number (e.g., "Line 42: Check condition")

#### Scenario: Rust node shows line number
- **WHEN** a Rust flowchart node represents a specific function or statement
- **THEN** the node label includes the line number for easy lookup in the source file

#### Scenario: Click-through to source
- **WHEN** user clicks a node in the comparison report (optional feature)
- **THEN** the source file opens (if available in the IDE or browser environment) at the corresponding line

### Requirement: Comparison report is exportable
CodeFlow's comparison analysis result SHALL be exportable for archiving and sharing.

#### Scenario: HTML export includes full comparison
- **WHEN** generating a comparison report
- **THEN** the HTML file is self-contained and can be saved, shared, and viewed offline

#### Scenario: JSON export of comparison data
- **WHEN** user requests JSON export of comparison results
- **THEN** CodeFlow produces a JSON file with both flowcharts, alignment data, and metadata

#### Scenario: Report filename reflects comparison
- **WHEN** generating a comparison of SPEC.md and tictactoe.py
- **THEN** the output file is named something like `tictactoe_comparison.html` or `tictactoe_spec_vs_py.html`

### Requirement: Comparison is optional; non-comparison workflow unchanged
CodeFlow's default single-file analysis workflow SHALL remain unchanged; comparison is an opt-in feature via CLI flag.

#### Scenario: Single file analysis unchanged
- **WHEN** user runs `codeflow analyze example.py`
- **THEN** CodeFlow generates a standard single-file flowchart report (no comparison)

#### Scenario: Comparison flag is explicit
- **WHEN** user does not provide a comparison flag
- **THEN** CodeFlow performs single-file analysis; comparison requires an explicit flag (e.g., `--compare` or `compare` subcommand)

#### Scenario: No performance impact without comparison
- **WHEN** running CodeFlow without comparison
- **THEN** there is no performance overhead from comparison infrastructure

### Requirement: Comparison handles missing files and partial analysis
CodeFlow's comparison feature SHALL degrade gracefully if one or more input files are unavailable or fail to parse.

#### Scenario: One file fails to parse
- **WHEN** attempting to compare SPEC.md, tictactoe.py, and tictactoe.rs, but tictactoe.rs fails to parse
- **THEN** CodeFlow generates a two-source comparison (SPEC and Python) and reports that Rust analysis failed with details

#### Scenario: Partial comparison report
- **WHEN** one source is unavailable
- **THEN** the report shows flowcharts for available sources and notes the missing source with an explanation

#### Scenario: Alignment markers adapt
- **WHEN** comparing an incomplete set of sources
- **THEN** alignment markers and summary statistics reflect the available data (e.g., "Python matches spec; Rust analysis unavailable")
