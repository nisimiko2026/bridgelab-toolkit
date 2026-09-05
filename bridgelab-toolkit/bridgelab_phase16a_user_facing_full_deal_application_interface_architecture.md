# BridgeLab Phase 16A — User-Facing Full-Deal Application Interface Architecture

## Application architecture and immutable models

Immutable FullDealApplicationRequest, FullDealApplicationValidationResult, FullDealApplicationError, and FullDealApplicationResponse define a presentation-neutral boundary for future CLI, GUI, REST/API, and file-import adapters. Existing main.py and user-owned CLI work are untouched.

## Validation, conversion, and error model

`application_request_to_full_deal_input` parses only canonical Deal serialization and explicit stage aliases, reuses canonical stage inputs and policies, and produces FullDealAnalysisInput. Errors distinguish PARSE_ERROR, VALIDATION_ERROR, UNSUPPORTED_INPUT, and PRODUCTION_ERROR; ordinary invalid data never exposes a traceback.

## Application-to-production call graph

`FullDealApplicationRequest → validation/conversion → FullDealAnalysisInput → analyze_full_deal (once) → full_deal_analysis_to_dict → FullDealApplicationResponse`. The adapter never calls a subsystem, summary builder, renderer, or probability engine directly.

The structured response reuses canonical serialization, and rendered_text is the existing Phase 14B output. Canonical result objects preserve KnowledgeSource, ProbabilityEvidence, skips, stage accounting, status, and traces.

## Legal information boundaries

A complete Deal may be parsed for request identity but is never used to reconstruct stage inputs. Opening lead, declarer, defense, and probability retain explicit legal-view inputs.

## Focused benchmark

- Application fixtures and valid/invalid: 22; 16/6
- COMPLETE/PARTIAL/NO_DECISION/ERROR: 9/1/6/6
- Parse/validation/unsupported/production failures: 3/2/1/0
- Production/duplicate orchestration calls: 16/0
- Rendered/structured responses: 16/16
- Deterministic repeats and provenance-preserved responses: 22/22
- Hidden-information violations and invented actions/numbers/sources/probabilities: 0.

## Cumulative Phase 16 and guards

```json
{
  "phase16_application_requests": 22,
  "phase16_invalid_requests": 6,
  "phase16_production_orchestration_calls": 16,
  "phase16_valid_requests": 16,
  "production_recommendations": 4
}
```

Phase 15 remains complete: 17/17 readiness, 20 closure fixtures, 11/2/6/1 statuses, 28/26/26/3 stage accounting, 12/12/12 references, provenance 20/0, serialization 20/0, and repeats 20/20. Phase 14 remains complete. Routes remain 45; ordinary bidding remains 7,871/761/9,239.

Focused Phase 16A tests: 10 passed. Selected Phase 13A–16A, PolicyRegistry, and router regressions: 280 passed. Selected Phase 12 cumulative guards: 71 passed. Ruff: clean.

Added bridge rules, routes, algorithms, formulas, defaults, and canonical knowledge Markdown: 0.

## Future interface readiness and Phase 16B

**A. COMMAND-LINE FULL-DEAL INTERFACE**

The narrow application boundary is stable; the repository's existing command-oriented structure makes a CLI the safest first concrete human interface without new dependencies.

Current cumulative Full Kit: Phase 16A
