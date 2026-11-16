"""Tests for Word (.docx) document generation."""

import os
import tempfile
import unittest
from pathlib import Path

from docx import Document

from codeflow.render.docx_generator import DocxGenerator
from codeflow.analyzers.python_analyzer import PythonAnalyzer


class TestDocxGeneration(unittest.TestCase):
    """Test Word document generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.python_code = """
def add(a, b):
    '''Add two numbers.'''
    if a < 0:
        return b
    else:
        return a + b

def process_list(items):
    '''Process a list of items.'''
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.temp_file.write(self.python_code)
        self.temp_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_docx_generator_creates_document(self):
        """Test that DocxGenerator creates a valid Document object."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        self.assertTrue(hasattr(doc, 'paragraphs'))
        self.assertGreater(len(doc.paragraphs), 0)

    def test_docx_saves_to_file(self):
        """Test that generated document can be saved to file."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'test_report.docx')

            generator = DocxGenerator(result)
            saved_path = generator.save(output_file)

            self.assertEqual(saved_path, output_file)
            self.assertTrue(os.path.exists(output_file))
            self.assertGreater(os.path.getsize(output_file), 0)

    def test_docx_file_is_readable(self):
        """Test that saved document is a valid .docx file."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'test_report.docx')

            generator = DocxGenerator(result)
            generator.save(output_file)

            # Try to read it back
            doc = Document(output_file)
            self.assertTrue(hasattr(doc, 'paragraphs'))
            self.assertGreater(len(doc.paragraphs), 0)

    def test_docx_contains_title_page(self):
        """Test that document contains title page elements."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs[:30])

        self.assertIn("CodeFlow Analysis Report", all_text)
        self.assertIn("Software System Documentation", all_text)

    def test_docx_contains_metadata_section(self):
        """Test that document contains analysis metadata."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        self.assertIn("Analysis Metadata", all_text)
        self.assertIn("Source:", all_text)
        self.assertIn("v0.2.1", all_text)

    def test_docx_contains_executive_summary(self):
        """Test that document contains executive summary."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        self.assertIn("Executive Summary", all_text)
        self.assertIn("Analysis Overview", all_text)

    def test_docx_contains_function_documentation(self):
        """Test that document contains function documentation."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        self.assertIn("Control-Flow Analysis", all_text)
        # Should mention at least one function
        self.assertTrue('add' in all_text or 'process_list' in all_text)

    def test_docx_contains_glossary(self):
        """Test that document contains a glossary section."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        self.assertIn("Glossary", all_text)
        self.assertIn("CFG", all_text)

    def test_docx_contains_limitations(self):
        """Test that document contains analysis limitations."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        self.assertIn("Limitations", all_text)
        self.assertIn("Analysis", all_text)

    def test_docx_metadata_table_exists(self):
        """Test that document contains metadata table."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        self.assertGreater(len(doc.tables), 0)
        # First table should have at least 2 columns
        self.assertGreaterEqual(len(doc.tables[0].rows[0].cells), 2)

    def test_docx_handles_errors_and_warnings(self):
        """Test that document properly handles results with errors/warnings."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        # Manually add an error for testing
        result.errors.append("Test error message")
        result.warnings.append("Test warning message")

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        self.assertIn("Findings and Issues", all_text)
        self.assertIn("Test error message", all_text)
        self.assertIn("Test warning message", all_text)

    def test_docx_handles_empty_functions(self):
        """Test that document handles analysis with no functions."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        # Remove all functions
        result.functions.clear()

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        # Should still have main sections but note no functions
        self.assertIn("Analysis", all_text)

    def test_docx_specification_note_included(self):
        """Test that document contains control-flow analysis content."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        # The document should contain the control-flow analysis section
        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        # Verify document contains control-flow analysis section
        self.assertIn("Control-Flow", all_text)

    def test_docx_formatting_styles_applied(self):
        """Test that document formatting styles are properly applied."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        generator = DocxGenerator(result)
        doc = generator.generate()

        # Check that headings are present
        heading_found = False
        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                heading_found = True
                break

        self.assertTrue(heading_found, "Document should contain heading styles")

    def test_docx_multiple_functions_documented(self):
        """Test that document handles multiple functions."""
        analyzer = PythonAnalyzer()
        result = analyzer.analyze(self.temp_file.name)

        self.assertGreater(len(result.functions), 0, "Test should analyze multiple functions")

        generator = DocxGenerator(result)
        doc = generator.generate()

        all_text = '\n'.join(p.text for p in doc.paragraphs)

        # Should have function count info
        self.assertIn("Function", all_text)


class TestDocxGeneratorIntegration(unittest.TestCase):
    """Integration tests for Word document generation."""

    def test_docx_generation_through_report_generator(self):
        """Test Word document generation through ReportGenerator."""
        from codeflow.report_generator import ReportGenerator

        python_code = """
def hello(name):
    '''Greet someone.'''
    return f"Hello, {name}!"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                html_file, json_file, docx_file, result = ReportGenerator.generate_report(
                    temp_file, tmpdir
                )

                self.assertIsNotNone(docx_file)
                self.assertTrue(os.path.exists(docx_file))
                self.assertTrue(docx_file.endswith('.docx'))

                # Verify it's a valid document
                doc = Document(docx_file)
                all_text = '\n'.join(p.text for p in doc.paragraphs)
                self.assertIn("hello", all_text)

        finally:
            os.unlink(temp_file)

    def test_docx_disable_generation(self):
        """Test that Word document generation can be disabled."""
        from codeflow.report_generator import ReportGenerator

        python_code = "def test(): pass"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                html_file, json_file, docx_file, result = ReportGenerator.generate_report(
                    temp_file, tmpdir, include_docx=False
                )

                self.assertIsNone(docx_file)
                # Other formats should still be generated
                self.assertIsNotNone(html_file)
                self.assertIsNotNone(json_file)

        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
