# B2.2 Opener Rebid consolidation

`assess_opener_rebid` assesses only opening -> responder's first bid -> opener's
second call. It reuses all 21 existing opener-rebid routes without changing their
rules, predicates, priorities, meanings or sources. No new route is registered.

## API and shared infrastructure

`bridge.opener_rebid.assess_opener_rebid(hand, auction=..., vulnerability=...,
profile=..., base_agreements=(), registry=None,
stayman_dual_major_response_policy_id=None)` returns an immutable
`OpenerRebidAssessment`. It records the opening and response, resolved profile,
canonical context, route ID, one selected RuleDecision or abstention/conflict,
reason, blockers and original engine evidence. `recommended_call` is the single
authoritative outcome; alternatives in `engine_result` remain audit evidence.

The existing partnership resolver still owns precedence and preserves treatment
parameters, source scope and profile sources. B2.1's option bindings and conflict
checks were extracted into `profile_rule_support.py` and are now reused by both
entry points. B2.1's public API and behavior are preserved. Relevant unbound
`rebid` and `opener.rebid` declarations additionally block B2.2 fallback, including
explicit removals and unsupported parameters. No new treatment meanings or
parameter interpretations are introduced.

Core facts come from `BiddingContext.create` and its `HandEvaluation`. All
existing rebid rules already consume those facts. No hand arithmetic or evaluator
is duplicated. The actual prior bids are auction evidence, not reconstructed
from opener's hand; no responder cards or complete deal are accepted. In
particular, this layer does not retroactively requalify the opening or response.

The existing router owns route choice; existing engine priorities own rule
precedence. Different top-priority calls produce explicit CONFLICT rather than
letting registration order conceal a disagreement. Same-call deduplication and
lower-priority evidence remain unchanged. Unsupported hands never become Pass
unless an existing positive Pass rule applies.

## Scope boundaries

Both opponent calls must be Pass. Competitive auctions, responder turns, and
later opener turns are rejected before rule evaluation. Leading passes are
retained rather than normalized: existing exact-auction routes then abstain.
No responder rebid is implemented. Existing Stayman/transfer acceptance assumes
the inquiry/transfer is already established; this phase does not choose it.

Nisim-Nily retains its TWO_OVER_ONE_GF identity. It can use the existing explicit
2/1 GF continuation slices; SAYC-only natural and NT rules do not become global
or leak into that partnership. Its Multi 2D and artificial two-minor 2NT meanings
cannot fall back to natural SAYC continuations. Unsupported systems remain
rejected by the existing typed profile/resolver contract.

## Existing families, precedence and gaps

Opponent passes are omitted in the table for readability.

