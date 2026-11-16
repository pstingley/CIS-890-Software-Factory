# Phase 5a: Infrastructure & LLM Integration (2-3 weeks)

## Overview

Phase 5a establishes the foundational infrastructure for DOC-002: LLM provider abstraction, semantic interpretation service, evidence model, and configuration system.

**Key Deliverables:**
- LLMProvider abstraction with Claude/GPT/local/mock implementations
- SemanticInterpreter service with evidence linking
- Configuration system (CLI flags, config file, environment variables)
- SemanticInterpretation data model (complete)
- Unit tests (90%+ coverage)

**Success Criteria:**
- SemanticInterpreter accepts AnalysisResult → produces SemanticInterpretation
- All evidence references validate against source code
- Mock provider works without API keys (for testing)
- Configuration system is fully functional
- No external dependencies beyond existing CodeFlow tooling

---

## Tasks

### 5a-1: LLMProvider Abstraction (3-4 days)

**Goal:** Define provider interface and implement Claude, GPT, local, and mock implementations.

**Deliverables:**
- `tools/codeflow/codeflow/semantic/llm_provider.py`
  - `LLMProvider` ABC with `interpret_analysis()` method
  - `ClaudeLLMProvider` (Anthropic API)
  - `GPTLLMProvider` (OpenAI API)
  - `LocalLLMProvider` (vLLM/Ollama via HTTP)
  - `MockLLMProvider` (heuristic-based, no API)
  - `SemanticInterpreterFactory.create(config)`

- `tools/codeflow/codeflow/semantic/provider_config.py`
  - Configuration data classes for each provider
  - Validation logic (e.g., API keys, endpoint URLs)
  - Defaults and environment variable handling

**Tests:**
- `tools/codeflow/tests/test_llm_provider_factory.py`
  - Provider creation from config (all 4 types)
  - API key fallback to environment variables
  - Invalid configuration handling
  - Provider-agnostic interface compliance

**Acceptance:**
- All 4 providers instantiate correctly
- Factory selects correct provider by name
- No API calls made without explicit configuration
- Mock provider runs offline

---

### 5a-2: SemanticInterpretation Data Model (3-4 days)

**Goal:** Define complete data classes for representing semantic understanding.

**Deliverables:**
- `tools/codeflow/codeflow/semantic/interpretation_model.py`
  - `SemanticClaim` (statement, claim_type, evidence, reasoning, confidence)
  - `EvidenceReference` (function_name, file_path, line_range, code_snippet, type)
  - `Capability` (name, description, functions, evidence)
  - `Workflow` (name, steps, functions, evidence)
  - `InputOutputSpec` (inputs, outputs, transformations)
  - `ErrorHandlingSpec` (error_types, detection, recovery)
  - `ComponentDescription`, `AlgorithmDescription`
  - `SemanticInterpretation` (complete root object)

- `tools/codeflow/codeflow/semantic/claim_types.py`
  - `ClaimType` enum (VERIFIED, INFERRED, UNCERTAIN)
  - `EvidenceType` enum (function_definition, control_flow, pattern, etc.)
  - Serialization/deserialization support (JSON, YAML)

**Tests:**
- `tools/codeflow/tests/test_interpretation_model.py`
  - Dataclass instantiation
  - JSON serialization/deserialization round-trip
  - Validation (e.g., evidence references must exist)
  - Required vs. optional fields

**Acceptance:**
- All dataclasses instantiate correctly
- JSON serialization produces valid, parseable output
- Validation catches invalid evidence references
- No circular references or infinite loops on serialization

---

### 5a-3: Evidence Linking & Validation (3-4 days)

**Goal:** Implement mechanism to link claims to source code locations and verify they exist.

**Deliverables:**
- `tools/codeflow/codeflow/semantic/evidence_model.py`
  - `EvidenceValidator` class
  - `validate_evidence(evidence_ref, analysis_result)` → bool
  - `extract_code_snippet(file_path, line_range)` → str
  - `find_evidence_for_function(function_name, analysis_result)` → List[EvidenceReference]

- `tools/codeflow/codeflow/semantic/evidence_extractor.py`
  - Extract evidence anchors from AnalysisResult:
    - Function entry/exit points
    - Control-flow branch nodes
    - Semantic labels (actual code expressions)
    - Error handling patterns
    - Entry points and workflows

**Tests:**
- `tools/codeflow/tests/test_evidence_model.py`
  - Valid reference validation passes
  - Invalid reference validation fails
  - Code snippet extraction correct
  - Evidence extractor finds patterns in CFG

- Regression tests with existing tic-tac-toe analysis:
  - 10+ evidence anchors correctly identified
  - All CFG nodes have traceable evidence

**Acceptance:**
- Evidence validator catches 100% of invalid references
- Code snippet extraction matches source file
- No false positives in pattern detection
- Performance: <100ms per validation

---

### 5a-4: Semantic Interpreter Service (4-5 days)

**Goal:** Implement the main SemanticInterpreter that orchestrates interpretation pipeline.

**Deliverables:**
- `tools/codeflow/codeflow/semantic/semantic_interpreter.py`
  - `SemanticInterpreter` class
  - `interpret_analysis(analysis)` → SemanticInterpretation
  - Orchestrates: prompt building → LLM call → response parsing → evidence validation
  - Error handling and fallback strategies

