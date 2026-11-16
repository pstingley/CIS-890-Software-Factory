# Spec Delta: Project-Level Discovery and Analysis

## Purpose

Provides multi-file project discovery, entry-point identification, and cross-file dependency mapping for Python, Rust, and PHP projects, enabling project-level flowchart analysis and reporting.

## ADDED Requirements

### Requirement: Discover project files for Python, Rust, and PHP
CodeFlow SHALL identify all relevant source files within a project directory and filter them by language.

#### Scenario: Python project discovery
- **WHEN** analyzing a Python project directory
- **THEN** CodeFlow:
  - Discovers all .py files in the project
  - Respects .gitignore or standard exclusions (venv, __pycache__, .tox, etc.)
  - Reports discovered files and counts

#### Scenario: Rust project discovery
- **WHEN** analyzing a Rust project directory
- **THEN** CodeFlow:
  - Discovers all .rs files in src/ and other source directories
  - Parses Cargo.toml to understand project structure (packages, workspaces)
  - Identifies main.rs, lib.rs as entry points
  - Reports discovered files and project metadata

#### Scenario: PHP project discovery
- **WHEN** analyzing a PHP project directory
- **THEN** CodeFlow:
  - Discovers all .php files in the project
  - Parses composer.json if present (autoload configuration, entry points)
  - Identifies index.php or configured entry points
  - Respects .gitignore and common exclusions (vendor/, node_modules/)
  - Reports discovered files and project metadata

### Requirement: Identify application entry points
CodeFlow SHALL identify statically identifiable application entry points for each language.

#### Scenario: Python entry point discovery
- **WHEN** analyzing a Python project
- **THEN** CodeFlow identifies:
  - `__main__.py` in the project root or main package
  - `if __name__ == "__main__":` blocks in root-level scripts
  - Entry points defined in setup.py or pyproject.toml
  - Reports: "Entry points: main.py, cli.py (from setup.py)"

#### Scenario: Rust entry point discovery
- **WHEN** analyzing a Rust project
- **THEN** CodeFlow identifies:
  - `src/main.rs` as binary entry point (if Cargo.toml has [[bin]])
  - `src/lib.rs` as library entry point
  - Additional entry points from Cargo.toml `[[bin]]` sections
  - Reports: "Entry points: src/main.rs (binary), src/lib.rs (library)"

#### Scenario: PHP entry point discovery
- **WHEN** analyzing a PHP project
- **THEN** CodeFlow identifies:
  - `index.php` in project root or public/ directory (by convention)
  - Entry points defined in composer.json (PSR-4 autoload entry class)
  - Web server root index files (public/index.php, web/app.php)
  - Standalone scripts (artisan, wp-cli, etc.) if present
  - Reports: "Entry points: public/index.php, artisan (CLI)"

### Requirement: Map cross-file dependencies and relationships
CodeFlow SHALL identify and map relationships between files (imports, includes, function/class references).

#### Scenario: Python cross-file dependencies
- **WHEN** analyzing a Python project
- **THEN** CodeFlow:
  - Tracks `import` and `from X import Y` statements
  - Maps which files import which modules
  - Identifies circular imports or dependency patterns
  - Reports: "dependencies.json: file_a.py → file_b.py, file_b.py → file_c.py"

#### Scenario: Rust cross-file dependencies
- **WHEN** analyzing a Rust project
- **THEN** CodeFlow:
  - Tracks `mod`, `use`, and external crate dependencies
  - Maps which modules use which other modules
  - Identifies module hierarchy and visibility (pub vs. private)
  - Reports: "Module tree: main → config → database, database → models"

#### Scenario: PHP cross-file dependencies
- **WHEN** analyzing a PHP project
- **THEN** CodeFlow:
  - Tracks `include`, `require`, and autoloading references
  - Maps which files include/require which others
  - Identifies class dependencies via `new ClassName()` and `ClassName::method()`
  - Attempts to resolve namespace-based class references via Composer autoload
  - Reports: "Dependencies: index.php → config.php, router.php; classes: User.php ← (3 files)"

### Requirement: Generate project-level overview flowchart
CodeFlow SHALL produce a high-level flowchart showing project structure and entry-point execution paths.

#### Scenario: Python project overview
- **WHEN** generating a project-level flowchart for a Python project
- **THEN** CodeFlow produces:
  - A flowchart showing entry point (e.g., main.py) at the top
  - Nodes representing main modules and classes
  - Edges showing include/import relationships
  - Multiple colors or groupings for different modules
  - A summary: "Project contains 15 files, 3 entry points, 42 functions"

#### Scenario: Rust project overview
- **WHEN** generating a project-level flowchart for a Rust project
- **THEN** CodeFlow produces:
  - A flowchart showing binary and library entry points
  - Nodes for modules and their public interfaces
  - Edges showing module dependencies
  - Indication of public vs. private items
  - A summary: "Project contains 8 files, 1 binary + 1 library, 25 public functions"

