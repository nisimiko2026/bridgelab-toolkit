# Phase 29R — Strong 2C / playing-tricks framework and evidence preparation

**522 of the 616 opening abstentions are blocked from Pass by unresolved strong playing strength; for 465 it is the sole remaining blocker.** Another 57 also have unresolved families. No Strong 2C predicate, playing-trick formula or production Pass was implemented.

**Canonical HCP correction:** the user confirmed that the cards are correct. HCP is now computed through the repository’s `Hand.parse` and `evaluate_hand` APIs. All ten hands contain exactly 13 cards. Superseded manual totals have been removed; provisional decisions remain unchanged.

## A. State and preservation

- Git root: `C:\Users\nisim\Documents\BridgeLab-phase18b-worktree`; toolkit child `bridgelab-toolkit`.
- Branch `codex/phase18b`; local/tracking/live remote HEAD `c70c0f330d641964308e0e98500e8f47c29699a6`; ahead/behind 0/0.
- Initial status: exactly four Phase 29P and four Phase 29Q files untracked; no tracked changes. Existing ignored `.pytest_cache` access warnings persist.
- All eight files preserved byte-for-byte; before/after SHA256 hashes are in JSON baseline metadata. Four new Phase 29R artifacts only.

## B. Approved concept, not a circular eligibility test

The current partnership concept is: 2C is GAME FORCING and a hand may qualify through 22+ HCP, 9+ Playing Tricks, or independently established game-forcing playing strength. These are alternative eligibility branches; the forcing meaning of the bid is a separate output property.

The module stores this concept declaratively. It does not implement either missing strength calculation and does not use “2C is game forcing” to infer “this hand qualifies for 2C.” The generic SAYC article’s extremely-weak-responder exception is not substituted for the new partnership concept, and existing production remains unchanged.

## C/G. Expert-answer-ready comparison table

Stored cards retain their original symbolic patterns. For canonical HCP and card-count validation only, each x is temporarily represented by a distinct zero-HCP spot in its suit. These representatives do not establish actual intermediates, suit quality or playing tricks. Expert fields are null, additional experts are an empty list, and consensus is AWAITING_EXPERTS for every row. User choices are PROVISIONAL evidence, not approved hand predicates.

| Hand | Cards S/H/D/C | Canonical HCP | Card count | User | Expert1 | Expert2 | Additional experts | Consensus |
|---:|---|---:|---:|---|---|---|---|---|
| 1 | `S AKQJxx / H AKx / D xx / C xx` | 17 | 13 | 2C | null | null | [] | AWAITING_EXPERTS |
| 2 | `S AKQJxxx / H AQx / D xx / C x` | 16 | 13 | 1S | null | null | [] | AWAITING_EXPERTS |
| 3 | `S AKQxxxx / H AKx / D xx / C x` | 16 | 13 | 2C | null | null | [] | AWAITING_EXPERTS |
| 4 | `S AKQJxxx / H KQx / D xx / C x` | 15 | 13 | 1S | null | null | [] | AWAITING_EXPERTS |
| 5 | `S AKQxxx / H AKQx / D xx / C x` | 18 | 13 | 1S | null | null | [] | AWAITING_EXPERTS |
| 6 | `S AKQxxx / H AQJx / D Kx / C x` | 19 | 13 | 1S | null | null | [] | AWAITING_EXPERTS |
| 7 | `S AKQJxx / H x / D AKQxx / C x` | 19 | 13 | 2C | null | null | [] | AWAITING_EXPERTS |
| 8 | `S AKxxx / H AKQxx / D Ax / C x` | 20 | 13 | 2C | null | null | [] | AWAITING_EXPERTS |
| 9 | `S AQJxxx / H AKx / D KQx / C x` | 19 | 13 | 1S | null | null | [] | AWAITING_EXPERTS |
| 10 | `S AKQJxxxx / H Kx / D Qx / C x` | 15 | 13 | 1S | null | null | [] | AWAITING_EXPERTS |

The JSON `probes` array is ready for later answers. `record_expert_answer(probe, ExpertAnswer(expert_id, decision, notes))` returns a new immutable evidence row, supports more than two experts and distinguishes single-expert, agreement and disagreement. It never rewrites the provisional user decision or adopts a rule. Use consistent call labels such as 2C/1S; expert notes can record uncertainty or a requested card correction.

## D. Implementation and source inventory

Files are relative to the git root. A Draft/Standard article label is internal metadata, not authenticated authority. The default source-authority registry is empty. Production-active references mean only the stated existing subset is consumed; no new theory is implied.

