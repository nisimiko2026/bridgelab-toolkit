# Phase 13C — Declarer State Architecture

## Canonical architecture

Phase 13C adds one immutable, strategy-free `DeclarerPlayState`. It reuses the production `Card`, `Suit`, `Rank`, `Seat`, `Vulnerability`, `Bid`, `Strain`, `Doubling`, and `Contract` types. Remaining declarer/dummy holdings use immutable card sets because `Hand` correctly represents only an original 13-card hand.

`PlayedCard` binds a canonical seat and card. `Trick` preserves clockwise order, led suit, completeness, and an objective winner for trump or notrump. Completed tricks and the current trick are the single ordered play-history source. Legal actions implement only follow-suit legality.

Validation covers distinct declarer/dummy seats through partnership derivation, declarer/dummy acting authority, duplicate/played-card conflicts, complete-history tricks, current-trick length/order, current actor order, contract/declarer consistency, and canonical types. Derived state exposes acting role/cards, legal actions, trick number, visible/played cards, unknown-card count, follow-suit requirement, and objectively determined trick counts. Hidden defender hands remain unknown.

The structured factory distinguishes missing contract, declarer seat/hand, dummy hand, actor, play history, and invalid card state. A complete state reaches `NO_DECISION/NONE/ENGINE_UNAVAILABLE`; incomplete state reaches `NO_DECISION/NONE/MISSING_STATE` with precise metadata. No recommendation algorithm is added.

## Benchmark and readiness

- Total positions: 20
- Auction positions: 5
- Declarer positions: 13
- Valid new declarer states: 8
- Invalid/incomplete declarer positions: 5
- Recommendations / abstentions / no-decisions / errors: 2 / 3 / 15 / 0
- Action counts: {'bid': 2, 'none': 18}

Probability readiness: {'restricted_choice': {'status': 'PARTIALLY_READY', 'missing': 'inference/event model for equivalent honors'}, 'vacant_places': {'status': 'PARTIALLY_READY', 'missing': 'defender known-card constraints'}, 'suit_distribution': {'status': 'PARTIALLY_READY', 'missing': 'probability calculator and defender constraints'}, 'trump_breaks': {'status': 'PARTIALLY_READY', 'missing': 'probability calculator'}, 'monte_carlo': {'status': 'PARTIALLY_READY', 'missing': 'consistent hidden-hand sampler and inference constraints'}}. The state supplies deterministic raw visible/play facts but intentionally adds no probability formula or hidden-hand inference.

Routes remain 45. Bidding rules/routes added: 0/0. Declarer algorithms added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13C: 0.

Selected Phase 13D: **A. FIRST DECLARER RECOMMENDATION ENGINE** — begin with one narrow, source-safe declarer technique rather than a general heuristic engine.

Current cumulative Full Kit: Phase 13C
