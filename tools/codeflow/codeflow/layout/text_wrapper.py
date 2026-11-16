"""Text wrapping for CFG node labels with intelligent boundary detection."""

import re
from typing import List, Tuple


class TextWrapper:
    """Wraps long text at natural boundaries while preserving exact source expressions."""

    def __init__(self, max_chars_per_line: int = 25, char_width: float = 7.0):
        """Initialize text wrapper.

        Args:
            max_chars_per_line: Target maximum characters per line
            char_width: Approximate pixel width of a character at rendering size
        """
        self.max_chars_per_line = max_chars_per_line
        self.char_width = char_width

        # Boundaries where we prefer to wrap (in order of preference)
        self.wrap_boundaries = [
            r'\s+',          # Spaces (highest priority)
            r'(?<=\))',      # After closing parenthesis
            r'(?<=,)',       # After comma
            r'(?<=[+\-*/%])', # After operators
            r'(?==)',        # Before equals sign
        ]

    def wrap(self, text: str, max_width: int = None) -> List[str]:
        """Wrap text at natural boundaries.

        Args:
            text: Text to wrap
            max_width: Maximum width in characters (uses max_chars_per_line if not provided)

        Returns:
            List of wrapped text lines (preserves original text, no truncation)
        """
        if not text:
            return []

        target_width = max_width or self.max_chars_per_line

        # If text fits on one line, return it as-is
        if len(text) <= target_width:
            return [text]

        lines = []
        remaining = text

        while remaining:
            if len(remaining) <= target_width:
                lines.append(remaining)
                break

            # Find the best break point
            best_break = self._find_break_point(remaining, target_width)

            if best_break == 0:
                # No good break point found, force split at target width
                lines.append(remaining[:target_width])
                remaining = remaining[target_width:].lstrip()
            else:
                # Take text up to break point
                line = remaining[:best_break].rstrip()
                lines.append(line)
                # Continue with remaining text
                remaining = remaining[best_break:].lstrip()

        return lines

    def _find_break_point(self, text: str, max_width: int) -> int:
        """Find the best position to break text within max_width.

        Returns the index where the line should break, or 0 if no break found.
        """
        # Look for break points in order of preference
        for boundary_pattern in self.wrap_boundaries:
            # Find all matches of this boundary type
            for match in re.finditer(boundary_pattern, text):
                break_pos = match.end()
                # Only consider breaks within our max width
                if break_pos <= max_width:
                    return break_pos
                # If we find a match beyond max_width, use the previous position if it exists
                # (Don't return here - look for earlier boundaries)

        # Fallback: Look for any whitespace at or before max_width
        last_space = text.rfind(' ', 0, max_width + 1)
        if last_space > 0:
            return last_space + 1

        # No break point found
        return 0

    def calculate_dimensions(self, text: str,
                            base_width: float = 120.0,
                            base_height: float = 40.0,
                            line_height: float = 14.0) -> Tuple[float, float]:
        """Calculate the width and height needed for wrapped text.

        Args:
            text: Text to measure
            base_width: Minimum node width
            base_height: Height of single-line node
            line_height: Height of each wrapped line

        Returns:
            (width, height) tuple for the node
        """
        lines = self.wrap(text)

        if len(lines) <= 1:
            return (base_width, base_height)

        # Find the longest line to determine width
        max_line_length = max(len(line) for line in lines)

        # Calculate width based on longest line
        # Base width + extra space for wrapped text
        calculated_width = max(
            base_width,
            max_line_length * self.char_width + 20  # 20px padding
        )

        # Calculate height based on number of lines
        calculated_height = base_height + (len(lines) - 1) * line_height

        return (calculated_width, calculated_height)
