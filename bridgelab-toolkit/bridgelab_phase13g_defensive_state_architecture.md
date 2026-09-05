# Phase 13G — Defensive State Architecture

## State and knowledge boundary

`DefensivePlayState` is immutable and reuses canonical `Card`, `Suit`, `Rank`, `Seat`, `Vulnerability`, `Bid`, `Strain`, `Doubling`, `Contract`, `PlayedCard`, `Trick`, and `legal_cards`. It stores only the acting defender's remaining cards, exposed dummy cards, and validated play history. Partner and declarer hidden holdings are neither required nor represented.

The factory distinguishes missing contract/declarer/defender/dummy/actor/history, declarer or dummy acting illegally as defender, inconsistent trick order, and other invalid card state. Derived properties expose declarer, dummy, defender partner, exact legal actions, follow-suit status, trick number/counts, visible/played cards, and unknown-card count. `build_defensive_probability_context` exports only those defender-known facts.

Incomplete top-level defensive analysis returns `NO_DECISION/NONE/MISSING_STATE` with precise metadata. A valid state returns `NO_DECISION/NONE/ENGINE_UNAVAILABLE`. Phase 13G selects no card and adds no defensive algorithm. `OPENING_LEAD` remains a distinct unintegrated stage.

## Signaling and policy audit

Canonical knowledge covers attitude, count, suit preference, standard and upside-down signals, carding styles, and opening-lead agreements. These are partnership-policy dependent; Phase 13G implements none and sets no defaults.

## Benchmark

- Fixtures / valid / incomplete / invalid: 14 / 9 / 2 / 3
- Follow-suit / void cases: 1 / 1
- Defensive recommendations: 0
- Extended architecture: {'total_positions_or_requests': 56, 'auction_positions': 5, 'declarer_positions': 23, 'defensive_positions': 15, 'valid_defensive_states': 9, 'invalid_or_incomplete_defensive_states': 6, 'bidding_recommendations': 2, 'declarer_recommendations': 2, 'defensive_recommendations': 0, 'abstentions': 3, 'no_decisions': 37, 'errors': 0, 'action_counts': {'bid': 2, 'card-play': 2, 'none': 40}}
- Probability readiness: {'KNOWN_CARD_COUNT': 'READY', 'RESTRICTED_CHOICE': 'ARCHITECTURE_READY', 'VACANT_PLACES': 'ARCHITECTURE_READY', 'SUIT_DISTRIBUTION': 'ARCHITECTURE_READY', 'TRUMP_BREAKS': 'ARCHITECTURE_READY', 'MONTE_CARLO': 'PARTIALLY_READY'}

Routes remain 45. Bidding rules/routes added: 0/0. Defensive algorithms added: 0. Probability formulas added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13G: 0.

Selected Phase 13H: **B. OPENING-LEAD STATE ARCHITECTURE**, because opening lead is the remaining distinct play-stage state gap and can reuse the new defensive foundations.

Current cumulative Full Kit: Phase 13G
