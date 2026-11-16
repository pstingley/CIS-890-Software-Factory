"""Python analyzer - builds CFG from Python source code."""

import ast
from typing import Optional, Dict, List
from codeflow.graph import (
    CFG, CFGNode, CFGEdge, NodeType, EdgeType, SourceLocation, AnalysisResult
)
from codeflow.analyzers.base import Analyzer


class LoopContext:
    """Tracks loop nesting context for break/continue routing."""
    def __init__(self, loop_entry_id: str, loop_exit_id: str):
        self.loop_entry_id = loop_entry_id  # Target for continue
        self.loop_exit_id = loop_exit_id    # Target for break


class PythonAnalyzer(Analyzer):
    """Analyzer for Python source files."""

    def analyze(self, source_path: str) -> AnalysisResult:
        """Analyze a Python source file and build CFGs for all functions.

        Args:
            source_path: Path to the Python file to analyze.

        Returns:
            AnalysisResult containing control-flow graphs for all functions.
        """
        with open(source_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code, filename=source_path)
        except SyntaxError as e:
            result = AnalysisResult(file_path=source_path, success=False)
            result.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return result

        builder = PythonCFGBuilder(source_code, source_path)
        result = AnalysisResult(file_path=source_path)

        # Extract all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                cfg = builder.build_cfg_for_function(node)
                result.functions[node.name] = cfg

        result.errors.extend(builder.errors)
        result.warnings.extend(builder.warnings)
        result.success = len(result.errors) == 0

        return result

    @property
    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".py", ".pyw"]

    @property
    def name(self) -> str:
        """Return the analyzer name."""
        return "PythonAnalyzer"

    @property
    def version(self) -> str:
        """Return the analyzer version."""
        return "0.3.0"


