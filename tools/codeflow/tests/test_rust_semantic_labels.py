"""Tests for Rust semantic labeling in flowcharts."""

import tempfile
from codeflow.analyzers.rust_analyzer import RustAnalyzer


class TestRustSemanticLabeling:
    """Test that flowchart nodes use meaningful source code labels, not generic node types."""

    def test_let_declaration_shows_actual_code(self):
        """Test that let declarations show actual code, not 'let_declaration'."""
        code = """fn test() {
            let x = 42;
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find the statement node (not entry/exit)
            statement_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'statement']
            assert len(statement_nodes) > 0

            # Should show actual code, not generic node type
            labels = [n.label for n in statement_nodes]
            assert any('let' in label and '42' in label for label in labels), \
                f"Expected 'let x = 42' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_function_call_shows_actual_call(self):
        """Test that function calls show receiver and function name."""
        code = """fn test() {
            let v = vec![];
            v.push(42);
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find statement nodes
            statement_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'statement']
            labels = [n.label for n in statement_nodes]

            # Should show actual method call
            assert any('push' in label for label in labels), \
                f"Expected method call 'push' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_if_condition_shows_actual_condition(self):
        """Test that if decisions show actual condition, not just 'if'."""
        code = """fn test(x: i32) {
            if x > 10 {
                let y = 1;
            }
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find decision nodes
            decision_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'decision']
            assert len(decision_nodes) > 0

            # Should show actual condition
            labels = [n.label for n in decision_nodes]
            assert any('>' in label and '10' in label for label in labels), \
                f"Expected condition 'x > 10' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_while_loop_shows_condition(self):
        """Test that while loops show actual loop condition."""
        code = """fn test(mut i: i32) {
            while i < 10 {
                i += 1;
            }
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find loop entry nodes
            loop_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'loop_entry']
            assert len(loop_nodes) > 0

            # Should show actual loop condition
            labels = [n.label for n in loop_nodes]
            assert any('while' in label and '<' in label and '10' in label for label in labels), \
                f"Expected 'while i < 10' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_for_loop_shows_pattern(self):
        """Test that for loops show actual iteration pattern."""
        code = """fn test() {
            for i in 0..10 {
                let x = i;
            }
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find loop entry nodes
            loop_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'loop_entry']
            assert len(loop_nodes) > 0

            # Should show actual for pattern (may be truncated)
            labels = [n.label for n in loop_nodes]
            assert any('for' in label and 'i' in label for label in labels), \
                f"Expected 'for i' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_return_shows_return_value(self):
        """Test that return statements show actual return value."""
        code = """fn test() -> i32 {
            return 42;
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find statement nodes
            statement_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'statement']
            labels = [n.label for n in statement_nodes]

            # Should show actual return value
            assert any('return' in label and '42' in label for label in labels), \
                f"Expected 'return 42' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_match_shows_scrutinee(self):
        """Test that match expressions show the value being matched."""
        code = """fn test(x: i32) {
            match x {
                1 => {},
                _ => {},
            }
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find decision nodes (match creates decisions)
            decision_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'decision']
            assert len(decision_nodes) > 0

            # Should show match with scrutinee
            labels = [n.label for n in decision_nodes]
            assert any('match' in label for label in labels), \
                f"Expected 'match' in labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_no_generic_node_type_labels(self):
        """Test that generic Tree-sitter node types are never used as labels."""
        code = """fn test() {
            let x = 42;
            if x > 10 {
                x + 1
            } else {
                x - 1
            }
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Collect all labels
            all_labels = [n.label for n in cfg.nodes.values()]

            # Forbidden generic node types (should never appear as labels)
            forbidden_types = {
                'let_declaration', 'call_expression', 'binary_expression',
                'assignment_expression', 'if_expression', 'match_expression',
                'for_expression', 'while_expression', 'return_expression',
                'identifier', 'integer_literal', 'comparison_expression'
            }

            for label in all_labels:
                assert label not in forbidden_types, \
                    f"Found forbidden generic node type '{label}' as label. All labels: {all_labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_label_truncation_for_long_code(self):
        """Test that very long statements are truncated to remain readable."""
        code = """fn test() {
            let very_long_variable_name_that_is_quite_excessive = some_function_with_many_arguments(arg1, arg2, arg3, arg4, arg5);
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find statement nodes
            statement_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'statement']
            labels = [n.label for n in statement_nodes]

            # Labels should be truncated (not entire source)
            assert any(len(label) < 100 for label in labels), \
                f"Expected truncated labels, got: {labels}"
        finally:
            import os
            os.unlink(temp_file)

    def test_source_line_references_preserved(self):
        """Test that source file and line references are preserved with semantic labels."""
        code = """fn test() {
            let x = 42;
        }"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            analyzer = RustAnalyzer()
            result = analyzer.analyze(temp_file)
            assert result.success
            cfg = result.functions['test']

            # Find statement nodes
            statement_nodes = [n for n in cfg.nodes.values() if n.node_type.value == 'statement']
            assert len(statement_nodes) > 0

            # Check that source locations are present
            for node in statement_nodes:
                assert node.source_location is not None, "Missing source location"
                assert node.source_location.file == temp_file, "Wrong file reference"
                assert node.source_location.start_line > 0, "Invalid line number"
        finally:
            import os
            os.unlink(temp_file)
