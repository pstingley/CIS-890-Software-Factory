"""CodeFlow analyzers package."""

from typing import Dict, Optional
from codeflow.analyzers.base import Analyzer
from codeflow.analyzers.python_analyzer import PythonAnalyzer
from codeflow.analyzers.rust_analyzer import RustAnalyzer

# Global registry mapping file extensions to analyzer instances
_analyzer_registry: Dict[str, Analyzer] = {}

def register_analyzer(analyzer: Analyzer) -> None:
    """Register an analyzer for its supported file extensions.

    Args:
        analyzer: An Analyzer instance to register.
    """
    for ext in analyzer.supported_extensions:
        _analyzer_registry[ext] = analyzer

def get_analyzer(extension: str) -> Optional[Analyzer]:
    """Get an analyzer for a file extension.

    Args:
        extension: File extension (e.g., '.py', '.rs', '.md').

    Returns:
        The registered Analyzer for this extension, or None if not found.
    """
    return _analyzer_registry.get(extension)

# Register built-in analyzers
_python_analyzer = PythonAnalyzer()
register_analyzer(_python_analyzer)

try:
    _rust_analyzer = RustAnalyzer()
    register_analyzer(_rust_analyzer)
except Exception as e:
    print(f"Warning: Failed to initialize Rust analyzer: {e}")

__all__ = ["Analyzer", "register_analyzer", "get_analyzer", "PythonAnalyzer", "RustAnalyzer"]
