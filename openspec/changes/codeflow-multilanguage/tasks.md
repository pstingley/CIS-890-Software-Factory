# Implementation Tasks: CodeFlow Multilanguage Support with PHP

## Regression Test Baseline

**Verified Test Count**: 107 passing + 2 skipped (independent verification)
- Python and SPEC.md tests: 68 passing
- Rust and integration tests: 39 passing
- Skipped: 2
- Total verified: 109 tests (107 passing + 2 skipped)

**Baseline Preservation Requirement:** All 107 currently passing tests must continue to pass throughout Phase 1-5 implementation. This is the primary regression gate.

**Canonical Test Command** (always use this full list, never wildcards):
```bash
python -m pytest tools/codeflow/tests/ -q
```

---

## Implementation Overview: Shared Correctness Contract First

CodeFlow 0.3 implements a **language-independent control-flow correctness contract** (Specification R1-R11, Testing T1-T8) across Python, Rust, and PHP.

**Key Insight:** The shared control-flow graph infrastructure and behavioral verification framework must be established and validated before language-specific analyzer corrections. This prevents shipping incomplete or incorrect analysis in any language.

### Implementation Sequence:
- **Phase 1** (Week 1): Shared Control-Flow Graph Correctness Infrastructure
- **Phase 2** (Week 2): Python Analyzer Correctness Against Contract
- **Phase 3** (Weeks 3-4): Rust Analyzer Correctness Against Contract
- **Phase 4** (Week 5): Cross-Language Verification (Python/Rust equivalence)
- **Phase 5** (Weeks 6-8): PHP Implementation Against Validated Contract

**Target: 107+ tests passing throughout, 150+ tests at completion**

---

## Phase 1: Shared Control-Flow Graph Correctness Infrastructure (Week 1)

**Objective:** Establish and test the shared infrastructure that all analyzers (Python, Rust, PHP) will use to build correct control-flow graphs. This is **not language-specific** but applies to all analyzers.

### Group 1.1: Control-Flow Graph Correctness Infrastructure

- [ ] 1.1.1 Review and audit current `codeflow/graph.py` against correctness contract (R1-R8)
  - Verify CFGNode class supports semantic labels (not AST types)
  - Verify CFG class tracks entry/exit nodes correctly
  - Verify edge types include decision/true/false/loop-back/exception labels
  - Verify source_reference field present (file, line, code)
  - Verify is_partial flag exists for incomplete analysis marking
  - Document any gaps or required enhancements
  - Verify by code review: graph structure matches all 8 universal requirements

- [ ] 1.1.2 Implement CFG validation function in `codeflow/graph.py`
  - Add `validate_graph(cfg: CFG, language: str) -> List[str]` function
  - Checks:
    - Entry node exists and has outgoing edges
    - All nodes reachable from entry have path to exit (normal or exception)
    - Decision nodes have correct branch labels (true/false, case names, pattern matches)
    - Loop nodes have back-edges to correct targets
    - Return nodes connect to normal EXIT
    - Exception nodes connect to EXCEPTION_EXIT
    - No syntactic-punctuation nodes (`{`, `}`, `;`)
    - All statement labels are executable operations, not AST types
  - Return list of validation errors (empty if valid)
  - Verify: test with correct and incorrect CFGs

- [ ] 1.1.3 Add source-expression tracking to CFGNode
  - Field: `full_source_expr: str` - complete source code for the statement/decision
  - Field: `display_label: str` - potentially truncated display label (max ~80 chars)
  - Field: `source_reference: Tuple[str, int]` - (file_path, line_number_1indexed)
  - Method: `get_tooltip_text() -> str` - returns full expression for hover/tooltip
  - Verify by inspection: CFGNode can store and retrieve full expressions

- [ ] 1.1.4 Implement shared exception-path handling
  - Define standard exception edge type distinct from normal edges
  - Implement exception routing in graph builder (all analyzers will use this)
  - Exception nodes must connect to EXCEPTION_EXIT, never normal EXIT
  - Function must have EXCEPTION_EXIT node if any exception paths exist
  - Verify: build simple CFG with exception, validate structure