| File | Symbol/section | Definition or scope | Executable | Production-active | Source/provenance |
|---|---|---|---|---|---|
| bridgelab-toolkit/bridge/sayc.py | SaycStrongTwoClubOpeningRule; _clear_strong_two_club | SAYC unopened context; 22+ HCP ->2C. 9+ playing-trick alternative explicitly unevaluated. No PT or independent-GF calculation. | True | True | KnowledgeSource bidding/systems/sayc#Opening Bid Requirements / Strong 2♣ Opening; internal reference, not authenticated authority |
| bridgelab-toolkit/bridge/sayc_strong_two_club.py | SaycStrongTwoClubWaitingResponseRule; SaycStrongTwoClubBalancedRebidRule | After established2C-P:2D waiting; after2C-P-2D-P balanced22–24:2NT. These consume an opening, not prove eligibility. | True | True | SAYC Responses and response-to-2-clubs#Opener’s Rebids |
| bridgelab-toolkit/bridge/evaluation.py | HandEvaluation; high_card_points; evaluate_hand | Objective HCP(A4,K3,Q2,J1), controls(A2,K1), lengths, balanced shape and raw honors. Controls are not QT; no PT/LTC/independent-GF score. | True | True | Canonical repository hand facts; no new strength interpretation |
| bridgelab-toolkit/bridge/playing_strength_policy.py | PlayingStrengthPolicy; PlayingStrengthAssessment; assess_playing_strength | QUALIFIES/DOES_NOT_QUALIFY/UNKNOWN interface; nonunknown requires explanation/source; no formula or default policy. | True | Interface only; no built-in formula | Explicit application/partnership policy contract |
| bridgelab-toolkit/bridge/policy_registry.py | PolicyRegistry; assess_configured_playing_strength | Explicit selection/resolution of a supplied playing-strength policy. Empty default registry; no numeric PT implementation. | True | Lookup infrastructure active; no default evaluator | Internal infrastructure, not bridge-theory authority |
| bridgelab-toolkit/bridge/sayc_natural_overcalls.py | Natural overcall rule evaluate methods | Consume configured suit-quality and playing-strength policies; missing/unknown policy abstains. Not a Strong 2C criterion. | True | True | Existing overcall sources and registry interfaces |
| bridgelab-toolkit/bridge/milestone_runner.py | _PlayingStrengthQualifies | Benchmark stub always supplies qualifying test evidence. Does not evaluate the hand or PT. | True | False | Explicit benchmark.phase10 fixture; never an admissible production definition |
| bridgelab-toolkit/bridge/two_over_one.py | assess_two_over_one_game_force | Recognizes configured game-forcing auction sequences, not an independent opening-hand strength test. | True | True | Two-over-One system and explicit treatment selection |
| bridgelab-toolkit/bridge/nisim_nily_opening_policy.py | assess_rule_of_20; build_nisim_nily_opening_policy | Executable HCP+two longest >=20 audit arithmetic; Rule22 reference only; historical29M protects strong-playing exceptions. | True | False | User29M declarative partnership evidence; no production integration |
| bridgelab-toolkit/bridge/nisim_nily_opening_pass_contract.py | assess_opening_pass_contract; resolve_families | 29Q checks STRONG_HCP separately from unresolved STRONG_PLAYING_TRICKS; positive opener wins; no unresolved family can establish Pass. | True | False | User29Q audit-only contract, preserves29P scoped negative signatures |
| bridgelab-toolkit/bridge/opening_pass_source_policy_audit.py; opening_pass_positive_predicate_audit.py; opening_pass_safety_evidence_audit.py | strong-playing-tricks evidence, required checks, safety_gap_matrix | 29L/N/O document source incompleteness and the missing below22 exclusion bound; no evaluator supplied. | True | False | Historical audit evidence, not new bidding rules |
| bridgelab-toolkit/bridge/source_authority.py | DEFAULT_SOURCE_AUTHORITY_REGISTRY | Default registrations empty; repository source metadata is not authenticated external authority. | True | True | Verified empty registry; do not elevate Draft/Standard labels to authoritative approval |
| knowledge/bidding/systems/sayc.md | Strong 2♣ Opening | Usually22+HCP OR9+PT; artificial; generic text says game forcing unless responder extremely weak. Current user29R partnership concept is unqualified game forcing, which is preserved separately. | False | HCP branch cited by production only | Draft internal system reference; default authority UNKNOWN |
| knowledge/bidding/natural-bids/opening-bids/2-clubs.md | Basic Requirements; Playing Tricks; Controls | 22+ balanced OR approximately9PT OR too strong for natural opening; qualitative controls/distribution. No independent computation. Printed balanced example claims22HCP but listed honors total26. | False | False | Draft internal reference; not a verified expert answer |
| knowledge/bidding/natural-bids/responses/response-to-2-clubs.md | Meaning of the 2♣ Opening; Expert Evaluation | Describes approximately22+ balanced HCP or too strong for normal opening, at least8.5–9PT and game forcing in most partnerships. This threshold variation supplies no PT calculation and does not supersede current user9+PT policy. | False | Balanced rebid section only is cited by production | Draft internal response reference; qualitative supporting evidence |
| knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md | Purpose; Estimating Playing Tricks; Major Suit Examples; Side Suit Values | Expected declarer tricks with little/no help, suitable fit/contract; explicitly no universal formula. Approximate AKQJxx6,AKQxx5,AQJxxx5,KQJxxx4.5,QJ109xx3.5–4. Side AK2,AQ1.5–2,A1,KQ1,K0.5,QJ0–0.5; worked KQ4 example1.5 differs from table. | False | False | Standard internal article; incomplete approximate examples, not an approved executable method |
| knowledge/bidding/principles/bidding-fundamentals/quick-tricks.md | Standard Quick Trick Values | Immediate honors: AK2,AQ1.5,A1,KQ1,K0.5,others0; suitwise. QT differs from long-term PT and cannot be compared to9PT. | False | False | Standard internal reference; no canonical executable QT scorer found |
| knowledge/bidding/principles/bidding-fundamentals/losing-trick-count.md | Counting Losers; Partnership LTC; When to Use LTC | First three cards/suit and explicit short-suit tables; expected partnership tricks=24−combined losers after fit. Partner hand/fit absent. 13−own losers is not this source formula. Example AJ5 count differs from the basic honor table convention. | False | False | Draft internal reference; context dependent; no canonical executable LTC scorer found |
| knowledge/bidding/principles/bidding-fundamentals/hand-evaluation.md | HCP; Distribution; Controls; Fit Evaluation; LTC | Basic points and qualitative shape/fit/honor evaluation; no independent game-force threshold. | False | Objective subset reflected in evaluation.py only | Draft internal reference |
| knowledge/bidding/principles/bidding-fundamentals/rule-of-20.md | Rule definition; Exceptions | HCP+two longest >=20 opening guideline with qualitative honor/control exceptions; no PT definition or Strong 2C selector. | False | Arithmetic in audit helper; not production Strong 2C | Draft internal reference plus later user partnership approvals for opening strength |
| knowledge/bidding/principles/bidding-fundamentals/rule-of-22.md | Formula; Counting Quick Tricks | HCP+two longest+QT>=22, first/second-seat opening guideline. Not a9PT or game-force criterion. | False | False | Standard internal reference; not partnership-adopted as mandatory rule |
| knowledge/bidding/principles/bidding-fundamentals/kaplan-rubens-hand-evaluation.md | Major Evaluation Factors; Limitations | Qualitative honor concentration, intermediates, controls, distribution and texture; no complete K&R algorithm in repository text. | False | False | Internal reference; no executable evaluator or adoption |
| knowledge/play/declarer-play/notrump-play/establishing-long-suits.md | Basic Principle; Choosing the Right Suit; Count Winners First | Establish winners with attention to entries, tempo, opponents and contract. Not an opening-hand PT formula. | False | False | Draft declarer-play reference, different context |
| knowledge/bidding/systems/culbertson.md | Hand Evaluation | Historical honor-trick table including QJ0.5; also mentions PT. Honor tricks are not a current nisim-nily PT formula. | False | False | Draft historical-system reference, not adopted partnership policy |

