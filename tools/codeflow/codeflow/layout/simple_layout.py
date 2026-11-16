"""Layout engine - positions CFG nodes in 2D space."""

from dataclasses import dataclass
from typing import Dict, Tuple, List, Set
from codeflow.graph import CFG, CFGNode, NodeType


@dataclass
class Position:
    """2D position for a node."""
    x: float
    y: float


@dataclass
class NodeDimensions:
    """Width and height of a node after text wrapping."""
    width: float
    height: float


class SimpleHierarchicalLayout:
    """Simple hierarchical layout algorithm."""
    
    def __init__(self, cfg: CFG):
        self.cfg = cfg
        self.positions: Dict[str, Position] = {}
        self.levels: Dict[str, int] = {}
        self.dimensions: Dict[str, NodeDimensions] = {}  # Pre-calculated dimensions
        self.base_node_width = 120
        self.base_node_height = 40
        self.x_spacing = 150
        self.y_spacing = 80
        self.min_x_gap = 30  # Minimum horizontal gap between nodes
        self.min_y_gap = 30  # Minimum vertical gap between nodes
    
    def calculate_node_dimensions(self) -> Dict[str, NodeDimensions]:
        """Calculate final width/height for each node after text wrapping."""
        dimensions: Dict[str, NodeDimensions] = {}
        
        for node_id, node in self.cfg.nodes.items():
            width, height = self._calculate_label_dimensions(node.label)
            dimensions[node_id] = NodeDimensions(width=width, height=height)
        
        self.dimensions = dimensions
        return dimensions
    
    def _calculate_label_dimensions(self, label: str) -> Tuple[float, float]:
        """Calculate width and height needed for a label with wrapping."""
        max_chars_per_line = 16
        base_width = self.base_node_width
        base_height = self.base_node_height
        line_height = 14
        char_width = 7  # Approximate character width in pixels at 12pt
        
        if len(label) <= max_chars_per_line:
            return (base_width, base_height)
        
        # Wrap text
        words = label.split()
        lines = []
        current_line = []
        
        for word in words:
            current_length = sum(len(w) for w in current_line) + len(current_line)
            if current_length + len(word) > max_chars_per_line:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate dimensions
        if len(lines) > 1:
            width = base_width + 20  # Extra width for wrapped text
            height = base_height + (len(lines) - 1) * line_height
        else:
            width = base_width
            height = base_height
        
        return (width, height)
    
    def layout(self) -> Dict[str, Position]:
        """Compute positions for all nodes."""
        if not self.cfg.entry_node_id:
            return {}
        
        # Calculate node dimensions first
        self.calculate_node_dimensions()
        
        # Assign levels using BFS
        self._compute_levels()
        
        # Assign x, y positions accounting for node dimensions
        self._compute_positions()
        
        return self.positions
    
    def _compute_levels(self) -> None:
        """Assign each node a level (depth) in the graph."""
        from collections import deque
        
        if not self.cfg.entry_node_id:
            return
        
        queue = deque([self.cfg.entry_node_id])
        visited = {self.cfg.entry_node_id}
        self.levels[self.cfg.entry_node_id] = 0
        
        # Build adjacency list (skip None nodes)
        adjacency: Dict[str, List[str]] = {}
        for node_id in self.cfg.nodes:
            adjacency[node_id] = []
        for edge in self.cfg.edges:
            if edge.source_id and edge.target_id and edge.source_id in adjacency:
                adjacency[edge.source_id].append(edge.target_id)
        
        while queue:
            current = queue.popleft()
            current_level = self.levels[current]
            
            for next_node in adjacency.get(current, []):
                if next_node not in visited:
                    visited.add(next_node)
                    self.levels[next_node] = current_level + 1
                    queue.append(next_node)
        
        # Assign default level for unreached nodes
        for node_id in self.cfg.nodes:
            if node_id not in self.levels:
                self.levels[node_id] = len(self.levels)
    
    def _compute_positions(self) -> None:
        """Compute x, y positions based on levels, accounting for node dimensions.
        
        Layout convention: Entry at top, exits at bottom in a reserved row.
        - Regular nodes positioned using BFS level assignments
        - Exit nodes (Normal Exit, Exception Exit if present) placed at bottom
        - Single exit: centered
        - Multiple exits: centered row with adequate spacing
        """
        # Separate exit nodes from regular nodes
        exit_nodes = [
            node_id for node_id in self.cfg.nodes
            if self.cfg.nodes[node_id].node_type == NodeType.EXIT
        ]
        regular_nodes = [
            node_id for node_id in self.cfg.nodes
            if self.cfg.nodes[node_id].node_type != NodeType.EXIT
        ]
        
        # Group regular nodes by level
        level_nodes: Dict[int, List[str]] = {}
        for node_id in regular_nodes:
            level = self.levels.get(node_id, 0)
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node_id)
        
        # Position regular nodes row by row
        y = 0
        for level in sorted(level_nodes.keys()):
            nodes = level_nodes[level]
            
            # Calculate row height (tallest node in this level)
            row_height = max(
                self.dimensions.get(node_id, NodeDimensions(self.base_node_width, self.base_node_height)).height
                for node_id in nodes
            )
            
            # Calculate total width needed for all nodes in this level
            total_width = sum(
                self.dimensions.get(node_id, NodeDimensions(self.base_node_width, self.base_node_height)).width
                for node_id in nodes
            ) + (len(nodes) - 1) * self.min_x_gap
            
            # Position nodes horizontally in this level
            x = -total_width / 2
            for node_id in nodes:
                node_dim = self.dimensions.get(node_id, NodeDimensions(self.base_node_width, self.base_node_height))
                # Center node in its allocated space
                node_x = x + node_dim.width / 2
                self.positions[node_id] = Position(node_x, y + row_height / 2)
                x += node_dim.width + self.min_x_gap
            
            # Move to next level
            y += row_height + self.min_y_gap
        
        # Position exit nodes in a final row at the bottom
        if exit_nodes:
            # Add gap before exit row (same as between normal rows)
            exit_y = y + self.min_y_gap
            
            # Sort exits: Normal Exit first, Exception Exit second (if present)
            exit_nodes_sorted = sorted(exit_nodes, key=lambda n: (
                "Exception Exit" in self.cfg.nodes[n].label
            ))
            
            widths = [self.dimensions[node_id].width for node_id in exit_nodes_sorted]
            row_width = sum(widths) + (len(widths) - 1) * self.min_x_gap
            x = -row_width / 2
            for node_id, width in zip(exit_nodes_sorted, widths):
                self.positions[node_id] = Position(x + width / 2, exit_y)
                x += width + self.min_x_gap

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box of positioned nodes accounting for their dimensions."""
        if not self.positions:
            return (0, 0, 100, 100)
        
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        for node_id, pos in self.positions.items():
            dim = self.dimensions.get(node_id, NodeDimensions(self.base_node_width, self.base_node_height))
            
            # Calculate actual rectangle bounds (center ± half dimensions)
            left = pos.x - dim.width / 2
            right = pos.x + dim.width / 2
            top = pos.y - dim.height / 2
            bottom = pos.y + dim.height / 2
            
            min_x = min(min_x, left)
            max_x = max(max_x, right)
            min_y = min(min_y, top)
            max_y = max(max_y, bottom)
        
        return (min_x, min_y, max_x, max_y)
    
    @property
    def node_dimensions(self) -> Dict[str, NodeDimensions]:
        """Alias for dimensions for backward compatibility."""
        return self.dimensions
