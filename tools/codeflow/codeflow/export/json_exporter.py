"""JSON exporter - exports CFG to JSON format."""

import json
from codeflow.graph import AnalysisResult

class JSONExporter:
    """Exports analysis results to JSON format."""

    @staticmethod
    def export(result: AnalysisResult) -> str:
        """Export analysis result to JSON string."""
        data = result.to_dict()
        return json.dumps(data, indent=2)

    @staticmethod
    def export_to_file(result: AnalysisResult, file_path: str) -> None:
        """Export analysis result to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(JSONExporter.export(result))
