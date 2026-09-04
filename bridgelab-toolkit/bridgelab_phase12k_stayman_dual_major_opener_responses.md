# Phase 12K — Policy-Gated Stayman Dual-Major Opener Responses

## Production mapping

- explicit HEARTS policy -> 2H
- explicit SPADES policy -> 2S
- UNKNOWN, missing, or unresolved policy -> abstain
- scope: exactly four hearts and exactly four spades after 1NT-P-2C-P

## Deterministic target

- seeds 1–10,000
- dual-major positions: 36
- 2-3-4-4: 19
- 3-2-4-4: 17

## Opener-policy coverage

- HEARTS fixture: 2H=36, coverage 36/36
- SPADES fixture: 2S=36, coverage 36/36
- UNKNOWN: abstain=36
- no policy: abstain=36

With only the dual-major policy configured, responder abstains after all 36
HEARTS-policy calls and all 36 SPADES-policy calls because the independent
continuation-strength policy remains unconfigured.

## Combined-policy measured downstream

### HEARTS + GAME_GOING

- opener 2H: 36
- responder heart fits: 5
- responder 4H: 5
- no-fit abstain: 31

### SPADES + GAME_GOING

- opener 2S: 36
- responder spade fits: 7
- responder 4S: 7
- no-fit abstain: 29

Responder continuation coverage is 5/36 for HEARTS and 7/36 for SPADES; it
is distinct from the 36/36 opener-policy coverage.

## Guards

- routes: 44
- default dual-major policy: NONE
- default continuation policy: NONE
- Phase 12G baseline: 4H=17, 4S=21
- Phase 12H residual baseline: 197
- ordinary no-policy behavior unchanged
- production defaults changed: NO
- knowledge changes: 0

Recommended next phase: **Phase 12L — Dual-Major Policy Downstream Coverage Audit**

Current cumulative Full Kit: Phase 12K
