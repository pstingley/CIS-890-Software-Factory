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


class TestGraphContraction(unittest.TestCase):
    """Tests for graph contraction with internal nodes."""

    def test_contraction_preserves_visible_nodes(self):
        """Test that visible nodes are preserved during contraction."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Entry", NodeType.ENTRY))
        cfg.add_node(CFGNode("v2", "Exit", NodeType.EXIT))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        visible_nodes, _ = cfg._contract_internal_nodes()

        self.assertIn("v1", visible_nodes)
        self.assertIn("v2", visible_nodes)
        self.assertNotIn("i1", visible_nodes)
        self.assertEqual(len(visible_nodes), 2)

    def test_contraction_simple_internal_node(self):
        """Test contraction of a simple sequence with one internal node."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "End", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.source_id, "v1")
        self.assertEqual(edge.target_id, "v2")
        self.assertEqual(edge.edge_type, EdgeType.NORMAL)

    def test_contraction_preserves_true_edge_type(self):
        """Test that TRUE edge type is preserved when contracting."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "If", NodeType.DECISION))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Exit", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "condition", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v2", "merge", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.edge_type, EdgeType.TRUE)

    def test_contraction_preserves_false_edge_type(self):
        """Test that FALSE edge type is preserved when contracting."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "If", NodeType.DECISION))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Exit", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "condition", EdgeType.FALSE))
        cfg.add_edge(CFGEdge("i1", "v2", "merge", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.edge_type, EdgeType.FALSE)

    def test_contraction_preserves_exception_edge(self):
        """Test that EXCEPTION edge type is preserved when contracting."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Call", NodeType.CALL))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Handler", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "throws", EdgeType.EXCEPTION))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.edge_type, EdgeType.EXCEPTION)

    def test_contraction_preserves_break_edge(self):
        """Test that BREAK edge type is preserved when contracting."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Loop", NodeType.LOOP_ENTRY))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "After", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.BREAK))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.edge_type, EdgeType.BREAK)

    def test_contraction_preserves_continue_edge(self):
        """Test that CONTINUE edge type is preserved when contracting."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Loop", NodeType.LOOP_ENTRY))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Loop", NodeType.LOOP_ENTRY))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.CONTINUE))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.edge_type, EdgeType.CONTINUE)

    def test_contraction_preserves_loop_back_edge(self):
        """Test that LOOP_BACK edge type is preserved when contracting."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Loop", NodeType.LOOP_ENTRY))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Loop", NodeType.LOOP_ENTRY))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.LOOP_BACK))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.edge_type, EdgeType.LOOP_BACK)

    def test_contraction_multiple_consecutive_internal_nodes(self):
        """Test contraction of multiple consecutive internal nodes."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal1", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("i2", "internal2", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "End", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "i2", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i2", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.source_id, "v1")
        self.assertEqual(edge.target_id, "v2")
        self.assertEqual(edge.edge_type, EdgeType.TRUE)

    def test_contraction_cycle_among_internal_nodes(self):
        """Test that cycles among internal nodes are handled safely."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Entry", NodeType.ENTRY))
        cfg.add_node(CFGNode("i1", "internal1", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("i2", "internal2", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Exit", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "i2", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i2", "i1", "", EdgeType.LOOP_BACK))  # Cycle
        cfg.add_edge(CFGEdge("i2", "v2", "", EdgeType.NORMAL))

        # Should not raise RecursionError
        _, contracted_edges = cfg._contract_internal_nodes()

        # With a cycle, there can be multiple paths. We should have:
        # 1. Direct normal path: v1 -> v2 (NORMAL)
        # 2. Cycle path: v1 -> v2 (LOOP_BACK) through the i2->i1 cycle
        self.assertEqual(len(contracted_edges), 2)

        # Verify both paths are present with correct types
        normal_edges = [e for e in contracted_edges if e.edge_type == EdgeType.NORMAL]
        loop_edges = [e for e in contracted_edges if e.edge_type == EdgeType.LOOP_BACK]

        self.assertEqual(len(normal_edges), 1)
        self.assertEqual(len(loop_edges), 1)

        # Both should go from v1 to v2
        for edge in contracted_edges:
            self.assertEqual(edge.source_id, "v1")
            self.assertEqual(edge.target_id, "v2")

    def test_contraction_multiple_outgoing_internal_edges(self):
        """Test contraction when internal node has multiple outgoing edges."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "If", NodeType.DECISION))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "True branch", NodeType.STATEMENT))
        cfg.add_node(CFGNode("v3", "False branch", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "condition", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v2", "true_path", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v3", "false_path", EdgeType.FALSE))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 2)

        # Both edges should preserve the incoming TRUE type
        types = [e.edge_type for e in contracted_edges]
        self.assertEqual(types.count(EdgeType.TRUE), 2)

    def test_contraction_edge_deduplication(self):
        """Test that duplicate edges (same source, target, type, label) are deduplicated."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "End", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "label", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v2", "label", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("v1", "v2", "label", EdgeType.TRUE))  # Direct edge

        _, contracted_edges = cfg._contract_internal_nodes()

        # Should have only one edge (the direct one), duplicates removed
        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.source_id, "v1")
        self.assertEqual(edge.target_id, "v2")
        self.assertEqual(edge.edge_type, EdgeType.TRUE)

    def test_to_dict_uses_contracted_graph(self):
        """Test that to_dict() exports the contracted presentation graph."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.ENTRY))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "End", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))
        cfg.entry_node_id = "v1"
        cfg.exit_node_ids = ["v2"]

        result_dict = cfg.to_dict()

        # Should export only 2 visible nodes
        self.assertEqual(len(result_dict["nodes"]), 2)
        node_ids = {n["id"] for n in result_dict["nodes"]}
        self.assertEqual(node_ids, {"v1", "v2"})

        # Should export 1 contracted edge
        self.assertEqual(len(result_dict["edges"]), 1)
        edge = result_dict["edges"][0]
        self.assertEqual(edge["source"], "v1")
        self.assertEqual(edge["target"], "v2")

    def test_to_dict_complete_includes_internal_nodes(self):
        """Test that to_dict_complete() includes internal nodes."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.ENTRY))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "End", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))
        cfg.entry_node_id = "v1"
        cfg.exit_node_ids = ["v2"]

        result_dict = cfg.to_dict_complete()

        # Should export all 3 nodes including internal
        self.assertEqual(len(result_dict["nodes"]), 3)
        node_ids = {n["id"] for n in result_dict["nodes"]}
        self.assertEqual(node_ids, {"v1", "i1", "v2"})

        # Should export original 2 edges
        self.assertEqual(len(result_dict["edges"]), 2)

    def test_contraction_preserves_no_spurious_edges(self):
        """Test that contraction doesn't create impossible paths."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "If", NodeType.DECISION))
        cfg.add_node(CFGNode("i1", "internal_true", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("i2", "internal_false", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Merge", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("v1", "i2", "", EdgeType.FALSE))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i2", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        # Should have exactly 2 edges: v1--true-->v2 and v1--false-->v2
        self.assertEqual(len(contracted_edges), 2)

        edge_types = {(e.source_id, e.target_id, e.edge_type) for e in contracted_edges}
        self.assertIn(("v1", "v2", EdgeType.TRUE), edge_types)
        self.assertIn(("v1", "v2", EdgeType.FALSE), edge_types)

    def test_contraction_with_visible_to_visible_edges(self):
        """Test that visible-to-visible edges are preserved as-is."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.STATEMENT))
        cfg.add_node(CFGNode("v2", "Direct", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v3", "End", NodeType.EXIT))

        cfg.add_edge(CFGEdge("v1", "v2", "direct", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("v1", "i1", "via_internal", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v3", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("v2", "v3", "direct2", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        # Should have direct edges (v1->v2, v2->v3) + contracted edge (v1->v3)
        self.assertEqual(len(contracted_edges), 3)

        # Find v1->v2 edge
        direct_edges = [e for e in contracted_edges if e.source_id == "v1" and e.target_id == "v2"]
        self.assertEqual(len(direct_edges), 1)
        self.assertEqual(direct_edges[0].label, "direct")

    def test_contraction_exception_propagates_through_internal(self):
        """Test that EXCEPTION edges propagate through internal nodes, overriding incoming type."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Statement", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal_call", NodeType.CALL, is_internal=True))
        cfg.add_node(CFGNode("v2", "ExceptionHandler", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.EXCEPTION))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        # EXCEPTION should propagate, not use incoming NORMAL
        self.assertEqual(edge.edge_type, EdgeType.EXCEPTION)

    def test_contraction_exception_overrides_true_branch(self):
        """Test that EXCEPTION edge propagates even from TRUE branch."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "If", NodeType.DECISION))
        cfg.add_node(CFGNode("i1", "internal_call", NodeType.CALL, is_internal=True))
        cfg.add_node(CFGNode("v2", "ExceptionHandler", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.EXCEPTION))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        # EXCEPTION should override TRUE
        self.assertEqual(edge.edge_type, EdgeType.EXCEPTION)

    def test_contraction_exception_through_multiple_internal(self):
        """Test that EXCEPTION propagates through multiple consecutive internal nodes."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Start", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal1", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("i2", "internal2", NodeType.CALL, is_internal=True))
        cfg.add_node(CFGNode("v2", "Handler", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "i2", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i2", "v2", "", EdgeType.EXCEPTION))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        self.assertEqual(edge.source_id, "v1")
        self.assertEqual(edge.target_id, "v2")
        # EXCEPTION should propagate through all internal nodes
        self.assertEqual(edge.edge_type, EdgeType.EXCEPTION)

    def test_contraction_break_propagates(self):
        """Test that BREAK edges propagate through internal nodes."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Statement", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "AfterLoop", NodeType.STATEMENT))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.BREAK))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        # BREAK should propagate, not use incoming NORMAL
        self.assertEqual(edge.edge_type, EdgeType.BREAK)

    def test_contraction_continue_propagates(self):
        """Test that CONTINUE edges propagate through internal nodes."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "Statement", NodeType.STATEMENT))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "LoopEntry", NodeType.LOOP_ENTRY))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.CONTINUE))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        # CONTINUE should propagate
        self.assertEqual(edge.edge_type, EdgeType.CONTINUE)

    def test_contraction_loop_back_propagates(self):
        """Test that LOOP_BACK edges propagate through internal nodes."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "LoopEntry", NodeType.LOOP_ENTRY))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "LoopEntry", NodeType.LOOP_ENTRY))

        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.LOOP_BACK))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        # LOOP_BACK should propagate
        self.assertEqual(edge.edge_type, EdgeType.LOOP_BACK)

    def test_contraction_true_false_edges_use_incoming_type(self):
        """Test that TRUE/FALSE branches use incoming edge type, not outgoing."""
        cfg = CFG("test")
        cfg.add_node(CFGNode("v1", "If", NodeType.DECISION))
        cfg.add_node(CFGNode("i1", "internal", NodeType.STATEMENT, is_internal=True))
        cfg.add_node(CFGNode("v2", "Merge", NodeType.STATEMENT))

        # TRUE incoming, NORMAL outgoing - result should be TRUE
        cfg.add_edge(CFGEdge("v1", "i1", "", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("i1", "v2", "", EdgeType.NORMAL))

        _, contracted_edges = cfg._contract_internal_nodes()

        self.assertEqual(len(contracted_edges), 1)
        edge = contracted_edges[0]
        # TRUE from decision point should be preserved
        self.assertEqual(edge.edge_type, EdgeType.TRUE)

if __name__ == '__main__':
    unittest.main()
