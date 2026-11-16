# DOC-002 Architecture & Design

## Overview

DOC-002 adds semantic interpretation to CodeFlow's documentation pipeline. The architecture separates concerns into three layers:

1. **Analysis Layer** (Existing CFG/semantic analysis)
2. **Semantic Interpretation Layer** (NEW: LLM-assisted understanding)
3. **Document Generation Layer** (Functional & Technical Word generators)

```
┌─────────────────────────────────────────────────────────────┐
│                     Source Code Files                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Analyzers  │  (Python, Rust, Markdown)
                    └──────┬──────┘
                           │
                    ┌──────▼─────────────────────┐
                    │   AnalysisResult (CFG,    │
                    │   semantic labels,         │
                    │   source references)       │
                    └──────┬─────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        │          ┌───────▼────────┐         │
        │          │  SemanticIn-   │         │
        │          │  terpreter(LLM)│         │
        │          └───────┬────────┘         │
        │                  │                  │
   ┌────▼─────┐    ┌──────▼─────────┐    ┌──▼──────┐
   │HTMLRender │    │SemanticInterpre│    │JSONExport
   │  (CFG)    │    │   tation       │    │  (CFG)
   └────┬─────┘    └──────┬─────────┘    └──┬──────┘
        │                  │                 │
   ┌────▼──────────┬───────▼────────┬───────▼──────┐
   │               │                │              │
   │             .html          Functional_      Technical_
   │              +           Description.    Description.
   │             SVG              docx            docx
   │
   └────────────────────────────────┘

   Also output:
   - SPEC.md (language-independent, based on semantic interpretation)
   - DOC-001.docx (simpler, CFG-focused - existing)
   - project/index.html (project summary)
```

## Layer 1: Analysis Layer (Existing, No Changes)

**Components:**
- PythonAnalyzer, RustAnalyzer, MarkdownAnalyzer
- ControlFlowGraph construction
- Semantic labels (actual source code expressions)
- Source references (file, line, column)
- Error/warning/finding collection

**Output:** `AnalysisResult`
```python
class AnalysisResult:
    source_path: str
    language: str
    functions: List[FunctionCFG]
    errors: List[str]
    warnings: List[str]
    findings: List[str]
    entry_points: List[EntryPoint]
    # ... (existing fields)
```

**Key Properties:**
- Preserves control-flow accuracy
- Maintains semantic labels (not generic "node 5" but actual code expressions)
- Records source references for traceability
- Marks unsupported/partial analysis

---

## Layer 2: Semantic Interpretation Layer (NEW)

### 2.1 Semantic Interpreter Interface

```python
class SemanticInterpreter:
    """Interprets AnalysisResult into human-readable explanations."""

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """
        Convert AnalysisResult into semantic understanding.

        Returns:
            SemanticInterpretation with:
            - application_purpose: str (what it does)
            - target_users: List[str] (who uses it)
            - major_capabilities: List[Capability] (what it can do)
            - primary_workflows: List[Workflow] (typical usage patterns)
            - inputs_outputs: InputOutputSpec (data interfaces)
            - constraints: List[str] (limitations and assumptions)
            - error_handling: ErrorHandlingSpec (error recovery)
        """
        pass

    def generate_functional_description(self, interpretation: SemanticInterpretation) -> str:
        """Generate narrative paragraphs for Functional_Description.docx"""
        pass

    def generate_technical_description(self, interpretation: SemanticInterpretation) -> str:
        """Generate narrative paragraphs for Technical_Description.docx"""
        pass
```

### 2.2 SemanticInterpretation Data Model

