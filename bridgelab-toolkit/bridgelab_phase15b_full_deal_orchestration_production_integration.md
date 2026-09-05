# BridgeLab Phase 15B — Full-Deal Orchestration Production Integration

## Public API and production entry point

The package exports `FullDealAnalysisInput`, `FullDealProbabilityRequest`, `FullDealSkippedStage`, `FullDealAnalysisResult`, `FullDealSkipReason`, `analyze_full_deal`, and `full_deal_analysis_to_dict`. `analyze_full_deal` remains the sole production orchestration engine; no competing wrapper was introduced.

## Stable result and status contract

The immutable result exposes original request identity, requested/applicable/attempted/skipped stages, canonical subsystem and probability results, DealSummaryResult, DealSummaryRendering, DealSummaryPipelineResult, final status, trace, and Phase 14B rendered text. COMPLETE, PARTIAL, NO_DECISION, and ERROR retain Phase 15A semantics.

## Production call graph and legal information boundaries

`caller → analyze_full_deal → canonical stage adapters → DealSummaryInput → build_and_render_deal_summary → FullDealAnalysisResult`. Each requested applicable subsystem runs at most once; summary and rendering each build once. The complete Deal is never passed to stage adapters, and legal-view inputs remain unchanged.

## Skips, errors, and serialization

Skipped stages retain stage, typed reason, and explanation. Invalid top-level objects, invalid stage values, and invalid probability requests return deterministic ERROR results. Missing or malformed canonical stage state remains an existing typed no-decision rather than an opaque exception.

`full_deal_analysis_to_dict` provides deterministic machine-readable statuses, stage lists, actions, explanations, source IDs, probability metadata, skipped reasons, rendered text, and traces while the object result remains the authoritative provenance graph.

## Focused production benchmark

- Public fixtures: 18
- COMPLETE/PARTIAL/NO_DECISION/ERROR: 9/2/6/1
- Requested/attempted/skipped references: 29/26/4
- Subsystem evaluations: {'auction': 7, 'opening-lead': 6, 'declarer-play': 4, 'defensive-play': 3, 'probability-evidence': 6}
- Duplicate evaluations and summary/rendering builds: 0; 18/18
- Production recommendations / orchestration references: 4/11
- Summary/rendered references: 11/11
- Evidence/unresolved references: 17/9
- API export/serialization failures: 0/0
- Deterministic repeats: 18/18
- Hidden-information violations, recomputation, and invented actions/numbers/sources/probabilities: 0.

## Cumulative Phase 15 and guards

```json
{
  "phase15_cumulative_requests": 36,
  "phase15a_architecture_requests": 18,
  "phase15a_orchestration_references": 12,
  "phase15b_orchestration_references": 11,
  "phase15b_production_integration_requests": 18,
  "production_recommendations": 4
}
```

Phase 15A remains exactly 18 fixtures; 9/3/6/0 statuses; 30/29/1 requested/attempted/skipped; stage evaluations 8/7/4/4/6; 12 recommendation references; 18 evidence, 11 unresolved, and 18/18 repeats. Phase 14 remains complete. Routes remain 45 and ordinary bidding remains 7,871/761/9,239.

Focused Phase 15B tests: 10 passed. Selected Phase 13A–15B, PolicyRegistry, and router regressions: 260 passed. Selected Phase 12 cumulative guards: 71 passed. Ruff: clean.

Added rules, routes, algorithms, formulas, defaults, and canonical knowledge Markdown: 0.

## Phase 15C

**A. PHASE 15 COVERAGE / CLOSURE AUDIT**

The production surface is complete; Phase 15 should now be measured and closed.

Current cumulative Full Kit: Phase 15B