A repository-wide textual sweep also recorded **68 knowledge files** mentioning playing tricks. Their sections, context snippets, execution/adoption status and provenance are indexed in the JSON and appendix below. Context mentions and reference links are not additional complete definitions. Searches of toolkit Python found interfaces, audit states and a benchmark stub, but no canonical numeric PT, QT, LTC or independent opening-game-force evaluator.

## E. Descriptive comparison without choosing a formula

**No executable Playing Tricks definition currently exists in the repository.** The playing-tricks article gives approximate holding examples and side-suit estimates, but leaves important holdings, fit, entry and suit-length interactions undefined. The2-clubs article supplies qualitative nine-trick/too-strong criteria only. Independent game-force hand strength is also undefined.

The table below transcribes only the sums supportable under explicitly stated illustrative assumptions. Approximate values are not bounds. An unavailable total is null, never zero. The threshold column concerns only the PT branch; failing it does not exclude the independent game-force branch or establish a specific1S call.

| Probe | Illustrative PT total | >=9? | Comparison to user | Evidence / missing definition |
|---:|---|---|---|---|
| 1 | approximately 8.0 | No, under stated illustration | PT_THRESHOLD_DIFFERS_FROM_USER_2C | S AKQJxx approximately6 + H AK approximately2 + two small suits0 = approximately8. |
| 2 | N/A | UNKNOWN | NOT_COMPUTABLE | Seven-card AKQJxxx is not listed; side AQ is approximately1.5–2. Total unavailable. |
| 3 | N/A | UNKNOWN | NOT_COMPUTABLE | Seven-card AKQxxxx is not listed; side AK approximately2. Total unavailable. |
| 4 | N/A | UNKNOWN | NOT_COMPUTABLE | Seven-card AKQJxxx is not listed; side KQ table1, worked example KQ4=1.5. Total unavailable. |
| 5 | N/A | UNKNOWN | NOT_COMPUTABLE | Six-card AKQxxx and side AKQx lack exact entries. Total unavailable. |
| 6 | N/A | UNKNOWN | NOT_COMPUTABLE | Six-card AKQxxx and side AQJx lack exact entries; side K approximately0.5. Total unavailable. |
| 7 | N/A | UNKNOWN | NOT_COMPUTABLE | S AKQJxx approximately6; AKQxx approximately5 is listed as a MAJOR example. Transferring it to a second long diamond suit to obtain11 needs an unapproved assumption; total left unavailable. |
| 8 | N/A | UNKNOWN | NOT_COMPUTABLE | H AKQxx approximately5 and side A approximately1; S AKxxx lacks an exact long-suit entry. Total unavailable. |
| 9 | approximately 8.0 | No, under stated illustration | PT_THRESHOLD_CONSISTENT_WITH_USER_1S_ONLY | S AQJxxx approximately5 + H AK approximately2 + D KQ table1 + small C0 = approximately8. Worked example KQ4=1.5 would instead give8.5. |
| 10 | N/A | UNKNOWN | NOT_COMPUTABLE | Eight-card AKQJxxxx is not listed; K approximately0.5, Qx not specified in side table. Total unavailable. |

