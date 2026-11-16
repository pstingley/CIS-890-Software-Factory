# DOC-002: Human-Readable Semantic Documentation Specification

## ADDED Requirements

### Requirement: DOC-002-001 — Semantic Interpretation from Analysis

CodeFlow SHALL infer and explain the purpose, users, major capabilities, inputs, outputs, operational rules, and observable behavior of analyzed programs using evidence-based semantic interpretation.

#### Scenario: Terminal-based Tic-Tac-Toe analysis

- **WHEN** CodeFlow analyzes the Python Tic-Tac-Toe application
- **THEN** its semantic interpretation identifies: purpose (two-player terminal game), users (two human players using a terminal interface), major capabilities (board display, move validation, win detection), inputs (player moves via terminal), outputs (board state and game status to terminal)
- **AND** control flow analysis reveals turn alternation, win/draw detection logic, and game-loop structure

#### Scenario: Multi-function application interpretation

- **WHEN** CodeFlow analyzes an application with 20+ functions
- **THEN** semantic interpretation ranks functions by criticality, identifies primary workflows vs. auxiliary utilities, and distinguishes entry points from utility functions
- **AND** interpretation includes reasoning for each categorization based on CFG evidence

#### Scenario: Uncertain behavior marking

- **WHEN** CodeFlow encounters runtime-dependent behavior (file I/O, network calls, reflection)
- **THEN** semantic interpretation explicitly marks affected claims as "UNCERTAIN" with explanation of what cannot be statically determined
- **AND** documentation distinguishes verified facts, inferred behavior, and uncertain/dynamic behavior

---

### Requirement: DOC-002-002 — Functional Description Document

CodeFlow SHALL generate a Functional_Description.docx document written for managers, customers, and non-technical stakeholders, explaining purpose, users, capabilities, workflows, inputs, outputs, and constraints in plain English.

#### Scenario: Non-technical comprehension of Tic-Tac-Toe

- **WHEN** CodeFlow generates Functional_Description.docx for the Python Tic-Tac-Toe application
- **THEN** the document contains: (1) executive summary explaining it is a terminal-based game for two players, (2) purpose section identifying educational and entertainment use, (3) capabilities section listing board display, move input, win/draw detection, (4) inputs/outputs section explaining player moves and board display, (5) rules section describing turn alternation and winning conditions
- **AND** the document uses clear English with no CFG jargon, graph statistics, or control-flow terminology
- **AND** length is 5-15 pages appropriate to application complexity

#### Scenario: Avoidance of template repetition

- **WHEN** CodeFlow generates Functional_Description.docx for any application
- **THEN** the document explains what the software accomplishes, not what graph structure it contains
- **AND** sentences are substantive behavioral explanations, not template patterns like "This function contains 6 statement nodes"
- **AND** each major capability is explained in domain terminology with examples

#### Scenario: Supporting source evidence

- **WHEN** functional document makes a substantive claim about behavior
- **THEN** the claim is supported by either: (1) reference to specific source locations (file, function, lines), (2) explicit marking as an inference with reasoning, or (3) explicit marking as uncertain with explanation

---

### Requirement: DOC-002-003 — Technical Description Document

CodeFlow SHALL generate a Technical_Description.docx document for software engineers, explaining architecture, components, algorithms, control flow, data flow, exception handling, and performance characteristics with code references and control-flow evidence.

#### Scenario: Engineer comprehension of Tic-Tac-Toe architecture

- **WHEN** CodeFlow generates Technical_Description.docx for the Python Tic-Tac-Toe application
- **THEN** the document contains: (1) architecture section describing game-loop design, (2) component descriptions for major functions (display_board, validate_move, check_winner, etc.) with line numbers, (3) control-flow section tracing major execution paths from entry to game termination, (4) data-flow section explaining board representation and game-state transitions, (5) exception handling section detailing error recovery mechanisms
- **AND** technical document includes references to control-flow graph, HTML flowchart, and JSON analysis for interactive detail
- **AND** length is 8-20 pages with code line numbers, file paths, and algorithm descriptions

#### Scenario: Multi-language technical accuracy

