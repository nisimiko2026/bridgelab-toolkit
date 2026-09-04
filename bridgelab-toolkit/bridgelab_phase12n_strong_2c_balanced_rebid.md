# Phase 12N — Source-Gated Strong 2C Balanced 22–24 Rebid

## Exact source contract

- Auction: `2C-P-2D-P`
- Opener: balanced, 22–24 HCP inclusive
- Call: `2NT`
- All non-target hands: `ABSTAIN`

The production rule reuses `BiddingContext.evaluation.is_balanced`, whose
canonical runtime distributions are 4-3-3-3, 4-4-3-2, and 5-3-3-2. It reuses
`BiddingContext.evaluation.hcp`, populated by the existing
`evaluate_hand`/`high_card_points` calculation (A=4, K=3, Q=2, J=1).

## Deterministic benchmark

- Seeds: 1–10,000
- Strong-2C rebid family: 47
- Balanced 22–24 target subset: 24
- Phase 12N newly handled `2NT`: 24
- Pre-existing calls: 0
- Remaining abstentions: 23

## Routing and guards

- Routes before: 44
- Routes after: 45
- New exact route: `sayc.opener.2c.2d.balanced`
- Production defaults: unchanged
- Phase 12G: 4H=17, 4S=21
- Phase 12H residual: 197
- Phase 12K no-policy dual-major abstentions: 36
- Phase 12L: HEARTS=5, SPADES=7
- Jacoby no-policy: 62 + 61 = 123
- Knowledge Markdown changes: 0

The remaining 23 positions are not assigned suit rebids or any inferred call.

Recommended next phase: Phase 12O — Strong 2C Rebid Residual Source Audit

Current cumulative Full Kit: Phase 12N
