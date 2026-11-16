"""Tests for control-flow graph validation and behavioral verification."""

import pytest
from codeflow.graph import (
    CFG, CFGNode, CFGEdge, NodeType, EdgeType, SourceLocation
)
from codeflow.validation import CFGValidator, CompletionStatus, ValidationError
from codeflow.behavioral_verification import BehavioralVerifier


class TestCFGValidator:
    """Test control-flow graph validation."""

    def test_validate_valid_simple_path(self):
        """Test validation of a valid simple linear path."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        stmt = CFGNode("stmt", "x = 42", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(stmt)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "stmt")
        cfg.add_edge_simple("stmt", "exit")

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_validate_detects_missing_entry(self):
        """Test that validation detects missing entry node."""
        cfg = CFG("test_function")
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)
        cfg.add_node(exit_node)
        cfg.exit_node_ids = ["exit"]

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "missing_entry" for e in result.errors)

    def test_validate_detects_invalid_edge_target(self):
        """Test that validation detects invalid edge targets."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        cfg.add_node(entry)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "nonexistent")

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "invalid_target" for e in result.errors)

    def test_validate_detects_break_to_exit(self):
        """Test that validation detects break edges targeting exit."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        break_stmt = CFGNode("break", "break", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(break_stmt)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "break")
        cfg.add_edge(CFGEdge("break", "exit", "", EdgeType.BREAK))

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "break_to_exit" for e in result.errors)

    def test_validate_detects_generic_labels(self):
        """Test that validation detects generic AST node labels."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        bad_node = CFGNode("bad", "let_declaration", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(bad_node)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "bad")
        cfg.add_edge_simple("bad", "exit")

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "generic_label" for e in result.errors)

    def test_validate_detects_punctuation_labels(self):
        """Test that validation detects bare punctuation labels."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        bad_node = CFGNode("bad", "{", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(bad_node)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "bad")
        cfg.add_edge_simple("bad", "exit")

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "generic_label" for e in result.errors)

    def test_validate_partial_graph_status(self):
        """Test that partial graphs are marked as PARTIAL status."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]
        cfg.is_partial = True
        cfg.partial_reason = "Macros not supported"

        cfg.add_edge_simple("entry", "exit")

        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.status == CompletionStatus.PARTIAL
        assert result.is_valid  # No validation errors

    def test_validate_decision_has_branches(self):
        """Test that decision nodes are checked for branches."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        decision = CFGNode("if", "if x > 0", NodeType.DECISION)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(decision)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "if")
        # Decision with no outgoing edges should warn
        cfg.add_edge_simple("if", "exit")

        validator = CFGValidator(cfg)
        result = validator.validate()

        # This should produce a warning about no branches
        assert len(result.warnings) > 0


class TestBehavioralVerifier:
    """Test behavioral verification helpers."""

    def test_assert_path_exists(self):
        """Test path existence assertion."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        stmt1 = CFGNode("stmt1", "x = 1", NodeType.STATEMENT)
        stmt2 = CFGNode("stmt2", "y = 2", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(stmt1)
        cfg.add_node(stmt2)
        cfg.add_node(exit_node)

        cfg.add_edge_simple("entry", "stmt1")
        cfg.add_edge_simple("stmt1", "stmt2")
        cfg.add_edge_simple("stmt2", "exit")

        verifier = BehavioralVerifier(cfg)
        verifier.assert_path_exists(["entry", "stmt1", "stmt2", "exit"])

    def test_assert_path_exists_fails(self):
        """Test that path assertion fails when path doesn't exist."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)
        cfg.add_edge_simple("entry", "exit")

        verifier = BehavioralVerifier(cfg)
        with pytest.raises(AssertionError):
            verifier.assert_path_exists(["entry", "nonexistent", "exit"])

    def test_assert_edge_exists(self):
        """Test edge existence assertion."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)
        cfg.add_edge_simple("entry", "exit")

        verifier = BehavioralVerifier(cfg)
        verifier.assert_edge_exists("entry", "exit")

    def test_assert_edge_exists_with_type(self):
        """Test edge existence with type checking."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)
        cfg.add_edge(CFGEdge("entry", "exit", "true", EdgeType.TRUE))

        verifier = BehavioralVerifier(cfg)
        verifier.assert_edge_exists("entry", "exit", EdgeType.TRUE, "true")

    def test_assert_edge_does_not_exist(self):
        """Test that non-existent edge assertion passes."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)

        verifier = BehavioralVerifier(cfg)
        verifier.assert_edge_does_not_exist("entry", "exit")

    def test_assert_edge_does_not_exist_fails(self):
        """Test that edge-does-not-exist fails when edge exists."""
        cfg = CFG("test_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)
        cfg.add_edge_simple("entry", "exit")

        verifier = BehavioralVerifier(cfg)
        with pytest.raises(AssertionError):
            verifier.assert_edge_does_not_exist("entry", "exit")

    def test_assert_node_label_does_not_contain(self):
        """Test that generic labels can be detected."""
        cfg = CFG("test_function")
        good_node = CFGNode("good", "x = 42", NodeType.STATEMENT)
        cfg.add_node(good_node)

        verifier = BehavioralVerifier(cfg)
        verifier.assert_node_label_does_not_contain("let_declaration")

    def test_assert_node_label_does_not_contain_fails(self):
        """Test that generic label detection fails correctly."""
        cfg = CFG("test_function")
        bad_node = CFGNode("bad", "let_declaration", NodeType.STATEMENT)
        cfg.add_node(bad_node)

        verifier = BehavioralVerifier(cfg)
        with pytest.raises(AssertionError):
            verifier.assert_node_label_does_not_contain("let_declaration")

    def test_assert_break_routes_to_target(self):
        """Test break routing assertion."""
        cfg = CFG("test_function")
        loop_entry = CFGNode("loop_entry", "while x", NodeType.LOOP_ENTRY)
        break_stmt = CFGNode("break", "break", NodeType.STATEMENT)
        after_loop = CFGNode("after_loop", "next", NodeType.STATEMENT)

        cfg.add_node(loop_entry)
        cfg.add_node(break_stmt)
        cfg.add_node(after_loop)

        cfg.add_edge(CFGEdge("break_stmt", "after_loop", "", EdgeType.BREAK))

        verifier = BehavioralVerifier(cfg)
        verifier.assert_break_routes_to_target("break_stmt", "after_loop")

    def test_assert_continue_routes_to_loop_entry(self):
        """Test continue routing assertion."""
        cfg = CFG("test_function")
        loop_entry = CFGNode("loop_entry", "while x", NodeType.LOOP_ENTRY)
        continue_stmt = CFGNode("continue", "continue", NodeType.STATEMENT)

        cfg.add_node(loop_entry)
        cfg.add_node(continue_stmt)

        cfg.add_edge(CFGEdge("continue", "loop_entry", "", EdgeType.CONTINUE))

        verifier = BehavioralVerifier(cfg)
        verifier.assert_continue_routes_to_loop_entry("continue", "loop_entry")

    def test_assert_decision_has_branches(self):
        """Test decision branch assertion."""
        cfg = CFG("test_function")
        decision = CFGNode("if", "if x > 0", NodeType.DECISION)
        true_node = CFGNode("true", "y = 1", NodeType.STATEMENT)
        false_node = CFGNode("false", "y = 2", NodeType.STATEMENT)

        cfg.add_node(decision)
        cfg.add_node(true_node)
        cfg.add_node(false_node)

        cfg.add_edge(CFGEdge("if", "true", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("if", "false", "false", EdgeType.FALSE))

        verifier = BehavioralVerifier(cfg)
        verifier.assert_decision_has_branches("if", ["true", "false"])

    def test_assert_all_decision_edges_have_labels(self):
        """Test that decision edges must be labeled."""
        cfg = CFG("test_function")
        decision = CFGNode("if", "if x > 0", NodeType.DECISION)
        true_node = CFGNode("true", "y = 1", NodeType.STATEMENT)
        false_node = CFGNode("false", "y = 2", NodeType.STATEMENT)

        cfg.add_node(decision)
        cfg.add_node(true_node)
        cfg.add_node(false_node)

        cfg.add_edge(CFGEdge("if", "true", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("if", "false", "false", EdgeType.FALSE))

        verifier = BehavioralVerifier(cfg)
        verifier.assert_all_decision_edges_have_labels()

    def test_assert_all_decision_edges_have_labels_fails(self):
        """Test that unlabeled decision edges are detected."""
        cfg = CFG("test_function")
        decision = CFGNode("if", "if x > 0", NodeType.DECISION)
        true_node = CFGNode("true", "y = 1", NodeType.STATEMENT)

        cfg.add_node(decision)
        cfg.add_node(true_node)

        cfg.add_edge(CFGEdge("if", "true", "", EdgeType.NORMAL))  # Unlabeled!

        verifier = BehavioralVerifier(cfg)
        with pytest.raises(AssertionError):
            verifier.assert_all_decision_edges_have_labels()

    def test_assert_node_has_source_location(self):
        """Test source location verification."""
        cfg = CFG("test_function")
        stmt = CFGNode(
            "stmt",
            "x = 42",
            NodeType.STATEMENT,
            SourceLocation("file.py", 42, 42, "x = 42"),
        )
        cfg.add_node(stmt)

        verifier = BehavioralVerifier(cfg)
        verifier.assert_node_has_source_location("stmt")

    def test_assert_node_has_source_location_fails(self):
        """Test that missing source location is detected."""
        cfg = CFG("test_function")
        stmt = CFGNode("stmt", "x = 42", NodeType.STATEMENT)
        cfg.add_node(stmt)

        verifier = BehavioralVerifier(cfg)
        with pytest.raises(AssertionError):
            verifier.assert_node_has_source_location("stmt")

    def test_loop_back_edge_detection(self):
        """Test loop-back edge detection."""
        cfg = CFG("test_function")
        loop_entry = CFGNode("loop_entry", "while x", NodeType.LOOP_ENTRY)
        loop_body = CFGNode("body", "y = y + 1", NodeType.STATEMENT)

        cfg.add_node(loop_entry)
        cfg.add_node(loop_body)

        cfg.add_edge_simple("loop_entry", "body")
        cfg.add_edge(CFGEdge("body", "loop_entry", "", EdgeType.LOOP_BACK))

        verifier = BehavioralVerifier(cfg)
        verifier.assert_loop_back_edge_exists("loop_entry")

    def test_loop_back_edge_detection_fails(self):
        """Test that missing loop-back edge is detected."""
        cfg = CFG("test_function")
        loop_entry = CFGNode("loop_entry", "while x", NodeType.LOOP_ENTRY)

        cfg.add_node(loop_entry)

        verifier = BehavioralVerifier(cfg)
        with pytest.raises(AssertionError):
            verifier.assert_loop_back_edge_exists("loop_entry")


class TestCFGMarkValidationFailed:
    """Test marking CFG as validation-failed."""

    def test_mark_validation_failed_sets_partial(self):
        """Test that marking validation failed sets is_partial."""
        cfg = CFG("test_function")
        cfg.mark_validation_failed("Break routing error")

        assert cfg.is_partial
        assert "Break routing error" in cfg.partial_reason

    def test_mark_validation_failed_appends_reasons(self):
        """Test that multiple failure reasons accumulate."""
        cfg = CFG("test_function")
        cfg.mark_validation_failed("First reason")
        cfg.mark_validation_failed("Second reason")

        assert "First reason" in cfg.partial_reason
        assert "Second reason" in cfg.partial_reason
        assert "; " in cfg.partial_reason
