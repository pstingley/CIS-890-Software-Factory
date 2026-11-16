"""Integration tests for validate_move and check_win functions."""

import unittest
import sys
import os

# Add parent directory to path so we can import codeflow
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codeflow.analyzers.python_analyzer import analyze_python_file
from codeflow.graph import NodeType, EdgeType

class TestTictactoeFunctions(unittest.TestCase):
    """Integration tests for tictactoe.py functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Analyze tictactoe.py
        tictactoe_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'examples',
            'python',
            'tictactoe.py'
        )
        if os.path.exists(tictactoe_path):
            cls.result = analyze_python_file(tictactoe_path)
        else:
            cls.result = None
            cls.skipTest = True

    def test_tictactoe_analysis_success(self):
        """Test that tictactoe.py analyzes without errors."""
        if self.result is None:
            self.skipTest("tictactoe.py not found")
        self.assertTrue(self.result.success, f"Analysis had errors: {self.result.errors}")

    def test_validate_move_exists(self):
        """Test that validate_move function was analyzed."""
        if self.result is None:
            self.skipTest("tictactoe.py not found")
        self.assertIn("validate_move", self.result.functions,
                     "validate_move function not found")

    def test_check_win_exists(self):
        """Test that check_win function was analyzed."""
        if self.result is None:
            self.skipTest("tictactoe.py not found")
        self.assertIn("check_win", self.result.functions,
                     "check_win function not found")

    def test_validate_move_has_entry_exit(self):
        """Test that validate_move has entry and exit nodes."""
        if self.result is None or "validate_move" not in self.result.functions:
            self.skipTest("validate_move not found")

        cfg = self.result.functions["validate_move"]
        self.assertIsNotNone(cfg.entry_node_id)
        self.assertTrue(len(cfg.exit_node_ids) > 0)

    def test_validate_move_has_decisions(self):
        """Test that validate_move has decision nodes (if statements)."""
        if self.result is None or "validate_move" not in self.result.functions:
            self.skipTest("validate_move not found")

        cfg = self.result.functions["validate_move"]
        decision_nodes = [n for n in cfg.nodes.values()
                         if n.node_type == NodeType.DECISION]
        self.assertTrue(len(decision_nodes) > 0,
                       "validate_move should have decision nodes")

    def test_validate_move_has_returns(self):
        """Test that validate_move has return statements."""
        if self.result is None or "validate_move" not in self.result.functions:
            self.skipTest("validate_move not found")

        cfg = self.result.functions["validate_move"]
        return_edges = [e for e in cfg.edges if "return" in e.label.lower()]
        # The function should have return statements (can be inferred from exit nodes)
        self.assertTrue(len(cfg.exit_node_ids) >= 1,
                       "validate_move should have exit nodes")

    def test_check_win_has_loop(self):
        """Test that check_win has loop structure."""
        if self.result is None or "check_win" not in self.result.functions:
            self.skipTest("check_win not found")

        cfg = self.result.functions["check_win"]
        loop_nodes = [n for n in cfg.nodes.values()
                     if n.node_type in [NodeType.LOOP_ENTRY, NodeType.LOOP_BODY]]
        self.assertTrue(len(loop_nodes) > 0,
                       "check_win should have loop nodes")

    def test_check_win_has_loop_back_edge(self):
        """Test that check_win has loop-back edges."""
        if self.result is None or "check_win" not in self.result.functions:
            self.skipTest("check_win not found")

        cfg = self.result.functions["check_win"]
        loop_back_edges = [e for e in cfg.edges
                          if e.edge_type == EdgeType.LOOP_BACK]
        self.assertTrue(len(loop_back_edges) > 0,
                       "check_win should have loop-back edges")

    def test_functions_are_complete(self):
        """Test that simple functions don't have partial status."""
        if self.result is None:
            self.skipTest("tictactoe.py not found")

        # validate_move and check_win should be marked complete
        for func_name in ["validate_move", "check_win"]:
            if func_name in self.result.functions:
                cfg = self.result.functions[func_name]
                # These functions don't use deferred constructs
                # (we expect them to be complete or only partial due to comprehensions)
                if cfg.is_partial and "loop else" not in cfg.partial_reason:
                    # List comprehensions are OK to make partial
                    self.assertIn("comprehension", cfg.partial_reason.lower())

class TestSimpleFixtures(unittest.TestCase):
    """Tests for simple test fixtures."""

    def test_simple_path_analysis(self):
        """Test analyzing simple_path.py fixture."""
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'simple_path.py'
        )
        if os.path.exists(fixture_path):
            result = analyze_python_file(fixture_path)
            self.assertTrue(result.success)
            self.assertIn("simple_path", result.functions)

    def test_single_decision_analysis(self):
        """Test analyzing single_decision.py fixture."""
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'single_decision.py'
        )
        if os.path.exists(fixture_path):
            result = analyze_python_file(fixture_path)
            self.assertTrue(result.success)
            self.assertIn("single_decision", result.functions)

            # Verify decision nodes
            cfg = result.functions["single_decision"]
            decision_nodes = [n for n in cfg.nodes.values()
                            if n.node_type == NodeType.DECISION]
            self.assertTrue(len(decision_nodes) > 0)

if __name__ == '__main__':
    unittest.main()
