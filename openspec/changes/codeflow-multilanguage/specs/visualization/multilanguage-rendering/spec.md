# Spec Delta: Multilanguage Rendering

## Purpose

Ensures that flowcharts generated from Python, Rust, and Markdown specifications use consistent visual conventions, layout algorithms, and interactive features, so users can compare behavior across implementations and specifications without cognitive overhead from different rendering styles.

## ADDED Requirements

### Requirement: Flowcharts from all languages use the same SVG visual conventions
CodeFlow SHALL render Python, Rust, and Markdown flowcharts using identical shapes, colors, and labels.

#### Scenario: Node shapes are consistent across languages
- **WHEN** viewing flowcharts from Python, Rust, and a Markdown spec side by side
- **THEN** entry nodes are the same shape, decision nodes are the same shape, statements use the same shape, and exit nodes are identical—regardless of source language

#### Scenario: Edge labels and types match across languages
- **WHEN** examining branching in Python, Rust, and Markdown flowcharts
- **THEN** true/false labels, loop-back edges, exception edges, and normal flow edges use the same line styles, colors, and labels

#### Scenario: Color coding is consistent
- **WHEN** comparing flowcharts from different sources
- **THEN** entry nodes are the same color, errors/exceptions use the same color, loops use the same styling, etc.

### Requirement: Flowchart layout algorithm works uniformly for all languages
CodeFlow SHALL use the same hierarchical layout algorithm to position nodes and route edges, regardless of language.

#### Scenario: Deep nesting in Python and Rust layouts similarly
- **WHEN** analyzing a Python function with 5-level nesting and a Rust function with 5-level nesting
- **THEN** both flowcharts use the same vertical/horizontal spacing and edge routing strategy

#### Scenario: Loop representation layout is consistent
- **WHEN** displaying loops from Python (for/while) and Rust (for/while/loop)
- **THEN** the back-edge routing and loop body positioning follow the same layout convention

#### Scenario: Large flowcharts remain readable
- **WHEN** displaying a complex function from any language with 20+ nodes
- **THEN** the layout algorithm prevents overlaps and maintains clarity using consistent principles

### Requirement: HTML report includes language and analyzer information
CodeFlow's HTML report SHALL display which language was analyzed and which analyzer version was used.

#### Scenario: Python report shows Python analyzer details
- **WHEN** viewing an HTML report generated from a .py file
- **THEN** the report header indicates "Source: Python (.py)" and shows the Python analyzer version

#### Scenario: Rust report shows Rust analyzer details
- **WHEN** viewing an HTML report generated from a .rs file
- **THEN** the report header indicates "Source: Rust (.rs)" and shows the Rust analyzer version

#### Scenario: Specification report shows specification source
- **WHEN** viewing an HTML report from a Markdown file
- **THEN** the report header indicates "Source: Specification (.md)" and notes whether flowchart was imported or AI-generated

### Requirement: SVG rendering supports interactive features
CodeFlow's SVG flowcharts SHALL support hover tooltips, node highlighting, and optional path tracing.

#### Scenario: Hover reveals full node label
- **WHEN** hovering over a truncated or abbreviated node label in the SVG
- **THEN** a tooltip appears showing the complete label text

#### Scenario: Click or highlight related nodes
- **WHEN** clicking a decision node
- **THEN** both outgoing branches are highlighted, showing the true and false paths

#### Scenario: Node details on click
- **WHEN** clicking a node in the flowchart
- **THEN** a panel appears showing source code location (if available), node type, and connected edges

### Requirement: HTML report structure is consistent across languages
CodeFlow's HTML reports from all languages SHALL include consistent sections: flowchart visualization, metadata, analysis summary, and optional warnings.

#### Scenario: Report sections match across Python, Rust, and spec
- **WHEN** viewing HTML reports from each language
- **THEN** each report contains a consistent structure (header, flowchart, statistics, analysis notes, footer)

#### Scenario: Statistics section shows language-appropriate metrics
- **WHEN** viewing a Rust report statistics section
- **THEN** it shows node count, edge count, and Rust-specific warnings (e.g., unsupported constructs)

#### Scenario: Analysis warnings appear consistently
- **WHEN** a file contains unsupported constructs
- **THEN** warnings are displayed in a consistent section of the HTML report, formatted identically to Python analysis warnings

### Requirement: Node labels are generated consistently
CodeFlow SHALL generate concise, readable node labels for all languages, truncating when necessary and exposing full text via hover.

#### Scenario: Statement node label
- **WHEN** creating a statement node for a Python assignment or Rust let binding
- **THEN** the label shows the core action (variable assignment, function call) without code syntax

#### Scenario: Decision node label clarity
- **WHEN** rendering a decision node from `if x > 5:` (Python) or `if x > 5 { }` (Rust)
- **THEN** the label shows a simplified condition: "x > 5?" without code punctuation

#### Scenario: Long labels are truncated
- **WHEN** a node's natural label exceeds a display width threshold
- **THEN** the label is truncated with ellipsis (...) and the full text is available via hover
