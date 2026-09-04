# Phase 12J — Stayman Dual-Major Response Policy Architecture

## Policy model

- enum: `StaymanDualMajorResponse`
- values: HEARTS, SPADES, UNKNOWN
- assessment: `StaymanDualMajorResponseAssessment`
- interface: `StaymanDualMajorResponsePolicy`
- assessment contains an abstract response choice and attribution only, never a bid
- known HEARTS/SPADES choices require explanation and `KnowledgeSource`
- UNKNOWN may be unattributed

## Registry and configuration

- option: `stayman_dual_major_response_policy`
- explicit register, resolve, and assess paths
- default dual-major response policy: **NONE**
- missing and unknown policy identifiers resolve to no policy
- no fallback is installed

## Deterministic architecture validation

- seeds 1–10,000
- dual-major positions: 36
- 2-3-4-4: 19
- 3-2-4-4: 17
- HEARTS fixture: 36
- SPADES fixture: 36
- UNKNOWN fixture: 36

Fixtures validate policy assessment only. They do not translate a response
choice to 2H or 2S through production bidding logic.

## Production guards

- production action: ABSTAIN for all 36
- existing route attempts through `sayc.opener.1nt.stayman`: 36
- routes: 44
- production bidding calls added: 0
- Phase 12G calls unchanged: 4H=17, 4S=21
- Phase 12H residuals unchanged: 197
- production defaults changed: NO
- knowledge changes: 0

Recommended next phase: **Phase 12K — Policy-Gated Stayman Dual-Major Opener Responses**

Current cumulative Full Kit: Phase 12J
