# Phase 12M — Next Deterministic Family Source-Readiness Audit

## Deterministic sample

- seeds 1–10,000
- ordinary no-policy production configuration
- production routes: 44
- candidate families: 9

Explicitly deferred families: Phase 12H Stayman residuals (197), Phase 12L dual-major downstream residuals (HEARTS 31, SPADES 29). Each is `DEFERRED_EXISTING` and excluded from selection.

## Complete candidate-family inventory

| Family ID | Auction prefix(es) | Seat | Count | Action | Route(s) | Rule abstains | Stops before rule | Frozen source | Classification |
|---|---|---|---:|---|---|---|---|---|---|
| opener.one-level-rebid-existing-rule | 1C P 1D P<br>1C P 1H P<br>1C P 1NT P<br>1C P 1S P<br>1D P 1S P<br>1D P 2NT P<br>1D P 3NT P<br>1H P 1S P<br>1H P 2H P<br>1H P 3H P<br>1S P 2S P<br>1S P 3S P | N | 406 | ABSTAIN | sayc.opener.1c.1d, sayc.opener.1c.1h, sayc.opener.1c.1s, sayc.opener.1d.1s, sayc.opener.1h.1s, sayc.opener.1h.2h, sayc.opener.1s.2s | YES | NO | ../knowledge/bidding/natural-bids/rebids/opening-rebids.md | SOURCE_PARTIAL |
| opener.strong-two-club-after-waiting | 2C P 2D P | N | 47 | ABSTAIN | NONE | NO | YES | ../knowledge/bidding/natural-bids/responses/response-to-2-clubs.md | SOURCE_PARTIAL |
| opening.unresolved | <opening> | N | 5889 | ABSTAIN | sayc.opening | YES | NO | ../knowledge/bidding/natural-bids/opening-bids/opening-requirements.md | SOURCE_PARTIAL |
| responder.rebid-after-opener-rebid | 1C P 1D P 1H P<br>1C P 1D P 1NT P<br>1C P 1D P 1S P<br>1C P 1D P 2C P<br>1C P 1H P 1NT P<br>1C P 1H P 1S P<br>1C P 1H P 2C P<br>1C P 1H P 2H P<br>1C P 1S P 1NT P<br>1C P 1S P 2C P<br>1C P 1S P 2D P<br>1C P 1S P 2H P<br>1C P 1S P 2NT P<br>1C P 1S P 2S P<br>1D P 1H P 1NT P<br>1D P 1H P 1S P<br>1D P 1H P 2C P<br>1D P 1H P 2D P<br>1D P 1H P 2H P<br>1D P 1H P 2NT P<br>1D P 1S P 1NT P<br>1D P 1S P 2C P<br>1D P 1S P 2D P<br>1D P 1S P 2H P<br>1D P 1S P 2NT P<br>1D P 1S P 2S P<br>1H P 1S P 1NT P<br>1H P 1S P 2D P<br>1H P 1S P 2H P<br>1H P 1S P 2NT P<br>1NT P 2D P 2H P<br>1NT P 2H P 2S P<br>2NT P 3D P 3H P<br>2NT P 3H P 3S P | S | 1194 | ABSTAIN | sayc.responder.1nt.jacoby.hearts.continuation, sayc.responder.1nt.jacoby.spades.continuation | YES | NO | ../knowledge/bidding/natural-bids/rebids/responder-rebids.md | SOURCE_PARTIAL |
| response.one-level-existing-rule | 1C P<br>1D P<br>1H P<br>1S P | S | 693 | ABSTAIN | sayc.response.1c, sayc.response.1d, sayc.response.1h, sayc.response.1s | YES | NO | ../knowledge/bidding/natural-bids/responses/responding-to-opening-bids.md | SOURCE_PARTIAL |
| response.one-notrump | 1NT P | S | 271 | ABSTAIN | sayc.response.1nt.jacoby | YES | NO | ../knowledge/bidding/natural-bids/responses/response-to-1nt.md | SOURCE_PARTIAL |
| response.three-level-preempt | 3C P<br>3D P<br>3H P<br>3S P | S | 166 | ABSTAIN | NONE | NO | YES | ../knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md | SOURCE_PARTIAL |
| response.two-notrump | 2NT P | S | 33 | ABSTAIN | sayc.response.2nt.jacoby | YES | NO | ../knowledge/bidding/natural-bids/responses/response-to-2nt.md | SOURCE_PARTIAL |
| response.weak-two | 2D P<br>2H P<br>2S P | S | 540 | ABSTAIN | NONE | NO | YES | ../knowledge/bidding/natural-bids/responses/response-to-weak-two.md | PARTNERSHIP_DEPENDENT |

