# Phase 12T — Two-Notrump Response Source-Readiness Audit

Seeds 1–10,000. Expected population 33; measured **33**, confirmed. All are exact `2NT P` responder abstentions routed to `sayc.response.2nt.jacoby`; downstream `2NT-3D-3H` and `2NT-3H-3S` are excluded. Routes remain 45.

Opener semantics: natural, balanced, 20–21 HCP. Primary partition: `{"balanced-no-four-major": 8, "both-majors-four-plus": 4, "exactly-one-four-card-major": 15, "five-plus-hearts": 1, "game-looking": 1, "long-minor": 3, "slam-interest-looking": 1}`. Complete HCP/shape/suit distributions and positions are in JSON.

Stayman `3C` and transfers `3D→hearts`, `3H→spades` are source-defined. Transfers require 5+ cards and any strength and acceptance is defined, but these residuals fall outside existing executable transfer coverage. Stayman responder strength, dual-major treatment, natural Pass/3NT/direct games, continuations, precedence, and exceptions remain incomplete or partnership-dependent.

| Family | Count | HCP | Candidate | Classification | Executable | Blocker |
|---|---:|---|---|---|---|---|
| five-plus-hearts | 1 | 8-8 | 3D | LOW_SAMPLE | NO | Incomplete exact strength/shape precedence and exceptions. |
| both-majors-four-plus | 4 | 1-12 | 3C | SOURCE_PARTIAL | NO | Incomplete exact strength/shape precedence and exceptions. |
| exactly-one-four-card-major | 15 | 3-10 | 3C | SOURCE_PARTIAL | NO | Incomplete exact strength/shape precedence and exceptions. |
| balanced-no-four-major | 8 | 0-10 | Pass, 3NT | SOURCE_PARTIAL | NO | Incomplete exact strength/shape precedence and exceptions. |
| long-minor | 3 | 4-8 | minor methods, 3NT | SOURCE_PARTIAL | NO | Incomplete exact strength/shape precedence and exceptions. |
| slam-interest-looking | 1 | 11-11 | slam actions | LOW_SAMPLE | NO | Incomplete exact strength/shape precedence and exceptions. |
| game-looking | 1 | 9-9 | 3NT | LOW_SAMPLE | NO | Incomplete exact strength/shape precedence and exceptions. |

Best source-safe subset: none. **E. DEFER 2NT RESPONSES.** Top candidates: exactly-one four-card major, both four-plus majors, five-plus hearts residual, balanced/no-major, long minor.

Recommend **Phase 12U — One-Level Response Residual Source-Readiness Audit**, prefixes `1C P / 1D P / 1H P / 1S P`, Phase 12M population 693, audit-only.

Production rules/routes/policies added: 0/0/0. Defaults and knowledge unchanged.

Current cumulative Full Kit: Phase 12T
