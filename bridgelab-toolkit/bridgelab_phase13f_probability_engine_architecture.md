# Phase 13F — Probability Engine Architecture

## Inventory

The repository contains one executable calculation: Phase 13C known-card accounting. `bridge.deals` provides deterministic seeded deals and `bridge.batch_simulation` provides bidding simulation, but neither calculates declarer probabilities or line success. Probability knowledge files contain prose/tables rather than callable formulas. No latent restricted-choice, vacant-place, suit/trump split, hypergeometric, Bayesian, or declarer Monte Carlo engine was found.

## Architecture

Immutable question variants represent known-card count, restricted choice, vacant places, suit distribution, trump breaks, and Monte Carlo inputs without inferring hidden facts. `ProbabilityContext` is built from `DeclarerPlayState` visible cards, played cards, and unknown count; it contains no defender hands.

`evaluate_probability` returns `SUCCESS`, `UNAVAILABLE`, `INVALID_INPUT`, or `ERROR`, plus explicit `EXACT`/`SIMULATED` mode, compact trace, and a real formula identifier where applicable. The immutable registry maps only `KnownCardCountQuestion` to the migrated `KNOWN_CARD_COUNT_V1` calculator. Other questions are architecturally representable but return `ENGINE_NOT_REGISTERED` with no numeric result. Phase 13E's `collect_declarer_probability_evidence` remains backward compatible and delegates through this engine boundary.

## Benchmark and readiness

- Questions: 7
- Success / unavailable / invalid / errors: 1 / 5 / 1 / 0
- Exact / simulated: 1 / 0
- Registered engines: ('KnownCardCountQuestion',)
- Readiness: {'KNOWN_CARD_COUNT': {'status': 'READY', 'engine': True, 'formula': True, 'tests': True, 'source': False, 'state_inputs': True, 'production_safe': True}, 'RESTRICTED_CHOICE': {'status': 'ARCHITECTURE_READY', 'engine': False, 'formula': False, 'tests': False, 'source': True, 'state_inputs': 'partial', 'production_safe': False}, 'VACANT_PLACES': {'status': 'ARCHITECTURE_READY', 'engine': False, 'formula': False, 'tests': False, 'source': True, 'state_inputs': 'partial', 'production_safe': False}, 'SUIT_DISTRIBUTION': {'status': 'ARCHITECTURE_READY', 'engine': False, 'formula': False, 'tests': False, 'source': True, 'state_inputs': True, 'production_safe': False}, 'TRUMP_BREAKS': {'status': 'ARCHITECTURE_READY', 'engine': False, 'formula': False, 'tests': False, 'source': True, 'state_inputs': True, 'production_safe': False}, 'MONTE_CARLO': {'status': 'PARTIALLY_READY', 'engine': False, 'formula': False, 'tests': False, 'source': False, 'state_inputs': 'partial', 'production_safe': False}}
- Extended architecture: {'total_positions_or_requests': 42, 'bidding_recommendations': 2, 'declarer_recommendations': 2, 'probability_evidence_items': 3, 'unavailable_evidence_requests': 8, 'invalid_input_results': 1, 'no_decisions': 23, 'errors': 0}

No formulas, declarer techniques, bidding rules, routes, defaults, or canonical knowledge were changed. Routes remain 45; the ordinary benchmark remains 7,871 / 761 / 9,239.

Selected Phase 13G: **E. DEFENSIVE STATE ARCHITECTURE**. With no safely adaptable probability formula, the probability boundary is complete enough and defense is the largest remaining end-to-end state gap.

Current cumulative Full Kit: Phase 13F
