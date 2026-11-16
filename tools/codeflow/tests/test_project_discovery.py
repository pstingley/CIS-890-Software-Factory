"""Tests for project discovery infrastructure."""

import tempfile
import json
from pathlib import Path

import pytest

from codeflow.project import (
    ProjectDiscoveryManager,
    PythonProjectDiscoverer,
    RustProjectDiscoverer,
    PHPProjectDiscoverer,
    ProjectType,
)

class TestPythonProjectDiscovery:
    """Test Python project discovery."""

    def test_detect_python_project_with_py_files(self):
        """Python discoverer detects projects with .py files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple Python file
            py_file = Path(tmpdir) / "main.py"
            py_file.write_text("print('hello')")

            discoverer = PythonProjectDiscoverer()
            assert discoverer.detect(tmpdir)

    def test_detect_python_project_with_setup_py(self):
        """Python discoverer detects projects with setup.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_py = Path(tmpdir) / "setup.py"
            setup_py.write_text("from setuptools import setup\nsetup(name='test')")

            discoverer = PythonProjectDiscoverer()
            assert discoverer.detect(tmpdir)

    def test_discover_python_project_structure(self):
        """Python discovery identifies files and entry points."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project structure
            root = Path(tmpdir)
            (root / "main.py").write_text("if __name__ == '__main__':\n    print('hello')")
            (root / "module.py").write_text("def func(): pass")
            (root / "package").mkdir()
            (root / "package" / "__init__.py").write_text("")
            (root / "package" / "submodule.py").write_text("def subfunc(): pass")

            # Create excluded directory
            (root / "venv").mkdir()
            (root / "venv" / "lib.py").write_text("# should be excluded")

            discoverer = PythonProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Verify discovered files
            assert len(analysis.files) >= 3  # main.py, module.py, package/__init__.py, package/submodule.py
            assert analysis.project_type == ProjectType.PYTHON

            # Verify entry point detection
            assert any(ep.path == "main.py" for ep in analysis.entry_points)

            # Verify venv is excluded
            assert not any("venv" in f for f in analysis.files.keys())

    def test_python_import_resolution(self):
        """Python discovery resolves local imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("import module\nfrom subpackage import helper")
            (root / "module.py").write_text("pass")
            (root / "subpackage").mkdir()
            (root / "subpackage" / "__init__.py").write_text("")
            (root / "subpackage" / "helper.py").write_text("pass")

            discoverer = PythonProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Check dependencies
            main_file = analysis.files.get("main.py")
            assert main_file is not None
            assert len(main_file.dependencies) >= 2

class TestRustProjectDiscovery:
    """Test Rust project discovery."""

    def test_detect_rust_project(self):
        """Rust discoverer detects projects with Cargo.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cargo_toml = Path(tmpdir) / "Cargo.toml"
            cargo_toml.write_text("""
[package]
name = "test"
version = "0.1.0"
edition = "2021"
""")

            discoverer = RustProjectDiscoverer()
            assert discoverer.detect(tmpdir)

    def test_discover_rust_project_structure(self):
        """Rust discovery identifies Cargo project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create Cargo.toml
            cargo_toml = root / "Cargo.toml"
            cargo_toml.write_text("""
[package]
name = "tictactoe"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "tictactoe"
path = "src/main.rs"

[lib]
name = "tictactoe"
path = "src/lib.rs"
""")

            # Create source files
            src = root / "src"
            src.mkdir()
            (src / "main.rs").write_text("fn main() {}")
            (src / "lib.rs").write_text("pub fn func() {}")
            (src / "util.rs").write_text("fn helper() {}")

            discoverer = RustProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Verify discovered files
            assert len(analysis.files) >= 3
            assert analysis.project_type == ProjectType.RUST

            # Verify entry points
            assert any(ep.path == "src/main.rs" for ep in analysis.entry_points)
            assert any(ep.path == "src/lib.rs" for ep in analysis.entry_points)

    def test_rust_module_discovery(self):
        """Rust discovery identifies module declarations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create Cargo.toml
            cargo_toml = root / "Cargo.toml"
            cargo_toml.write_text("""
