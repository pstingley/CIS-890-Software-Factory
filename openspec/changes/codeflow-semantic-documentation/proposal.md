# DOC-002 Proposal: Human-Readable Semantic Documentation

## Why

CodeFlow's current DOC-001 Word documentation provides valid structural control-flow analysis but fails to serve non-technical stakeholders, procurement decision-makers, compliance teams, and knowledge-transfer scenarios. The 18-page Tic-Tac-Toe report never explains what the application actually does—it repeats graph statistics ("6 statement nodes") instead of behavioral meaning. Managers cannot determine whether the system meets requirements. Engineers lack clear architectural explanations. This gap prevents CodeFlow from addressing realistic documentation needs in organizations.

DOC-002 solves this by adding evidence-based semantic interpretation: inferring purpose, users, capabilities, and behavior from control-flow analysis and grounding every claim in source code. Generated Functional_Description.docx explains *what* the software does (for stakeholders), while Technical_Description.docx explains *how* it works (for engineers). Both documents derive from the same verified interpretation, making them consistent and trustworthy. This positions CodeFlow as a complete reverse-engineering and documentation tool, not just a CFG visualizer.

## Problem Statement

CodeFlow 0.2 generates Microsoft Word documents (DOC-001) containing valid structural analysis of control-flow graphs, but the documentation lacks semantic meaning and fails to explain what the software actually does.

**Current Issue (DOC-001):**
- Executive summary never explains the Tic-Tac-Toe application is a "terminal-based, two-player game"
- Documents repeat technical graph metadata: "This function contains 6 statement nodes and 1 decision node"
- No explanation of purpose, users, capabilities, inputs, outputs, or behavior
- No distinction between technical (engineer-focused) and functional (stakeholder-focused) explanations
- No traceable evidence linking claims to source code

**Impact:**
- 18-page Word document fails to communicate software purpose to non-technical readers
- Managers, customers, and stakeholders cannot understand the system from the documentation
- Engineers lack clear architectural and behavioral explanations
- Current documentation is unsuitable for procurement, compliance, or knowledge transfer

## Solution Overview

DOC-002 adds LLM-assisted semantic interpretation to CodeFlow's documentation pipeline, generating two separate, high-quality Word documents:

1. **Functional_Description.docx** - For managers, customers, non-technical stakeholders
   - What the application does
   - Who uses it and why
   - Major capabilities and workflows
   - Expected inputs, outputs, and behavior
   - Constraints and limitations (from user perspective)

2. **Technical_Description.docx** - For software engineers
   - Architecture and component design
   - Major algorithms and data structures
   - Control flow and execution paths
   - Exception handling and error recovery
   - Integration points and dependencies

Both documents are grounded in CodeFlow's verified analysis model (CFG, semantic labels, source references) and use an LLM to interpret that data into human-readable explanations.

## Key Characteristics

### Semantic Grounding
- Every claim is linked to source evidence (line numbers, function names, control flow)
- Inferences are explicitly marked: "Based on code analysis, this appears to..." vs "The code implements..."
- Uncertain or dynamically determined behavior is identified without inventing functionality

### Evidence-Based Documentation
- Generated text explains *actual* behavior observed from analysis, not speculated functionality
- When behavior cannot be determined statically, the limitation is documented
- Source code references enable verification and traceability

### Quality Standards
- Avoid template repetition ("This function contains N nodes...")
- Provide functional explanations with context
- Distinguish observable behavior from architectural assumptions
- Document constraints and edge cases

### Configurable LLM Integration
- LLM provider is configurable, not hard-coded to Claude
- Can use different models based on deployment context
- Graceful degradation if LLM is unavailable
- Explicit cost tracking for LLM API calls

## Target Use Cases

1. **Procurement & Compliance**: Stakeholders need to understand system behavior before purchase/integration
2. **Knowledge Transfer**: New team members need functional and technical overviews
3. **Architecture Review**: Engineers need clear component and control-flow documentation
4. **API Documentation**: External developers need to understand system inputs/outputs
5. **Regulatory Documentation**: Compliance teams need to understand behavior for certification

## Success Criteria

