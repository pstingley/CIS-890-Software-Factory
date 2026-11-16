"""Command-line interface for CodeFlow."""

import argparse
from pathlib import Path
import sys
import webbrowser

from codeflow import __version__, specification
from codeflow.report_generator import ReportGenerator
from codeflow.analyzers import get_analyzer

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

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="codeflow",
        description="Draw a flowchart from source code or a Markdown specification.",
        epilog="Example: python -m codeflow analyze examples/python/tictactoe.py",
    )
    parser.add_argument("source", nargs="?", help="Python (.py), Rust (.rs), or Markdown (.md) file")
    parser.add_argument("--output-dir", "-o", help="Report directory (default: beside the input)")
    parser.add_argument("--open", "-O", action="store_true", help="Open the report in your browser")
    parser.add_argument("--version", action="version", version=f"CodeFlow {__version__}")
    specification.add_options(parser)

    # Keep the original 'analyze FILE' form while also accepting a bare filename.
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "analyze":
        arguments.pop(0)
    args = parser.parse_args(arguments)

    try:
        if args.source is None:
            args.source = input("File to examine (.py, .rs, or .md): ").strip().strip('"')
        if not args.source:
            raise ValueError("Enter the path to a .py, .rs, or .md file.")
        extension = Path(args.source).suffix.lower()

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
            raise ValueError("Choose a .py, .rs source file or a .md specification.")
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