[package]
name = "test"
version = "0.1.0"
edition = "2021"
""")

            # Create source files with mod declarations
            src = root / "src"
            src.mkdir()
            (src / "main.rs").write_text("mod util;\nfn main() {}")
            (src / "util.rs").write_text("pub fn helper() {}")

            discoverer = RustProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Check for module dependencies
            main_file = analysis.files.get("src/main.rs")
            assert main_file is not None

class TestPHPProjectDiscovery:
    """Test PHP project discovery."""

    def test_detect_php_project_with_php_files(self):
        """PHP discoverer detects projects with .php files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            php_file = Path(tmpdir) / "index.php"
            php_file.write_text("<?php echo 'hello'; ?>")

            discoverer = PHPProjectDiscoverer()
            assert discoverer.detect(tmpdir)

    def test_detect_php_project_with_composer_json(self):
        """PHP discoverer detects projects with composer.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = Path(tmpdir) / "composer.json"
            composer.write_text('{"name": "test/project"}')

            discoverer = PHPProjectDiscoverer()
            assert discoverer.detect(tmpdir)

    def test_discover_php_project_structure(self):
        """PHP discovery identifies files and entry points."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create PHP project structure
            (root / "index.php").write_text("<?php echo 'index'; ?>")
            (root / "config.php").write_text("<?php define('DB', 'localhost'); ?>")
            (root / "public").mkdir()
            (root / "public" / "app.php").write_text("<?php require '../config.php'; ?>")

            # Create excluded directory
            (root / "vendor").mkdir()
            (root / "vendor" / "lib.php").write_text("<?php // should be excluded")

            discoverer = PHPProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Verify discovered files
            assert len(analysis.files) >= 3
            assert analysis.project_type == ProjectType.PHP

            # Verify entry points
            assert any(ep.path == "index.php" for ep in analysis.entry_points)

            # Verify vendor is excluded
            assert not any("vendor" in f for f in analysis.files.keys())

    def test_php_include_extraction(self):
        """PHP discovery extracts include/require statements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "index.php").write_text("""<?php
require 'config.php';
include_once 'vendor/autoload.php';
include 'helpers.php';
?>""")
            (root / "config.php").write_text("<?php ?>")
            (root / "helpers.php").write_text("<?php ?>")
            (root / "vendor").mkdir()
            (root / "vendor" / "autoload.php").write_text("<?php ?>")

            discoverer = PHPProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Check dependencies
            index_file = analysis.files.get("index.php")
            assert index_file is not None

class TestProjectDiscoveryManager:
    """Test project discovery manager (multi-language detection)."""

    def test_discover_python_project(self):
        """Manager detects and analyzes Python projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("main.py").write_text("print('hello')")

            manager = ProjectDiscoveryManager()
            analysis = manager.discover(tmpdir)

            assert analysis.project_type == ProjectType.PYTHON
            assert "python" in analysis.detected_languages
            assert len(analysis.files) > 0

    def test_discover_rust_project(self):
        """Manager detects and analyzes Rust projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            root.joinpath("Cargo.toml").write_text("[package]\nname = 'test'\nversion = '0.1.0'")
            root.joinpath("src").mkdir()
            root.joinpath("src/main.rs").write_text("fn main() {}")

            manager = ProjectDiscoveryManager()
            analysis = manager.discover(tmpdir)

            assert analysis.project_type == ProjectType.RUST
            assert "rust" in analysis.detected_languages
            assert len(analysis.files) > 0

    def test_discover_php_project(self):
        """Manager detects and analyzes PHP projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("index.php").write_text("<?php ?>")

            manager = ProjectDiscoveryManager()
            analysis = manager.discover(tmpdir)

            assert analysis.project_type == ProjectType.PHP
            assert "php" in analysis.detected_languages
            assert len(analysis.files) > 0

    def test_discover_mixed_project(self):
        """Manager detects mixed-language projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Add Python files
            root.joinpath("script.py").write_text("print('hello')")

            # Add PHP files
            root.joinpath("index.php").write_text("<?php ?>")

            manager = ProjectDiscoveryManager()
            analysis = manager.discover(tmpdir)

            assert analysis.project_type == ProjectType.MIXED
            assert "python" in analysis.detected_languages
            assert "php" in analysis.detected_languages
            assert len(analysis.files) > 0

    def test_project_analysis_json_serialization(self):
        """Project analysis can be serialized to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("main.py").write_text("print('hello')")

            manager = ProjectDiscoveryManager()
            analysis = manager.discover(tmpdir)

            # Should be serializable to JSON
            json_data = analysis.to_dict()
            json_str = json.dumps(json_data)

            assert json_str
            assert "project_root" in json_data
            assert "files" in json_data
            assert "statistics" in json_data

