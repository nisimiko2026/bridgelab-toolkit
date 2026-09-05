# BridgeLab Phase 14B — Deal-Summary Rendering / Explanation Engine

## Rendering architecture

`render_deal_summary` returns immutable `DealSummaryRendering` and ordered `DealSummaryRenderedSection` values. Each section retains its original summary item or probability result, exact sources/evidence, and stable trace metadata.

AVAILABLE, PARTIAL, NO_DECISION, and ERROR receive distinct deterministic wording. Recommendations render only their existing typed action and explanation; abstention, no-decision, and errors remain distinct. Exact probability facts, calculation mode, assumptions, known facts, and source IDs are rendered without confidence or odds.

## Focused benchmark

- Fixtures: 16
- AVAILABLE / PARTIAL / NO_DECISION / ERROR: 8 / 2 / 4 / 2
- Recommendation references: 11
- Evidence/source references: 17
- Unresolved / error sections: 8 / 1
- Deterministic repeats matched: 16/16
- Invented actions / numbers / sources / probabilities: 0 / 0 / 0 / 0

## Cumulative Phase 14

```json
{
  "cumulative_requests": 142,
  "production_recommendations": 4,
  "rendered_evidence_references": 17,
  "rendered_recommendation_references": 11,
  "rendered_unresolved_references": 8,
  "rendering_errors": 2,
  "rendering_requests": 16,
  "summary_recommendation_references": 8,
  "summary_requests": 16
}
```

Rendering references are not new production recommendations. Phase 14A remains 16 summaries, 8/1/5/2 statuses, and eight recommendation references. Phase 13L remains 16 closure fixtures and four production recommendations.

## Phase 14C

**D. DEAL-SUMMARY END-TO-END INTEGRATION**

The remaining summary gap is one coherent optional pipeline call returning structured and rendered forms without changing existing return types.

Routes remain 45. Ordinary bidding remains 7,871 / 761 / 9,239. Rules, routes, algorithms, formulas, defaults, and knowledge changes: 0.

Current cumulative Full Kit: Phase 14B
