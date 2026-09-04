# Phase 12H — Stayman Continuation Residual Coverage Audit

## Deterministic sample

- seeds 1–10,000
- implemented Phase 12G: 4H=17, 4S=21, total=38
- residual after 2D: 104
- residual after 2H no-fit: 53
- residual after 2S no-fit: 40
- residual total: 197

## Exact mutually-exclusive shape partitions

### after_2D

- both_majors_four_plus: 9
- exactly_one_four_card_major: 52
- five_four_major_pattern: 2
- no_four_card_major_balanced_looking: 30
- no_four_card_major_long_minor: 9
- no_four_card_major_other_shape: 2

### after_2H_no_fit

- no_four_card_major_balanced_looking: 23
- no_four_card_major_long_minor: 7
- no_four_card_major_other_shape: 8
- other_major_exactly_four: 15

### after_2S_no_fit

- no_four_card_major_balanced_looking: 14
- no_four_card_major_long_minor: 6
- no_four_card_major_other_shape: 1
- other_major_exactly_four: 19

## Source-certainty matrix

| Endpoint | Primary shape bucket | Count | Candidate calls | Classification | Executable? | Blocker | Action |
|---|---|---:|---|---|---|---|---|
| after_2D | both_majors_four_plus | 9 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2D | exactly_one_four_card_major | 52 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2D | five_four_major_pattern | 2 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2D | no_four_card_major_balanced_looking | 30 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2D | no_four_card_major_long_minor | 9 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2D | no_four_card_major_other_shape | 2 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2H_no_fit | no_four_card_major_balanced_looking | 23 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2H_no_fit | no_four_card_major_long_minor | 7 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2H_no_fit | no_four_card_major_other_shape | 8 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2H_no_fit | other_major_exactly_four | 15 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2S_no_fit | no_four_card_major_balanced_looking | 14 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2S_no_fit | no_four_card_major_long_minor | 6 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2S_no_fit | no_four_card_major_other_shape | 1 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |
| after_2S_no_fit | other_major_exactly_four | 19 | 3NT, major, minor game, slam | SOURCE_INSUFFICIENT | NO | Competing calls, shape exceptions, and precedence are unresolved. | defer |

## Existing-route attempts

- after 2D: 0 route matches
- after 2H no-fit: 53 route matches, 0 production actions
- after 2S no-fit: 40 route matches, 0 production actions

## Source-safe subset candidates

None. No residual bucket has a complete frozen-source condition-to-call mapping
and precedence contract. In particular, no blanket 3NT fallback is supported.

## Recommendation

**D. DEFER STAYMAN RESIDUALS.**

Recommended Phase 12I direction: Audit a policy boundary for the 36 Stayman opener hands with both four-card majors; the frozen source explicitly marks whether 2H may also contain four spades as partnership-agreement dependent.

Production route count: 44

Default Stayman continuation policy: NONE

Dual-major opener cases unchanged: 36

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12H
