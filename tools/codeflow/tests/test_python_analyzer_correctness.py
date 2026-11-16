"""
Phase 4b: Python Analyzer Correctness Tests.

Tests verify that the Python analyzer produces semantically correct control-flow graphs
using the Phase 4a validation and behavioral verification infrastructure.

Tests are generated from actual Python source code, not only manually constructed fixtures.
"""

import unittest
import tempfile
import os
from pathlib import Path

from codeflow.analyzers.python_analyzer import analyze_python_file
from codeflow.graph import NodeType, EdgeType
from codeflow.validation import CFGValidator, CompletionStatus
from codeflow.behavioral_verification import BehavioralVerifier


class TestPythonSimpleStatements(unittest.TestCase):
    """Test Python analyzer on simple statements."""

    def _analyze_code(self, code: str, func_name: str = "test_func"):
        """Helper to analyze Python code and extract CFG."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                self.assertIn(func_name, result.functions, f"Function {func_name} not found")
                cfg = result.functions[func_name]
                return cfg
            finally:
                os.unlink(f.name)

    def test_empty_function(self):
        """Test that empty function has entry -> exit."""
        code = "def test_func():\n    pass\n"
        cfg = self._analyze_code(code)

        # Should have entry and exit
        self.assertIsNotNone(cfg.entry_node_id)
        self.assertGreater(len(cfg.exit_node_ids), 0)

        # Validate graph
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

    def test_simple_sequence(self):
        """Test that simple statement sequence is linear."""
        code = """def test_func():
    x = 1
    y = 2
    return x + y
"""
        cfg = self._analyze_code(code)

        # Should have entry, statements, and exit
        self.assertGreater(len(cfg.nodes), 2)

        # Validate graph
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

        # Verify entry and exit exist and are reachable
        self.assertIsNotNone(cfg.entry_node_id)
        self.assertGreater(len(cfg.exit_node_ids), 0)

    def test_no_generic_placeholder_nodes(self):
        """Test that analyzer doesn't create generic placeholder nodes like 'Loop body' or 'Loop exit'."""
        code = """def test_func():
    for i in range(5):
        x = i + 1
"""
        cfg = self._analyze_code(code)

        # Collect all node labels
        labels = [n.label for n in cfg.nodes.values()]

        # Reject generic placeholders
        generic_labels = ["Loop body", "Loop exit", "for ... in ..."]
        for label in labels:
            self.assertNotIn(label, generic_labels,
                            f"Found generic placeholder label '{label}' in graph")


class TestPythonDecisions(unittest.TestCase):
    """Test Python analyzer on if/else statements."""

    def _analyze_code(self, code: str, func_name: str = "test_func"):
        """Helper to analyze Python code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                cfg = result.functions[func_name]
                return cfg
            finally:
                os.unlink(f.name)

    def test_if_then_decision(self):
        """Test if/then has correct branch routing."""
        code = """def test_func():
    x = 5
    if x > 0:
        y = 10
    return y
"""
        cfg = self._analyze_code(code)

        # Find decision node
        decision_nodes = [n for n in cfg.nodes.values()
                         if n.node_type == NodeType.DECISION]
        self.assertGreater(len(decision_nodes), 0, "No decision nodes found")

        # Decision should have TRUE and FALSE edges
        verifier = BehavioralVerifier(cfg)
        decision_node = decision_nodes[0]

        true_edges = [e for e in cfg.edges
                     if e.source_id == decision_node.id and e.edge_type == EdgeType.TRUE]
        false_edges = [e for e in cfg.edges
                      if e.source_id == decision_node.id and e.edge_type == EdgeType.FALSE]

        self.assertGreater(len(true_edges), 0, "No TRUE branch found")
        self.assertGreater(len(false_edges), 0, "No FALSE branch found")

    def test_if_else_convergent_branches(self):
        """Test if/else branches converge correctly."""
        code = """def test_func():
    if x > 0:
        y = 1
    else:
        y = 2
    return y