✅ Non-technical reader can identify application purpose, users, major behaviors, and constraints from functional document without reading source code
✅ Engineer can understand architecture, components, algorithms, and data flow from technical document
✅ Every substantive claim is traceable to source evidence or explicitly marked as inference
✅ No template repetition or meaningless graph statistics
✅ Documents are generated within 10 seconds
✅ Quality meets or exceeds hand-written documentation
✅ Existing CodeFlow capabilities (CFG, HTML, JSON, SPEC.md) remain unchanged

## What Changes

**New Capabilities:**
- LLMProvider abstraction with pluggable providers (Claude, GPT-4, local, mock)
- SemanticInterpretation service infers system purpose, users, capabilities, and behavior
- Functional_Description.docx generator for non-technical stakeholders (plain English, operational focus)
- Technical_Description.docx generator for engineers (architecture, algorithms, control flow, evidence references)
- Evidence linking framework: every claim categorized as VERIFIED, INFERRED, or UNCERTAIN
- SPEC.md enhancement with semantic interpretation derived from same analysis
- Configuration system: CLI flags, config file, environment variables for LLM provider selection
- Cost tracking and threshold alerts for LLM API usage

**Modified Capabilities:**
- ReportGenerator extended to support semantic documentation pipeline
- SPEC.md updated to include behavioral interpretation and evidence references
- Configuration loading enhanced to support semantic provider settings

**Preserved Capabilities:**
- Control-flow graph analysis and generation (unchanged)
- Graph contraction algorithm (unchanged)
- HTML/SVG flowchart rendering (unchanged)
- JSON structured export (unchanged)
- DOC-001 Word documentation (unchanged)
- Python, Rust, PHP analyzers (unchanged)
- Non-invasive analysis requirement (unchanged)

## Implementation Approach

**Phase 5a: Infrastructure & Integration**
- Design LLM integration abstraction (configurable provider)
- Create semantic interpretation service
- Extend analysis pipeline to include semantic inference
- Add evidence collection and linking

**Phase 5b: Document Generation**
- Implement Functional_Description.docx generator
- Implement Technical_Description.docx generator
- Integrate LLM-generated explanations into document structure
- Add evidence references and source links

**Phase 5c: Quality & Testing**
- Develop acceptance tests for semantic quality
- Test cross-language support (Python, Rust)
- Validate evidence traceability
- Performance and cost benchmarking

## Deliverables

1. Updated OpenSpec: requirements.md, design.md, tasks.md
2. Semantic interpretation service (LLM integration abstraction)
3. Functional_Description and Technical_Description Word generators
4. Test suite validating semantic quality and evidence traceability
5. Configuration system for LLM provider selection
6. Cost tracking and usage reporting

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM generates false claims | Mandatory evidence linking; explicit inference markers; human review workflow |
| Hallucinated functionality | Grounding in verified CFG analysis; rejection of unsupported constructs |
| High API costs | Local model option; caching; progressive documentation (generate high-value sections first) |
| Poor documentation quality | Acceptance tests; automated quality scoring; human feedback loop |
| Slow generation | Parallel LLM requests; caching; incremental updates |

## Relationship to Existing Features

**Preserves:**
- CFG analysis and graph contraction
- HTML/SVG flowchart rendering
- JSON structured export
- SPEC.md language-independent specification
- DOC-001 Word document (simpler, graph-focused)

**Builds Upon:**
- CodeFlow's control-flow analysis (CFG source)
- Semantic labels (evidence for LLM)
- Source code references (traceability)
- Error/warning collection (constraints documentation)

**Adds:**
- LLM-assisted semantic interpretation
- Functional description document
- Technical description document
- Acceptance tests for documentation quality

## Timeline & Effort Estimate

- **Phase 5a Infrastructure**: 2-3 weeks (LLM integration, semantic service)
- **Phase 5b Document Generation**: 2-3 weeks (generators, templates)
- **Phase 5c Quality & Testing**: 1-2 weeks (tests, benchmarking, refinement)
- **Total**: 5-8 weeks (medium-sized feature)

## Next Steps

1. Review and approve DOC-002 proposal
2. Create detailed requirements specification
3. Design semantic interpretation architecture
4. Plan implementation in 3 phases
5. Begin Phase 5a infrastructure work
