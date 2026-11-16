"""Report generator - orchestrates the analysis and report generation."""

import os
from codeflow.analyzers import get_analyzer
from codeflow.render.html_generator import HTMLReportGenerator
from codeflow.export.json_exporter import JSONExporter

class ReportGenerator:
    """Orchestrates source analysis and report generation."""

    @staticmethod
    def generate_report(source_file: str, output_dir: str = None) -> tuple:
        """
        Analyze a source file and generate reports.

        Args:
            source_file: Path to source file (supports .py, .rs, .md, etc.)
            output_dir: Directory to save reports (default: same as source)

        Returns:
            Tuple of (html_file, json_file, result)
        """
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")

        if output_dir is None:
            output_dir = os.path.dirname(source_file) or "."

        os.makedirs(output_dir, exist_ok=True)

        # Get file extension and find appropriate analyzer
        _, file_ext = os.path.splitext(source_file)
        analyzer = get_analyzer(file_ext)

        if analyzer is None:
            raise ValueError(f"No analyzer available for file extension: {file_ext}")

        # Analyze source file using appropriate analyzer
        result = analyzer.analyze(source_file)

        # Generate base name for output files
        base_name = os.path.splitext(os.path.basename(source_file))[0]

        # Generate HTML report
        html_generator = HTMLReportGenerator(result)
        html_content = html_generator.generate()
        html_file = os.path.join(output_dir, f"{base_name}_codeflow.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Generate JSON export
        json_file = os.path.join(output_dir, f"{base_name}_codeflow.json")
        JSONExporter.export_to_file(result, json_file)

        return html_file, json_file, result
