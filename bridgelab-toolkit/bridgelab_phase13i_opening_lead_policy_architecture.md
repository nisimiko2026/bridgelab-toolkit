# BridgeLab Phase 13I — Opening-Lead Policy Architecture

## Outcome

Policy architecture only: no card selection and no production recommendation.

## Benchmark

- Fixtures: 10
- Explicit / unresolved: 8 / 2
- Source-backed dimensions: 3
- Recommendations generated: 0

## Policy dimensions

- Length: FOURTH_BEST / THIRD_AND_FIFTH / OTHER / UNKNOWN
- Honor: STANDARD / RUSINOW / UNKNOWN
- Top of Nothing: ENABLED / DISABLED / UNKNOWN

Missing policy remains unresolved; it never implies Standard. Policy and OpeningLeadState remain separate.

## Source inventory

- `knowledge/play/defence/opening-leads/fourth-best.md` — Basic Principle — POLICY_EXECUTABLE
- `knowledge/play/defence/opening-leads/third-fifth.md` — Basic Principle — POLICY_EXECUTABLE
- `knowledge/play/defence/opening-leads/standard-leads.md` — Sequence Leads — POLICY_EXECUTABLE
- `knowledge/play/defence/opening-leads/rusinow.md` — Basic Principle — POLICY_EXECUTABLE
- `knowledge/play/defence/opening-leads/top-of-nothing.md` — Definition — POLICY_EXECUTABLE

Unsupported axes: mud, coded-tens-nines, journalist-leads, attitude-leads, unsupported-ace-king.

## Cumulative Phase 13

```json
{
  "abstentions": 3,
  "auction_positions": 5,
  "bidding_recommendations": 2,
  "declarer_positions": 23,
  "declarer_recommendations": 2,
  "defensive_positions": 15,
  "defensive_recommendations": 0,
  "errors": 0,
  "explicit_opening_lead_policies": 8,
  "no_decisions": 51,
  "opening_lead_policy_requests": 10,
  "opening_lead_positions": 14,
  "opening_lead_recommendations": 0,
  "probability_evidence_items": 3,
  "total_positions_or_requests": 80,
  "unresolved_policies": 2
}
```

## Phase 13J

B. OPENING-LEAD SOURCE-READINESS AUDIT
