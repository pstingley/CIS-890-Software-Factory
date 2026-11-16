# Spec Delta: Behavioral Control-Flow Verification Testing

## Purpose

This specification defines the testing strategy for verifying that CodeFlow analyzers produce **correct control-flow graphs that accurately represent executable program behavior**, not merely syntactically valid graphs or Node/Edge count metrics.

## ADDED Requirements

### Requirement: Behavioral tests SHALL verify exact control-flow paths and edges
CodeFlow test suites SHALL include behavioral tests that verify specific sequences of nodes, edge destinations, and control-flow routing—not just structural validity (node count, connectivity).

#### Scenario: Test verifies specific path exists
- **WHEN** analyzing a simple if/else
- **THEN** test asserts the exact path: ['entry' → 'if x > 0 decision' → 'return 42' → 'exit']

#### Scenario: Test verifies edge destination
- **WHEN** analyzing a decision node
- **THEN** test asserts outgoing edges have correct targets and labels (e.g., 'true' edge to correct node, 'false' edge to correct node)

#### Scenario: Test verifies break routes to loop exit
- **WHEN** analyzing a break statement in a loop
- **THEN** test asserts the break edge targets the after-loop node, NOT the function exit

#### Scenario: Test verifies continue targets loop entry
- **WHEN** analyzing a continue statement in a loop
- **THEN** test asserts the continue edge targets the loop entry/test node, NOT the function exit or arbitrary node

#### Scenario: Test verifies no invalid edges
- **WHEN** analyzing control flow
- **THEN** test asserts that certain edges do NOT exist (e.g., 'return' should NOT connect to 'return', break should NOT connect to exit)

### Requirement: Test fixtures SHALL represent complex control-flow scenarios
CodeFlow SHALL include representative test programs for each language demonstrating nested decisions, loops, early returns, exceptions, and multiple execution paths.

#### Scenario: Python test fixture includes nested if/elif/else
- **WHEN** testing Python analyzer
- **THEN** test fixtures include code like `if cond1: ... elif cond2: ... elif cond3: ... else: ...` with multiple return paths

#### Scenario: Python test fixture includes nested loops with break/continue
- **WHEN** testing Python analyzer
- **THEN** test fixtures include nested for/while loops with break in inner loop and continue in outer loop

#### Scenario: Python test fixture includes try/except/finally
- **WHEN** testing Python analyzer
- **THEN** test fixtures include exception handling with multiple except clauses and finally block

#### Scenario: Rust test fixture includes match expressions
- **WHEN** testing Rust analyzer
- **THEN** test fixtures include match with 3+ arms, guard conditions, and pattern matching

#### Scenario: Rust test fixture includes error propagation
- **WHEN** testing Rust analyzer
- **THEN** test fixtures include functions using `?` operator demonstrating error propagation paths

#### Scenario: Rust test fixture includes nested loops with break/continue
- **WHEN** testing Rust analyzer
- **THEN** test fixtures include nested for/while loops demonstrating correct break/continue routing

#### Scenario: PHP test fixture includes switch with cases
- **WHEN** testing PHP analyzer (Phase 4+)
- **THEN** test fixtures include switch statements with multiple cases, fall-through, and break

#### Scenario: PHP test fixture includes multi-file relationships
- **WHEN** testing PHP analyzer (Phase 4+)
- **THEN** test fixtures include include/require statements with statically resolvable cross-file references

### Requirement: Behavioral tests SHALL verify no generic/syntactic node labels
CodeFlow tests SHALL explicitly assert that generated CFG nodes do NOT contain generic AST node types or syntactic artifacts in their labels.

#### Scenario: Test asserts no "let_declaration" labels
- **WHEN** running tests on analyzed code
- **THEN** test asserts no node label contains "let_declaration"

#### Scenario: Test asserts no "call_expression" labels
- **WHEN** running tests on analyzed code
- **THEN** test asserts no node label contains "call_expression"

#### Scenario: Test asserts no standalone punctuation
- **WHEN** running tests on analyzed code
- **THEN** test asserts no node has label "{", "}", ";", etc.

#### Scenario: Test asserts actual operation labels
- **WHEN** running tests on a declaration like `let x = 42`
- **THEN** test asserts the node label is exactly `let x = 42`, not a type name

### Requirement: Test assertion API SHALL provide readable behavioral assertions
CodeFlow test infrastructure SHALL provide assertion functions for path verification, edge verification, label verification, and graph traversal.

