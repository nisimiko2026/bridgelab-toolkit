# Phase 13D — First Declarer Recommendation Engine

## Source audit and selection

The committed frozen source `play/declarer-play/general-techniques/unblock`, **Example 1 – Simple Unblock**, gives the exact combination dummy A-J-10-9 opposite declarer K-Q and explicitly orders: cash the king, then cash the queen. This candidate is `SOURCE_EXECUTABLE`. Marked finesse is `PROBABILITY_REQUIRED`; safety play and establishing long suits are `SOURCE_PARTIAL` because they require contract goals, entries, timing, defender information, or alternative-line evaluation absent from the state.

The selected `SIMPLE_UNBLOCK_KING` engine triggers only in notrump, with declarer leading an empty trick, exact K-Q in declarer's suit and exact A-J-10-9 in dummy, and exactly one matching suit. It recommends that suit's king only after confirming membership in `legal_actions`. Reversed hands, rank/suit near misses, nonempty tricks, suit contracts, missing cards, unrelated positions, and ambiguous multiple matches receive no recommendation. No probability model or fallback “play high” heuristic exists.

The result preserves the exact card, deterministic explanation and trace, and `KnowledgeSource`. Top-level normalization produces `CARD_PLAY`; incomplete states retain Phase 13C `MISSING_STATE` behavior.

## Benchmarks

- Declarer fixture positions: 10
- Recommendations / abstentions / no-decisions / errors: 3 / 0 / 7 / 0
- Technique hits: 3
- Near misses: 6
- Illegal recommendations: 0
- Extended architecture: {'total_positions': 30, 'auction_positions': 5, 'declarer_positions': 23, 'recommendations': 4, 'bidding_recommendations': 2, 'declarer_recommendations': 2, 'abstentions': 3, 'no_decisions': 23, 'errors': 0, 'action_counts': {'bid': 2, 'card-play': 2, 'none': 26}}

Routes remain 45. Bidding rules/routes added: 0/0. Declarer algorithms added: 1 narrow engine. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13D: 0.

Selected Phase 13E: **B. PROBABILITY-EVIDENCE ADAPTER**, because the next valuable techniques require explicit probability/counting evidence.

Current cumulative Full Kit: Phase 13D
