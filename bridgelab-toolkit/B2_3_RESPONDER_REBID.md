# B2.3 Responder Rebid consolidation

## Scope and API

`bridge.responder_rebid.assess_responder_rebid(hand, auction=...,
vulnerability=..., profile=..., base_agreements=(), registry=None,
jacoby_continuation_strength_policy_id=None,
stayman_continuation_strength_policy_id=None)` assesses only the responder's
second call after an opening, first response, and opener rebid. It accepts the
responder's exact hand and visible auction, not opener cards or a complete deal.

The frozen `ResponderRebidAssessment` records the resolved profile, core
`BiddingContext`, opening/response/opener-rebid calls, route ID, disposition,
selected original `RuleDecision`, complete engine evidence, blockers, and reason.
`recommended_call` is the authoritative single outcome. `production_adopted`
remains False. Existing public APIs and production routing are unchanged.

The auction must be live, with exactly three partnership bids and intervening
opponent passes after any leading passes. Wrong turns, later responder calls,
and competitive/interference positions are rejected. Leading passes are retained;
the existing exact-prefix routes do not support them, so those positions abstain.
Prior bids are accepted as visible evidence; the layer does not retroactively
qualify them from the responder's hand or infer the hidden opener hand.

## Reused infrastructure and precedence

- `BiddingContext.create` supplies the existing core `HandEvaluation`; no HCP,
  shape, shortness, or playing-trick arithmetic is duplicated.
- `resolve_partnership_profile` preserves base-system identity, overrides,
  parameters, and source scope. `profile_rule_support.response_system` supplies
  the B2.1/B2.2 bindings unchanged. Relevant unbound opening/response agreements
  and `rebid`, `opener.rebid`, or `responder.rebid` declarations block fallback.
  Explicit disablement or unsupported parameters cannot be bypassed by a policy.
- `create_standard_sayc_router` supplies all four existing responder routes.
  No new rule, route, or continuation family is registered.
- Original engine priorities determine precedence. The shared
  `top_priority_conflicts` check returns CONFLICT for distinct equal-top-priority
  calls. Same-call deduplication and lower-priority audit evidence are preserved.
- Original explanations and rule/policy sources remain attached to the selected
  decision. A missing route or an abstaining rule produces ABSTAIN, never a
  manufactured Pass. There is no new generic forcing-state model.

The optional IDs select existing explicit caller-supplied policies from the
existing `PolicyRegistry`. They do not create a classifier, choose a default,
interpret agreement parameters, or promote a treatment to a global setting.
Unregistered policies abstain; malformed IDs are rejected. Registry presence
alone does not activate a policy. SAYC-only rules remain SAYC-only: Nisim-Nily
retains its TWO_OVER_ONE_GF identity, and no NT treatment leaks into it.

## Existing families and explicit gaps

Opponent passes are omitted below. All four executable routes have one existing
rule at priority 100; they are distinguished by exact auction prefixes.

| Opening family / prefix | Existing responder outcome reused | Remaining gap |
| --- | --- | --- |
| 1NT-2D-2H / 1NT-2H-2S | `SaycOneNotrumpJacobyContinuationRule`: explicit WEAK -> Pass; INVITATIONAL -> 2NT; GAME_GOING -> 4H / 4S. | No default numeric HCP classifier. UNKNOWN, SLAM_INTEREST, missing/unregistered policy abstain. No own-suit invitation, new suit, superaccept continuation, or slam method is inferred. |
| 1NT-2C-2H / 1NT-2C-2S | `SaycOneNotrumpStaymanMajorFitGameContinuationRule`: explicit GAME_GOING plus 4+ cards in opener's shown major -> 4H / 4S. | OTHER, UNKNOWN, missing/unregistered policy and insufficient shown-major support abstain. No new Stayman meaning, invitation, no-fit, or 2D-denial continuation. |
| 1C / 1D natural continuations | No existing executable responder-rebid route. | Own-suit rebid, preference to opener, raise, NT, fourth-suit/new-suit, signoff, invitation/game choices remain explicit abstentions. |
| 1H / 1S natural continuations | No existing executable responder-rebid route. | Same natural gaps; no major-raise convention, Bergen, Jacoby 2NT, or Drury added. |
| Established 2/1 GF, including 1S-2C-2D and 1H-2D-2S | Resolved game_force treatment and its partnership provenance remain in context; no responder-rebid route exists. | No continuation or Pass is inferred from opener's implemented rebid. No invented GF minimum or continuation mapping. |
| Strong 2C-2D-2NT | No existing responder-rebid route. | No analogy to natural 2NT is assumed; strength/shape continuations remain deferred. |
| Natural 2NT-3D-3H, 2NT-3H-3S, or 2NT-3C-3H/3S | Existing opener acceptance rules do not provide responder's next call. | No 1NT class mapping or new transfer/Stayman structures generalized to 2NT. |
| Multi / preempt / other prefixes | No existing responder-rebid route. | Explicit abstention; no invented convention meanings. |

The prior Phase 12Q source-readiness audit was inspected. It identifies natural
responder-rebid source contracts as incomplete: qualitative candidate calls do
not specify sufficient trigger, strength, support, forcing, and precedence
conditions to execute them. B2.3 does not turn those examples into new rules.
The audit and its large deterministic sample were not rerun.

## Boundary interpretation

The approved Jacoby continuation rule consumes an established auction plus a
policy classification; it does not recheck the transfer's original five-card
condition. This consolidation preserves that behavior, including for supplied
four-, five-, and six-card test hands. It does not manufacture a six-card
invitational own-suit rebid. The Stayman rule does impose the existing four-card
support boundary, which is tested at three, four, and five cards.

There are no approved numeric HCP boundaries in these responder continuation
classifiers. Tests therefore check that representative low/high HCP values and
adjacent strength values do not create a default recommendation. Fixed test
classifiers exercise the existing class-to-call contract only; their test hands
do not establish new partnership HCP thresholds. GAME_GOING NT continuation
classes are not relabeled as a general 2/1 game-force contract.

## Validation

- B2.3 focused: **133 passed**.
- Directly related existing continuation/policy/router tests: **51 passed**.
- B2.1 first-response compatibility: **144 passed**.
- B2.2 opener-rebid compatibility: **147 passed**.
- Total: **475 passed**, no failures or skips.

Focused coverage includes signoff, invitation, NT and game selections;
HCP non-default behavior; suit-length/support boundaries; natural own-suit,
preference, raise and fourth-suit abstentions; GF preservation; registry/profile
isolation; provenance/parameters; deterministic single decisions; explicit
conflicts; all four dealer orientations; wrong-turn/interference guards; and
comparison with complete original engine results for every responder route.

The related selection was limited to the two 1NT continuation test modules,
their two strength-policy test modules, and route configuration. No full
historical regression, PT datasets, or DDS benchmarks ran. No PT research file,
production rule, router, evaluator, resolver, or shared B2.1/B2.2 module changed.

`production_changed = False`; routes before = 45; routes after = 45.
No staging, commit, push, or B2.4 work. OneDrive was not touched.
