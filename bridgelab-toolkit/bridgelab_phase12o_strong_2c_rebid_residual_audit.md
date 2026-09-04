# Phase 12O — Strong 2C Rebid Residual Source Audit

## Deterministic sample

- Seeds: 1–10,000
- Exact decision: `2C-P-2D-P`, opener to act
- Original family: 47
- Phase 12N handled: 24
- Residual: 23
- Current action for every residual: `ABSTAIN`

## Source-certainty matrix and exact primary partition

| Primary bucket | Count | HCP range | Candidate calls | Classification | Executable subset? | Blocker | Action |
|---|---:|---|---|---|---|---|---|
| balanced_below_22 | 0 | none | none | SOURCE_INSUFFICIENT | NO | Zero observations and no complete frozen-source mapping. | defer |
| balanced_above_24 | 2 | 25-26 | 2NT, 3NT | SOURCE_INSUFFICIENT | NO | No call or level is defined for balanced 25+ HCP. | defer |
| unbalanced_below_22 | 0 | none | none | SOURCE_INSUFFICIENT | NO | Zero observations and no complete frozen-source mapping. | defer |
| unbalanced_22_24_single_longest_major | 11 | 22-24 | 2H, 2S | SOURCE_PARTIAL | NO | No exact length/strength threshold, spade mapping, level precedence, or exceptions. | defer |
| unbalanced_22_24_single_longest_minor | 9 | 22-23 | 3C, 3D | SOURCE_PARTIAL | NO | No exact length/strength threshold, diamond mapping, level precedence, or exceptions. | defer |
| unbalanced_22_24_tied_longest | 1 | 23-23 | 2H, 2S, 3C, 3D | SOURCE_INSUFFICIENT | NO | Tie treatment and competing-suit precedence are absent. | defer |
| unbalanced_above_24 | 0 | none | none | SOURCE_INSUFFICIENT | NO | Zero observations and no complete frozen-source mapping. | defer |

HCP distribution: {'22': 13, '23': 5, '24': 3, '25': 1, '26': 1}

Exact C-D-H-S shape distribution: {'1-2-7-3': 1, '1-5-3-4': 1, '2-2-4-5': 1, '2-4-5-2': 1, '2-6-1-4': 1, '3-1-7-2': 1, '3-2-4-4': 1, '3-2-6-2': 1, '3-3-1-6': 1, '3-4-4-2': 1, '3-6-3-1': 1, '3-8-1-1': 1, '4-0-6-3': 1, '4-1-4-4': 1, '4-2-5-2': 1, '4-3-1-5': 1, '4-7-1-1': 1, '5-1-4-3': 1, '5-3-4-1': 2, '5-4-3-1': 1, '6-3-1-3': 1, '6-3-2-2': 1}

Overlapping secondary flags: {'5+ card major': 11, '5+ card minor': 9, '6+ card suit': 11, '7+ card suit': 4, 'two-suited shape': 15}

## Position and router audit

| Seed | HCP | C-D-H-S shape | Balanced | Primary bucket | Secondary flags | Action | Route | Rule abstains | Other route |
|---:|---:|---|---|---|---|---|---|---|---|
| 5 | 24 | 6-3-2-2 | False | unbalanced_22_24_single_longest_major | 5+ card major, 6+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 32 | 23 | 5-1-4-3 | False | unbalanced_22_24_single_longest_major | 5+ card major, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 665 | 26 | 3-2-4-4 | True | balanced_above_24 | two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 754 | 22 | 1-2-7-3 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, 6+ card suit, 7+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 1489 | 22 | 5-4-3-1 | False | unbalanced_22_24_single_longest_major | 5+ card major, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 1925 | 22 | 4-0-6-3 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, 6+ card suit, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 2053 | 22 | 3-2-6-2 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, 6+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 2083 | 24 | 4-7-1-1 | False | unbalanced_22_24_single_longest_major | 5+ card major, 6+ card suit, 7+ card suit, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 2413 | 22 | 4-2-5-2 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 2868 | 22 | 3-1-7-2 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, 6+ card suit, 7+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 4981 | 24 | 2-6-1-4 | False | unbalanced_22_24_single_longest_major | 5+ card major, 6+ card suit, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 5531 | 23 | 4-1-4-4 | False | unbalanced_22_24_tied_longest | two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 5710 | 23 | 1-5-3-4 | False | unbalanced_22_24_single_longest_major | 5+ card major, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 5916 | 25 | 3-4-4-2 | True | balanced_above_24 | two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 6075 | 23 | 4-3-1-5 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 6538 | 22 | 3-3-1-6 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, 6+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 6863 | 22 | 5-3-4-1 | False | unbalanced_22_24_single_longest_major | 5+ card major, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 7248 | 22 | 6-3-1-3 | False | unbalanced_22_24_single_longest_major | 5+ card major, 6+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 7786 | 22 | 3-6-3-1 | False | unbalanced_22_24_single_longest_major | 5+ card major, 6+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 8379 | 22 | 5-3-4-1 | False | unbalanced_22_24_single_longest_major | 5+ card major, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 9817 | 22 | 3-8-1-1 | False | unbalanced_22_24_single_longest_major | 5+ card major, 6+ card suit, 7+ card suit | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 9902 | 23 | 2-2-4-5 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |
| 10000 | 22 | 2-4-5-2 | False | unbalanced_22_24_single_longest_minor | 5+ card minor, two-suited shape | ABSTAIN | sayc.opener.2c.2d.balanced | YES | NONE |

All 23 reach `sayc.opener.2c.2d.balanced`; its Phase 12N rule checks and abstains. No other route or rule attempts the position. Production routes remain 45.

## Frozen-source finding

The frozen `response-to-2-clubs` source completely defines only the already
implemented balanced 22–24 HCP `2NT` contract. Its suit-rebid examples use
qualitative terms (“strong heart suit” and “powerful club suit”) without exact
length, strength, complete suit mapping, level precedence, tied-suit treatment,
or long-suit/two-suited exceptions. Balanced hands above 24 also have no exact
next-call contract. Therefore there is no source-safe residual subset.

## Decision and Phase 12P

**D. DEFER REMAINING STRONG-2C REBIDS.**

Phase 12P — Natural 1NT Response Source-Readiness Audit: return to the Phase 12M inventory and audit the next-ranked response.one-notrump family, excluding already implemented/deferred Stayman and Jacoby branches.

Guards: Phase 12N 2NT=24; Phase 12G={'4H': 17, '4S': 21}; Phase 12H=197; Phase 12K abstain=36; Phase 12L={'HEARTS': 5, 'SPADES': 7}; Jacoby={'heart_transfer': 62, 'spade_transfer': 61, 'total': 123}; defaults unchanged; knowledge Markdown changes=0.

Current cumulative Full Kit: Phase 12O
