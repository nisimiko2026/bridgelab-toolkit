# B2.1 Responder Logic consolidation

Scope: responder's first call only. `bridge.first_response.assess_first_response`
composes the existing partnership resolver, `BiddingContext.create`, and the
existing standard router. It defines no bidding-rule family and changes no
production rule, route, source meaning, HCP threshold or suit-length threshold.

## API and architectural reuse

Call `assess_first_response(hand, auction=..., vulnerability=..., profile=...,
base_agreements=(), registry=None, suit_quality_policy_id=None)`.
The immutable assessment contains the resolved profile (including parameters,
source scope and source IDs), canonical context/core evaluation, opening token,
matched route, disposition, one selected RuleDecision, blockers and full engine
trace. `recommended_call` is the authoritative single response. A recommendation
retains the original rule's reason and KnowledgeSource references. Engine
alternatives remain diagnostic evidence, not additional selected outcomes.

`resolve_partnership_profile` owns base-versus-partnership precedence. Base
agreements are explicit SYSTEM-scope inputs, not inferred from a profile name.
Three exact existing family-to-option bindings are supported:

| Resolved family | Existing option | Supported treatment IDs |
| --- | --- | --- |
| response.major.1nt | forcing_one_notrump | forcing, nonforcing |
| response.major.two_over_one | two_over_one | game_force, natural |
| response.major.raises | major_raise_style | traditional, bergen |

These bindings do not activate unimplemented meanings: Bergen disables existing
traditional raises without manufacturing Bergen calls; natural 2/1 does not
create new natural two-level rules. DISABLE survives resolver removal through
explicit disabling option values, so traditional-raise defaults cannot reappear.
Unbound relevant opening/response treatments or parameters cause abstention;
parameters remain available in the resolved profile rather than being discarded.
Unrelated opening families do not affect the current response. Defaults already
inside existing rule APIs remain unchanged (including traditional SAYC raises).

The optional suit-quality policy ID uses the existing PolicyRegistry lookup.
There is no new default quality test. The full declared system identity is
preserved; Nisim-Nily remains TWO_OVER_ONE_GF and is never relabelled SAYC.
Thus its existing 2/1 GF minor-response slice can execute with explicit quality
policy evidence, but SAYC-only response rules remain unavailable to it.

The auction guard rejects opener/rebid positions before routing. Passed-hand
and competitive first-response positions retain their actual auction, so they
abstain when no existing route matches; no normalization expands rule scope.
The existing router and legacy public APIs remain the source of truth.

## Opening-family inventory, precedence and gaps

All executable routes below are the already registered production routes,
reused without mutation. Priorities are the existing RuleDecision priorities.

| Opening | Existing route / implemented first-response subset | Precedence / overlap | Explicit remaining gaps |
| --- | --- | --- | --- |
| 1C | sayc.response.1c: Pass 0-5; 6+ with a clear 4+ major; 6+ clear longer diamonds; balanced 6-10 no four-card major -> 1NT | Pass 100, majors 90, diamonds 80, NT 70. A balanced longer-diamond hand can match both 1D and 1NT; 1D wins by existing priority. Unequal majors choose longer. | Equal 4+/4+ majors, club raises/inverted-minor choice, uncovered stronger/minor hands. |
| 1D | sayc.response.1d: Pass 0-5; 6+ four hearts or four spades; balanced/no four-card major 10-12 -> 2NT, 13-15 -> 3NT | Pass 100, majors 90, NT 80. Hearts precede spades when both are four; NT gates exclude majors. Invitational/game explanations preserved. | 1NT unspecified stopper suit, diamond raises/inverted minors, natural 2C strength contract, other HCP/shape ranges. |
| 1H | sayc.response.1h: Pass 0-5; traditional simple raise 6-9/3+ support; limit 10-12/4+; 6+/4+ spades without 3 hearts; configured balanced 6-9 1NT without support/better major; explicit qualified 12+ 2/1 minor | Pass 100, raises 90, spades 80, GF minor 75, NT 70. Support excludes spades/NT/GF; spades exclude GF and NT; GF and NT HCP ranges do not overlap. | Bergen calls, unsupported raise/game/slam ranges, absent forcing option, missing/unknown quality policy, tied minors or qualitative GF branches. |
| 1S | sayc.response.1s: same Pass, simple/limit raise, configured 1NT and qualified 2/1 minor structures | Pass 100, raises 90, GF minor 75, NT 70; support/strength gates separate families. No higher major response. | Same treatment/strength/quality gaps; no new natural 2H rule. |
| 1NT | sayc.response.1nt.jacoby: unique 5+ heart/spade suit -> 2D/2H at any HCP | Priority 100; both majors 5+ deliberately abstain. | First-call Stayman, natural NT/pass, minor and other response structures are not executable here; existing Stayman opener responses are later calls. |
| strong 2C | sayc.response.2c.waiting: 2D waiting at all HCP | One rule, priority 100; original waiting/default meaning retained. | Partnership positive responses and non-SAYC execution not implemented. |
| Multi 2D | No implemented first-response route | No competing call is manufactured. Explicit Multi opening treatment blocks natural fallback. | Multi responder meanings remain unimplemented. |
| natural 2NT | sayc.response.2nt.jacoby: unique 5+ heart/spade suit -> 3D/3H at any HCP | Priority 100; both majors 5+ abstain. | Natural first NT/pass, Stayman/Texas first-call selection and other structures absent; opener acceptance rules do not supply these decisions. Nisim-Nily 2NT is a different opening meaning and cannot use this route. |
| weak two / three- or four-level preempt | No implemented first-response routes | Existing source-readiness audits do not constitute executable rules. | Raises, new suits, forcing inquiries and NT responses remain gaps. |

Higher existing priority determines a unique call. Same-call candidates retain
existing engine deduplication. Distinct equal-top-priority calls are explicitly
CONFLICT with no selected response, retaining all decisions; registration order
alone cannot hide a contradiction. No observed existing family required a new
precedence agreement. Missing rules remain abstentions, never inferred Pass.

## Hand facts and isolation

Existing first-response rules already use `context.evaluation` for HCP, exact
lengths and balanced shape. This phase reuses `BiddingContext.create` and adds no
hand arithmetic, parallel evaluator, bidding meaning, DDS or PT research logic.
Profile bindings are local to this opt-in assessment and do not update the global
router, policy registry, system classifiers or partnership resolver.

## Focused validation

- New B2.1 focused tests: **144 passed**.
- Directly related existing tests: **168 passed**.
- Total across these disjoint selections: **312 passed**, no skips.

Related selection: SAYC 1C/1D/1H/1S responses, 1D notrump, major 1NT, 2/1
responses, 1NT/2NT Jacoby modules, strong 2C, major-response options and standard
route configuration. Existing mixed-module tests include their unchanged later
call checks; no later-call implementation was changed. Full historical regression
and research datasets/DDS benchmarks were not run.

Boundary tests cover HCP minima/maxima, lengths, major/minor choices, preserved
forcing/nonforcing and GF/limit meanings, all four dealer orientations, profile
overrides/provenance/unsupported parameters, Nisim-Nily and system isolation,
explicit gaps and conflict handling. Four initial determinism assertions compared
separate Auction objects by identity; they were corrected to compare decisions,
trace and serialized auction. No bidding behavior changed to accommodate tests.

`production_changed = False`; routes before = 45; routes after = 45.
The integration regression compares existing router results and route metadata.
No tracked production files were modified. No commit, push or B2.2 work.