- **WHEN** CodeFlow generates Technical_Description.docx for Rust or Python implementations of the same algorithm
- **THEN** both documents explain the same logical architecture and control flow, but adapted to the language's implementation patterns
- **AND** technical accuracy is verified against CFG analysis and source code review

#### Scenario: Truthful limitation documentation

- **WHEN** technical document describes an application feature
- **THEN** limitations section explicitly lists: (1) which language features are unsupported by CodeFlow, (2) which runtime behaviors cannot be statically determined, (3) which external dependencies are not analyzed, (4) what would require dynamic instrumentation to verify
- **AND** no functionality is invented or claimed without supporting evidence

---

### Requirement: DOC-002-004 — Evidence-Based Behavioral Claims

Every substantive behavioral claim in generated documentation SHALL have traceable source evidence or be explicitly categorized as inference, inferred pattern, or uncertain behavior with clear reasoning.

#### Scenario: Verified claim with source reference

- **WHEN** functional or technical document states "The application validates moves against board positions"
- **THEN** the claim includes evidence reference such as "validate_move function at lines 42-48 in tictactoe.py checks position boundaries and occupancy"
- **AND** the reference is verifiable against actual source code

#### Scenario: Inferred behavioral claim

- **WHEN** functional or technical document infers behavior not directly visible in source (e.g., "Players take turns")
- **THEN** the claim is explicitly marked as "INFERRED" or "Based on code analysis" with reasoning
- **AND** reasoning references CFG evidence such as "Loop structure at lines 20-35 alternates between player1 and player2 by toggling a turn variable"

#### Scenario: Uncertain runtime behavior

- **WHEN** semantic interpretation encounters behavior that depends on runtime conditions or external state
- **THEN** the documentation explicitly marks the claim as "UNCERTAIN" or "DYNAMIC" with explanation: "The application may interact with files or the network; this behavior is not statically analyzable"
- **AND** the limitation is documented without inventing how such behavior works

#### Scenario: Hierarchical evidence linking

- **WHEN** functional description claims a system-level capability
- **THEN** the technical description provides function-level evidence for how that capability is implemented
- **AND** both documents use consistent evidence references so claims are traceable across documents

---

### Requirement: DOC-002-005 — Behavioral Description, Not Source Recitation

Generated documentation SHALL describe actual behavior in domain terminology, not repeat source code expressions, function names, graph statistics, or control-flow jargon.

#### Scenario: Meaningful explanation of board display

- **WHEN** technical document describes the display_board function
- **THEN** the document explains: "The function renders the current 3×3 grid state, showing player marks (X and O) and empty positions, numbered 1-9 for player reference" (line 42-48)
- **AND** NOT: "The function contains 6 statement nodes and 1 decision node with 2 output edges"

#### Scenario: Workflow explanation, not control-flow jargon

- **WHEN** functional document describes game flow
- **THEN** the document explains: "The game proceeds through repeated turns: player makes a move, the application validates and applies it, checks for win/draw conditions, and switches players" (supported by loop at lines 20-35)
- **AND** NOT: "The loop has a termination condition evaluating two sub-conditions joined by an OR operator"

#### Scenario: Domain-based capability summary

- **WHEN** functional description lists capabilities
- **THEN** capabilities are expressed as "The application can: (1) display the board with current positions, (2) accept and validate player moves, (3) detect winning patterns, (4) identify draw conditions, (5) provide game status"
- **AND** NOT: "The code contains functions for board rendering, move processing, and state evaluation"

---

### Requirement: DOC-002-005a — Evidence-Based User and Purpose Documentation

CodeFlow SHALL NOT present inferred user demographics, organizational purpose, business intent, or use cases as verified facts unless explicitly supported by source-code evidence or supplied authoritative requirements. Unsubstantiated interpretations SHALL be labeled INFERRED or UNCERTAIN and SHALL NOT silently become requirements in SPEC.md.

#### Scenario: Verified user identification from source

