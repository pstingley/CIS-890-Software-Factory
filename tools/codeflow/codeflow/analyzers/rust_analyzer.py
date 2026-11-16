"""Rust analyzer - builds CFG from Rust source code using Tree-sitter."""

import sys
from typing import Optional, Dict, List, Tuple, Set, Any
from tree_sitter import Parser, Language
import tree_sitter_rust
from codeflow.graph import (
    CFG, CFGNode, CFGEdge, NodeType, EdgeType, SourceLocation, AnalysisResult
)
from codeflow.analyzers.base import Analyzer


class RustAnalyzer(Analyzer):
    """Analyzer for Rust source files using Tree-sitter."""

    def __init__(self):
        """Initialize the Rust analyzer with Tree-sitter."""
        try:
            self.rust_language = Language(tree_sitter_rust.language(), "rust")
            self.parser = Parser()
            self.parser.set_language(self.rust_language)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Rust parser: {e}")

    def analyze(self, source_path: str) -> AnalysisResult:
        """Analyze a Rust source file and build CFGs for all functions.

        Args:
            source_path: Path to the Rust file to analyze.

        Returns:
            AnalysisResult containing control-flow graphs for all functions.
        """
        with open(source_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        try:
            tree = self.parser.parse(source_code.encode('utf-8'))
        except Exception as e:
            result = AnalysisResult(file_path=source_path, success=False)
            result.errors.append(f"Parser error: {e}")
            return result

        builder = RustCFGBuilder(source_code, source_path, self.rust_language)
        result = AnalysisResult(file_path=source_path)

        # Extract all function definitions
        try:
            self._extract_functions(tree.root_node, builder, result)
        except Exception as e:
            result.errors.append(f"Analysis error: {e}")
            result.success = False

        result.errors.extend(builder.errors)
        result.warnings.extend(builder.warnings)
        result.ambiguity_flags.extend(builder.ambiguity_flags)
        result.analysis_incomplete = builder.analysis_incomplete
        result.success = len(result.errors) == 0 and not builder.analysis_incomplete

        return result

    def _extract_functions(self, node: Any, builder: 'RustCFGBuilder', result: AnalysisResult) -> None:
        """Recursively extract function definitions from the syntax tree."""
        if node.type == "function_item":
            # Build CFG for this function
            cfg = builder.build_cfg_for_function(node)
            func_name = self._get_function_name(node)
            if func_name:
                result.functions[func_name] = cfg

        # Recurse into children
        for child in node.children:
            self._extract_functions(child, builder, result)

    def _get_function_name(self, func_node: Any) -> Optional[str]:
        """Extract function name from a function_item node."""
        for child in func_node.children:
            if child.type == "identifier":
                return child.text.decode('utf-8')
        return None

    @property
    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".rs"]

    @property
    def name(self) -> str:
        """Return the analyzer name."""
        return "RustAnalyzer"

    @property
    def version(self) -> str:
        """Return the analyzer version."""
        return "0.3.0"


