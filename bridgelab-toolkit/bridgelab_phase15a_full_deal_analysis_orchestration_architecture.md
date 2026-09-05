# BridgeLab Phase 15A — Full-Deal Analysis / Orchestration Architecture

## Architecture inventory and models

Immutable `FullDealAnalysisInput` reuses canonical Deal, AnalysisStage, BiddingContext, OpeningLeadInput, DeclarerPlayInput, DefensivePlayInput, ProbabilityQuestion/ProbabilityContext, and PolicyRegistry types. `FullDealAnalysisResult` retains the original request, requested/applicable/attempted/skipped stages, original subsystem and probability results, and the Phase 14 pipeline result.

## Stage selection and information boundaries

Stages run in auction, opening-lead, declarer-play, defensive-play, probability order. Selection is explicit; missing state and unavailable engines become typed skips or existing subsystem no-decisions. The complete Deal is retained for caller identity only and is never passed to an adapter. Each adapter receives only its canonical legal-view input, and probability work runs only for explicit questions with an explicit legal-view context.

## Subsystem orchestration and summary integration

`analyze_full_deal` calls each requested applicable subsystem once, constructs DealSummaryInput from those exact results, and calls `build_and_render_deal_summary` once. Existing auction, opening-lead, declarer, defense, probability, summary, and rendering functions are reused; no second renderer or decision engine exists.

## Focused benchmark

- Fixtures: 18
- COMPLETE/PARTIAL/NO_DECISION/ERROR: 9/3/6/0
- Requested/attempted/skipped stage references: 30/29/1
- Auction/opening/declarer/defense/probability evaluations: 8/7/4/4/6
- Production recommendations / orchestration references: 4/12
- Summary/rendered references: 12/12
- Evidence/unresolved references: 18/11
- Summary/rendering builds and deterministic repeats: 18/18/18
- Hidden-information violations, recomputation, invented actions/numbers/sources/probabilities: 0/0/0/0/0/0.

## Cumulative Phase 15 and guards

```json
{
  "orchestration_recommendation_references": 12,
  "phase14d_closure_fixtures": 16,
  "phase14d_provenance_lost": 0,
  "phase14d_provenance_preserved": 16,
  "phase15_requests": 18,
  "production_recommendations": 4
}
```

Phase 14D remains 16 closure fixtures, 16/16/16 successes, 9/3/3/1 statuses, four production recommendations, 13/13/13 references, 21 evidence references, eight unresolved references, 16/0 provenance, and 16/16 repeats. Routes remain 45; ordinary bidding remains 7,871/761/9,239.

Focused Phase 15A tests: 10 passed. Selected Phase 13A–15A, PolicyRegistry, and router regressions: 250 passed. Selected Phase 12 cumulative guards: 71 passed. Ruff: clean.

Rules, routes, declarer/opening/defensive algorithms, probability formulas, defaults, and canonical knowledge changes: 0.

## Phase 15B

**A. FULL-DEAL ORCHESTRATION PRODUCTION INTEGRATION**

The architecture is complete and intentionally separate from existing callers; the next step is controlled top-level production wiring.

Current cumulative Full Kit: Phase 15A
