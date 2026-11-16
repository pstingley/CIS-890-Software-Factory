# CIS 890 Software Factory — Agent Instructions

## 1. Specification-Driven Development

- Follow approved OpenSpec requirements.
- Do not expand scope without explicit user authorization.
- Validate OpenSpec changes using strict validation.
- Do not begin the next phase without user approval.

## 2. Completion and Acceptance

Never declare work COMPLETE, VERIFIED, ACCEPTED, or
PRODUCTION-READY simply because code was written or
automated tests passed.

Use these distinct statuses:

- IMPLEMENTED: Code has been written.
- TESTED: Automated tests have passed.
- VERIFIED: Requirements have been independently checked.
- ACCEPTED: The user has explicitly approved the result.

The implementing AI agent cannot independently approve
its own implementation.

## 3. Independent Verification

Every completion report must provide:

- Requirements implemented and their identifiers.
- Exact test commands executed.
- Actual test results and failure counts.
- Acceptance criteria demonstrated.
- Acceptance criteria not yet demonstrated.
- Known limitations and unresolved issues.
- Artifacts available for independent inspection.

Never dismiss failures as pre-existing without evidence.
Never claim an unexecuted test passed.

## 4. CodeFlow Requirements

CodeFlow must:

- Analyze source code without modifying or executing it.
- Preserve accurate execution paths in control-flow graphs.
- Generate readable HTML/SVG flowcharts.
- Generate human-readable prose documentation in DOCX.
- Generate language-independent behavioral specifications
  in SPEC.md.
- Preserve source-code traceability.
- Distinguish VERIFIED, INFERRED, and UNCERTAIN claims.
- Never invent unsupported users, purposes, or requirements.
- Treat PHP as an input language only.
- Never generate PHP source code.

## 5. Required Regression Tests

Run the complete CodeFlow test suite:

.venv/bin/python -m pytest tools/codeflow/tests/ -q -W error::DeprecationWarning

Run strict OpenSpec validation for the active change.

Passing tests does not establish complete functional acceptance.

## 6. Artifact Quality

Inspect actual generated artifacts, not just file existence.

Verify:
- Flowchart control-flow correctness and readability.
- Meaningful functional descriptions for managers and customers.
- Accurate technical descriptions for engineers.
- Source evidence for behavioral claims.
- Valid DOCX, SPEC.md, HTML/SVG, and JSON outputs.

## 7. Change Control

- Do not commit or push without user authorization.
- Do not modify unrelated code.
- Do not silently add dependencies.
- Do not continue into another implementation phase.
- Stop for independent review at each acceptance gate.

## 8. Final Reporting

Every implementation report must conclude with:

IMPLEMENTED:
TESTED:
INDEPENDENTLY VERIFIED:
NOT YET VERIFIED:
KNOWN LIMITATIONS:
AWAITING USER ACCEPTANCE:

Never substitute an optimistic completion statement
for independent acceptance evidence.

## 9. Git Whitespace and Formatting Requirements

- Never introduce trailing spaces or tabs.
- Never leave whitespace-only lines.
- Preserve existing line endings and formatting.
- Run `git diff --check` before staging changes.
- Run `git diff --cached --check` after staging changes.
- Correct all whitespace errors before declaring a commit ready.
- Preserve intentional Markdown formatting when necessary.
- Both checks must pass before committing.
