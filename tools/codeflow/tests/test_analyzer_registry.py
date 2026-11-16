"""Tests for the analyzer registry and routing system."""

import pytest
from codeflow.analyzers import get_analyzer, register_analyzer, Analyzer
from codeflow.analyzers.python_analyzer import PythonAnalyzer

class TestAnalyzerRegistry:
    """Test cases for analyzer registry functionality."""

    def test_python_analyzer_registered_for_py(self):
        """Test that PythonAnalyzer is registered for .py extension."""
        analyzer = get_analyzer(".py")
        assert analyzer is not None
        assert isinstance(analyzer, PythonAnalyzer)
        assert analyzer.name == "PythonAnalyzer"

    def test_python_analyzer_registered_for_pyw(self):
        """Test that PythonAnalyzer is registered for .pyw extension."""
        analyzer = get_analyzer(".pyw")
        assert analyzer is not None
        assert isinstance(analyzer, PythonAnalyzer)
        assert analyzer.name == "PythonAnalyzer"

    def test_unsupported_extension_returns_none(self):
        """Test that get_analyzer returns None for unsupported extensions."""
        analyzer = get_analyzer(".rs")
        assert analyzer is None

        analyzer = get_analyzer(".md")
        assert analyzer is None

        analyzer = get_analyzer(".go")
        assert analyzer is None

    def test_python_analyzer_properties(self):
        """Test that PythonAnalyzer has required properties."""
        analyzer = get_analyzer(".py")
        assert analyzer.name == "PythonAnalyzer"
        assert analyzer.version == "0.2.0"
        assert ".py" in analyzer.supported_extensions
        assert ".pyw" in analyzer.supported_extensions

    def test_python_analyzer_analyze_method(self):
        """Test that PythonAnalyzer.analyze returns AnalysisResult."""
        import os
        import tempfile

        analyzer = get_analyzer(".py")

        # Create a simple Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def foo():\n    x = 1\n    return x\n')
            temp_file = f.name

        try:
            result = analyzer.analyze(temp_file)
            assert result is not None
            assert hasattr(result, 'functions')
            assert hasattr(result, 'file_path')
        finally:
            os.unlink(temp_file)

    def test_analyzer_is_singleton_per_extension(self):
        """Test that the same analyzer instance is returned for multiple lookups."""
        analyzer1 = get_analyzer(".py")
        analyzer2 = get_analyzer(".py")
        assert analyzer1 is analyzer2  # Same object instance

class TestAnalyzerInterface:
    """Test cases for Analyzer ABC interface."""

    def test_analyzer_abc_cannot_be_instantiated(self):
        """Test that Analyzer ABC cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Analyzer()

    def test_python_analyzer_implements_analyzer(self):
        """Test that PythonAnalyzer implements Analyzer interface."""
        analyzer = get_analyzer(".py")
        assert isinstance(analyzer, Analyzer)

        # Verify all required methods/properties exist
        assert callable(analyzer.analyze)
        assert hasattr(analyzer, 'supported_extensions')
        assert hasattr(analyzer, 'name')
        assert hasattr(analyzer, 'version')

class TestCLIRouting:
    """Test cases for CLI file routing through analyzer registry."""

    def test_cli_routing_logic(self):
        """Test the logic used in CLI for routing files to analyzers."""
        import os

        test_cases = [
            ("example.py", True),      # Should find analyzer
            ("example.pyw", True),     # Should find analyzer
            ("example.rs", False),     # No analyzer yet
            ("example.md", False),     # No analyzer yet
            ("example.js", False),     # No analyzer
        ]

        for filename, should_have_analyzer in test_cases:
            ext = os.path.splitext(filename)[1]
            analyzer = get_analyzer(ext)

            if should_have_analyzer:
                assert analyzer is not None, f"Expected analyzer for {filename}"
            else:
                assert analyzer is None, f"Unexpected analyzer for {filename}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
