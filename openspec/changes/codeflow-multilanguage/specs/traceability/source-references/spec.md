# Spec Delta: Source Traceability

## Purpose

Establishes mechanisms for tracking and displaying the source location (file path, line numbers, specification section IDs) of each control-flow node across Python, Rust, and Markdown specifications, enabling users to navigate from the flowchart back to source code or specification sections for verification and review.

## ADDED Requirements

### Requirement: Python analyzer populates source references
CodeFlow's Python analyzer SHALL record the source file path and line number for each CFG node representing identifiable code constructs.

#### Scenario: Statement node with source reference
- **WHEN** parsing a Python statement (assignment, function call, return)
- **THEN** the corresponding CFG node includes source reference: (file_path, line_number)

#### Scenario: Control flow node with source reference
- **WHEN** parsing an if, for, while, or try statement
- **THEN** the CFG node includes the line number of the control structure

#### Scenario: Function entry and exit nodes
- **WHEN** parsing a function definition and its body
- **THEN** entry node references the function definition line; exit node is implicit (end of function or return statement line)

#### Scenario: Exception path reference
- **WHEN** parsing exception handling (try/except)
- **THEN** exception-path CFG nodes reference the line with the risky operation and the corresponding except line

### Requirement: Rust analyzer populates source references
CodeFlow's Rust analyzer SHALL record the source file path and line number for each CFG node, using tree-sitter's position information.

#### Scenario: Rust statement node with source reference
- **WHEN** parsing a Rust statement (let binding, assignment, function call)
- **THEN** the corresponding CFG node includes source reference: (file_path, line_number) from tree-sitter node position

#### Scenario: Rust control flow node with source reference
- **WHEN** parsing a Rust if, match, for, or while construct
- **THEN** the CFG node includes the starting line number from tree-sitter

#### Scenario: Match arm references
- **WHEN** parsing a match expression with multiple arms
- **THEN** each arm's CFG node includes the starting line number of that arm

#### Scenario: Error propagation references
- **WHEN** parsing Rust's `?` operator
- **THEN** the exception-path CFG node references the line containing the `?` operator

### Requirement: Specification analyzer populates source references with section IDs
CodeFlow's Markdown specification analyzer SHALL record section identifiers and line references for flowchart nodes.

#### Scenario: Specification node with section reference
- **WHEN** the SPEC.md file includes requirement IDs or section markers (e.g., "§7.1" or "[REQ-42]")
- **THEN** CFG nodes derived from those sections include the reference ID

#### Scenario: Specification paragraph reference
- **WHEN** a flowchart node is generated from a specific paragraph or requirement in SPEC.md
- **THEN** the node includes the paragraph line number (useful for scrolling to source in editor)

#### Scenario: Imported flowchart with source mapping
- **WHEN** SPEC.md contains an embedded flowchart (as diagram or image)
- **THEN** nodes in the imported flowchart, if parseable, are mapped to the corresponding lines in SPEC.md

### Requirement: AnalysisResult includes source references collection
CodeFlow's `AnalysisResult` class SHALL include a `source_references` field for storing and retrieving node-to-source mappings.

#### Scenario: Data structure for traceability
- **WHEN** an analyzer completes
- **THEN** the returned `AnalysisResult` includes: `source_references: Dict[str, Tuple[str, int]]` where keys are CFG node IDs and values are (file_path, line_number)

#### Scenario: Optional specification references
- **WHEN** the AnalysisResult is for a Markdown specification
- **THEN** the source_references may include section IDs alongside line numbers (e.g., "§7.1@line_42")

#### Scenario: Ambiguity flags for uncertain references
- **WHEN** a node's source location is uncertain or inferred
- **THEN** the node is flagged in the `ambiguity_flags` list with reason (e.g., "Derived from Claude Code; actual line not found in source")

### Requirement: HTML report displays source references
CodeFlow's HTML flowchart report SHALL display source location information for each node, enabling quick navigation to source.

#### Scenario: Node tooltip shows source location
- **WHEN** hovering over a CFG node in the HTML flowchart
- **THEN** a tooltip appears displaying the source file path and line number

#### Scenario: Python example: node details
- **WHEN** clicking a node in a Python flowchart
- **THEN** a sidebar or modal shows: Source file, Line number, Source code excerpt (first ~50 characters)

#### Scenario: Rust example: node details with tree-sitter info
- **WHEN** clicking a node in a Rust flowchart
- **THEN** the details panel shows: Source file, Line number (from tree-sitter), Source code snippet (abbreviated)

#### Scenario: Specification example: node details with section reference
- **WHEN** clicking a node in a specification flowchart
- **THEN** the details show: Section ID (if present), Line number in SPEC.md, Text excerpt from that section

#### Scenario: Clickable source navigation (optional)
- **WHEN** user clicks "Go to source" on a node (optional feature)
- **THEN** if running in an IDE or editor, the corresponding file opens at the referenced line

### Requirement: JSON export includes full source references
CodeFlow's JSON export of analysis results SHALL include complete source reference information.

#### Scenario: JSON CFG export with references
- **WHEN** exporting a flowchart to JSON format
- **THEN** each node includes: `{ id, type, label, source_references: { file_path, line_number } }`

#### Scenario: JSON comparison export with source mappings
- **WHEN** exporting a comparison report to JSON
- **THEN** aligned nodes show source references from both sources, enabling external tools to build cross-references

### Requirement: Source references are validated and reported
CodeFlow's analyzers SHALL validate that recorded source references are accurate and report anomalies.

#### Scenario: Validation on analyzer completion
- **WHEN** an analyzer finishes and populates source_references
- **THEN** it validates that line numbers are within the source file bounds (not negative, not beyond EOF)

#### Scenario: Report mismatches
- **WHEN** source reference validation detects an out-of-bounds line number
- **THEN** the anomaly is flagged in ambiguity_flags with explanation: "Line number exceeds source file length; likely parser error"

#### Scenario: Graceful degradation
- **WHEN** source references cannot be accurately determined for part of the code
- **THEN** those nodes include best-effort references and are flagged; analysis continues without failing

### Requirement: Backward compatibility with non-reference versions
CodeFlow's flowchart rendering and analysis SHALL work even if source references are absent or incomplete (for legacy code or unsupported constructs).

#### Scenario: Flowchart displays without source references
- **WHEN** an old Python file (analyzed before source traceability was added) is re-analyzed
- **THEN** the flowchart still displays correctly; nodes simply do not show source location details

#### Scenario: Graceful fallback
- **WHEN** rendering an unsupported construct that lacks source reference
- **THEN** the flowchart node displays with generic label (e.g., "Unsupported construct") and no source details

### Requirement: Performance does not degrade with source reference tracking
CodeFlow's analysis and rendering performance SHALL remain acceptable even with source reference collection.

#### Scenario: Large file analysis
- **WHEN** analyzing a large Python or Rust file with 100+ functions
- **THEN** source reference collection adds minimal overhead (<5% time penalty)

#### Scenario: HTML report generation
- **WHEN** generating an HTML report with source references
- **THEN** the report renders quickly; source reference data is included without bloating the file size excessively