- **WHEN** CodeFlow analyzes source code that explicitly establishes user types (e.g., main() function accepts specific command-line parameters or environment variables)
- **THEN** the documentation marks identified user types as VERIFIED with specific evidence reference
- **AND** example: "VERIFIED: The application accepts input from two separate terminal sessions (users). Evidence: input/output handling in lines 45-67 of main.py"

#### Scenario: Inferred user demographics marked as such

- **WHEN** CodeFlow's semantic interpretation infers that the application might serve "students" or "casual gamers" based on control flow, naming, or heuristics
- **THEN** the documentation marks this interpretation as INFERRED with explicit reasoning and evidence
- **AND** the inference is NOT included in SPEC.md as a requirement
- **AND** example: "INFERRED: Based on board game mechanics and simple validation logic, this application might serve educational or casual play contexts. Evidence: Tic-Tac-Toe game logic and turn-based flow."

#### Scenario: Unsubstantiated purpose excluded from final documentation

- **WHEN** CodeFlow's semantic interpretation cannot determine organizational purpose, business intent, or user demographics from source code alone
- **THEN** these unsubstantiated claims are either: (1) marked as UNCERTAIN with explicit explanation, (2) excluded from Functional_Description.docx entirely, or (3) presented as "purpose cannot be determined from code analysis"
- **AND** SPEC.md does not include unverified purpose or user demographic claims
- **AND** example NOT included: "This application is designed for use in educational settings" (without source evidence)

#### Scenario: Authoritative requirements override inference

- **WHEN** CodeFlow is provided authoritative requirements (e.g., procurement specification, design document) that describe intended users or business purpose
- **THEN** the documentation identifies which claims are from authoritative sources vs. inferred from code analysis
- **AND** both source types are distinguishable in the generated documents
- **AND** example: "AUTHORITATIVE: The system is intended for two human players. INFERRED: Players appear to use a terminal interface based on I/O code."

---

### Requirement: DOC-002-006 — Configurable LLM-Assisted Semantic Interpretation

CodeFlow SHALL use a pluggable, configurable LLM-assisted semantic interpretation system not hard-coded to any specific provider.

#### Scenario: Provider configuration via CLI

- **WHEN** user runs CodeFlow with `--semantic-provider claude --semantic-model claude-opus`
- **THEN** the semantic interpreter uses Claude's API for interpretation
- **AND** the same analysis generates consistent documentation quality

#### Scenario: Provider configuration via environment variable

- **WHEN** user sets `CODEFLOW_SEMANTIC_PROVIDER=gpt` and `CODEFLOW_SEMANTIC_MODEL=gpt-4`
- **THEN** semantic interpreter uses GPT-4 for interpretation
- **AND** no hard-coded provider dependencies are required

#### Scenario: Configuration file-based provider selection

- **WHEN** ~/.codeflow/config.yaml contains `semantic_interpreter.provider: local` with `endpoint: http://localhost:8000`
- **THEN** semantic interpreter connects to local LLM server
- **AND** configuration takes precedence over environment variables and defaults

#### Scenario: Graceful fallback to mock provider

- **WHEN** LLM provider is unavailable or user disables LLM to reduce costs
- **THEN** CodeFlow falls back to heuristic-based semantic interpretation using CFG analysis, function names, control-flow patterns, and documentation strings
- **AND** output is generated with reduced quality but no crashes or missing documentation

#### Scenario: Cost-aware operation

- **WHEN** user enables cost tracking with `--semantic-track-costs` and sets `--semantic-cost-threshold 10.0`
- **THEN** CodeFlow logs LLM API calls, token usage, and estimated costs
- **AND** warns user if daily costs approach threshold
- **AND** provides option to disable LLM-assisted interpretation for cost control

---

### Requirement: DOC-002-007 — Identification of Uncertain, Unsupported, and Dynamic Behavior

CodeFlow SHALL identify and explicitly document uncertain, unsupported, or dynamically determined behavior without inventing functionality or claiming false capabilities.

#### Scenario: Supported and analyzed behavior

- **WHEN** semantic documentation describes function behavior visible in source code (control flow, data transformations, function calls)
- **THEN** documentation marks claims as "VERIFIED" or supported by specific CFG evidence
- **AND** example: "✓ The application validates moves against board positions (verified in validate_move function at lines 42-48)"

