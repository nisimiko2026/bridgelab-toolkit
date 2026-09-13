# BridgeLab Phase 26B — System Profile Contract Design
## Status
DESIGN ONLY — NO PRODUCTION CHANGE
Phase 26A evidence review is complete.
This document defines the minimum system-profile contract required to support
Two-over-One Game Force as a first-class BridgeLab bidding system without
changing established SAYC behavior or inventing unsupported bridge semantics.
---
## 1. Objective
BridgeLab shall support more than one bidding-system profile while preserving
the existing theory-neutral infrastructure.
The immediate target is:
- existing SAYC profile;
- generic Two-over-One Game Force profile;
- later, a Nily–Nisim partnership profile layered on top of the generic
  Two-over-One profile.
The objective is functional system separation, not duplication of files,
rules, or engines.
---
## 2. Established Baseline
The current production baseline contains:
- 45 explicit SAYC bidding routes;
- one registered probability engine;
- one registered declarer-play technique.
The existing SAYC router is:
`create_standard_sayc_router()`
The 45-route SAYC baseline is frozen for this phase.
Phase 26 MUST NOT change:
- the number of SAYC routes;
- existing SAYC route IDs;
- existing SAYC rule IDs;
- existing SAYC recommendations;
- existing SAYC abstention semantics;
- existing SAYC policy metadata.
---
## 3. Existing Shared Infrastructure
The following infrastructure is already system-neutral and SHALL remain
system-neutral:
- `SystemContext`;
- `BiddingContext`;
- partnership option parsing;
- `BiddingEngine`;
- `BiddingEngineRouter`;
- `EngineRoute`;
- JSON bidding-context parsing;
- full-deal application validation;
- full-deal analysis orchestration.
No redesign of these components is justified by Phase 26 evidence.
---
## 4. System Identity
BridgeLab shall distinguish system identity from partnership treatment options.
Conceptually:
- `SAYC` identifies the SAYC system profile.
- `TWO_OVER_ONE_GF` identifies the generic Two-over-One Game Force profile.
Partnership options remain separate from system identity.
Examples of existing options include:
- `two_over_one`;
- `forcing_one_notrump`;
- `major_raise_style`.
A system profile MUST NOT silently infer unsupported partnership agreements.
---
## 5. SAYC Contract
SAYC remains an independent production profile.
Existing SAYC-specific rules SHALL NOT automatically become Two-over-One
rules merely because the two systems share some natural bidding principles.
In particular, Phase 26 MUST NOT globally replace checks such as:
`system == SAYC`
with:
`system == SAYC or TWO_OVER_ONE_GF`
Such a change would incorrectly transfer SAYC-specific semantics into the
Two-over-One profile.
---
## 6. Two-over-One Core Contract
The repository already contains source-grounded Two-over-One logic.
Established executable Two-over-One material includes controlled portions of:
- automatic game-force recognition;
- responder two-level new-suit actions;
- opener second-suit rebids;
- opener support rebids;
- opener own-suit rebids.
The canonical automatic game-force response pairs currently established are:
- 1H — 2C;
- 1H — 2D;
- 1S — 2C;
- 1S — 2D.
Phase 26 MUST NOT expand this set without additional deterministic evidence.
Existing Two-over-One rules that are semantically based on Two-over-One
sources but are currently gated by SAYC identity are classified as a
localized architectural gap.
They MAY become reusable by the Two-over-One profile only after focused tests
prove that the change does not alter SAYC behavior.
---
## 7. Shared Rules
A rule may be shared between SAYC and Two-over-One only when evidence
establishes that its semantics are valid for both profiles.
Shared implementation is preferred over duplicated implementation.
However:
shared implementation != assumed shared semantics.
Each candidate shared capability must be classified before reuse.
Allowed classifications are:
- SHARED;
- SAYC_SPECIFIC;
- TWO_OVER_ONE_SPECIFIC;
- PARTNERSHIP_DEPENDENT;
- NOT_ESTABLISHED.
`NOT_ESTABLISHED` means abstain or omit the capability; it does not authorize
a guessed rule.
---
## 8. Opening-Bid Separation
The existing `sayc.py` opening package remains SAYC-specific.
It SHALL NOT be reused wholesale by the Two-over-One profile.
This is required because partnership/system opening structures may differ,
especially at the two level.
The generic Two-over-One profile therefore requires explicit evidence before
reusing each opening family.
No SAYC Weak-Two, strong-opening, notrump-range, minor-opening, or preempt
rule becomes part of Two-over-One merely through profile creation.
---
## 9. Forcing 1NT
Forcing 1NT is a distinct semantic coverage issue.
The existing controlled SAYC 1NT response rule implements a narrow natural
slice and permits an explicit forcing/nonforcing treatment.
That rule is NOT a complete implementation of the Two-over-One Forcing 1NT
structure.
Therefore Phase 26 SHALL NOT obtain apparent Two-over-One coverage simply by
opening the existing SAYC 1NT rule to the new profile.
Full Two-over-One Forcing 1NT remains a semantic capability gap until
deterministic source and policy contracts support its complete executable
branches.
---
## 10. Partnership Profiles
A partnership profile is more specific than a generic bidding-system profile.
The Nily–Nisim partnership is currently documented as playing Two-over-One
Game Force with explicit partnership agreements.
The partnership profile SHALL conceptually layer on top of the generic
Two-over-One profile.
It MUST NOT redefine the meaning of generic Two-over-One for all users.
Partnership-specific conventions must be activated only when their individual
production contracts are established.
The current partnership document is Draft and contains material that may be
ambiguous or incomplete. It therefore cannot by itself authorize unsupported
production semantics.
---
## 11. Router Contract
`BiddingEngineRouter` remains unchanged.
A Two-over-One router/configuration, if implemented, SHALL be a composition
layer using the existing router infrastructure.
The new profile MUST NOT mutate the existing SAYC router.
Conceptually:
`create_standard_sayc_router()`
continues to create the frozen SAYC production composition.
A separate Two-over-One composition MAY be introduced after its route set is
explicitly audited and tested.
No requirement exists for the Two-over-One router to contain exactly 45
routes.
Route-count parity is not system-coverage parity.
---
## 12. Route and Capability Identity
Existing `sayc.*` route and rule identities remain unchanged.
New Two-over-One-specific production routes MUST NOT falsely use `sayc.*`
identity.
Stable Two-over-One identities shall use a distinct namespace selected during
implementation.
Identity changes MUST NOT be used to disguise duplicated or unsupported
semantics.
Public capability identity and provenance observability established in prior
phases must remain intact.
---
## 13. Public Application Selection
The JSON application boundary already preserves:
`bidding.system.id`
and:
`bidding.system.options`
inside `SystemContext`.
The full-deal application and analysis layers already accept an explicitly
supplied bidding router.
The current CLI nevertheless always supplies:
`create_standard_sayc_router()`
This is a real integration gap.
The eventual production path SHALL select a router/profile from the canonical
system identity already present in the bidding request.
The CLI SHOULD NOT require a duplicate `--system` argument when the canonical
JSON bidding context already contains system identity.
Unsupported system identities must fail or abstain explicitly; they must not
silently fall back to SAYC.
---
## 14. Source and Authority Boundary
Phase 25 remains authoritative for provenance-quality interpretation.
Repository provenance does not establish bridge-theory authority.
The current Two-over-One knowledge article may support controlled internal
implementation and auditing, but its Draft status and lack of claim-level
external authority mapping prohibit unsupported authority upgrades.
Phase 26 MUST NOT:
- invent numeric thresholds;
- convert qualitative descriptions into numeric rules;
- infer missing precedence;
- infer partnership choices;
- claim authoritative source coverage that Phase 25 did not establish.
---
## 15. Deferred Capabilities
The seven previously deferred capability areas remain deferred unless new
evidence independently resolves their gates:
- NATURAL_1NT_RESPONSES;
- RESTRICTED_CHOICE;
- SAFETY_PLAY;
- SECOND_HAND_LOW;
- STANDARD_HONOR_LEAD;
- THIRD_HAND_HIGH;
- VACANT_PLACES.
The Two-over-One requirement does not automatically reopen or resolve them.
The interaction between NATURAL_1NT_RESPONSES and Two-over-One Forcing 1NT
must be documented explicitly rather than treated as an implicit resolution.
---
## 16. Initial Change Budget
The first implementation increment after this design is intentionally small.
Expected permissible changes are limited to:
1. system/profile identity and eligibility support where required;
2. removing inappropriate SAYC-only eligibility from proven Two-over-One
   semantic rules;
