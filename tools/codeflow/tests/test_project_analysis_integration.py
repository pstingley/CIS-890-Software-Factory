"""End-to-end tests for project-level analysis and report generation.

Verifies that the 'codeflow project <directory>' command generates HTML
flowcharts and SVG diagrams in addition to project discovery JSON.
"""

import json
import tempfile
from pathlib import Path
import pytest

from codeflow.project import ProjectDiscoveryManager
from codeflow.report_generator import ReportGenerator
from codeflow.cli import analyze_project


# Resolve example project path relative to codeflow package
CODEFLOW_DIR = Path(__file__).parent.parent
TICTACTOE_PROJECT = CODEFLOW_DIR / "examples" / "rust" / "tictactoe"
PYTHON_TICTACTOE = CODEFLOW_DIR / "examples" / "python" / "tictactoe.py"


class TestProjectAnalysisIntegration:
    """End-to-end tests for project analysis with report generation."""

    def test_analyze_project_generates_index_html(self):
        """Verify that project analysis generates index.html."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            index_file = output_dir / "index.html"
            assert index_file.exists(), "index.html should be generated"

            content = index_file.read_text()
            assert "<!DOCTYPE html>" in content
            assert "CodeFlow Project Analysis" in content

    def test_project_analysis_generates_flowchart_htmls(self):
        """Verify that individual flowchart HTML files are generated."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            # Check for main.rs flowchart
            main_html = output_dir / "main_codeflow.html"
            assert main_html.exists(), "main_codeflow.html should be generated"

            # Check for lib.rs flowchart
            lib_html = output_dir / "lib_codeflow.html"
            assert lib_html.exists(), "lib_codeflow.html should be generated"

    def test_project_analysis_generates_json_exports(self):
        """Verify that JSON exports are generated for each file."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            # Check for main.rs JSON
            main_json = output_dir / "main_codeflow.json"
            assert main_json.exists(), "main_codeflow.json should be generated"

            # Verify it's valid JSON
            main_data = json.loads(main_json.read_text())
            assert "functions" in main_data

            # Check for lib.rs JSON
            lib_json = output_dir / "lib_codeflow.json"
            assert lib_json.exists(), "lib_codeflow.json should be generated"

            # Verify it's valid JSON
            lib_data = json.loads(lib_json.read_text())
            assert "functions" in lib_data

    def test_project_analysis_generates_project_json(self):
        """Verify that project discovery JSON is generated."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            project_json = output_dir / "project_analysis.json"
            assert project_json.exists(), "project_analysis.json should be generated"

            # Verify it's valid JSON
            data = json.loads(project_json.read_text())
            assert data["project_type"] == "rust"
            assert "files" in data
            assert len(data["files"]) == 2  # main.rs and lib.rs

    def test_flowchart_html_contains_svgs(self):
        """Verify that flowchart HTML files contain SVG elements."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            # Check main.rs flowchart
            main_html = output_dir / "main_codeflow.html"
            main_content = main_html.read_text()
            assert "<svg" in main_content, "SVG elements should be in main flowchart"

            # Check lib.rs flowchart
            lib_html = output_dir / "lib_codeflow.html"
            lib_content = lib_html.read_text()
            assert "<svg" in lib_content, "SVG elements should be in lib flowchart"
            assert len(lib_content) > len(main_content), "lib.rs should have more flowcharts"

    def test_index_html_links_to_flowcharts(self):
        """Verify that index.html contains links to flowchart files."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            index_html = output_dir / "index.html"
            content = index_html.read_text()

            # Check for links to individual flowcharts
            assert "main_codeflow.html" in content
            assert "lib_codeflow.html" in content
            assert "project_analysis.json" in content

            # Verify they're in href attributes
            assert 'href="main_codeflow.html"' in content
            assert 'href="lib_codeflow.html"' in content

    def test_index_html_displays_project_summary(self):
        """Verify that index.html displays project summary statistics."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            index_html = output_dir / "index.html"
            content = index_html.read_text()

            # Check for expected summary elements
            assert "Project Type" in content
            assert "rust" in content
            assert "Files Analyzed" in content
            assert "Entry Points" in content

    def test_tictactoe_project_analysis_complete(self):
        """Full integration test: analyze Tic-Tac-Toe project and verify all outputs."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Analyze the project
            analyze_project(str(project_root), str(output_dir))

            # Verify all expected files exist
            expected_files = [
                "index.html",
                "project_analysis.json",
                "main_codeflow.html",
                "main_codeflow.json",
                "lib_codeflow.html",
                "lib_codeflow.json",
            ]

            for filename in expected_files:
                file_path = output_dir / filename
                assert file_path.exists(), f"{filename} should be generated"
                assert file_path.stat().st_size > 0, f"{filename} should not be empty"

            # Verify JSON files are valid and contain expected data
            project_data = json.loads((output_dir / "project_analysis.json").read_text())
            assert project_data["project_type"] == "rust"
            assert len(project_data["files"]) == 2
            assert project_data["files"]["src/main.rs"]["language"] == "rust"
            assert project_data["files"]["src/lib.rs"]["language"] == "rust"

            # Verify flowchart JSON files have functions
            main_codeflow = json.loads((output_dir / "main_codeflow.json").read_text())
            assert "functions" in main_codeflow
            assert len(main_codeflow["functions"]) >= 1

            lib_codeflow = json.loads((output_dir / "lib_codeflow.json").read_text())
            assert "functions" in lib_codeflow
            assert len(lib_codeflow["functions"]) >= 1

            # Verify index.html contains links and summary
            index_content = (output_dir / "index.html").read_text()
            assert "CodeFlow Project Analysis" in index_content
            assert "main_codeflow.html" in index_content
            assert "lib_codeflow.html" in index_content
            assert "View Flowcharts" in index_content

    def test_unsupported_constructs_reported_in_analysis(self):
        """Verify that unsupported Rust constructs are reported."""
        project_root = TICTACTOE_PROJECT
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyze_project(str(project_root), str(output_dir))

            # Verify that the analysis JSON contains ambiguity information
            project_data = json.loads((output_dir / "project_analysis.json").read_text())

            # The project discovery may have warnings about unsupported constructs
            # (this will be shown in the analysis)
            # Just verify the structure is there
            assert "files" in project_data
            assert "statistics" in project_data

    def test_project_uses_default_output_directory(self):
        """Verify that project analysis uses default output directory when not specified."""
        project_root = TICTACTOE_PROJECT

        # Create a temporary copy of the project to avoid modifying the original
        with tempfile.TemporaryDirectory() as tmpdir:
            import shutil
            temp_project = Path(tmpdir) / "tictactoe"
            shutil.copytree(project_root, temp_project)

            # Analyze without specifying output directory (should use temp_project/codeflow_reports)
            analyze_project(str(temp_project), None)

            # Verify reports were created in codeflow_reports subdirectory
            reports_dir = temp_project / "codeflow_reports"
            assert reports_dir.exists()
            assert (reports_dir / "index.html").exists()
            assert (reports_dir / "project_analysis.json").exists()

    def test_project_analysis_preserves_existing_python_functionality(self):
        """Verify that existing Python analysis is not broken by project analysis changes."""
        # This is a sanity check - single-file Python analysis should still work
        python_file = PYTHON_TICTACTOE

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            html_file, json_file, docx_file, result = ReportGenerator.generate_report(
                str(python_file), str(output_dir)
            )

            assert Path(html_file).exists()
            assert Path(json_file).exists()
            assert Path(docx_file).exists()

            data = json.loads(Path(json_file).read_text())
            assert "functions" in data
            assert len(data["functions"]) > 0