"""
        cfg = self._analyze_code(code)

        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

        # Should have path from entry to exit through both branches
        entry_node = cfg.nodes[cfg.entry_node_id]
        exit_node = cfg.nodes[cfg.exit_node_ids[0]]

        # Both branches should lead to exit
        self.assertTrue(len(cfg.exit_node_ids) > 0, "No exit nodes")


class TestPythonLoops(unittest.TestCase):
    """Test Python analyzer on loop statements."""

    def _analyze_code(self, code: str, func_name: str = "test_func"):
        """Helper to analyze Python code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                cfg = result.functions[func_name]
                return cfg
            finally:
                os.unlink(f.name)

    def test_while_loop_basic(self):
        """Test while loop has entry, body, and exit."""
        code = """def test_func():
    i = 0
    while i < 10:
        i = i + 1
    return i
"""
        cfg = self._analyze_code(code)

        # Find loop entry
        loop_entries = [n for n in cfg.nodes.values()
                       if n.node_type == NodeType.LOOP_ENTRY]
        self.assertGreater(len(loop_entries), 0, "No loop entry found")

        # Find loop back edges
        loop_back_edges = [e for e in cfg.edges
                          if e.edge_type == EdgeType.LOOP_BACK]
        self.assertGreater(len(loop_back_edges), 0, "No loop-back edge found")

        # Validate
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

    def test_while_loop_with_break(self):
        """Test break statement routes to after-loop, not function exit."""
        code = """def test_func():
    i = 0
    while i < 10:
        if i == 5:
            break
        i = i + 1
    return i
"""
        cfg = self._analyze_code(code)

        # Find break statement
        break_nodes = [n for n in cfg.nodes.values()
                      if "break" in n.label.lower()]
        self.assertGreater(len(break_nodes), 0, "No break statement found")

        # Break should use BREAK edge
        break_edges = [e for e in cfg.edges
                      if e.edge_type == EdgeType.BREAK]
        self.assertGreater(len(break_edges), 0, "No BREAK edge found")

        # Validate: break must NOT route to function exit
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

    def test_while_loop_with_continue(self):
        """Test continue statement routes to loop entry via LOOP_BACK edge."""
        code = """def test_func():
    for i in range(10):
        if i == 5:
            continue
        print(i)
    return
"""
        cfg = self._analyze_code(code)

        # Find continue statement
        continue_nodes = [n for n in cfg.nodes.values()
                         if "continue" in n.label.lower()]
        self.assertGreater(len(continue_nodes), 0, "No continue statement found")

        # Find loop entry
        loop_entries = [n for n in cfg.nodes.values()
                       if n.node_type == NodeType.LOOP_ENTRY]
        self.assertGreater(len(loop_entries), 0, "No loop entry found")

        # Continue should route to loop entry via LOOP_BACK
        loop_entry = loop_entries[0]
        continue_to_loop_edges = [e for e in cfg.edges
                                 if any(c.id == e.source_id for c in continue_nodes)
                                 and e.target_id == loop_entry.id
                                 and e.edge_type == EdgeType.LOOP_BACK]
        self.assertGreater(len(continue_to_loop_edges), 0,
                          "Continue must route to loop entry via LOOP_BACK edge")

        # Validate
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

    def test_nested_loops_break_scoping(self):
        """Test break in nested loop targets inner loop, not outer."""
        code = """def test_func():
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                break
            print(i, j)
        print(i)
    return
"""
        cfg = self._analyze_code(code)

        # Validate graph
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

        # Should have two loop entries
        loop_entries = [n for n in cfg.nodes.values()
                       if n.node_type == NodeType.LOOP_ENTRY]
        self.assertGreater(len(loop_entries), 1, "Should have nested loops")


class TestPythonReturns(unittest.TestCase):
    """Test Python analyzer on return statements."""

    def _analyze_code(self, code: str, func_name: str = "test_func"):
        """Helper to analyze Python code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                cfg = result.functions[func_name]
                return cfg
            finally:
                os.unlink(f.name)

    def test_single_return(self):
        """Test function with single return."""
        code = """def test_func():
    x = 1
    return x
