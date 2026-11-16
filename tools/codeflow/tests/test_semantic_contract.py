"""Semantic control-flow contract verification tests.

These tests verify that the shared control-flow contract is implemented
correctly using language-independent graph fixtures.
"""

import pytest
from codeflow.graph import EdgeType
from codeflow.validation import CFGValidator, CompletionStatus
from codeflow.behavioral_verification import BehavioralVerifier
from tests.fixtures_control_flow import ControlFlowGraphFixtures


class TestSemanticControlFlowContract:
    """Test the language-independent semantic control-flow contract."""

    def test_empty_function_valid(self):
        """Test that empty function (entry → exit) is valid."""
        cfg = ControlFlowGraphFixtures.empty_function()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_simple_sequence_valid(self):
        """Test that simple statement sequence is valid."""
        cfg = ControlFlowGraphFixtures.simple_sequence()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

        # Verify path
        verifier = BehavioralVerifier(cfg)
        verifier.assert_path_exists(["entry", "stmt1", "stmt2", "exit"])

    def test_simple_sequence_has_source_locations(self):
        """Test that statements have source locations."""
        cfg = ControlFlowGraphFixtures.simple_sequence()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_node_has_source_location("stmt1")
        verifier.assert_node_has_source_location("stmt2")

    def test_if_else_statement_valid(self):
        """Test that if/else with convergence is valid."""
        cfg = ControlFlowGraphFixtures.if_else_statement()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_if_else_has_both_branches(self):
        """Test that if/else decision has both branches."""
        cfg = ControlFlowGraphFixtures.if_else_statement()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_decision_has_branches("if", ["true", "false"])

    def test_if_else_true_branch(self):
        """Test that if true-branch reaches merge."""
        cfg = ControlFlowGraphFixtures.if_else_statement()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_path_exists(["if", "true_stmt", "merge"])

    def test_if_else_false_branch(self):
        """Test that if false-branch reaches merge."""
        cfg = ControlFlowGraphFixtures.if_else_statement()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_path_exists(["if", "false_stmt", "merge"])

    def test_while_loop_with_break_valid(self):
        """Test that while loop with break is valid."""
        cfg = ControlFlowGraphFixtures.while_loop_with_break()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_while_loop_with_break_break_routes_to_after_loop(self):
        """Test that break routes to after-loop, not exit."""
        cfg = ControlFlowGraphFixtures.while_loop_with_break()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_break_routes_to_target("break", "after_loop")
        verifier.assert_edge_does_not_exist("break", "exit")

    def test_while_loop_with_break_no_break_to_exit(self):
        """Test that validation rejects break to exit."""
        cfg = ControlFlowGraphFixtures.while_loop_with_break()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_no_break_to_exit()

    def test_while_loop_with_continue_valid(self):
        """Test that while loop with continue is valid."""
        cfg = ControlFlowGraphFixtures.while_loop_with_continue()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_while_loop_with_continue_continues_to_loop_entry(self):
        """Test that continue routes to loop entry."""
        cfg = ControlFlowGraphFixtures.while_loop_with_continue()
        verifier = BehavioralVerifier(cfg)

        # Continue is implemented as a loop-back edge back to the loop entry
        verifier.assert_edge_exists("continue", "loop_entry", EdgeType.LOOP_BACK)

    def test_while_loop_with_continue_has_loop_back(self):
        """Test that loop back-edge exists."""
        cfg = ControlFlowGraphFixtures.while_loop_with_continue()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_loop_back_edge_exists("loop_entry")

    def test_early_return_valid(self):
        """Test that early return paths are valid."""
        cfg = ControlFlowGraphFixtures.early_return()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_early_return_true_branch(self):
        """Test that true branch with return connects to exit."""
        cfg = ControlFlowGraphFixtures.early_return()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_return_connects_to_exit("return")

    def test_early_return_both_paths_to_exit(self):
        """Test that both branches converge to exit."""
        cfg = ControlFlowGraphFixtures.early_return()
        verifier = BehavioralVerifier(cfg)

        # True branch: if → return → exit
        verifier.assert_path_exists(["if", "return", "exit"])
        # False branch: if → normal → exit
        verifier.assert_path_exists(["if", "normal", "exit"])

    def test_nested_loops_with_break_valid(self):
        """Test that nested loops with break in inner are valid."""
        cfg = ControlFlowGraphFixtures.nested_loops_with_break_in_inner()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_nested_loops_inner_break_routes_to_after_inner(self):
        """Test that inner break routes to after-inner, not after-outer."""
        cfg = ControlFlowGraphFixtures.nested_loops_with_break_in_inner()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_break_routes_to_target("break", "after_inner")
        verifier.assert_edge_does_not_exist("break", "after_outer")
        verifier.assert_edge_does_not_exist("break", "exit")

    def test_nested_loops_outer_continues_through_after_inner(self):
        """Test that after-inner connects back to outer loop."""
        cfg = ControlFlowGraphFixtures.nested_loops_with_break_in_inner()
        verifier = BehavioralVerifier(cfg)

        # after_inner should loop back to outer_loop, not exit
        verifier.assert_edge_exists("after_inner", "outer_loop")

    def test_match_expression_all_arms_present(self):
        """Test that all match arms are represented."""
        cfg = ControlFlowGraphFixtures.match_expression_three_arms()
        verifier = BehavioralVerifier(cfg)

        # Verify all three arms exist
        verifier.assert_decision_has_branches("match", ["Pattern::A", "Pattern::B", "_"])

    def test_match_expression_all_edges_labeled(self):
        """Test that all decision edges are labeled."""
        cfg = ControlFlowGraphFixtures.match_expression_three_arms()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_all_decision_edges_have_labels()

    def test_match_expression_all_arms_reach_merge(self):
        """Test that all match arms converge to merge."""
        cfg = ControlFlowGraphFixtures.match_expression_three_arms()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_path_exists(["match", "arm1", "merge", "exit"])
        verifier.assert_path_exists(["match", "arm2", "merge", "exit"])
        verifier.assert_path_exists(["match", "arm3", "merge", "exit"])

    def test_exception_propagation_valid(self):
        """Test that exception paths are valid."""
        cfg = ControlFlowGraphFixtures.exception_propagation()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert result.is_valid
        assert result.status == CompletionStatus.COMPLETE

    def test_exception_propagation_has_exception_exit(self):
        """Test that exception path reaches exception exit."""
        cfg = ControlFlowGraphFixtures.exception_propagation()
        verifier = BehavioralVerifier(cfg)

        verifier.assert_edge_exists("call", "exception_exit")

    def test_invalid_break_to_exit_validation_fails(self):
        """Test that break-to-exit is detected as invalid."""
        cfg = ControlFlowGraphFixtures.invalid_break_to_exit()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "break_to_exit" for e in result.errors)

    def test_invalid_generic_labels_validation_fails(self):
        """Test that generic labels are detected as invalid."""
        cfg = ControlFlowGraphFixtures.invalid_generic_labels()
        validator = CFGValidator(cfg)
        result = validator.validate()

        assert not result.is_valid
        assert any(e.error_type == "generic_label" for e in result.errors)

    def test_invalid_generic_labels_no_bare_ast_types(self):
        """Test that AST type names are rejected."""
        cfg = ControlFlowGraphFixtures.invalid_generic_labels()
        verifier = BehavioralVerifier(cfg)

        # This should fail: the CFG contains "let_declaration"
        with pytest.raises(AssertionError):
            verifier.assert_node_label_does_not_contain("let_declaration")

    def test_all_valid_fixtures_are_complete(self):
        """Test that all valid fixtures are marked COMPLETE."""
        valid_cfgs = [
            ControlFlowGraphFixtures.empty_function(),
            ControlFlowGraphFixtures.simple_sequence(),
            ControlFlowGraphFixtures.if_else_statement(),
            ControlFlowGraphFixtures.while_loop_with_break(),
            ControlFlowGraphFixtures.while_loop_with_continue(),
            ControlFlowGraphFixtures.early_return(),
            ControlFlowGraphFixtures.nested_loops_with_break_in_inner(),
            ControlFlowGraphFixtures.match_expression_three_arms(),
            ControlFlowGraphFixtures.exception_propagation(),
        ]

        for cfg in valid_cfgs:
            validator = CFGValidator(cfg)
            result = validator.validate()
            assert result.status == CompletionStatus.COMPLETE, \
                f"CFG {cfg.name} should be COMPLETE but got {result.status}"

    def test_all_invalid_fixtures_are_invalid(self):
        """Test that invalid fixtures are marked INVALID."""
        invalid_cfgs = [
            ControlFlowGraphFixtures.invalid_break_to_exit(),
            ControlFlowGraphFixtures.invalid_generic_labels(),
        ]

        for cfg in invalid_cfgs:
            validator = CFGValidator(cfg)
            result = validator.validate()
            assert result.status == CompletionStatus.INVALID, \
                f"CFG {cfg.name} should be INVALID but got {result.status}"