| Opening/response | Reused executable rebids and precedence | Explicit gaps |
| --- | --- | --- |
| 1C-1D | Four hearts -> 1H; otherwise four spades -> 1S; otherwise six clubs -> 2C; otherwise balanced 12-14 -> 1NT. | Diamond support, jumps/reverses and other uncovered shapes/strengths. |
| 1C-1H | Four-card heart support -> 2H; otherwise four spades -> 1S; otherwise six clubs -> 2C; otherwise balanced 12-14 -> 1NT. | Other strength/jump/reverse branches. |
| 1C-1S | Four spades -> 2S; qualifying reverse (16+, four hearts, longer clubs) -> 2H; otherwise four diamonds with no four hearts -> 2D; then eligible balanced 12-14 -> 1NT / 18-19 -> 2NT; then six clubs -> 2C. | Weak/unqualified heart reverses block lower descriptions; no invented invitation or jump-suit meanings. |
| 1D-1H | Four hearts -> 2H; otherwise four spades -> 1S; otherwise four clubs -> 2C; then eligible balanced 12-14 -> 1NT / 18-19 -> 2NT; then six diamonds -> 2D. | Uncovered shape/strength and jump-suit choices. |
| 1D-1S | Four spades -> 2S; qualifying heart reverse (16+, four hearts, longer diamonds) -> 2H; then four clubs -> 2C; then eligible balanced 12-14 -> 1NT / 18-19 -> 2NT; then six diamonds -> 2D. | Incomplete reverse/other strength descriptions and jumps. |
| 1H-1S | Existing exact four-diamond second suit -> 2D, unless four clubs also compete; then six hearts -> 2H; then eligible balanced 12-14 -> 1NT / 18-19 -> 2NT. | Four-card spade support is reserved but not implemented; club second suit and multi-suit ambiguity remain unresolved. |
| 1H-2H / 1S-2S | Traditional simple raise: opener's 12-14 minimum -> Pass. Existing explanation preserves responder's 6-9 simple-raise meaning. | Invitational/game/slam selections above this minimum; nontraditional raises. |
| Established 1S-2C GF | Second suit four diamonds (without four hearts) -> 2D; otherwise four-club support without competing second suit -> 3C; otherwise six spades without those higher branches -> 2S. | Multiple second suits; qualitative poor/minimum hand alternatives; balanced minimum lacks a numeric contract. |
| Established 1H-2D GF | At least five hearts and four spades -> 2S. | Other shapes; balanced 2NT is evidence-only, not executable. Generic SAYC 18-19 is not imported. |
| Established 1H-2C / 1S-2D GF | Routes exist, but the current exact example rules abstain. | No new symmetrical rules inferred from other GF pairs. |
| 1NT-2D / 1NT-2H | Existing Jacoby acceptance -> 2H / 2S. | No superaccept or new transfer meanings. |
| 1NT-2C | Existing Stayman: no four-card major -> 2D; unique major -> 2H/2S. Exactly 4-4 requires an explicit existing Stayman dual-major policy. | Missing, unresolved, UNKNOWN dual-major preference or shapes outside its exact 4-4 scope. |
| Strong 2C-2D | Balanced 22-24 -> 2NT, with existing waiting-response provenance. | Other HCP, unbalanced hands and other responses. |
| Natural 2NT-3D / 2NT-3H | Existing Jacoby acceptance -> 3H / 3S. | Other acceptance variants. |
| Natural 2NT-3C | Existing Stayman denies/shows a unique four-card major via 3D/3H/3S. | Both four-card majors remain unresolved; the 1NT policy is not generalized to 2NT. |
| Natural 2NT-4D / 2NT-4H | Existing Texas acceptance -> 4H / 4S. | No new responder-side Texas selection or continuations. |
| Multi / weak-two / preempt | No existing executable opener-rebid routes. | Remain explicit abstentions; natural-system fallback is prohibited for unbound partnership meanings. |

The existing reverse source references, established GF context, minimum/simple
raise explanations and 18-19 jump-NT meanings are retained verbatim in the
selected rule evidence. There is no new forcing-state representation, numeric
GF-minimum threshold, jump-suit rule, or invention of invitation/game choices.
Some existing shape-only rules deliberately have no HCP gate; this consolidation
does not add one under the assumption that an opening has already occurred.

## Validation

- **147 B2.2 focused tests passed**.
- **144 B2.1 compatibility tests passed** after the shared-helper extraction.
- **135 directly related existing continuation tests passed**.
- Total: **426 passed**, no skips.

The related selection covers the six natural opener-rebid modules, simple-major
raise continuations, existing 2/1 opener/balanced evidence, 1NT/2NT Jacoby and
Stayman, 2NT Texas, strong 2C, the Stayman preference policy and route
configuration. No full historical regression, PT datasets or DDS benchmarks ran.

Tests exercise HCP and length boundaries, own-suit/support/NT/second-suit choices,
reverse and jump-NT provenance, GF priorities, missing invitation contracts,
profile overrides/removal/parameters, system isolation, all dealer orientations,
first-opener-turn guards, ambiguity and one selected result. A route inventory
check covers every one of the 21 current opener-rebid routes and compares the
complete original engine result with the composed assessment.

`production_changed = False`; routes before = 45; routes after = 45.
No production rule or routing file was modified. No PT research code changed.
No staging, commit, push or B2.3 work.