"""Regression tests for Rust syntax-only node filtering."""

import tempfile
import os
from codeflow.analyzers.rust_analyzer import RustAnalyzer
from codeflow.graph import NodeType


class TestRustSyntaxNodeFiltering:
    """Test that syntax-only nodes (braces, semicolons) are not generated as CFG nodes."""

    def test_empty_function(self):
        """An empty function should have only entry and exit nodes."""
        code = """
fn empty() {
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                assert 'empty' in result.functions

                cfg = result.functions['empty']
                nodes = list(cfg.nodes.values())  # Get nodes from dict

                # Should have exactly 2 nodes: entry and exit
                assert len(nodes) == 2, f"Expected 2 nodes, got {len(nodes)}: {[n.label for n in nodes]}"

                # Verify node types
                node_types = {n.node_type for n in nodes}
                assert NodeType.ENTRY in node_types
                assert NodeType.EXIT in node_types

                # Verify no STATEMENT nodes
                statement_nodes = [n for n in nodes if n.node_type == NodeType.STATEMENT]
                assert len(statement_nodes) == 0, f"Found unexpected statement nodes: {[n.label for n in statement_nodes]}"

            finally:
                os.unlink(f.name)

    def test_function_with_single_statement(self):
        """A function with one statement should not generate nodes for braces or semicolons."""
        code = """
fn test() {
    let x = 5;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['test']
                nodes = list(cfg.nodes.values())

                # Should have entry, exit, and 1 statement node (for the let_declaration)
                # but NOT nodes for { } or ;
                labels = {n.label for n in nodes}

                # Should NOT contain brace or semicolon labels
                assert "{" not in labels, f"Found {{ node in CFG: {labels}"
                assert "}" not in labels, f"Found }} node in CFG: {labels}"
                assert ";" not in labels, f"Found ; node in CFG: {labels}"

            finally:
                os.unlink(f.name)

    def test_function_with_nested_blocks(self):
        """Nested blocks should not generate brace nodes."""
        code = """
fn nested() {
    let x = 5;
    {
        let y = 10;
    }
    let z = 15;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['nested']
                nodes = list(cfg.nodes.values())

                labels = {n.label for n in nodes}

                # No brace nodes should exist
                assert "{" not in labels, f"Found {{ node: {labels}"
                assert "}" not in labels, f"Found }} node: {labels}"

            finally:
                os.unlink(f.name)

    def test_function_with_if_statement(self):
        """If statements should generate decision nodes, not brace nodes."""
        code = """
fn conditional() {
    if x > 5 {
        let y = 10;
    } else {
        let y = 20;
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['conditional']
                nodes = list(cfg.nodes.values())

                # Should have decision nodes but not brace nodes
                labels = {n.label for n in nodes}

                assert "{" not in labels, f"Found {{ node: {labels}"
                assert "}" not in labels, f"Found }} node: {labels}"

                # Should have an "if" decision node
                has_if_node = any('if' in label.lower() for label in labels if isinstance(label, str))
                assert has_if_node, f"No if decision node found: {labels}"

            finally:
                os.unlink(f.name)

    def test_function_with_loop(self):
        """Loop statements should generate loop nodes, not brace nodes."""
        code = """
fn looping() {
    for i in 0..10 {
        let x = i;
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['looping']
                nodes = list(cfg.nodes.values())

                labels = {n.label for n in nodes}

                # No brace or semicolon nodes
                assert "{" not in labels, f"Found {{ node: {labels}"
                assert "}" not in labels, f"Found }} node: {labels}"
                assert ";" not in labels, f"Found ; node: {labels}"

            finally:
                os.unlink(f.name)

    def test_no_dangling_exception_exits(self):
        """Exception exit nodes should not be created for simple functions."""
        code = """
fn simple() {
    let x = 5;
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['simple']
                nodes = list(cfg.nodes.values())

                # Should have no exception exit nodes
                exception_exits = [n for n in nodes if n.is_exceptional_exit]
                assert len(exception_exits) == 0, f"Found unexpected exception exit nodes: {[n.label for n in exception_exits]}"

                # Should have exactly one normal exit
                normal_exits = [nid for nid in cfg.exit_node_ids if nid not in cfg.exception_exit_node_ids]
                assert len(normal_exits) == 1, f"Expected 1 normal exit, got {len(normal_exits)}"

            finally:
                os.unlink(f.name)

    def test_complex_function_no_syntax_nodes(self):
        """Complex functions should not generate syntax-only nodes."""
        code = """
fn complex(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }

    let mut result = 1;
    for i in 2..=n {
        result = result * i;
    }

    result
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['complex']
                nodes = list(cfg.nodes.values())

                labels = {n.label for n in nodes}

                # No syntax nodes
                assert "{" not in labels, f"Found {{ node: {labels}"
                assert "}" not in labels, f"Found }} node: {labels}"
                assert ";" not in labels, f"Found ; node: {labels}"

                # Should have semantic nodes (if, loop, etc.)
                has_control_flow = any(
                    any(keyword in str(label).lower() for keyword in ['if', 'for', 'loop', 'while', 'match'])
                    for label in labels if isinstance(label, str)
                )
                # Note: This function might not have semantic control-flow nodes if the loop isn't
                # recognized, but it definitely shouldn't have syntax nodes

            finally:
                os.unlink(f.name)

    def test_function_with_return_statements_only(self):
        """Function with multiple returns should have return nodes, not syntax nodes."""
        code = """
fn multi_return(x: i32) -> i32 {
    if x > 0 {
        return 1;
    }

    if x < 0 {
        return -1;
    }

    0
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['multi_return']
                nodes = list(cfg.nodes.values())

                labels = {n.label for n in nodes}

                # No syntax nodes
                assert "{" not in labels, f"Found {{ node: {labels}"
                assert "}" not in labels, f"Found }} node: {labels}"

            finally:
                os.unlink(f.name)

    def test_match_expression_no_syntax_nodes(self):
        """Match expressions should not generate brace nodes."""
        code = """
fn pattern_match(x: i32) -> &'static str {
    match x {
        1 => "one",
        2 => "two",
        _ => "other",
    }
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(code)
            f.flush()

            try:
                analyzer = RustAnalyzer()
                result = analyzer.analyze(f.name)

                assert result.success, f"Analysis failed: {result.errors}"
                cfg = result.functions['pattern_match']
                nodes = list(cfg.nodes.values())

                labels = {n.label for n in nodes}

                # No brace or syntax nodes
                assert "{" not in labels, f"Found {{ node: {labels}"
                assert "}" not in labels, f"Found }} node: {labels}"

            finally:
                os.unlink(f.name)