- [ ] 1.1.5 Implement shared loop-construct helpers
  - Helper functions for all analyzers to construct loop CFGs correctly:
    - `create_loop_cfg(condition_node, loop_body_cfgs, break_target, continue_target, language) -> CFG`
    - `route_break_to_loop_exit(break_node, containing_loop_node) -> Edge`
    - `route_continue_to_loop_test(continue_node, containing_loop_node) -> Edge`
  - These ensure consistent loop routing across Python, Rust, PHP
  - Verify: construct nested loops, verify break/continue routing

### Group 1.2: Behavioral Verification Test Framework

- [ ] 1.2.1 Implement graph-verification assertion API in `tests/test_helpers.py`
  - `assert_node_exists(cfg: CFG, label_substring: str) -> CFGNode` - find node by label
  - `assert_edge_exists(cfg: CFG, from_label: str, to_label: str, edge_type: str) -> Edge` - verify specific edge
  - `assert_path_exists(cfg: CFG, path: List[str]) -> bool` - verify sequence of nodes reachable
  - `assert_no_syntactic_nodes(cfg: CFG) -> List[str]` - return list of any `{`, `}`, `;` nodes (should be empty)
  - `assert_all_nodes_have_sources(cfg: CFG) -> List[str]` - verify all nodes have file/line (return missing)
  - `assert_graph_valid(cfg: CFG, language: str) -> List[str]` - calls validate_graph, returns errors
  - `assert_decision_has_branches(cfg: CFG, decision_label: str, expected_branches: List[str])` - verify decision branches
  - `assert_loop_has_backedge(cfg: CFG, loop_label: str)` - verify loop back-edge exists
  - Verify: all functions work in standalone tests

- [ ] 1.2.2 Create `tests/test_control_flow_correctness.py` with shared infrastructure tests
  - **R1 Semantic Labeling Tests** (~5 tests)
    - test_no_ast_node_type_labels (verify no "let_declaration", "call_expression")
    - test_no_syntactic_punctuation_nodes (verify no `{`, `}` nodes)
    - test_statement_labels_are_operations (verify labels describe actual code)
    - test_decision_condition_in_label (verify if/match conditions visible)
    - test_full_source_expr_accessible (verify full code available via tooltip)

  - **R2 Decision Branch Correctness Tests** (~6 tests)
    - test_if_true_false_edges (verify if has true/false branches)
    - test_if_else_both_paths_shown (verify both branches connected)
    - test_match_all_arms_present (verify no arms omitted)
    - test_switch_case_edges (verify each case has edge)
    - test_nested_decisions_routing (verify nested if inside if, then, else)
    - test_decision_condition_matches_source (verify condition label matches actual code)

  - **R3 Loop Routing Tests** (~8 tests)
    - test_loop_has_backedge (verify back-edge to loop entry)
    - test_break_exits_loop_not_function (verify break → loop exit, not function exit)
    - test_continue_reaches_loop_test (verify continue → loop condition/top)
    - test_nested_loops_break_routing (verify inner break exits inner loop, not outer)
    - test_nested_loops_continue_routing (verify inner continue targets inner loop)
    - test_for_loop_iteration (verify loop structure preserved)
    - test_while_loop_condition (verify condition at loop entry)
    - test_do_while_executes_once (verify body before condition check)

  - **R4 Return Path Tests** (~4 tests)
    - test_return_connects_to_exit (verify return → function EXIT)
    - test_multiple_returns_shown (verify CFG shows all return points)
    - test_implicit_return_connected (verify implicit return at end → EXIT)
    - test_no_return_path_to_exception_exit (verify return never goes to EXCEPTION_EXIT)

  - **R5 Exception Path Tests** (~4 tests)
    - test_exception_edges_to_exception_exit (verify exception → EXCEPTION_EXIT)
    - test_try_catch_routing (verify try body has exception edge to catch)
    - test_multiple_catch_branches (verify each catch is separate branch)
    - test_throw_routes_to_exception_exit (verify throw → EXCEPTION_EXIT)

  - **R6 Graph Validation Tests** (~5 tests)
    - test_all_nodes_reachable (verify no orphaned nodes)
    - test_all_paths_terminate (verify all paths reach exit)
    - test_no_invalid_cycles (verify only loop back-edges)
    - test_entry_has_outgoing_edges (verify entry not empty)
    - test_exit_has_incoming_edges (verify exit reachable)

  - **R7 Traceability Tests** (~4 tests)
    - test_all_nodes_have_source_references (verify file/line present)
    - test_source_line_matches_code (verify line numbers correct)
    - test_full_expression_available (verify complete source accessible)
    - test_source_ref_format_consistent (verify tuple format: (file, line_1indexed))

  - **R8 Partial Analysis Marking Tests** (~5 tests)
    - test_unsupported_construct_sets_partial (verify is_partial=True)
    - test_incomplete_analysis_not_marked_complete (verify flag blocks COMPLETE)
    - test_ambiguity_flags_documented (verify reason in ambiguity_flags list)
    - test_dynamic_behavior_flagged (verify unresolved calls flagged)
    - test_parsing_errors_flagged (verify syntax errors marked)