- LLM Prompt Engineering:
  - `tools/codeflow/codeflow/semantic/prompts.py`
  - Prompt templates for each semantic aspect (purpose, capabilities, workflows, etc.)
  - Structured output format (JSON)
  - Evidence inclusion in prompt
  - Temperature/token limits appropriate for each call

**Core Process:**
1. Extract evidence anchors from AnalysisResult
2. Build structured prompt including:
   - Function summaries with line numbers
   - Entry points
   - Control-flow patterns
   - Semantic labels (code expressions)
3. Call LLM provider
4. Parse structured JSON response
5. Validate evidence references
6. Mark unvalidated claims as INFERRED
7. Return complete SemanticInterpretation

**Tests:**
- `tools/codeflow/tests/test_semantic_interpreter.py`
  - Interpreter instantiation (all provider types)
  - Interpretation of tic-tac-toe analysis
  - Evidence validation in returned interpretation
  - Fallback to MockProvider when API fails
  - Prompt formatting produces valid JSON response structure
  - JSON parsing error handling

- Integration test with real AnalysisResult:
  - Tic-tac-toe AnalysisResult → valid SemanticInterpretation
  - All major capabilities identified
  - Workflows described
  - Evidence links validated

**Acceptance:**
- Produces valid SemanticInterpretation for test input
- All VERIFIED claims have valid evidence
- Gracefully falls back to MockProvider
- Runs in <10 seconds (using mock or cached)

---

### 5a-5: Configuration System (2-3 days)

**Goal:** Implement CLI flags, config file, and environment variable handling.

**Deliverables:**
- `tools/codeflow/codeflow/semantic/config.py`
  - `SemanticConfig` dataclass
  - Load from: CLI args → config file → environment variables → defaults
  - Validation and error messages

- CLI Extension (modify `tools/codeflow/cli.py`):
  - `--semantic-provider {claude|gpt|local|mock}` flag
  - `--semantic-model` flag (e.g., "claude-opus")
  - `--semantic-config` flag (path to config file)
  - `--no-doc002` flag (disable semantic documentation)
  - `--semantic-timeout` (LLM call timeout in seconds)

- Config File Format (`~/.codeflow/config.yaml`):
  ```yaml
  documentation:
    semantic:
      provider: claude
      model: claude-opus
      timeout: 30
      track_costs: true
      cost_limit: 10.0
  ```

**Tests:**
- `tools/codeflow/tests/test_semantic_config.py`
  - CLI flags parsing
  - Config file loading
  - Environment variable fallback
  - Defaults applied correctly
  - Invalid configurations rejected

**Acceptance:**
- All 4 providers selectable via config
- Environment variables override config file
- CLI flags override all
- No hard-coded API keys in source
- Help text explains all options

---

### 5a-6: Integration with ReportGenerator (2-3 days)

**Goal:** Wire SemanticInterpreter into existing CodeFlow pipeline.

**Deliverables:**
- Modify `tools/codeflow/codeflow/report_generator.py`:
  - Add semantic interpretation as optional step
  - Accept semantic configuration
  - Return SemanticInterpretation alongside AnalysisResult
  - Cost tracking (tokens, API calls)

- Error handling:
  - LLM unavailable → graceful fallback to MockProvider
  - API error → retry with backoff
  - Timeout → partial results with warning

**Tests:**
- `tools/codeflow/tests/test_report_generator_semantic.py`
  - report_generator with and without semantic config
  - Cost tracking output
  - Fallback behavior on API error
  - Performance within acceptable range

**Acceptance:**
- ReportGenerator produces SemanticInterpretation
- Pipeline completes successfully
- No breaking changes to existing functionality
- Semantic step is optional and can be disabled

---

## Phase 5a Success Checklist

- [ ] LLM provider abstraction complete (4 implementations)
- [ ] SemanticInterpretation data model complete
- [ ] Evidence linking and validation working
- [ ] SemanticInterpreter service functional
- [ ] Configuration system (CLI, config file, env vars)
- [ ] Integration with ReportGenerator
- [ ] All 5a unit tests passing (90%+ coverage)
- [ ] Integration test passes with tic-tac-toe
- [ ] No hard-coded API keys
- [ ] Documentation of configuration options complete
- [ ] Ready for Phase 5b (document generation)

---

## Estimated Timeline

- Task 5a-1: LLMProvider abstraction — 3-4 days
- Task 5a-2: SemanticInterpretation model — 3-4 days
- Task 5a-3: Evidence linking — 3-4 days
- Task 5a-4: SemanticInterpreter service — 4-5 days
- Task 5a-5: Configuration system — 2-3 days
- Task 5a-6: ReportGenerator integration — 2-3 days
- **Total: 2-3 weeks**

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM API calls expensive | Cache results, track costs, provide mock fallback |
| JSON parsing errors from LLM | Strict schema validation, retry with stricter prompt |
| Evidence references invalid | Comprehensive validation, mark as INFERRED if invalid |
| Configuration confusion | Clear docs, sensible defaults, helpful error messages |
| Timeout on slow networks | Configurable timeout, partial results, graceful degradation |