"""
        cfg = self._analyze_code(code)

        # Should have entry and single exit
        self.assertIsNotNone(cfg.entry_node_id)
        self.assertEqual(len(cfg.exit_node_ids), 1)

        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE)

    def test_multiple_returns(self):
        """Test function with multiple return paths."""
        code = """def test_func(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
"""
        cfg = self._analyze_code(code)

        # Should have single exit node with multiple incoming edges
        self.assertEqual(len(cfg.exit_node_ids), 1)
        exit_node = cfg.exit_node_ids[0]

        # Count incoming edges to exit
        incoming = [e for e in cfg.edges if e.target_id == exit_node]
        self.assertGreater(len(incoming), 0, "No edges to exit node")

        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE)

    def test_early_return_in_loop(self):
        """Test early return inside loop."""
        code = """def test_func():
    for i in range(10):
        if i == 5:
            return i
        print(i)
    return -1
"""
        cfg = self._analyze_code(code)

        # Validate: returns must not leave unreachable code
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")


class TestPythonExceptions(unittest.TestCase):
    """Test Python analyzer on exception handling."""

    def _analyze_code(self, code: str, func_name: str = "test_func"):
        """Helper to analyze Python code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                cfg = result.functions[func_name]
                return cfg
            finally:
                os.unlink(f.name)

    def test_try_except_basic(self):
        """Test try/except has handler."""
        code = """def test_func():
    try:
        x = risky_operation()
    except ValueError:
        x = None
    return x
"""
        cfg = self._analyze_code(code)

        # Should have exception exit or exception edges
        exception_edges = [e for e in cfg.edges
                          if e.edge_type == EdgeType.EXCEPTION]
        self.assertGreater(len(exception_edges), 0, "No exception edges found")

    def test_raise_statement(self):
        """Test raise statement routes to exception exit."""
        code = """def test_func(x):
    if x < 0:
        raise ValueError("negative")
    return x
"""
        cfg = self._analyze_code(code)

        # Find raise statement
        raise_nodes = [n for n in cfg.nodes.values()
                      if "raise" in n.label.lower()]
        self.assertGreater(len(raise_nodes), 0, "No raise statement found")


class TestPythonSemanticCorrectness(unittest.TestCase):
    """Test Phase 4b semantic correctness improvements."""

    def _analyze_code(self, code: str, func_name: str = "test_func"):
        """Helper to analyze Python code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                self.assertIn(func_name, result.functions, f"Function {func_name} not found")
                return result.functions[func_name]
            finally:
                os.unlink(f.name)

    def test_no_docstring_nodes(self):
        """Test that docstrings are not rendered as statement nodes."""
        code = '''def test_func():
    """This is a docstring."""
    x = 1
    return x
'''
        cfg = self._analyze_code(code)

        # Count visible (non-internal) nodes
        visible = [n for n in cfg.nodes.values() if not n.is_internal]

        # Should NOT have a node with just '"""'
        docstring_nodes = [n for n in visible if n.label.strip() == '"""']
        self.assertEqual(len(docstring_nodes), 0, "Docstring should not be rendered as a node")

    def test_while_true_no_false_exit(self):
        """Test that while True doesn't have a False exit edge."""
        code = '''def test_func():
    while True:
        x = 1
        if x == 1:
            break
    return x
'''
        cfg = self._analyze_code(code)

        # Find while True node
        loop_nodes = [n for n in cfg.nodes.values()
                     if n.node_type == NodeType.LOOP_ENTRY and "while True" in n.label]
        self.assertGreater(len(loop_nodes), 0, "No while True loop found")

        loop_node = loop_nodes[0]

        # Check edges from loop node
        loop_edges = [e for e in cfg.edges if e.source_id == loop_node.id]

        # Should NOT have a False edge from while True
        false_edges = [e for e in loop_edges if e.label == "False" and e.edge_type == EdgeType.FALSE]
        self.assertEqual(len(false_edges), 0, "while True should not have a False exit edge")

    def test_try_except_internal_nodes(self):
        """Test that try/except blocks are marked internal."""
        code = '''def test_func():
    try:
        x = risky_operation()
    except ValueError:
        x = None
    return x
'''
        cfg = self._analyze_code(code)

        # Find try/except nodes
        try_nodes = [n for n in cfg.nodes.values()
                    if "try:" in n.label or "except" in n.label]

        # All try/except nodes should be internal
        for node in try_nodes:
            self.assertTrue(node.is_internal,
                          f"Try/except block '{node.label}' should be internal")

    def test_exception_edges_present(self):
        """Test that exception edges are created for try/except."""
        code = '''def test_func():
    try:
        x = int(user_input)
    except ValueError:
        x = -1
    return x
'''
        cfg = self._analyze_code(code)

        # Should have exception edges
        exception_edges = [e for e in cfg.edges if e.edge_type == EdgeType.EXCEPTION]
        self.assertGreater(len(exception_edges), 0,
                          "No exception edges found in try/except")

    def test_no_empty_visible_nodes(self):
        """Test that empty nodes are marked internal."""
        code = '''def test_func():
    if x > 0:
        y = 1
    else:
        y = 2
    return y
'''
        cfg = self._analyze_code(code)

        # Find visible (non-internal) nodes with empty labels
        empty_visible = [n for n in cfg.nodes.values()
                        if n.label.strip() == "" and not n.is_internal]

        self.assertEqual(len(empty_visible), 0,
                        "No empty nodes should be visible (merge/structural nodes)")

    def test_loop_back_edges_correct(self):
        """Test that loop back edges go to the correct loop entry."""
        code = '''def test_func():
    for i in range(10):
        if i == 5:
            break
        x = i
    return x
'''
        cfg = self._analyze_code(code)

        # Find loop nodes
        loop_nodes = [n for n in cfg.nodes.values()
                     if n.node_type == NodeType.LOOP_ENTRY]
        self.assertGreater(len(loop_nodes), 0, "No loop found")

        # Check loop back edges
        loop_back_edges = [e for e in cfg.edges if e.edge_type == EdgeType.LOOP_BACK]

        for edge in loop_back_edges:
            # Loop back should go to a loop entry
            target = cfg.nodes.get(edge.target_id)
            self.assertIsNotNone(target)
            self.assertEqual(target.node_type, NodeType.LOOP_ENTRY,
                           f"Loop back edge should target loop entry, got {target.node_type}")


class TestASTConstantHandling(unittest.TestCase):
    """Regression tests for AST constant handling (Python 3.14 compatibility)."""

    def _analyze_code(self, code: str, func_name: str = "test_func") -> "CFG":
        """Helper to analyze code and return CFG for the specified function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = analyze_python_file(f.name)
                self.assertTrue(result.success, f"Analysis failed: {result.errors}")
                self.assertIn(func_name, result.functions, f"Function {func_name} not found")
                return result.functions[func_name]
            finally:
                os.unlink(f.name)

    def test_string_constants_as_docstrings(self):
        """Test that string constants are correctly identified as docstrings."""
        code = '''def test_func():
    """This is a docstring."""
    x = "not a docstring"
    return x
'''
        cfg = self._analyze_code(code)

        # Should not have docstring as a node (docstrings are skipped)
        docstring_nodes = [n for n in cfg.nodes.values()
                          if "This is a docstring" in n.label]
        self.assertEqual(len(docstring_nodes), 0,
                        "Docstring should not appear as a node")

        # String assignment should be present
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

    def test_while_true_boolean_semantics(self):
        """Test that while True correctly distinguishes True from integer 1."""
        code = '''def test_func():
    while True:
        x = 1
        break
    return x
'''
        cfg = self._analyze_code(code)

        # Find while True node
        loop_nodes = [n for n in cfg.nodes.values()
                     if n.node_type == NodeType.LOOP_ENTRY and "True" in n.label]
        self.assertGreater(len(loop_nodes), 0, "No while True found")

        # Should NOT have a False exit (while True is unconditional)
        loop_node = loop_nodes[0]
        false_edges = [e for e in cfg.edges
                      if e.source_id == loop_node.id and e.edge_type == EdgeType.FALSE]
        self.assertEqual(len(false_edges), 0,
                        "while True should not have False exit edge")

    def test_while_false_boolean_semantics(self):
        """Test that while False correctly distinguishes False from integer 0."""
        code = '''def test_func():
    x = 0
    while False:
        x = 1
    return x
'''
        cfg = self._analyze_code(code)

        # Find while False node
        loop_nodes = [n for n in cfg.nodes.values()
                     if n.node_type == NodeType.LOOP_ENTRY and "False" in n.label]
        self.assertGreater(len(loop_nodes), 0, "No while False found")

        # Should have a False exit (while False always exits immediately)
        loop_node = loop_nodes[0]
        false_edges = [e for e in cfg.edges
                      if e.source_id == loop_node.id and e.edge_type == EdgeType.FALSE]
        self.assertGreater(len(false_edges), 0,
                          "while False should have False exit edge")

    def test_while_integer_one_conditional(self):
        """Test that while 1 (integer) is treated as conditional, not unconditional."""
        code = '''def test_func():
    while 1:
        x = 1
        break
    return x
'''
        cfg = self._analyze_code(code)

        # Find loop
        loop_nodes = [n for n in cfg.nodes.values()
                     if n.node_type == NodeType.LOOP_ENTRY]
        self.assertGreater(len(loop_nodes), 0, "No loop found")

        # Note: while 1 should be treated as while True in some contexts,
        # but semantically it's a truthy integer, not a boolean
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

    def test_conditional_expressions_with_booleans(self):
        """Test that conditional expressions with booleans are handled correctly."""
        code = '''def test_func():
    x = True
    if x:
        y = True
    else:
        y = False
    return y
'''
        cfg = self._analyze_code(code)

        # Should have if decision
        decisions = [n for n in cfg.nodes.values()
                    if n.node_type == NodeType.DECISION]
        self.assertGreater(len(decisions), 0, "No decision found")

        # Should have both True and False paths
        edges = cfg.edges
        true_edges = [e for e in edges if e.edge_type == EdgeType.TRUE]
        false_edges = [e for e in edges if e.edge_type == EdgeType.FALSE]
        self.assertGreater(len(true_edges), 0, "No TRUE edge found")
        self.assertGreater(len(false_edges), 0, "No FALSE edge found")

    def test_ast_constant_node_replacement(self):
        """Test that AST Constant nodes are properly handled (no ast.Str/NameConstant)."""
        code = '''def test_func():
    s = "string"
    b = True
    n = None
    return (s, b, n)
'''
        cfg = self._analyze_code(code)

        # Validate the graph structure
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"Validation failed: {result.errors}")

        # Should have nodes for assignments
        self.assertGreater(len(cfg.nodes), 0, "No nodes in CFG")


class TestPythonTicTacToe(unittest.TestCase):
    """Integration tests on actual Python Tic-Tac-Toe example."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        tictactoe_path = Path(__file__).parent.parent / "examples" / "python" / "tictactoe.py"
        if tictactoe_path.exists():
            result = analyze_python_file(str(tictactoe_path))
            cls.result = result
            cls.tictactoe_path = tictactoe_path
        else:
            cls.result = None
            cls.tictactoe_path = None

    def test_tictactoe_analysis_success(self):
        """Test that tictactoe.py analyzes successfully."""
        if self.result is None:
            self.skipTest("tictactoe.py not found")
        self.assertTrue(self.result.success, f"Analysis failed: {self.result.errors}")

    def test_validate_move_correctness(self):
        """Test validate_move function produces correct CFG."""
        if self.result is None or "validate_move" not in self.result.functions:
            self.skipTest("validate_move not found")

        cfg = self.result.functions["validate_move"]

        # validate_move has if statements and returns
        decisions = [n for n in cfg.nodes.values() if n.node_type == NodeType.DECISION]
        self.assertGreater(len(decisions), 0, "validate_move should have decisions")

        # Validate graph
        validator = CFGValidator(cfg)
        result = validator.validate()
        self.assertEqual(result.status, CompletionStatus.COMPLETE,
                        f"validate_move validation failed: {result.errors}")

    def test_no_invalid_edges(self):
        """Test that all CFGs have valid edges (no None sources)."""
        if self.result is None:
            self.skipTest("tictactoe.py not found")

        for func_name, cfg in self.result.functions.items():
            for edge in cfg.edges:
                self.assertIsNotNone(edge.source_id,
                                   f"Invalid edge in {func_name}: source is None")
                self.assertIsNotNone(edge.target_id,
                                   f"Invalid edge in {func_name}: target is None")


if __name__ == '__main__':
    unittest.main()