Assumptions for probes 1/9: exact listed long-major estimate; side AK/KQ interpreted as honor combinations in longer side suits; small spots contribute0 under the table; additive approximate illustration as used by the article. Probe 9 would be8.5 using its worked-example KQ4 value rather than the side table’s1. Both are below9, but the inconsistency and context dependence prevent treating either as a safety proof. Probe 1’s provisional2C differs from the narrow PT>=9 illustration; another independent strong-family justification could still explain it. No formula was altered to fit that answer.

For **each of hands 1–10**, the qualitative2-clubs criterion and independent game-force criterion have calculated value=null, >=9 status=null and comparison=NOT_COMPUTABLE. All30 method/hand rows are explicit in JSON. For probe 7, adding6 to5 after transferring the article’s major-suit AKQxx estimate to a second long diamond suit would suggest11, but that transfer is unapproved; it is not installed as a value or algorithm.

### Related metrics are not Playing Tricks

For expert orientation only, these manual transcriptions use the repository QT table, LTC first-three/short-suit tables, and canonical HCP. QT chooses the strongest listed honor combination per suit; LTC follows the supplied AQJ example where applicable. These do not define PT or Strong 2C. LTC’s partnership formula needs partner’s losers and a fit, neither of which is provided. No13−own-losers shortcut is adopted.

| Probe | Reference QT | Reference LTC losers | Rule20 | Reference Rule22 | >=9PT / Strong 2C inference |
|---:|---:|---:|---:|---:|---|
| 1 | 4 | 5 | 26 | 30 | Not applicable; different quantities |
| 2 | 3.5 | 4 | 26 | 29.5 | Not applicable; different quantities |
| 3 | 4 | 4 | 26 | 30 | Not applicable; different quantities |
| 4 | 3 | 4 | 25 | 28 | Not applicable; different quantities |
| 5 | 4 | 3 | 28 | 32 | Not applicable; different quantities |
| 6 | 4 | 3 | 29 | 33 | Not applicable; different quantities |
| 7 | 4 | 2 | 30 | 34 | Not applicable; different quantities |
| 8 | 5 | 3 | 30 | 35 | Not applicable; different quantities |
| 9 | 4.5 | 4 | 28 | 32.5 | Not applicable; different quantities |
| 10 | 2.5 | 4 | 25 | 27.5 | Not applicable; different quantities |

## F. Real 616-hand blocker impact

Reproduced `SimulationConfig(seed=100, deal_count=1000)` through the unchanged29Q contract. The existing audit regenerates and verifies actual hands/routes. Simulation errors: 0. No selected hand is reclassified as Pass.

| Population distinction | Count |
|---|---:|
| All depth0 opening ABSTAINs | 616 |
| Raw unresolved STRONG_PLAYING_TRICKS check | 599 |
| Of those, already affirmatively opening/treatment-supported | 77 |
| Pass-blocked specifically by unresolved strong family | 522 |
| Strong family is the sole remaining blocker | 465 |
| Also protected by another unresolved family | 57 |
| Historical29Q scoped Pass approvals, excluded from blocker analysis | 17 |

Thus599=77+522,522=465+57, and616=77+522+17. A raw unknown check on a known opener is not a Pass-blocked candidate. These are29Q baseline counts, not a new certification of the independent game-force branch approved conceptually in29R.

### HCP distribution of the 522

| HCP | Count |
|---:|---:|
| 0 | 4 |
| 1 | 7 |
| 2 | 17 |
| 3 | 17 |
| 4 | 40 |
| 5 | 59 |
| 6 | 60 |
| 7 | 74 |
| 8 | 74 |
| 9 | 72 |
| 10 | 52 |
| 11 | 46 |

