# BridgeLab Phase 14C — Deal-Summary End-to-End Integration

## Integration architecture

`build_and_render_deal_summary` accepts already-computed `DealSummaryInput`, invokes `build_deal_summary` once, invokes `render_deal_summary` once, and returns immutable `DealSummaryPipelineResult`. Existing `analyze_deal_decision` behavior and return type are unchanged.

The result exposes original subsystem objects, structured summary, rendered summary, rendered text, explicit integration status, and narrow structural failure codes. Provenance remains navigable through rendered section → summary item → original result and through probability section → original engine result/evidence.

## Focused benchmark

- Fixtures: 16
- Complete / partial / no-decision / error: 9 / 3 / 3 / 1
- Summary / rendering builds: 16 / 16
- Integrated / rendered recommendation references: 13 / 13
- Evidence / unresolved references: 21 / 7
- Provenance preserved / deterministic repeats: 16 / 16
- Invented actions/numbers/sources/probabilities and recomputed recommendations: 0

## Cumulative Phase 14

```json
{
  "cumulative_requests": 158,
  "integrated_evidence_references": 21,
  "integrated_recommendation_references": 13,
  "integrated_unresolved_references": 7,
  "integration_errors": 1,
  "integration_requests": 16,
  "production_recommendations": 4,
  "rendered_recommendation_references": 11,
  "rendering_requests": 16,
  "summary_recommendation_references": 8,
  "summary_requests": 16
}
```

Underlying production recommendations remain four; summary, rendering, and integration counts are references only. Historical Phase 14A, Phase 14B, and Phase 13L metrics remain unchanged.

## Historical guards

- Phase 14A: 16 fixtures; AVAILABLE/PARTIAL/NO_DECISION/ERROR = 8/1/5/2; recommendation references = 8 (bidding 6, declarer 2).
- Phase 14B: 16 fixtures; AVAILABLE/PARTIAL/NO_DECISION/ERROR = 8/2/4/2; rendered recommendation references = 11; deterministic repeats = 16/16.
- Phase 13L: 16 fixtures; production recommendations/abstentions/no-decisions/evidence/errors = 4/2/9/1/0; recommendation rate = 25%.
- Opening-lead/defensive algorithms = 0/0; registered probability engines = 1; no new declarer algorithm or probability formula.

## Regression validation

- Phase 14C focused tests: 10 passed.
- Selected Phase 13A–14C, PolicyRegistry, and router regressions: 230 passed.
- Selected Phase 12 cumulative guards: 71 passed.
- Ruff over every Phase 14C Python file: clean.
- Ordinary deterministic benchmark: production calls/completed/abstained = 7,871/761/9,239.

## Phase 14D

**D. PHASE 14 COVERAGE / CLOSURE AUDIT**

Summary architecture, deterministic rendering, and one-pass integration are complete and should now be measured and closed.

Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Rules, routes, algorithms, formulas, defaults, and knowledge changes: 0.

Current cumulative Full Kit: Phase 14C
