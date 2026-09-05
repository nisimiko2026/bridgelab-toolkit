# Phase 13H — Opening-Lead State Architecture

## State and information boundary

`OpeningLeadState` is immutable and reuses canonical `Hand`, card/seat/contract types, an immutable `AuctionEntry` snapshot, and `ProbabilityContext`. It is distinct from `DefensivePlayState`: no card or trick exists yet, dummy is not exposed, and all 13 cards in the leader's hand are legal.

The leader must be immediately left of declarer; partner is derived canonically. Optional complete auction history is preserved without interpreting calls. Structural hand outputs include count, suit lengths, and honor holdings without ranking leads. Known-card accounting includes only the leader's 13 cards, yielding 39 unknown; no dummy, declarer, or partner cards exist in the model.

The factory distinguishes missing contract/declarer/leader seat/leader hand, wrong leader, caller-required missing auction, invalid hand state, and inconsistent contract/auction. A valid top-level state returns `NO_DECISION/NONE/ENGINE_UNAVAILABLE`; incomplete state returns `NO_DECISION/NONE/MISSING_STATE`. No lead is recommended.

## Policy audit and benchmark

Lead methods such as fourth-best versus third/fifth, honor sequences, top-of-nothing, and Rusinow are partnership-policy dependent. Other strategic families are partial or absent. Phase 13H assigns no default and implements no rule.

- Fixtures / valid / incomplete / invalid: 14 / 11 / 1 / 2
- Auction-present / probability-context builds: 1 / 11
- Opening-lead recommendations: 0
- Extended architecture: {'total_positions_or_requests': 70, 'auction_positions': 5, 'opening_lead_positions': 14, 'declarer_positions': 23, 'defensive_positions': 15, 'valid_opening_lead_states': 11, 'invalid_or_incomplete_opening_lead_states': 3, 'bidding_recommendations': 2, 'opening_lead_recommendations': 0, 'declarer_recommendations': 2, 'defensive_recommendations': 0, 'probability_evidence_items': 3, 'abstentions': 3, 'no_decisions': 51, 'errors': 0, 'action_counts': {'bid': 2, 'card-play': 2, 'none': 54}}

Routes remain 45. Bidding rules/routes added: 0/0. Opening-lead and defensive algorithms added: 0/0. Probability formulas added: 0. Defaults changed: NO. Canonical knowledge Markdown changed by Phase 13H: 0.

Selected Phase 13I: **B. OPENING-LEAD POLICY ARCHITECTURE**, because useful opening-lead treatments are primarily agreement-dependent and must not receive implicit defaults.

Current cumulative Full Kit: Phase 13H
