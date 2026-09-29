# B2.4A Jacoby 2NT major-raise consolidation audit

## Result and scope

**There is no existing executable Jacoby 2NT major-raise implementation to
consolidate at this checkpoint.** Neither the first-response engines after 1H/1S
nor opener/responder continuation routes implement this convention. This phase
therefore consolidates the findings and adds focused safeguards around the
existing APIs. It does not claim new executable coverage or add an always-abstain
parallel evaluator. No production module or public API changes.

The similarly named `sayc_2nt_jacoby.py` implements transfers AFTER a natural 2NT
opening. It is not the artificial 2NT response to a one-major opening. The
`jacoby_continuation_strength_policy` also belongs to accepted 1NT transfers;
its INVITATIONAL -> 2NT mapping cannot be used as a major-raise meaning.

## Inventory and reuse

| Position (opponent passes omitted) | Existing implementation | B2.4A result |
| --- | --- | --- |
| 1H -> 2NT | General `sayc.response.1h` route exists; no Jacoby 2NT rule. | Preserve existing first-response rules and explicit unsupported cases. |
| 1S -> 2NT | General `sayc.response.1s` route exists; no Jacoby 2NT rule. | Same boundary. |
| 1H/1S-2NT -> opener rebid | No matching production route. | Existing `assess_opener_rebid` abstains. |
| 1H/1S-2NT-opener rebid -> responder continuation | No matching production route. | Existing `assess_responder_rebid` abstains, including after a game bid. No Pass inferred. |
| 1NT transfer response, acceptance, continuation | Five existing Jacoby transfer routes. | Unchanged; cannot substitute for a major raise. |
| Natural 2NT transfer response and acceptance | Three existing Jacoby transfer routes. | Unchanged; cannot substitute for a major raise. |

Reused directly: `assess_first_response`, `assess_opener_rebid`,
`assess_responder_rebid`, the existing router and rules, `HandEvaluation`,
partnership resolver, and shared profile binding/conflict handling. There are
zero executable Jacoby 2NT major-raise rules to reuse. No new continuation
family, convention option binding, strength classifier, or route was created.

The prior B2.1-B2.3 reports and the Jacoby-related audit inventory were inspected.
Phase 12C/12D and responder source-readiness references concern accepted NT
transfers and their policy boundaries. They do not authorize major-raise rules.
No historical audit sample or dataset was rerun.

## Source meaning, fit and unresolved choices

Local source references (repository-root relative):

- `knowledge/bidding/conventions/responses/jacoby-notrump.md`, Overview,
  Requirements, Meaning of 2NT, Standard Response Structure, Partnership
  Agreements: artificial response to 1H/1S, four-card-or-longer support,
  game-forcing values, possible slam interest. It describes approximately 13+
  HCP **or equivalent playing strength**, and multiple opener response schemes.
- `knowledge/bidding/natural-bids/responses/response-to-major-opening.md`,
  Jacoby 2NT and 2NT: distinguishes a game-forcing support raise from a natural
  invitational 2NT when Jacoby is not played.
- `knowledge/bidding/systems/2-over-1.md`, Jacoby 2NT: describes four-card support,
  game force, balanced/semi-balanced and no shortness. The dedicated convention
  article also describes balanced or unbalanced hands and variant structures.
- `knowledge/bidding/convention-cards/cc-nily-nisim.md`, Conventions: lists
  Jacoby Notrump but does not provide a complete executable trigger/precedence
  and continuation contract. The current typed Nisim-Nily profile does not bind
  a Jacoby 2NT family.

These source statements are preserved here as documentation, not promoted to
new executable defaults. In particular, source examples do not authorize us to
choose a hard 13-HCP floor, a shape restriction, a lighter-strength exception,
an opener shortness/strength priority, or responder cue-bid/slam decisions.
No distribution, ERV, playing-trick, PT research, or DDS calculation is introduced.

Remaining implementation gaps are the initial raise qualification and its
precedence against existing responses; explicit profile binding and natural
versus artificial 2NT resolution; complete opener response meanings/priorities;
and responder continuation contracts. Suit support and a game-force label alone
do not resolve those gaps. No new Bergen, Drury, Splinter or Swiss rule is added.

## Profile isolation and conflict handling

The resolver remains the sole authority for system identity, override precedence,
parameters and provenance. Unsupported relevant treatments block fallback rather
than turning into a traditional raise or an unrelated natural NT bid. Duplicate
case-insensitive family declarations are rejected, including competing natural
and Jacoby declarations for the same family. Nisim-Nily retains TWO_OVER_ONE_GF;
its convention-card listing does not implicitly activate a new binding.

Tests use `response.major.2nt` with opaque `jacoby_2nt` / `natural` values only to
probe the existing unsupported-treatment boundary. This is **not** a new approved
family name, public configuration contract, or executable treatment. Similarly,
`forcing=game_force` and `min_support=4` are opaque test parameters whose
preservation is tested; the rules do not interpret them or infer a GF state.

At 12 HCP with four/five-card support, the existing SAYC traditional limit raise
can still be selected. That is preserved as an invitational raise, not relabeled
Jacoby. High-card/support examples outside existing rules remain abstentions.
An explicit unbound 2NT agreement prevents silently selecting an unrelated raise.

## Focused validation

- `tests/test_bridge_b24a_jacoby_2nt.py`: **50 passed**.
- Existing Jacoby tests: **35 passed**, across `test_bridge_sayc_1nt_jacoby.py`,
  `test_bridge_sayc_2nt_jacoby.py`,
  `test_bridge_sayc_1nt_jacoby_continuations.py`, and
  `test_bridge_jacoby_continuation_strength_policy.py`.
- Total: **85 passed**, no failures or skips.

The focused tests cover both major openings, 3/4/5-card support, adjacent
12/13/14 HCP examples without inventing thresholds, missing continuation routes,
profile isolation, natural/artificial declaration conflicts, disabled treatments,
parameter/source-scope retention, deterministic original engine evidence, and
transfer/major-raise separation. All eight existing Jacoby-named routes remain
transfer routes; the complete production router still has 45 routes.

`production_changed = False`; routes before = 45; routes after = 45.
No B2.1/B2.2/B2.3 full compatibility suites, historical regression, PT datasets,
or DDS benchmarks were run. No staging, commit, push, or Bergen work. OneDrive
was not touched.

**Ready to commit the audit report and focused safeguards only.** Executable
Jacoby 2NT major-raise coverage remains unimplemented and is not represented as
completed by this consolidation-only phase.