#### Scenario: assert_path_exists function
- **WHEN** using test API
- **THEN** test can call `assert_path_exists(cfg, ['entry', 'decision_node', 'statement_node', 'exit'])` to verify a specific sequence

#### Scenario: assert_edge_exists function
- **WHEN** using test API
- **THEN** test can call `assert_edge_exists(cfg, 'node_a', 'node_b', edge_type=EdgeType.TRUE, label='true')` to verify edge properties

#### Scenario: assert_edge_does_not_exist function
- **WHEN** using test API
- **THEN** test can call `assert_edge_does_not_exist(cfg, 'break_stmt', 'function_exit')` to verify an edge must NOT exist

#### Scenario: assert_node_label_does_not_contain function
- **WHEN** using test API
- **THEN** test can call `assert_node_label_does_not_contain(cfg, 'let_declaration')` to ensure no syntactic artifacts

### Requirement: Behavioral tests SHALL verify loop routing is correct
CodeFlow loop tests SHALL verify back-edges, break targets, and continue targets are correct.

#### Scenario: Test verifies loop-back edge exists
- **WHEN** testing a for/while loop
- **THEN** test asserts a loop-back edge (LOOP_BACK or CONTINUE type) exists from loop body to loop entry

#### Scenario: Test verifies break targets after-loop
- **WHEN** testing break in a loop
- **THEN** test asserts break edge targets the specific after-loop node, with correct edge type (BREAK)

#### Scenario: Test verifies continue targets loop entry
- **WHEN** testing continue in a loop
- **THEN** test asserts continue edge targets the specific loop-entry/test node, with correct edge type

#### Scenario: Test verifies nested loop routing
- **WHEN** testing nested loops
- **THEN** test asserts inner loop back-edge targets inner-loop-entry, outer loop back-edge targets outer-loop-entry

#### Scenario: Test verifies break in nested loop
- **WHEN** testing break in inner loop of nested structure
- **THEN** test asserts break routes to after-inner-loop, NOT after-outer-loop or function-exit

### Requirement: Behavioral tests SHALL verify decision branch routing
CodeFlow decision tests SHALL verify all branches are reachable and route to correct targets.

#### Scenario: Test verifies if/else has both branches
- **WHEN** testing if/else
- **THEN** test asserts both [true] and [false] branches exist and are reachable

#### Scenario: Test verifies match has all arms
- **WHEN** testing match/switch with 3+ arms
- **THEN** test asserts every arm pattern has an outgoing edge from the match decision node

#### Scenario: Test verifies branch merge point
- **WHEN** testing if/else or match
- **THEN** test asserts all branches converge to same merge node (if merge is expected) or terminate separately (if branches have different termination)

#### Scenario: Test asserts unreachable branches are handled
- **WHEN** testing `if true: ...` or similar always-true condition
- **THEN** test asserts only [true] branch is executable, [false] is omitted or marked unreachable

### Requirement: Behavioral tests SHALL verify source traceability
CodeFlow tests SHALL verify that every CFG node has valid source references enabling traceability to actual source code.

#### Scenario: Test verifies file path in node
- **WHEN** testing an analyzed file
- **THEN** test asserts every STATEMENT/DECISION node has correct `source_location.file` path

#### Scenario: Test verifies line number in node
- **WHEN** testing a statement on specific line
- **THEN** test asserts the CFG node has correct `source_location.start_line`

#### Scenario: Test verifies source code in node
- **WHEN** testing a statement
- **THEN** test asserts `source_location.source_code` contains the actual source text (or truncated indicator)

### Requirement: Behavioral tests SHALL verify completeness marking
CodeFlow tests SHALL verify that partial analysis is explicitly marked and complete analysis is only marked when all supported constructs are analyzed.

#### Scenario: Test verifies is_partial flag on incomplete
- **WHEN** analyzing code with unsupported constructs (e.g., Rust macros)
- **THEN** test asserts `cfg.is_partial == True` and `partial_reason` contains explanation

#### Scenario: Test verifies complete analysis marked correctly
- **WHEN** analyzing code with only supported constructs and no dynamic behavior
- **THEN** test asserts `cfg.is_partial == False` (or omitted if default)

#### Scenario: Test asserts partial_reason is non-empty when partial
- **WHEN** analyzing incomplete code
- **THEN** test asserts `cfg.partial_reason` is a non-empty string explaining why analysis is partial