## Top-five ranking

| Rank | Family | Count | Classification | Source-safe subset | Primary blocker | Action |
|---:|---|---:|---|---|---|---|
| 1 | opener.strong-two-club-after-waiting | 47 | SOURCE_PARTIAL | 24 balanced 22–24 HCP positions -> 2NT | The 2NT subset is exact; suit rebids use qualitative strength and suit language. | Phase 12N narrow subset |
| 2 | response.one-notrump | 271 | SOURCE_PARTIAL | NO | Natural calls are explicit, but convention precedence prevents a complete family contract. | defer |
| 3 | responder.rebid-after-opener-rebid | 1194 | SOURCE_PARTIAL | NO | Broad family has strength ranges but incomplete mutually exclusive call precedence. | defer |
| 4 | response.three-level-preempt | 166 | SOURCE_PARTIAL | NO | Pass/game/sacrifice choices depend on fit, shape, vulnerability, and judgment. | defer |
| 5 | response.weak-two | 540 | PARTNERSHIP_DEPENDENT | NO | Actions use usually/constructive language, suit quality, vulnerability, and agreements. | defer |

The ranking prioritizes source certainty over volume. Exact blockers for every non-selected top candidate are shown above.

## Deep frozen-source audit

### 1. opener.strong-two-club-after-waiting

1_auction_prefix. **2C P 2D P**
2_required_conditions. **balanced and 22–24 HCP**
3_runtime_state_available. **True**
4_source_calls. **('2NT',)**
5_mutually_exclusive. **True**
6_precedence_present. **True**
7_numeric_boundaries. **True**
8_boundaries_frozen. **True**
9_distribution_explicit. **True**
10_exceptions_explicit. **False**
11_partnership_agreement_required. **False**
12_entire_family_safe. **False**
13_smaller_executable_subset. **balanced 22–24 HCP -> 2NT**
14_policy_boundary_solves. **False**
15_architecture_alone_solves. **False**

Router: {"new_route_required": true, "route_exists": false, "route_reaches_rule": false, "routes": [], "rule_abstains": false}

### 2. response.one-notrump

1_auction_prefix. **1NT P**
2_required_conditions. **Family-specific strength, shape, fit, and prior-call state.**
3_runtime_state_available. **False**
4_source_calls. **()**
5_mutually_exclusive. **False**
6_precedence_present. **False**
7_numeric_boundaries. **False**
8_boundaries_frozen. **False**
9_distribution_explicit. **False**
10_exceptions_explicit. **False**
11_partnership_agreement_required. **False**
12_entire_family_safe. **False**
13_smaller_executable_subset. **None**
14_policy_boundary_solves. **False**
15_architecture_alone_solves. **False**

Router: {"new_route_required": false, "route_exists": true, "route_reaches_rule": true, "routes": ["sayc.response.1nt.jacoby"], "rule_abstains": true}

### 3. responder.rebid-after-opener-rebid

