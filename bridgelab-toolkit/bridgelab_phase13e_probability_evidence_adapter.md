# Phase 13E — Probability-Evidence Adapter

## Inventory and readiness

The production inventory found one existing calculation suitable for normalization: Phase 13C's exact `visible_cards`, `played_cards`, and `unknown_card_count`. No production restricted-choice posterior, vacant-place weighting, suit-distribution, trump-break, or declarer-play Monte Carlo calculation exists. Deal/bidding simulation does not evaluate declarer lines and is not relabeled as probability evidence.

Readiness: {'known_card_count': {'status': 'READY', 'blocker': 'none'}, 'restricted_choice': {'status': 'NOT_READY', 'blocker': 'no production posterior calculator or typed event inputs'}, 'vacant_places': {'status': 'NOT_READY', 'blocker': 'no production seat-weight calculator or defender constraints'}, 'suit_distribution': {'status': 'NOT_READY', 'blocker': 'no production distribution calculator'}, 'trump_breaks': {'status': 'NOT_READY', 'blocker': 'no production trump-break calculator'}, 'monte_carlo': {'status': 'NOT_READY', 'blocker': 'no declarer-play sampler or line-success evaluator'}}

## Evidence contract and adapter

Immutable `ProbabilityEvidence` carries an evidence type, subject, assumptions, known facts, result, optional probability/alternatives/sample size, exact/simulated flags, optional source, and trace. Phase 13E defines only the actually supported `KNOWN_CARD_COUNT` type. `KnownCardCountQuestion` makes collection explicit and demand-driven; `collect_declarer_probability_evidence` reuses validated `DeclarerPlayState` accounting and never infers hidden defender cards.

Missing question/state and invalid accounting have structured outcomes. An unavailable request returns no evidence—not a misleading zero probability. The representative exact result is 8 visible + 0 played = 44 unknown; it is deterministic, nonsimulated, source-free computational evidence with no confidence metadata.

`DeclarerRecommendation` can carry immutable probability evidence, and `analyze_deal_decision` preserves attached items. `SIMPLE_UNBLOCK_KING` remains unchanged and carries an empty collection because it does not require probability evidence. The top-level analyzer never runs evidence families automatically.

## Benchmarks and guards

- Requests: 5
- Successful / unavailable / errors: 2 / 3 / 0
- Exact calculations / deterministic simulations: 2 / 0
- Counts: {'known-card-count': 2, 'unavailable': 3}
- Extended architecture: {'total_positions_or_requests': 35, 'bidding_recommendations': 2, 'declarer_recommendations': 2, 'probability_evidence_items': 2, 'unavailable_evidence_requests': 3, 'no_decisions': 23, 'errors': 0}

Routes remain 45. Bidding rules/routes added: 0/0. Declarer techniques added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13E: 0.

Selected Phase 13F: **E. PROBABILITY ENGINE ARCHITECTURE**, because the requested probability families have no production calculations to adapt safely.

Current cumulative Full Kit: Phase 13E
