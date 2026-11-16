# Spec Delta: Python Documentation

## Purpose

Provides optional human-readable documentation generation for Python implementations, explaining control flow logic in plain English suitable for stakeholders unfamiliar with the code, covering normal paths, decision points, error handling, and exit conditions.

## ADDED Requirements

### Requirement: Generate plain-English documentation from Python source
CodeFlow SHALL analyze Python source files and produce optional human-readable documentation describing the function's behavior.

#### Scenario: User requests Python documentation
- **WHEN** user runs `codeflow analyze example.py --prose` (or answers Yes to prose prompt)
- **THEN** CodeFlow generates `example_Python_Walkthrough.docx` in addition to the flowchart

#### Scenario: Documentation follows flowchart coverage
- **WHEN** documentation is generated for a Python function
- **THEN** the documentation describes the same control flow paths shown in the flowchart (normal path, branches, loops, returns)

#### Scenario: Documentation is optional
- **WHEN** user runs `codeflow analyze example.py --no-prose`
- **THEN** CodeFlow generates only the flowchart, no Word document

### Requirement: Documentation explains normal execution paths
CodeFlow's Python documentation SHALL describe the primary (happy path) execution sequence in plain English.

#### Scenario: Linear function documented
- **WHEN** generating documentation for a function with no branches or loops
- **THEN** the documentation reads as a sequential narrative: "The function begins by X, then Y, then returns Z"

#### Scenario: Function with early return
- **WHEN** a function has an early return condition (e.g., validation check)
- **THEN** the documentation explains both the early exit case and the normal continuation path

#### Scenario: Multiple independent paths
- **WHEN** a function has several distinct execution paths (if/elif/else)
- **THEN** the documentation describes each path separately with clear trigger conditions

### Requirement: Documentation explains decision points and branching
CodeFlow's Python documentation SHALL clearly describe conditions that determine which code path executes.

#### Scenario: Simple if statement
- **WHEN** documenting a function with `if condition: ... else: ...`
- **THEN** the documentation explains "When condition is true, X happens. Otherwise, Y happens."

#### Scenario: Complex conditional
- **WHEN** documenting nested conditions or compound boolean logic
- **THEN** the documentation breaks down each condition and shows how branches combine

#### Scenario: Loop conditions
- **WHEN** a function contains loops (for, while)
- **THEN** the documentation explains the loop condition, what happens per iteration, and the exit condition

### Requirement: Documentation describes error handling
CodeFlow's Python documentation SHALL explain exception handling and error paths.

#### Scenario: Try/except block
- **WHEN** documenting code with try/except
- **THEN** the documentation explains which operations might raise exceptions and how exceptions are handled

#### Scenario: Multiple exception types
- **WHEN** code catches different exception types separately
- **THEN** the documentation distinguishes between each exception's handling

#### Scenario: Unhandled exceptions
- **WHEN** a function can raise exceptions that are not caught
- **THEN** the documentation flags these as potential exit points with warnings

### Requirement: Documentation format is readable prose
CodeFlow's Python documentation SHALL use clear, concise English without code-like syntax or symbols.

#### Scenario: Plain language descriptions
- **WHEN** documentation is written
- **THEN** it avoids code snippets, variable names used as nouns without context, and other programmer-centric notation

#### Scenario: Accessible to non-programmers
- **WHEN** a stakeholder reads the documentation
- **THEN** they can understand the behavior without knowledge of Python syntax

#### Scenario: Organized with clear sections
- **WHEN** documentation covers multiple aspects (normal path, decision points, error handling)
- **THEN** it is organized into clearly labeled sections (e.g., "Normal Execution", "Error Cases", "Special Conditions")

### Requirement: Documentation output is a Word (.docx) file
CodeFlow's Python documentation output SHALL be a Microsoft Word document, compatible with standard Office software.

#### Scenario: File format verification
- **WHEN** documentation is generated
- **THEN** the output file has a .docx extension and is readable by Microsoft Word and compatible applications

#### Scenario: Document structure
- **WHEN** opening the .docx file
- **THEN** it contains a title, introduction, sectioned prose content, and a source citation

#### Scenario: No markdown or HTML in output
- **WHEN** examining the Word document content
- **THEN** it contains only formatted text, headings, and paragraphs—no Markdown syntax or HTML tags

### Requirement: Python documentation supports Claude Code integration with explicit fallback labeling
CodeFlow's Python documentation generation SHALL use Claude Code to generate narrative content. When Claude Code is unavailable, CodeFlow SHALL generate a statistics-based fallback and **clearly label the output to distinguish between full AI-generated narrative and statistics-based fallback**.

#### Scenario: Claude Code available - AI-generated narrative
- **WHEN** Claude Code is available and documentation generation is requested
- **THEN** it produces fluent, well-organized narrative prose describing function behavior
- **AND** the documentation is labeled: **"AI-Generated Narrative"** (in title or prominent header)

#### Scenario: Claude Code unavailable - Statistics-based fallback
- **WHEN** generating Python documentation but Claude Code is unavailable
- **THEN** CodeFlow:
  - Generates a statistics-based summary (node count, branch count, loops, exception paths)
  - **Labels the output clearly: "Statistics-Based Summary (Full AI Generation Unavailable)"** (in title or prominent header)
  - Includes explanation: "This summary was generated from control flow structure only; human review of source code is recommended for complete understanding"
  - Never silently substitutes statistics for full narrative without explicit labeling

#### Scenario: Consistent labeling and integration
- **WHEN** comparing Python documentation with Rust or SPEC.md documentation
- **THEN** the same labeling rules apply to all input types for consistency
  - Claude Code available → "AI-Generated Narrative"
  - Claude Code unavailable → "Statistics-Based Summary (Full AI Generation Unavailable)"
