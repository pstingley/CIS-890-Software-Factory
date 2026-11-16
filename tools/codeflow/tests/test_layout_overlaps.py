"""Tests for detecting overlapping nodes in layout."""

import unittest
from codeflow.analyzers.python_analyzer import analyze_python_file
import tempfile
import os

class TestLayoutNoOverlaps(unittest.TestCase):
    """Test that layout produces no overlapping node bounding boxes."""

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

    def _get_node_bounds(self, cfg, layout):
        """Get bounding rectangles for all nodes."""
        bounds = {}
        for node_id, pos in layout.positions.items():
            if node_id not in layout.node_dimensions:
                continue
            dim = layout.node_dimensions[node_id]
            bounds[node_id] = {
                'left': pos.x - dim.width / 2,
                'right': pos.x + dim.width / 2,
                'top': pos.y - dim.height / 2,
                'bottom': pos.y + dim.height / 2,
                'width': dim.width,
                'height': dim.height,
            }
        return bounds

    def _rects_overlap(self, rect1, rect2, tolerance=0.1):
        """Check if two rectangles overlap (with small tolerance for floating point)."""
        return not (rect1['right'] + tolerance < rect2['left'] or
                   rect1['left'] - tolerance > rect2['right'] or
                   rect1['bottom'] + tolerance < rect2['top'] or
                   rect1['top'] - tolerance > rect2['bottom'])

    def _check_no_overlaps(self, bounds):
        """Check that no two nodes overlap."""
        node_ids = list(bounds.keys())
        overlaps = []

        for i, node_id1 in enumerate(node_ids):
            for node_id2 in node_ids[i+1:]:
                if self._rects_overlap(bounds[node_id1], bounds[node_id2]):
                    overlaps.append((node_id1, node_id2))

        return overlaps

    def test_check_draw_no_overlaps(self):
        """Test that check_draw has no overlapping nodes."""
        source = '''
def check_draw(board):
    """Check if board is full."""
    for row in board:
        if ' ' in row:
            return False
    return True
'''
        cfg = self._analyze_function(source, 'check_draw')
        self.assertIsNotNone(cfg, "Function should be analyzed")

        # Create layout and get node bounds
        from codeflow.layout.simple_layout import SimpleHierarchicalLayout
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()

        bounds = self._get_node_bounds(cfg, layout)
        overlaps = self._check_no_overlaps(bounds)

        self.assertEqual(overlaps, [], f"check_draw should have no overlaps, but found: {overlaps}")

    def test_complex_function_no_overlaps(self):
        """Test that complex function (with long labels) has no overlapping nodes."""
        source = '''
def complex_function_with_many_conditions_and_long_names():
    """Function with long name and complex logic."""
    if some_very_long_condition_name_here:
        return process_first_branch_with_long_name()
    elif another_very_long_condition_name():
        return process_second_branch_with_long_name()
    else:
        return default_branch_with_long_name()
'''
        cfg = self._analyze_function(source, 'complex_function_with_many_conditions_and_long_names')
        self.assertIsNotNone(cfg, "Function should be analyzed")

        from codeflow.layout.simple_layout import SimpleHierarchicalLayout
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()

        bounds = self._get_node_bounds(cfg, layout)
        overlaps = self._check_no_overlaps(bounds)

        self.assertEqual(overlaps, [], f"Complex function should have no overlaps, but found: {overlaps}")

    def test_get_player_move_no_overlaps(self):
        """Test that get_player_move (with long wrapped labels) has no overlaps."""
        # This is a simplified version that tests the wrapping behavior
        source = '''
def get_player_move_with_very_long_descriptive_name(board_state):
    """Get next player move with extensive validation."""
    while True:
        try:
            move_input = input("Enter position (1-9) or q to quit: ")
            if move_input.lower() == 'q':
                raise Exception("User quit")
            pos = int(move_input)
            if 1 <= pos <= 9 and board_state[pos - 1] == ' ':
                return pos
            print("Invalid: position occupied or out of range")
        except ValueError:
            print("Enter number 1-9 or q")
        except KeyboardInterrupt:
            raise Exception("Interrupted")
'''
        cfg = self._analyze_function(source, 'get_player_move_with_very_long_descriptive_name')
        self.assertIsNotNone(cfg, "Function should be analyzed")

        from codeflow.layout.simple_layout import SimpleHierarchicalLayout
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()

        bounds = self._get_node_bounds(cfg, layout)
        overlaps = self._check_no_overlaps(bounds)

        self.assertEqual(overlaps, [], f"get_player_move should have no overlaps, but found: {overlaps}")

    def test_tictactoe_get_player_move_no_overlaps(self):
        """Test actual tictactoe.py get_player_move function."""
        import pathlib

        tictactoe_path = pathlib.Path(__file__).parent.parent / 'examples' / 'python' / 'tictactoe.py'
        if not tictactoe_path.exists():
            self.skipTest(f"tictactoe.py not found at {tictactoe_path}")

        from codeflow.analyzers.python_analyzer import analyze_python_file
        result = analyze_python_file(str(tictactoe_path))

        cfg = result.functions.get('get_player_move')
        self.assertIsNotNone(cfg, "get_player_move should be analyzed")

        from codeflow.layout.simple_layout import SimpleHierarchicalLayout
        layout = SimpleHierarchicalLayout(cfg)
        layout.layout()

        bounds = self._get_node_bounds(cfg, layout)
        overlaps = self._check_no_overlaps(bounds)

        self.assertEqual(overlaps, [], f"tictactoe.get_player_move should have no overlaps, but found: {overlaps}")

if __name__ == '__main__':
    unittest.main()
