# CodeFlow 0.2.1

CodeFlow draws how a Python program executes or how a Markdown specification says it should behave. The two reports give you different evidence to compare.

## Start on Windows

Extract the ZIP and double-click **codeflow_analyze.bat**, or open a terminal in the extracted folder and run:

```powershell
python -m codeflow
```

At **File to examine (.py or .md)**, enter a file path. Paths with spaces work. You can also provide the filename directly:

```powershell
python -m codeflow "examples/python/tictactoe.py" --open
python -m codeflow "examples/python/SPEC.md" --open
```

The original `python -m codeflow.cli analyze FILE` command still works. The Python command writes reports beside the input unless you give `--output-dir`. The batch launcher opens the report and writes it to the current directory by default, as before. It still accepts an optional second positional argument for the output folder.

## What each option produces

- **Python (.py)** produces the existing `*_codeflow.html` source flowchart and `*_codeflow.json` export.
- **Markdown (.md)** produces `*_specflow.html`. CodeFlow renders this report with the same local SVG renderer as the Python report. It can import simple embedded Mermaid flowcharts with quoted nodes and directed arrows. It reports skipped embedded diagrams that use more complex syntax. If no workflow can be imported, Claude Code drafts one from the specification and CodeFlow shows the supplied section or requirement references. Review AI-drafted branches and flagged gaps against the specification.
- After choosing a Markdown file, answer **Y** to also write `*_Walkthrough.docx`, a plain-English account of the behavior. Answer **N** or press Enter for the chart alone.

To compare the included examples, open both reports and follow an invalid move through each. The specification report shows the behavior described in Markdown. The Python report shows the paths found in the implementation.

## Requirements and options

- Python 3.11 or later. The Python source analyzer needs no extra packages.
- An installed and signed-in `claude` command for Markdown without an importable embedded flowchart and for prose generation. These operations send the specification text through your configured Claude Code account. When importing an embedded flowchart and choosing N, CodeFlow makes no Claude call.
- For Word output, install the optional dependency using `python -m pip install python-docx` in your Python environment.

Use `--prose` or `--no-prose` to skip the Y/N question, `--force` to replace an earlier Markdown report, or `--claude PATH` to choose a different Claude Code executable. Run `python -m codeflow --help` to see the full command options.
