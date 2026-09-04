# Phase 12F — Stayman Responder Continuation Policy Architecture

## Policy interface

- protocol: `StaymanContinuationStrengthPolicy`
- result: `StaymanContinuationStrengthAssessment`
- classification enum: `StaymanContinuationStrength`
- values: `GAME_GOING`, `OTHER`, `UNKNOWN`
- the policy returns classifications only and never selects a bidding call
- known classifications require an explanation and `KnowledgeSource`

## Registry and default behavior

- registry option: `stayman_continuation_strength_policy`
- register, resolve, and assess paths are explicit
- default Stayman continuation policy: **NONE**
- unknown or unregistered identifiers resolve to no policy

## Benchmark validation

- opener 2D: 104
- opener 2H: 70
  - heart fit: 17
  - no fit: 53
- opener 2S: 61
  - spade fit: 21
  - no fit: 40
- total audited: 235
- future source-safe fit target: 17 + 21 = 38

The no-fit branches remain deferred. The 36
dual-four-card-major opener positions remain unchanged and partnership-dependent.

Production routes: 42 before, 42 after.

Production bidding calls added: 0

Production defaults changed: NO

Knowledge Markdown changed: 0

Recommended next phase: **Phase 12G — Policy-Gated Stayman Major-Fit Game Continuations**

Current cumulative Full Kit: Phase 12F