- [ ] 1.2.3 Create `tests/fixtures/correctness_examples/` with representative programs
  - `simple_if.py`, `nested_if.rs` - decision correctness
  - `for_loop.py`, `while_loop.rs`, `do_while.php` - loop routing
  - `nested_loops.py` - break/continue in nested context
  - `multiple_returns.rs` - return path verification
  - `try_catch.php` - exception routing
  - `empty_function.rs` - empty blocks without syntax nodes
  - `mixed_control_flow.py` - complex program with all features
  - Verify: all fixtures are syntactically valid and analyzable

### Group 1.3: Verification Gate

- [ ] 1.3.1 Run baseline tests against shared infrastructure
  - Run: `python -m pytest tests/test_control_flow_correctness.py -v`
  - Verify: all 32+ infrastructure tests pass
  - Verify: Python/SPEC.md tests unchanged, all 68 passing
  - Verify: Rust/integration tests - document current status (expected failures)
  - **Gate: All 107 baseline tests must still pass. If regression detected, fix before proceeding.**

- [ ] 1.3.2 Run OpenSpec validation
  - Run: `openspec validate codeflow-multilanguage --strict`
  - Verify: 0 errors, 0 warnings
  - Verify: control-flow-correctness and behavioral-verification specs present

---

## Phase 2: Python Analyzer Correctness Against Contract (Week 2)

**Objective:** Verify existing Python analyzer satisfies the control-flow correctness contract. Make only necessary correctness improvements to reach 107+ passing tests.

### Group 2.1: Python Analyzer Audit Against Correctness Contract

- [ ] 2.1.1 Audit Python analyzer against R1-R8 requirements
  - Review `codeflow/analyzers/python_analyzer.py` for semantic labeling (R1)
  - Review decision routing: if, elif, else handling (R2)
  - Review loop routing: for, while, break, continue (R3)
  - Review return path handling (R4)
  - Review exception handling: try/except/finally (R5)
  - Verify graph validation applied (R6)
  - Verify source references present (R7)
  - Verify is_partial flag handling (R8)
  - Document findings: what works, what needs correction

- [ ] 2.1.2 Identify Python correctness defects
  - Use test results from Phase 1.3.1 to identify specific failures
  - For each failure, determine root cause:
    - Semantic labeling issue (R1) → document which constructs mislabeled
    - Branch routing issue (R2) → document which paths incorrect
    - Loop routing issue (R3) → document which loops/breaks/continues wrong
    - Return routing issue (R4) → document which returns routed incorrectly
    - Exception routing issue (R5) → document which exceptions misrouted
    - Graph validation issue (R6) → document structural errors
    - Traceability issue (R7) → document missing/wrong references
    - Partial marking issue (R8) → document incomplete analysis marked complete
  - Prioritize by impact (how many tests fail)

- [ ] 2.1.3 Add Python-specific behavioral tests (R9)
  - Extend `tests/test_control_flow_correctness.py` with Python-specific tests (~10-15 tests)
  - Test Python-specific constructs: for loops (enumerate, zip), comprehensions, generators, with statements, context managers
  - Verify each construct produces correct control-flow graph
  - Verify nested structures (for inside if, try inside while, etc.)
  - Create fixtures for each test in `tests/fixtures/correctness_examples/`

