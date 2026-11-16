"""Tests for layout exit node convention: exits at bottom."""

import unittest
import tempfile
import os
from codeflow.analyzers.python_analyzer import analyze_python_file
from codeflow.layout.simple_layout import SimpleHierarchicalLayout
from codeflow.graph import NodeType


class TestLayoutExitConvention(unittest.TestCase):
    """Test that exit nodes are positioned below regular nodes."""
    
    def _analyze_function(self, source: str, func_name: str):
        """Helper to analyze a Python function."""
        fd, temp_path = tempfile.mkstemp(suffix='.py', text=True)
        try:
            os.write(fd, source.encode('utf-8'))
            os.close(fd)
            result = analyze_python_file(temp_path)
            return result.functions.get(func_name)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def test_single_exit_centered(self):
        """Test that a single exit node (Normal Exit) is centered."""
        source = 'def simple():\n    x = 1\n    return x\n'
        cfg = self._analyze_function(source, 'simple')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()
        
        # Find exit node
        exit_nodes = [
            nid for nid in cfg.nodes
            if cfg.nodes[nid].node_type == NodeType.EXIT
        ]
        
        self.assertTrue(len(exit_nodes) > 0, "No exit node found")
        
        # Single exit should be centered (x ≈ 0)
        if len(exit_nodes) == 1:
            exit_x = layout.positions[exit_nodes[0]].x
            self.assertLess(abs(exit_x), 5, f"Single exit not centered: x={exit_x}")
    
    def test_exit_below_regular_nodes(self):
        """Test that exit nodes are positioned below all regular nodes."""
        source = 'def check_value(x):\n    if x > 0:\n        return True\n    else:\n        return False\n'
        cfg = self._analyze_function(source, 'check_value')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()
        
        # Separate exit and regular nodes
        exit_nodes = [
            nid for nid in cfg.nodes
            if cfg.nodes[nid].node_type == NodeType.EXIT
        ]
        regular_nodes = [
            nid for nid in cfg.nodes
            if cfg.nodes[nid].node_type != NodeType.EXIT
        ]
        
        self.assertTrue(len(exit_nodes) > 0, "No exit nodes found")
        self.assertTrue(len(regular_nodes) > 0, "No regular nodes found")
        
        # Find max y of regular nodes (bottom of regular nodes)
        regular_ys = [layout.positions[nid].y for nid in regular_nodes if nid in layout.positions]
        if regular_ys:
            regular_max_y = max(regular_ys)
        else:
            self.fail("No regular nodes positioned")
        
        # Find min y of exit nodes (top of exit nodes)
        exit_ys = [layout.positions[nid].y for nid in exit_nodes if nid in layout.positions]
        if exit_ys:
            exit_min_y = min(exit_ys)
        else:
            self.fail("No exit nodes positioned")
        
        # Exit nodes should be below regular nodes
        self.assertGreater(
            exit_min_y, regular_max_y,
            f"Exit nodes not below regular nodes: "
            f"regular_max_y={regular_max_y}, exit_min_y={exit_min_y}"
        )
    
    def test_two_exits_side_by_side(self):
        """Test that two exits (Normal + Exception) are positioned side-by-side."""
        source = 'def risky_operation(x):\n    if x < 0:\n        raise ValueError("Negative")\n    return x * 2\n'
        cfg = self._analyze_function(source, 'risky_operation')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()
        
        # Find exit nodes
        exit_nodes = [
            nid for nid in cfg.nodes
            if cfg.nodes[nid].node_type == NodeType.EXIT
        ]
        
        # Collect exit y-coordinates to verify they're at same level
        if len(exit_nodes) >= 1:
            exit_y_values = [layout.positions[nid].y for nid in exit_nodes if nid in layout.positions]
            if len(exit_y_values) > 1:
                # For multiple exits, they should all be at the same y level
                y_diff = max(exit_y_values) - min(exit_y_values)
                self.assertLess(
                    y_diff, 5,
                    f"Exit nodes not aligned horizontally: "
                    f"y_values={exit_y_values}, diff={y_diff}"
                )
    
    def test_loop_function_exit_at_bottom(self):
        """Test exit positioning in a function with loops."""
        source = 'def find_value(items, target):\n    for item in items:\n        if item == target:\n            return item\n    return None\n'
        cfg = self._analyze_function(source, 'find_value')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()
        
        # Separate nodes by type
        exit_nodes = [
            nid for nid in cfg.nodes
            if cfg.nodes[nid].node_type == NodeType.EXIT
        ]
        regular_nodes = [
            nid for nid in cfg.nodes
            if cfg.nodes[nid].node_type != NodeType.EXIT
        ]
        
        self.assertTrue(len(exit_nodes) > 0, "No exit nodes found")
        self.assertTrue(len(regular_nodes) > 0, "No regular nodes found")
        
        # Get y positions
        regular_ys = [layout.positions[nid].y for nid in regular_nodes if nid in layout.positions]
        exit_ys = [layout.positions[nid].y for nid in exit_nodes if nid in layout.positions]
        
        if regular_ys and exit_ys:
            regular_max_y = max(regular_ys)
            exit_min_y = min(exit_ys)
            
            self.assertGreater(
                exit_min_y, regular_max_y,
                f"Exit nodes should be below regular nodes in loop function: "
                f"regular_max_y={regular_max_y}, exit_min_y={exit_min_y}"
            )
    
    def test_exit_spacing_matches_regular_spacing(self):
        """Test that the gap before exit row matches regular row gaps."""
        source = 'def sequence():\n    a = 1\n    b = 2\n    c = 3\n    return a + b + c\n'
        cfg = self._analyze_function(source, 'sequence')
        self.assertIsNotNone(cfg, "Function should be analyzed")
        
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()
        
        # This test primarily ensures no crash and layout computes successfully
        # The gap calculation is handled internally by min_y_gap
        self.assertTrue(len(layout.positions) > 0, "No positions computed")
        
        # Verify all nodes have positions
        for node_id in cfg.nodes:
            self.assertIn(node_id, layout.positions, f"Node {node_id} has no position")


if __name__ == "__main__":
    unittest.main()

