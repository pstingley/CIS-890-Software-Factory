"""Command-line interface for CodeFlow."""

import argparse
from pathlib import Path
import sys
import webbrowser
import json
import os

from codeflow import __version__, specification
from codeflow.report_generator import ReportGenerator
from codeflow.analyzers import get_analyzer
from codeflow.project import ProjectDiscoveryManager

def _generate_project_index(analysis, file_reports, index_file, output_path):
    """Generate a combined HTML index report for the project.

    Args:
        analysis: ProjectAnalysis object
        file_reports: Dict mapping relative paths to (html_file, json_file, docx_file, result) tuples
        index_file: Path to write index.html
        output_path: Path to output directory
    """
    # Build file items
    file_items_html = []
    for rel_path, report_tuple in sorted(file_reports.items()):
        # Handle both old and new tuple formats
        if len(report_tuple) == 4:
            html_file, json_file, docx_file, result = report_tuple
        else:
            html_file, json_file, result = report_tuple
            docx_file = None

        file_info = analysis.files[rel_path]
        html_link = os.path.relpath(html_file, output_path)
        json_link = os.path.relpath(json_file, output_path)

        docx_link_html = ""
        if docx_file:
            docx_link = os.path.relpath(docx_file, output_path)
            docx_link_html = f'<a href="{docx_link}" class="btn btn-secondary">Word Doc</a>'

        file_items_html.append(f"""
        <li class="file-item">
            <div>
                <div class="file-path">{rel_path}</div>
                <div class="file-meta">
                    {file_info.line_count} lines |
                    {len(result.functions)} functions |
                    Language: <span class="language-badge">{file_info.language}</span>
                </div>
            </div>
            <div class="file-links">
                <a href="{html_link}" class="btn">View Flowcharts</a>
                <a href="{json_link}" class="btn btn-secondary">JSON</a>
                {docx_link_html}
            </div>
        </li>
        """)

    # Build entry points section
    entry_points_html = ""
    if analysis.entry_points:
        eps = []
        for ep in analysis.entry_points:
            eps.append(f'<div class="entry-point"><strong>{ep.path}</strong> ({ep.type}, {ep.language}): {ep.description}</div>')
        entry_points_html = f"""
        <h2>Entry Points</h2>
        <div class="entry-points">
            {''.join(eps)}
        </div>
        """

    # Build warnings section
    warnings_html = ""
    if analysis.warnings:
        warnings = []
        for warning in analysis.warnings[:10]:
            warnings.append(f'<div class="warning">{warning}</div>')
        more_count = len(analysis.warnings) - 10
        more_text = f'<div style="margin-top: 10px; color: #7f8c8d;">... and {more_count} more</div>' if more_count > 0 else ''
        warnings_html = f"""
        <h2>Warnings</h2>
        <div class="warnings">
            {''.join(warnings)}
            {more_text}
        </div>
        """

    # Build errors section
    errors_html = ""
    if analysis.errors:
        errors = []
        for error in analysis.errors:
            errors.append(f'<div class="error">{error}</div>')
        errors_html = f"""
        <h2>Errors</h2>
        <div class="errors">
            {''.join(errors)}
        </div>
        """

    # Build HTML index
    file_count = len(file_reports)
    line_count = analysis.statistics.get('total_lines', 0)
    entry_point_count = len(analysis.entry_points)
    dep_count = analysis.statistics.get('dependencies', 0)
    language_count = len(analysis.detected_languages)
    project_type = analysis.project_type.value

    file_items_str = ''.join(file_items_html)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeFlow Project Analysis</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-item {{
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .file-path {{
            font-weight: 500;
            color: #2c3e50;
        }}
        .file-meta {{
            font-size: 0.85em;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .file-links {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .btn {{
            display: inline-block;
            padding: 8px 16px;
            margin: 0 5px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.85em;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #5568d3;
        }}
        .btn-secondary {{
            background: #95a5a6;
        }}
        .btn-secondary:hover {{
            background: #7f8c8d;
        }}
        .entry-points, .warnings, .errors {{
            margin: 20px 0;
        }}
        .entry-point, .warning, .error {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .entry-point {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
        }}
        .warning {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .error {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            font-size: 0.85em;
            color: #7f8c8d;
            text-align: center;
        }}
        .language-badge {{
            display: inline-block;
            padding: 3px 8px;
            margin: 0 5px;
            background: #667eea;
            color: white;
            border-radius: 3px;
            font-size: 0.75em;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CodeFlow Project Analysis</h1>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-label">Project Type</div>
                <div class="stat-value">{project_type}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Languages</div>
                <div class="stat-value">{language_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Files Analyzed</div>
                <div class="stat-value">{file_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Lines</div>
                <div class="stat-value">{line_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Entry Points</div>
                <div class="stat-value">{entry_point_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Dependencies</div>
                <div class="stat-value">{dep_count}</div>
            </div>
        </div>

        <h2>Source Files</h2>
        <ul class="file-list">
            {file_items_str}
        </ul>

        {entry_points_html}
        {warnings_html}
        {errors_html}

        <div class="footer">
            <p>Generated by CodeFlow | <a href="project_analysis.json">View raw analysis JSON</a></p>
        </div>
    </div>
</body>
</html>
"""

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def analyze_source(source, output_dir):
    """Analyze a source file using the appropriate analyzer.

    Args:
        source: Path to source file (.py, .rs, .md, etc.)
        output_dir: Output directory for reports

    Returns:
        Path to the generated HTML report.
    """
    extension = Path(source).suffix.lower()
    analyzer = get_analyzer(extension)

    if analyzer:
        analyzer_name = analyzer.name
    else:
        analyzer_name = "unknown"

    print(f"Analyzing {source} (using {analyzer_name})...")
    html_file, json_file, docx_file, result = ReportGenerator.generate_report(source, output_dir)
    print("Analysis complete!")
    print(f"  HTML report: {html_file}")
    print(f"  JSON export: {json_file}")
    if docx_file:
        print(f"  Word document: {docx_file}")
    print(f"  Functions analyzed: {len(result.functions)}")
    for label, messages in (("Errors", result.errors), ("Warnings", result.warnings)):
        if messages:
            print(f"  {label}: {len(messages)}")
            for message in messages:
                print(f"    - {message}")
    return Path(html_file)

def analyze_project(project_root, output_dir):
    """Analyze a project directory using project discovery.

    Args:
        project_root: Path to project root directory
        output_dir: Output directory for reports

    Returns:
        Path to the generated project report (index.html).
    """
    root = Path(project_root)
    if not root.is_dir():
        raise ValueError(f"Not a directory: {project_root}")

    print(f"Discovering project structure at {project_root}...")

    manager = ProjectDiscoveryManager()
    analysis = manager.discover(str(root))

    # Generate output directory
    if not output_dir:
        output_dir = str(root / "codeflow_reports")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Write project analysis JSON
    json_file = output_path / "project_analysis.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(analysis.to_dict(), f, indent=2)

    # Analyze each discovered source file and generate flowcharts
    file_reports = {}  # Maps relative path to (html_file, json_file, docx_file, result)
    for rel_path, file_info in analysis.files.items():
        abs_path = root / rel_path
        if abs_path.exists():
            try:
                print(f"  Analyzing {rel_path}...")
                html_file, json_file, docx_file, result = ReportGenerator.generate_report(str(abs_path), str(output_path))
                file_reports[rel_path] = (html_file, json_file, docx_file, result)
            except Exception as e:
                analysis.errors.append(f"Failed to analyze {rel_path}: {str(e)}")
                print(f"    Error: {e}")

    # Generate combined index.html report
    index_file = output_path / "index.html"
    _generate_project_index(analysis, file_reports, index_file, output_path)


    # Print summary
    print("Project discovery complete!")
    print(f"  Project type: {analysis.project_type.value}")
    print(f"  Detected languages: {', '.join(analysis.detected_languages)}")
    print(f"  Total files: {analysis.statistics.get('total_files', 0)}")
    print(f"  Total lines: {analysis.statistics.get('total_lines', 0)}")
    print(f"  Entry points: {analysis.statistics.get('entry_points', 0)}")
    print(f"  Dependencies: {analysis.statistics.get('dependencies', 0)}")
    print(f"  Unresolved references: {analysis.statistics.get('unresolved_references', 0)}")
    print(f"  Generated flowcharts: {len(file_reports)}")

    if analysis.entry_points:
        print("\n  Entry points:")
        for ep in analysis.entry_points:
            print(f"    - {ep.path} ({ep.type}, {ep.language})")

    if analysis.errors:
        print(f"\n  Errors: {len(analysis.errors)}")
        for error in analysis.errors:
            print(f"    - {error}")

    if analysis.warnings:
        print(f"\n  Warnings: {len(analysis.warnings)}")
        for warning in analysis.warnings[:5]:
            print(f"    - {warning}")
        if len(analysis.warnings) > 5:
            print(f"    ... and {len(analysis.warnings) - 5} more")

    print(f"\n  Analysis saved to: {index_file}")
    return str(index_file)

class LegacyActionParser(argparse.Action):
    """Custom action to handle legacy positional argument parsing."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

def main(argv=None):
    # First, detect if we're using legacy behavior (bare filename)
    arguments = list(sys.argv[1:] if argv is None else argv)

    # Remove 'analyze' subcommand if present (for backward compat)
    if arguments and arguments[0] == "analyze":
        arguments.pop(0)

    # Check if first argument looks like a project directory (exists and is dir)
    # or a file (has known extension)
    legacy_mode = False
    if arguments and not arguments[0].startswith('-'):
        first_arg = Path(arguments[0])
        if first_arg.is_dir():
            # Looks like a project directory - could be 'project <dir>' without 'project' keyword
            # Only treat as legacy if it doesn't look like a command
            if arguments[0] not in ['analyze', 'project']:
                legacy_mode = True
        elif first_arg.suffix.lower() in {'.py', '.rs', '.md', '.pyw'}:
            # Definitely a source file - legacy mode
            legacy_mode = True

    # Create main parser
    parser = argparse.ArgumentParser(
        prog="codeflow",
        description="Draw flowcharts from source code, projects, or Markdown specifications.",
        epilog="Examples:\n  python -m codeflow examples/python/tictactoe.py\n  python -m codeflow project examples/rust/tictactoe",
    )
    parser.add_argument("--version", action="version", version=f"CodeFlow {__version__}")

    if not legacy_mode and arguments and arguments[0] in ['analyze', 'project']:
        # New-style subcommand mode
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")

        # 'analyze' subcommand
        analyze_parser = subparsers.add_parser("analyze", help="Analyze a single source file")
        analyze_parser.add_argument("source", help="Python (.py), Rust (.rs), or Markdown (.md) file")
        analyze_parser.add_argument("--output-dir", "-o", help="Report directory (default: beside the input)")
        analyze_parser.add_argument("--open", "-O", action="store_true", help="Open the report in your browser")
        specification.add_options(analyze_parser)

        # 'project' subcommand
        project_parser = subparsers.add_parser("project", help="Analyze a project directory")
        project_parser.add_argument("directory", help="Project root directory")
        project_parser.add_argument("--output-dir", "-o", help="Report directory (default: <project>/codeflow_reports)")

        args = parser.parse_args(arguments)

        try:
            if args.command == "project":
                analyze_project(args.directory, args.output_dir)
                return 0
            elif args.command == "analyze":
                source = args.source
                output_dir = args.output_dir
                extension = Path(source).suffix.lower()
                if extension == ".md":
                    report = specification.run(args)
                else:
                    report = analyze_source(source, output_dir)
                if args.open:
                    if not webbrowser.open(report.resolve().as_uri()):
                        print("Open the HTML report in your browser using the path shown above.")
                return 0
        except (OSError, ValueError, EOFError) as exc:
            print(f"CodeFlow: {exc}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\nCodeFlow canceled.", file=sys.stderr)
            return 130
    else:
        # Legacy mode: bare filename or directory
        parser.add_argument("source", nargs="?", help="Python (.py), Rust (.rs), Markdown (.md) file, or project directory")
        parser.add_argument("--output-dir", "-o", help="Report directory (default: beside the input or <project>/codeflow_reports)")
        parser.add_argument("--open", "-O", action="store_true", help="Open the report in your browser")
        specification.add_options(parser)

        args = parser.parse_args(arguments)

        try:
            if args.source is None:
                args.source = input("File or project to examine (.py, .rs, .md, or directory): ").strip().strip('"')
            if not args.source:
                raise ValueError("Enter the path to a .py, .rs, .md file or a project directory.")

            source_path = Path(args.source)

            # Check if it's a directory (project mode)
            if source_path.is_dir():
                analyze_project(str(source_path), args.output_dir)
                return 0

            # Check if it's a file (single-file analysis mode)
            if not source_path.exists():
                raise ValueError(f"File or directory not found: {args.source}")

            extension = source_path.suffix.lower()

            if extension == ".py" or extension == ".pyw":
                if args.prose or args.no_prose or args.force:
                    raise ValueError("--prose, --no-prose, and --force are for Markdown input.")
                report = analyze_source(args.source, args.output_dir)
            elif extension == ".rs":
                if args.prose or args.no_prose or args.force:
                    raise ValueError("--prose, --no-prose, and --force are for Markdown input.")
                report = analyze_source(args.source, args.output_dir)
            elif extension == ".md":
                report = specification.run(args)
            else:
                raise ValueError("Choose a .py, .rs source file, .md specification, or a project directory.")

            if args.open:
                if not webbrowser.open(report.resolve().as_uri()):
                    print("Open the HTML report in your browser using the path shown above.")
            return 0
        except (OSError, ValueError, EOFError) as exc:
            print(f"CodeFlow: {exc}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\nCodeFlow canceled.", file=sys.stderr)
            return 130

if __name__ == "__main__":
    sys.exit(main())
