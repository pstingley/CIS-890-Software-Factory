# DOC-002 Requirements Specification: Human-Readable Semantic Documentation

## Functional Requirements

### FR-1: Semantic Interpretation from Analysis
**Requirement:** CodeFlow SHALL infer and explain the purpose, users, major capabilities, inputs, outputs, operational rules, and observable behavior of analyzed programs.

**Acceptance Criteria:**
- Semantic interpretation service receives AnalysisResult and produces SemanticInterpretation
- Interpretation identifies: application purpose, user roles, key capabilities, typical workflows
- Output includes behavioral claims linked to source evidence
- Uncertain or inferred behavior is explicitly marked
- System handles multi-function applications and identifies primary vs. auxiliary functionality

**Evidence Sources:**
- Function names and docstrings
- Control flow patterns (entry points, loops, conditionals)
- Data flow (inputs, outputs, transformations)
- Error handling patterns (exceptions, error codes)
- Semantic labels from CFG analysis

---

### FR-2: Functional Description Document
**Requirement:** CodeFlow SHALL generate a Functional_Description.docx written for managers, customers, and non-technical stakeholders.

**Acceptance Criteria:**
- Document is in .docx format, valid and readable via python-docx
- Audience is non-technical (no CFG jargon, minimal code references)
- Sections include:
  1. Executive summary (2-3 paragraphs explaining "what it does")
  2. Purpose and users (who benefits from this software)
  3. Major capabilities and workflows (what can users do with it)
  4. Inputs and outputs (what data the system accepts and produces)
  5. Operational rules and constraints (what the system will and won't do)
  6. Known limitations (from user perspective)
- Language is clear, complete sentences, no template repetition
- Length: 5-15 pages depending on application complexity
- No CFG diagrams, control-flow jargon, or graph statistics

**Example Content (Tic-Tac-Toe):**
```
Executive Summary
This is a command-line Tic-Tac-Toe game for two human players.
Players take turns placing their marks (X and O) on a 3x3 grid
until one player achieves three in a row or the grid is full.

Purpose and Users
The application serves educational and entertainment purposes.
Students learn game logic and strategy; casual users enjoy a simple game.

Major Capabilities
- Display the game board with numbered positions
- Accept player moves and validate legality
- Detect winning conditions (three in a row)
- Determine when the board is full (draw)
- Alternate turns between players
- Provide game status and outcome
```

---

### FR-3: Technical Description Document
**Requirement:** CodeFlow SHALL generate a separate Technical_Description.docx explaining architecture, components, algorithms, data flow, control flow, and exception handling for software engineers.

**Acceptance Criteria:**
- Document is in .docx format, valid and readable via python-docx
- Audience is software engineers (can use technical terminology, code references)
- Sections include:
  1. Architecture and design (overall structure, components, design patterns)
  2. Component descriptions (major functions/classes, responsibilities, interfaces)
  3. Algorithms and data structures (key algorithms, complexity, decision logic)
  4. Control flow and execution paths (entry points, major code paths, state transitions)
  5. Data flow (how data moves through the system, transformations, persistence)
  6. Exception and error handling (error conditions, recovery mechanisms, error codes)
  7. Integration points (dependencies, external interfaces, library usage)
  8. Performance and resource constraints (time/space complexity, resource usage)
- Code references include line numbers and file paths
- Control-flow diagrams referenced with directions to HTML/JSON for interactive view
- Length: 8-20 pages depending on complexity
- Technical accuracy is verified against CFG analysis

**Example Content (Tic-Tac-Toe):**
```
Architecture and Design
The application follows a game-loop architecture: initialization → game state management →
turn processing → game-state evaluation. The main entry point (main() or main.rs)
orchestrates this loop until game completion.

Component: Display
Function: display_board (line X in tictactoe.py)
Responsibility: Render current board state to terminal output
Data: Receives 3x3 board representation (list of lists)
Output: Formatted string with positions and player marks (X/O/empty)

Control Flow
Entry: main() function at line Y
1. Initialize board state (3x3 grid, all empty)
2. Enter game loop:
   a. Display current board
   b. Prompt current player for move
   c. Validate move (position in range, not occupied)
   d. Apply move to board
   e. Check for win condition (line Z)
   f. Check for draw condition (line W)
   g. Switch player
   h. Loop until game over
3. Display final board
4. Report winner or draw
5. Exit
```

---

### FR-4: Evidence-Based Claims with Traceability
**Requirement:** Every substantive behavioral claim SHALL have traceable source evidence, or be explicitly identified as an inference requiring review.

**Acceptance Criteria:**
- Claims are categorized as:
  - **Verified**: "The code implements..." (supported by CFG, semantic labels)
  - **Inferred**: "Based on code analysis, this appears to..." (reasonable interpretation, not directly stated)
  - **Uncertain**: "The behavior depends on runtime conditions that cannot be statically determined..." (dynamic, external, or missing information)

- Each claim includes evidence reference:
  - **Function-level**: "display_board (lines 42-48 in tictactoe.py)"
  - **Control-flow level**: "if statement at line 15 evaluates winning condition"
  - **Pattern-level**: "Loop structure at lines 20-30 suggests iterative processing"

- Inferred claims include reasoning: "The function name 'is_winner' and its position in the control flow suggest it evaluates game-winning conditions"

- Uncertain areas are documented: "The file I/O mechanism is not visible in the analyzed source; external persistence is not modeled"

---

### FR-5: Behavioral Description, Not Source Recitation
**Requirement:** Documentation SHALL describe actual behavior rather than simply repeat source-code expressions, function names, node counts, and edge counts.

**Acceptance Criteria:**
- Avoid template patterns such as:
  - "This function contains 6 statement nodes and 1 decision node"
  - "The function has 2 edges (true/false branches)"
  - "Returns control to the caller"
  - "Parameter X is of type Y"

- Instead, explain:
  - What the function accomplishes (purpose in domain terms)
  - How its logic works (in human terms, not AST terms)
  - What inputs it expects and what it produces
  - Why it has particular control-flow structure
  - What decisions it makes and what determines each branch

- Examples:
  - ✅ "The is_winner function checks all three-in-a-row patterns (rows, columns, diagonals) to determine if the current player has won"
  - ❌ "The is_winner function contains multiple if statements checking board positions"
  - ✅ "The game loop continues until either a player achieves three in a row or all nine positions are filled"
  - ❌ "The loop has a termination condition that evaluates two sub-conditions joined by an OR operator"

---

### FR-6: Configurable LLM Integration
**Requirement:** Use an LLM-assisted semantic interpretation stage grounded in the shared CodeFlow analysis model and relevant source-code evidence. Keep the model provider configurable rather than hard-coding Claude.

**Acceptance Criteria:**
- LLM provider abstraction layer supports:
  - Pluggable provider implementations (Claude, GPT, local model, mock)
  - Configuration via environment variables or config file
  - Graceful degradation if LLM unavailable

- Provider interface:
  ```python
  class SemanticInterpreter:
      def __init__(self, provider_config: Dict):
          # provider_config = {"provider": "claude", "model": "claude-opus", ...}

      def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
          # Returns functional and technical explanations with evidence

      def generate_functional_description(self, interpretation: SemanticInterpretation) -> str:
          # Returns paragraphs for functional document

      def generate_technical_description(self, interpretation: SemanticInterpretation) -> str:
          # Returns paragraphs for technical document
  ```

- Configuration sources (priority order):
  1. Command-line flags: `--semantic-provider claude --semantic-model claude-opus`
  2. Config file: `~/.codeflow/config.yaml` → `semantic_interpreter.provider`
  3. Environment: `CODEFLOW_SEMANTIC_PROVIDER=claude`
  4. Default: Mock provider (simple heuristics, no API calls)

- Cost tracking: Log LLM API calls, tokens, and costs for cost-aware operation

---

### FR-7: Identify Uncertain, Unsupported, and Dynamic Behavior
**Requirement:** CodeFlow SHALL identify uncertain, unsupported, or dynamically determined behavior without inventing missing functionality.

**Acceptance Criteria:**
- Categories of behavior:
  - **Supported & Analyzed**: Function calls, control flow, data transformations visible in source
  - **Supported & Partial**: Recognized constructs with limitations (e.g., macros in Rust = unsupported)
  - **Unsupported Constructs**: Identified but not analyzed (reflection, dynamic code generation)
  - **Dynamic & Unanalyzable**: Runtime-dependent behavior (network I/O, database queries, OS calls)

- Documentation includes:
  - "✓ The application can process user input from the command line (analyzed)"
  - "~ The application may use external libraries; their behavior is not modeled (partial)"
  - "✗ The application may interact with files or the network; this is not statically analyzable (dynamic)"

- Limitations section explicitly lists:
  - Which language features are unsupported
  - Which runtime behaviors cannot be statically determined
  - What external dependencies are not analyzed
  - What would require runtime instrumentation to verify

---

### FR-8: Language-Independent SPEC.md Derivation
**Requirement:** The generated language-independent SPEC.md SHALL derive from the same verified behavioral interpretation as the Word documents.

**Acceptance Criteria:**
- SPEC.md contains:
  - Formal specification of behavioral requirements
  - Input/output contracts for major functions
  - State transitions and invariants
  - Exception and error conditions
  - Performance constraints
  - Resource requirements

- SPEC.md uses the same evidence linking and traceability as Word documents
- SPEC.md is independently readable without Word documents
- SPEC.md serves as the source of truth for behavioral specification
- Word documents provide narrative explanations of SPEC.md content

---

### FR-9: Source and PHP Input-Only Preservation
**Requirement:** Source files SHALL remain unmodified, and PHP SHALL remain input-only.

**Acceptance Criteria:**
- CodeFlow performs no modifications to analyzed files
- PHP source files are processed for analysis but not code-generated
- Semantic documentation is generated about PHP behavior, not PHP code
- All output is in separate files (.docx, .md, .html, .json, .svg)

---

### FR-10: Cross-Language Support
**Requirement:** Semantic documentation generation SHALL work consistently for Python, Rust, and correctly handle PHP.

**Acceptance Criteria:**
- Python analysis: Functional and technical documents generated ✅
- Rust analysis: Functional and technical documents generated ✅
- PHP analysis: Documents generated about behavior without PHP code generation ✅
- Multi-language projects: Each file analyzed in its language; combined project documentation
- Consistent quality across languages

---

## Non-Functional Requirements

### NF-1: Performance
- Semantic interpretation: < 5 seconds for typical application (< 20 functions)
- Document generation: < 5 seconds per document
- Total overhead for DOC-002: < 15 seconds

### NF-2: Quality
- Generated documentation is of professional quality (suitable for procurement, compliance, knowledge transfer)
- No obvious errors, hallucinations, or logical inconsistencies
- Acceptance tests verify semantic quality

### NF-3: Reliability
- Graceful degradation if LLM unavailable
- Fallback to heuristic-based interpretation
- Error handling for API rate limits, timeouts, failures

### NF-4: Configurability
- LLM provider configurable without code changes
- Cost-aware operation (option to disable LLM for certain operations)
- Local vs. cloud model selection

### NF-5: Backward Compatibility
- Existing DOC-001, CFG, HTML, JSON, SPEC.md generation unchanged
- New DOC-002 output is additive (doesn't replace existing outputs)

---

## Acceptance Tests

### AT-1: Functional Description Quality
**Test:** Non-technical reader can identify application purpose, users, major capabilities, and constraints from functional document alone.

**Method:**
- Remove generated functional document of target application (e.g., Tic-Tac-Toe)
- Ask evaluator to read document and answer:
  1. What does this application do?
  2. Who are the primary users?
  3. What are the major capabilities?
  4. What are the constraints or limitations?
- Compare answers to ground truth
- Success: ≥80% accuracy on key points

### AT-2: Technical Description Accuracy
**Test:** Engineer can understand architecture and control flow from technical document.

**Method:**
- Ask engineer to read technical document and:
  1. Draw architecture diagram
  2. Identify major components and their responsibilities
  3. Trace execution path for typical operation
  4. Identify error handling mechanisms
- Compare to actual source code and CFG
- Success: ≥85% accuracy; all major components identified

### AT-3: Evidence Traceability
**Test:** Every claim can be traced to source evidence.

**Method:**
- For each substantive claim in documents:
  1. Identify evidence reference (e.g., "line 42-48 in tictactoe.py")
  2. Verify source code matches claim
  3. Verify evidence is accurate
- Track and report statistics: X% of claims have valid evidence, Y% marked as inferred
- Success: 100% of verified claims have valid evidence; ≥95% of inferred claims explicitly marked

### AT-4: No Template Repetition
**Test:** Documents avoid repetitive template patterns.

**Method:**
- Search documents for repeated patterns:
  - "This function contains N statement nodes"
  - "The function has M decision nodes"
  - "Returns control to the caller"
  - Other boilerplate
- Count occurrences
- Success: ≤2 occurrences per 10 pages (acceptable for edge cases only)

### AT-5: Behavioral Accuracy
**Test:** Claims about behavior match static analysis results.

**Method:**
- For 5-10 test programs with known behavior:
  1. Generate functional and technical documents
  2. Extract behavioral claims
  3. Verify against CFG analysis and manual code review
  4. Check for false claims, hallucinations, or missing functionality
- Success: ≥95% of behavioral claims are accurate

### AT-6: Cross-Language Consistency
**Test:** Documentation quality is consistent across Python, Rust, and PHP.

**Method:**
- Generate DOC-002 for Tic-Tac-Toe implementations in each language
- Evaluate functional and technical documents
- Compare quality metrics: readability, accuracy, completeness
- Success: Quality scores within 10% across languages

### AT-7: Performance
**Test:** Semantic documentation generation completes within time budget.

**Method:**
- Measure end-to-end time for DOC-002 generation on:
  - Small app (< 10 functions): target < 10 seconds
  - Medium app (20-50 functions): target < 20 seconds
  - Large app (50-100 functions): target < 30 seconds
- Success: 90% of applications complete within budget

---

## Configuration Interface

### Command-Line Options
```bash
python -m codeflow source.py -o output_dir \
    --doc-semantic \                           # Enable semantic documentation
    --semantic-provider claude \               # LLM provider
    --semantic-model claude-opus \             # Specific model
    --semantic-config ~/.codeflow/config.yaml # Config file
```

### Configuration File
```yaml
documentation:
  semantic:
    enabled: true
    provider: claude  # or gpt, local, mock
    model: claude-opus
    # provider-specific settings:
    claude:
      api_key: ${ANTHROPIC_API_KEY}
      timeout: 30
    gpt:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4
    local:
      endpoint: http://localhost:8000
      model: llama2
    # cost tracking:
    track_costs: true
    cost_threshold: 10.0  # Stop if daily cost exceeds $10
```

### Environment Variables
```bash
CODEFLOW_SEMANTIC_ENABLED=true
CODEFLOW_SEMANTIC_PROVIDER=claude
CODEFLOW_SEMANTIC_MODEL=claude-opus
CODEFLOW_SEMANTIC_CONFIG=~/.codeflow/config.yaml
ANTHROPIC_API_KEY=sk-...
```

---

## Error Handling & Fallback Strategies

| Scenario | Behavior |
|----------|----------|
| LLM API unavailable | Generate documents using heuristic-based interpretation (simpler, but functional) |
| Rate limit exceeded | Queue requests for retry; generate documents with partial content |
| Timeout | Use partial results; mark sections as "Analysis in progress" |
| Hallucination detected | Mark claim as inference; require human review before publication |
| Configuration error | Log error; fall back to default or mock provider |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Functional doc readability | Professional quality | Readability score ≥ 70/100 |
| Technical doc accuracy | ≥95% | Accuracy evaluation by engineer |
| Evidence traceability | 100% | Manual verification |
| Generation time | <15 sec | Benchmarking on test apps |
| Template repetition | Minimal | Automated pattern detection |
| Cross-language consistency | ±10% | Quality metrics across languages |
| Acceptance test pass rate | 100% | All AT-1 through AT-7 pass |

---

## References

- **DOC-001**: Microsoft Word documentation output (simpler, graph-focused)
- **Control-Flow Analysis**: CFG extraction and semantic labeling
- **SPEC.md**: Language-independent behavioral specification
- **ANL-001**: Non-invasive source code analysis
