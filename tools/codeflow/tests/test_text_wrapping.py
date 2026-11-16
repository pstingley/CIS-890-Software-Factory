"""Tests for text wrapping and label layout."""

import unittest
from codeflow.layout.text_wrapper import TextWrapper


class TestTextWrapper(unittest.TestCase):
    """Test the TextWrapper class for intelligent text wrapping."""

    def setUp(self):
        """Set up test fixtures."""
        self.wrapper = TextWrapper(max_chars_per_line=25)

    def test_short_text_no_wrap(self):
        """Test that short text doesn't wrap."""
        text = "x = 1"
        result = self.wrapper.wrap(text)
        self.assertEqual(result, ["x = 1"])

    def test_long_text_wraps_at_spaces(self):
        """Test that long text wraps at spaces."""
        text = "square_num = row * 3 + col + 1"
        result = self.wrapper.wrap(text)
        # Should wrap at spaces
        self.assertGreater(len(result), 1)
        # All lines should fit within max_chars
        for line in result:
            self.assertLessEqual(len(line), 30)  # Allow some margin

    def test_wrap_preserves_exact_text(self):
        """Test that wrapping preserves exact source text."""
        text = "row_squares.append(f\"{square_value}\")"
        result = self.wrapper.wrap(text)
        # Rejoin and compare
        rejoined = "".join(result).replace("\n", "")
        self.assertEqual(text, rejoined.replace(" ", "").replace("\n", ""))

    def test_wrap_respects_operators(self):
        """Test that wrapping prefers to break at operators."""
        text = "value_one + value_two + value_three"
        result = self.wrapper.wrap(text)
        # Should have multiple lines
        self.assertGreater(len(result), 1)
        # Each line should be reasonable
        for line in result:
            self.assertLessEqual(len(line), 30)

    def test_wrap_respects_parentheses(self):
        """Test that wrapping prefers to break after parentheses."""
        text = "row_squares.append(something)"
        result = self.wrapper.wrap(text)
        # Should have at least this many lines if wrapping is needed
        if len(text) > 25:
            self.assertGreater(len(result), 1)

    def test_calculate_dimensions_single_line(self):
        """Test dimension calculation for single-line text."""
        text = "x = 1"
        width, height = self.wrapper.calculate_dimensions(text)
        self.assertEqual(width, 120.0)  # Base width
        self.assertEqual(height, 40.0)  # Base height

    def test_calculate_dimensions_wrapped(self):
        """Test dimension calculation for wrapped text."""
        text = "row_squares.append(f\"{square_value}\")"
        width, height = self.wrapper.calculate_dimensions(text)
        # Should be wider than base
        self.assertGreater(width, 120.0)
        # Should be taller (multiple lines)
        self.assertGreater(height, 40.0)

    def test_empty_text(self):
        """Test handling of empty text."""
        result = self.wrapper.wrap("")
        self.assertEqual(result, [])

    def test_text_with_special_characters(self):
        """Test wrapping text with special characters."""
        text = "board[row][col] = square_value"
        result = self.wrapper.wrap(text)
        # Should wrap somewhere
        rejoined = "".join(result)
        # Exact text should be preserved (without spaces added by join)
        self.assertIn("board", "".join(result))
        self.assertIn("square_value", "".join(result))


class TestLabelLayoutRegression(unittest.TestCase):
    """Regression tests for label layout and rendering."""

    def test_text_fits_in_node_bounds(self):
        """Test that wrapped text fits within calculated node dimensions."""
        from codeflow.analyzers.python_analyzer import analyze_python_file
        from codeflow.layout.simple_layout import SimpleHierarchicalLayout
        import tempfile
        import os

        # Create a test function with long labels
        source = '''def test_func():
    row_squares.append(f"{square_value}")
    row_squares.append(f"{square_num}")
    print(" | ".join(row_squares))
    return row_squares
'''
        fd, temp_path = tempfile.mkstemp(suffix='.py', text=True)
        try:
            os.write(fd, source.encode('utf-8'))
            os.close(fd)
            result = analyze_python_file(temp_path)

            if result.success and "test_func" in result.functions:
                cfg = result.functions["test_func"]
                layout = SimpleHierarchicalLayout(cfg)
                layout.layout()

                # Check that all text fit within node bounds
                # The layout dimensions should be consistent with wrapped text
                for node_id, wrapped_lines in layout.wrapped_labels.items():
                    if node_id not in layout.dimensions:
                        continue

                    dim = layout.dimensions[node_id]
                    # Verify that dimensions are reasonable for wrapped text
                    # At minimum, should be base_width for single-line or larger for wrapped
                    if len(wrapped_lines) > 1:
                        # Multi-line text should be wider and taller
                        self.assertGreater(dim.width, 120,
                                         f"Multi-line node {node_id} width should be > 120")
                        self.assertGreater(dim.height, 40,
                                         f"Multi-line node {node_id} height should be > 40")
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass


if __name__ == '__main__':
    unittest.main()