class RustCFGBuilder:
    """Builds a CFG from Rust source code using Tree-sitter AST."""

    def __init__(self, source_code: str, file_path: str, language: Language):
        self.source_code = source_code
        self.file_path = file_path
        self.language = language
        self.source_lines = source_code.split('\n')
        self.node_counter = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.ambiguity_flags: List[str] = []
        self.analysis_incomplete = False

    def _new_node_id(self) -> str:
        """Generate a unique node ID."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        return node_id

    def _get_source_location(self, node: Any) -> SourceLocation:
        """Extract source location from tree-sitter node."""
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        source_code = ""
        if 0 < start_line <= len(self.source_lines):
            source_code = self.source_lines[start_line - 1].strip()

        return SourceLocation(
            file=self.file_path,
            start_line=start_line,
            end_line=end_line,
            source_code=source_code
        )

    def _get_node_label(self, node: Any) -> str:
        """Extract a meaningful label from a node using its actual source code.

        Returns the actual source code expression/statement instead of generic node type.
        Truncates to reasonable length for readability.
        """
        node_type = node.type
        source_text = self._node_text(node).strip()

        # For long source code, truncate intelligently
        max_length = 60
        if len(source_text) > max_length:
            # Try to find a good break point (space, operator, etc.)
            truncated = source_text[:max_length]
            if ' ' in truncated:
                truncated = truncated.rsplit(' ', 1)[0]
            source_text = truncated + '...'

        # Clean up excess whitespace
        source_text = ' '.join(source_text.split())

        return source_text if source_text else node_type

    def _get_condition_text(self, condition_node: Any) -> str:
        """Extract the actual condition expression from an if/while condition node."""
        if condition_node is None:
            return "condition"

        source_text = self._node_text(condition_node).strip()
        # Limit condition to reasonable length
        if len(source_text) > 50:
            source_text = source_text[:47] + '...'
        return source_text if source_text else "condition"

    def _node_text(self, node: Any) -> str:
        """Get text content of a node."""
        return node.text.decode('utf-8') if isinstance(node.text, bytes) else node.text

    def _report_unsupported(self, construct_type: str, line_num: int) -> None:
        """Report an unsupported construct."""
        msg = f"WARNING: Unsupported construct at line {line_num}: {construct_type}"
        self.warnings.append(msg)
        self.ambiguity_flags.append(f"Line {line_num}: {construct_type} (not fully analyzed)")
        self.analysis_incomplete = True
        print(msg, file=sys.stderr)

    def build_cfg_for_function(self, func_node: Any) -> CFG:
        """Build a CFG for a Rust function.

        Args:
            func_node: A tree-sitter function_item node.

        Returns:
            A CFG representing the function's control flow.
        """
        func_name = None
        func_body = None
        source_loc = self._get_source_location(func_node)

        # Find function name and body
        for child in func_node.children:
            if child.type == "identifier":
                func_name = self._node_text(child)
            elif child.type == "block":
                func_body = child

        if not func_name:
            func_name = "unknown"

        cfg = CFG(name=func_name, source_location=source_loc)
        entry_node = CFGNode(
            id=self._new_node_id(),
            label=f"{func_name} entry",
            node_type=NodeType.ENTRY,
            source_location=source_loc
        )
        cfg.add_node(entry_node)
        cfg.entry_node_id = entry_node.id

        exit_node = CFGNode(
            id=self._new_node_id(),
            label=f"{func_name} exit",
            node_type=NodeType.EXIT,
            source_location=source_loc
        )
        cfg.add_node(exit_node)
        cfg.exit_node_ids.append(exit_node.id)

        # Note: Exception exits are not created in Phase 3 since error handling
        # (via ? operator) is reported as unsupported syntax and not analyzed.
        # This avoids showing hypothetical exception paths as actual execution paths.

        if func_body:
            # Build CFG for the function body
            last_node_ids = self._build_block_cfg(func_body, cfg, entry_node.id, exit_node.id, exit_node.id)
            # Connect all exit paths to the exit node
            for node_id in last_node_ids:
                cfg.add_edge_simple(node_id, exit_node.id, edge_type=EdgeType.NORMAL)
        else:
            # No body, direct entry to exit
            cfg.add_edge_simple(entry_node.id, exit_node.id)

        return cfg

    def _is_syntax_only_node(self, node: Any) -> bool:
        """Check if a node is purely syntactic (braces, semicolons, etc.) with no semantic meaning.

        These nodes represent structural syntax, not executable statements.
        """
        # Nodes that are just delimiters, not executable statements
        syntax_only_types = {
            "{", "}", ";", ",", ":", ".", "->", "=>", "|", "&", "*", "+", "-",
            "!", "~", "<<", ">>", "==", "!=", "<", ">", "<=", ">=", "||", "&&",
            "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", ">>=", "<<=",
            "^", "(", ")", "[", "]", "<", ">", "as", "@", "#", "$", "`"
        }
        return node.type in syntax_only_types

    def _build_block_cfg(self, block_node: Any, cfg: CFG, entry_node_id: str,
                         exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Build CFG for a block statement.

        Returns:
            List of node IDs that should connect to the next statement or exit.
        """
        last_node_ids = [entry_node_id]

        for child in block_node.children:
            if child.type == "block" or child.type == "ERROR":
                # Skip nested blocks and error nodes
                continue

            # Skip syntax-only nodes (braces, semicolons, etc.)
            if self._is_syntax_only_node(child):
                continue

            new_last_ids = self._build_statement_cfg(
                child, cfg, last_node_ids, exit_node_id, exception_exit_node_id
            )
            if new_last_ids:
                last_node_ids = new_last_ids

        return last_node_ids

    def _build_statement_cfg(self, stmt_node: Any, cfg: CFG, prev_node_ids: List[str],
                            exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Build CFG for a statement and return node IDs that should continue to the next statement.

        Args:
            stmt_node: A statement node from the syntax tree.
            cfg: The CFG being built.
            prev_node_ids: Node IDs of previous statements.
            exit_node_id: The exit node ID for the containing function.
            exception_exit_node_id: The exception exit node ID.

        Returns:
            List of node IDs that continue the control flow, or empty if path terminates.
        """
        stmt_type = stmt_node.type

        if stmt_type == "if_expression":
            return self._handle_if_expression(stmt_node, cfg, prev_node_ids, exit_node_id, exception_exit_node_id)
        elif stmt_type == "match_expression":
            return self._handle_match_expression(stmt_node, cfg, prev_node_ids, exit_node_id, exception_exit_node_id)
        elif stmt_type in ("for_expression", "while_expression", "loop_statement"):
            return self._handle_loop(stmt_node, cfg, prev_node_ids, exit_node_id, exception_exit_node_id)
        elif stmt_type == "return_expression":
            return self._handle_return(stmt_node, cfg, prev_node_ids, exit_node_id)
        elif stmt_type == "break_expression":
            # Break statement - create edge to exit (or loop exit)
            for prev_id in prev_node_ids:
                cfg.add_edge_simple(prev_id, exit_node_id, edge_type=EdgeType.BREAK)
            return []
        elif stmt_type == "continue_expression":
            # Continue statement - would go back to loop, but we don't track loop entry here
            # For now, treat as a path that continues
            return prev_node_ids
        elif stmt_type == "expression_statement":
            return self._handle_expression_statement(stmt_node, cfg, prev_node_ids, exit_node_id, exception_exit_node_id)
        elif stmt_type == "block":
            return self._build_block_cfg(stmt_node, cfg, prev_node_ids[0] if prev_node_ids else "", exit_node_id, exception_exit_node_id)
        elif stmt_type == "macro_invocation":
            # Unsupported: macro
            line_num = stmt_node.start_point[0] + 1
            self._report_unsupported("macro_invocation", line_num)
            return prev_node_ids
        elif stmt_type in ("item", "use_declaration"):
            # Skip items and use declarations
            return prev_node_ids
        elif self._is_syntax_only_node(stmt_node):
            # Skip syntax-only nodes (braces, semicolons, etc.)
            return prev_node_ids
        else:
            # Other statement types - create a node with actual source code as label
            if stmt_type not in ("comment", ""):
                stmt_id = self._new_node_id()
                # Use actual source code as label, not generic node type
                label = self._get_node_label(stmt_node)
                stmt_node_obj = CFGNode(
                    id=stmt_id,
                    label=label,
                    node_type=NodeType.STATEMENT,
                    source_location=self._get_source_location(stmt_node)
                )
                cfg.add_node(stmt_node_obj)
                for prev_id in prev_node_ids:
                    cfg.add_edge_simple(prev_id, stmt_id)
                return [stmt_id]
            return prev_node_ids

    def _handle_if_expression(self, if_node: Any, cfg: CFG, prev_node_ids: List[str],
                             exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Handle if/else if/else expressions."""
        # Find condition and blocks
        condition_expr = None
        then_block = None
        else_block = None

        child_idx = 0
        for i, child in enumerate(if_node.children):
            if child.type == "if":
                continue
            elif child.type in ("identifier", "binary_expression", "comparison_expression",
                               "unary_expression", "call_expression", "field_expression",
                               "index_expression", "parenthesized_expression"):
                condition_expr = child
            elif child.type == "block":
                if then_block is None:
                    then_block = child
                else:
                    else_block = child
            elif child.type == "else":
                # This is an else keyword; look for the following block or if
                if i + 1 < len(if_node.children):
                    next_child = if_node.children[i + 1]
                    if next_child.type == "if_expression":
                        else_block = next_child
                    elif next_child.type == "block":
                        else_block = next_child

        # Create decision node
        decision_node_id = self._new_node_id()
        condition_text = self._get_condition_text(condition_expr)
        decision_node = CFGNode(
            id=decision_node_id,
            label=f"if {condition_text}",
            node_type=NodeType.DECISION,
            source_location=self._get_source_location(if_node)
        )
        cfg.add_node(decision_node)

        # Connect previous nodes to decision
        for prev_id in prev_node_ids:
            cfg.add_edge_simple(prev_id, decision_node_id)

        # Handle then branch
        then_last_ids = []
        if then_block:
            then_last_ids = self._build_block_cfg(then_block, cfg, decision_node_id, exit_node_id, exception_exit_node_id)
        else:
            then_last_ids = [decision_node_id]

        # Connect then branch with "true" label
        for node_id in then_last_ids:
            if decision_node_id in [e.source_id for e in cfg.edges if e.target_id == node_id]:
                # Already connected
                pass
            else:
                cfg.add_edge_simple(decision_node_id, node_id if node_id != decision_node_id else self._new_node_id(),
                                   label="true", edge_type=EdgeType.TRUE)

        # Handle else branch
        else_last_ids = []
        if else_block:
            if else_block.type == "if_expression":
                # else if - recurse
                else_last_ids = self._handle_if_expression(else_block, cfg, [decision_node_id], exit_node_id, exception_exit_node_id)
            else:
                # else block
                else_last_ids = self._build_block_cfg(else_block, cfg, decision_node_id, exit_node_id, exception_exit_node_id)
        else:
            # No else - false branch continues after if
            else_last_ids = [decision_node_id]

        # Create a merge node after if/else
        merge_node_id = self._new_node_id()
        merge_node = CFGNode(
            id=merge_node_id,
            label="merge",
            node_type=NodeType.STATEMENT,
            source_location=self._get_source_location(if_node)
        )
        cfg.add_node(merge_node)

        # Connect all branches to merge node
        for node_id in then_last_ids:
            if node_id != decision_node_id:
                cfg.add_edge_simple(node_id, merge_node_id)

        for node_id in else_last_ids:
            if node_id != decision_node_id:
                cfg.add_edge_simple(node_id, merge_node_id, edge_type=EdgeType.FALSE)

        # If false branch was just decision node (no else), add direct false edge
        if not else_block:
            cfg.add_edge_simple(decision_node_id, merge_node_id, label="false", edge_type=EdgeType.FALSE)

        return [merge_node_id]

    def _handle_match_expression(self, match_node: Any, cfg: CFG, prev_node_ids: List[str],
                                exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Handle match expressions."""
        # Find the scrutinee (the value being matched)
        scrutinee_text = ""
        for child in match_node.children:
            if child.type == "match" or self._is_syntax_only_node(child):
                continue
            if child.type == "block":
                break
            scrutinee_text = self._node_text(child).strip()
            if scrutinee_text:
                break

        # Create decision node with match scrutinee
        decision_node_id = self._new_node_id()
        label = f"match {scrutinee_text[:40]}" if scrutinee_text else "match"
        decision_node = CFGNode(
            id=decision_node_id,
            label=label,
            node_type=NodeType.DECISION,
            source_location=self._get_source_location(match_node)
        )
        cfg.add_node(decision_node)

        # Connect previous nodes to decision
        for prev_id in prev_node_ids:
            cfg.add_edge_simple(prev_id, decision_node_id)

        # Find all match arms
        all_last_ids = []
        for child in match_node.children:
            if child.type == "match_arm":
                # Build CFG for this arm
                arm_last_ids = self._build_match_arm(child, cfg, decision_node_id, exit_node_id, exception_exit_node_id)
                all_last_ids.extend(arm_last_ids)

        # Create merge node
        merge_node_id = self._new_node_id()
        merge_node = CFGNode(
            id=merge_node_id,
            label="merge",
            node_type=NodeType.STATEMENT,
            source_location=self._get_source_location(match_node)
        )
        cfg.add_node(merge_node)

        # Connect all arms to merge
        for node_id in all_last_ids:
            if node_id != decision_node_id:
                cfg.add_edge_simple(node_id, merge_node_id)

        return [merge_node_id]

    def _build_match_arm(self, arm_node: Any, cfg: CFG, match_decision_id: str,
                        exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Build CFG for a match arm.

        Returns:
            List of node IDs that should connect to the merge node.
        """
        # Find pattern and expression/block
        pattern_text = ""
        arm_body = None

        for child in arm_node.children:
            if child.type == "match_pattern":
                pattern_text = self._node_text(child)
            elif child.type == "block":
                arm_body = child
            elif child.type in ("identifier", "integer_literal", "string_literal"):
                pattern_text = self._node_text(child)

        # Create arm node
        arm_node_id = self._new_node_id()
        arm_obj = CFGNode(
            id=arm_node_id,
            label=f"=> {pattern_text[:30]}",
            node_type=NodeType.STATEMENT,
            source_location=self._get_source_location(arm_node)
        )
        cfg.add_node(arm_obj)
        cfg.add_edge_simple(match_decision_id, arm_node_id, label=pattern_text, edge_type=EdgeType.NORMAL)

        # Build body
        if arm_body:
            return self._build_block_cfg(arm_body, cfg, arm_node_id, exit_node_id, exception_exit_node_id)
        else:
            return [arm_node_id]

    def _handle_loop(self, loop_node: Any, cfg: CFG, prev_node_ids: List[str],
                    exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Handle for, while, and loop statements."""
        loop_type = loop_node.type

        # Build a meaningful label for the loop
        loop_label = "loop"
        if loop_type == "for_expression":
            # Try to extract for pattern/condition
            for_pattern = ""
            for child in loop_node.children:
                if child.type == "for" or self._is_syntax_only_node(child):
                    continue
                if child.type == "block":
                    break
                for_pattern = self._node_text(child).strip()
                if for_pattern:
                    break
            if for_pattern:
                if len(for_pattern) > 40:
                    for_pattern = for_pattern[:37] + '...'
                loop_label = f"for {for_pattern}"
            else:
                loop_label = "for"
        elif loop_type == "while_expression":
            # Try to extract while condition
            while_condition = ""
            for child in loop_node.children:
                if child.type == "while" or self._is_syntax_only_node(child):
                    continue
                if child.type == "block":
                    break
                while_condition = self._node_text(child).strip()
                if while_condition:
                    break
            if while_condition:
                if len(while_condition) > 40:
                    while_condition = while_condition[:37] + '...'
                loop_label = f"while {while_condition}"
            else:
                loop_label = "while"

        # Create loop entry node
        loop_entry_id = self._new_node_id()
        loop_entry = CFGNode(
            id=loop_entry_id,
            label=loop_label,
            node_type=NodeType.LOOP_ENTRY,
            source_location=self._get_source_location(loop_node)
        )
        cfg.add_node(loop_entry)

        # Connect previous nodes to loop entry
        for prev_id in prev_node_ids:
            cfg.add_edge_simple(prev_id, loop_entry_id)

        # Find loop body
        loop_body = None
        for child in loop_node.children:
            if child.type == "block":
                loop_body = child
                break

        # Build loop body CFG
        if loop_body:
            body_last_ids = self._build_block_cfg(loop_body, cfg, loop_entry_id, exit_node_id, exception_exit_node_id)
        else:
            body_last_ids = [loop_entry_id]

        # Create loop back edge and exit
        for node_id in body_last_ids:
            cfg.add_edge_simple(node_id, loop_entry_id, edge_type=EdgeType.LOOP_BACK)

        # Exit node after loop (represents loop not taken or break)
        exit_after_loop_id = self._new_node_id()
        exit_after_loop = CFGNode(
            id=exit_after_loop_id,
            label="loop exit",
            node_type=NodeType.STATEMENT,
            source_location=self._get_source_location(loop_node)
        )
        cfg.add_node(exit_after_loop)
        cfg.add_edge_simple(loop_entry_id, exit_after_loop_id, label="break", edge_type=EdgeType.BREAK)

        return [exit_after_loop_id]

    def _handle_return(self, return_node: Any, cfg: CFG, prev_node_ids: List[str], exit_node_id: str) -> List[str]:
        """Handle return statements."""
        # Create return node with actual returned value
        return_node_id = self._new_node_id()
        return_text = self._node_text(return_node).strip()

        # Extract just the returned value if it's available
        if return_text.startswith('return'):
            return_text = return_text[6:].strip()
            if return_text:
                # Limit to reasonable length
                if len(return_text) > 40:
                    return_text = return_text[:37] + '...'
                label = f"return {return_text}"
            else:
                label = "return"
        else:
            label = return_text if return_text else "return"

        return_obj = CFGNode(
            id=return_node_id,
            label=label,
            node_type=NodeType.STATEMENT,
            source_location=self._get_source_location(return_node)
        )
        cfg.add_node(return_obj)

        # Connect previous nodes to return
        for prev_id in prev_node_ids:
            cfg.add_edge_simple(prev_id, return_node_id)

        # Connect return to exit
        cfg.add_edge_simple(return_node_id, exit_node_id)

        # Return stops the flow
        return []

    def _handle_expression_statement(self, expr_stmt_node: Any, cfg: CFG, prev_node_ids: List[str],
                                     exit_node_id: str, exception_exit_node_id: str) -> List[str]:
        """Handle expression statements."""
        # Find the actual expression
        for child in expr_stmt_node.children:
            if child.type != ";":
                return self._build_statement_cfg(child, cfg, prev_node_ids, exit_node_id, exception_exit_node_id)

        return prev_node_ids


    def analyze(self, source_path: str) -> AnalysisResult:
        """Analyze a Rust source file and build CFGs for all functions.

        Args:
            source_path: Path to the Rust file to analyze.

        Returns:
            AnalysisResult containing control-flow graphs for all functions.
        """
        with open(source_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        try:
            tree = self.parser.parse(source_code.encode('utf-8'))
        except Exception as e:
            result = AnalysisResult(file_path=source_path, success=False)
            result.errors.append(f"Parser error: {e}")
            return result

        builder = RustCFGBuilder(source_code, source_path, self.rust_language)
        result = AnalysisResult(file_path=source_path)

        # Extract all function definitions
        try:
            self._extract_functions(tree.root_node, builder, result)
        except Exception as e:
            result.errors.append(f"Analysis error: {e}")
            result.success = False

        result.errors.extend(builder.errors)
        result.warnings.extend(builder.warnings)
        result.ambiguity_flags.extend(builder.ambiguity_flags)
        result.analysis_incomplete = builder.analysis_incomplete
        result.success = len(result.errors) == 0 and not builder.analysis_incomplete

        return result

    def _extract_functions(self, node: Any, builder: 'RustCFGBuilder', result: AnalysisResult) -> None:
        """Recursively extract function definitions from the syntax tree."""
        if node.type == "function_item":
            # Build CFG for this function
            cfg = builder.build_cfg_for_function(node)
            func_name = self._get_function_name(node)
            if func_name:
                result.functions[func_name] = cfg

        # Recurse into children
        for child in node.children:
            self._extract_functions(child, builder, result)

    def _get_function_name(self, func_node: Any) -> Optional[str]:
        """Extract function name from a function_item node."""
        for child in func_node.children:
            if child.type == "identifier":
                return child.text.decode('utf-8')
        return None

    @property
    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".rs"]

    @property
    def name(self) -> str:
        """Return the analyzer name."""
        return "RustAnalyzer"

    @property
    def version(self) -> str:
        """Return the analyzer version."""
        return "0.3.0"
