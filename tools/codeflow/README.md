# CodeFlow 0.2.1

CodeFlow draws how a program executes or how a Markdown specification says it should behave. The two reports give you different evidence to compare.

## Start on Windows

Extract the ZIP and double-click **codeflow_analyze.bat**, or open a terminal in the extracted folder and run:

```powershell
python -m codeflow
```

At **File to examine (.py, .rs, or .md)**, enter a file path. Paths with spaces work. You can also provide the filename directly:

```powershell
python -m codeflow "examples/python/tictactoe.py" --open
python -m codeflow "examples/python/SPEC.md" --open
```

The original `python -m codeflow.cli analyze FILE` command still works. The Python command writes reports beside the input unless you give `--output-dir`. The batch launcher opens the report and writes it to the current directory by default, as before. It still accepts an optional second positional argument for the output folder.

## What each option produces

- **Python (.py)** produces the existing `*_codeflow.html` source flowchart and `*_codeflow.json` export.
- **Rust (.rs)** produces `*_codeflow.html` source flowchart and `*_codeflow.json` export (requires tree-sitter).
- **Markdown (.md)** produces `*_specflow.html`. CodeFlow renders this report with the same local SVG renderer as the Python report. It can import simple embedded Mermaid flowcharts with quoted nodes and directed arrows. It reports skipped embedded diagrams that use more complex syntax. If no workflow can be imported, Claude Code drafts one from the specification and CodeFlow shows the supplied section or requirement references. Review AI-drafted branches and flagged gaps against the specification.
- After choosing a Markdown file, answer **Y** to also write `*_Walkthrough.docx`, a plain-English account of the behavior. Answer **N** or press Enter for the chart alone.

To compare the included examples, open both reports and follow an invalid move through each. The specification report shows the behavior described in Markdown. The Python or Rust report shows the paths found in the implementation.

## Requirements and Installation

### Python Version
- Python 3.11 or later

### Required Dependencies

**For Python analysis (.py files):**
- No external dependencies required. The Python source analyzer uses only the standard library.

**For Rust analysis (.rs files):**
- Install tree-sitter bindings and Rust grammar:
  ```bash
  pip install tree-sitter==0.21.1 tree-sitter-rust==0.21.1
  ```
  The versions must match. See [tree-sitter-py](https://github.com/tree-sitter/py-tree-sitter) for compatibility information.

### Optional Dependencies

**For Word document output (.docx):**
- Install the optional python-docx package:
  ```bash
  pip install python-docx>=0.8.10
  ```
  Word output is available for all input types (Python, Rust, Markdown).

**For Markdown specifications:**
- An installed and signed-in `claude` command for specifications without an importable embedded flowchart and for prose generation. These operations send the specification text through your configured Claude Code account. When importing an embedded flowchart and choosing N, CodeFlow makes no Claude call.

### Installation from Requirements

To install all dependencies from the included `requirements.txt`:

```bash
pip install -r requirements.txt
```

Note: This installs tree-sitter by default for Rust support. If you only use Python analysis, tree-sitter installation is optional.

### Troubleshooting tree-sitter Installation

If tree-sitter installation fails:

1. **On Linux/macOS**, ensure you have build tools:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential python3-dev

   # macOS
   brew install python3
   ```

2. **On Windows**, ensure you have Visual C++ build tools installed or use pre-built wheels.

3. **Verify installation**:
   ```bash
   python -c "from tree_sitter import Language, Parser; print('tree-sitter OK')"
   ```

## Options and Commands

Use `--prose` or `--no-prose` to skip the Y/N question, `--force` to replace an earlier Markdown report, or `--claude PATH` to choose a different Claude Code executable. Run `python -m codeflow --help` to see the full command options.
