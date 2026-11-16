# Spec Delta: Language-Independent Control-Flow Correctness Contract

## Purpose

Establishes a **language-independent semantic control-flow contract** that all CodeFlow analyzers (Python, Rust, PHP, and future languages) must implement to generate accurate control-flow diagrams representing executable program behavior, not AST terminology or syntactic artifacts. This specification fixes critical correctness defects in existing control-flow graphs and prevents similar issues in future language analyzers.

## ADDED Requirements

### Requirement: Control-flow graphs SHALL represent executable operations, not AST terminology
CodeFlow SHALL generate node labels that describe what code actually does when executed, never bare AST node types (let_declaration, call_expression, assignment_expression, etc.) or syntactic punctuation ({, }, ;).

#### Scenario: Statement node uses actual code expression
- **WHEN** analyzing a variable declaration like `let x = 42`
- **THEN** the CFG node label shows the complete statement `let x = 42`, not `let_declaration`

#### Scenario: Call expression shows function/method and arguments
- **WHEN** analyzing a function call like `self.squares.insert(position, Square::Empty)`
- **THEN** the CFG node label shows `self.squares.insert(position, Square::Empty)`, not `call_expression`

#### Scenario: Return expression shows return value
- **WHEN** analyzing a return statement like `return Some(winner)`
- **THEN** the CFG node label shows `return Some(winner)`, not `return_expression`

#### Scenario: If condition shows actual predicate
- **WHEN** analyzing an if statement like `if x > 10`
- **THEN** the DECISION node shows `if x > 10` or the condition expression, not generic `condition` or `if_expression`

#### Scenario: No standalone punctuation nodes
- **WHEN** generating a control-flow graph
- **THEN** no CFG nodes have labels that are only "{", "}", ";", or other punctuation

### Requirement: Decision nodes SHALL correctly represent conditional branches
CodeFlow SHALL ensure every decision node has reachable branches that connect to correct targets, with branches labeled true/false or pattern-specific labels (for match/switch).

#### Scenario: If/else has both true and false branches
- **WHEN** analyzing an if/else statement
- **THEN** the DECISION node has two outgoing edges labeled "true" and "false" to correct targets

#### Scenario: Unreachable branches are marked or omitted
- **WHEN** analyzing `if true` or `if false` or similar always-true/always-false conditionals
- **THEN** only reachable branches are shown as executable paths; unreachable branches are either omitted or marked explicitly

#### Scenario: Both branches converge to merge node or terminate
- **WHEN** analyzing an if/else block
- **THEN** both [true] and [false] branches either converge to the same merge node and continue, OR terminate (return/break/exception) without false convergence

#### Scenario: Rust match arms all appear in diagram
- **WHEN** analyzing a Rust match expression with multiple arms
- **THEN** every pattern arm appears as a separate outgoing edge from the match DECISION node

#### Scenario: PHP/Python switch/match cases all appear
- **WHEN** analyzing a switch/match statement with multiple cases
- **THEN** every case pattern appears as a separate outgoing edge; fall-through behavior is correctly represented

### Requirement: Loop constructs SHALL route break and continue to correct targets
CodeFlow SHALL ensure break statements exit only to the immediately enclosing loop's after-loop node, and continue statements return to the immediately enclosing loop's entry/test, never to function exit or wrong loop.

#### Scenario: Break exits to after-loop node
- **WHEN** analyzing a break statement inside a loop
- **THEN** the edge from the break statement targets the loop's after-loop node, NOT the function exit node

#### Scenario: Continue targets loop entry
- **WHEN** analyzing a continue statement inside a loop
- **THEN** the edge from the continue statement targets the loop entry/test node (the beginning of the next iteration), NOT the function exit or arbitrary node

#### Scenario: Nested loops have correct break/continue scoping
- **WHEN** analyzing nested loops with break/continue in the inner loop
- **THEN** break in inner loop exits to after-inner-loop (not after-outer-loop or function exit), and continue in inner loop targets inner-loop-test

#### Scenario: Break in nested control flow
- **WHEN** analyzing break inside a match/if nested within a loop
- **THEN** break in the match/if targets the enclosing loop's after-loop node, NOT the function exit