### Group 2.2: Python Analyzer Correctness Fixes

- [ ] 2.2.1 Fix Python semantic labeling (if needed, per audit in 2.1.2)
  - Ensure all statement labels show actual Python code, not AST types
  - Ensure decision labels show actual conditions (e.g., `if x > 10:` not `if_statement`)
  - Ensure loop labels show actual iteration (e.g., `for item in list:` not `for_statement`)
  - Verify via inspection and behavioral tests in 2.1.3

- [ ] 2.2.2 Fix Python decision routing (if needed, per audit in 2.1.2)
  - Verify if/elif/else chains produce correct branch graph
  - Verify nested if statements produce correct nested branches
  - Verify boolean operators (and, or) handled correctly
  - Verify no false branches missing
  - Test via `tests/test_control_flow_correctness.py` decision tests

- [ ] 2.2.3 Fix Python loop routing (if needed, per audit in 2.1.2)
  - Verify for/while loops have back-edges to loop entry
  - Verify break statements exit to loop-exit node, not function exit
  - Verify continue statements jump to loop-condition, not arbitrary target
  - Verify nested loops break/continue route to correct enclosing loop
  - Test via `tests/test_control_flow_correctness.py` loop tests

- [ ] 2.2.4 Fix Python exception routing (if needed, per audit in 2.1.2)
  - Verify try/except blocks route exceptions correctly
  - Verify finally blocks execute before exit
  - Verify raise statements route to EXCEPTION_EXIT
  - Test via `tests/test_control_flow_correctness.py` exception tests

- [ ] 2.2.5 Apply source-reference tracking improvements (if needed)
  - Ensure all CFG nodes have file/line from Python AST
  - Ensure full source expressions captured for all statements
  - Verify source references traceability via behavioral tests
  - Test via R7 traceability tests in `tests/test_control_flow_correctness.py`

### Group 2.3: Verification Gate

- [ ] 2.3.1 Run full test suite including Phase 1 and Python-specific tests
  - Run: `python -m pytest tools/codeflow/tests/ -q`
  - Confirm: 107+ tests passing (at least 107, potentially with new Python-specific tests)
  - Confirm: 0 regressions in original baseline tests
  - **Gate: Must have 107+ passing tests before proceeding to Phase 3**

- [ ] 2.3.2 Verify Python analyzer satisfies correctness contract
  - Run Python analyzer on representative Python programs from fixtures
  - Visually inspect generated SVG flowcharts: semantic labels, correct branches, loop routing
  - Verify no `{`, `}` nodes
  - Verify source references correct
  - Verify is_partial flag correct
  - Run `openspec validate codeflow-multilanguage --strict`
  - Verify: 0 errors, 0 warnings

---

## Phase 3: Rust Analyzer Correctness Against Contract (Weeks 3-4)

**Objective:** Implement Rust analyzer satisfying the full correctness contract (R1-R8, R10). Use Tic-Tac-Toe acceptance test.

### Group 3.1: Rust Analyzer Architecture Review

- [ ] 3.1.1 Review existing `codeflow/analyzers/rust_analyzer.py` against R1-R8, R10
  - Semantic labeling (R1): verify all labels are actual Rust code
  - Decision routing (R2, R10): verify if/match branches all present and routed correctly
  - Loop routing (R3, R10): verify for/while/loop back-edges, break/continue routing
  - Return routing (R4): verify returns to EXIT
  - Exception routing (R5, R10): verify ? operator and Result-based errors routed correctly
  - Graph validation (R6): run validation checks
  - Traceability (R7): verify source references present
  - Partial marking (R8): verify incomplete analysis marked
  - Rust-specific (R10): async/await, closures, macros detection
  - Document current state: what satisfies contract, what needs fixes