### Shape distribution, sorted lengths

| Shape | Count |
|---|---:|
| 4-3-3-3 | 74 |
| 4-4-3-2 | 127 |
| 4-4-4-1 | 27 |
| 5-3-3-2 | 91 |
| 5-4-2-2 | 63 |
| 5-4-3-1 | 72 |
| 5-4-4-0 | 11 |
| 5-5-2-1 | 5 |
| 5-5-3-0 | 1 |
| 6-3-2-2 | 22 |
| 6-3-3-1 | 8 |
| 6-4-2-1 | 9 |
| 6-4-3-0 | 4 |
| 6-5-1-1 | 1 |
| 6-5-2-0 | 1 |
| 7-2-2-2 | 1 |
| 7-3-2-1 | 3 |
| 7-4-1-1 | 2 |

S/H/D/C-specific shape frequencies are also retained in JSON; sorted shapes above do not imply suit equivalence for policy.

### Longest suit and overlapping protection

| Longest suit | Count |
|---:|---:|
| 4 | 228 |
| 5 | 243 |
| 6 | 45 |
| 7 | 6 |

6+ card suit: 51; 7+ card suit: 6; 8+ card suit: 0. These are nested counts, not disjoint buckets.

| Other unresolved family | Memberships |
|---|---:|
| PREEMPT | 6 |
| PROTECTED_DISTRIBUTION | 8 |
| SIX_MINOR | 35 |
| WEAK_MULTI | 16 |

These memberships overlap within 57 distinct hands. The465 sole-blocker records would still require real negative strong-family evidence; describing a hypothetical cleared check does not classify them Pass.

### 24 representative real blocker hands

Selection covers every observed HCP value, longest-suit length and other-blocker combination, plus early sole-blocker records. All selected records are actual first-seat dealer hands with production ABSTAIN. Dealer and actor coincide. No fictional later-seat context is introduced.

| Deal | Hand S.H.D.C | HCP | S/H/D/C | Rule20 | Dealer/actor | Vuln | Other unresolved families | Current29Q result |
|---:|---|---:|---|---:|---|---|---|---|
| 1 | `J987.962.94.J943` | 2 | 4/3/2/4 | 10 | E/E | NS | None — strong is sole blocker | OTHER_UNRESOLVED |
| 2 | `974.KQT93.53.964` | 5 | 3/5/2/3 | 13 | S/S | EW | None — strong is sole blocker | OTHER_UNRESOLVED |
| 4 | `854.A9853.J74.K4` | 8 | 3/5/3/2 | 16 | N/N | None | None — strong is sole blocker | OTHER_UNRESOLVED |
| 5 | `9.AJT8.532.KT753` | 8 | 1/4/3/5 | 17 | E/E | NS | None — strong is sole blocker | OTHER_UNRESOLVED |
| 6 | `J94.854.7643.KT4` | 4 | 3/3/4/3 | 11 | S/S | EW | None — strong is sole blocker | OTHER_UNRESOLVED |
| 7 | `J952.KT63.854.T9` | 4 | 4/4/3/2 | 12 | W/W | Both | None — strong is sole blocker | OTHER_UNRESOLVED |
| 9 | `Q852.A2.J92.A642` | 11 | 4/2/3/4 | 19 | E/E | NS | None — strong is sole blocker | OTHER_UNRESOLVED |
| 10 | `Q.K84.9752.J9742` | 6 | 1/3/4/5 | 15 | S/S | EW | None — strong is sole blocker | OTHER_UNRESOLVED |
| 17 | `AT52.A76.7653.75` | 8 | 4/3/4/2 | 16 | E/E | NS | None — strong is sole blocker | OTHER_UNRESOLVED |
| 19 | `KT853.JT3.74.K87` | 7 | 5/3/2/3 | 15 | W/W | Both | None — strong is sole blocker | OTHER_UNRESOLVED |
| 23 | `AK4.JT2.KT6.8754` | 11 | 3/3/3/4 | 18 | W/W | Both | None — strong is sole blocker | OTHER_UNRESOLVED |
| 24 | `Q62.A974.J754.T9` | 7 | 3/4/4/2 | 15 | N/N | None | None — strong is sole blocker | OTHER_UNRESOLVED |
| 27 | `932.KQ2.863.A843` | 9 | 3/3/3/4 | 16 | W/W | Both | None — strong is sole blocker | OTHER_UNRESOLVED |
| 36 | `4.T6.QT98732.K98` | 5 | 1/2/7/3 | 15 | N/N | None | PREEMPT, SIX_MINOR | PREEMPT_UNRESOLVED |
| 39 | `A752.AJT9.JT86.2` | 10 | 4/4/4/1 | 18 | W/W | Both | None — strong is sole blocker | OTHER_UNRESOLVED |
| 43 | `85.Q72.43.KJT743` | 6 | 2/3/2/6 | 15 | W/W | Both | SIX_MINOR | PROTECTED_UNRESOLVED |
| 52 | `KT984.QJ986.9.42` | 6 | 5/5/1/2 | 16 | N/N | None | PROTECTED_DISTRIBUTION | PROTECTED_UNRESOLVED |
| 92 | `T54.QJT4.72.6432` | 3 | 3/4/2/4 | 11 | N/N | None | None — strong is sole blocker | OTHER_UNRESOLVED |
| 118 | `T842.QJT9753.4.6` | 3 | 4/7/1/1 | 14 | S/S | EW | WEAK_MULTI, PREEMPT | PREEMPT_UNRESOLVED |
| 119 | `Q98763.963.T7.84` | 2 | 6/3/2/2 | 11 | W/W | Both | WEAK_MULTI | WEAK_MULTI_UNRESOLVED |
| 269 | `T9743.8642.96.T5` | 0 | 5/4/2/2 | 9 | E/E | NS | None — strong is sole blocker | OTHER_UNRESOLVED |
| 401 | `-.T8632.86.AK9854` | 7 | 0/5/2/6 | 18 | E/E | NS | SIX_MINOR, PROTECTED_DISTRIBUTION | PROTECTED_UNRESOLVED |
| 502 | `62.84.J9542.T643` | 1 | 2/2/5/4 | 10 | S/S | EW | None — strong is sole blocker | OTHER_UNRESOLVED |
| 927 | `3.AT9872.3.97432` | 4 | 1/6/1/5 | 15 | W/W | Both | WEAK_MULTI, PROTECTED_DISTRIBUTION | PROTECTED_UNRESOLVED |