```python
@dataclass
class SemanticClaim:
    """Single behavioral claim with evidence linking."""
    statement: str                    # "is_winner() checks three-in-a-row patterns"
    claim_type: ClaimType            # VERIFIED, INFERRED, UNCERTAIN
    evidence: List[EvidenceReference]  # source locations
    reasoning: Optional[str]          # why we believe this claim
    confidence: float                 # 0.0-1.0

@dataclass
class EvidenceReference:
    """Traceable link to source code."""
    function_name: str
    file_path: str
    line_range: Tuple[int, int]
    code_snippet: Optional[str]
    reference_type: str              # "function_definition", "control_flow", "pattern"

@dataclass
class Capability:
    """Major application capability."""
    name: str                         # "Move validation"
    description: str                 # "Checks if a move is legal"
    related_functions: List[str]      # ["is_valid_move"]
    evidence: List[EvidenceReference]

@dataclass
class Workflow:
    """Typical usage pattern."""
    name: str                         # "Playing a game"
    steps: List[str]                 # ["Initialize board", "Display board", ...]
    related_functions: List[str]
    evidence: List[EvidenceReference]

@dataclass
class InputOutputSpec:
    """Data input/output specification."""
    inputs: List[InputChannel]        # user input, files, APIs, etc.
    outputs: List[OutputChannel]      # displayed output, files, return values
    data_transformations: List[str]   # how data flows through system

@dataclass
class ErrorHandlingSpec:
    """Error handling and recovery."""
    error_types: List[str]
    detection_mechanisms: List[str]
    recovery_strategies: List[str]
    related_functions: List[str]

@dataclass
class SemanticInterpretation:
    """Complete semantic understanding of analyzed code."""
    application_purpose: str
    target_users: List[str]
    major_capabilities: List[Capability]
    primary_workflows: List[Workflow]
    inputs_outputs: InputOutputSpec
    architecture: str                 # "game-loop", "request-response", etc.
    main_components: List[ComponentDescription]
    key_algorithms: List[AlgorithmDescription]
    constraints: List[SemanticClaim]
    error_handling: ErrorHandlingSpec
    unsupported_areas: List[str]
    uncertain_behaviors: List[str]
    all_claims: List[SemanticClaim]  # for validation & evidence checking
```

### 2.3 LLM Provider Abstraction

```python
class LLMProvider(ABC):
    """Abstract interface for LLM-backed semantic interpretation."""

    @abstractmethod
    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        """Analyze code and produce semantic interpretation."""
        pass

class ClaudeLLMProvider(LLMProvider):
    """Uses Anthropic Claude API for semantic interpretation."""

    def __init__(self, model: str = "claude-opus", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        # Build prompt from AnalysisResult
        # Include: functions, control flow, semantic labels, errors/warnings
        # Request: purpose, capabilities, workflows, etc.
        # Parse response into SemanticInterpretation with evidence linking
        pass

class GPTLLMProvider(LLMProvider):
    """Uses OpenAI GPT for semantic interpretation."""
    pass

class LocalLLMProvider(LLMProvider):
    """Uses local LLM via vLLM or Ollama."""
    pass

class MockLLMProvider(LLMProvider):
    """Fallback: Heuristic-based interpretation without LLM calls."""

    def interpret_analysis(self, analysis: AnalysisResult) -> SemanticInterpretation:
        # Extract patterns from code without LLM:
        # - Function names → capabilities
        # - Entry points → starting workflows
        # - Error handling → error spec
        # - Loops/conditionals → algorithm description
        # Produces reasonable but simpler interpretation
        pass

class SemanticInterpreterFactory:
    @staticmethod
    def create(provider_config: Dict) -> LLMProvider:
        """Create appropriate provider based on configuration."""
        provider = provider_config.get("provider", "mock")

        if provider == "claude":
            return ClaudeLLMProvider(
                model=provider_config.get("model", "claude-opus"),
                api_key=provider_config.get("api_key")
            )
        elif provider == "gpt":
            return GPTLLMProvider(...)
        elif provider == "local":
            return LocalLLMProvider(...)
        else:
            return MockLLMProvider()
```

### 2.4 Semantic Interpretation Process

**Input:** AnalysisResult (CFG, semantic labels, source references)

**Process:**
1. **Extract Evidence Anchors** from CFG:
   - Entry/exit points → workflow starts/ends
   - Control flow patterns → algorithm description
   - Function calls → capability identification
   - Error handling → error spec
   - Semantic labels → evidence references