#### Scenario: Loop back-edge returns to correct entry
- **WHEN** analyzing a for/while loop
- **THEN** the loop back-edge (marked LOOP_BACK or CONTINUE edge type) returns to the loop entry node, not loop body or arbitrary target

### Requirement: Return statements SHALL connect to function exit, not arbitrary nodes
CodeFlow SHALL ensure all return statements in a function connect directly to that function's normal EXIT node, with no edges continuing past a return as executable paths.

#### Scenario: Single return connects to exit
- **WHEN** analyzing a function with a single return statement
- **THEN** the return node has an edge to the function's EXIT node

#### Scenario: Multiple returns all reach same exit
- **WHEN** analyzing a function with multiple return statements
- **THEN** each return statement has an edge to the same function EXIT node

#### Scenario: Unreachable statements after return are not connected
- **WHEN** analyzing code after an unconditional return
- **THEN** statements after the return are either omitted from the graph or marked unreachable, with no executable edge from return to unreachable statements

#### Scenario: Early return in conditional
- **WHEN** analyzing `if cond { return early } else { continue }`
- **THEN** return in [true] branch connects to EXIT; [false] branch continues with normal flow

#### Scenario: Multiple return paths from nested conditions
- **WHEN** analyzing nested if/elif/else with returns in multiple branches
- **THEN** each return path reaches EXIT; merge nodes are created only where paths actually converge

### Requirement: Exception paths SHALL propagate to function EXCEPTION_EXIT
CodeFlow SHALL ensure error/exception/panic statements connect to the function's EXCEPTION_EXIT node, never to normal EXIT or arbitrary nodes.

#### Scenario: Rust ? operator has Err branch to exception_exit
- **WHEN** analyzing `let file = File::open(path)?`
- **THEN** the ? operator creates an Err path connecting to function EXCEPTION_EXIT

#### Scenario: Python exception propagation reaches exception_exit
- **WHEN** analyzing code that raises an exception (and is not caught)
- **THEN** the raise statement has an edge to function EXCEPTION_EXIT

#### Scenario: Rust panic creates exception path
- **WHEN** analyzing `panic!("message")`
- **THEN** panic creates an edge to function EXCEPTION_EXIT

#### Scenario: PHP throw creates exception path
- **WHEN** analyzing `throw new Exception()`
- **THEN** throw creates an edge to function EXCEPTION_EXIT

#### Scenario: Caught exceptions route to handler, not exception_exit
- **WHEN** analyzing `try { risky() } except ValueError { handle }`
- **THEN** exception paths route to the except/catch handler block, not directly to exception_exit

### Requirement: Graph validation rules SHALL enforce correctness
CodeFlow's graph validation SHALL check that all CFGs satisfy fundamental correctness invariants before marking analysis complete.

#### Scenario: Entry node has outgoing edges
- **WHEN** analyzing a function
- **THEN** the ENTRY node has at least one outgoing edge (or connects directly to a single EXIT if function is empty)

#### Scenario: All reachable nodes have path to exit
- **WHEN** validating a control-flow graph
- **THEN** every reachable node either reaches EXIT, EXCEPTION_EXIT, or is unreachable (marked explicitly)

#### Scenario: No invalid cycles except loop-back
- **WHEN** validating a control-flow graph
- **THEN** the only cycles are loop-back edges (marked LOOP_BACK or CONTINUE edge types) and their targets are loop-entry nodes

#### Scenario: Decision edges have semantic labels
- **WHEN** validating a DECISION node
- **THEN** each outgoing edge has a label: [true]/[false] for boolean decisions, or pattern/case labels for match/switch

#### Scenario: Graph is not marked complete if incomplete
- **WHEN** analyzing code with unsupported constructs, macros, dynamic dispatch, or incomplete analysis
- **THEN** the CFG has `is_partial=True` with explicit `partial_reason`; never marked COMPLETE

#### Scenario: Break edge never targets function exit
- **WHEN** validating a control-flow graph
- **THEN** no BREAK edge points to the function EXIT node

#### Scenario: Continue edge targets loop entry
- **WHEN** validating a control-flow graph
- **THEN** every CONTINUE edge points to a loop entry/test node, never to function exit or arbitrary node

