# Spec Delta: PHP Parsing

## Purpose

Provides structured parsing of PHP source files and projects to extract control flow information, multi-file relationships, and project-level structure, generating control-flow graph (CFG) nodes and edges that represent function/method entry/exit, decision statements, loops, exception handling, and cross-file dependencies, with explicit flagging of dynamic behavior and analysis limitations.

## ADDED Requirements

### Requirement: Parse PHP function definitions and entry/exit
CodeFlow SHALL identify PHP function definitions and represent them as CFG entry and exit nodes, including type hints and return types where applicable.

#### Scenario: Simple function with return statement
- **WHEN** parsing a PHP function with an explicit `return` statement
- **THEN** the CFG contains one entry node (function name) and one exit node (return target)

#### Scenario: Function with implicit return (void)
- **WHEN** parsing a PHP function without an explicit return or with no return type
- **THEN** the CFG contains an entry node and an exit node where control flow ends

#### Scenario: Multiple return paths
- **WHEN** parsing a PHP function with multiple `return` statements in different branches
- **THEN** the CFG contains one entry node and multiple paths that converge on a single exit node

### Requirement: Parse PHP class and method definitions
CodeFlow SHALL identify PHP classes, methods (public/private/protected), properties, constructors, and static methods, representing them as callable CFG nodes.

#### Scenario: Class with methods
- **WHEN** parsing a PHP class with instance methods and a constructor
- **THEN** the CFG represents the constructor as an entry point and each method as a callable unit with entry/exit nodes

#### Scenario: Static methods
- **WHEN** parsing `public static function methodName()`
- **THEN** the CFG marks the method as static-callable without requiring an instance

#### Scenario: Magic methods (__construct, __call, etc.)
- **WHEN** parsing magic methods like `__construct` or `__call`
- **THEN** the CFG identifies them and labels them appropriately; flags automatic invocation behavior in ambiguity_flags

### Requirement: Parse namespace declarations and use statements
CodeFlow SHALL identify PHP namespace declarations and `use` statements, representing them in source traceability for multi-file contexts.

#### Scenario: Namespaced code
- **WHEN** parsing `namespace App\Services; class MyService { ... }`
- **THEN** the CFG preserves the namespace path; source_references include fully qualified names

#### Scenario: Use statements and aliases
- **WHEN** parsing `use Some\Long\ClassName as Alias;` followed by `new Alias()`
- **THEN** the CFG resolves the alias to the full class name in source_references where possible

### Requirement: Parse if/else decision statements
CodeFlow SHALL parse PHP if, else if, and else blocks as decision nodes with two or more branches.

#### Scenario: Simple if-else
- **WHEN** parsing `if ($condition) { ... } else { ... }`
- **THEN** the CFG contains a decision node with two outgoing edges labeled "true" and "false"

#### Scenario: if-elseif-else chain
- **WHEN** parsing `if ($c1) { ... } elseif ($c2) { ... } else { ... }`
- **THEN** the CFG contains nested decision nodes representing each condition in sequence

#### Scenario: if without else
- **WHEN** parsing an `if ($condition) { ... }` without an else block
- **THEN** the CFG contains a decision node with true and false branches; the false branch merges with continuation after the if

### Requirement: Parse switch/match expressions as multi-branch decisions
CodeFlow SHALL parse PHP switch statements and match expressions (PHP 8+) as multi-branch decision nodes, with each case as a separate path.

#### Scenario: Switch with cases and default
- **WHEN** parsing `switch ($value) { case 1: {...} case 2: {...} default: {...} }`
- **THEN** the CFG contains a decision node with outgoing edges for each case, with implicit fallthrough or break handling

#### Scenario: Match expression (PHP 8+)
- **WHEN** parsing `match ($value) { 1 => {...}, 2 => {...}, default => {...} }`
- **THEN** the CFG represents each arm as a separate path; match does not fall through (returns a value)

#### Scenario: Break statements in switch
- **WHEN** parsing switch cases with and without `break`
- **THEN** the CFG shows fallthrough edges for cases without break; explicit exit for cases with break

### Requirement: Parse loop constructs
CodeFlow SHALL parse PHP for, foreach, while, and do-while statements as loop-entry nodes with back edges and exit paths.

#### Scenario: Foreach loop over array
- **WHEN** parsing `foreach ($array as $key => $value) { ... }`
- **THEN** the CFG contains a loop-entry node and a back edge from the loop body to the condition, with an exit edge when the loop terminates

