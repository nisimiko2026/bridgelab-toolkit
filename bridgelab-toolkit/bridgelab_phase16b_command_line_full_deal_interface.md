# BridgeLab Phase 16B — Command-Line Full-Deal Interface

## Existing CLI inventory

The repository has a user-owned Typer `main.py`, `commands/`, and no packaging script configuration. Phase 16B leaves them untouched and adds a narrow standalone module.

## CLI architecture and entry point

`python -m bridge.full_deal_cli --input request.json --format text|json` reads UTF-8 JSON (or `--input -`), converts through the Phase 16A application helper, and calls `analyze_full_deal_application` once. It never calls the production orchestrator or subsystem engines directly.

The schema reuses `deal`, `requested_stages`, and `probability_requests`; the first probability form is `known-card-count` with explicit visible/played cards and unknown count. Text reuses rendered text. JSON preserves status, errors, canonical structured result, rendered text, diagnostics, KnowledgeSource, ProbabilityEvidence, stage accounting, skips, and traces.

## Exit and stream contract

Exit codes are 0 success, 1 unexpected internal error, 2 usage/file/UTF-8/JSON error, 3 application validation or unsupported input, and 4 production error. Success is stdout; failures are stderr. JSON mode emits JSON only. pathlib, UTF-8, stdin, redirection, and ordinary Windows paths are supported.

## Focused benchmark

Fixtures/success/failed: 28/20/8.
Text/JSON successes: 10/9. Parse/application/production/internal failures: 3/5/0/0.
Application calls/duplicates: 24/0. Production calls/duplicates: 19/0.
Deterministic text/JSON repeats: 1/1. Structured/provenance JSON: 9/9.
Hidden-information violations and invented actions/numbers/sources/probabilities: 0.

## Cumulative Phase 16 and guards

```json
{
  "phase16a_application_requests": 22,
  "phase16b_application_interface_calls": 24,
  "phase16b_cli_executions": 28,
  "phase16b_production_orchestration_calls": 19
}
```

Phase 16A remains exactly 22 fixtures, 16/6 valid/invalid, 9/1/6/6 statuses, 3/2/1/0 failures, 16/0 production calls, 16/16 rendered/structured, 22/22 deterministic, and 22/22 provenance. Phase 15 remains complete with 17/17 readiness and Phase 14 remains complete. Production recommendations remain 4, routes remain 45, and ordinary bidding remains 7,871/761/9,239.

No bidding rules/routes, declarer/opening-lead/defensive algorithms, probability formulas, defaults, or canonical knowledge Markdown changed.

## Verification results

Phase 16B focused plus Phase 16A tests: 20 passed. Cumulative Phase 13–16 regressions: 262 passed. Full Phase 12 guards: 112 passed. Additional PolicyRegistry/router regressions: 28 passed. Ruff over every added or modified Python file: clean. The ordinary deterministic guard remains 7,871 production calls, 761 completed, and 9,239 abstained.

## Phase 16C decision

**E. PHASE 16 COVERAGE / CLOSURE AUDIT**

The application boundary and deterministic CLI satisfy the intended Phase 16 interface mission; the next measured step is closure rather than another interface implementation.

Current cumulative Full Kit: Phase 16B