#### Scenario: Supported but partial analysis

- **WHEN** CodeFlow recognizes constructs with analysis limitations (e.g., Rust macros, Python decorators with dynamic signatures)
- **THEN** documentation marks behavior as "PARTIAL" with explanation of limitation
- **AND** example: "~ The application may use external library calls; their internal behavior is not modeled (partial)"

#### Scenario: Unsupported constructs

- **WHEN** source code contains constructs CodeFlow does not analyze (reflection, code generation, eval)
- **THEN** documentation identifies the construct and marks behavior as "UNSUPPORTED"
- **AND** example: "✗ Dynamic code generation is used; the generated code is not statically analyzable (unsupported)"

#### Scenario: Dynamic and unanalyzable behavior

- **WHEN** behavior depends on runtime conditions, external state, or OS/network operations
- **THEN** documentation marks claims as "UNCERTAIN" or "DYNAMIC" with explanation
- **AND** example: "✗ The application may interact with files or network; this runtime behavior is not statically analyzable (dynamic)"

#### Scenario: Limitations section truthfulness

- **WHEN** technical or functional description concludes
- **THEN** a "Known Limitations" or "Analysis Limitations" section explicitly lists: (1) unsupported language features, (2) unanalyzable runtime behaviors, (3) external dependencies not modeled, (4) what would require instrumentation to verify
- **AND** limitations are stated without hedging; a reader can understand exactly what is not covered

---

### Requirement: DOC-002-008 — Language-Independent Specification Generation

CodeFlow SHALL generate language-independent SPEC.md derived from the same verified behavioral interpretation as functional and technical Word documents.

#### Scenario: Consistent behavioral specification

- **WHEN** CodeFlow generates documentation for a Python Tic-Tac-Toe application
- **THEN** the SPEC.md contains formal specification: input/output contracts, state transitions, winning/draw conditions, error cases
- **AND** SPEC.md references the same evidence used in Functional_Description.docx and Technical_Description.docx
- **AND** SPEC.md serves as the authoritative behavioral specification independent of Word documents

#### Scenario: Cross-language specification consistency

- **WHEN** SPEC.md is generated for Python, Rust, and PHP implementations of the same algorithm
- **THEN** each SPEC.md describes the same behavioral specification in language-independent terms
- **AND** implementation differences are noted but behavioral semantics are consistent

#### Scenario: Specification includes traceability

- **WHEN** SPEC.md describes a behavioral requirement or constraint
- **THEN** the requirement includes source-code traceability (file, function, line ranges) showing where the requirement is implemented
- **AND** example: "REQUIREMENT: Accept player move input within range 1-9. IMPLEMENTATION: validate_move (tictactoe.py, lines 42-48)"

---

### Requirement: DOC-002-009 — Source and PHP Input-Only Preservation

CodeFlow SHALL preserve analyzed source files byte-for-byte without modification and SHALL treat PHP as input-only.

#### Scenario: No source modification

- **WHEN** CodeFlow analyzes any source file (Python, Rust, PHP, etc.)
- **THEN** the original file is not modified, instrumented, wrapped, or changed in any way
- **AND** source file checksums remain identical before and after analysis

#### Scenario: PHP input-only analysis

- **WHEN** CodeFlow analyzes a PHP application
- **THEN** functional and technical documentation are generated describing PHP behavior
- **AND** no PHP source code is generated or modified
- **AND** PHP files are analyzed using the same multi-language infrastructure as Python and Rust

#### Scenario: Separate output files

- **WHEN** CodeFlow generates documentation for any source
- **THEN** all outputs (Functional_Description.docx, Technical_Description.docx, SPEC.md, control-flow graph, HTML flowchart, JSON analysis) are written to separate output files
- **AND** source directory is not modified

---

### Requirement: DOC-002-010 — Cross-Language Support Consistency

CodeFlow SHALL generate semantic documentation consistently for Python, Rust, and PHP with equivalent quality and functional content.

#### Scenario: Python Tic-Tac-Toe documentation

