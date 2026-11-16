"""Command-line interface for CodeFlow."""

import argparse
from pathlib import Path
import sys
import webbrowser
import json

from codeflow import __version__, specification
from codeflow.report_generator import ReportGenerator
from codeflow.analyzers import get_analyzer
from codeflow.project import ProjectDiscoveryManager

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
    html_file, json_file, result = ReportGenerator.generate_report(source, output_dir)
    print("Analysis complete!")
    print(f"  HTML report: {html_file}")
    print(f"  JSON export: {json_file}")
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
        Path to the generated project report.
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

    # Print summary
    print("Project discovery complete!")
    print(f"  Project type: {analysis.project_type.value}")
    print(f"  Detected languages: {', '.join(analysis.detected_languages)}")
    print(f"  Total files: {analysis.statistics.get('total_files', 0)}")
    print(f"  Total lines: {analysis.statistics.get('total_lines', 0)}")
    print(f"  Entry points: {analysis.statistics.get('entry_points', 0)}")
    print(f"  Dependencies: {analysis.statistics.get('dependencies', 0)}")
    print(f"  Unresolved references: {analysis.statistics.get('unresolved_references', 0)}")

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

    print(f"\n  Analysis saved to: {json_file}")
    return json_file

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
