"""Unit tests for CFG graph structures."""

import unittest
from codeflow.graph import CFG, CFGNode, CFGEdge, NodeType, EdgeType, SourceLocation

class TestCFGNode(unittest.TestCase):
    """Tests for CFGNode."""

    def test_node_creation(self):
        """Test creating a CFG node."""
        loc = SourceLocation("test.py", 1, 1, "x = 1")
        node = CFGNode("node_0", "x = 1", NodeType.STATEMENT, loc)
        self.assertEqual(node.id, "node_0")
        self.assertEqual(node.label, "x = 1")
        self.assertEqual(node.node_type, NodeType.STATEMENT)

    def test_node_to_dict(self):
        """Test converting node to dictionary."""
        loc = SourceLocation("test.py", 1, 1, "x = 1")
        node = CFGNode("node_0", "x = 1", NodeType.STATEMENT, loc)
        d = node.to_dict()
        self.assertEqual(d["id"], "node_0")
        self.assertEqual(d["label"], "x = 1")
        self.assertEqual(d["type"], "statement")

class TestCFGEdge(unittest.TestCase):
    """Tests for CFGEdge."""

    def test_edge_creation(self):
        """Test creating a CFG edge."""
        edge = CFGEdge("node_0", "node_1", "True", EdgeType.TRUE)
        self.assertEqual(edge.source_id, "node_0")
        self.assertEqual(edge.target_id, "node_1")
        self.assertEqual(edge.label, "True")

    def test_edge_to_dict(self):
        """Test converting edge to dictionary."""
        edge = CFGEdge("node_0", "node_1", "True", EdgeType.TRUE)
        d = edge.to_dict()
        self.assertEqual(d["source"], "node_0")
        self.assertEqual(d["target"], "node_1")
        self.assertEqual(d["label"], "True")

class TestCFG(unittest.TestCase):
    """Tests for CFG."""

    def test_cfg_creation(self):
        """Test creating a CFG."""
        cfg = CFG("test_func")
        self.assertEqual(cfg.name, "test_func")
        self.assertEqual(len(cfg.nodes), 0)
        self.assertEqual(len(cfg.edges), 0)

    def test_add_node(self):
        """Test adding a node to CFG."""
        cfg = CFG("test_func")
        node = CFGNode("node_0", "Entry", NodeType.ENTRY)
        cfg.add_node(node)
        self.assertEqual(len(cfg.nodes), 1)
        self.assertIn("node_0", cfg.nodes)

    def test_add_edge(self):
        """Test adding an edge to CFG."""
        cfg = CFG("test_func")
        edge = CFGEdge("node_0", "node_1")
        cfg.add_edge(edge)
        self.assertEqual(len(cfg.edges), 1)

if __name__ == '__main__':
    unittest.main()
