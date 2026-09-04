# Phase 12E — 1NT Stayman GAME_GOING Responder Continuation Audit

## Deterministic sample

- seeds 1–10,000
- ordinary production endpoints: 2D=0, 2H=0, 2S=0
- fixture-supported Stayman endpoints: 2D=104, 2H=70, 2S=61
- opener both-major abstentions: 36
- GAME_GOING audited: 235

## Source-certainty matrix

| Auction endpoint | Count | Responder holding | Candidate | Source status | Executable? | Blocker | Action |
|---|---:|---|---|---|---|---|---|
| 1NT-P-2C-P-2D-P | 104 | any audited holding | 3NT | SOURCE_INSUFFICIENT | False | The source also permits minor game or slam according to distribution and gives no complete precedence. | defer |
| 1NT-P-2C-P-2H-P | 17 | responder has 4+ hearts | 4H | ARCHITECTURE_REQUIRED | False | The call is source-explicit, but BridgeLab has no Stayman continuation strength-policy abstraction. | add architecture only in a later phase |
| 1NT-P-2C-P-2H-P | 53 | responder has fewer than 4 hearts | 3NT / other | SOURCE_INSUFFICIENT | False | No exact no-fit GAME_GOING call or shape precedence is defined. | defer |
| 1NT-P-2C-P-2S-P | 21 | responder has 4+ spades | 4S | ARCHITECTURE_REQUIRED | False | The call is source-explicit, but BridgeLab has no Stayman continuation strength-policy abstraction. | add architecture only in a later phase |
| 1NT-P-2C-P-2S-P | 40 | responder has fewer than 4 spades | 3NT / other | SOURCE_INSUFFICIENT | False | No exact no-fit GAME_GOING call or shape precedence is defined. | defer |

## Findings after 2D

The source gives 3NT as a no-major-fit game example, but its general text also
allows 2NT, minor-suit game, or slam exploration according to strength and
distribution. GAME_GOING removes 2NT, but it does not resolve minor-game, slam,
five-card-major, or unusual-shape precedence. Therefore 3NT is not executable
as a general deterministic continuation.

## Findings after 2H

With 4+ responder hearts, the source-explicit major-fit call is 4H. Without a
heart fit, the frozen source does not select 3NT or another exact call. Holdings
in the other major and unusual shapes remain unresolved.

## Findings after 2S

With 4+ responder spades, the symmetric source-explicit call is 4S. Without a
spade fit, the frozen source does not select 3NT or another exact call.

## Exact source-safe calls

- 3NT after 2D generally: NO
- 4H after an established heart fit: YES, but architecture is required
- 4S after an established spade fit: YES, but architecture is required

## Branch classification totals

- SOURCE_EXECUTABLE: 0
- POLICY_REQUIRED: 0
- SOURCE_INSUFFICIENT: 3
- ARCHITECTURE_REQUIRED: 2
- TERMINAL: 0
- ALREADY_ROUTED: 0

## Recommendation

**D. DEFER THIS FAMILY.** The complete family remains source-incomplete.

Recommended Phase 12F direction: Design and audit a non-default Stayman continuation strength/state policy boundary, scoped first to the source-complete major-fit GAME_GOING branches (4H and 4S); keep all no-fit branches deferred.

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12E