- [ ] 3.1.2 Identify Rust analyzer correctness defects (referencing initial problem report)
  - R3 Loop Routing: break routing to function EXIT instead of loop exit (TEST T4)
  - R3 Loop Routing: continue routing to wrong nodes (TEST T4)
  - R2, R10 Match Arms: match expression arms missing/incomplete (TEST T3)
  - R1 Semantic Labeling: generic node type labels instead of actual code (TEST T2)
  - R6, R8 Partial Marking: graphs with unsupported constructs marked COMPLETE (TEST T6)
  - Prioritize fixes by severity: break/continue routing must be correct before shipping

### Group 3.2: Rust-Specific Behavioral Tests

- [ ] 3.2.1 Create `tests/test_rust_correctness.py` with Rust-specific tests (~25-30 tests)
  - Extend Phase 1 shared tests with Rust-specific constructs (~15-20 Rust-specific tests)
  - R10 Async/Await: test detection, unsupported marking (async fn, .await)
  - R10 Closures: test detection, unsupported marking (|x| ..., move |x| ...)
  - R10 Macros: test detection, unsupported marking (println!, vec!, etc.)
  - R10 Complex Generics: test detection, unsupported marking (Trait<T: Bound>)
  - R10 Error Handling: test ? operator routing (TEST T5)
  - Create fixtures for all Rust-specific tests in `tests/fixtures/correctness_examples/rust/`

### Group 3.3: Rust Analyzer Corrections

- [ ] 3.3.1 Fix R3 Loop Routing (break/continue)
  - Fix: break statements must route to immediately enclosing loop exit, never function exit
  - Fix: continue statements must route to immediately enclosing loop test/entry, never function exit or wrong loop
  - Implementation: use loop-construct helpers from Phase 1.1.5
  - Test: run loop routing tests from Phase 1.2.2 R3 tests
  - Test: run Rust-specific loop tests from 3.2.1

- [ ] 3.3.2 Fix R2, R10 Match Arm Routing
  - Fix: all match expression arms must be present in CFG
  - Fix: each arm must have edge from match decision node
  - Fix: arm pattern must be visible (R1 semantic labeling)
  - Implementation: verify tree-sitter match_expression parsing includes all arms
  - Test: run decision branch tests from Phase 1.2.2 R2
  - Test: run Rust match-specific tests from 3.2.1

- [ ] 3.3.3 Fix R1 Semantic Labeling (Generic Node Types)
  - Fix: replace generic labels like "let_declaration", "call_expression" with actual code
  - Method: extract source text from tree-sitter node position in source file
  - Implementation: use full_source_expr field added in Phase 1.1.3
  - Test: run R1 semantic labeling tests from Phase 1.2.2
  - Test: verify no "let_declaration", "call_expression", etc. in generated labels

- [ ] 3.3.4 Fix R6, R8 Partial Marking (Incomplete Analysis)
  - Fix: graphs with unsupported constructs (R10 categories) must have is_partial=True
  - Fix: reason must be in ambiguity_flags list
  - Fix: graph must NOT be marked COMPLETE if any unsupported constructs found
  - Implementation: set is_partial=True when any R10 unsupported construct encountered
  - Test: run R8 partial marking tests from Phase 1.2.2
  - Test: verify graphs with async/await, macros, etc. marked partial

- [ ] 3.3.5 Apply source-reference improvements
  - Ensure all CFG nodes have file/line from tree-sitter positions
  - Ensure full source expressions captured for all statements
  - Use source-expression tracking from Phase 1.1.3
  - Test: run R7 traceability tests from Phase 1.2.2

### Group 3.4: Rust Analyzer Testing with Tic-Tac-Toe

- [ ] 3.4.1 Verify Rust Tic-Tac-Toe acceptance test
  - Location: `tools/codeflow/examples/rust/tictactoe/`
  - Run: `python -m codeflow project tools/codeflow/examples/rust/tictactoe/`
  - Verify: generates HTML index report with links to individual function SVGs
  - Verify: main.rs functions analyzed correctly
  - Verify: lib.rs functions analyzed correctly
  - Verify: cross-file relationships identified (main calls lib functions)
  - Verify: no syntactic nodes (`{`, `}`)
  - Verify: semantic labels show actual Rust code
  - Verify: break/continue routing correct in game loop
  - Verify: match expressions (if present) have all arms
  - Visually inspect representative functions: game loop, move validation, win detection
  - Verify: control-flow matches actual Rust execution semantics

