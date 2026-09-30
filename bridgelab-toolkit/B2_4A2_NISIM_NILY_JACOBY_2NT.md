# B2.4A2 Nisim-Nily Jacoby 2NT

## Approved agreement

Authority: the user's B2.4A2 specification in this task. This approval supersedes
B2.4A's absence-of-implementation finding for the new opt-in revision only.
The generic source article remains a reference; its approximate thresholds and
variant structures do not replace this precise partnership approval.

After uncontested 1H or 1S, responder's 2NT is an artificial game-forcing raise
with **13+ HCP and 4+ support for opener's major**, with no balanced/unbalanced
restriction. No alternative playing-strength qualification or shortness bonus
is inferred. Opener's approved descriptions are:

- A new three-level suit: singleton or void in that side suit; both qualify.
- 3M: extras and slam interest.
- 3NT: balanced 14-15 HCP.
- 4M: minimum.

M is the opening major. No later responder slam continuation is implemented.

## Explicit opt-in profile and API

`bridge.nisim_nily_partnership_profile.NISIM_NILY_JACOBY_2NT_PROFILE` is the new
`B2.4A2` revision of the same `nisim-nily` / `TWO_OVER_ONE_GF` partnership. It adds
`response.major.2nt = nisim_nily_jacoby_2nt`, with `min_hcp=13`, `min_support=4`
and approval provenance. The validated `NISIM_NILY_PROFILE` Phase 29Y snapshot
is unchanged. Consumers explicitly select the new revision for this agreement;
no production router, B2.1-B2.3 API, or default option is changed.

New entry points in `bridge.nisim_nily_jacoby_2nt`:

- `assess_jacoby_2nt_response(hand, auction=..., vulnerability=..., profile=...,
  base_agreements=())`
- `assess_jacoby_2nt_opener(hand, auction=..., vulnerability=..., profile=...,
  base_agreements=(), strength=None)`

Both return immutable `JacobyAssessment`: resolved profile, canonical context,
disposition, one selected `RuleDecision` or abstention/conflict, typed selected
`JacobyMeaning`, complete engine trace, reason, blockers and
`production_adopted=False`. `recommended_call` is the authoritative selection.

Gating requires Nisim-Nily identity, TWO_OVER_ONE_GF base, the exact supported
agreement and parameters, and PARTNERSHIP source scope. Merely using 2/1 or SAYC,
copying the agreement into another partnership, or supplying it as a system
default cannot activate the rules. Disabled/replaced agreements and unsupported
parameters abstain. The existing resolver owns override precedence; the shared
profile guards retain all other relevant unsupported-meaning blockers. The
existing Bergen metadata is not interpreted or implemented by this module.

The implementation uses `BiddingContext.create`, `HandEvaluation`, the existing
`BiddingEngine`, `RuleDecision`, and shared top-priority conflict handling. HCP,
support, balanced shape, and side-suit shortness come exclusively from the core
evaluation. There is no second evaluator, hidden opener/responder card input,
PT calculation, or DDS dependency.

## Qualitative strength and precedence

No numeric definition of extras/minimum was approved. Therefore `3M` and `4M`
are conditional on caller-supplied `OpenerStrengthEvidence`, containing a typed
EXTRAS or MINIMUM classification, an explanation, source pointers, and the exact
hand/auction being assessed. Evidence bound to another hand, dealer, or auction
is rejected. The single enum cannot simultaneously classify a hand as both.
UNKNOWN or absent evidence never becomes extras/minimum based on HCP. Fixed
classifications in tests are interface probes, not proposed HCP ranges.

The implementation follows the listed order as deterministic priority:

1. Side-suit singleton/void (priority 400).
2. Explicit EXTRAS classification -> 3M (300).
3. Core balanced shape and 14-15 HCP -> 3NT (200).
4. Explicit MINIMUM classification -> 4M (100).

These precedence and explicit-classification choices were presented for user
clarification during implementation. They are conservative implementation
choices, not newly approved numeric partnership ranges. No further qualification
is inferred when the corresponding evidence is missing.

Two short side suits have equal priority. The shared conflict handler returns
CONFLICT with no selected call rather than using suit order. Lower-priority
strength descriptions do not bypass this unresolved shortness choice. A void is
not ranked above or below a singleton; both meet the approved definition.

`JacobyMeaning.game_forcing` records the established Jacoby agreement's game-force
context, including when 4M reaches game; it does not claim a further force beyond
game. Shortness bids explicitly identify the shown side suit and artificial
meaning. The initial response records artificial/GF meaning and minimum support;
3M records extras/slam interest; 3NT records balance and the 14-15 range; 4M
records minimum. Selected decisions cite this approval; strength-based decisions
also retain the caller's classification sources.

## Scope and remaining gaps

Only exact uncontested `1H/1S P` response positions and `1H/1S P 2NT P` opener
positions are implemented. Leading passes, competition, other openings, and
later calls abstain; completed auctions are rejected by the existing context
contract. Previous calls are accepted as visible auction evidence, not rechecked
against hidden hands or silently normalized into another auction.

Remaining gaps: automatic EXTRAS/MINIMUM classification, multiple-short-suit
selection, passed-hand/interference agreements, later responder continuations,
and production adoption. Unsupported hands return no call, never an inferred
Pass. No Bergen, Drury, Splinter, Swiss, control bidding, or slam method added.

## Validation

- B2.4A2 focused: **107 passed**.
- Directly related Jacoby/profile tests: **185 passed**.
- Total: **292 passed**, no failures or skips.

Related tests: the prior B2.4A legacy-boundary audit (50), existing NT Jacoby
response/acceptance/continuation and strength-policy tests (35), and Phase
29X/29Y resolver/profile tests (100). B2.4A assertions continue to apply to the
legacy snapshot and unchanged standard router; the new revision is explicit.

Tests cover 12/13-HCP and 3/4-card support boundaries, additional strength/support
values, balanced/semi-balanced/unbalanced responder shapes, every side suit's
void/singleton/doubleton cases, both original majors, balanced 13/14/15/16 HCP,
semi-balanced exclusions, explicit extras/minimum, precedence and conflicts,
source/evidence binding, profile isolation and overrides, later-call exclusions,
core facts, immutability, dealer orientation, deterministic selection and router
invariance. No full historical regression, full B2.1-B2.3 compatibility, PT
dataset, or DDS benchmark ran.

`production_changed = False`; routes before = 45; routes after = 45.
No staging, commit, push, or Bergen work. OneDrive was not touched.
