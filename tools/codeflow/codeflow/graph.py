"""Control-Flow Graph data structures and utilities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple

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
class CFGNode:
    """A node in the control-flow graph."""
    id: str
    label: str
    node_type: NodeType
    source_location: Optional[SourceLocation] = None
    is_exceptional_exit: bool = False

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

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "name": self.name,
            "nodes": [self.nodes[nid].to_dict() for nid in self.nodes],
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
