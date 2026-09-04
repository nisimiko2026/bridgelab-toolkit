# Phase 12G — Policy-Gated Stayman Major-Fit Game Continuations

## Production rule

- `GAME_GOING + 2H + 4+ hearts -> 4H`
- `GAME_GOING + 2S + 4+ spades -> 4S`

Routes added: 2

Route count: 42 before, 44 after.

## Benchmark fixture

- 2D = 104 -> 0 calls / 104 abstain
- 2H = 70 -> 17 4H / 53 abstain
- 2S = 61 -> 21 4S / 40 abstain

Continuation calls: 4H=17, 4S=21, total=38.

Abstentions: 197

Fixture coverage: 38/235 = 16.17%

No-fit branches remain deferred. The 2D branch remains deferred. The
36 dual-major opener cases are unchanged.

Default Stayman continuation policy: **NONE**

Knowledge Markdown changes: 0

Recommended next phase: **Phase 12H — Stayman Continuation Residual Coverage Audit**

Current cumulative Full Kit: Phase 12G
