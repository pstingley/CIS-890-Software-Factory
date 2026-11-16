"""Python analyzer - builds CFG from Python source code."""

import ast
import inspect
from typing import Optional, Dict, List, Tuple
from codeflow.graph import (
    CFG, CFGNode, CFGEdge, NodeType, EdgeType, SourceLocation, AnalysisResult
)
from codeflow.analyzers.base import Analyzer

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
        return "0.2.0"

class PythonCFGBuilder(ast.NodeVisitor):
    """Builds a CFG from Python AST."""

    def __init__(self, source_code: str, file_path: str):
        self.source_code = source_code
        self.file_path = file_path
        self.source_lines = source_code.split('\n')
        self.node_counter = 0
        self.current_cfg: Optional[CFG] = None
        self.current_entry_node_id: Optional[str] = None
        self.last_statement_node_id: Optional[str] = None
        self.break_target_node_id: Optional[str] = None
        self.continue_target_node_id: Optional[str] = None
        self.loop_exit_node_id: Optional[str] = None
        self.function_cfgs: Dict[str, CFG] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        # Track nodes that should connect to exit
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
                  ast_node: ast.AST, is_exceptional_exit: bool = False) -> str:
        """Add a node to the current CFG."""
        node_id = self._new_node_id()
        cfg_node = CFGNode(
            id=node_id,
            label=label,
            node_type=node_type,
            source_location=self._get_source_location(ast_node),
            is_exceptional_exit=is_exceptional_exit
        )
        if self.current_cfg:
            self.current_cfg.add_node(cfg_node)
        return node_id

    def _connect_nodes(self, source_id: str, target_id: str,
                       label: str = "", edge_type: EdgeType = EdgeType.NORMAL) -> None:
        """Add an edge between two nodes."""
        if self.current_cfg:
            self.current_cfg.add_edge(CFGEdge(source_id, target_id, label, edge_type))

    def _extract_source_expr(self, node: ast.AST) -> str:
        """Extract source code for an expression."""
        if hasattr(node, 'lineno') and node.lineno > 0 and node.lineno <= len(self.source_lines):
            line = self.source_lines[node.lineno - 1].strip()
            # For simple cases, return the line; for complex, return a descriptive label
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

        # Entry node
        entry_id = self._add_node("Entry", NodeType.ENTRY, func_def)
        cfg.entry_node_id = entry_id
        self.last_statement_node_id = entry_id

        # Process function body
        for stmt in func_def.body:
            if self.last_statement_node_id:  # Only process if we haven't hit return/break
                self._process_statement(stmt)

        # Collect fall-through paths (last_statement_node_id != None after body)
        if self.last_statement_node_id:
            self.exit_node_targets.append(self.last_statement_node_id)

        # Exit node - only create if there are incoming edges
        normal_exit_id = None
        if self.exit_node_targets:
            normal_exit_id = self._add_node("Exit", NodeType.EXIT, func_def)
            cfg.exit_node_ids.append(normal_exit_id)
            for target_node_id in self.exit_node_targets:
                if target_node_id != normal_exit_id:
                    self._connect_nodes(target_node_id, normal_exit_id)

        # Exception exit - only create if there are incoming edges
        exception_exit_id = None
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
        elif isinstance(stmt, ast.Expr):
            self._process_expr(stmt)
        elif isinstance(stmt, ast.Assign):
            self._process_assign(stmt)
        elif isinstance(stmt, ast.AugAssign):
            self._process_augassign(stmt)
        elif isinstance(stmt, (ast.Pass, ast.Continue)):
            pass  # No node needed
        else:
            # Generic statement
            source = self._extract_source_expr(stmt)
            node_id = self._add_node(source, NodeType.STATEMENT, stmt)
            if self.last_statement_node_id:
                self._connect_nodes(self.last_statement_node_id, node_id)
            self.last_statement_node_id = node_id

    def _process_assign(self, assign: ast.Assign) -> None:
        """Process assignment statement."""
        source = self._extract_source_expr(assign)
        node_id = self._add_node(source, NodeType.STATEMENT, assign)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id)
        self.last_statement_node_id = node_id

    def _process_augassign(self, assign: ast.AugAssign) -> None:
        """Process augmented assignment statement."""
        source = self._extract_source_expr(assign)
        node_id = self._add_node(source, NodeType.STATEMENT, assign)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id)
        self.last_statement_node_id = node_id

    def _process_expr(self, expr_stmt: ast.Expr) -> None:
        """Process expression statement (usually a call)."""
        expr = expr_stmt.value
        if isinstance(expr, ast.Call):
            self._process_call(expr_stmt)
        else:
            source = self._extract_source_expr(expr_stmt)
            node_id = self._add_node(source, NodeType.STATEMENT, expr_stmt)
            if self.last_statement_node_id:
                self._connect_nodes(self.last_statement_node_id, node_id)
            self.last_statement_node_id = node_id

    def _process_call(self, call_stmt: ast.Expr) -> None:
        """Process function call."""
        call = call_stmt.value
        source = self._extract_source_expr(call_stmt)
        node_id = self._add_node(source, NodeType.CALL, call_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id)
        self.last_statement_node_id = node_id

    def _process_if(self, if_stmt: ast.If) -> None:
        """Process if statement."""
        # Decision node
        test_source = self._extract_source_expr(if_stmt.test)
        decision_id = self._add_node(test_source, NodeType.DECISION, if_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, decision_id)

        # True branch
        true_entry = decision_id
        saved_last = self.last_statement_node_id
        self.last_statement_node_id = true_entry
        for stmt in if_stmt.body:
            self._process_statement(stmt)
        true_exit = self.last_statement_node_id

        # False branch (else or orelse)
        self.last_statement_node_id = saved_last
        if if_stmt.orelse:
            for stmt in if_stmt.orelse:
                self._process_statement(stmt)
            false_exit = self.last_statement_node_id
        else:
            false_exit = decision_id

        # Merge branches
        merge_id = self._new_node_id()
        self.current_cfg.nodes[merge_id] = CFGNode(
            id=merge_id,
            label="Merge",
            node_type=NodeType.STATEMENT,
            source_location=self._get_source_location(if_stmt)
        )

        # Connect true branch to merge
        if true_exit != decision_id:
            self._connect_nodes(true_exit, merge_id, label="", edge_type=EdgeType.NORMAL)
        else:
            self._connect_nodes(decision_id, merge_id, label="True", edge_type=EdgeType.TRUE)

        # Connect false branch to merge
        if false_exit != decision_id:
            self._connect_nodes(false_exit, merge_id, label="", edge_type=EdgeType.NORMAL)
        else:
            self._connect_nodes(decision_id, merge_id, label="False", edge_type=EdgeType.FALSE)

        self.last_statement_node_id = merge_id

    def _process_for(self, for_stmt: ast.For) -> None:
        """Process for loop."""
        # Loop entry
        for_source = self._extract_source_expr(for_stmt)
        loop_entry_id = self._add_node(f"for ... in ...", NodeType.LOOP_ENTRY, for_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, loop_entry_id)

        # Loop body
        loop_body_id = self._add_node("Loop body", NodeType.LOOP_BODY, for_stmt)
        self._connect_nodes(loop_entry_id, loop_body_id, label="iterate", edge_type=EdgeType.NORMAL)

        # Save loop context
        saved_last = self.last_statement_node_id
        saved_break = self.break_target_node_id
        saved_continue = self.continue_target_node_id

        self.last_statement_node_id = loop_body_id
        self.break_target_node_id = None
        self.continue_target_node_id = loop_entry_id

        # Process loop body statements
        for stmt in for_stmt.body:
            self._process_statement(stmt)

        # Loop back edge
        loop_back_id = self.last_statement_node_id
        if loop_back_id and loop_back_id != loop_entry_id:
            self._connect_nodes(loop_back_id, loop_entry_id, label="", edge_type=EdgeType.LOOP_BACK)

        # Loop exit
        loop_exit_id = self._add_node("Loop exit", NodeType.STATEMENT, for_stmt)
        self._connect_nodes(loop_entry_id, loop_exit_id, label="exit", edge_type=EdgeType.NORMAL)

        # Restore loop context
        self.last_statement_node_id = loop_exit_id
        self.break_target_node_id = saved_break
        self.continue_target_node_id = saved_continue

    def _process_while(self, while_stmt: ast.While) -> None:
        """Process while loop."""
        # Loop entry (condition)
        condition_source = self._extract_source_expr(while_stmt.test)
        loop_entry_id = self._add_node(condition_source, NodeType.LOOP_ENTRY, while_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, loop_entry_id)

        # Loop body
        loop_body_id = self._add_node("Loop body", NodeType.LOOP_BODY, while_stmt)
        self._connect_nodes(loop_entry_id, loop_body_id, label="True", edge_type=EdgeType.TRUE)

        # Save loop context
        saved_last = self.last_statement_node_id
        saved_break = self.break_target_node_id
        saved_continue = self.continue_target_node_id

        self.last_statement_node_id = loop_body_id
        self.break_target_node_id = None
        self.continue_target_node_id = loop_entry_id

        # Process loop body statements
        for stmt in while_stmt.body:
            self._process_statement(stmt)

        # Loop back edge
        loop_back_id = self.last_statement_node_id
        if loop_back_id and loop_back_id != loop_entry_id:
            self._connect_nodes(loop_back_id, loop_entry_id, label="", edge_type=EdgeType.LOOP_BACK)

        # Loop exit
        loop_exit_id = self._add_node("Loop exit", NodeType.STATEMENT, while_stmt)
        self._connect_nodes(loop_entry_id, loop_exit_id, label="False", edge_type=EdgeType.FALSE)

        # Restore loop context
        self.last_statement_node_id = loop_exit_id
        self.break_target_node_id = saved_break
        self.continue_target_node_id = saved_continue

    def _process_return(self, return_stmt: ast.Return) -> None:
        """Process return statement."""
        return_source = self._extract_source_expr(return_stmt)
        node_id = self._add_node(return_source, NodeType.STATEMENT, return_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id)
        # Track this return node to connect to exit later
        self.exit_node_targets.append(node_id)
        self.last_statement_node_id = None  # Return ends current path

    def _process_break(self, break_stmt: ast.Break) -> None:
        """Process break statement."""
        node_id = self._add_node("break", NodeType.STATEMENT, break_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id,
                               label="break", edge_type=EdgeType.BREAK)
        self.last_statement_node_id = None  # Don't continue after break

    def _process_continue(self, continue_stmt: ast.Continue) -> None:
        """Process continue statement."""
        node_id = self._add_node("continue", NodeType.STATEMENT, continue_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id,
                               label="continue", edge_type=EdgeType.CONTINUE)
        self.last_statement_node_id = None

    def _process_try(self, try_stmt: ast.Try) -> None:
        """Process try/except/finally statement."""
        # Try block entry
        try_id = self._add_node("try:", NodeType.STATEMENT, try_stmt)
        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, try_id)

        # Process try body
        saved_last = self.last_statement_node_id
        self.last_statement_node_id = try_id
        for stmt in try_stmt.body:
            self._process_statement(stmt)
        try_exit = self.last_statement_node_id

        # Process except handlers
        except_exits = []
        for handler in try_stmt.handlers:
            self.last_statement_node_id = saved_last
            handler_label = f"except {handler.type.id if hasattr(handler.type, 'id') else 'Exception'}:"
            handler_id = self._add_node(handler_label, NodeType.STATEMENT, handler)
            if saved_last:
                self._connect_nodes(saved_last, handler_id,
                                   label="exception", edge_type=EdgeType.EXCEPTION)

            for stmt in handler.body:
                self._process_statement(stmt)
            except_exits.append(self.last_statement_node_id)

        # Process finally block
        if try_stmt.finalbody:
            finally_id = self._add_node("finally:", NodeType.STATEMENT, try_stmt)
            if try_exit and try_exit != try_id:
                self._connect_nodes(try_exit, finally_id)
            for except_exit in except_exits:
                if except_exit and except_exit != saved_last:
                    self._connect_nodes(except_exit, finally_id)

            saved_last = self.last_statement_node_id
            self.last_statement_node_id = finally_id
            for stmt in try_stmt.finalbody:
                self._process_statement(stmt)
            self.last_statement_node_id = self.last_statement_node_id or finally_id

    def _process_raise(self, raise_stmt: ast.Raise) -> None:
        """Process raise statement."""
        if raise_stmt.exc:
            raise_source = self._extract_source_expr(raise_stmt)
            node_id = self._add_node(raise_source, NodeType.STATEMENT, raise_stmt)
        else:
            # Bare raise (re-raise in exception handler)
            node_id = self._add_node("raise (re-raise)", NodeType.STATEMENT, raise_stmt)

        if self.last_statement_node_id:
            self._connect_nodes(self.last_statement_node_id, node_id,
                               label="raise", edge_type=EdgeType.EXCEPTION)

        # Track this raise node to connect to exception exit later
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
