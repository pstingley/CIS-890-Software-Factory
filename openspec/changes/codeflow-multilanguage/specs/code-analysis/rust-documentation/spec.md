# Spec Delta: Rust Documentation

## Purpose

Provides optional human-readable documentation generation for Rust implementations, explaining control flow logic, error handling patterns, and asynchronous or safety-critical behavior in plain English, suitable for reviewers and maintainers unfamiliar with the Rust codebase.

## ADDED Requirements

### Requirement: Generate plain-English documentation from Rust source
CodeFlow SHALL analyze Rust source files and produce optional human-readable documentation describing the function's behavior, particularly control flow decisions and error handling.

#### Scenario: User requests Rust documentation
- **WHEN** user runs `codeflow analyze example.rs --prose` (or answers Yes to prose prompt)
- **THEN** CodeFlow generates `example_Rust_Walkthrough.docx` in addition to the flowchart

#### Scenario: Documentation aligns with flowchart
- **WHEN** documentation is generated for a Rust function
- **THEN** the documentation describes the same control flow paths shown in the flowchart (match arms, loops, error paths via ?)

#### Scenario: Documentation explains Rust-specific patterns
- **WHEN** documenting Rust code with match expressions and error propagation
- **THEN** the documentation translates these idiomatic patterns into plain English (e.g., "If the operation succeeds, X. If it fails, the error is returned immediately.")

### Requirement: Documentation explains match expressions
CodeFlow's Rust documentation SHALL translate `match` expressions into clear decision narratives.

#### Scenario: Simple match on enum
- **WHEN** documenting `match option { Some(x) => ..., None => ... }`
- **THEN** the documentation reads: "If the value is Some, [action]. If it is None, [action]."

#### Scenario: Match with multiple patterns
- **WHEN** documenting `match value { Pattern1 => ..., Pattern2 => ..., _ => ... }`
- **THEN** the documentation explains each pattern match case and the default case separately

#### Scenario: Match with guards
- **WHEN** documenting `match value { x if x > 0 => ..., _ => ... }`
- **THEN** the documentation clearly explains the guard condition: "If the value matches the pattern AND the condition is true..."

### Requirement: Documentation explains error propagation and Result handling
CodeFlow's Rust documentation SHALL describe how Rust's Result type and `?` operator handle errors.

#### Scenario: Function returning Result
- **WHEN** documenting a function that returns `Result<T, E>`
- **THEN** the documentation explains that the function can succeed (returning Ok) or fail (returning Err)

#### Scenario: ? operator chain
- **WHEN** documenting `first()?.second()?.third()?`
- **THEN** the documentation explains: "Each operation can succeed or fail immediately. If any operation fails, the error is returned to the caller."

#### Scenario: Explicit error handling vs propagation
- **WHEN** documenting code with both explicit match on Result and `?` operator
- **THEN** the documentation distinguishes between locally-handled errors and propagated errors

#### Scenario: Option pattern matching
- **WHEN** documenting `if let Some(x) = option { ... }`
- **THEN** the documentation explains the Some/None distinction and what happens in each case

### Requirement: Documentation describes loop control in Rust
CodeFlow's Rust documentation SHALL explain loops, including Rust-specific patterns like labeled breaks and continue.

#### Scenario: For loop iteration
- **WHEN** documenting `for item in collection { ... }`
- **THEN** the documentation explains iteration: "For each item in the collection, [action is performed]."

#### Scenario: While loop condition
- **WHEN** documenting `while condition { ... }`
- **THEN** the documentation explains: "The loop continues while condition is true. When condition becomes false, the loop exits."

#### Scenario: Loop with break and continue
- **WHEN** documenting a loop with `break` and `continue` statements
- **THEN** the documentation explains what triggers early exit and what causes skipping to the next iteration

#### Scenario: Labeled loops
- **WHEN** documenting `'outer: loop { ... break 'outer; }`
- **THEN** the documentation explains which loop is exited by the labeled break

### Requirement: Documentation flags Rust-specific limitations and idioms
CodeFlow's Rust documentation SHALL highlight patterns and constructs that may not be familiar to non-Rust readers.

#### Scenario: Ownership and borrowing
- **WHEN** documenting functions with ownership transfer or borrowing
- **THEN** the documentation flags significant ownership patterns (e.g., "The function takes ownership of X" or "X is borrowed immutably")

#### Scenario: Unsafe code blocks
- **WHEN** a function contains `unsafe { ... }` blocks
- **THEN** the documentation highlights unsafe code as a notable concern with explanation of why it is marked unsafe

#### Scenario: Trait objects and generics
- **WHEN** functions use trait objects or complex generics
- **THEN** the documentation simplifies explanation (e.g., "Accepts any type implementing Trait") without assuming reader knows Rust generics syntax

#### Scenario: Lifetimes annotation
- **WHEN** functions have explicit lifetime parameters
- **THEN** the documentation provides context (e.g., "The returned reference is valid as long as the input reference") in plain language

### Requirement: Documentation output is a Word (.docx) file
CodeFlow's Rust documentation output SHALL be a Microsoft Word document, compatible with standard Office software.

#### Scenario: File format for Rust analysis
- **WHEN** Rust documentation is generated
- **THEN** the output file has a .docx extension and is readable by Microsoft Word

#### Scenario: Document structure for Rust
- **WHEN** opening the Rust Walkthrough document
- **THEN** it contains a title, introduction, sectioned prose content covering normal flow, error handling, and special cases, plus a source citation

#### Scenario: Consistent format with Python documentation
- **WHEN** comparing a Rust documentation file with a Python documentation file
- **THEN** both follow the same document structure (title, sections, prose, citation) for consistency

### Requirement: Rust documentation supports Claude Code integration with explicit fallback labeling
CodeFlow's Rust documentation generation SHALL use Claude Code to generate narrative content. When Claude Code is unavailable, CodeFlow SHALL generate a statistics-based fallback and **clearly label the output to distinguish between full AI-generated narrative and statistics-based fallback**.

#### Scenario: Claude Code available - AI-generated narrative
- **WHEN** Claude Code is available and documentation generation is requested
- **THEN** it produces fluent, well-organized narrative prose describing function behavior
- **AND** the documentation is labeled: **"AI-Generated Narrative"** (in title or prominent header)

#### Scenario: Claude Code unavailable - Statistics-based fallback
- **WHEN** generating Rust documentation but Claude Code is unavailable
- **THEN** CodeFlow:
  - Generates a statistics-based summary (function signature, node count, branches, loops, error handling paths)
  - **Labels the output clearly: "Statistics-Based Summary (Full AI Generation Unavailable)"** (in title or prominent header)
  - Includes explanation: "This summary was generated from control flow structure only; human review of source code is recommended for complete understanding of Rust-specific patterns"
  - Never silently substitutes statistics for full narrative without explicit labeling

#### Scenario: Consistent labeling across all languages
- **WHEN** comparing Rust documentation with Python or SPEC.md documentation
- **THEN** the same labeling rules apply to all input types
  - Claude Code available → "AI-Generated Narrative"
  - Claude Code unavailable → "Statistics-Based Summary (Full AI Generation Unavailable)"
