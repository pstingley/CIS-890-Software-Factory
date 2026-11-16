"""HTML report generator - creates interactive HTML reports."""

import json
import html as html_module
from datetime import datetime
from codeflow import __version__
from codeflow.graph import AnalysisResult
from codeflow.render.svg_renderer import SVGRenderer


class HTMLReportGenerator:
    """Generates HTML reports for analysis results."""
    
    def __init__(self, result: AnalysisResult, specification_note: str = ""):
        self.result = result
        self.specification_note = specification_note
        self.timestamp = datetime.now().isoformat()
    
    def generate(self) -> str:
        """Generate the complete HTML report."""
        html_parts = [
            self._get_html_header(),
            self._get_metadata_section(),
            self._get_function_list(),
            self._get_diagrams_section(),
            self._get_errors_section(),
            self._get_footer(),
        ]
        return '\n'.join(html_parts)
    
    def _get_html_header(self) -> str:
        """Return HTML header and styles."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeFlow Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        header p { font-size: 1.1em; opacity: 0.9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .metadata {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .metadata h2 { margin-top: 0; color: #667eea; }
        .metadata table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .metadata td { padding: 8px 12px; border-bottom: 1px solid #eee; }
        .metadata td:first-child { font-weight: 600; width: 30%; }
        .function-list {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .function-list h2 { margin-top: 0; color: #667eea; }
        .function-list ul { list-style: none; }
        .function-list li {
            padding: 10px;
            margin: 5px 0;
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            cursor: pointer;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .function-list li:hover { background: #f0f0f0; }
        .function-list a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .function-list a:hover { text-decoration: underline; }
        .diagram-section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .diagram-section h2 { color: #667eea; margin-bottom: 20px; }
        .diagram-header {
            padding: 10px 0;
            border-bottom: 2px solid #667eea;
            margin-bottom: 10px;
        }
        .diagram-info { font-size: 0.9em; color: #666; margin: 5px 0; }
        .diagram-svg {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            background: #fafafa;
            overflow: auto;
        }
        .diagram-svg > svg { display: block; margin-inline: auto; }
        .error-section {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
        }
        .error-section h2 { color: #856404; }
        .error-list { list-style: none; padding: 10px 0; }
        .error-list li {
            padding: 5px 0;
            color: #856404;
            border-left: 3px solid #ffc107;
            padding-left: 10px;
        }
        footer {
            text-align: center;
            padding: 30px 20px;
            color: #666;
            font-size: 0.9em;
        }
        .complete-badge { display: inline-block; padding: 3px 8px; background: #d4edda; color: #155724; border-radius: 4px; font-size: 0.85em; }
        .partial-badge { display: inline-block; padding: 3px 8px; background: #fff3cd; color: #856404; border-radius: 4px; font-size: 0.85em; }
        .source-code {
            background: #f4f4f4;
            padding: 10px;
            border-left: 3px solid #667eea;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <header>
        <h1>CodeFlow Analysis Report</h1>
        <p>Control-flow visualization for Python source code</p>
    </header>
    <div class="container">'''
    
    def _get_metadata_section(self) -> str:
        """Return metadata section."""
        parts = [
            '<div class="metadata">',
            '<h2>Analysis Metadata</h2>',
            '<table>',
            f'  <tr><td>Source File</td><td><code>{html_module.escape(self.result.file_path)}</code></td></tr>',
            f'  <tr><td>Analysis Time</td><td>{self.timestamp}</td></tr>',
            f'  <tr><td>CodeFlow Version</td><td>{__version__}</td></tr>',
            f'  <tr><td>{"Workflows" if self.specification_note else "Functions Analyzed"}</td><td>{len(self.result.functions)}</td></tr>',
            f'  <tr><td>Specification</td><td>{html_module.escape(self.specification_note)}</td></tr>' if self.specification_note else "",
            f'  <tr><td>Status</td><td>{"Success" if self.result.success else "Errors Found"}</td></tr>',
            '</table>',
            '</div>',
        ]
        return '\n'.join(parts)
    
    def _get_function_list(self) -> str:
        """Return function list section."""
        if not self.result.functions:
            return ''
        
        parts = [
            '<div class="function-list">',
            '<h2>Workflows</h2>' if self.specification_note else '<h2>Functions</h2>',
            '<ul>',
        ]
        
        for func_name in sorted(self.result.functions.keys()):
            parts.append(f'  <li><a href="#{func_name}">{func_name}</a></li>')
        
        parts.extend(['</ul>', '</div>'])
        return '\n'.join(parts)
    
    def _get_diagrams_section(self) -> str:
        """Return diagrams section."""
        if not self.result.functions:
            return '<p>No functions analyzed.</p>'
        
        parts = ['<h2>Control-Flow Diagrams</h2>']
        
        for func_name, cfg in sorted(self.result.functions.items()):
            parts.append(f'<div class="diagram-section" id="{func_name}">')
            parts.append(f'  <div class="diagram-header">')
            parts.append(f'    <h3>{func_name}</h3>')
            
            # Status badge
            if self.specification_note:
                parts.append('    <span class="complete-badge">SPECIFICATION VIEW</span>')
            elif cfg.is_partial:
                parts.append(f'    <span class="partial-badge">PARTIAL - {cfg.partial_reason}</span>')
            else:
                parts.append(f'    <span class="complete-badge">COMPLETE</span>')
            
            # Source info
            if cfg.source_location:
                parts.append(f'    <div class="diagram-info">Lines {cfg.source_location.start_line}-{cfg.source_location.end_line}</div>')
            
            parts.append(f'  </div>')
            
            # SVG diagram
            renderer = SVGRenderer(cfg)
            svg_content = renderer.render()
            parts.append(f'  <div class="diagram-svg">')
            parts.append(svg_content)
            parts.append(f'  </div>')
            
            parts.append(f'</div>')
        
        return '\n'.join(parts)
    
    def _get_errors_section(self) -> str:
        """Return errors and warnings section."""
        if not self.result.errors and not self.result.warnings:
            return ''
        
        parts = []
        
        if self.result.errors:
            parts.extend([
                '<div class="error-section">',
                '<h2>Errors</h2>',
                '<ul class="error-list">',
            ])
            for error in self.result.errors:
                parts.append(f'  <li>{html_module.escape(error)}</li>')
            parts.extend(['</ul>', '</div>'])
        
        if self.result.warnings:
            parts.extend([
                '<div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; padding: 15px; margin: 20px 0;">',
                '<h2 style="color: #0c5460;">Warnings</h2>',
                '<ul class="error-list" style="border-left-color: #17a2b8;">',
            ])
            for warning in self.result.warnings:
                parts.append(f'  <li style="border-left-color: #17a2b8; color: #0c5460;">{html_module.escape(warning)}</li>')
            parts.extend(['</ul>', '</div>'])
        
        return '\n'.join(parts)
    
    def _get_footer(self) -> str:
        """Return HTML footer."""
        return '''    </div>
    <footer>
        <p>Generated by CodeFlow v1.0.0 - A Python control-flow visualization tool</p>
        <p>For more information, visit the project documentation.</p>
    </footer>
</body>
</html>'''