2. **Prepare LLM Prompt**:
   ```
   Analyze this program based on the following control-flow analysis:

   Functions analyzed:
   - display_board (lines 42-48): displays game board
   - is_winner (lines 20-30): checks winning condition
   - main (lines 100-150): orchestrates game loop

   Control flow pattern:
   - main calls display_board in a loop (lines 110-125)
   - Within loop, calls is_winner to check game-over condition (line 120)

   Question 1: What is the purpose of this application?
   Question 2: Who are the primary users?
   Question 3: What are the major capabilities?
   Question 4: Describe the typical workflow.

   For each answer, cite the specific functions and line numbers that support it.
   ```

3. **Process LLM Response**:
   - Parse structured output (JSON)
   - Link claims back to source evidence
   - Validate evidence references
   - Mark inferences explicitly

4. **Fallback to Heuristics** if LLM unavailable:
   - Function name heuristics ("display_*" → capability, "is_*" → decision)
   - Entry point detection (main, __main__, entry points)
   - Loop/recursive pattern detection
   - Error handling pattern recognition

**Output:** SemanticInterpretation with fully traced evidence

---

## Layer 3: Document Generation Layer (NEW)

### 3.1 Functional Description Generator

```python
class FunctionalDescriptionGenerator:
    """Generates non-technical documentation for stakeholders."""

    def generate(self, interpretation: SemanticInterpretation,
                 analysis: AnalysisResult) -> Document:
        """Produce Functional_Description.docx"""
        doc = Document()

        # 1. Title Page
        self._add_title_page(doc, analysis)

        # 2. Executive Summary (key: explain what it does in plain English)
        self._add_executive_summary(doc, interpretation)

        # 3. Purpose and Users
        self._add_purpose_and_users(doc, interpretation)

        # 4. Capabilities and Workflows
        self._add_capabilities_workflows(doc, interpretation)

        # 5. Inputs and Outputs
        self._add_inputs_outputs(doc, interpretation)

        # 6. Constraints and Limitations
        self._add_constraints_limitations(doc, interpretation)

        # 7. Known Issues (from errors/warnings)
        self._add_known_issues(doc, analysis)

        # 8. Appendix: How to Use
        self._add_appendix_usage(doc, interpretation)

        return doc

    def _add_executive_summary(self, doc: Document, interp: SemanticInterpretation):
        """Generate functional summary WITHOUT technical jargon."""
        doc.add_heading("Executive Summary", level=1)

        # Use interpretation.application_purpose
        doc.add_paragraph(interp.application_purpose)

        doc.add_heading("What You Can Do With It", level=2)
        for capability in interp.major_capabilities:
            doc.add_paragraph(f"• {capability.name}: {capability.description}")

        doc.add_heading("How It Works", level=2)
        for workflow in interp.primary_workflows:
            doc.add_paragraph(f"{workflow.name}:")
            for step in workflow.steps:
                doc.add_paragraph(f"  → {step}", style='List Number')
```

### 3.2 Technical Description Generator

```python
class TechnicalDescriptionGenerator:
    """Generates technical documentation for engineers."""

    def generate(self, interpretation: SemanticInterpretation,
                analysis: AnalysisResult) -> Document:
        """Produce Technical_Description.docx"""
        doc = Document()

        # 1. Title Page
        self._add_title_page(doc, analysis)

        # 2. Architecture
        self._add_architecture(doc, interpretation)

        # 3. Component Descriptions
        self._add_components(doc, interpretation, analysis)

        # 4. Algorithms and Data Structures
        self._add_algorithms(doc, interpretation)

        # 5. Control Flow
        self._add_control_flow(doc, interpretation, analysis)

        # 6. Data Flow
        self._add_data_flow(doc, interpretation)

        # 7. Exception and Error Handling
        self._add_error_handling(doc, interpretation)

        # 8. Integration Points
        self._add_integration(doc, analysis)

        # 9. Performance and Constraints
        self._add_performance(doc, interpretation, analysis)

        # 10. Appendix: CFG Reference
        self._add_appendix_cfg(doc, analysis)

        return doc

    def _add_control_flow(self, doc: Document, interp: SemanticInterpretation,
                         analysis: AnalysisResult):
        """Describe control flow with evidence links."""
        doc.add_heading("Control Flow and Execution Paths", level=1)

        for func in analysis.functions:
            doc.add_heading(f"{func.name}", level=2)
            doc.add_paragraph(f"File: {func.source_file}, Lines {func.start_line}-{func.end_line}")

            # Reference the full CFG in HTML/JSON
            doc.add_paragraph(
                "→ View complete control-flow diagram in HTML flowchart or JSON export"
            )

            # Describe high-level flow
            doc.add_paragraph("Execution flow:")
            # (describe major branches, loops, etc. in human terms)
```