#### Scenario: PHP project overview
- **WHEN** generating a project-level flowchart for a PHP project
- **THEN** CodeFlow produces:
  - A flowchart showing primary entry points (index.php, CLI scripts)
  - Nodes for key classes and their relationships
  - Edges showing include/require and class instantiation
  - Indication of unresolved classes (dynamic dispatch, framework routing)
  - A summary: "Project contains 23 files, 2 entry points, 18 classes, 12 unresolved calls"

### Requirement: Per-file flowcharts within project context
CodeFlow SHALL generate individual flowcharts for each significant file, with cross-file call indicators.

#### Scenario: Per-file Python flowchart
- **WHEN** generating per-file flowcharts for a Python project
- **THEN** CodeFlow produces:
  - A flowchart for each module/file
  - Nodes for functions and classes in that file
  - Edges for internal calls
  - Special indicators (bold edges, arrows) for external calls to other modules
  - Labels showing target module names

#### Scenario: Per-file Rust flowchart
- **WHEN** generating per-file flowcharts for a Rust project
- **THEN** CodeFlow produces:
  - A flowchart for each source file
  - Nodes for public and private functions
  - Edges for function calls within the file
  - Cross-module call indicators with module names
  - Visibility annotations (pub, priv)

#### Scenario: Per-file PHP flowchart with method calls
- **WHEN** generating per-file flowcharts for a PHP project
- **THEN** CodeFlow produces:
  - A flowchart for each PHP file
  - Nodes for functions and classes
  - Method nodes grouped within class nodes (or separate section)
  - Edges for internal method calls and function calls
  - Cross-file call indicators with target file and method/function name
  - Unresolved call indicators (dynamic calls, reflection, framework dispatch)

### Requirement: Compiler-style project-level error and warning reporting
CodeFlow SHALL report project-level issues in a compiler-like format for easy review and integration with CI/CD.

#### Scenario: Cross-language error reporting
- **WHEN** completing project-level analysis
- **THEN** CodeFlow outputs:
  - Summary: "Analysis complete. 50 files, 3 entry points, 150 functions, 8 warnings"
  - Errors (if any): "ERROR: Circular import detected: module_a.py → module_b.py → module_a.py"
  - Warnings: "WARNING: Unresolved call at router.php:42: framework_dispatch (not statically analyzable)"
  - Compiler-like format: "file:line: error|warning: message"

#### Scenario: Python circular dependency detection
- **WHEN** analyzing a Python project with circular imports
- **THEN** CodeFlow reports:
  - "ERROR: Circular import: module_a.py ← module_b.py ← module_c.py ← module_a.py"
  - Suggests refactoring or notes if circular import is conditional

#### Scenario: Unresolved references in project
- **WHEN** analyzing a project with missing or unresolvable files/classes
- **THEN** CodeFlow reports:
  - "WARNING: Unresolved class (database.php:10): UserRepository not found in discovered files"
  - Lists all unresolved references in a summary table

### Requirement: Respect language-specific project structures and conventions
CodeFlow SHALL recognize and respect project structure conventions for each language.

#### Scenario: Python projects (src layout, flat layout, namespace packages)
- **WHEN** analyzing a Python project
- **THEN** CodeFlow recognizes:
  - `src/` layout (source files in src/ directory)
  - Flat layout (source files in project root)
  - Namespace packages (packages without __init__.py)
  - Virtual environments (venv/, virtualenv) and excludes them

#### Scenario: Rust projects (single binary, workspace, library)
- **WHEN** analyzing a Rust project
- **THEN** CodeFlow recognizes:
  - Single-crate projects (simple Cargo.toml)
  - Workspaces (multiple crates via workspace.members)
  - Library vs. binary targets (src/lib.rs vs. src/main.rs)
  - Build scripts (build.rs) and excludes them from analysis

#### Scenario: PHP projects (Laravel, Symfony, WordPress, custom)
- **WHEN** analyzing a PHP project
- **THEN** CodeFlow recognizes:
  - Laravel: app/, routes/, config/ directories; routes/web.php entry point
  - Symfony: src/, config/, public/ structure
  - WordPress: wp-content/plugins/, wp-content/themes/ plugin/theme discovery
  - PSR-4 autoloading from composer.json
  - Custom structures: public/index.php, web/app.php, or user-specified entry points
  - Excludes vendor/, node_modules/, and cache directories

### Requirement: Produce project analysis report
CodeFlow SHALL generate a comprehensive JSON or structured report documenting project-level analysis.

#### Scenario: Project analysis JSON report
- **WHEN** generating a project analysis report
- **THEN** CodeFlow outputs a structured JSON file containing:
  - Project metadata (name, language, structure)
  - List of discovered files with paths and line counts
  - Entry points and their descriptions
  - Dependency graph (file → list of dependencies)
  - Cross-file call summary (number of unresolved calls per file)
  - Warnings and errors (with file:line references)
  - Statistics (total files, functions, classes, unresolved references)

#### Scenario: HTML project report
- **WHEN** generating an HTML project report
- **THEN** CodeFlow produces:
  - A web-viewable project overview page
  - Interactive dependency visualization (clickable, zoomable)
  - Per-file report links
  - Summary statistics and warnings section
  - Export capability (save as PDF or high-res image)
