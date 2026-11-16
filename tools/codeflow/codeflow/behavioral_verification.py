"""Behavioral verification helpers for testing control-flow graphs."""

from typing import List, Set, Tuple, Optional
from codeflow.graph import CFG, CFGNode, CFGEdge, EdgeType, NodeType


class BehavioralVerifier:
    """Provides reusable assertions for testing control-flow graph behavior."""

    def __init__(self, cfg: CFG):
        """Initialize verifier for a CFG."""
        self.cfg = cfg

    def assert_path_exists(self, expected_path: List[str]) -> None:
        """Assert that a specific sequence of nodes exists as a path in the CFG.

        Args:
            expected_path: List of node IDs representing the expected path.

        Raises:
            AssertionError: If the path does not exist.
        """
        for i in range(len(expected_path) - 1):
            source_id = expected_path[i]
            target_id = expected_path[i + 1]
            if not self._edge_exists(source_id, target_id):
                raise AssertionError(
                    f"Path does not exist: {source_id} → {target_id}. "
                    f"Full expected path: {expected_path}"
                )

    def assert_edge_exists(
        self,
        source_id: str,
        target_id: str,
        edge_type: Optional[EdgeType] = None,
        label: Optional[str] = None,
    ) -> None:
        """Assert that an edge exists with optional type and label matching.

        Args:
            source_id: ID of source node.
            target_id: ID of target node.
            edge_type: Expected edge type (optional).
            label: Expected edge label (optional).

        Raises:
            AssertionError: If edge does not exist or properties don't match.
        """
        edge = None
        for e in self.cfg.edges:
            if e.source_id == source_id and e.target_id == target_id:
                edge = e
                break

        if not edge:
            raise AssertionError(
                f"Edge {source_id} → {target_id} does not exist"
            )

        if edge_type is not None and edge.edge_type != edge_type:
            raise AssertionError(
                f"Edge {source_id} → {target_id} has type {edge.edge_type}, "
                f"expected {edge_type}"
            )

        if label is not None and edge.label != label:
            raise AssertionError(
                f"Edge {source_id} → {target_id} has label '{edge.label}', "
                f"expected '{label}'"
            )

    def assert_edge_does_not_exist(
        self,
        source_id: str,
        target_id: str,
    ) -> None:
        """Assert that an edge does NOT exist.

        Args:
            source_id: ID of source node.
            target_id: ID of target node.

        Raises:
            AssertionError: If edge exists.
        """
        for e in self.cfg.edges:
            if e.source_id == source_id and e.target_id == target_id:
                raise AssertionError(
                    f"Edge {source_id} → {target_id} exists but should not"
                )

    def assert_node_label_does_not_contain(self, pattern: str) -> None:
        """Assert that no node label contains a specific pattern.

        Args:
            pattern: Pattern that should not appear in any node label.

        Raises:
            AssertionError: If any node label contains the pattern.
        """
        for node_id, node in self.cfg.nodes.items():
            if pattern in node.label:
                raise AssertionError(
                    f"Node {node_id} has label '{node.label}' containing '{pattern}'"
                )

    def assert_node_label_contains(self, node_id: str, pattern: str) -> None:
        """Assert that a specific node's label contains a pattern.

        Args:
            node_id: ID of the node.
            pattern: Pattern that should appear in the label.

        Raises:
            AssertionError: If node label doesn't contain the pattern.
        """
        node = self.cfg.nodes.get(node_id)
        if not node:
            raise AssertionError(f"Node {node_id} does not exist")

        if pattern not in node.label:
            raise AssertionError(
                f"Node {node_id} label '{node.label}' does not contain '{pattern}'"
            )

    def assert_loop_back_edge_exists(self, loop_entry_id: str) -> None:
        """Assert that a loop-back edge exists from somewhere to loop entry.

        Args:
            loop_entry_id: ID of the loop entry node.

        Raises:
            AssertionError: If no loop-back edge targets this node.
        """
        for e in self.cfg.edges:
            if e.target_id == loop_entry_id and e.edge_type == EdgeType.LOOP_BACK:
                return  # Found it
        raise AssertionError(
            f"No loop-back edge targets loop entry {loop_entry_id}"
        )

    def assert_break_routes_to_target(
        self,
        break_statement_id: str,
        expected_target_id: str,
    ) -> None:
        """Assert that a break statement routes to expected target.

        Args:
            break_statement_id: ID of the break statement node.
            expected_target_id: ID of expected target (after-loop node).

        Raises:
            AssertionError: If break doesn't route to target.
        """
        for e in self.cfg.edges:
            if (
                e.source_id == break_statement_id
                and e.edge_type == EdgeType.BREAK
            ):
                if e.target_id == expected_target_id:
                    return  # Found correct route
                raise AssertionError(
                    f"Break {break_statement_id} routes to {e.target_id}, "
                    f"expected {expected_target_id}"
                )
        raise AssertionError(
            f"Break statement {break_statement_id} has no BREAK edge"
        )

    def assert_continue_routes_to_loop_entry(
        self,
        continue_statement_id: str,
        expected_loop_entry_id: str,
    ) -> None:
        """Assert that a continue statement routes to loop entry.

        Args:
            continue_statement_id: ID of the continue statement node.
            expected_loop_entry_id: ID of expected loop entry node.

        Raises:
            AssertionError: If continue doesn't route to loop entry.
        """
        for e in self.cfg.edges:
            if (
                e.source_id == continue_statement_id
                and e.edge_type == EdgeType.CONTINUE
            ):
                if e.target_id == expected_loop_entry_id:
                    return  # Found correct route
                raise AssertionError(
                    f"Continue {continue_statement_id} routes to {e.target_id}, "
                    f"expected loop entry {expected_loop_entry_id}"
                )
        raise AssertionError(
            f"Continue statement {continue_statement_id} has no CONTINUE edge"
        )

    def assert_decision_has_branches(
        self,
        decision_id: str,
        expected_labels: List[str],
    ) -> None:
        """Assert that a decision node has specific branches.

        Args:
            decision_id: ID of the decision node.
            expected_labels: Expected branch labels (e.g., ["true", "false"]).

        Raises:
            AssertionError: If branches don't match.
        """
        node = self.cfg.nodes.get(decision_id)
        if not node or node.node_type != NodeType.DECISION:
            raise AssertionError(f"Node {decision_id} is not a DECISION node")

        outgoing_labels = set()
        for e in self.cfg.edges:
            if e.source_id == decision_id:
                outgoing_labels.add(e.label)

        expected_set = set(expected_labels)
        if outgoing_labels != expected_set:
            raise AssertionError(
                f"Decision {decision_id} has branches {outgoing_labels}, "
                f"expected {expected_set}"
            )

    def assert_all_decision_edges_have_labels(self) -> None:
        """Assert that all decision nodes have properly labeled outgoing edges.

        Raises:
            AssertionError: If any decision has unlabeled edges.
        """
        for node_id, node in self.cfg.nodes.items():
            if node.node_type == NodeType.DECISION:
                for e in self.cfg.edges:
                    if e.source_id == node_id:
                        if not e.label or e.label.strip() == "":
                            raise AssertionError(
                                f"Decision {node_id} has unlabeled edge to {e.target_id}"
                            )

    def assert_no_break_to_exit(self) -> None:
        """Assert that no break edges target the function exit.

        Raises:
            AssertionError: If a break edge targets exit.
        """
        exit_ids = set(self.cfg.exit_node_ids)
        for e in self.cfg.edges:
            if e.edge_type == EdgeType.BREAK and e.target_id in exit_ids:
                raise AssertionError(
                    f"Break edge {e.source_id} → {e.target_id} targets function exit"
                )

    def assert_return_connects_to_exit(
        self,
        return_node_id: str,
    ) -> None:
        """Assert that a return statement connects to function exit.

        Args:
            return_node_id: ID of the return statement node.

        Raises:
            AssertionError: If return doesn't connect to exit.
        """
        for e in self.cfg.edges:
            if e.source_id == return_node_id and e.target_id in self.cfg.exit_node_ids:
                return  # Found it
        raise AssertionError(
            f"Return {return_node_id} does not connect to any exit node"
        )

    def assert_node_has_source_location(self, node_id: str) -> None:
        """Assert that a node has valid source location information.

        Args:
            node_id: ID of the node.

        Raises:
            AssertionError: If node has no source location.
        """
        node = self.cfg.nodes.get(node_id)
        if not node:
            raise AssertionError(f"Node {node_id} does not exist")

        if not node.source_location:
            raise AssertionError(f"Node {node_id} has no source location")

        if not node.source_location.file:
            raise AssertionError(f"Node {node_id} has no source file")

        if node.source_location.start_line < 0:
            raise AssertionError(f"Node {node_id} has invalid start line")

    def assert_all_nodes_have_source_locations(self) -> None:
        """Assert that all statement/decision nodes have source locations.

        Raises:
            AssertionError: If any node is missing source location.
        """
        for node_id, node in self.cfg.nodes.items():
            if node.node_type not in (NodeType.ENTRY, NodeType.EXIT):
                self.assert_node_has_source_location(node_id)

    def _edge_exists(self, source_id: str, target_id: str) -> bool:
        """Check if an edge exists."""
        for e in self.cfg.edges:
            if e.source_id == source_id and e.target_id == target_id:
                return True
        return False