## H–I. Artifacts and validation

- `bridge/strong_two_club_policy_audit.py`: declarative concept, immutable probe/expert records, descriptive comparisons and blocker analysis; no strength predicate.
- `bridgelab_phase29r_strong_two_club_policy_audit.json`: expert-ready rows, source inventory, all 522 blocker records, distributions and preservation hashes.
- `bridgelab_phase29r_strong_two_club_policy_audit.md`: this report and review tables.
- `tests/test_bridge_phase29r_strong_two_club_policy_audit.py`: input preservation, canonical HCP and 13-card assertions, noncircular concept, expert consensus isolation, incomplete reference values, actual-deal counts and determinism.

**Focused tests: 48 passed in 2.48s. Production routes: 45.**

Correction-focused selection: Phase 29R, canonical hand evaluation, Strong 2C and SAYC openings. No new phase or production change. Exact command:

```text
python -m pytest -q -p no:cacheprovider tests/test_bridge_phase29r_strong_two_club_policy_audit.py tests/test_bridge_hand_evaluation.py tests/test_bridge_sayc_strong_two_club.py tests/test_bridge_sayc_openings.py
```

`git diff --check`: clean. `git diff --stat`: empty (all 12 additions remain untracked). Four new 29R files additionally checked for trailing whitespace and final newlines. Final status has exactly:

```text
?? bridgelab-toolkit/bridge/nisim_nily_opening_pass_contract.py
?? bridgelab-toolkit/bridge/opening_pass_nisim_nily_policy_audit.py
?? bridgelab-toolkit/bridge/strong_two_club_policy_audit.py
?? bridgelab-toolkit/bridgelab_phase29p_nisim_nily_opening_policy_audit.json
?? bridgelab-toolkit/bridgelab_phase29p_nisim_nily_opening_policy_audit.md
?? bridgelab-toolkit/bridgelab_phase29q_nisim_nily_opening_pass_contract.json
?? bridgelab-toolkit/bridgelab_phase29q_nisim_nily_opening_pass_contract.md
?? bridgelab-toolkit/bridgelab_phase29r_strong_two_club_policy_audit.json
?? bridgelab-toolkit/bridgelab_phase29r_strong_two_club_policy_audit.md
?? bridgelab-toolkit/tests/test_bridge_phase29p_nisim_nily_opening_policy_audit.py
?? bridgelab-toolkit/tests/test_bridge_phase29q_nisim_nily_opening_pass_contract.py
?? bridgelab-toolkit/tests/test_bridge_phase29r_strong_two_club_policy_audit.py
```

No tracked edits, no production semantics/routes changes, no full regression, no commit, no push. The eight Phase 29P/Q files are preserved exactly.

## J. End state and expert review

1. **522/616** have a Pass decision blocked by unresolved Strong 2C playing strength under the 29Q baseline.
2. **465/616** have it as the sole remaining blocker; 57 have additional blockers.
3. Existing PT material is an approximate holding/example table and qualitative Strong 2C guidance. QT, LTC, controls, Rule20/22 and K&R context are different measures; none supplies the missing approved PT/GF test.
4. **No existing PT or independent game-force definition can be adopted without further human approval.** No executable complete definition was found. The new game-forcing partnership concept does not fill that gap.
5. The ten-hand table above and JSON probe records are ready for expert answers. The cards and canonical HCP are confirmed. Retain each expert’s independent decision and reasoning, and review disagreements before choosing any definition. **No production integration is recommended before that review.**

