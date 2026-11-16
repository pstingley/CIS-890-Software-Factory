# Spec Delta: PHP Documentation Generation

## Purpose

Provides optional human-readable documentation generation for PHP source code and projects, translating PHP control flow, exception handling, and multi-file relationships into clear prose (Markdown or Word format).

## ADDED Requirements

### Requirement: Generate narrative documentation for PHP implementations
CodeFlow SHALL accept PHP source (single-file or multi-file project) and produce optional human-readable documentation (Markdown or Word) explaining the control flow logic, PHP-specific patterns, and relationships.

#### Scenario: Single-file PHP documentation
- **WHEN** user requests documentation for a single PHP file containing functions and classes
- **THEN** CodeFlow generates a Markdown or Word document that:
  - Describes the purpose and structure of the file (namespace, classes, main functions)
  - Explains the control flow for each function/method in plain English
  - Notes exception handling patterns (try/catch/finally)
  - Describes method dependencies and call sequences

#### Scenario: Multi-file PHP project documentation
- **WHEN** user requests documentation for a PHP project with multiple files and entry points
- **THEN** CodeFlow generates documentation that:
  - Describes the overall project structure and entry points
  - Explains the relationships between files (include/require, autoloading, cross-file calls)
  - For each significant file or class: describes its role, control flow, and interactions
  - Flags framework dependencies, dynamic dispatch, and unresolved calls

#### Scenario: Documentation includes static analysis results
- **WHEN** generating documentation
- **THEN** the output includes:
  - Callstack and execution paths identified from static analysis
  - Notes on exception-handling patterns (which exceptions are caught, where)
  - Descriptions of conditionals and loops (what they guard, loop iteration behavior)
  - Lists of flagged dynamic constructs and unresolved calls
  - Warnings about incomplete analysis due to dynamic behavior

### Requirement: PHP-specific pattern translation in documentation
CodeFlow's documentation generator SHALL recognize common PHP patterns and explain them clearly in generated prose.

#### Scenario: Exception handling patterns
- **WHEN** generating documentation for code using try/catch/finally
- **THEN** the documentation explains:
  - Which exceptions are caught and by which handlers
  - What finally blocks always execute (cleanup, logging, etc.)
  - Which exceptions propagate uncaught and their impact

#### Scenario: Namespace and autoloading patterns
- **WHEN** generating documentation for a project with PSR-4 autoloading and namespaced classes
- **THEN** the documentation explains:
  - The namespace structure and how it maps to file locations
  - How classes are discovered and instantiated via autoloading
  - The role of Composer configuration in file discovery

#### Scenario: Magic method explanation
- **WHEN** documentation encounters magic methods (__construct, __call, __get, etc.)
- **THEN** the documentation explains:
  - When each magic method is automatically invoked
  - What parameters they receive and what they should return
  - How they affect class instantiation or method resolution

#### Scenario: Static vs. instance method distinction
- **WHEN** generating documentation for a class with both static and instance methods
- **THEN** the documentation clearly distinguishes:
  - Which methods require class instantiation
  - Which methods can be called directly on the class
  - How they interact (static initialization patterns, factory methods, etc.)

### Requirement: Optional Claude Code integration with graceful fallback
CodeFlow's documentation generator SHALL attempt to integrate with Claude Code (if available) to generate rich narratives, with a clearly-labeled fallback for environments where Claude Code is unavailable.

#### Scenario: Documentation with Claude Code available
- **WHEN** Claude Code integration is available and enabled
- **THEN** CodeFlow:
  - Sends the CFG and source analysis to Claude Code
  - Receives a rich narrative explaining the control flow in plain English
  - Integrates the narrative into the Markdown or Word document
  - Labels the narrative as "Generated with Claude Code analysis"

#### Scenario: Documentation without Claude Code
- **WHEN** Claude Code is unavailable or integration is disabled
- **THEN** CodeFlow:
  - Generates a statistics-based summary from the CFG and source annotations
  - Includes counts of functions, classes, loops, exceptions, and dynamic constructs
  - Lists entry points and significant code sections
  - Labels the summary as "Statistics-based summary (Claude Code integration unavailable)"
  - Is explicit that manual review recommended for complete understanding

#### Scenario: Partial Claude Code integration
- **WHEN** Claude Code integration fails or times out for a large file
- **THEN** CodeFlow:
  - Falls back to statistics-based summary
  - Logs a warning: "Claude Code integration failed; using statistics-based summary"
  - Includes both attempted narrative (if partial) and fallback summary
  - Flags the limitation in the document

### Requirement: Word output support (python-docx)
CodeFlow's documentation generator SHALL support optional Word (.docx) output, with graceful fallback to Markdown if python-docx is unavailable.