#### Scenario: Merge nodes appear only where paths converge
- **WHEN** validating a control-flow graph
- **THEN** MERGE nodes are only created where multiple paths join (e.g., after if/else), not for every statement

### Requirement: Source references SHALL be maintained for every statement/decision
CodeFlow SHALL retain valid file paths, line numbers, and source-code text for every statement and decision node, enabling traceability to actual source code.

#### Scenario: Statement node has file path
- **WHEN** analyzing a function in `/path/to/file.py`
- **THEN** every STATEMENT node in the CFG has `source_location.file = /path/to/file.py`

#### Scenario: Node has line number
- **WHEN** analyzing a statement on line 42
- **THEN** the STATEMENT node has `source_location.start_line = 42`

#### Scenario: Node preserves source code text
- **WHEN** analyzing a statement
- **THEN** the STATEMENT node has `source_location.source_code` containing the actual source text (or truncated with indicator if too long)

#### Scenario: Truncated labels reference full source
- **WHEN** a node label is truncated
- **THEN** the full source is available in `source_location.source_code`, and node label ends with "..." if truncated

### Requirement: Partial analysis SHALL be explicitly marked
CodeFlow SHALL never silently omit unsupported constructs or incomplete analysis, and SHALL explicitly indicate partial analysis in the AnalysisResult.

#### Scenario: Macros trigger partial marking
- **WHEN** analyzing Rust code containing macros (e.g., `println!`, `vec!`)
- **THEN** the CFG has `is_partial=True` with `partial_reason="Macros not supported: println! (line 42), vec! (line 15)"`

#### Scenario: Dynamic dispatch marked as partial
- **WHEN** analyzing code with unresolvable dynamic dispatch or reflection
- **THEN** the CFG has `is_partial=True` with explicit reason

#### Scenario: Ambiguities explicitly reported
- **WHEN** analysis encounters unresolved or ambiguous constructs
- **THEN** `AnalysisResult.ambiguity_flags` contains description of each ambiguity

#### Scenario: Never mark incomplete as complete
- **WHEN** AnalysisResult is created
- **THEN** `is_partial=False` only if all supported constructs are analyzed and all code paths are represented
- **AND** `is_partial=True` if ANY unsupported construct, dynamic behavior, or incomplete analysis exists

### Requirement: Python analyzers SHALL maintain existing correctness
CodeFlow's Python analyzer SHALL continue satisfying all control-flow correctness requirements without regression.

#### Scenario: Python if/else maintains correctness
- **WHEN** analyzing Python if/elif/else
- **THEN** all branches are reachable, correct, and converge properly

#### Scenario: Python loops maintain correctness
- **WHEN** analyzing Python for/while with break/continue
- **THEN** break exits to after-loop, continue targets loop-entry, never function exit

#### Scenario: Python exceptions route correctly
- **WHEN** analyzing Python try/except/finally
- **THEN** exception paths route to correct exception handlers, not normal flow

### Requirement: Rust analyzers SHALL implement full correctness contract
CodeFlow's Rust analyzer SHALL satisfy all control-flow correctness requirements specified in this document.

#### Scenario: Rust match arms all appear
- **WHEN** analyzing Rust match expressions
- **THEN** every arm pattern appears in the CFG, never omitted

#### Scenario: Rust error propagation correct
- **WHEN** analyzing `expr?` error propagation
- **THEN** Err branches route to function EXCEPTION_EXIT

#### Scenario: Rust break/continue scoped correctly
- **WHEN** analyzing nested loops with Rust break/continue
- **THEN** each break/continue routes to correct target, never to function exit

### Requirement: PHP analyzers SHALL implement full correctness contract
CodeFlow's PHP analyzer SHALL satisfy all control-flow correctness requirements specified in this document.

#### Scenario: PHP switch cases all appear
- **WHEN** analyzing PHP switch with multiple cases
- **THEN** every case appears as an outgoing edge, fall-through is represented

#### Scenario: PHP exception handling correct
- **WHEN** analyzing PHP try/catch/finally
- **THEN** exception paths route to correct catch handlers

#### Scenario: PHP loops and control flow correct
- **WHEN** analyzing PHP for/foreach/while with break/continue
- **THEN** break/continue route to correct targets