1_auction_prefix. **1C P 1D P 1H P / 1C P 1D P 1NT P / 1C P 1D P 1S P / 1C P 1D P 2C P / 1C P 1H P 1NT P / 1C P 1H P 1S P / 1C P 1H P 2C P / 1C P 1H P 2H P / 1C P 1S P 1NT P / 1C P 1S P 2C P / 1C P 1S P 2D P / 1C P 1S P 2H P / 1C P 1S P 2NT P / 1C P 1S P 2S P / 1D P 1H P 1NT P / 1D P 1H P 1S P / 1D P 1H P 2C P / 1D P 1H P 2D P / 1D P 1H P 2H P / 1D P 1H P 2NT P / 1D P 1S P 1NT P / 1D P 1S P 2C P / 1D P 1S P 2D P / 1D P 1S P 2H P / 1D P 1S P 2NT P / 1D P 1S P 2S P / 1H P 1S P 1NT P / 1H P 1S P 2D P / 1H P 1S P 2H P / 1H P 1S P 2NT P / 1NT P 2D P 2H P / 1NT P 2H P 2S P / 2NT P 3D P 3H P / 2NT P 3H P 3S P**
2_required_conditions. **Family-specific strength, shape, fit, and prior-call state.**
3_runtime_state_available. **False**
4_source_calls. **()**
5_mutually_exclusive. **False**
6_precedence_present. **False**
7_numeric_boundaries. **False**
8_boundaries_frozen. **False**
9_distribution_explicit. **False**
10_exceptions_explicit. **False**
11_partnership_agreement_required. **False**
12_entire_family_safe. **False**
13_smaller_executable_subset. **None**
14_policy_boundary_solves. **False**
15_architecture_alone_solves. **False**

Router: {"new_route_required": false, "route_exists": true, "route_reaches_rule": true, "routes": ["sayc.responder.1nt.jacoby.hearts.continuation", "sayc.responder.1nt.jacoby.spades.continuation"], "rule_abstains": true}

### 4. response.three-level-preempt

1_auction_prefix. **3C P / 3D P / 3H P / 3S P**
2_required_conditions. **Family-specific strength, shape, fit, and prior-call state.**
3_runtime_state_available. **False**
4_source_calls. **()**
5_mutually_exclusive. **False**
6_precedence_present. **False**
7_numeric_boundaries. **False**
8_boundaries_frozen. **False**
9_distribution_explicit. **False**
10_exceptions_explicit. **False**
11_partnership_agreement_required. **False**
12_entire_family_safe. **False**
13_smaller_executable_subset. **None**
14_policy_boundary_solves. **False**
15_architecture_alone_solves. **False**

Router: {"new_route_required": true, "route_exists": false, "route_reaches_rule": false, "routes": [], "rule_abstains": false}

### 5. response.weak-two

1_auction_prefix. **2D P / 2H P / 2S P**
2_required_conditions. **Family-specific strength, shape, fit, and prior-call state.**
3_runtime_state_available. **False**
4_source_calls. **()**
5_mutually_exclusive. **False**
6_precedence_present. **False**
7_numeric_boundaries. **False**
8_boundaries_frozen. **False**
9_distribution_explicit. **False**
10_exceptions_explicit. **False**
11_partnership_agreement_required. **True**
12_entire_family_safe. **False**
13_smaller_executable_subset. **None**
14_policy_boundary_solves. **True**
15_architecture_alone_solves. **False**

Router: {"new_route_required": true, "route_exists": false, "route_reaches_rule": false, "routes": [], "rule_abstains": false}

## Selection

**D. ONLY A NARROW SUBSET IS IMPLEMENTABLE.** The best source-safe candidate is the 24-position balanced 22–24 HCP subset within the 47-position strong-2C opener-rebid family. A smaller subset is required because the source describes suit rebids qualitatively and does not give their complete precedence.

## Recommended Phase 12N specification

- Target family: Strong 2C opener rebid after 2D waiting — balanced subset
- Exact auction prefix: `2C P 2D P`
- Decision seat: N
- Observed deterministic population: family 47; executable subset 24
- Exact source-backed condition: Opener is balanced with 22–24 HCP.
- Expected call: `2NT`
- Policy architecture needed: NO
- Route change needed: YES, one exact-prefix route
- Production implementation appropriate: YES, in Phase 12N only
- Guards: exact uncontested prefix only; balanced only; 22–24 HCP inclusive; all other hands abstain; no default or policy changes

Production guards: routes=44; defaults NONE/NONE/NONE; Phase 12G=17/21; Phase 12H=197; Phase 12L=5/7; Jacoby no-policy=62+61=123; production rules added=0; policies added=0; production defaults changed=NO; knowledge Markdown changed=0.

Current cumulative Full Kit: Phase 12M
