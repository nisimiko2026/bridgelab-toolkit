# Phase 12D — Post-Jacoby Continuation Endpoint Audit

## Deterministic sample

- seeds 1–10,000
- Phase 12C successful continuations: 75

## WEAK

- total: 25
- heart Pass: 17
- spade Pass: 8
- terminal count: 25
- endpoint classification: TERMINAL

## INVITATIONAL

- total: 25
- heart 2NT: 11
- spade 2NT: 14
- endpoint classification: SOURCE_INSUFFICIENT

## GAME_GOING

- total: 25
- 4H: 12
- 4S: 13
- terminal count: 25
- endpoint classification: TERMINAL

## Source-certainty matrix

| Endpoint | Count | Next actor | Source status | Executable? | Blocker |
|---|---:|---|---|---|---|
| WEAK heart Pass | 17 | none | TERMINAL | True | none |
| WEAK spade Pass | 8 | none | TERMINAL | True | none |
| INVITATIONAL heart 2NT | 11 | opener | SOURCE_INSUFFICIENT | False | No exact opener call, trigger conditions, or precedence in the frozen corpus. |
| INVITATIONAL spade 2NT | 14 | opener | SOURCE_INSUFFICIENT | False | No exact opener call, trigger conditions, or precedence in the frozen corpus. |
| GAME_GOING 4H | 12 | none | TERMINAL | True | none |
| GAME_GOING 4S | 13 | none | TERMINAL | True | none |

## Invitational-2NT source findings

The frozen `jacoby-transfers.md` source explicitly presents both transfer-then-2NT
auctions and says responder invites game. It does not state opener's next call,
define minimum/maximum for this decision, map two- versus three-card support,
or provide deterministic precedence among Pass, 3H/3S, 3NT, and 4H/4S.
`response-to-1nt.md` says the goal of an invitational hand is to determine whether
opener has a maximum, but likewise supplies no post-transfer call mapping.
`sayc.md` lists Jacoby Transfers as part of SAYC but adds no such continuation.

- **Pass**: not explicitly stated; no trigger or complete precedence is supplied.
- **3H / 3S**: not explicitly stated; no trigger or complete precedence is supplied.
- **3NT**: not explicitly stated; no trigger or complete precedence is supplied.
- **4H / 4S**: not explicitly stated; no trigger or complete precedence is supplied.

## Recommendation

**C. DEFER THIS FAMILY.** The source is incomplete, not merely separated by a
well-defined policy classification, so Phase 12D must not implement this family.

Recommended next implementation-family audit: Audit game-going responder continuations after deterministic 1NT Stayman responses; the frozen Stayman source explicitly names 4H/4S when a major fit is found and 3NT in its no-major-fit game example, subject to an explicit responder-strength policy boundary.

Ordinary no-policy benchmark unchanged: **YES**
(62 + 61 = 123).

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12D
