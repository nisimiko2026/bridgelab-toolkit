# Phase 13B — Declarer-Play Adapter / Recommendation Integration

## Inventory and integration decision

A repository-wide Python inventory found no production-capable declarer-play engine, state model, card recommender, restricted-choice calculator, vacant-places calculator, trump-break calculator, or Monte Carlo play engine. The play-related runtime files are knowledge retrieval/metadata maintenance; `bridge.playing_strength_policy` evaluates auction suitability and is not card play.

Consequently there is no canonical declarer production entry point to adapt. Phase 13B does not invent one. `analyze_deal_decision` now dispatches an explicit `DECLARER_PLAY` stage to a stable adapter boundary which returns `NO_DECISION`, `NONE`, and `MISSING_STATE`. It supplies no card, explanation beyond the factual integration gap, source, probability/counting evidence, or numeric confidence.

Restricted choice, vacant places, distribution probabilities, trump breaks, and Monte Carlo are all **NOT USED BY CURRENT DECLARER ENGINE**, because no such engine exists. Existing direct APIs are unchanged.

## Deterministic architecture benchmark

- Positions: 10
- Recommendations: 2
- Abstentions: 3
- No-decisions: 5
- Errors: 0
- Stage counts: {'auction': 5, 'deal-summary': 1, 'declarer-play': 3, 'defensive-play': 1}
- Action counts: {'bid': 2, 'none': 8}
- Ordinary benchmark: {'seeds': 10000, 'production_calls': 7871, 'completed': 761, 'abstained': 9239}
- Phase 12 guards: {'routes': 45, 'phase12n': 24, 'phase12o': 23, 'phase12q': 1194, 'phase12r': 166, 'phase12s': 540, 'phase12t': 33, 'phase12g': {'4H': 17, '4S': 21}, 'phase12h': 197, 'phase12l': {'completed': 5, 'abstained': 7}, 'jacoby': {'hearts': 62, 'spades': 61}}

The retained eight Phase 13A fixtures plus two repeated declarer missing-state fixtures prove stable dispatch and determinism. A successful declarer card fixture, explanation/source fixture, and probability fixture cannot honestly be supplied until a production state model and recommender exist.

## Compatibility and next phase

Auction behavior and the Phase 12N `2NT` result are unchanged. Routes remain 45. Bidding rules/routes added: 0. Production defaults changed: NO. Canonical knowledge Markdown changed by Phase 13B: 0.

Selected Phase 13C: **D. DECLARER STATE ARCHITECTURE**.

Current cumulative Full Kit: Phase 13B