- **WHEN** CodeFlow analyzes Python Tic-Tac-Toe and generates DOC-002
- **THEN** output includes: Functional_Description.docx, Technical_Description.docx, SPEC.md, control-flow graphs, HTML flowcharts, JSON analysis
- **AND** documentation quality meets all acceptance criteria (FR-1 through FR-10)

#### Scenario: Rust Tic-Tac-Toe documentation

- **WHEN** CodeFlow analyzes Rust Tic-Tac-Toe and generates DOC-002
- **THEN** output includes: Functional_Description.docx, Technical_Description.docx, SPEC.md, control-flow graphs, HTML flowcharts, JSON analysis
- **AND** documentation quality is equivalent to Python output despite language differences
- **AND** technical documentation correctly describes Rust-specific patterns (ownership, error handling, pattern matching)

#### Scenario: PHP Tic-Tac-Toe documentation

- **WHEN** CodeFlow analyzes PHP Tic-Tac-Toe and generates DOC-002
- **THEN** output includes functional and technical documentation for PHP behavior (not generated PHP code)
- **AND** documentation explains PHP-specific constructs (global state, type juggling, untyped parameters) without inventing unsupported analysis
- **AND** limitations section identifies dynamic and unanalyzable PHP behavior (reflection, variable functions, eval)

#### Scenario: Multi-language project documentation

- **WHEN** CodeFlow analyzes a project with Python, Rust, and PHP files
- **THEN** each file is analyzed in its language using language-specific analyzers
- **AND** semantic interpretation works across all languages
- **AND** combined project documentation integrates behavior from all languages without duplication or inconsistency

---

### Requirement: DOC-002-011 — Non-Invasive Analysis Preservation

CodeFlow SHALL preserve non-invasive analysis requirement: acceptance of existing source without instrumentation, wrapper functions, or additional entry-point code.

#### Scenario: No instrumentation required

- **WHEN** user provides a source file or directory to CodeFlow
- **THEN** CodeFlow analyzes the existing code without requesting modifications, instrumentation, or wrapper code
- **AND** analysis proceeds via static control-flow and data-flow analysis

#### Scenario: Identification of entry points and utilities

- **WHEN** CodeFlow analyzes a Python application with main() and 15 utility functions
- **THEN** semantic interpretation identifies main() as the known entry point
- **AND** distinguishes main() from utility functions and helper methods
- **AND** handles applications without an obvious single entry point (libraries, frameworks)

#### Scenario: Existing static analysis preservation

- **WHEN** DOC-002 is implemented
- **THEN** existing CodeFlow analysis capabilities remain unchanged: CFG generation, semantic labels, HTML flowcharts, JSON export
- **AND** DOC-002 is additive; it does not modify analyzer, CFG construction, or existing output

---

### Requirement: DOC-002-012 — Non-Functional Requirements: Performance

CodeFlow semantic documentation generation SHALL meet the following performance targets:

#### Scenario: Small application performance

- **WHEN** CodeFlow generates DOC-002 for a small application (< 10 functions, < 500 lines)
- **THEN** total semantic documentation generation (interpretation + document creation) completes in < 10 seconds
- **AND** performance target holds even when using LLM-assisted interpretation

#### Scenario: Medium application performance

- **WHEN** CodeFlow generates DOC-002 for a medium application (20-50 functions, 1000-5000 lines)
- **THEN** total semantic documentation generation completes in < 20 seconds

#### Scenario: Large application performance

- **WHEN** CodeFlow generates DOC-002 for a large application (50-100+ functions, 5000+ lines)
- **THEN** total semantic documentation generation completes in < 30 seconds

#### Scenario: Performance breakdown accounting

- **WHEN** performance targets are evaluated
- **THEN** CodeFlow logs breakdown: semantic interpretation time, Functional_Description generation time, Technical_Description generation time, SPEC.md generation time
- **AND** most time is attributed to LLM-assisted interpretation; heuristic-based fallback is significantly faster

---

### Requirement: DOC-002-013 — Non-Functional Requirements: Quality

CodeFlow semantic documentation SHALL meet professional quality standards suitable for procurement decisions, compliance documentation, and knowledge transfer.

