"""Abstract base class for language-specific analyzers."""

from abc import ABC, abstractmethod
from typing import List
from codeflow.graph import AnalysisResult

class Analyzer(ABC):
    """Abstract base class for language-specific code analyzers.

    Each analyzer inherits from this class and implements support for analyzing
    a specific file type (e.g., Python .py files, Rust .rs files, Markdown specifications).
    """

    @abstractmethod
    def analyze(self, source_path: str) -> AnalysisResult:
        """Analyze a source file and return the control-flow analysis result.

        Args:
            source_path: Absolute or relative path to the source file to analyze.

        Returns:
            AnalysisResult containing the control-flow graph(s) and metadata.
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of file extensions this analyzer supports (e.g., ['.py', '.pyw']).

        Returns:
            List of file extensions (including the dot prefix).
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable name of this analyzer (e.g., 'PythonAnalyzer').

        Returns:
            Analyzer name string.
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version string for this analyzer (e.g., '1.0.0').

        Returns:
            Version string.
        """
        pass
