"""Word document (.docx) generator for CodeFlow analysis results."""

import os
from datetime import datetime
from typing import Dict, List, Tuple
from io import BytesIO
import xml.etree.ElementTree as ET

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from codeflow import __version__
from codeflow.graph import AnalysisResult, CFG
from codeflow.render.svg_renderer import SVGRenderer


class DocxGenerator:
    """Generates Word (.docx) documents for analysis results."""

    def __init__(self, result: AnalysisResult, specification_note: str = ""):
        """Initialize the Word document generator.

        Args:
            result: AnalysisResult from code analysis
            specification_note: Optional specification context
        """
        self.result = result
        self.specification_note = specification_note
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.doc = Document()
        self._setup_styles()

    def _setup_styles(self):
        """Configure document styles."""
        # Set up title style
        style = self.doc.styles['Heading 1']
        style.font.size = Pt(28)
        style.font.bold = True
        style.font.color.rgb = RGBColor(102, 126, 234)

        style = self.doc.styles['Heading 2']
        style.font.size = Pt(16)
        style.font.bold = True
        style.font.color.rgb = RGBColor(52, 73, 94)

        style = self.doc.styles['Heading 3']
        style.font.size = Pt(13)
        style.font.bold = True
        style.font.color.rgb = RGBColor(100, 100, 100)

        style = self.doc.styles['Normal']
        style.font.size = Pt(11)

    def generate(self) -> Document:
        """Generate the complete Word document.

        Returns:
            Document object ready for saving
        """
        self._add_title_page()
        self._add_metadata_section()
        self._add_executive_summary()
        self._add_table_of_contents()
        self._add_analysis_overview()
        self._add_control_flow_section()
        self._add_findings_section()
        self._add_appendices()

        return self.doc

    def save(self, file_path: str) -> str:
        """Save the document to a file.

        Args:
            file_path: Path to save the .docx file

        Returns:
            Path to the saved file
        """
        self.generate()
        self.doc.save(file_path)
        return file_path

    def _add_title_page(self):
        """Add title page with document header."""
        # Title
        title = self.doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.add_run("CodeFlow Analysis Report")
        title_run.font.size = Pt(32)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(102, 126, 234)

        # Subtitle
        subtitle = self.doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_run = subtitle.add_run(
            f"Software System Documentation and Control-Flow Analysis"
        )
        subtitle_run.font.size = Pt(14)
        subtitle_run.font.italic = True

        # Spacing
        self.doc.add_paragraph()
        self.doc.add_paragraph()

        # File info
        file_info = self.doc.add_paragraph()
        file_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        file_run = file_info.add_run(f"Source: {os.path.basename(self.result.file_path)}")
        file_run.font.size = Pt(12)

        # Analysis info
        analysis_info = self.doc.add_paragraph()
        analysis_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        analysis_run = analysis_info.add_run(f"Generated: {self.timestamp}")
        analysis_run.font.size = Pt(11)

        version_info = self.doc.add_paragraph()
        version_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        version_run = version_info.add_run(f"CodeFlow v{__version__}")
        version_run.font.size = Pt(11)

        # Page break
        self.doc.add_page_break()

    def _add_metadata_section(self):
        """Add analysis metadata section."""
        self.doc.add_heading("Analysis Metadata", level=2)

        # Create metadata table
        table = self.doc.add_table(rows=1, cols=2)
        table.style = "Light Grid Accent 1"
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Property"
        hdr_cells[1].text = "Value"

        # Make header bold
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True

        # Add metadata rows
        metadata = [
            ("Source File", os.path.basename(self.result.file_path)),
            ("Full Path", self.result.file_path),
            ("Analysis Time", self.timestamp),
            ("CodeFlow Version", __version__),
            (
                "Functions/Workflows Analyzed",
                str(len(self.result.functions)),
            ),
            (
                "Analysis Status",
                "✓ Success" if self.result.success else "✗ Errors Found",
            ),
            (
                "Specification Context",
                self.specification_note if self.specification_note else "Standard analysis",
            ),
        ]

        for prop, value in metadata:
            row_cells = table.add_row().cells
            row_cells[0].text = prop
            row_cells[1].text = value

        self.doc.add_paragraph()

    def _add_executive_summary(self):
        """Add executive summary section."""
        self.doc.add_heading("Executive Summary", level=2)

        # Overview
        overview = self.doc.add_paragraph()
        overview.add_run("Analysis Overview\n").bold = True
        self._add_analysis_overview_text()

        self.doc.add_paragraph()

        # Key Findings
        findings = self.doc.add_paragraph()
        findings.add_run("Key Findings\n").bold = True

        if self.result.errors:
            error_para = self.doc.add_paragraph(style="List Bullet")
            error_run = error_para.add_run(
                f"Analysis Errors: {len(self.result.errors)} issue(s) found"
            )
            error_run.font.color.rgb = RGBColor(192, 0, 0)

        if self.result.warnings:
            warn_para = self.doc.add_paragraph(style="List Bullet")
            warn_run = warn_para.add_run(
                f"Warnings: {len(self.result.warnings)} item(s) flagged"
            )
            warn_run.font.color.rgb = RGBColor(255, 128, 0)

        if not self.result.errors and not self.result.warnings:
            success_para = self.doc.add_paragraph(style="List Bullet")
            success_run = success_para.add_run(
                "No errors or warnings detected during analysis"
            )
            success_run.font.color.rgb = RGBColor(0, 128, 0)

        self.doc.add_paragraph()

    def _add_analysis_overview_text(self):
        """Add overview text about the analysis."""
        num_functions = len(self.result.functions)
        source_name = os.path.basename(self.result.file_path)

        text_parts = [
            f"This report documents the results of CodeFlow analysis on {source_name}.",
            "",
            f"The analysis identified and documented {num_functions} function(s) or workflow(s)",
            "in the source code, extracting their control-flow characteristics, semantic",
            "labels, and graphical representations.",
            "",
            "Each function's control-flow graph (CFG) is presented both textually",
            "(describing decision branches, loop structures, and exception handling)",
            "and visually (as an SVG flowchart embedded in this document).",
        ]

        for text in text_parts:
            if text:
                self.doc.add_paragraph(text, style="Normal")

    def _add_table_of_contents(self):
        """Add table of contents."""
        self.doc.add_heading("Table of Contents", level=2)

        toc_items = [
            "1. Analysis Metadata",
            "2. Executive Summary",
            "3. Table of Contents",
            "4. Analysis Overview",
            "5. Control-Flow Analysis",
        ]

        if self.result.functions:
            toc_items.append(f"   • Function Details ({len(self.result.functions)} items)")

        if self.result.errors or self.result.warnings:
            toc_items.append("6. Findings and Issues")

        toc_items.extend([
            "7. Appendices",
            "   • Glossary",
            "   • Analysis Limitations",
            "   • Source References",
        ])

        for item in toc_items:
            self.doc.add_paragraph(item, style="List Bullet" if item.startswith("   •") else "Normal")

        self.doc.add_page_break()

    def _add_analysis_overview(self):
        """Add analysis overview section."""
        self.doc.add_heading("Analysis Overview", level=2)

        self.doc.add_heading("Scope and Purpose", level=3)
        self.doc.add_paragraph(
            "This analysis uses CodeFlow to automatically extract and document the "
            "control-flow structure of software systems. Each function's execution "
            "paths, decision points, and exception handling are identified and visualized."
        )

        self.doc.add_heading("Analysis Methodology", level=3)
        methodology = [
            "Source-level parsing and abstract syntax tree (AST) analysis",
            "Control-flow graph (CFG) construction from semantic information",
            "Identification of decision branches (if/else, switch/match)",
            "Loop detection and characterization (for, while, do-while)",
            "Exception and error-handling path analysis",
            "Automatic SVG flowchart generation with semantic labels",
        ]

        for item in methodology:
            self.doc.add_paragraph(item, style="List Bullet")

        self.doc.add_heading("Supported Language Features", level=3)
        self.doc.add_paragraph(
            "CodeFlow analyzes the following control-flow constructs:"
        )

        features = [
            "Conditional branches (if, else if, else; switch/match)",
            "Loop structures (for, while, do-while, loop)",
            "Function and method calls",
            "Return statements and exit points",
            "Exception and error handling (try/catch, panic, Result types)",
            "Break and continue statements",
            "Loop-back edges and cyclic structures",
        ]

        for item in features:
            self.doc.add_paragraph(item, style="List Bullet")

        self.doc.add_page_break()

    def _add_control_flow_section(self):
        """Add control-flow analysis section."""
        self.doc.add_heading("Control-Flow Analysis", level=2)

        if not self.result.functions:
            self.doc.add_paragraph("No functions were analyzed.")
            return

        for func_name, cfg in sorted(self.result.functions.items()):
            self._add_function_documentation(func_name, cfg)

    def _add_function_documentation(self, func_name: str, cfg: CFG):
        """Add documentation for a single function."""
        # Function heading
        heading = self.doc.add_heading(f"Function: {func_name}", level=3)

        # Status badge
        status_para = self.doc.add_paragraph()
        if self.specification_note:
            status_run = status_para.add_run("STATUS: Specification View")
            status_run.font.bold = True
            status_run.font.color.rgb = RGBColor(0, 112, 192)
        elif cfg.is_partial:
            status_run = status_para.add_run(f"STATUS: Partial Analysis - {cfg.partial_reason}")
            status_run.font.bold = True
            status_run.font.color.rgb = RGBColor(255, 128, 0)
        else:
            status_run = status_para.add_run("STATUS: Complete")
            status_run.font.bold = True
            status_run.font.color.rgb = RGBColor(0, 128, 0)

        # Source location
        if cfg.source_location:
            loc_para = self.doc.add_paragraph()
            loc_para.add_run("Source Location: ").bold = True
            loc_para.add_run(
                f"Lines {cfg.source_location.start_line}-{cfg.source_location.end_line}"
            )

            # Source code snippet
            if cfg.source_location.source_code:
                self.doc.add_paragraph("Source Code:", style="Heading 4")
                code_para = self.doc.add_paragraph(cfg.source_location.source_code)
                code_format = code_para.paragraph_format
                code_format.left_indent = Inches(0.5)
                for run in code_para.runs:
                    run.font.name = "Courier New"
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(100, 100, 100)

        # Functional description
        self.doc.add_heading("Functional Description", level=4)
        self._add_function_description(cfg)

        # Technical description
        self.doc.add_heading("Technical Description", level=4)
        self._add_technical_description(cfg)

        # Control-flow graph visualization
        self.doc.add_heading("Control-Flow Graph", level=4)
        self._add_svg_diagram(func_name, cfg)

        # Branch analysis
        self.doc.add_heading("Branch Analysis", level=4)
        self._add_branch_analysis(cfg)

        self.doc.add_paragraph()

    def _add_function_description(self, cfg: CFG):
        """Add functional description of a function."""
        desc = self.doc.add_paragraph()

        # Analyze the CFG to describe what it does
        num_nodes = len(cfg.nodes)
        num_decision_nodes = sum(1 for n in cfg.nodes.values() if n.node_type.name in ['DECISION', 'LOOP'])

        lines = [
            f"This function contains {num_nodes} statement node(s) and {num_decision_nodes} decision/loop node(s).",
            "",
            "The function's execution begins at the entry point and follows one or more",
            "paths through its decision branches and loops before reaching an exit point.",
            "The specific path taken depends on input values and runtime conditions.",
        ]

        for line in lines:
            if line:
                self.doc.add_paragraph(line)

    def _add_technical_description(self, cfg: CFG):
        """Add technical description of control-flow characteristics."""
        self.doc.add_paragraph("Control-Flow Characteristics:", style="Heading 4")

        # Analyze CFG structure
        has_loops = any(e.edge_type.name == "LOOP_BACK" for e in cfg.edges)
        has_exceptions = any(e.edge_type.name == "EXCEPTION" for e in cfg.edges)
        has_decision = any(n.node_type.name in ['DECISION', 'LOOP'] for n in cfg.nodes.values())

        characteristics = []

        if has_decision:
            characteristics.append("• Contains conditional branches or decision points")
        if has_loops:
            characteristics.append("• Contains loop structures with loop-back edges")
        if has_exceptions:
            characteristics.append("• Contains exception or error-handling paths")

        if cfg.nodes:
            entry_id = cfg.entry_node_id
            exit_ids = cfg.exit_node_ids
            characteristics.append(f"• Entry point: {entry_id}")
            characteristics.append(f"• Exit point(s): {', '.join(exit_ids)}")

        for char in characteristics:
            self.doc.add_paragraph(char)

    def _add_svg_diagram(self, func_name: str, cfg: CFG):
        """Add SVG diagram to the document."""
        try:
            renderer = SVGRenderer(cfg)
            svg_content = renderer.render()

            # SVG cannot be directly embedded in .docx, so we'll add a placeholder
            # and instructions to view the HTML or JSON version
            note_para = self.doc.add_paragraph()
            note_run = note_para.add_run(
                "⚠ SVG Flowchart (view in HTML or JSON export for interactive diagram)"
            )
            note_run.font.italic = True
            note_run.font.size = Pt(10)
            note_run.font.color.rgb = RGBColor(128, 128, 128)

            # Add a text-based description of the control flow
            self._add_text_flow_diagram(cfg)

        except Exception as e:
            self.doc.add_paragraph(f"[Unable to generate diagram: {e}]", style="Normal")

    def _add_text_flow_diagram(self, cfg: CFG):
        """Add text-based representation of control flow."""
        self.doc.add_paragraph("Text-Based Flow Representation:")

        # Build a simple ASCII-like representation
        visited = set()
        flow_lines = []

        entry_node = cfg.nodes.get(cfg.entry_node_id)
        if entry_node:
            flow_lines.append(f"[Entry] → {entry_node.label or 'Start'}")

        # List decision points
        for node_id, node in cfg.nodes.items():
            if node.node_type.name in ['DECISION', 'LOOP']:
                flow_lines.append(f"  ⬥ {node.label or f'Decision {node_id}'}")

        # List exit points
        for exit_id in cfg.exit_node_ids:
            exit_node = cfg.nodes.get(exit_id)
            if exit_node:
                flow_lines.append(f"[Exit] ← {exit_node.label or 'End'}")

        for line in flow_lines:
            flow_para = self.doc.add_paragraph(line)
            flow_para.paragraph_format.left_indent = Inches(0.25)

    def _add_branch_analysis(self, cfg: CFG):
        """Add branch analysis details."""
        branches = {}

        for edge in cfg.edges:
            edge_type = edge.edge_type.name
            if edge_type not in branches:
                branches[edge_type] = []
            branches[edge_type].append(edge)

        if not branches:
            self.doc.add_paragraph("No branch information available.")
            return

        self.doc.add_paragraph("Edge Types and Paths:")

        for edge_type in sorted(branches.keys()):
            edges = branches[edge_type]
            self.doc.add_paragraph(f"{edge_type}: {len(edges)} path(s)", style="List Bullet")

    def _add_findings_section(self):
        """Add findings and issues section."""
        if not self.result.errors and not self.result.warnings and not self.result.ambiguity_flags:
            return

        self.doc.add_page_break()
        self.doc.add_heading("Findings and Issues", level=2)

        # Errors
        if self.result.errors:
            self.doc.add_heading("Analysis Errors", level=3)
            for i, error in enumerate(self.result.errors, 1):
                error_para = self.doc.add_paragraph(style="List Bullet")
                error_run = error_para.add_run(f"{i}. {error}")
                error_run.font.color.rgb = RGBColor(192, 0, 0)

        # Warnings
        if self.result.warnings:
            self.doc.add_heading("Warnings", level=3)
            for i, warning in enumerate(self.result.warnings, 1):
                warn_para = self.doc.add_paragraph(style="List Bullet")
                warn_run = warn_para.add_run(f"{i}. {warning}")
                warn_run.font.color.rgb = RGBColor(255, 128, 0)

        # Ambiguity flags
        if self.result.ambiguity_flags:
            self.doc.add_heading("Ambiguities and Limitations", level=3)
            for i, flag in enumerate(self.result.ambiguity_flags, 1):
                amb_para = self.doc.add_paragraph(style="List Bullet")
                amb_run = amb_para.add_run(f"{i}. {flag}")
                amb_run.font.color.rgb = RGBColor(100, 100, 100)

    def _add_appendices(self):
        """Add appendix sections."""
        self.doc.add_page_break()
        self.doc.add_heading("Appendices", level=2)

        # Glossary
        self.doc.add_heading("Glossary of Terms", level=3)
        glossary = [
            ("CFG", "Control-Flow Graph: a directed graph representation of all execution paths"),
            ("Entry Node", "The starting point of a function's execution"),
            ("Exit Node", "A point where the function returns or terminates"),
            ("Decision Node", "A branch point where execution can follow multiple paths"),
            ("Loop-Back Edge", "An edge that creates a cycle, representing loop structures"),
            ("Exception Path", "An edge representing exception or error handling"),
            ("Node Label", "Human-readable semantic description of a code statement"),
            ("Edge Type", "Classification of the relationship between nodes (normal, conditional, loop, exception)"),
        ]

        for term, definition in glossary:
            term_para = self.doc.add_paragraph()
            term_run = term_para.add_run(term)
            term_run.bold = True
            term_para.add_run(f": {definition}")

        self.doc.add_page_break()

        # Analysis Limitations
        self.doc.add_heading("Analysis Limitations and Disclaimers", level=3)
        limitations = [
            "CodeFlow analyzes static source code and cannot predict all runtime behaviors.",
            "Dynamic dispatch, reflection, and runtime-generated code are not analyzed.",
            "Third-party library calls are represented as single nodes without internal analysis.",
            "Implicit control-flow (e.g., exception propagation across function boundaries) may be simplified.",
            "The analysis assumes the source code is syntactically valid and can be parsed.",
            "Some language-specific constructs (macros, templates, metacode) may be partially or fully unsupported.",
            "Generated documentation should be reviewed and supplemented with domain knowledge.",
        ]

        for limitation in limitations:
            self.doc.add_paragraph(limitation, style="List Bullet")

        self.doc.add_page_break()

        # Source References
        self.doc.add_heading("Source Code References", level=3)

        if self.result.source_references:
            source_table = self.doc.add_table(rows=1, cols=3)
            source_table.style = "Light Grid Accent 1"
            hdr = source_table.rows[0].cells
            hdr[0].text = "Line"
            hdr[1].text = "Code"
            hdr[2].text = "Context"

            for ref in self.result.source_references[:20]:  # Limit to first 20
                row = source_table.add_row().cells
                row[0].text = str(ref.start_line) if hasattr(ref, 'start_line') else "?"
                row[1].text = str(ref.source_code)[:50] if hasattr(ref, 'source_code') else "?"
                row[2].text = ""  # Context placeholder
        else:
            self.doc.add_paragraph("No source references available.")
