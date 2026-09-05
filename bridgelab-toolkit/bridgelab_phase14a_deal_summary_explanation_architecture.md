# BridgeLab Phase 14A — Deal-Summary / Explanation Architecture

## Architecture

Immutable `DealSummaryInput`, `DealSummaryItem`, and `DealSummaryResult` aggregate original `DealAnalysisResult` and `ProbabilityEngineResult` objects. Statuses are AVAILABLE, PARTIAL, NO_DECISION, and ERROR; failures distinguish missing input, invalid stage results, and duplicate stages.

Canonical order is auction, opening lead, declarer play, defensive play, then probability evidence. Existing actions, explanations, abstention codes, `KnowledgeSource`, exact calculation modes, evidence assumptions, known facts, and traces remain on their original immutable objects.

The builder does not compute bridge decisions, probabilities, confidence, hidden cards, or an overall best action.

## Focused benchmark

- Summaries: 16
- Available / partial / no-decision / error: 8 / 1 / 5 / 2
- Recommendation references: 8 (bidding 6, declarer 2)
- Evidence / unresolved / source-backed: 11 / 6 / 11
- Invented recommendations / probabilities: 0 / 0

## Cumulative Phase 14

```json
{
  "cumulative_requests": 126,
  "phase13_closure_requests": 16,
  "production_recommendations": 4,
  "summary_errors": 2,
  "summary_evidence_items": 11,
  "summary_recommendation_references": 8,
  "summary_requests": 16,
  "unresolved_summary_items": 6
}
```

Summary references are not counted as new production recommendations. Phase 13L remains 16 fixtures, four production recommendations, two abstentions, nine no-decisions, one evidence result, zero errors, and 25% recommendation rate.

## Phase 14B

**A. DEAL-SUMMARY RENDERING / EXPLANATION ENGINE**

The structured aggregation boundary is complete; the next gap is a deterministic renderer over these preserved fields.

Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Algorithms, formulas, rules, routes, defaults, and canonical knowledge changes: 0.

Current cumulative Full Kit: Phase 14A
