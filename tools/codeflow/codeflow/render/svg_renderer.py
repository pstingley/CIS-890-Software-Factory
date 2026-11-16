"""SVG renderer - converts CFG to SVG diagram."""

from typing import Dict, Tuple
from codeflow.graph import CFG, CFGNode, CFGEdge, NodeType
from codeflow.layout.simple_layout import SimpleHierarchicalLayout, Position, NodeDimensions
import html as html_module


class SVGRenderer:
    """Renders a CFG as SVG."""
    
    def __init__(self, cfg: CFG):
        self.cfg = cfg
        self.layout = SimpleHierarchicalLayout(cfg)
        self.positions = self.layout.layout()
        # Get dimensions from layout (pre-calculated with text wrapping)
        self.node_dimensions = self.layout.dimensions
        self.padding = 40
    
    def render(self) -> str:
        """Render the CFG as SVG string."""
        # Calculate viewBox from actual node positions and dimensions
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        # Calculate bounds from positioned nodes with their actual dimensions
        for node_id, pos in self.positions.items():
            if node_id not in self.node_dimensions:
                continue
            
            dim = self.node_dimensions[node_id]
            
            # Calculate rectangle bounds (center ± half dimensions)
            rect_left = pos.x - dim.width / 2
            rect_right = pos.x + dim.width / 2
            rect_top = pos.y - dim.height / 2
            rect_bottom = pos.y + dim.height / 2
            
            min_x = min(min_x, rect_left)
            max_x = max(max_x, rect_right)
            min_y = min(min_y, rect_top)
            max_y = max(max_y, rect_bottom)
        
        # Apply padding
        vb_min_x = min_x - self.padding
        vb_min_y = min_y - self.padding
        vb_max_x = max_x + self.padding
        vb_max_y = max_y + self.padding
        
        vb_width = vb_max_x - vb_min_x
        vb_height = vb_max_y - vb_min_y
        
        svg_parts = [
            f'<svg width="{vb_width}" height="{vb_height}" '
            f'viewBox="{vb_min_x} {vb_min_y} {vb_width} {vb_height}" '
            f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">',
            '<defs>',
            self._get_style_defs(),
            '</defs>',
            '<g>',
        ]
        
        # Add edges first (so they appear behind nodes)
        for edge in self.cfg.edges:
            svg_parts.append(self._render_edge(edge))
        
        # Add nodes
        for node_id, node in self.cfg.nodes.items():
            svg_parts.append(self._render_node(node_id, node))
        
        svg_parts.extend(['</g>', '</svg>'])
        
        return '\n'.join(svg_parts)
    
    def _get_style_defs(self) -> str:
        """Return CSS style definitions."""
        return '''
        <style>
            .entry-node { fill: #90EE90; stroke: #2d5016; stroke-width: 2; }
            .exit-node { fill: #FFB6C6; stroke: #8b0000; stroke-width: 2; }
            .statement-node { fill: #E0F0FF; stroke: #003366; stroke-width: 1.5; }
            .decision-node { fill: #FFFFE0; stroke: #999900; stroke-width: 1.5; }
            .loop-node { fill: #FFE4B5; stroke: #ff8c00; stroke-width: 1.5; }
            .call-node { fill: #E6E6FA; stroke: #4b0082; stroke-width: 1.5; }
            .exception-node { fill: #FFE4E1; stroke: #dc143c; stroke-width: 1.5; }
            .node-label { font-family: Arial, sans-serif; font-size: 11px; text-anchor: middle; }
            .edge-label { font-family: Arial, sans-serif; font-size: 10px; fill: #333; }
            .normal-edge { stroke: #000; stroke-width: 1.5; fill: none; }
            .true-edge { stroke: #008000; stroke-width: 1.5; fill: none; stroke-dasharray: 5,5; }
            .false-edge { stroke: #dc143c; stroke-width: 1.5; fill: none; stroke-dasharray: 5,5; }
            .exception-edge { stroke: #ff6347; stroke-width: 2; fill: none; stroke-dasharray: 3,3; }
            .break-edge { stroke: #ff8c00; stroke-width: 1.5; fill: none; }
            .continue-edge { stroke: #4169e1; stroke-width: 1.5; fill: none; }
            .loop-back-edge { stroke: #800080; stroke-width: 1.5; fill: none; stroke-dasharray: 3,3; }
            .arrow { fill: #000; }
        </style>
        '''
    
    def _render_node(self, node_id: str, node: CFGNode) -> str:
        """Render a single node using pre-calculated dimensions."""
        if node_id not in self.positions:
            return ""
        
        pos = self.positions[node_id]
        x = pos.x
        y = pos.y
        
        # Use pre-calculated dimensions from layout
        dim = self.node_dimensions.get(node_id)
        if not dim:
            return ""
        
        adjusted_width = dim.width
        adjusted_height = dim.height
        
        # Determine node class based on type
        if node.node_type == NodeType.ENTRY:
            shape_class = "entry-node"
        elif node.node_type == NodeType.EXIT:
            shape_class = "exit-node"
        elif node.node_type == NodeType.DECISION:
            shape_class = "decision-node"
        elif node.node_type in [NodeType.LOOP_ENTRY, NodeType.LOOP_BODY]:
            shape_class = "loop-node"
        elif node.node_type == NodeType.CALL:
            shape_class = "call-node"
        elif node.node_type == NodeType.EXCEPTION:
            shape_class = "exception-node"
        else:
            shape_class = "statement-node"
        
        # Escape label and wrap text
        safe_label = html_module.escape(node.label)
        
        # Wrap text using same algorithm as layout
        max_chars_per_line = 16
        if len(safe_label) > max_chars_per_line:
            words = safe_label.split()
            lines = []
            current_line = []
            for word in words:
                if sum(len(w) for w in current_line) + len(current_line) + len(word) > max_chars_per_line:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            if current_line:
                lines.append(' '.join(current_line))
        else:
            lines = [safe_label]
        
        # Create rectangle node (use pre-calculated dimensions)
        svg_node = [
            f'<g id="{node_id}" class="node" data-node-id="{node_id}">',
            f'  <rect x="{x - adjusted_width/2}" y="{y - adjusted_height/2}" '
            f'width="{adjusted_width}" height="{adjusted_height}" '
            f'class="{shape_class}" rx="5"/>',
        ]
        
        # Add text lines
        for i, line in enumerate(lines):
            text_y = y + (i - len(lines)/2 + 0.5) * 14 + 4
            svg_node.append(f'  <text x="{x}" y="{text_y}" class="node-label">{line}</text>')
        
        # Add source reference as tooltip
        if node.source_location:
            source_code = html_module.escape(node.source_location.source_code)
            svg_node.append(
                f'  <title>Line {node.source_location.start_line}: {source_code}</title>'
            )
        
        svg_node.append('</g>')
        return '\n'.join(svg_node)
    
    def _render_edge(self, edge: CFGEdge) -> str:
        """Render a single edge."""
        if not edge.source_id or not edge.target_id:
            return ""
        if edge.source_id not in self.positions or edge.target_id not in self.positions:
            return ""
        
        source_pos = self.positions[edge.source_id]
        target_pos = self.positions[edge.target_id]
        
        # Get dimensions for edge routing
        source_dim = self.node_dimensions.get(edge.source_id)
        target_dim = self.node_dimensions.get(edge.target_id)
        
        if not source_dim or not target_dim:
            return ""
        
        x1 = source_pos.x
        y1 = source_pos.y + source_dim.height / 2
        x2 = target_pos.x
        y2 = target_pos.y - target_dim.height / 2
        
        # Determine edge style
        edge_type_map = {
            'normal': 'normal-edge',
            'true': 'true-edge',
            'false': 'false-edge',
            'exception': 'exception-edge',
            'break': 'break-edge',
            'continue': 'continue-edge',
            'loop_back': 'loop-back-edge',
        }
        edge_class = edge_type_map.get(edge.edge_type.value, 'normal-edge')
        
        # Create arrow marker ID
        arrow_id = f"arrow-{edge.edge_type.value}"
        
        svg_edge = [
            f'<g class="edge" id="edge_{edge.source_id}_{edge.target_id}">',
            f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{edge_class}" '
            f'marker-end="url(#{arrow_id})"/>',
        ]
        
        # Add edge label if present
        if edge.label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            safe_label = html_module.escape(edge.label)
            svg_edge.append(
                f'  <text x="{mid_x}" y="{mid_y - 5}" class="edge-label">{safe_label}</text>'
            )
        
        svg_edge.append('</g>')
        return '\n'.join(svg_edge)
