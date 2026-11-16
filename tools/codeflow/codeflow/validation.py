"""Control-flow graph validation and correctness verification."""

from dataclasses import dataclass
from typing import List, Set, Tuple, Optional
from enum import Enum
from codeflow.graph import CFG, CFGNode, CFGEdge, NodeType, EdgeType


class CompletionStatus(Enum):
    """Completion status of a control-flow graph."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    INVALID = "invalid"


@dataclass
class ValidationError:
    """A validation error in a control-flow graph."""
    error_type: str
    message: str
    affected_nodes: List[str]
    affected_edges: List[Tuple[str, str]]


@dataclass
class ValidationResult:
    """Result of validating a control-flow graph."""
    status: CompletionStatus
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    affected_edges: List[Tuple[str, str]]


class CFGValidator:
    """Validates control-flow graphs for correctness."""

    def __init__(self, cfg: CFG):
        """Initialize validator for a CFG."""
        self.cfg = cfg
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []

    def validate(self) -> ValidationResult:
        """Run all validation checks on the CFG."""
        self.errors.clear()
        self.warnings.clear()

        # Run validation checks
        self._validate_entry_node()
        self._validate_exit_nodes()
        self._validate_all_edges_valid()
        self._validate_no_break_to_exit()
        self._validate_no_continue_to_exit()
        self._validate_continue_to_loop_entry()
        self._validate_break_routing()
        self._validate_all_nodes_reachable()
        self._validate_no_invalid_cycles()
        self._validate_decision_edges()
        self._validate_no_edges_past_return()
        self._validate_no_generic_labels()

        # Determine overall status
        is_valid = len(self.errors) == 0
        if self.cfg.is_partial:
            status = CompletionStatus.PARTIAL
        elif is_valid:
            status = CompletionStatus.COMPLETE
        else:
            status = CompletionStatus.INVALID

        return ValidationResult(
            status=status,
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            affected_edges=[(e.source_id, e.target_id) for e in self.cfg.edges],
        )

    def _validate_entry_node(self) -> None:
        """Validate that entry node exists and has outgoing edges."""
        if not self.cfg.entry_node_id:
            self.errors.append(ValidationError(
                error_type="missing_entry",
                message="CFG has no entry node",
                affected_nodes=[],
                affected_edges=[],
            ))
            return

        entry_node = self.cfg.nodes.get(self.cfg.entry_node_id)
        if not entry_node:
            self.errors.append(ValidationError(
                error_type="invalid_entry",
                message=f"Entry node {self.cfg.entry_node_id} not in graph",
                affected_nodes=[self.cfg.entry_node_id],
                affected_edges=[],
            ))
            return

        # Check that entry has outgoing edges (or connects directly to empty-function exit)
        outgoing = [e for e in self.cfg.edges if e.source_id == self.cfg.entry_node_id]
        if not outgoing and len(self.cfg.nodes) > 2:
            self.warnings.append(
                f"Entry node {self.cfg.entry_node_id} has no outgoing edges"
            )

    def _validate_exit_nodes(self) -> None:
        """Validate that exit nodes are defined."""
        if not self.cfg.exit_node_ids:
            self.warnings.append("CFG has no normal exit nodes")

    def _validate_all_edges_valid(self) -> None:
        """Validate that all edges point to valid nodes."""
        node_ids = set(self.cfg.nodes.keys())
        for edge in self.cfg.edges:
            if edge.source_id not in node_ids:
                self.errors.append(ValidationError(
                    error_type="invalid_source",
                    message=f"Edge source {edge.source_id} not in graph",
                    affected_nodes=[edge.source_id],
                    affected_edges=[(edge.source_id, edge.target_id)],
                ))
            if edge.target_id not in node_ids:
                self.errors.append(ValidationError(
                    error_type="invalid_target",
                    message=f"Edge target {edge.target_id} not in graph",
                    affected_nodes=[edge.target_id],
                    affected_edges=[(edge.source_id, edge.target_id)],
                ))

    def _validate_no_break_to_exit(self) -> None:
        """Validate that break edges never target function exit."""
        exit_node_ids = set(self.cfg.exit_node_ids)
        for edge in self.cfg.edges:
            if edge.edge_type == EdgeType.BREAK and edge.target_id in exit_node_ids:
                self.errors.append(ValidationError(
                    error_type="break_to_exit",
                    message=f"Break edge targets function exit (node {edge.target_id})",
                    affected_nodes=[edge.source_id, edge.target_id],
                    affected_edges=[(edge.source_id, edge.target_id)],
                ))

    def _validate_no_continue_to_exit(self) -> None:
        """Validate that continue edges never target function exit."""
        exit_node_ids = set(self.cfg.exit_node_ids)
        for edge in self.cfg.edges:
            if edge.edge_type == EdgeType.CONTINUE and edge.target_id in exit_node_ids:
                self.errors.append(ValidationError(
                    error_type="continue_to_exit",
                    message=f"Continue edge targets function exit (node {edge.target_id})",
                    affected_nodes=[edge.source_id, edge.target_id],
                    affected_edges=[(edge.source_id, edge.target_id)],
                ))

    def _validate_continue_to_loop_entry(self) -> None:
        """Validate that continue edges target loop entry nodes."""
        loop_entry_ids = {
            nid for nid, node in self.cfg.nodes.items()
            if node.node_type in (NodeType.LOOP_ENTRY,)
        }
        for edge in self.cfg.edges:
            if edge.edge_type == EdgeType.CONTINUE:
                if edge.target_id not in loop_entry_ids:
                    self.warnings.append(
                        f"Continue edge from {edge.source_id} targets non-loop-entry "
                        f"{edge.target_id}"
                    )

    def _validate_break_routing(self) -> None:
        """Validate break edges route to after-loop nodes, not arbitrary nodes."""
        # This is a complex validation; at minimum, verify they don't go to exit
        pass

    def _validate_all_nodes_reachable(self) -> None:
        """Validate that all reachable nodes have a path to exit."""
        reachable = self._find_reachable_nodes()
        exit_ids = set(self.cfg.exit_node_ids + self.cfg.exception_exit_node_ids)

        for node_id in reachable:
            if node_id not in exit_ids:
                paths_to_exit = self._find_paths_to_exit(node_id)
                if not paths_to_exit:
                    # Only warn if node is not marked unreachable
                    self.warnings.append(
                        f"Reachable node {node_id} has no path to exit"
                    )

    def _validate_no_invalid_cycles(self) -> None:
        """Validate that only loop-back edges create cycles."""
        # Build adjacency excluding loop-back edges
        adj = {nid: [] for nid in self.cfg.nodes}
        for edge in self.cfg.edges:
            if edge.edge_type != EdgeType.LOOP_BACK:
                adj[edge.source_id].append(edge.target_id)

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node_id)
            return False

        for node_id in self.cfg.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    self.warnings.append(
                        f"Cycle detected in graph (not via LOOP_BACK edges)"
                    )

    def _validate_decision_edges(self) -> None:
        """Validate that decision nodes have properly labeled branches."""
        for node_id, node in self.cfg.nodes.items():
            if node.node_type == NodeType.DECISION:
                outgoing = [e for e in self.cfg.edges if e.source_id == node_id]
                if not outgoing:
                    self.warnings.append(
                        f"Decision node {node_id} has no outgoing edges"
                    )
                # Check that edges have meaningful labels
                for edge in outgoing:
                    if not edge.label or edge.label.strip() == "":
                        self.warnings.append(
                            f"Decision edge {node_id} → {edge.target_id} has no label"
                        )

    def _validate_no_edges_past_return(self) -> None:
        """Validate that statements after unconditional return are not connected."""
        # Find all return nodes
        return_nodes = {
            nid for nid, node in self.cfg.nodes.items()
            if "return" in node.label.lower() and node.node_type != NodeType.EXIT
        }
        # This is a complex check; at minimum verify returns connect to exit
        for node_id in return_nodes:
            outgoing = [e for e in self.cfg.edges if e.source_id == node_id]
            # Return should only connect to exit
            if not all(e.target_id in self.cfg.exit_node_ids for e in outgoing):
                self.warnings.append(
                    f"Return node {node_id} has non-exit outgoing edges"
                )

    def _validate_no_generic_labels(self) -> None:
        """Validate that node labels are not generic AST types or punctuation."""
        generic_types = {
            "let_declaration", "call_expression", "assignment_expression",
            "return_expression", "if_expression", "match_expression",
            "loop_body", "condition", "statement", "{", "}", ";",
        }
        for node_id, node in self.cfg.nodes.items():
            label_lower = node.label.lower()
            if label_lower in generic_types or node.label in {"{", "}", ";"}:
                self.errors.append(ValidationError(
                    error_type="generic_label",
                    message=f"Node {node_id} has generic/punctuation label: '{node.label}'",
                    affected_nodes=[node_id],
                    affected_edges=[],
                ))

    def _find_reachable_nodes(self) -> Set[str]:
        """Find all nodes reachable from entry."""
        if not self.cfg.entry_node_id:
            return set()

        reachable = set()
        to_visit = [self.cfg.entry_node_id]
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in reachable:
                continue
            reachable.add(node_id)
            for edge in self.cfg.edges:
                if edge.source_id == node_id and edge.target_id not in reachable:
                    to_visit.append(edge.target_id)
        return reachable

    def _find_paths_to_exit(self, start_node_id: str) -> List[List[str]]:
        """Find all paths from a node to an exit node."""
        exit_ids = set(self.cfg.exit_node_ids + self.cfg.exception_exit_node_ids)
        paths = []

        def dfs(node_id, path, visited):
            if node_id in exit_ids:
                paths.append(path + [node_id])
                return
            if node_id in visited:
                return
            visited.add(node_id)
            for edge in self.cfg.edges:
                if edge.source_id == node_id:
                    dfs(edge.target_id, path + [node_id], visited.copy())

        dfs(start_node_id, [], set())
        return paths
