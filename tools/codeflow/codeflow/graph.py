"""Control-Flow Graph data structures and utilities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from codeflow.validation import ValidationResult

class NodeType(Enum):
    """Types of CFG nodes."""
    ENTRY = "entry"
    EXIT = "exit"
    STATEMENT = "statement"
    DECISION = "decision"
    LOOP_ENTRY = "loop_entry"
    LOOP_BODY = "loop_body"
    CALL = "call"
    EXCEPTION = "exception"

class EdgeType(Enum):
    """Types of CFG edges."""
    NORMAL = "normal"
    TRUE = "true"
    FALSE = "false"
    BREAK = "break"
    CONTINUE = "continue"
    EXCEPTION = "exception"
    LOOP_BACK = "loop_back"

@dataclass
class SourceLocation:
    """Source code location reference."""
    file: str
    start_line: int
    end_line: int
    source_code: str = ""

@dataclass
@dataclass
class CFGNode:
    """A node in the control-flow graph."""
    id: str
    label: str
    node_type: NodeType
    source_location: Optional[SourceLocation] = None
    is_exceptional_exit: bool = False
    is_internal: bool = False  # Internal/structural node, may be hidden in rendering

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "source": {
                "file": self.source_location.file,
                "start_line": self.source_location.start_line,
                "end_line": self.source_location.end_line,
                "code": self.source_location.source_code,
            } if self.source_location else None,
            "exceptional_exit": self.is_exceptional_exit,
            "internal": self.is_internal,
        }

@dataclass
class CFGEdge:
    """An edge in the control-flow graph."""
    source_id: str
    target_id: str
    label: str = ""
    edge_type: EdgeType = EdgeType.NORMAL

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "source": self.source_id,
            "target": self.target_id,
            "label": self.label,
            "type": self.edge_type.value,
        }

@dataclass
class CFG:
    """A control-flow graph for a function or module."""
    name: str
    nodes: Dict[str, CFGNode] = field(default_factory=dict)
    edges: List[CFGEdge] = field(default_factory=list)
    entry_node_id: Optional[str] = None
    exit_node_ids: List[str] = field(default_factory=list)
    exception_exit_node_ids: List[str] = field(default_factory=list)
    source_location: Optional[SourceLocation] = None
    is_partial: bool = False
    partial_reason: str = ""

    def add_node(self, node: CFGNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: CFGEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)

    def add_edge_simple(self, source_id: str, target_id: str,
                        label: str = "", edge_type: EdgeType = EdgeType.NORMAL) -> None:
        """Add an edge by IDs."""
        self.add_edge(CFGEdge(source_id, target_id, label, edge_type))

    def to_dict_complete(self) -> dict:
        """Export complete semantic graph including internal nodes."""
        return {
            "name": self.name,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "entry_node": self.entry_node_id,
            "exit_nodes": self.exit_node_ids,
            "exception_exit_nodes": self.exception_exit_node_ids,
            "source": {
                "file": self.source_location.file,
                "start_line": self.source_location.start_line,
                "end_line": self.source_location.end_line,
            } if self.source_location else None,
            "complete": not self.is_partial,
            "partial_reason": self.partial_reason if self.is_partial else "",
        }

    def _contract_internal_nodes(self) -> Tuple[Dict[str, CFGNode], List[CFGEdge]]:
        """Contract internal nodes while preserving execution paths and semantics.

        Returns:
            Tuple of (visible_nodes, simplified_edges) where edges are rewritten
            to bypass internal nodes while preserving:
            - Edge type (TRUE, FALSE, EXCEPTION, BREAK, CONTINUE, LOOP_BACK)
            - Edge labels
            - All reachability relationships
        """
        visible_nodes = {nid: node for nid, node in self.nodes.items() if not node.is_internal}
        internal_nodes = {nid: node for nid, node in self.nodes.items() if node.is_internal}

        # Use a set to deduplicate bypass edges by (source, target, type, label)
        edge_set = set()
        simplified_edges = []

        for edge in self.edges:
            # If both endpoints are visible, keep the edge as-is
            if edge.source_id in visible_nodes and edge.target_id in visible_nodes:
                edge_key = (edge.source_id, edge.target_id, edge.edge_type.value, edge.label)
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    simplified_edges.append(edge)
            # If source is visible but target is internal, find paths through the internal node
            elif edge.source_id in visible_nodes and edge.target_id in internal_nodes:
                # Find all paths from this internal node to visible nodes,
                # preserving the incoming edge's type (the semantics at the decision point)
                self._find_bypass_paths(edge.target_id, edge, visible_nodes, internal_nodes,
                                       edge_set, simplified_edges)
            # If source is internal but target is visible, the incoming edge already handled it
            elif edge.source_id in internal_nodes and edge.target_id in visible_nodes:
                # This edge will be created by the bypass when processing the incoming edge
                pass
            # If both are internal, skip (will be handled transitively)
            else:
                pass

        return visible_nodes, simplified_edges

    def _find_bypass_paths(self, internal_node_id: str, incoming_edge: CFGEdge,
                           visible_nodes: Dict[str, CFGNode],
                           internal_nodes: Dict[str, CFGNode],
                           edge_set: set,
                           result_edges: List[CFGEdge]) -> None:
        """Find paths from an internal node to visible nodes and create bypass edges.

        Preserves semantic meaning according to edge type:
        - EXCEPTION, BREAK, CONTINUE, LOOP_BACK: preserve outgoing edge type (they propagate)
        - TRUE, FALSE, NORMAL: preserve incoming edge type (decision point semantics)

        Args:
            internal_node_id: ID of the internal node to bypass
            incoming_edge: The edge entering the internal node (carries decision semantics)
            visible_nodes: Map of visible (non-internal) nodes
            internal_nodes: Map of internal nodes
            edge_set: Set to track (source, target, type, label) for deduplication
            result_edges: List to append bypass edges to
        """
        visited = set()
        self._find_bypass_paths_impl(internal_node_id, incoming_edge, visible_nodes,
                                      internal_nodes, edge_set, result_edges, visited)

    def _find_bypass_paths_impl(self, internal_node_id: str, incoming_edge: CFGEdge,
                                visible_nodes: Dict[str, CFGNode],
                                internal_nodes: Dict[str, CFGNode],
                                edge_set: set,
                                result_edges: List[CFGEdge],
                                visited: Set[str]) -> None:
        """Implementation of bypass path finding with cycle detection."""
        # Create a key for memoization: (internal_node_id, incoming_edge_type)
        # Prevents infinite recursion in cycles
        memo_key = (internal_node_id, incoming_edge.edge_type.value)
        if memo_key in visited:
            return
        visited.add(memo_key)

        # Find outgoing edges from current node
        outgoing = [e for e in self.edges if e.source_id == internal_node_id]

        for out_edge in outgoing:
            if out_edge.target_id in visible_nodes:
                # Determine which edge type to use in the bypass edge:
                # - EXCEPTION, BREAK, CONTINUE, LOOP_BACK must propagate (preserve outgoing type)
                # - TRUE, FALSE, NORMAL use incoming type (decision point semantics)
                if out_edge.edge_type in (EdgeType.EXCEPTION, EdgeType.BREAK,
                                           EdgeType.CONTINUE, EdgeType.LOOP_BACK):
                    # Propagating edge types: preserve the outgoing edge type
                    edge_type_to_use = out_edge.edge_type
                else:
                    # Decision/normal edges: preserve the incoming edge type
                    edge_type_to_use = incoming_edge.edge_type

                # Prefer outgoing label if present, otherwise use incoming
                label = out_edge.label if out_edge.label else incoming_edge.label

                bypass_edge = CFGEdge(
                    source_id=incoming_edge.source_id,
                    target_id=out_edge.target_id,
                    label=label,
                    edge_type=edge_type_to_use
                )

                edge_key = (bypass_edge.source_id, bypass_edge.target_id,
                           bypass_edge.edge_type.value, bypass_edge.label)
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    result_edges.append(bypass_edge)

            elif out_edge.target_id in internal_nodes:
                # Continue traversing through internal nodes
                # For propagating edge types, pass them through; otherwise use incoming
                if out_edge.edge_type in (EdgeType.EXCEPTION, EdgeType.BREAK,
                                           EdgeType.CONTINUE, EdgeType.LOOP_BACK):
                    # Create a temporary edge to pass the propagating type through
                    pass_through_edge = CFGEdge(
                        source_id=incoming_edge.source_id,
                        target_id=out_edge.target_id,
                        label=out_edge.label if out_edge.label else incoming_edge.label,
                        edge_type=out_edge.edge_type
                    )
                    self._find_bypass_paths_impl(out_edge.target_id, pass_through_edge,
                                                visible_nodes, internal_nodes,
                                                edge_set, result_edges, visited)
                else:
                    # Normal/decision edges continue with original incoming edge semantics
                    self._find_bypass_paths_impl(out_edge.target_id, incoming_edge,
                                               visible_nodes, internal_nodes,
                                               edge_set, result_edges, visited)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export with simplified presentation graph.

        Keeps the complete semantic graph internally but exports a simplified version
        with internal nodes contracted while preserving all execution paths.
        """
        visible_nodes, simplified_edges = self._contract_internal_nodes()

        return {
            "name": self.name,
            "nodes": [visible_nodes[nid].to_dict() for nid in visible_nodes],
            "edges": [e.to_dict() for e in simplified_edges],
            "entry_node": self.entry_node_id,
            "exit_nodes": self.exit_node_ids,
            "exception_exit_nodes": self.exception_exit_node_ids,
            "source": {
                "file": self.source_location.file,
                "start_line": self.source_location.start_line,
                "end_line": self.source_location.end_line,
            } if self.source_location else None,
            "complete": not self.is_partial,
            "partial_reason": self.partial_reason if self.is_partial else "",
        }

    def mark_validation_failed(self, reason: str) -> None:
        """Mark graph as partial due to validation failure.

        Args:
            reason: Description of validation failure.
        """
        self.is_partial = True
        if self.partial_reason:
            self.partial_reason += "; " + reason
        else:
            self.partial_reason = reason

@dataclass
class AnalysisResult:
    """Result of analyzing a source file."""
    file_path: str
    functions: Dict[str, CFG] = field(default_factory=dict)
    module_cfg: Optional[CFG] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    source_references: Dict[str, Tuple[str, int]] = field(default_factory=dict)
    ambiguity_flags: List[str] = field(default_factory=list)
    analysis_incomplete: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "schema_version": "1.0",
            "source_file": self.file_path,
            "functions": {name: cfg.to_dict() for name, cfg in self.functions.items()},
            "module": self.module_cfg.to_dict() if self.module_cfg else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "source_references": self.source_references,
            "ambiguity_flags": self.ambiguity_flags,
            "analysis_incomplete": self.analysis_incomplete,
        }