## Appendix: broader repository playing-trick context index

These are reference-only textual matches, not claimed additional algorithms. All are non-executable; direct production use, where any, is limited to the explicitly listed core inventory subset. Full matched sections/snippets and provenance are in JSON.

| File | Matched section(s) | Definition/context excerpt | Executable / adopted PT formula | Provenance |
|---|---|---|---|---|
| knowledge/bidding/conventions/competitive/brozel.md | Strength Requirements | Playing tricks are considerably more important than raw HCP. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/cappelletti.md | Opponent Bids Game | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/dont.md | Opponent Bids Game | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/fit-jump-shift.md | Requirements; Hand Evaluation; Modern Expert Perspective | - playing tricks,; - playing tricks,; - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/fit-jump.md | Hand Evaluation | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/ghestem.md | Opponent Raises | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/hamilton.md | Strong Hands; Competition After the Relay | Playing tricks matter more than HCP.; - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/landy.md | Competition After the Major Is Chosen | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/michaels-cue-bid.md | Opponent Raises | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/multi-landy.md | Strength Requirements; Opponent Raises Notrump | Distribution and playing tricks are more important than raw HCP.; - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/negative-free-bid.md | Hand Evaluation | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/top-and-bottom-cue-bid.md | Hand Evaluation | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/unusual-2nt.md | Strong Style; Responses by Advancer; Opponent Raises | - Playing tricks.; - Playing tricks.; - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/unusual-vs-unusual.md | Hand Evaluation | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/competitive/weak-jump-overcall.md | Typical Strength; Responses by Advancer; Opponent Raises; Tips; Summary | Playing tricks matter more than points.; - Playing tricks.; - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/defensive-methods/twerb.md | Hand Evaluation | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/doubles/dsi.md | Judgment Factors | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/doubles/maximal-double.md | Partner's Responsibilities | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/doubles/re-opening-double.md | Opponent Competes Further; Tips | - Playing tricks.; - Count playing tricks as well as HCP. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/doubles/responsive-double.md | Opponent Competes Further | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/doubles/support-double.md | Further Competition | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/doubles/take-out-double.md | Hand Evaluation; Opponent Raises; Tips | - Playing tricks.; - Playing tricks.; - Count playing tricks as well as HCP. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/game-invitations/game-invitations.md | Evaluating Invitations | - Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/game-invitations/help-suit-game-try.md | Related BridgeLab Articles | - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/game-invitations/invitations-index.md | Hand Evaluation | - Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/game-invitations/long-suit-game-try.md | Related BridgeLab Articles | - `playing-tricks.md` | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/game-invitations/two-way-game-try.md | Playing Strength | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/opening-bids/benjamin-two-bids.md | 2♦ Opening | - Usually eight or more playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/opening-bids/ekren.md | Balancing and Reopening; Overvaluing High Cards | - Playing tricks.; - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/opening-bids/gambling-3nt.md | Expert; Playing Tricks; Playing-Trick Style; Summary | Playing tricks matter more than HCP.; # Playing Tricks; - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/opening-bids/namyats.md | Requirements; Partnership Agreements; Tips | - Eight or more playing tricks.; Some partnerships evaluate primarily by playing tricks rather than HCP.; - Playing trick requirements. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/opening-bids/roman-2-diamonds.md | Requirements | - Usually eight or more playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/opening-bids/two-diamond-multi.md | Strength; Responder Rebids; Competition After the Relay; Balancing and Reopening; Tips | Playing tricks are more important than HCP.; - Playing tricks.; - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/relay/relay-bidding.md | Strength Relay | - playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/responses/2nt-inquiry-over-weak-2.md | Related BridgeLab Articles | - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/responses/minor-suit-stayman.md | Minor Suit Games | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/responses/ogust.md | What Is a Maximum? | - Playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/responses/response-to-gambling-3nt.md | Related BridgeLab Articles | - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/responses/soloway.md | Requirements | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/slam-conventions/asking-bid.md | Suit Quality Asks | - Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/conventions/slam-conventions/slam-bid-index.md | Slam Principles; Hand Evaluation | - Playing Tricks; - Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/opening-bids/2-clubs.md | Basic Requirements; Evaluating Strong Hands; Playing Tricks; Overvaluing HCP; Expert Evaluation | - approximately **9 playing tricks**; - Playing Tricks; Playing tricks are often more important than HCP. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/opening-bids/four-level-preempts.md | Hand Evaluation; Overvaluing HCP; Expert Evaluation; Related BridgeLab Articles; Summary | - Playing Tricks; Shape and playing tricks are more important than raw points.; - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/opening-bids/opening-requirements.md | Overview; Playing Tricks; Modern Expert Philosophy; Expert Evaluation; Learning Progression | - playing tricks,; # Playing Tricks; Playing tricks are one of the best measures of offensive strength. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/opening-bids/three-level-preempts.md | Hand Evaluation; Expert Evaluation; Related BridgeLab Articles | - Playing Tricks; - playing tricks,; - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/opening-bids/weak-two-bids.md | Hand Evaluation; Expert Evaluation; Related BridgeLab Articles | - playing tricks,; - playing tricks,; - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/rebids/jump-rebids.md | Overview; Hand Evaluation; Playing Tricks; Unbalanced Hands; Modern Expert Style | - additional playing tricks,; - playing tricks,; # Playing Tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/rebids/natural-rebids-index.md | Supporting Articles | - **playing-tricks.md** — Evaluating offensive trick-taking potential. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/rebids/rebids-after-preempts.md | Hand Evaluation; Overvaluing High Card Points; Related BridgeLab Articles | - playing tricks,; Playing tricks and suit quality remain more important.; - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/limit-raise.md | Borderline Hands | - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/respond-preemptive-opening-in-3-level.md | General Principles | 2. Count playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/responding-with-unbalanced-hands.md | Overview | - extra playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/response-to-2-clubs.md | Overview; Meaning of the 2♣ Opening; Expert Evaluation | - 9+ playing tricks,; - at least 8½–9 playing tricks,; - playing tricks, | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/response-to-four-level-preempt.md | Evaluating the Hand; Expert Evaluation; Related BridgeLab Articles; Summary | - playing tricks,; - playing tricks,; - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/response-to-three-level-preempt.md | Evaluating the Hand; Expert Evaluation; Related BridgeLab Articles | - playing tricks,; - playing tricks,; - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/natural-bids/responses/response-to-weak-two.md | Expert Evaluation; Related BridgeLab Articles | - playing tricks,; - playing-tricks.md | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/principles/bidding-fundamentals/offensive-vs-defensive-values.md | Indicators of Offensive Strength; Relationship to Other Evaluation Methods; Lean Toward Bidding When; Related Topics | - Playing Tricks; / Playing Tricks / Offensive trick-taking potential /; - You expect many Playing Tricks. | No / No | Internal reference; Standard; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/principles/bidding-fundamentals/playing-tricks.md | Playing Tricks; Purpose; Basic Concept; Estimating Playing Tricks; AKQJxx | # Playing Tricks; **Playing Tricks (PT)** estimate the number of tricks a hand is expected to take **as declarer with little or no help from partner**, assuming a suitable trump fit or an appropriate contract.; Unlike **High Card Points (HCP)**, which measure honor strength, or **Quick Tricks**, which measure immediate winners, Playing Tricks evaluate a hand's **offensive trick-taking potential** based on: | No / No | Internal reference; Standard; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/principles/bidding-fundamentals/preemptive-openings.md | Hand Evaluation; Overvaluing High Cards; Tips; Competition After Responder's Action; See Also | - Playing tricks; - Playing Tricks; Distribution and playing tricks matter far more than raw HCP. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/principles/bidding-fundamentals/seat-position.md | First Seat; Related Topics | Require reasonable Playing Tricks and suit quality.; - Playing Tricks | No / No | Internal reference; Standard; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/principles/bidding-fundamentals/vulnerability.md | Unfavorable Vulnerability; Relationship to Other Principles | - Better Playing Tricks; - Playing Tricks | No / No | Internal reference; Standard; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/principles/principles-index.md | Hand Evaluation | - Playing Tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/systems/acol.md | Principle 3; Hand Evaluation; Expert Tips; Expert Advice | Suit quality and playing tricks receive considerable attention.; - Playing tricks.; Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/systems/benjamin-acol.md | Overview; Opening Structure; 2♣ Opening; 2♦ Opening; Playing Tricks vs High Card Points | - **2♣** = Strong one-suited hand (about 8 playing tricks); / 2♣ / Strong one-suited hand (≈8 playing tricks) /; - about **8 playing tricks** | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/systems/culbertson.md | Overview; Basic Philosophy; Hand Evaluation; Historical Importance; Summary | Unlike modern systems, Culbertson emphasized **honor tricks**, **quick tricks**, and **playing tricks** rather than simply counting High Card Points (HCP). Although the system is no longer played in serious competition, its concepts profoun; - Playing tricks; - Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/systems/polish-club.md | Expert Tips; Expert Advice | Playing Tricks; Playing tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/systems/sayc.md | Hand Evaluation; Requirements | - Playing tricks.; 9+ playing tricks. | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
| knowledge/bidding/systems/standard-american.md | Hand Evaluation | - Playing Tricks | No / No | Internal reference; Draft; unverified authority; context listing is not an adopted definition |