class TestRealRustTicTacToe:
    """Test project discovery on the real Tic-Tac-Toe Cargo project."""

    def test_discover_tictactoe_project(self):
        """Discover the actual Tic-Tac-Toe Rust project."""
        tictactoe_dir = Path("/workspaces/CIS-890-Software-Factory/tools/codeflow/examples/rust/tictactoe")

        if not tictactoe_dir.exists():
            pytest.skip(f"Tic-Tac-Toe project not found at {tictactoe_dir}")

        discoverer = RustProjectDiscoverer()
        assert discoverer.detect(str(tictactoe_dir))

        analysis = discoverer.discover(str(tictactoe_dir))

        # Verify structure
        assert analysis.project_type == ProjectType.RUST
        assert len(analysis.files) >= 2  # At least main.rs and lib.rs
        assert len(analysis.entry_points) >= 2  # Binary and library

        # Verify specific files
        file_paths = set(analysis.files.keys())
        assert any("src/main.rs" in p for p in file_paths)
        assert any("src/lib.rs" in p for p in file_paths)

        # Verify entry points
        ep_paths = {ep.path for ep in analysis.entry_points}
        assert any("main.rs" in p for p in ep_paths)
        assert any("lib.rs" in p for p in ep_paths)

        # Verify statistics
        assert analysis.statistics["total_files"] >= 2
        assert analysis.statistics["total_lines"] > 0
        assert analysis.statistics["entry_points"] >= 2

    def test_manager_discover_tictactoe_project(self):
        """Test manager discovery on Tic-Tac-Toe project."""
        tictactoe_dir = Path("/workspaces/CIS-890-Software-Factory/tools/codeflow/examples/rust/tictactoe")

        if not tictactoe_dir.exists():
            pytest.skip(f"Tic-Tac-Toe project not found at {tictactoe_dir}")

        manager = ProjectDiscoveryManager()
        analysis = manager.discover(str(tictactoe_dir))

        assert analysis.project_type == ProjectType.RUST
        assert "rust" in analysis.detected_languages
        assert len(analysis.files) >= 2
        assert len(analysis.entry_points) >= 2

class TestProjectDiscoveryEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_directory(self):
        """Manager handles empty directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ProjectDiscoveryManager()
            analysis = manager.discover(tmpdir)

            assert analysis.project_type == ProjectType.UNKNOWN
            assert len(analysis.files) == 0

    def test_invalid_directory(self):
        """Manager rejects non-existent directories."""
        manager = ProjectDiscoveryManager()

        with pytest.raises(ValueError):
            manager.discover("/nonexistent/path/to/project")

    def test_circular_imports_python(self):
        """Python discovery handles circular imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            (root / "module_a.py").write_text("import module_b")
            (root / "module_b.py").write_text("import module_a")

            discoverer = PythonProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Should complete without error and record dependencies
            assert len(analysis.files) >= 2
            assert len(analysis.dependencies) > 0

    def test_missing_files_in_includes(self):
        """PHP discovery records unresolved includes as warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            (root / "index.php").write_text("<?php require 'nonexistent.php'; ?>")

            discoverer = PHPProjectDiscoverer()
            analysis = discoverer.discover(tmpdir)

            # Should record as external reference
            index_file = analysis.files.get("index.php")
            assert index_file is not None
            assert len(index_file.external_references) > 0 or len(analysis.warnings) > 0