#### Scenario: While loop with condition
- **WHEN** parsing `while ($condition) { ... }`
- **THEN** the CFG contains a decision node (the condition) with a back edge to itself (loop) and an exit edge

#### Scenario: Do-while loop
- **WHEN** parsing `do { ... } while ($condition);`
- **THEN** the CFG shows the loop body executes at least once, then loops back to the condition check

#### Scenario: Break and continue in loop
- **WHEN** parsing a loop with `break` and `continue` statements
- **THEN** the CFG shows break edges exiting the loop and continue edges looping back to the loop condition/top

### Requirement: Parse exception handling (try/catch/finally)
CodeFlow SHALL parse PHP try/catch/finally blocks as exception-handling paths.

#### Scenario: Try-catch block
- **WHEN** parsing `try { ... } catch (Exception $e) { ... }`
- **THEN** the CFG creates an exception path from the try block to the catch handler

#### Scenario: Multiple catch blocks
- **WHEN** parsing `try { ... } catch (SpecificException $e) { ... } catch (Exception $e) { ... }`
- **THEN** the CFG shows multiple exception paths, one per catch block, in the order they would match

#### Scenario: Try-catch-finally
- **WHEN** parsing `try { ... } catch (Exception $e) { ... } finally { ... }`
- **THEN** the CFG shows the finally block is always executed after try or catch, before exit

#### Scenario: Throw statement
- **WHEN** parsing `throw new Exception("message");`
- **THEN** the CFG creates an exception edge from the throw statement to the nearest enclosing catch block (or function exit if uncaught)

### Requirement: Parse function and method call sequences
CodeFlow SHALL recognize function calls, method calls, and chained method calls, representing them as statement nodes in the call sequence.

#### Scenario: Direct function call
- **WHEN** parsing a line with a function call like `someFunction()`
- **THEN** the CFG contains a call node (or statement node labeled with the function name)

#### Scenario: Method call on object
- **WHEN** parsing `$obj->method()`
- **THEN** the CFG represents the call as a method-call node with the receiver object and method name

#### Scenario: Static method call
- **WHEN** parsing `ClassName::staticMethod()`
- **THEN** the CFG represents the call as a static-method-call node with the class name and method

#### Scenario: Chained method calls
- **WHEN** parsing `$obj->method1()->method2()->method3()`
- **THEN** the CFG represents the sequence as connected statement nodes showing the chain

### Requirement: Identify statically resolvable cross-file calls and include relationships
CodeFlow SHALL attempt to map include/require statements to files and identify statically resolvable function/class calls across files, flagging unresolved calls explicitly.

#### Scenario: Include or require statement
- **WHEN** parsing `include 'config.php';` or `require_once 'database.php';`
- **THEN** the CFG:
  - Attempts to resolve the file path relative to the current file
  - If successful, adds a cross-file edge in source_references
  - If unsuccessful or dynamic (variable path), logs to ambiguity_flags: "Line NNN: unresolved_include (dynamic or missing file path)"

#### Scenario: Static class instantiation across files
- **WHEN** parsing `new App\Services\UserService()` where UserService is defined in another file
- **THEN** the CFG:
  - If the class file is discovered via autoloading or include chains, links the call to the class definition
  - If the class cannot be resolved, flags in ambiguity_flags: "Line NNN: unresolved_class (UserService not found in discovered files)"

#### Scenario: Static function call across files
- **WHEN** parsing a call to a function defined in a different file
- **THEN** the CFG:
  - If the function file is discovered, creates a cross-file call edge
  - If the function cannot be resolved, flags in ambiguity_flags: "Line NNN: unresolved_function (functionName not found)"

### Requirement: Discover PHP project structure and entry points
CodeFlow SHALL discover PHP project files and identify statically identifiable entry points.

#### Scenario: Entry point discovery in flat project
- **WHEN** analyzing a PHP project directory containing `index.php`, `config.php`, and other files
- **THEN** CodeFlow:
  - Identifies `index.php` as the primary entry point (by convention)
  - Discovers all `.php` files in the project
  - Reports entry points in analysis metadata

#### Scenario: Entry point discovery with Composer autoloading
- **WHEN** a project contains a `composer.json` with autoload configuration (PSR-0, PSR-4)
- **THEN** CodeFlow:
  - Parses the autoload sections to understand namespace-to-file mappings
  - Uses this to resolve cross-file calls more accurately
  - Flags unresolvable paths in ambiguity_flags