class PythonCFGBuilder(ast.NodeVisitor):
    """Builds a CFG from Python AST."""

    def __init__(self, source_code: str, file_path: str):
        self.source_code = source_code
        self.file_path = file_path
        self.source_lines = source_code.split('\n')
        self.node_counter = 0
        self.current_cfg: Optional[CFG] = None
        self.last_statement_node_id: Optional[str] = None
        self.loop_stack: List[LoopContext] = []  # Stack of nested loops
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.exit_node_targets: List[str] = []  # Nodes that return/fall-through to exit
        self.exception_exit_targets: List[str] = []  # Nodes that raise to exception exit

    def _new_node_id(self) -> str:
        """Generate a unique node ID."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        return node_id

    def _get_source_location(self, node: ast.AST) -> SourceLocation:
        """Extract source location from AST node."""
        start_line = node.lineno if hasattr(node, 'lineno') else 0
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line

        source_code = ""
        if 0 < start_line <= len(self.source_lines):
            source_code = self.source_lines[start_line - 1].strip()

        return SourceLocation(
            file=self.file_path,
            start_line=start_line,
            end_line=end_line,
            source_code=source_code
        )

    def _add_node(self, label: str, node_type: NodeType,
                  ast_node: ast.AST, is_exceptional_exit: bool = False,
                  is_internal: bool = False) -> str:
        """Add a node to the current CFG."""
        node_id = self._new_node_id()
        cfg_node = CFGNode(
            id=node_id,
            label=label,
            node_type=node_type,
            source_location=self._get_source_location(ast_node),
            is_exceptional_exit=is_exceptional_exit,
            is_internal=is_internal
        )
        if self.current_cfg:
            self.current_cfg.add_node(cfg_node)
        return node_id

    def _connect_nodes(self, source_id: Optional[str], target_id: str,
                       label: str = "", edge_type: EdgeType = EdgeType.NORMAL) -> None:
        """Add an edge between two nodes. Skip if source is None."""
        if source_id is None or not self.current_cfg:
            return
        self.current_cfg.add_edge(CFGEdge(source_id, target_id, label, edge_type))

    def _extract_source_expr(self, node: ast.AST) -> str:
        """Extract source code for an expression."""
        if hasattr(node, 'lineno') and 0 < node.lineno <= len(self.source_lines):
            line = self.source_lines[node.lineno - 1].strip()
            if len(line) < 100:
                return line
            else:
                return f"expression (line {node.lineno})"
        return "expression"

    def build_cfg_for_function(self, func_def: ast.FunctionDef) -> CFG:
        """Build a CFG for a function definition."""
        cfg = CFG(
            name=func_def.name,
            source_location=self._get_source_location(func_def)
        )

        self.current_cfg = cfg
        self.node_counter = 0
        self.exit_node_targets = []
        self.exception_exit_targets = []
        self.loop_stack = []

        # Entry node
        entry_id = self._add_node("Entry", NodeType.ENTRY, func_def)
        cfg.entry_node_id = entry_id
        self.last_statement_node_id = entry_id

        # Process function body
        for stmt in func_def.body:
            if self.last_statement_node_id:
                self._process_statement(stmt)

        # Collect fall-through paths
        if self.last_statement_node_id:
            self.exit_node_targets.append(self.last_statement_node_id)

        # Exit node
        if self.exit_node_targets:
            normal_exit_id = self._add_node("Exit", NodeType.EXIT, func_def)
            cfg.exit_node_ids.append(normal_exit_id)
            for target_node_id in self.exit_node_targets:
                if target_node_id != normal_exit_id:
                    self._connect_nodes(target_node_id, normal_exit_id)

        # Exception exit
        if self.exception_exit_targets:
            exception_exit_id = self._add_node(
                "Exception Exit", NodeType.EXIT, func_def, is_exceptional_exit=True
            )
            cfg.exception_exit_node_ids.append(exception_exit_id)
            for target_node_id in self.exception_exit_targets:
                if target_node_id != exception_exit_id:
                    self._connect_nodes(target_node_id, exception_exit_id,
                                      edge_type=EdgeType.EXCEPTION)

        self.current_cfg = None
        return cfg

    def _process_statement(self, stmt: ast.AST) -> None:
        """Process a single statement."""
        if isinstance(stmt, ast.If):
            self._process_if(stmt)
        elif isinstance(stmt, ast.For):
            self._process_for(stmt)
        elif isinstance(stmt, ast.While):
            self._process_while(stmt)
        elif isinstance(stmt, ast.Return):
            self._process_return(stmt)
        elif isinstance(stmt, ast.Break):
            self._process_break(stmt)
        elif isinstance(stmt, ast.Continue):
            self._process_continue(stmt)
        elif isinstance(stmt, ast.Try):
            self._process_try(stmt)
        elif isinstance(stmt, ast.Raise):
            self._process_raise(stmt)
        elif isinstance(stmt, ast.Pass):
            pass
        elif isinstance(stmt, ast.Expr):
            self._process_expr(stmt)
        elif isinstance(stmt, ast.Assign):
            self._process_assign(stmt)
        elif isinstance(stmt, ast.AugAssign):
            self._process_augassign(stmt)
        else:
            # Generic statement
            source = self._extract_source_expr(stmt)
            node_id = self._add_node(source, NodeType.STATEMENT, stmt)
            self._connect_nodes(self.last_statement_node_id, node_id)
            self.last_statement_node_id = node_id

    def _process_assign(self, assign: ast.Assign) -> None:
        """Process assignment statement."""
        source = self._extract_source_expr(assign)
        node_id = self._add_node(source, NodeType.STATEMENT, assign)
        self._connect_nodes(self.last_statement_node_id, node_id)
        self.last_statement_node_id = node_id

    def _process_augassign(self, assign: ast.AugAssign) -> None:
        """Process augmented assignment statement."""
        source = self._extract_source_expr(assign)
        node_id = self._add_node(source, NodeType.STATEMENT, assign)
        self._connect_nodes(self.last_statement_node_id, node_id)
        self.last_statement_node_id = node_id

    def _is_docstring(self, expr: ast.Expr) -> bool:
        """Check if an Expr node is a docstring."""
        value = expr.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return True
        return False

    def _process_expr(self, expr_stmt: ast.Expr) -> None:
        """Process expression statement."""
        # Skip docstrings
        if self._is_docstring(expr_stmt):
            return

        expr = expr_stmt.value
        if isinstance(expr, ast.Call):
            source = self._extract_source_expr(expr_stmt)
            node_id = self._add_node(source, NodeType.CALL, expr_stmt)
        else:
            source = self._extract_source_expr(expr_stmt)
            node_id = self._add_node(source, NodeType.STATEMENT, expr_stmt)
        self._connect_nodes(self.last_statement_node_id, node_id)
        self.last_statement_node_id = node_id

    def _process_if(self, if_stmt: ast.If) -> None:
        """Process if statement with proper decision branching."""
        # Create decision node
        test_source = self._extract_source_expr(if_stmt.test)
        decision_id = self._add_node(test_source, NodeType.DECISION, if_stmt)
        self._connect_nodes(self.last_statement_node_id, decision_id)

        # Save starting node counts to track new nodes
        nodes_before = set(self.current_cfg.nodes.keys())

        # Process true branch
        self.last_statement_node_id = decision_id
        for i, stmt in enumerate(if_stmt.body):
            # Track the node ID before processing the statement
            nodes_before_stmt = set(self.current_cfg.nodes.keys())
            self._process_statement(stmt)

            # If this was the first statement, find the edge and label it TRUE
            if i == 0:
                # Find all edges from decision created by this statement
                for edge in self.current_cfg.edges:
                    if edge.source_id == decision_id and edge.edge_type == EdgeType.NORMAL and edge.label == "":
                        # This might be a TRUE edge - check if it goes to a node created for this statement
                        nodes_new = set(self.current_cfg.nodes.keys()) - nodes_before_stmt
                        if edge.target_id in nodes_new or (self.current_cfg.nodes[edge.target_id].node_type == NodeType.STATEMENT and edge.target_id != decision_id):
                            # Relabel this edge
                            self.current_cfg.edges.remove(edge)
                            self.current_cfg.add_edge(CFGEdge(decision_id, edge.target_id, "True", EdgeType.TRUE))
                            break
        true_exit = self.last_statement_node_id

        # Process false branch
        self.last_statement_node_id = decision_id
        if if_stmt.orelse:
            for i, stmt in enumerate(if_stmt.orelse):
                nodes_before_stmt = set(self.current_cfg.nodes.keys())
                self._process_statement(stmt)

                # If this was the first statement, find the edge and label it FALSE
                if i == 0:
                    for edge in self.current_cfg.edges:
                        if edge.source_id == decision_id and edge.edge_type == EdgeType.NORMAL and edge.label == "":
                            nodes_new = set(self.current_cfg.nodes.keys()) - nodes_before_stmt
                            if edge.target_id in nodes_new or (self.current_cfg.nodes[edge.target_id].node_type == NodeType.STATEMENT and edge.target_id != decision_id):
                                self.current_cfg.edges.remove(edge)
                                self.current_cfg.add_edge(CFGEdge(decision_id, edge.target_id, "False", EdgeType.FALSE))
                                break
            false_exit = self.last_statement_node_id
        else:
            false_exit = None

        # Create merge node for convergence - internal node
        merge_id = self._add_node("", NodeType.STATEMENT, if_stmt, is_internal=True)

        # Connect exits to merge
        if true_exit and true_exit != decision_id:
            self._connect_nodes(true_exit, merge_id)
        elif not if_stmt.body:
            # Empty true branch
            self._connect_nodes(decision_id, merge_id, label="True", edge_type=EdgeType.TRUE)

        if false_exit and false_exit != decision_id:
            self._connect_nodes(false_exit, merge_id)
        elif not if_stmt.orelse:
            # No else clause
            self._connect_nodes(decision_id, merge_id, label="False", edge_type=EdgeType.FALSE)

        self.last_statement_node_id = merge_id

    def _process_for(self, for_stmt: ast.For) -> None:
        """Process for loop."""
        # Loop entry (the for statement itself)
        for_source = self._extract_source_expr(for_stmt)
        loop_entry_id = self._add_node(for_source, NodeType.LOOP_ENTRY, for_stmt)
        self._connect_nodes(self.last_statement_node_id, loop_entry_id)

        # Loop exit (after loop) - internal node
        loop_exit_id = self._add_node("", NodeType.STATEMENT, for_stmt, is_internal=True)

        # Push loop context
        self.loop_stack.append(LoopContext(loop_entry_id, loop_exit_id))

        # Process loop body
        saved_last = self.last_statement_node_id
        self.last_statement_node_id = loop_entry_id

        for stmt in for_stmt.body:
            self._process_statement(stmt)

        # Loop back edge
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, loop_entry_id, edge_type=EdgeType.LOOP_BACK)

        # Pop loop context
        self.loop_stack.pop()

        # Connect loop exit
        self._connect_nodes(loop_entry_id, loop_exit_id, label="exit", edge_type=EdgeType.NORMAL)
        self.last_statement_node_id = loop_exit_id

    def _process_while(self, while_stmt: ast.While) -> None:
        """Process while loop."""
        # Check if this is while True (unconditional loop)
        is_unconditional = False
        if isinstance(while_stmt.test, ast.Constant):
            # ast.Constant covers all constant values including True, False, strings, numbers
            # Distinguish True from integer 1 using 'is True' (identity check)
            is_unconditional = while_stmt.test.value is True

        # Loop entry (condition)
        condition_source = self._extract_source_expr(while_stmt.test)
        loop_entry_id = self._add_node(condition_source, NodeType.LOOP_ENTRY, while_stmt)
        self._connect_nodes(self.last_statement_node_id, loop_entry_id)

        # For unconditional loops, don't create a default exit - only break/return/exceptions exit
        # For conditional loops, create an exit node for the False path
        if is_unconditional:
            # Create a placeholder exit that break/return will connect to
            # but don't connect the False edge of the loop entry
            loop_exit_id = self._add_node("", NodeType.STATEMENT, while_stmt, is_internal=True)
        else:
            loop_exit_id = self._add_node("", NodeType.STATEMENT, while_stmt, is_internal=True)
            self._connect_nodes(loop_entry_id, loop_exit_id, label="False", edge_type=EdgeType.FALSE)

        # Push loop context
        self.loop_stack.append(LoopContext(loop_entry_id, loop_exit_id))

        # Process loop body
        self.last_statement_node_id = loop_entry_id

        # Connect loop entry to first body statement with TRUE label (unless unconditional)
        body_start_node = self.last_statement_node_id
        for i, stmt in enumerate(while_stmt.body):
            self._process_statement(stmt)

        # Loop back edge
        if self.last_statement_node_id and self.last_statement_node_id != body_start_node:
            self._connect_nodes(self.last_statement_node_id, loop_entry_id, edge_type=EdgeType.LOOP_BACK)

        # Pop loop context
        self.loop_stack.pop()

        # Update last node to loop exit
        self.last_statement_node_id = loop_exit_id

    def _process_return(self, return_stmt: ast.Return) -> None:
        """Process return statement."""
        return_source = self._extract_source_expr(return_stmt)
        node_id = self._add_node(return_source, NodeType.STATEMENT, return_stmt)
        self._connect_nodes(self.last_statement_node_id, node_id)
        self.exit_node_targets.append(node_id)
        self.last_statement_node_id = None

    def _process_break(self, break_stmt: ast.Break) -> None:
        """Process break statement."""
        node_id = self._add_node("break", NodeType.STATEMENT, break_stmt)
        self._connect_nodes(self.last_statement_node_id, node_id, label="break", edge_type=EdgeType.BREAK)

        # Route to loop exit
        if self.loop_stack:
            loop_ctx = self.loop_stack[-1]
            self._connect_nodes(node_id, loop_ctx.loop_exit_id, edge_type=EdgeType.BREAK)

        self.last_statement_node_id = None

    def _process_continue(self, continue_stmt: ast.Continue) -> None:
        """Process continue statement."""
        node_id = self._add_node("continue", NodeType.STATEMENT, continue_stmt)
        self._connect_nodes(self.last_statement_node_id, node_id, label="continue", edge_type=EdgeType.CONTINUE)

        # Route to loop entry via LOOP_BACK
        if self.loop_stack:
            loop_ctx = self.loop_stack[-1]
            self._connect_nodes(node_id, loop_ctx.loop_entry_id, edge_type=EdgeType.LOOP_BACK)

        self.last_statement_node_id = None

    def _process_try(self, try_stmt: ast.Try) -> None:
        """Process try/except/finally statement.

        Creates exception edges from try block entry to each handler, representing
        potential exception paths. Try/except blocks themselves are marked internal
        to avoid cluttering the visual output.
        """
        # Save entry point
        try_entry = self.last_statement_node_id

        # Create try entry node (internal)
        try_node_id = self._add_node("try:", NodeType.STATEMENT, try_stmt, is_internal=True)
        self._connect_nodes(try_entry, try_node_id)

        # Process try body
        self.last_statement_node_id = try_node_id
        for stmt in try_stmt.body:
            self._process_statement(stmt)
        try_body_exit = self.last_statement_node_id

        # Build handlers
        handler_exits = []

        for handler in try_stmt.handlers:
            # Create handler node (internal)
            if handler.type is None:
                exc_label = "Exception"
            elif isinstance(handler.type, ast.Name):
                exc_label = handler.type.id
            elif isinstance(handler.type, ast.Tuple):
                exc_label = "(" + ", ".join(
                    exc.id if isinstance(exc, ast.Name) else str(exc)
                    for exc in handler.type.elts
                ) + ")"
            else:
                exc_label = "Exception"

            handler_node_id = self._add_node(
                f"except {exc_label}:",
                NodeType.STATEMENT,
                handler,
                is_internal=True
            )
            # Create exception edge from try entry to handler
            self._connect_nodes(try_entry, handler_node_id, edge_type=EdgeType.EXCEPTION)

            # Process handler body
            self.last_statement_node_id = handler_node_id
            for stmt in handler.body:
                self._process_statement(stmt)
            handler_exits.append(self.last_statement_node_id)

        # Process finally block if present
        if try_stmt.finalbody:
            finally_node_id = self._add_node("finally:", NodeType.STATEMENT, try_stmt, is_internal=True)

            # Connect try body to finally
            if try_body_exit:
                self._connect_nodes(try_body_exit, finally_node_id)

            # Connect all handlers to finally
            for handler_exit in handler_exits:
                if handler_exit:
                    self._connect_nodes(handler_exit, finally_node_id)

            # Process finally body
            self.last_statement_node_id = finally_node_id
            for stmt in try_stmt.finalbody:
                self._process_statement(stmt)
            self.last_statement_node_id = self.last_statement_node_id
        else:
            # Merge try body and handler exits
            if handler_exits:
                merge_id = self._add_node("", NodeType.STATEMENT, try_stmt, is_internal=True)

                if try_body_exit:
                    self._connect_nodes(try_body_exit, merge_id)

                for handler_exit in handler_exits:
                    if handler_exit:
                        self._connect_nodes(handler_exit, merge_id)

                self.last_statement_node_id = merge_id
            else:
                self.last_statement_node_id = try_body_exit

    def _process_raise(self, raise_stmt: ast.Raise) -> None:
        """Process raise statement."""
        if raise_stmt.exc:
            raise_source = self._extract_source_expr(raise_stmt)
        else:
            raise_source = "raise (re-raise)"

        node_id = self._add_node(raise_source, NodeType.STATEMENT, raise_stmt)
        self._connect_nodes(self.last_statement_node_id, node_id, edge_type=EdgeType.EXCEPTION)
        self.exception_exit_targets.append(node_id)
        self.last_statement_node_id = None


def analyze_python_file(file_path: str) -> AnalysisResult:
    """Analyze a Python source file and build CFGs for all functions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        result = AnalysisResult(file_path=file_path, success=False)
        result.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return result

    builder = PythonCFGBuilder(source_code, file_path)
    result = AnalysisResult(file_path=file_path)

    # Extract all function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            cfg = builder.build_cfg_for_function(node)
            result.functions[node.name] = cfg

    result.errors.extend(builder.errors)
    result.warnings.extend(builder.warnings)
    result.success = len(result.errors) == 0

    return result