### 3.3 Integration with Report Generator

```python
class ReportGenerator:
    @staticmethod
    def generate_report_with_semantics(
        source_file: str,
        output_dir: str,
        semantic_provider_config: Optional[Dict] = None,
        include_doc001: bool = True,
        include_doc002: bool = True
    ) -> Tuple[str, str, Optional[str], Optional[str], Optional[str], AnalysisResult]:
        """
        Generate comprehensive documentation including semantic interpretation.

        Returns:
            (html_file, json_file, doc001_file, func_desc_file, tech_desc_file, result)
        """
        # 1. Analyze source
        analyzer = AnalyzerRegistry.get_analyzer(source_file)
        analysis = analyzer.analyze(source_file)

        # 2. Generate HTML/JSON (DOC-001)
        if include_doc001:
            html_file = HTMLRender.render(analysis, output_dir)
            json_file = JSONExport.export(analysis, output_dir)
            doc001_file = DocxGenerator.generate(analysis, output_dir)

        # 3. Semantic interpretation & DOC-002
        func_desc_file = None
        tech_desc_file = None
        if include_doc002:
            interpreter = SemanticInterpreterFactory.create(
                semantic_provider_config or {"provider": "mock"}
            )
            interpretation = interpreter.interpret_analysis(analysis)

            # Generate Functional_Description.docx
            func_gen = FunctionalDescriptionGenerator()
            func_doc = func_gen.generate(interpretation, analysis)
            func_desc_file = os.path.join(output_dir, f"{basename}_Functional_Description.docx")
            func_doc.save(func_desc_file)

            # Generate Technical_Description.docx
            tech_gen = TechnicalDescriptionGenerator()
            tech_doc = tech_gen.generate(interpretation, analysis)
            tech_desc_file = os.path.join(output_dir, f"{basename}_Technical_Description.docx")
            tech_doc.save(tech_desc_file)

            # Generate/update SPEC.md
            spec_generator = SpecGenerator()
            spec_md = spec_generator.generate_from_interpretation(interpretation, analysis)
            spec_file = os.path.join(output_dir, "SPEC.md")
            with open(spec_file, 'w') as f:
                f.write(spec_md)

        return html_file, json_file, doc001_file, func_desc_file, tech_desc_file, analysis
```

---

## Decision Points

### D-1: LLM Provider Strategy

**Decision:** Support pluggable LLM providers with mock fallback.

**Rationale:**
- Deployment flexibility (Claude for high quality, local for cost, mock for testing)
- Future-proof against LLM API changes
- Graceful degradation without breaking pipeline

**Implementation:** Factory pattern with provider interface (see Section 2.3)

---

### D-2: Evidence Linking Format

**Decision:** Use source references (file, function, line range) with optional code snippets.

**Rationale:**
- Enables verification without requiring full source parsing
- Minimal data overhead in documents
- Clear traceability for readers

**Example:**
```
"Display function (display_board, tictactoe.py, lines 42-48)"
"Board update: Modifies the game state before checking win condition (line 25)"
```

---

### D-3: Inference vs. Verification Distinction

**Decision:** Categorize all claims as VERIFIED, INFERRED, or UNCERTAIN.

**Rationale:**
- Prevents hallucination by grounding in analysis
- Explicit uncertainty prevents false confidence
- Enables human review workflow

**Implementation:** Mark in documentation:
- ✓ Verified: "The code implements..."
- ~ Inferred: "Based on code analysis, this appears to..."
- ? Uncertain: "The behavior depends on runtime conditions..."

---

### D-4: Document Separation