3. a separate Two-over-One composition layer;
4. focused tests for profile isolation and route ownership;
5. public router selection only after the profile composition is proven.
Not permitted in the first increment:
- rewriting SAYC;
- changing the 45-route SAYC baseline;
- broad renaming;
- broad refactoring;
- implementing new bridge conventions;
- inventing new thresholds;
- completing Forcing 1NT by assumption;
- implementing Nily–Nisim conventions merely because they appear on the
  partnership card.
---
## 17. Required Safety Tests
Before any new Two-over-One profile is considered production-capable, tests
must establish at minimum:
1. existing SAYC router still has exactly 45 routes;
2. existing SAYC route IDs remain unchanged;
3. existing SAYC focused tests remain green;
4. Two-over-One rules activate only for authorized profiles/treatments;
5. SAYC-only rules do not leak into Two-over-One;
6. Two-over-One-only rules do not leak into plain SAYC without the required
   treatment;
7. unsupported Two-over-One positions abstain rather than guess;
8. unsupported system identity never silently falls back to SAYC;
9. capability identity remains deterministic;
10. provenance and policy observability remain structurally valid.
---
## 18. Implementation Principle
Phase 26 follows:
PROVE -> CLASSIFY -> DESIGN -> IMPLEMENT -> FOCUSED TEST -> DIFF REVIEW ->
REGRESSION -> AUDIT -> CLOSE
No production change may be justified solely by a desire for apparent system
coverage.
The target is a trustworthy Two-over-One production profile, not a larger
route count.
---
## 19. Phase 26B Decision
The evidence supports creation of a first-class Two-over-One system profile
without redesigning BridgeLab's core routing, application, or analysis
architecture.
The primary gaps are localized to:
- system/profile eligibility;
- Two-over-One route composition;
- public router selection;
- incomplete semantic capabilities such as full Forcing 1NT.
Implementation may proceed incrementally while preserving the existing SAYC
baseline.
Marker:
PHASE_26B_SYSTEM_PROFILE_CONTRACT_DESIGN_COMPLETE_PENDING_FOCUSED_IMPLEMENTATION
