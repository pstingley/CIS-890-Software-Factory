"""Language-independent control-flow graph fixtures for behavioral testing."""

from codeflow.graph import (
    CFG, CFGNode, CFGEdge, NodeType, EdgeType, SourceLocation
)


class ControlFlowGraphFixtures:
    """Factory for creating test CFGs representing common control-flow patterns."""

    @staticmethod
    def empty_function() -> CFG:
        """Create a CFG for an empty function (entry → exit only)."""
        cfg = CFG("empty_function")
        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(exit_node)
        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "exit")
        return cfg

    @staticmethod
    def simple_sequence() -> CFG:
        """Create a CFG for a simple sequence: entry → stmt1 → stmt2 → exit."""
        cfg = CFG("simple_sequence")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        stmt1 = CFGNode("stmt1", "x = 1", NodeType.STATEMENT,
                       SourceLocation("test.py", 1, 1, "x = 1"))
        stmt2 = CFGNode("stmt2", "y = 2", NodeType.STATEMENT,
                       SourceLocation("test.py", 2, 2, "y = 2"))
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(stmt1)
        cfg.add_node(stmt2)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "stmt1")
        cfg.add_edge_simple("stmt1", "stmt2")
        cfg.add_edge_simple("stmt2", "exit")

        return cfg

    @staticmethod
    def if_else_statement() -> CFG:
        """Create a CFG for if/else with convergence.

        entry → decision → [true] stmt1 → merge → exit
                        → [false] stmt2 →
        """
        cfg = CFG("if_else_statement")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        decision = CFGNode("if", "if x > 0", NodeType.DECISION,
                          SourceLocation("test.py", 1, 1, "if x > 0"))
        true_stmt = CFGNode("true_stmt", "y = 1", NodeType.STATEMENT,
                           SourceLocation("test.py", 2, 2, "y = 1"))
        false_stmt = CFGNode("false_stmt", "y = 2", NodeType.STATEMENT,
                            SourceLocation("test.py", 4, 4, "y = 2"))
        merge = CFGNode("merge", "merge", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(decision)
        cfg.add_node(true_stmt)
        cfg.add_node(false_stmt)
        cfg.add_node(merge)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "if")
        cfg.add_edge(CFGEdge("if", "true_stmt", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("if", "false_stmt", "false", EdgeType.FALSE))
        cfg.add_edge_simple("true_stmt", "merge")
        cfg.add_edge_simple("false_stmt", "merge")
        cfg.add_edge_simple("merge", "exit")

        return cfg

    @staticmethod
    def while_loop_with_break() -> CFG:
        """Create a CFG for a while loop with break.

        entry → loop_entry → decision → [true] body → break → after_loop → exit
                                     → [false] after_loop
        """
        cfg = CFG("while_loop_with_break")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        loop_entry = CFGNode("loop_entry", "while x > 0", NodeType.LOOP_ENTRY,
                            SourceLocation("test.py", 1, 1, "while x > 0"))
        decision = CFGNode("decision", "x > 0", NodeType.DECISION)
        body = CFGNode("body", "y = y + 1", NodeType.STATEMENT,
                      SourceLocation("test.py", 2, 2, "y = y + 1"))
        break_stmt = CFGNode("break", "break", NodeType.STATEMENT,
                            SourceLocation("test.py", 3, 3, "break"))
        after_loop = CFGNode("after_loop", "after_loop", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(loop_entry)
        cfg.add_node(decision)
        cfg.add_node(body)
        cfg.add_node(break_stmt)
        cfg.add_node(after_loop)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "loop_entry")
        cfg.add_edge_simple("loop_entry", "decision")
        cfg.add_edge(CFGEdge("decision", "body", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("decision", "after_loop", "false", EdgeType.FALSE))
        cfg.add_edge_simple("body", "break")
        cfg.add_edge(CFGEdge("break", "after_loop", "", EdgeType.BREAK))
        cfg.add_edge_simple("after_loop", "exit")

        return cfg

    @staticmethod
    def while_loop_with_continue() -> CFG:
        """Create a CFG for a while loop with continue.

        entry → loop_entry → decision → [true] body → continue → loop_entry
                                     → [false] after_loop → exit
        """
        cfg = CFG("while_loop_with_continue")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        loop_entry = CFGNode("loop_entry", "while x > 0", NodeType.LOOP_ENTRY,
                            SourceLocation("test.py", 1, 1, "while x > 0"))
        decision = CFGNode("decision", "x > 0", NodeType.DECISION)
        body = CFGNode("body", "y = y + 1", NodeType.STATEMENT,
                      SourceLocation("test.py", 2, 2, "y = y + 1"))
        continue_stmt = CFGNode("continue", "continue", NodeType.STATEMENT,
                               SourceLocation("test.py", 3, 3, "continue"))
        after_loop = CFGNode("after_loop", "after_loop", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(loop_entry)
        cfg.add_node(decision)
        cfg.add_node(body)
        cfg.add_node(continue_stmt)
        cfg.add_node(after_loop)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "loop_entry")
        cfg.add_edge_simple("loop_entry", "decision")
        cfg.add_edge(CFGEdge("decision", "body", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("decision", "after_loop", "false", EdgeType.FALSE))
        cfg.add_edge_simple("body", "continue")
        cfg.add_edge(CFGEdge("continue", "loop_entry", "", EdgeType.LOOP_BACK))
        cfg.add_edge_simple("after_loop", "exit")

        return cfg

    @staticmethod
    def early_return() -> CFG:
        """Create a CFG for early return.

        entry → decision → [true] return_stmt → exit
                       → [false] normal_stmt → exit
        """
        cfg = CFG("early_return")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        decision = CFGNode("if", "if error", NodeType.DECISION,
                          SourceLocation("test.py", 1, 1, "if error"))
        return_stmt = CFGNode("return", "return None", NodeType.STATEMENT,
                             SourceLocation("test.py", 2, 2, "return None"))
        normal_stmt = CFGNode("normal", "y = do_work()", NodeType.STATEMENT,
                             SourceLocation("test.py", 4, 4, "y = do_work()"))
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(decision)
        cfg.add_node(return_stmt)
        cfg.add_node(normal_stmt)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "if")
        cfg.add_edge(CFGEdge("if", "return", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("if", "normal", "false", EdgeType.FALSE))
        cfg.add_edge_simple("return", "exit")
        cfg.add_edge_simple("normal", "exit")

        return cfg

    @staticmethod
    def nested_loops_with_break_in_inner() -> CFG:
        """Create a CFG for nested loops with break in inner loop.

        entry → outer_loop → outer_cond → [true] inner_loop → inner_cond
                                       → [false] after_outer → exit

        inner_cond → [true] inner_body → break → after_inner → outer_loop
                  → [false] after_inner
        """
        cfg = CFG("nested_loops_with_break_in_inner")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        outer_loop = CFGNode("outer_loop", "for x in items", NodeType.LOOP_ENTRY,
                            SourceLocation("test.py", 1, 1, "for x in items"))
        outer_cond = CFGNode("outer_cond", "has_next_x", NodeType.DECISION)
        inner_loop = CFGNode("inner_loop", "while y > 0", NodeType.LOOP_ENTRY,
                            SourceLocation("test.py", 2, 2, "while y > 0"))
        inner_cond = CFGNode("inner_cond", "y > 0", NodeType.DECISION)
        inner_body = CFGNode("inner_body", "z = z + 1", NodeType.STATEMENT,
                            SourceLocation("test.py", 3, 3, "z = z + 1"))
        break_stmt = CFGNode("break", "break", NodeType.STATEMENT,
                            SourceLocation("test.py", 4, 4, "break"))
        after_inner = CFGNode("after_inner", "after_inner", NodeType.STATEMENT)
        after_outer = CFGNode("after_outer", "after_outer", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(outer_loop)
        cfg.add_node(outer_cond)
        cfg.add_node(inner_loop)
        cfg.add_node(inner_cond)
        cfg.add_node(inner_body)
        cfg.add_node(break_stmt)
        cfg.add_node(after_inner)
        cfg.add_node(after_outer)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "outer_loop")
        cfg.add_edge_simple("outer_loop", "outer_cond")
        cfg.add_edge(CFGEdge("outer_cond", "inner_loop", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("outer_cond", "after_outer", "false", EdgeType.FALSE))
        cfg.add_edge_simple("inner_loop", "inner_cond")
        cfg.add_edge(CFGEdge("inner_cond", "inner_body", "true", EdgeType.TRUE))
        cfg.add_edge(CFGEdge("inner_cond", "after_inner", "false", EdgeType.FALSE))
        cfg.add_edge_simple("inner_body", "break")
        cfg.add_edge(CFGEdge("break", "after_inner", "", EdgeType.BREAK))
        cfg.add_edge(CFGEdge("after_inner", "outer_loop", "", EdgeType.LOOP_BACK))
        cfg.add_edge_simple("after_outer", "exit")

        return cfg

    @staticmethod
    def match_expression_three_arms() -> CFG:
        """Create a CFG for match/switch with three arms.

        entry → decision → [arm1] arm1_body → merge → exit
                        → [arm2] arm2_body →
                        → [arm3] arm3_body →
        """
        cfg = CFG("match_expression_three_arms")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        decision = CFGNode("match", "match value", NodeType.DECISION,
                          SourceLocation("test.py", 1, 1, "match value"))
        arm1_body = CFGNode("arm1", "result = 1", NodeType.STATEMENT,
                           SourceLocation("test.py", 2, 2, "result = 1"))
        arm2_body = CFGNode("arm2", "result = 2", NodeType.STATEMENT,
                           SourceLocation("test.py", 4, 4, "result = 2"))
        arm3_body = CFGNode("arm3", "result = 3", NodeType.STATEMENT,
                           SourceLocation("test.py", 6, 6, "result = 3"))
        merge = CFGNode("merge", "merge", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(decision)
        cfg.add_node(arm1_body)
        cfg.add_node(arm2_body)
        cfg.add_node(arm3_body)
        cfg.add_node(merge)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "match")
        cfg.add_edge(CFGEdge("match", "arm1", "Pattern::A", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("match", "arm2", "Pattern::B", EdgeType.NORMAL))
        cfg.add_edge(CFGEdge("match", "arm3", "_", EdgeType.NORMAL))
        cfg.add_edge_simple("arm1", "merge")
        cfg.add_edge_simple("arm2", "merge")
        cfg.add_edge_simple("arm3", "merge")
        cfg.add_edge_simple("merge", "exit")

        return cfg

    @staticmethod
    def exception_propagation() -> CFG:
        """Create a CFG with exception path.

        entry → risky_call → [success] normal_exit
                          → [exception] exception_exit
        """
        cfg = CFG("exception_propagation")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        risky_call = CFGNode("call", "file = open(path)?", NodeType.STATEMENT,
                            SourceLocation("test.rs", 1, 1, "file = open(path)?"))
        normal_exit = CFGNode("normal_exit", "exit", NodeType.EXIT)
        exception_exit = CFGNode("exception_exit", "exception_exit", NodeType.EXIT,
                                is_exceptional_exit=True)

        cfg.add_node(entry)
        cfg.add_node(risky_call)
        cfg.add_node(normal_exit)
        cfg.add_node(exception_exit)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["normal_exit"]
        cfg.exception_exit_node_ids = ["exception_exit"]

        cfg.add_edge_simple("entry", "call")
        cfg.add_edge_simple("call", "normal_exit")
        cfg.add_edge(CFGEdge("call", "exception_exit", "", EdgeType.EXCEPTION))

        return cfg

    @staticmethod
    def invalid_break_to_exit() -> CFG:
        """Create an INVALID CFG where break incorrectly targets exit."""
        cfg = CFG("invalid_break_to_exit")

        entry = CFGNode("entry", "entry", NodeType.ENTRY)
        loop_entry = CFGNode("loop_entry", "while x", NodeType.LOOP_ENTRY)
        break_stmt = CFGNode("break", "break", NodeType.STATEMENT)
        exit_node = CFGNode("exit", "exit", NodeType.EXIT)

        cfg.add_node(entry)
        cfg.add_node(loop_entry)
        cfg.add_node(break_stmt)
        cfg.add_node(exit_node)

        cfg.entry_node_id = "entry"
        cfg.exit_node_ids = ["exit"]

        cfg.add_edge_simple("entry", "loop_entry")
        cfg.add_edge_simple("loop_entry", "break")
        # INVALID: break should not target exit
        cfg.add_edge(CFGEdge("break", "exit", "", EdgeType.BREAK))

        return cfg

    @staticmethod
    def invalid_generic_labels() -> CFG:
        """Create an INVALID CFG with generic AST node labels."""
        cfg = CFG("invalid_generic_labels")

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

        return cfg