#### Scenario: Namespace-based file structure
- **WHEN** analyzing a project with PSR-4 autoloading (e.g., `src/` → `App\`)
- **THEN** CodeFlow:
  - Maps namespaced class references to their file locations
  - Discovers related files for multi-file analysis
  - Flags files with unresolved namespaces in ambiguity_flags

### Requirement: Parse multi-file PHP projects for comprehensive analysis
CodeFlow SHALL accept a directory path and analyze the entire PHP project, mapping dependencies and relationships.

#### Scenario: Project-level analysis requested
- **WHEN** user runs `codeflow analyze project_dir --type=project --language=php`
- **THEN** CodeFlow:
  - Discovers all .php files and entry points in the directory
  - Analyzes each file's control flow
  - Maps include/require and class/function cross-file relationships
  - Produces a project-level overview flowchart and detailed per-file reports

#### Scenario: Mixed PHP files with HTML
- **WHEN** the project contains files with mixed PHP and HTML (e.g., template files with PHP blocks)
- **THEN** CodeFlow:
  - Parses PHP blocks using the tree-sitter PHP parser
  - Flags HTML portions as non-code in source_references
  - Notes in ambiguity_flags: "File contains mixed PHP/HTML; analysis covers PHP control flow only"

### Requirement: Flag dynamic includes, reflection, and unresolved calls explicitly
CodeFlow SHALL accept files with dynamic behavior, attempt best-effort analysis, and report limitations and uncertainty clearly.

#### Scenario: Dynamic include with variable path
- **WHEN** parsing `include $filename;` or `include "./includes/{$page}.php";`
- **THEN** CodeFlow:
  - Cannot resolve the target file at parse time
  - Logs to stderr: "WARNING: Dynamic include detected at line NNN: variable_include_path (Cannot resolve path statically)"
  - Stores warning in AnalysisResult.ambiguity_flags: "Line NNN: dynamic_include (path is variable or computed)"
  - Sets AnalysisResult.analysis_incomplete = True

#### Scenario: Reflection or dynamic class instantiation
- **WHEN** parsing `$className = 'MyClass'; new $className();` or `$reflection->newInstance()`
- **THEN** CodeFlow:
  - Flags the call as unresolvable
  - Logs to stderr: "WARNING: Dynamic call detected at line NNN: reflection_or_variable_instantiation (Cannot resolve class statically)"
  - Stores warning in ambiguity_flags: "Line NNN: unresolved_call (dynamic instantiation)"
  - Sets analysis_incomplete = True

#### Scenario: Call via callback or callable array
- **WHEN** parsing `$callback(); call_user_func($func);` or `['ClassName', 'methodName']()`
- **THEN** CodeFlow:
  - Flags the call as uncertain
  - Logs to stderr: "WARNING: Callable indirection at line NNN: callback_or_callable (Target not statically resolvable)"
  - Stores warning in ambiguity_flags: "Line NNN: unresolved_callback"
  - Sets analysis_incomplete = True (unless all calls in file are static)

#### Scenario: Framework routing or dispatch
- **WHEN** parsing code that uses a framework's router or service locator (e.g., Laravel's `app()`, Symfony's container)
- **THEN** CodeFlow:
  - Treats the router/locator call as an opaque call
  - Logs to stderr: "WARNING: Framework dispatch detected at line NNN: framework_routing (Actual target depends on runtime configuration)"
  - Stores warning in ambiguity_flags: "Line NNN: framework_dispatch (not statically analyzable)"
  - Sets analysis_incomplete = True

#### Scenario: Unsupported construct does not block analysis
- **WHEN** parsing a file with multiple dynamic calls and framework patterns
- **THEN** CodeFlow:
  - Completes analysis successfully for static portions
  - Generates CFG for static code paths
  - Logs multiple warnings to stderr (one per dynamic construct)
  - Lists all unresolved items in ambiguity_flags
  - Sets analysis_incomplete = True
  - Includes summary: "Analysis completed with X unresolved dynamic constructs; review HTML report for details"

### Requirement: AnalysisResult includes analysis_incomplete flag
CodeFlow SHALL include an `analysis_incomplete: bool` field in AnalysisResult. This field is set to True whenever dynamic behavior or unresolved constructs are encountered that could affect control flow accuracy; it is False when analysis is complete or only informational.

#### Scenario: Analysis completeness indicated via field
- **WHEN** the PHP analyzer completes analysis of a file
- **THEN** the AnalysisResult includes:
  - `analysis_incomplete = False` if all constructs are resolved and static
  - `analysis_incomplete = True` if dynamic includes, reflection, unresolved calls, or framework patterns were encountered

#### Scenario: HTML report includes completeness indicator
- **WHEN** generating the HTML flowchart report for a PHP file
- **THEN** the report includes a note (if `analysis_incomplete = True`): "Note: This analysis is incomplete due to dynamic constructs and unresolved calls. Review warnings below." with a list of the warnings

### Requirement: CLI accepts .php files and routes them to the PHP analyzer
CodeFlow's command-line interface SHALL accept PHP (.php) files and invoke the PHP analyzer, producing flowchart output using the same format as Python and Rust analysis.

#### Scenario: User provides .php file path
- **WHEN** user runs `codeflow analyze example.php`
- **THEN** CodeFlow parses the PHP file and generates an HTML flowchart report named `example_codeflow.html`

#### Scenario: User provides PHP project directory
- **WHEN** user runs `codeflow analyze project_dir --language=php --mode=project`
- **THEN** CodeFlow discovers all .php files, identifies entry points, and generates project overview and per-file reports

#### Scenario: Output directory specified for .php file
- **WHEN** user runs `codeflow analyze example.php --output-dir ./reports`
- **THEN** CodeFlow writes the HTML report to `./reports/example_codeflow.html`

#### Scenario: .php file extension is recognized alongside .py, .rs, and .md
- **WHEN** user provides a .php path
- **THEN** CodeFlow recognizes .php as a supported extension and analyzes it using the PHP analyzer

### Requirement: Backward compatibility with Python, Rust, and Markdown workflows
CodeFlow's existing Python, Rust, and Markdown workflows SHALL remain unchanged; all new PHP functionality is additive.

#### Scenario: Existing Python analysis produces same output
- **WHEN** running CodeFlow on a Python file that was analyzed before the PHP upgrade
- **THEN** the output (flowchart structure, node labels, edges) is identical

#### Scenario: Existing Rust analysis produces same output
- **WHEN** running CodeFlow on a Rust file
- **THEN** the output is identical to pre-PHP-upgrade behavior

#### Scenario: Existing SPEC.md workflow unchanged
- **WHEN** analyzing a Markdown specification file (SPEC.md)
- **THEN** the flowchart import, Claude Code integration, and Word walkthrough features work as before

#### Scenario: Command-line interface remains compatible
- **WHEN** using the original `python -m codeflow analyze FILE` command
- **THEN** it continues to work without modification for .py, .rs, and .md files

### Requirement: PHP parser uses tree-sitter PHP for robust grammar-based parsing
CodeFlow's PHP analyzer SHALL use tree-sitter with the tree-sitter-php grammar for parsing instead of regex or manual parsing.

#### Scenario: Parser dependency availability
- **WHEN** CodeFlow initializes the PHP analyzer
- **THEN** it loads tree-sitter and the PHP language grammar; if either is unavailable, CodeFlow reports a configuration error with guidance on installation

#### Scenario: Graceful handling of unsupported constructs
- **WHEN** the PHP parser encounters constructs that CodeFlow does not analyze (attributes, enums, fibers, type unions beyond basic detection)
- **THEN** it identifies them, logs a degradation flag with line number, and continues parsing the rest of the file

#### Scenario: Parse results include ambiguity flags
- **WHEN** a PHP file is analyzed
- **THEN** the `AnalysisResult.ambiguity_flags` list documents all dynamic constructs, unresolved calls, mixed PHP/HTML sections, and framework patterns (e.g., "Line 42: dynamic_include (path is variable)", "Line 103: framework_dispatch (Laravel routing)")

#### Scenario: Mixed PHP/HTML file handling
- **WHEN** analyzing a file containing both PHP code blocks and HTML markup
- **THEN** CodeFlow:
  - Parses PHP blocks using tree-sitter-php
  - Treats HTML as non-executable
  - Logs a note in ambiguity_flags: "File contains mixed PHP/HTML; HTML not analyzed"
  - Completes analysis of PHP portions normally

#### Scenario: Version consistency
- **WHEN** CodeFlow is deployed or updated
- **THEN** tree-sitter and tree-sitter-php versions are pinned in dependencies to ensure reproducible parsing across environments
