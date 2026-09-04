# Phase 12L — Dual-Major Policy Downstream Coverage Audit

## Deterministic sample

- seeds 1–10,000
- target: 36
- opener shapes: 2-3-4-4=19, 3-2-4-4=17

## Policy paths

- HEARTS: opener 2H=36, 4H=5, residual=31, coverage=13.89%
- SPADES: opener 2S=36, 4S=7, residual=29, coverage=19.44%

Benchmark coverage is descriptive, not a source-backed bidding preference.

## Cross-policy outcome matrix

| Outcome | Count |
|---|---:|
| BOTH_TERMINAL | 0 |
| HEARTS_ONLY_TERMINAL | 5 |
| SPADES_ONLY_TERMINAL | 7 |
| NEITHER_TERMINAL | 24 |

## Exact responder primary shape partition

| Primary bucket | Count |
|---|---:|
| both_majors_four_plus | 0 |
| hearts_only_four_plus | 5 |
| spades_only_four_plus | 7 |
| neither_major_long_minor | 8 |
| neither_major_balanced_looking | 12 |
| neither_major_other_shape | 4 |

Exact C-D-H-S responder shapes and overlapping secondary flags are preserved in the JSON artifact.

## HEARTS residual shape matrix

| Primary bucket | Count |
|---|---:|
| other_major_exactly_four | 7 |
| other_major_five_plus | 0 |
| no_four_card_major_long_minor | 8 |
| no_four_card_major_balanced_looking | 12 |
| no_four_card_major_other_shape | 4 |

## SPADES residual shape matrix

| Primary bucket | Count |
|---|---:|
| other_major_exactly_four | 5 |
| other_major_five_plus | 0 |
| no_four_card_major_long_minor | 8 |
| no_four_card_major_balanced_looking | 12 |
| no_four_card_major_other_shape | 4 |

## Source-certainty matrix

| Path | Residual shape | Count | Candidate calls | Classification | Executable? | Blocker | Action |
|---|---|---:|---|---|---|---|---|
| HEARTS | other_major_exactly_four | 7 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| HEARTS | other_major_five_plus | 0 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| HEARTS | no_four_card_major_long_minor | 8 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| HEARTS | no_four_card_major_balanced_looking | 12 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| HEARTS | no_four_card_major_other_shape | 4 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| SPADES | other_major_exactly_four | 5 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| SPADES | other_major_five_plus | 0 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| SPADES | no_four_card_major_long_minor | 8 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| SPADES | no_four_card_major_balanced_looking | 12 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |
| SPADES | no_four_card_major_other_shape | 4 | 3NT, other major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, strength boundaries, exceptions, and precedence are unresolved. | defer |

No source-safe downstream residual subset exists.

## Router and per-position cross-policy audit

Both branches use `sayc.opener.1nt.stayman`, followed respectively by the existing
`sayc.responder.1nt.stayman.after.2h` or `.after.2s` route.

| Seed | Opener shape | Responder shape | HEARTS outcome | SPADES outcome | Cross-policy class |
|---:|---|---|---|---|---|
| 865 | 3-2-4-4 | 4-3-3-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 1023 | 3-2-4-4 | 3-4-4-2 | 4H | ABSTAIN | HEARTS_ONLY_TERMINAL |
| 1972 | 2-3-4-4 | 6-1-2-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 2261 | 3-2-4-4 | 2-5-4-2 | 4H | ABSTAIN | HEARTS_ONLY_TERMINAL |
| 2267 | 2-3-4-4 | 2-7-2-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 2596 | 3-2-4-4 | 3-5-4-1 | 4H | ABSTAIN | HEARTS_ONLY_TERMINAL |
| 2620 | 2-3-4-4 | 4-5-2-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 2977 | 2-3-4-4 | 4-6-1-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 3007 | 3-2-4-4 | 5-2-2-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 3395 | 2-3-4-4 | 5-3-2-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 3818 | 2-3-4-4 | 5-3-3-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 3862 | 2-3-4-4 | 3-3-3-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 3914 | 2-3-4-4 | 3-6-1-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 4021 | 2-3-4-4 | 4-4-2-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 4093 | 2-3-4-4 | 4-4-3-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 4257 | 2-3-4-4 | 5-3-1-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 4854 | 3-2-4-4 | 5-2-4-2 | 4H | ABSTAIN | HEARTS_ONLY_TERMINAL |
| 4995 | 3-2-4-4 | 5-3-3-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 5071 | 3-2-4-4 | 6-5-1-1 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 5435 | 3-2-4-4 | 5-5-2-1 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 5754 | 3-2-4-4 | 3-5-3-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 5772 | 2-3-4-4 | 4-5-3-1 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 5879 | 3-2-4-4 | 2-6-3-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 6017 | 3-2-4-4 | 5-1-3-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 7303 | 3-2-4-4 | 2-4-3-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 7356 | 2-3-4-4 | 3-4-3-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 7469 | 3-2-4-4 | 2-6-2-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 7610 | 2-3-4-4 | 5-2-3-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 7686 | 2-3-4-4 | 6-1-3-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 8030 | 3-2-4-4 | 4-2-4-3 | 4H | ABSTAIN | HEARTS_ONLY_TERMINAL |
| 8085 | 2-3-4-4 | 5-5-2-1 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 8740 | 3-2-4-4 | 2-5-3-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 8947 | 3-2-4-4 | 5-3-3-2 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 9171 | 2-3-4-4 | 1-7-2-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |
| 9915 | 2-3-4-4 | 3-4-2-4 | ABSTAIN | 4S | SPADES_ONLY_TERMINAL |
| 9984 | 2-3-4-4 | 3-5-2-3 | ABSTAIN | ABSTAIN | NEITHER_TERMINAL |

## Source interpretation and decision

**NO SOURCE-BACKED POLICY PREFERENCE. The 5-versus-7 difference is a sample-specific consequence of responder distribution; the frozen source defines no strategic preference from benchmark coverage.**

**D. DEFER DUAL-MAJOR DOWNSTREAM RESIDUALS.**

Recommended Phase 12M direction: Phase 12M — Next Deterministic Family Source-Readiness Audit: audit unimplemented non-Stayman benchmark families and select a target only where the frozen source supplies a complete call contract.

Routes: 44

Default policies: NONE / NONE

Phase 12G baseline: 4H=17, 4S=21

Phase 12H residual baseline: 197

Jacoby no-policy: 62 + 61 = 123

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12L
