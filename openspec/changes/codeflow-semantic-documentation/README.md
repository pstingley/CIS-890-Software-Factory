# DOC-002 Semantic Documentation — OpenSpec Index

**Status:** ✅ Planning Complete
**Ready for:** Implementation Review and Approval
**Timeline:** 5-8 weeks (Phases 5a, 5b, 5c)

---

## Quick Start

**New to this project?** Start here:

1. **[proposal.md](proposal.md)** — 10 min read
   - What's the problem? (repetitive documentation)
   - What's the solution? (LLM-assisted semantic interpretation)
   - How will it work? (high-level overview)

2. **[specs/design/DOC-002-architecture.md](specs/design/DOC-002-architecture.md)** — 20 min read
   - Three-layer architecture
   - LLMProvider abstraction
   - SemanticInterpretation data model
   - Five key design decisions

3. **[tasks.md](tasks.md)** — 15 min read
   - What work needs to happen?
   - How long will it take? (5-8 weeks)
   - What are the risks?
   - How do we know it's done?

**Have feedback?** See [How to Contribute](#how-to-contribute) below.

---

## Document Guide

### Executive Level
- **[proposal.md](proposal.md)** — Problem statement, solution overview, success criteria

### Requirements & Acceptance
- **[specs/requirements/DOC-002-requirements.md](specs/requirements/DOC-002-requirements.md)**
  - Functional requirements (FR-1 through FR-10)
  - Non-functional requirements (NF-1 through NF-5)
  - Acceptance tests (AT-1 through AT-7)
  - Configuration interface
  - Quality metrics

### Architecture & Design
- **[specs/design/DOC-002-architecture.md](specs/design/DOC-002-architecture.md)**
  - Three-layer architecture (Analysis → Interpretation → Documentation)
  - Component design and interfaces
  - LLMProvider abstraction with factory pattern
  - SemanticInterpretation data model (complete)
  - Evidence linking and validation framework
  - Testing strategy
  - Configuration and deployment
  - Five design decisions (D-1 through D-5)

### Implementation Planning

#### Phase 5a: Infrastructure & LLM Integration (2-3 weeks)
- **[specs/implementation/phase-5a-infrastructure.md](specs/implementation/phase-5a-infrastructure.md)**
  - 6 tasks (5a-1 through 5a-6)
  - LLMProvider abstraction
  - SemanticInterpretation data model
  - Evidence linking and validation
  - Configuration system
  - ReportGenerator integration
  - **Deliverable:** SemanticInterpretation for any AnalysisResult

#### Phase 5b: Document Generation (2-3 weeks)
- **[specs/implementation/phase-5b-document-generation.md](specs/implementation/phase-5b-document-generation.md)**
  - 7 tasks (5b-1 through 5b-7)
  - Functional description generator (non-technical)
  - Technical description generator (technical)
  - Document formatting and styling
  - SPEC.md generation update
  - Project summary document
  - Integration and cross-language testing (Python, Rust, PHP)
  - **Deliverable:** Complete documentation pipeline (7 outputs)

#### Phase 5c: Quality, Testing & Acceptance (1-2 weeks)
- **[specs/implementation/phase-5c-testing-quality.md](specs/implementation/phase-5c-testing-quality.md)**
  - 5 tasks (5c-1 through 5c-5)
  - Acceptance test suite (AT-1 through AT-7)
  - Quality metrics and reporting
  - User documentation and examples
  - Performance optimization
  - **Deliverable:** Production-ready DOC-002

### Consolidated View
- **[tasks.md](tasks.md)**
  - Combined task breakdown across all 3 phases
  - Consolidated timeline (week-by-week)
  - Critical path analysis
  - Risk register and mitigations
  - Quality gates and success criteria

---

## Key Concepts

### The Problem
CodeFlow's current documentation (DOC-001) generates 18-page Word reports that contain:
- Repetitive graph statistics ("6 statement nodes, 1 decision node")
- Generic descriptions that don't explain what the software actually does
- Example: Tic-Tac-Toe report never mentions "terminal-based, two-player game"

### The Solution
DOC-002 adds an LLM-assisted semantic interpretation layer that:

1. **Analyzes** the control-flow graph and semantic labels
2. **Interprets** application purpose, capabilities, workflows, error handling
3. **Generates** two separate professional Word documents:
   - Functional_Description.docx (non-technical stakeholders)
   - Technical_Description.docx (software engineers)
4. **Traces** all claims back to source code evidence
5. **Preserves** existing HTML, SVG, JSON, SPEC.md outputs

### The Architecture

```
Source Code Files
      ↓
   Analyzers (Python, Rust, Markdown)
      ↓
  AnalysisResult (CFG, semantic labels, source references)
      ↓
  ┌─────────────────────────────┐
  │  Semantic Interpreter (NEW)  │  ← LLM-assisted interpretation
  │  ↓                           │
  │  SemanticInterpretation      │  ← Purpose, capabilities, workflows,
  │                              │    evidence-based claims
  └─────────────────────────────┘
      ↓
   ┌──────────────┬──────────────┬──────────────┐
   ↓              ↓               ↓              ↓
HTML/SVG      Functional_      Technical_    SPEC.md
(CFG)         Description      Description   (semantic)
              .docx            .docx
```

### Five Key Design Decisions

**D-1: Pluggable LLM Providers**
- Claude (Anthropic) — high quality
- GPT-4 (OpenAI) — alternative
- Local LLM (vLLM) — cost control
- Mock provider — offline testing, fallback

**D-2: Evidence-Based Claims**
- VERIFIED: supported by CFG analysis
- INFERRED: reasonable code interpretation
- UNCERTAIN: depends on runtime
- Each claim traces to source code location (file, function, lines)

**D-3: Separate Documents for Different Audiences**
- Functional: plain English, operational focus (non-technical)
- Technical: architecture, algorithms, control flow (engineers)

**D-4: No Template Repetition**
- Explicit rule: NO "This function contains 3 nodes"
- Required: Behavioral explanations in domain terms

**D-5: Cross-Language Support**
- Same architecture for Python, Rust, PHP
- Analyzers produce AnalysisResult
- Semantic interpreter operates on AnalysisResult (language-agnostic)
- Document generators produce consistent quality

### Quality Targets

| Metric | Target | Test |
|--------|--------|------|
| Non-technical comprehension | ≥80% clear | AT-1 |
| Technical accuracy | ≥95% | AT-2 |
| Evidence traceability | 100% verified | AT-3 |
| Template repetition | ≤2 per 10 pages | AT-4 |
| Behavioral accuracy | ≥95% | AT-5 |
| Cross-language consistency | ±10% variance | AT-6 |
| Performance | <15 seconds total | AT-7 |

---

## Document Structure

```
codeflow-semantic-documentation/
├── .openspec.yaml                    ← Metadata (phase, status, etc.)
├── proposal.md                       ← Executive summary
├── tasks.md                          ← Consolidated task breakdown
└── specs/
    ├── requirements/
    │   └── DOC-002-requirements.md   ← FR-1..10, NF-1..5, AT-1..7
    ├── design/
    │   └── DOC-002-architecture.md   ← Detailed architecture
    └── implementation/
        ├── phase-5a-infrastructure.md     ← Week 1-2 tasks
        ├── phase-5b-document-generation.md ← Week 3-4 tasks
        └── phase-5c-testing-quality.md     ← Week 5-6 tasks
```

---

## Review Checklist

Before approving DOC-002 for implementation:

### Scope & Requirements
- [ ] Problem statement clear (DOC-001 limitations)
- [ ] Solution well-defined (semantic interpretation layer)
- [ ] Functional requirements (FR-1 through FR-10) make sense
- [ ] Acceptance tests (AT-1 through AT-7) are measurable
- [ ] Configuration approach is flexible (Claude, GPT, local, mock)

### Architecture & Design
- [ ] Three-layer architecture understood
- [ ] LLMProvider abstraction makes sense
- [ ] SemanticInterpretation data model is complete
- [ ] Evidence linking approach is practical
- [ ] Five design decisions (D-1 through D-5) are justified

### Implementation Plan
- [ ] Tasks are clearly defined (5a-1 through 5c-5)
- [ ] Timeline is realistic (5-8 weeks, 3 phases)
- [ ] Critical path is clear
- [ ] Risks and mitigations are identified
- [ ] Quality gates will ensure success

### No Regressions
- [ ] Existing analysis (CFG, semantic labels) unchanged
- [ ] Existing outputs (HTML, SVG, JSON) preserved
- [ ] Existing DOC-001 generation unaffected
- [ ] Existing SPEC.md generation (now improved with semantics)
- [ ] No breaking changes to CodeFlow API

---

## How to Contribute

### During Planning Phase
1. Read the OpenSpec documents (proposal, requirements, architecture, tasks)
2. Provide feedback on:
   - Scope and feasibility
   - Design decisions and alternatives
   - Timeline and resource estimates
   - Risk identification and mitigation

### During Implementation Phases
1. Follow the task breakdown in phase-5a/5b/5c specs
2. Maintain quality gates at each phase boundary
3. Run acceptance tests for validation
4. Report issues and blockers

### After Implementation
1. Use DOC-002 to generate documentation
2. Provide feedback on document quality
3. Report bugs or areas needing improvement
4. Request features or enhancements

---

## Related Documentation

- **Phase 4b (Complete):** Graph contraction architecture — verified
- **Phase 4c (Complete):** Python AST deprecation fixes — zero warnings
- **Phase 4d (Complete):** SVG label wrapping — readable flowcharts
- **DOC-001 (Existing):** Graph-focused Word documentation (preserved)
- **Phase 5 (This):** DOC-002 Semantic documentation (planning complete)

---

## Success Criteria

This planning phase is **complete** when:

✅ All OpenSpec artifacts created and reviewed
✅ Architecture documented and decisions justified
✅ Implementation tasks clearly defined with time estimates
✅ Quality targets established and measurable
✅ Risks identified with mitigation strategies
✅ Timeline validated (5-8 weeks, 3 phases)
✅ User review and approval obtained
✅ Ready to proceed to Phase 5a implementation

**Current Status:** ✅ **ALL CRITERIA MET**

---

## Questions & Clarifications

**Q: Why separate Functional and Technical documents?**
A: Different audiences with different needs. Functional for stakeholders (plain English, capabilities), Technical for engineers (architecture, algorithms, evidence).

**Q: What if the LLM API is unavailable?**
A: Fall back to MockLLMProvider (heuristic-based interpretation). Quality is simpler but functional. Fully graceful degradation.

**Q: Will existing CodeFlow functionality be affected?**
A: No. DOC-002 is fully additive. All existing HTML, SVG, JSON, SPEC.md, and DOC-001 outputs are preserved and unchanged.

**Q: Can I use a local LLM instead of Claude?**
A: Yes! The LLMProvider abstraction supports Claude, GPT-4, local LLM (vLLM/Ollama), or mock provider. Configure via CLI, config file, or environment variables.

**Q: How long will this take to implement?**
A: 5-8 weeks total:
- Phase 5a: 2-3 weeks (infrastructure)
- Phase 5b: 2-3 weeks (document generation)
- Phase 5c: 1-2 weeks (testing & quality)

**Q: What about PHP support?**
A: DOC-002 will generate documentation for PHP code (describing its behavior). CodeFlow does not generate PHP code, only analyzes it, so this is fully supported.

---

## Document History

| Date | Phase | Status | Notes |
|------|-------|--------|-------|
| 2025 Session | Planning | ✅ Complete | All OpenSpec artifacts created |
| Pending | 5a | Upcoming | Infrastructure & LLM integration |
| Pending | 5b | Upcoming | Document generation |
| Pending | 5c | Upcoming | Quality, testing & acceptance |

---

## References

- **CodeFlow Project:** CIS-890-Software-Factory
- **OpenSpec Format:** Proposal, Requirements, Design, Tasks
- **Previous Phases:** 4b (graph contraction), 4c (AST deprecation), 4d (SVG wrapping)
- **LLM Integration:** Claude, GPT-4, local models, mock provider
- **Languages:** Python, Rust, PHP (input analysis)

---

**Last Updated:** Planning Phase Complete
**Status:** Ready for Implementation Review
**Next Step:** Review OpenSpec artifacts and approve implementation