**Decision:** Generate separate Functional and Technical documents instead of single comprehensive document.

**Rationale:**
- Different audiences with different concerns
- Functional doc remains clean without technical jargon
- Technical doc can reference CFG/flow details
- Both grounded in same semantic interpretation

---

### D-5: Performance Optimization

**Decision:** Cache semantic interpretations and use progressive document generation.

**Rationale:**
- LLM calls can be expensive; cache for multi-document generation
- Generate high-value sections first (executive summary)
- Support interruption and partial generation
- Enable cost-aware operation

---

## Testing Strategy

### Unit Tests
- **SemanticInterpreter**: Mock LLM provider produces expected interpretations
- **Evidence Linking**: Claims link correctly to source code
- **Document Generators**: Generated documents have correct structure

### Integration Tests
- End-to-end: source → analysis → interpretation → documents
- Cross-provider: Results consistent across Claude, GPT, mock
- Multi-language: Python, Rust, PHP handling

### Acceptance Tests (See requirements doc AT-1 through AT-7)
- Functional doc readability (non-technical reader evaluation)
- Technical doc accuracy (engineer review)
- Evidence traceability (100% of claims traceable)
- Behavioral accuracy (no hallucinations)

### Performance Tests
- Semantic interpretation time < 5 seconds
- Document generation < 5 seconds each
- Total overhead < 15 seconds

---

## Error Handling & Fallback Strategies

| Failure Point | Strategy |
|---------------|----------|
| LLM API unavailable | Use MockLLMProvider (heuristic-based) |
| LLM rate limited | Queue and retry with exponential backoff |
| LLM timeout | Use partial results; mark sections incomplete |
| Configuration missing | Use defaults; log warnings |
| Invalid evidence link | Log warning; mark claim as inference |
| Hallucination detected | Reject claim; use fallback heuristic |

---

## Configuration & Deployment

### Environment Variables (Priority Order)

```bash
# 1. Explicit command-line override
python -m codeflow source.py --semantic-provider claude

# 2. Environment variable
export CODEFLOW_SEMANTIC_PROVIDER=claude
export ANTHROPIC_API_KEY=sk-...

# 3. Config file
~/.codeflow/config.yaml:
  documentation:
    semantic:
      provider: claude
      model: claude-opus

# 4. Default
# Falls back to "mock" provider (heuristic-based, no API calls)
```

### Cost Tracking

```yaml
# In config.yaml
documentation:
  semantic:
    track_costs: true
    cost_limit: 10.0  # Stop if daily cost > $10
    cost_log: ~/.codeflow/costs.log
```

Output in CLI:
```
Semantic documentation generated
  Interpretation time: 2.3s
  LLM provider: claude
  Tokens used: 1,250 input + 450 output
  API cost: $0.08
```

---

## Relationship to Existing Components

**Preserves:**
- AnalysisResult unchanged
- CFG construction unchanged
- Semantic labels unchanged
- DOC-001 Word generator unchanged
- HTML/SVG rendering unchanged
- JSON export unchanged

**Builds Upon:**
- Semantic labels as evidence sources
- Control-flow patterns for interpretation
- Entry points for workflow identification
- Error/warning collection for constraints

**Adds:**
- SemanticInterpretation data model
- LLM provider abstraction
- Functional and technical document generators
- Evidence linking and traceability
- SPEC.md generation from interpretation

---

## Success Criteria

✅ Functional documents are readable by non-technical stakeholders
✅ Technical documents are accurate for engineers
✅ 100% of claims are traceable to evidence or marked as inference
✅ No template repetition or generic graph statistics
✅ Semantic interpretation completes within 15 seconds
✅ Cross-language support (Python, Rust, PHP)
✅ Graceful fallback if LLM unavailable
✅ Configurable provider without code changes
✅ Acceptance tests demonstrate quality

---

## References

- **DOC-001**: Graph-focused Word documentation (preserved)
- **Control-Flow Analysis**: CFG extraction and semantic labeling
- **SPEC.md**: Language-independent specification
- **LLM Abstraction**: Provider interface for Claude, GPT, local models