- [ ] 3.4.2 Document Rust analyzer limitations
  - Explicitly mark what constructs are unsupported: async/await, macros, complex generics, closures
  - Verify is_partial=True for TicTacToe if any unsupported constructs present
  - Or verify is_partial=False and ambiguity_flags=[] if fully supported

### Group 3.5: Verification Gate

- [ ] 3.5.1 Run full test suite (Phases 1, 2, 3)
  - Run: `python -m pytest tools/codeflow/tests/ -q`
  - Confirm: 107+ tests passing
  - Confirm: 0 regressions in baseline tests
  - Confirm: Rust-specific tests passing
  - Confirm: 2 skipped (unchanged from baseline)
  - **Gate: Must have 107+ passing tests with Rust fixes before proceeding**

- [ ] 3.5.2 Verify Rust analyzer satisfies correctness contract
  - Run Rust analyzer on representative Rust programs from fixtures
  - Visually inspect generated SVG flowcharts: semantic labels, correct branches, loop routing, match arms
  - Verify no `{`, `}` nodes
  - Verify source references correct
  - Verify is_partial flag correct
  - Run `openspec validate codeflow-multilanguage --strict`
  - Verify: 0 errors, 0 warnings

---

## Phase 4: Cross-Language Verification (Week 5)

**Objective:** Verify consistent control-flow semantics across Python and Rust using equivalent programs.

### Group 4.1: Equivalent Program Pairs

- [ ] 4.1.1 Create equivalent Python/Rust program pairs
  - `fibonacci.py` / `fibonacci.rs` - simple recursion and loops
  - `search_array.py` / `search_array.rs` - decision trees and early return
  - `validate_input.py` / `validate_input.rs` - nested conditionals and error handling
  - `game_turn.py` / `game_turn.rs` - complex control flow (from TicTacToe)
  - Verify: programs have identical execution logic, different syntax

### Group 4.2: Cross-Language CFG Comparison

- [ ] 4.2.1 Create `tests/test_cross_language_verification.py`
  - For each equivalent pair, generate Python and Rust CFGs
  - Compare structure: same decision points, same loop structure, same return/exception routing
  - Create assertion helpers to compare graphs structure-wise (allowing for language-specific details)
  - Test: Python fibonacci CFG matches Rust fibonacci CFG in structure
  - Test: Python search CFG matches Rust search CFG
  - Etc. for all equivalent pairs
  - Verify: 5-10 cross-language verification tests pass

### Group 4.3: Verification Gate

- [ ] 4.3.1 Run cross-language verification suite
  - Run: `python -m pytest tests/test_cross_language_verification.py -v`
  - Confirm: all cross-language tests pass
  - Confirm: 107+ baseline tests still passing
  - **Gate: Cross-language consistency verified before PHP implementation**

---

## Phase 5: PHP Implementation Against Validated Contract (Weeks 6-8)

**Objective:** Implement PHP analyzer satisfying full correctness contract (R1-R8, R11) using validated infrastructure from Phases 1-4.

**Requirement:** PHP implementation deferred until Phases 1-4 complete and all infrastructure validated. This prevents shipping incomplete analysis and ensures PHP follows same correctness standards as Python and Rust.

---

## Summary: Why This Order Matters

1. **Phase 1 (Shared Infrastructure)**: Establishes the correctness contract and behavioral tests that ALL analyzers must satisfy. Without this, language-specific fixes lack a unified standard.

2. **Phase 2 (Python Correctness)**: Verifies existing Python analyzer meets contract. If Python can't satisfy the contract, Rust and PHP implementations will fail too.

3. **Phase 3 (Rust Correctness)**: Implements new language using validated contract and infrastructure. Rust-specific fixes (break/continue routing, match arms, semantic labeling) are tested against Phase 1 behavioral framework.

4. **Phase 4 (Cross-Language Verification)**: Ensures consistent semantics across languages. This is the validation gate for correctness.

5. **Phase 5 (PHP Implementation)**: Can proceed with confidence knowing Python/Rust are correct, infrastructure is robust, and cross-language verification has passed. PHP follows same contract, benefits from shared infrastructure.
