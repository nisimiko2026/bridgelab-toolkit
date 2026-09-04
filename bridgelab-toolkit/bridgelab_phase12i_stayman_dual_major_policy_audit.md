# Phase 12I — Stayman Opener Dual-Major Policy Boundary Audit

## Deterministic sample

- seeds 1–10,000
- dual-major opener positions: 36

## Exact mutually-exclusive shape partition

| Dual-major shape | Exact count |
|---|---:|
| 4H_4S | 36 |
| 4H_5plusS | 0 |
| 5plusH_4S | 0 |
| 5plusH_5plusS | 0 |

The exact full shapes are 2-3-4-4 (19) and
3-2-4-4 (17), in C-D-H-S order.

## Canonical source findings

The frozen Stayman `Opener's Responses` source says that 2H shows four hearts
and may also contain four spades depending on partnership agreement. It says
that 2S shows four spades and normally denies four hearts. The source therefore
acknowledges more than one partnership treatment without defining a universal
precedence, strength, suit-quality, vulnerability, or style rule.

## Source-certainty matrix

| Shape | Count | Source-permitted responses | Source statement | Classification | Policy boundary? | Blocker | Action |
|---|---:|---|---|---|---|---|---|
| 4H_4S | 36 | 2H, 2S | 2H may also contain four spades depending on partnership agreement; 2S normally denies four hearts. | POLICY_REQUIRED | YES | No partnership choice is configured by default. | add non-default policy architecture in Phase 12J |
| 4H_5plusS | 0 | 2H, 2S | 2H may also contain four spades depending on partnership agreement; 2S normally denies four hearts. | POLICY_REQUIRED | YES | No partnership choice is configured by default. | add non-default policy architecture in Phase 12J |
| 5plusH_4S | 0 | 2H, 2S | 2H may also contain four spades depending on partnership agreement; 2S normally denies four hearts. | POLICY_REQUIRED | YES | No partnership choice is configured by default. | add non-default policy architecture in Phase 12J |
| 5plusH_5plusS | 0 | 2H, 2S | 2H may also contain four spades depending on partnership agreement; 2S normally denies four hearts. | POLICY_REQUIRED | YES | No partnership choice is configured by default. | add non-default policy architecture in Phase 12J |

## Current production behavior and existing routes

- production action: ABSTAIN for all 36
- existing route attempts: 36 through `sayc.opener.1nt.stayman`
- production route count: 44
- no default dual-major policy exists

## Policy-boundary finding

A clean boundary is source-safe. Its only responsibility is choosing the
partnership-agreed 2H or 2S branch after the hand is already known to contain
both qualifying majors. The proposed output domain is HEARTS, SPADES, UNKNOWN.
No policy and UNKNOWN must abstain. Known choices require an explanation and
frozen-source attribution.

## Decision and Phase 12J recommendation

**B. ADD NON-DEFAULT DUAL-MAJOR POLICY ARCHITECTURE.**

Add a non-default Stayman dual-major response policy abstraction with HEARTS, SPADES, and UNKNOWN outputs; require explanation and frozen-source attribution for known choices; preserve no-policy and UNKNOWN abstention; do not add responder continuations.

Phase 12G calls unchanged: 4H=17, 4S=21

Phase 12H residuals unchanged: 197

Production defaults changed: NO

Knowledge Markdown changed: 0

Current cumulative Full Kit: Phase 12I
