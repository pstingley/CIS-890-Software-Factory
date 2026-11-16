# Spec Delta: Analyzer Plugin System

## Purpose

Establishes a pluggable analyzer architecture allowing CodeFlow to support multiple programming languages (Python, Rust, and others) through a common Analyzer interface, enabling independent language-specific parsers to register and be discovered by the CLI and report generator without tight coupling.

## ADDED Requirements

### Requirement: Analyzer interface provides a common contract
CodeFlow SHALL define an Analyzer abstract base or protocol with a standard interface that all language-specific analyzers implement.

#### Scenario: Analyzer defines analyze method
- **WHEN** implementing a new language analyzer
- **THEN** the analyzer implements an `analyze(source_path: str) -> AnalysisResult` method or equivalent

#### Scenario: Analyzer returns consistent result type
- **WHEN** calling the analyzer for any language
- **THEN** it returns an AnalysisResult object with fields: functions (dict of CFGs), errors (list of strings), warnings (list of strings)

#### Scenario: Analyzer metadata is discoverable
- **WHEN** querying an analyzer's capabilities
- **THEN** it exposes: supported file extensions (e.g., [".py", ".rs"]), language name, version, and supported features

### Requirement: Analyzers register by file extension
CodeFlow SHALL allow analyzers to declare which file extensions they handle; the CLI and ReportGenerator route input files to the appropriate analyzer.

#### Scenario: Python analyzer registers .py extension
- **WHEN** CodeFlow initializes
- **THEN** the Python analyzer registers itself for .py files

#### Scenario: Rust analyzer registers .rs extension
- **WHEN** CodeFlow initializes
- **THEN** the Rust analyzer registers itself for .rs files

#### Scenario: Markdown analyzer registers .md extension
- **WHEN** CodeFlow initializes
- **THEN** the Markdown (specification) analyzer registers itself for .md files

#### Scenario: Multiple analyzers can be loaded
- **WHEN** CodeFlow initializes
- **THEN** all available analyzers are discovered and registered in a central registry

### Requirement: CLI routes files to appropriate analyzer by extension
CodeFlow's command-line interface SHALL inspect the input file's extension and invoke the registered analyzer.

#### Scenario: .py file routes to Python analyzer
- **WHEN** user provides a .py file
- **THEN** CodeFlow detects the .py extension and uses the Python analyzer

#### Scenario: .rs file routes to Rust analyzer
- **WHEN** user provides a .rs file
- **THEN** CodeFlow detects the .rs extension and uses the Rust analyzer

#### Scenario: .md file routes to Markdown analyzer
- **WHEN** user provides a .md file
- **THEN** CodeFlow detects the .md extension and uses the Markdown specification analyzer

#### Scenario: Unsupported extension triggers error
- **WHEN** user provides a file with unsupported extension (e.g., .go, .js)
- **THEN** CodeFlow displays an error message listing supported file types

### Requirement: ReportGenerator uses pluggable analyzer discovery
CodeFlow's ReportGenerator class SHALL discover and invoke the appropriate analyzer without hardcoding language-specific logic.

#### Scenario: ReportGenerator.generate_report works for any language
- **WHEN** calling `ReportGenerator.generate_report("example.rs")`
- **THEN** the ReportGenerator discovers the Rust analyzer and uses it (previously, this only worked for .py files)

#### Scenario: ReportGenerator returns consistent output structure
- **WHEN** generating reports for different languages
- **THEN** all reports contain the same output files (HTML flowchart, JSON export) with consistent structure

#### Scenario: Analyzer selection happens automatically
- **WHEN** user does not specify which analyzer to use
- **THEN** ReportGenerator automatically selects the appropriate analyzer based on file extension

### Requirement: Analyzer plugins can be extended without modifying core
CodeFlow's core CLI and ReportGenerator SHALL remain unchanged when a new language analyzer is added.

#### Scenario: Adding a new language analyzer
- **WHEN** a developer creates a new analyzer (e.g., for Go, JavaScript, Java)
- **THEN** they implement the Analyzer interface and register the extension, without modifying cli.py, report_generator.py, or other core files

#### Scenario: New analyzer immediately available
- **WHEN** a new analyzer is registered
- **THEN** the CLI automatically accepts files of the new type without any configuration or code changes to core

#### Scenario: No core code changes for new language
- **WHEN** adding Rust support
- **THEN** only new files (rust_analyzer.py) and registration code are added; no changes to existing CLI or ReportGenerator logic

### Requirement: Analyzer fallback and error handling
CodeFlow SHALL gracefully handle cases where an appropriate analyzer is not found or analyzer invocation fails.

#### Scenario: No analyzer for file type
- **WHEN** user provides a file type with no registered analyzer
- **THEN** CodeFlow displays a clear error: "No analyzer available for .xyz files"

#### Scenario: Analyzer initialization failure
- **WHEN** an analyzer fails to initialize (e.g., missing dependency)
- **THEN** CodeFlow reports the failure with a descriptive message suggesting remedies

#### Scenario: Analysis error within analyzer
- **WHEN** an analyzer encounters a parse error or exception during analysis
- **THEN** CodeFlow captures the error and includes it in the analysis result's error list, without crashing

### Requirement: Backward compatibility with existing Python workflow
CodeFlow's Python analysis workflow SHALL continue to work exactly as before; the plugin system is transparent to users.

#### Scenario: Existing Python scripts work unchanged
- **WHEN** using CodeFlow on Python files as before the upgrade
- **THEN** the flowchart output, JSON export, and all options work identically

#### Scenario: Plugin system does not affect Python performance
- **WHEN** analyzing a Python file with the new plugin system
- **THEN** analysis time and resource usage are comparable to before (no significant overhead from routing)

#### Scenario: Python analyzer can be swapped without CLI changes
- **WHEN** the Python analyzer implementation is updated
- **THEN** the CLI continues to work without modification as long as the Analyzer interface contract is maintained