#### Scenario: Word output with python-docx available
- **WHEN** user requests Word documentation and python-docx is installed
- **THEN** CodeFlow generates a .docx file with:
  - Formatted headings (title, sections, subsections)
  - Embedded diagrams (CFG flowchart as an image)
  - Code snippets with syntax highlighting
  - Tables for cross-file relationships or call graphs
  - Properly formatted prose narrative

#### Scenario: Word output with python-docx unavailable
- **WHEN** user requests Word documentation but python-docx is not installed
- **THEN** CodeFlow:
  - Logs a warning: "python-docx not available; generating Markdown instead"
  - Generates a Markdown file with equivalent content
  - Includes a note in the output: "Word format unavailable; Markdown provided"

#### Scenario: Markdown output (default)
- **WHEN** user requests Markdown documentation (or no format specified)
- **THEN** CodeFlow generates a .md file with:
  - Markdown headings and formatting
  - Embedded code blocks
  - Callout boxes for warnings or important notes
  - Tables for structured information
  - Links between sections (table of contents)

### Requirement: Distinguish specification intent from implementation notes
CodeFlow's documentation SHALL clearly separate what the code does from how it deviates from or supplements a specification.

#### Scenario: Specification and implementation comparison
- **WHEN** documentation is generated for both a SPEC.md specification and a PHP implementation
- **THEN** the documentation includes:
  - A section on "Specification Intent" (from SPEC.md)
  - A section on "Implementation" (from PHP source)
  - A "Relationship" section noting alignment or divergence
  - Flags for paths in the specification not covered by the implementation

#### Scenario: Implementation-only documentation
- **WHEN** documentation is generated for PHP code without a corresponding specification
- **THEN** the documentation clearly states:
  - "No specification provided; this describes the implementation behavior as written"
  - Analysis is based on static code review only
  - Actual runtime behavior may differ due to dynamic constructs

### Requirement: CLI support for documentation generation
CodeFlow's command-line interface SHALL provide a flag to request documentation output alongside or instead of flowchart generation.

#### Scenario: User requests documentation alongside flowchart
- **WHEN** user runs `codeflow analyze example.php --generate-docs --format=markdown`
- **THEN** CodeFlow generates:
  - A flowchart HTML report (default)
  - A documentation Markdown file (requested)
  - Both files in the output directory

#### Scenario: User requests documentation only
- **WHEN** user runs `codeflow analyze example.php --docs-only --format=word`
- **THEN** CodeFlow generates only the Word documentation file, skipping flowchart generation

#### Scenario: Documentation for multi-file project
- **WHEN** user runs `codeflow analyze project_dir --type=project --generate-docs --format=markdown`
- **THEN** CodeFlow generates:
  - Project overview documentation
  - Per-file documentation (or combined)
  - Cross-file relationship diagrams or descriptions
  - All in the requested format

### Requirement: Documentation includes ambiguity and incompleteness flags
CodeFlow's documentation SHALL prominently flag analysis limitations, dynamic constructs, and unresolved references.

#### Scenario: Documentation with flagged unresolved calls
- **WHEN** generating documentation for a file with dynamic includes or reflection
- **THEN** the documentation includes:
  - A "Limitations" or "Warnings" section
  - Lists of flagged dynamic constructs with line numbers
  - Explanations of why the construct could not be statically analyzed
  - Advice on manual review

#### Scenario: Documentation with incomplete analysis
- **WHEN** generating documentation where `analysis_incomplete = True`
- **THEN** the document includes:
  - A prominent warning at the beginning: "⚠️ This analysis is incomplete. See Limitations section."
  - A "Limitations" section with the full list of ambiguity flags
  - Recommendations for manual code review or runtime inspection

### Requirement: Markdown and Word documents are platform-independent
CodeFlow's documentation output SHALL be platform-independent and renderable across all major platforms (Windows, macOS, Linux).

#### Scenario: Markdown documentation rendering
- **WHEN** a Markdown document is generated
- **THEN** it is compatible with standard Markdown renderers (GitHub, pandoc, VS Code, etc.)

#### Scenario: Word documentation rendering
- **WHEN** a Word document is generated
- **THEN** it opens correctly in Microsoft Word, LibreOffice, Google Docs, and other .docx-compatible readers

### Requirement: Documentation generation preserves source traceability
CodeFlow's documentation SHALL reference source locations (file paths, line numbers) for all analyzed code elements.

#### Scenario: Function references include file and line
- **WHEN** documentation describes a function or method
- **THEN** it includes:
  - The function/method name
  - The containing file and line number (clickable or formatted as reference)
  - The namespace or class (if applicable)

#### Scenario: Cross-file calls are traced
- **WHEN** documentation describes a call to a function in another file
- **THEN** it notes:
  - The calling file and line
  - The called function and its file and line
  - The relationship (include, autoload, namespace resolution, etc.)
