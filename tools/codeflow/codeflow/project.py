"""Project-level discovery and analysis infrastructure.

Provides shared project discovery for Python, Rust, and PHP projects,
including file discovery, entry point identification, and dependency mapping.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import json
import re

class ProjectType(Enum):
    """Supported project types."""
    PYTHON = "python"
    RUST = "rust"
    PHP = "php"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class AmbiguityCategory(Enum):
    """Categories for explicit ambiguity reporting."""
    DYNAMIC_BEHAVIOR = "dynamic_behavior"
    UNSUPPORTED_SYNTAX = "unsupported_syntax"
    PARSING_ERROR = "parsing_error"
    INCOMPLETE_ANALYSIS = "incomplete_analysis"

@dataclass
class SourceReference:
    """Reference to a source file and line number."""
    file_path: str
    line_number: int
    source_code: str = ""

@dataclass
class Dependency:
    """A dependency relationship between files."""
    source_file: str
    target_file: str
    dependency_type: str  # "import", "include", "require", "mod", "use", etc.
    line_number: Optional[int] = None
    resolved: bool = True  # Whether the target file was found
    ambiguity_flags: List[str] = field(default_factory=list)

@dataclass
class ProjectFile:
    """Information about a file within a project."""
    path: str  # Relative to project root
    absolute_path: str
    language: str  # "python", "rust", "php"
    line_count: int
    is_entry_point: bool = False
    entry_point_type: Optional[str] = None  # "binary", "library", "index", "script", etc.
    dependencies: List[Dependency] = field(default_factory=list)
    external_references: List[str] = field(default_factory=list)  # Unresolved references

@dataclass
class ProjectEntryPoint:
    """An entry point for a project."""
    path: str  # Relative to project root
    description: str  # Human-readable description
    type: str  # "binary", "library", "index", "script", "class", etc.
    language: str

@dataclass
class ProjectAnalysis:
    """Results of project-level analysis."""
    project_root: str
    project_type: ProjectType
    detected_languages: List[str]
    files: Dict[str, ProjectFile] = field(default_factory=dict)
    entry_points: List[ProjectEntryPoint] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    ambiguity_flags: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "schema_version": "2.0",
            "project_root": self.project_root,
            "project_type": self.project_type.value,
            "detected_languages": self.detected_languages,
            "files": {
                path: {
                    "language": f.language,
                    "lines": f.line_count,
                    "is_entry_point": f.is_entry_point,
                    "entry_point_type": f.entry_point_type,
                    "dependencies": [
                        {
                            "target": d.target_file,
                            "type": d.dependency_type,
                            "line": d.line_number,
                            "resolved": d.resolved,
                            "ambiguity_flags": d.ambiguity_flags,
                        }
                        for d in f.dependencies
                    ],
                    "external_references": f.external_references,
                }
                for path, f in self.files.items()
            },
            "entry_points": [
                {
                    "path": ep.path,
                    "description": ep.description,
                    "type": ep.type,
                    "language": ep.language,
                }
                for ep in self.entry_points
            ],
            "statistics": self.statistics,
            "errors": self.errors,
            "warnings": self.warnings,
            "ambiguity_flags": self.ambiguity_flags,
        }

class ProjectDiscoverer(ABC):
    """Abstract base class for language-specific project discoverers."""

    @abstractmethod
    def detect(self, project_root: str) -> bool:
        """Detect if a project root contains this language.

        Args:
            project_root: Path to project root directory

        Returns:
            True if this language is detected, False otherwise
        """
        pass

    @abstractmethod
    def discover(self, project_root: str) -> ProjectAnalysis:
        """Discover project structure, files, and dependencies.

        Args:
            project_root: Path to project root directory

        Returns:
            ProjectAnalysis with discovered files and metadata
        """
        pass

class PythonProjectDiscoverer(ProjectDiscoverer):
    """Discovers Python projects."""

    PYTHON_EXTENSIONS = {".py", ".pyw"}
    STANDARD_EXCLUSIONS = {
        "__pycache__", ".tox", ".venv", "venv", "env",
        "virtualenv", ".egg-info", "*.egg", ".pytest_cache",
        ".mypy_cache", "dist", "build"
    }

    def detect(self, project_root: str) -> bool:
        """Detect Python project by presence of .py files or setup files."""
        root = Path(project_root)

        # Check for setup.py, pyproject.toml, etc.
        config_files = {"setup.py", "pyproject.toml", "setup.cfg", "MANIFEST.in"}
        if any((root / cf).exists() for cf in config_files):
            return True

        # Check for .py files
        for py_file in root.rglob("*.py"):
            if not self._is_excluded(py_file, root):
                return True

        return False

    def discover(self, project_root: str) -> ProjectAnalysis:
        """Discover Python project structure."""
        root = Path(project_root)
        analysis = ProjectAnalysis(
            project_root=str(root),
            project_type=ProjectType.PYTHON,
            detected_languages=["python"],
        )

        # Discover all Python files
        py_files: List[Path] = []
        for py_file in root.rglob("*.py"):
            if not self._is_excluded(py_file, root):
                py_files.append(py_file)

        # Analyze each file
        import_map: Dict[str, Set[str]] = {}  # file -> set of imported modules

        for py_file in py_files:
            rel_path = py_file.relative_to(root).as_posix()
            line_count = self._count_lines(py_file)

            pf = ProjectFile(
                path=rel_path,
                absolute_path=str(py_file),
                language="python",
                line_count=line_count,
            )

            # Parse imports from file
            imports = self._extract_imports(py_file)
            import_map[rel_path] = imports

            # Check if it's an entry point
            if rel_path in {"__main__.py", "main.py", "cli.py", "app.py"}:
                pf.is_entry_point = True
                pf.entry_point_type = "script"
                analysis.entry_points.append(ProjectEntryPoint(
                    path=rel_path,
                    description=f"Python entry point: {rel_path}",
                    type="script",
                    language="python",
                ))
            elif self._has_main_block(py_file):
                pf.is_entry_point = True
                pf.entry_point_type = "script"

            analysis.files[rel_path] = pf

        # Resolve dependencies
        for source_file, imports in import_map.items():
            for imp in imports:
                # Try to resolve import to file
                target_file = self._resolve_python_import(imp, root, py_files)
                if target_file:
                    dep = Dependency(
                        source_file=source_file,
                        target_file=target_file.relative_to(root).as_posix(),
                        dependency_type="import",
                        resolved=True,
                    )
                    if source_file in analysis.files:
                        analysis.files[source_file].dependencies.append(dep)
                    analysis.dependencies.append(dep)
                else:
                    # Unresolved import (external package)
                    if source_file in analysis.files:
                        analysis.files[source_file].external_references.append(imp)

        # Statistics
        analysis.statistics = {
            "total_files": len(analysis.files),
            "total_lines": sum(f.line_count for f in analysis.files.values()),
            "entry_points": len(analysis.entry_points),
            "dependencies": len(analysis.dependencies),
            "unresolved_references": sum(
                len(f.external_references) for f in analysis.files.values()
            ),
        }

        return analysis

    def _is_excluded(self, file_path: Path, root: Path) -> bool:
        """Check if a file should be excluded."""
        for part in file_path.relative_to(root).parts:
            if part in self.STANDARD_EXCLUSIONS:
                return True
        return False

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return len(f.readlines())
        except Exception:
            return 0

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from a Python file."""
        imports = set()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Simple regex patterns for imports
            import_pattern = r"^\s*from\s+(\S+)\s+import|^\s*import\s+(\S+)"
            for line in content.split("\n"):
                match = re.match(import_pattern, line)
                if match:
                    module = match.group(1) or match.group(2)
                    # Extract root module name
                    root_module = module.split(".")[0]
                    imports.add(root_module)
        except Exception:
            pass

        return imports

    def _has_main_block(self, file_path: Path) -> bool:
        """Check if a Python file has a __main__ block."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return 'if __name__ == "__main__"' in content
        except Exception:
            return False

    def _resolve_python_import(self, module_name: str, root: Path,
                               py_files: List[Path]) -> Optional[Path]:
        """Try to resolve a Python import to a file in the project."""
        # Look for module_name.py or module_name/__init__.py
        for py_file in py_files:
            rel_path = py_file.relative_to(root)
            # Match module.py
            if rel_path.stem == module_name:
                return py_file
            # Match module/__init__.py
            if rel_path.parent.name == module_name and rel_path.name == "__init__.py":
                return py_file
        return None

class RustProjectDiscoverer(ProjectDiscoverer):
    """Discovers Rust projects."""

    def detect(self, project_root: str) -> bool:
        """Detect Rust project by presence of Cargo.toml."""
        return (Path(project_root) / "Cargo.toml").exists()

    def discover(self, project_root: str) -> ProjectAnalysis:
        """Discover Rust project structure."""
        root = Path(project_root)
        analysis = ProjectAnalysis(
            project_root=str(root),
            project_type=ProjectType.RUST,
            detected_languages=["rust"],
        )

        cargo_toml = root / "Cargo.toml"
        if not cargo_toml.exists():
            analysis.errors.append(f"Cargo.toml not found at {cargo_toml}")
            return analysis

        # Parse Cargo.toml
        cargo_data = self._parse_cargo_toml(cargo_toml)

        # Discover Rust source files
        src_root = root / "src"
        if not src_root.exists():
            analysis.errors.append(f"src/ directory not found at {src_root}")
            return analysis

        rs_files: List[Path] = []
        for rs_file in src_root.rglob("*.rs"):
            rs_files.append(rs_file)

        # Create ProjectFile entries
        for rs_file in rs_files:
            rel_path = rs_file.relative_to(root).as_posix()
            line_count = self._count_lines(rs_file)

            pf = ProjectFile(
                path=rel_path,
                absolute_path=str(rs_file),
                language="rust",
                line_count=line_count,
            )

            # Check if it's an entry point
            if rel_path == "src/main.rs":
                pf.is_entry_point = True
                pf.entry_point_type = "binary"
                analysis.entry_points.append(ProjectEntryPoint(
                    path=rel_path,
                    description="Rust binary entry point (main.rs)",
                    type="binary",
                    language="rust",
                ))
            elif rel_path == "src/lib.rs":
                pf.is_entry_point = True
                pf.entry_point_type = "library"
                analysis.entry_points.append(ProjectEntryPoint(
                    path=rel_path,
                    description="Rust library entry point (lib.rs)",
                    type="library",
                    language="rust",
                ))

            analysis.files[rel_path] = pf

        # Extract module declarations (mod statements)
        for rs_file in rs_files:
            rel_path = rs_file.relative_to(root).as_posix()
            modules = self._extract_rust_modules(rs_file)

            for mod_name in modules:
                # Try to find the module file
                # Could be mod_name.rs or mod_name/mod.rs
                candidates = [
                    rs_file.parent / f"{mod_name}.rs",
                    rs_file.parent / mod_name / "mod.rs",
                ]

                target_file = None
                for candidate in candidates:
                    if candidate.exists():
                        target_file = candidate.relative_to(root).as_posix()
                        break

                dep = Dependency(
                    source_file=rel_path,
                    target_file=target_file or f"{mod_name}.rs",
                    dependency_type="mod",
                    resolved=target_file is not None,
                )

                if rel_path in analysis.files:
                    analysis.files[rel_path].dependencies.append(dep)
                analysis.dependencies.append(dep)

        # Statistics
        analysis.statistics = {
            "total_files": len(analysis.files),
            "total_lines": sum(f.line_count for f in analysis.files.values()),
            "entry_points": len(analysis.entry_points),
            "dependencies": len(analysis.dependencies),
            "unresolved_references": sum(
                len(f.external_references) for f in analysis.files.values()
            ),
        }

        return analysis

    def _parse_cargo_toml(self, cargo_toml: Path) -> dict:
        """Parse Cargo.toml (simple TOML parsing for key fields)."""
        data = {
            "package_name": None,
            "version": None,
            "bins": [],
            "lib": None,
        }

        try:
            with open(cargo_toml, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple regex extraction (not full TOML parsing)
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                data["package_name"] = name_match.group(1)

            # Find [[bin]] sections
            bin_pattern = r'\[\[bin\]\]\s+(?:name\s*=\s*["\']([^"\']+)["\'].*?)?path\s*=\s*["\']([^"\']+)["\']'
            for match in re.finditer(bin_pattern, content, re.MULTILINE | re.DOTALL):
                name = match.group(1)
                path = match.group(2)
                data["bins"].append({"name": name, "path": path})

            # Check for [lib]
            if "[lib]" in content:
                lib_path_match = re.search(r'\[lib\].*?path\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
                if lib_path_match:
                    data["lib"] = {"path": lib_path_match.group(1)}
        except Exception as e:
            pass

        return data

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return len(f.readlines())
        except Exception:
            return 0

    def _extract_rust_modules(self, file_path: Path) -> Set[str]:
        """Extract module declarations from a Rust file."""
        modules = set()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Match mod declarations
            mod_pattern = r"^\s*(?:pub\s+)?mod\s+(\w+)(?:\s*{|;)"
            for match in re.finditer(mod_pattern, content, re.MULTILINE):
                modules.add(match.group(1))
        except Exception:
            pass

        return modules

class PHPProjectDiscoverer(ProjectDiscoverer):
    """Discovers PHP projects."""

    def detect(self, project_root: str) -> bool:
        """Detect PHP project by presence of .php files or composer.json."""
        root = Path(project_root)

        # Check for composer.json
        if (root / "composer.json").exists():
            return True

        # Check for .php files
        for php_file in root.rglob("*.php"):
            if not self._is_excluded(php_file, root):
                return True

        return False

    def discover(self, project_root: str) -> ProjectAnalysis:
        """Discover PHP project structure."""
        root = Path(project_root)
        analysis = ProjectAnalysis(
            project_root=str(root),
            project_type=ProjectType.PHP,
            detected_languages=["php"],
        )

        # Discover all PHP files
        php_files: List[Path] = []
        for php_file in root.rglob("*.php"):
            if not self._is_excluded(php_file, root):
                php_files.append(php_file)

        # Parse composer.json if present
        composer_data = {}
        composer_json = root / "composer.json"
        if composer_json.exists():
            composer_data = self._parse_composer_json(composer_json)

        # Analyze each PHP file
        include_map: Dict[str, List[Tuple[str, int]]] = {}  # file -> [(include, line)]

        for php_file in php_files:
            rel_path = php_file.relative_to(root).as_posix()
            line_count = self._count_lines(php_file)

            pf = ProjectFile(
                path=rel_path,
                absolute_path=str(php_file),
                language="php",
                line_count=line_count,
            )

            # Extract include/require statements
            includes = self._extract_includes(php_file)
            include_map[rel_path] = includes

            # Check if it's an entry point
            if rel_path in {"index.php", "public/index.php", "web/app.php"}:
                pf.is_entry_point = True
                pf.entry_point_type = "index"
                analysis.entry_points.append(ProjectEntryPoint(
                    path=rel_path,
                    description=f"PHP entry point: {rel_path}",
                    type="index",
                    language="php",
                ))
            elif rel_path.endswith((".php", ".phtml")) and rel_path not in {"composer.json"}:
                # Check for framework entry points
                if any(x in rel_path for x in ["route", "bootstrap", "app.php", "index.php"]):
                    pf.is_entry_point = True
                    pf.entry_point_type = "script"

            analysis.files[rel_path] = pf

        # Resolve dependencies (include/require)
        for source_file, includes in include_map.items():
            for inc_path, line_no in includes:
                # Try to resolve include to file
                target_file = self._resolve_php_include(inc_path, Path(source_file).parent, root, php_files)
                if target_file:
                    dep = Dependency(
                        source_file=source_file,
                        target_file=target_file.relative_to(root).as_posix(),
                        dependency_type="include",
                        line_number=line_no,
                        resolved=True,
                    )
                    if source_file in analysis.files:
                        analysis.files[source_file].dependencies.append(dep)
                    analysis.dependencies.append(dep)
                else:
                    # Unresolved include
                    if source_file in analysis.files:
                        analysis.files[source_file].external_references.append(inc_path)
                    analysis.warnings.append(
                        f"{source_file}:{line_no}: Unresolved include: {inc_path}"
                    )

        # Statistics
        analysis.statistics = {
            "total_files": len(analysis.files),
            "total_lines": sum(f.line_count for f in analysis.files.values()),
            "entry_points": len(analysis.entry_points),
            "dependencies": len(analysis.dependencies),
            "unresolved_references": sum(
                len(f.external_references) for f in analysis.files.values()
            ),
        }

        return analysis

    def _is_excluded(self, file_path: Path, root: Path) -> bool:
        """Check if a file should be excluded."""
        excluded_dirs = {"vendor", "node_modules", ".git", "cache", "tmp", "logs"}
        for part in file_path.relative_to(root).parts:
            if part in excluded_dirs:
                return True
        return False

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return len(f.readlines())
        except Exception:
            return 0

    def _extract_includes(self, file_path: Path) -> List[Tuple[str, int]]:
        """Extract include/require statements from a PHP file."""
        includes = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f.readlines(), 1):
                    # Match include, require, include_once, require_once
                    inc_pattern = r"(?:include|require)(?:_once)?\s*\(?['\"]([^'\"]+)['\"]"
                    match = re.search(inc_pattern, line)
                    if match:
                        includes.append((match.group(1), line_no))
        except Exception:
            pass

        return includes

    def _resolve_php_include(self, inc_path: str, source_dir: Path, root: Path,
                            php_files: List[Path]) -> Optional[Path]:
        """Try to resolve a PHP include path to a file in the project."""
        # Remove leading ./ or ../
        clean_path = inc_path.lstrip(".").lstrip("/")

        # Try direct file
        for php_file in php_files:
            if php_file.name == inc_path or str(php_file.relative_to(root)) == clean_path:
                return php_file

        # Try relative to source file
        try:
            potential = (source_dir / inc_path).resolve()
            if potential.exists() and potential in php_files:
                return potential
        except Exception:
            pass

        return None

    def _parse_composer_json(self, composer_json: Path) -> dict:
        """Parse composer.json for autoload configuration."""
        try:
            with open(composer_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

class ProjectDiscoveryManager:
    """Manages project discovery across multiple languages."""

    def __init__(self):
        """Initialize discovery manager with all discoverers."""
        self.discoverers = [
            PythonProjectDiscoverer(),
            RustProjectDiscoverer(),
            PHPProjectDiscoverer(),
        ]

    def discover(self, project_root: str) -> ProjectAnalysis:
        """Discover a project, detecting its type(s) automatically.

        Args:
            project_root: Path to project root directory

        Returns:
            ProjectAnalysis with discovered files and metadata
        """
        root = Path(project_root)
        if not root.is_dir():
            raise ValueError(f"Project root is not a directory: {project_root}")

        # Detect which languages are present
        detected_languages = []
        analyses = {}

        for discoverer in self.discoverers:
            if discoverer.detect(str(root)):
                detected_languages.append(discoverer.__class__.__name__)
                analysis = discoverer.discover(str(root))
                analyses[analysis.detected_languages[0]] = analysis

        if not analyses:
            # Return empty analysis if no languages detected
            return ProjectAnalysis(
                project_root=str(root),
                project_type=ProjectType.UNKNOWN,
                detected_languages=[],
                errors=["No recognized project structure detected"],
            )

        # If single language, return that analysis
        if len(analyses) == 1:
            return list(analyses.values())[0]

        # Merge multiple language analyses
        merged = ProjectAnalysis(
            project_root=str(root),
            project_type=ProjectType.MIXED,
            detected_languages=list(analyses.keys()),
        )

        for lang, analysis in analyses.items():
            merged.files.update(analysis.files)
            merged.entry_points.extend(analysis.entry_points)
            merged.dependencies.extend(analysis.dependencies)
            merged.errors.extend(analysis.errors)
            merged.warnings.extend(analysis.warnings)

        # Recalculate statistics
        merged.statistics = {
            "total_files": len(merged.files),
            "total_lines": sum(f.line_count for f in merged.files.values()),
            "entry_points": len(merged.entry_points),
            "dependencies": len(merged.dependencies),
            "unresolved_references": sum(
                len(f.external_references) for f in merged.files.values()
            ),
        }

        return merged