#### Scenario: Professional documentation presentation

- **WHEN** Functional_Description.docx is generated
- **THEN** the document uses professional formatting: consistent headings, proper typography, organized sections, numbered lists, tables where appropriate
- **AND** language is clear, grammatically correct, and free of obvious errors

#### Scenario: Hallucination-free documentation

- **WHEN** semantic documentation is generated
- **THEN** all behavioral claims are grounded in CFG analysis, source code, or explicitly marked as inference
- **AND** no functionality is invented, hallucinated, or claimed without supporting evidence

#### Scenario: Logical consistency

- **WHEN** functional and technical documents are compared
- **THEN** both documents describe the same behavior consistently
- **AND** no contradictions exist between documents or with underlying CFG analysis

---

### Requirement: DOC-002-014 — Non-Functional Requirements: Reliability and Configurability

CodeFlow semantic documentation generation SHALL be reliable and configurable.

#### Scenario: Graceful degradation

- **WHEN** LLM provider is unavailable (API error, network timeout, rate limit)
- **THEN** CodeFlow falls back to heuristic-based interpretation
- **AND** semantic documentation is still generated with reduced quality but without crashing

#### Scenario: Error handling

- **WHEN** semantic interpretation encounters an error (invalid configuration, malformed source)
- **THEN** error messages are clear and actionable
- **AND** CodeFlow exits gracefully without partial or corrupted output

#### Scenario: Configuration flexibility

- **WHEN** user wants to use different LLM providers for different analyses
- **THEN** provider can be changed via CLI, config file, or environment variable without code modification
- **AND** configuration takes effect immediately

#### Scenario: Cost awareness

- **WHEN** LLM-assisted interpretation incurs API costs
- **THEN** CodeFlow provides cost tracking, logging, and threshold alerts
- **AND** user can disable LLM interpretation or select a lower-cost provider

---

### Requirement: DOC-002-015 — Non-Functional Requirements: Backward Compatibility

CodeFlow semantic documentation generation SHALL not modify or degrade existing CodeFlow capabilities.

#### Scenario: Existing DOC-001 preservation

- **WHEN** CodeFlow continues generating DOC-001 (basic Word documentation)
- **THEN** DOC-001 output remains unchanged
- **AND** DOC-001 and DOC-002 are separately selectable

#### Scenario: CFG and HTML flowchart preservation

- **WHEN** CodeFlow generates documentation
- **THEN** control-flow graph generation, HTML flowchart rendering, and JSON export work identically
- **AND** flowcharts used by semantic documentation reference the same underlying graph structures

#### Scenario: SPEC.md update without replacement

- **WHEN** SPEC.md is generated with DOC-002
- **THEN** SPEC.md is enhanced with semantic interpretation but retains all existing behavioral specification content
- **AND** existing consumers of SPEC.md are not broken

#### Scenario: Python, Rust, PHP analyzer preservation

- **WHEN** DOC-002 is implemented
- **THEN** existing Python, Rust, and PHP analyzer behavior is unchanged
- **AND** analysis results are identical whether DOC-002 is enabled or disabled

---

### Requirement: DOC-002-016 — Acceptance Test: Functional Description Quality

CodeFlow generated Functional_Description.docx SHALL be comprehensible and accurate for non-technical stakeholders.

#### Scenario: Non-technical comprehension test

- **WHEN** a non-technical evaluator reads the generated Functional_Description.docx for a test application
- **THEN** the evaluator can correctly answer: (1) What does this application do? (2) Who are the primary users? (3) What are the major capabilities? (4) What are the constraints or limitations?
- **AND** evaluator answers match ground-truth facts about the application
- **AND** at least 80% accuracy on key facts indicates passing test

#### Scenario: Document completeness

- **WHEN** Functional_Description.docx is evaluated
- **THEN** the document contains sections: executive summary, purpose and users, major capabilities, inputs and outputs, operational rules, known limitations
- **AND** each section is substantive, not empty or template-only

---

### Requirement: DOC-002-017 — Acceptance Test: Technical Description Accuracy

CodeFlow generated Technical_Description.docx SHALL enable software engineers to understand architecture and implementation.

#### Scenario: Engineer understanding test

- **WHEN** a software engineer reads the generated Technical_Description.docx
- **THEN** the engineer can: (1) draw an architecture diagram, (2) identify major components and responsibilities, (3) trace a typical execution path, (4) identify error handling mechanisms
- **AND** engineer's understanding matches source code and CFG analysis
- **AND** at least 85% accuracy on architectural and control-flow questions indicates passing test

#### Scenario: Code reference accuracy

- **WHEN** Technical_Description.docx references source code
- **THEN** all file paths and line numbers are correct and verifiable
- **AND** referenced code actually implements the claimed behavior

---

### Requirement: DOC-002-018 — Acceptance Test: Evidence Traceability

CodeFlow generated documentation SHALL provide full traceability between behavioral claims and source evidence.

#### Scenario: Claim verification

- **WHEN** each substantive claim in Functional_Description.docx or Technical_Description.docx is examined
- **THEN** the claim is either: (1) supported by specific source reference (file, function, line range) with verification that the reference is accurate, (2) marked as INFERRED with explicit reasoning, or (3) marked as UNCERTAIN with explanation
- **AND** 100% of verified claims have valid source evidence
- **AND** ≥95% of inferred claims are explicitly marked

#### Scenario: Traceability statistics

- **WHEN** documentation is generated
- **THEN** CodeFlow reports: X% of claims have direct source evidence, Y% are marked as inferred, Z% are marked as uncertain
- **AND** statistics are logged for quality review

---

### Requirement: DOC-002-019 — Acceptance Test: No Template Repetition

CodeFlow generated documentation SHALL avoid repetitive template patterns.

#### Scenario: Template pattern detection

- **WHEN** Functional_Description.docx and Technical_Description.docx are scanned for repetitive patterns
- **THEN** patterns such as "This function contains N statement nodes", "The function has M decision nodes", "Returns control to the caller" are counted
- **AND** count ≤2 occurrences per 10 pages (acceptable for edge cases only)
- **AND** test passes if repetition is minimal

---

### Requirement: DOC-002-020 — Acceptance Test: Behavioral Accuracy

CodeFlow semantic documentation SHALL accurately represent analyzed program behavior.

#### Scenario: Behavioral claim verification

- **WHEN** semantic documentation is generated for 5-10 test programs with known behavior
- **THEN** each substantive behavioral claim is verified: (1) against CFG analysis, (2) against manual code review, (3) for false claims and hallucinations
- **AND** ≥95% of behavioral claims are accurate
- **AND** no false functionality or hallucinations are present

---

### Requirement: DOC-002-021 — Acceptance Test: Cross-Language Consistency

CodeFlow semantic documentation quality SHALL be consistent across Python, Rust, and PHP.

#### Scenario: Multi-language quality comparison

- **WHEN** DOC-002 is generated for Tic-Tac-Toe implementations in Python, Rust, and PHP
- **THEN** functional and technical documents are generated for each
- **AND** quality metrics are compared: readability, accuracy, completeness, evidence quality
- **AND** quality scores are within ±10% across languages

#### Scenario: Language-specific documentation accuracy

- **WHEN** technical documentation for Rust describes language-specific constructs (ownership, error handling, pattern matching)
- **THEN** descriptions are accurate and reflect Rust's actual semantics
- **AND** similarly for PHP documentation (global state, type juggling, dynamic typing)

---

### Requirement: DOC-002-022 — Acceptance Test: Performance

CodeFlow semantic documentation generation SHALL meet performance targets.

#### Scenario: Performance measurement

- **WHEN** CodeFlow generates DOC-002 for applications of varying sizes
- **THEN** timing is measured for: semantic interpretation, Functional_Description generation, Technical_Description generation, SPEC.md generation
- **AND** total time for small app (< 10 functions) is < 10 seconds
- **AND** total time for medium app (20-50 functions) is < 20 seconds
- **AND** total time for large app (50-100+ functions) is < 30 seconds
- **AND** at least 90% of applications complete within budget---

## Notes for Implementation (see design.md for detailed architecture)
