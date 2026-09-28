# PT-A2C — Counterfactual Target Redesign: final validation

**Recommendation: PT-A2D TARGET METHODOLOGY REQUIRED.**

**The exchange target preserves both defender hands and the original exchange invariants; its established coverage remains 76.38%. The new targets may alter defender spot cards and other shortness features. Their increased definition coverage answers a different counterfactual question. These are not recovered exchange cases.**

No candidate is adopted. Definition coverage alone neither establishes causal validity nor justifies PT-A3.

## A. PT-A2B checkpoint

Commit: ed131bf134e38842bd9c1412c28379b6a9d3ffb3.
Message: PT-A2B: calibrate counterfactual coverage and ambiguity.
The checkpoint contains four PT-A2B code/test/report files and six small JSON results (coverage, pilot/main summaries, cap validation, test selections, validation manifest). Environments, logs, detailed archives and unrelated compatibility files were excluded. Nothing was pushed.

## B. Repository state and files

Working directory: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit.
Git root: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree.
Branch: codex/phase18b. HEAD remains the checkpoint above.
PT-A2C is untracked, unstaged and uncommitted; no tracked production file changed.

New files:

- bridge/shortness_target_redesign.py
- tests/test_bridge_pta2c_target_redesign.py
- benchmarks/pta2c_target_validation.py
- benchmarks/pta2c_validation_diagnostics.py
- benchmarks/PTA2C_README.md

Principal outputs under output/pta2c_targets/:

- coverage.json; impossible_reference_census.json
- pilot/summary.json; pilot/comparisons.jsonl.gz
- diagnostics/summary.json; diagnostics/collateral_stress_case.json
- diagnostics/collateral_controls.jsonl.gz
- case_analysis.json; validation_summary.json; test_selections.json

Logs and *_exit_code.txt execution records remain untracked. The existing .pta2_env/ is ignored and must not be committed. Old PT research datasets and saved PT-A2/PT-A2B measurements were read only where required and not overwritten. OneDrive was not touched.

The resumed work verified both interrupted edits, ran affected tests first, recovered the completed pilot/historical run, and added bounded validation diagnostics. The existing implementation was not restarted. No larger main cohort was launched.

## C. Candidate estimands and causal question

The useful prospective quantity for later bidding would concern total declarer tricks conditional on the visible hand, hard auction information, specified strain/declarer and trump allocation. It is not automatically the effect of one fewer side-suit card, one extra ruff, or a fixed shortness bonus. A physical shortness intervention must put replacement cards somewhere; its effects on entries, other shortness and defense cannot be assumed away.

A. Exchange delta: source DDS minus a PT-1B-style doubleton control. Retain first-valid, bounded uniform-control mean, median and original seeded reference.

B. Structural relocation: source DDS minus one explicitly selected nearest legal doubleton deal. Move only the minimum required one or two incoming low spots, with equal outgoing own side spots. Donors may include defenders. Own compensation floors remain; partner's studied doubleton floor is deliberately not imposed.

C. Matched expectation: source DDS minus the mean DDS of four nearest distinct controls from a 32-draw conditional pool, using an exposed lexicographic matching distance.

D. Conditional baseline contrast: source DDS minus the expected DDS under uniform legal nontrump-spot assignments with own studied length two, all honor ownership and every seat's exact trump cards fixed. The pilot estimates that population mean using eight IID draws with replacement.

B/C/D are interpretable as specified hand-reallocation contrasts. None is established as an isolated ruffing or intrinsic shortness value. C and D average broader side-suit structure; B can transfer the shortness benefit to partner. The conditional expected total-trick contrast remains the relevant research direction, but this phase does not select its intervention/reference law.

## D. Preserved variables

All methods keep complete-deal legality, 13 cards per seat, trump suit, exact trump cards/allocation per seat, total fit, every honor in its original hand, every seat's HCP and partnership HCP, declarer and optimal-opening-lead convention fixed. Thus side-suit honor patterns and side-ace entry proxies are exact.

| Variable | A exchange | B structural | C matched | D baseline |
| --- | --- | --- | --- | --- |
| Both complete defender hands | Exact | Spots may move; prioritize fewest changed defender cards | Spots may move; shape distance prioritized | Spots freely reassigned under fixed honors/trumps |
| Own nonstudied compensation floors | Exact rule retained | Retained | Not imposed | Not imposed |
| Partner studied length >=2 | Required | Not required | Not required | Not required |
| Other side-suit lengths | Limited exchange changes | Minimum relocation changes | Approximately matched by explicit distance | Allowed to change |
| Other shortness features | Restricted, not globally fixed | Can change in other hands | Can change, including own hand | Can change, including own hand |
| Actual entries and ruffable losers | May change | May change | Proxy difference is a matching component | May change |

Actual entries are not equivalent to side aces and are not claimed fixed. No solver-derived ruff count is used. Vulnerability and contract level do not alter the maximum-trick outcome being measured; score/decision value is out of scope. A fixed opening lead is not imposed.

## E. Definition coverage and structural exclusions

Zero-DDS census over the same 5,000 hypotheses:

| Target | Defined / 5,000 | Coverage | Singleton coverage | Void coverage |
| --- | --- | --- | --- | --- |
| A | 3819 | 76.38% | 84.08% | 68.68% |
| B | 5000 | 100.00% | 100.00% | 100.00% |
| C | 5000 | 100.00% | 100.00% | 100.00% |
| D | 5000 | 100.00% | 100.00% | 100.00% |

This census contains only the two original visible hands. It is not universal coverage. The exchange exclusions remain structurally selected. New targets are defined there because their rules permit interventions previously excluded, not because the old missing outcomes were identified.

Separate stress census, never pooled into a flattering aggregate coverage number:

| Exact own hand | A | B | C | D |
| --- | --- | --- | --- | --- |
| AKQJT.AKQ.2.AKQJ | excluded: own_compensation_spots_insufficient_honors_locked | excluded: fixed_honors_and_trumps_leave_no_doubleton_capacity | excluded: fixed_honors_and_trumps_leave_no_doubleton_capacity | excluded: fixed_honors_and_trumps_leave_no_doubleton_capacity |
| AKQJT9876543.2.-.- | excluded: own_side_suit_doubleton_floor | excluded: fixed_honors_and_trumps_leave_no_doubleton_capacity | excluded: fixed_honors_and_trumps_leave_no_doubleton_capacity | excluded: fixed_honors_and_trumps_leave_no_doubleton_capacity |
| AKQJ9876.543.-.T2 | excluded: own_side_suit_doubleton_floor | excluded: structural_own_compensation_floor | defined | defined |

A and B exclude all three stress cases; C/D exclude the two fixed-card-capacity cases. A fixed 12-trump hand leaves only one side-suit slot and cannot acquire a doubleton. The honor-locked singleton likewise has insufficient free slots while preserving all honors.

For AKQJ9876.543.-.T2, B retains COMPENSATION_FLOOR. C/D remain evaluable but must change another own shortness feature: after eight fixed trumps plus a diamond doubleton, only three cards remain for hearts/clubs. Real-DDS contrasts for that case are C=+1 and D=+1.125; B stays undefined. Nothing is imputed as zero.

## F. Control construction and matching distance

B enumerates every minimum-size legal low-spot relocation, holding honors/trumps fixed and allowing any other seat to donate. It orders controls by changed defender-card count, then the default matching distance, then a fixed canonical hash. It is one defined structural policy, not a DDS-selected favorable control.

C's distance is the lexicographic tuple: defender nontrump shape L1 difference; partner nontrump shape L1 difference; own other-side length L1 difference; absolute change in the published ruffable-loser proxy. HCP, honor and trump differences are prohibited rather than assigned hidden penalties. An explicit alternative prioritizes partner before defenders. No numeric weights are invented or fitted. Ties use canonical hashes. It finds nearest controls in the finite pool, not provably nearest over the whole population.

D generates its exact uniform proposal without rejection: choose own required studied spots uniformly, choose own remaining nonstudied spots uniformly, then uniformly partition remaining spots into the other seats' fixed vacancies. Every physical allocation has the same product probability. The exact support cardinality is combinatorial. Duplicate draws retain their probability mass.

Only the pool construction is exact; an eight-draw DDS mean is not the exact population expectation. C selects four distinct controls from the pool and is not IID after selection. B/C/D use reproducible seeds; none conditions on DDS results while selecting controls.

## G. Exchange-target comparisons

The recovered pilot has 30 full source cases: 20 PT-A2B conditional sources, four PT-1B-conditioned cases, four diverse-deal diagnostics and two impossible-reference stresses. An added stress case is measured separately. Priors/cohorts are not pooled for agreement claims.

For the principal PT-A2B cohort, 16 cases overlap the exchange target. Differences below are new minus exchange. Rank correlation is Spearman with average ranks for ties. Sign disagreements include zero versus nonzero; large disagreement means absolute difference >=1.5 tricks.

| New target | Exchange comparator | n | Mean diff | Median diff | Pearson | Spearman | Sign differences | Large cases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B structural | first_valid | 16 | 0.1875 | 0.0000 | 0.7891 | 0.7997 | 2 | 0 |
| B structural | mean | 16 | -0.2214 | 0.0000 | 0.7811 | 0.8422 | 3 | 1 |
| B structural | median | 16 | -0.3750 | 0.0000 | 0.7063 | 0.7501 | 4 | 1 |
| C matched | first_valid | 16 | 0.0938 | 0.0000 | 0.6128 | 0.5898 | 6 | 2 |
| C matched | mean | 16 | -0.3151 | -0.5000 | 0.6693 | 0.6739 | 4 | 2 |
| C matched | median | 16 | -0.4688 | -0.5000 | 0.6645 | 0.7269 | 5 | 2 |
| D baseline | first_valid | 16 | 0.0703 | -0.0625 | 0.6417 | 0.6451 | 7 | 1 |
| D baseline | mean | 16 | -0.3385 | -0.3750 | 0.6544 | 0.7387 | 4 | 1 |
| D baseline | median | 16 | -0.4922 | -0.5000 | 0.6312 | 0.7464 | 5 | 1 |

The exchange mean/median use up to eight distinct terminals; exhaustive status is retained. The original PT-A2 seeded reference is also saved and is not mislabeled first-valid.

PT-1B-conditioned validation has only three overlapping cases; mean differences versus exchange mean are B=-0.25, C=-0.0833, D=-0.125. Four diverse-deal overlaps have differences B=-0.10, C=-0.10, D=-0.00625. Their small counts prevent strong claims. Full first/mean/median correlation and sign tables are in pilot/summary.json. No coefficients were fitted and no full PT-1 corpus was rerun.

## H. Concrete structural cases

Complete replayable records are saved in case_analysis.json.

Agreement: exchange mean 0, B=0 and C=0. Matching can agree even though it changes defender spots; agreement is not proof of a common estimand.

Source: N:J976.K.AK875.852|E:-.JT32.QJ642.AKQ4|S:AKQ42.9876.3.J76|W:T853.AQ54.T9.T93

Large disagreement: exchange mean +2.5 (median +3, first-valid +1), B=+1, C=+1, D=+0.625. Partner starts with five diamonds; exchange removes two within partnership, whereas C/D reshape nontrump spots across all seats. Source DDS=11; D controls average 10.375. The 1.875-trick disagreement is substantive, not a test failure.

Source: N:JT83.2.AJ743.AK8|E:96.AJT43.QT5.Q42|S:AKQ42.98765.-.J76|W:75.KQ.K9862.T953

Newly defined under a different estimand: exchange is excluded because partner starts with only two diamonds. B yields -1 by making partner's J7 into singleton J and changing other side-suit cards, while C=+1.25 and D=+0.625. B preserves defenders here but violates the old partner floor; C/D also alter defenders. This is not a recovered exchange outcome.

Source: N:9876.AK3.J7.KQ32|E:5.Q2.AKQT9542.84|S:AKQ42.9876.3.J76|W:JT3.JT54.86.AT95

The large-disagreement source also illustrates exchange ambiguity: legal sampled exchange deltas range from +1 to +3. That two-trick spread is distinct from the new targets' differences in population, matching and side-suit reallocation.

## I. Singleton results

All ten original singleton pilot sources are defined for B/C/D. Sixteen-case overlap results above should not be substituted for unconditional means. Descriptive means for the ten singleton sources are:

| Target | n | Mean contrast |
| --- | --- | --- |
| B structural | 10 | 0.4000 |
| C matched | 10 | 0.6750 |
| D baseline | 10 | 0.5625 |

## J. Void results

All ten original void pilot sources are defined for B/C/D. These descriptive means refer to the same ten sources per target:

| Target | n | Mean contrast |
| --- | --- | --- |
| B structural | 10 | 0.9000 |
| C matched | 10 | 0.6750 |
| D baseline | 10 | 0.5500 |

The values are target-dependent total-trick contrasts, not singleton/void coefficients. Short/equal/long-trump roles, loser proxies, side-ace proxies and defender splits are retained for each source. The supplied pooled descriptive strata must not be interpreted as a common-prior calibration result; cohort-specific comparisons are used above.

## K. Fit-state behavior and experimental expectations

PT-A1B hard-conditioned sampling feeds a separate experimental comparison API; the existing PT-A2 estimator is unchanged. Four hypotheses per state demonstrate behavior, not a production-grade accuracy claim. No candidate is adopted. Means below average each candidate over the same hard-conditioned sampled hypotheses:

| State | B mean | C mean | D mean |
| --- | --- | --- | --- |
| singleton_unknown_fit | 0.7500 | 0.4375 | 0.3125 |
| singleton_support_ge3 | 0.0000 | 0.5000 | 0.5000 |
| singleton_support_ge4 | 0.0000 | -0.1875 | -0.4062 |
| singleton_support_eq4 | 1.0000 | 0.8750 | 0.9062 |
| singleton_defender_diamonds_5_3 | 0.7500 | 0.3750 | 0.5000 |
| void_unknown_fit | 0.2500 | -0.0625 | -0.0938 |
| void_support_ge3 | 1.0000 | 0.6875 | 0.9062 |
| void_support_ge4 | 0.2500 | 0.5625 | -0.1250 |
| void_support_eq4 | 1.7500 | 1.7500 | 1.4375 |
| void_defender_diamonds_5_3 | 1.5000 | 1.3750 | 1.1562 |

No monotonic fit ordering is enforced. Guarantees >=3, >=4, exactly four, and defender-specific diamond evidence change the underlying hypothesis distribution. Four samples per state give substantial sampling uncertainty, recorded separately in each target's statistics. Hard evidence only is used; unresolved soft evidence remains INSUFFICIENT_WEIGHTING.

## L. Hidden-information isolation and full-information collapse

Real-DDS leakage validation passed: two different complete source worlds with identical visible state and sampling/target configuration yield identical experimental partial-information results. A source deal is not accepted by compare_candidate_expectations; actual hidden cards enter only separate validation scoring.

When the outer information state forces one hidden deal, estimates reproduce that deal's corresponding full-information candidate:

| Unique hidden source | Original exchange reference | B | C | D |
| --- | --- | --- | --- | --- |
| singleton | 1 | 1.0000 | 3.0000 | 2.8750 |
| void | 2 | 2.0000 | 3.7500 | 3.8750 |

The singleton results are +1/+3/+2.875 for B/C/D; void results +2/+3.75/+3.875. These differences are expected when the counterfactual population changes. Collapse means equality with the chosen candidate's full-information algorithm under the same seed/configuration, not forced agreement with exchange.

For C/D this is collapse to a deterministic finite-control estimate. Zero outer SE does not eliminate control-set approximation error or prove the infinite-population baseline mean. D retains a separate finite-reference SE.

## M. Defender spots, collateral shortness and matching stability

Defender-only validation uses the first selected C or D control for three singleton and three void sources. It exhausts legal one-swap nontrump spot transpositions between the defenders while fixing both partnership hands, all honors/trumps, every hand shape, and C's complete matching-distance vector. Source DDS remains fixed.

This is a controlled conditional-neighborhood diagnostic. It changes a permissible finite control realization; it does not claim that the original finite C pool was reselected or that D's population expectation changes.

| Target | Sources | Nonzero control spread | Mean spread | Maximum spread |
| --- | --- | --- | --- | --- |
| C matched | 6 | 1 | 0.1667 | 1 |
| D baseline | 6 | 0 | 0.0000 | 0 |

One of six C neighborhoods has a one-trick spread. Replacing just that selected control changes the four-control target mean over a 0.25-trick range. D has zero spread in these six restricted neighborhoods; this is not proof of general defender-spot invariance. Broader spot redistributions can change shapes and are a different diagnostic.

This conditional-neighborhood diagnostic covers C/D. B's selected minimum-relocation policy was held fixed; no general defender-invariance claim is made for B. Testing alternative defender realizations within B's own co-optimal minimal family remains a limitation. No extra defender exchange was silently added to its definition.

Collateral shortness is a change among void/singleton/two-or-more in any seat/suit except the intended own studied transition and trump suit. Own collateral is reported separately. Counts include 30 pilot source cases plus the added compensation-floor stress case:

| Target | Controls | Own collateral | Any collateral | Changed-group mean delta | Unchanged-group mean delta | Changed-group delta range |
| --- | --- | --- | --- | --- | --- | --- |
| B structural | 28 | 0 (0.0%) | 10 (35.7%) | 0.8000 | 0.5556 | -1 to 2 |
| C matched | 116 | 19 (16.4%) | 60 (51.7%) | 0.8167 | 0.5536 | -2 to 3 |
| D baseline | 232 | 55 (23.7%) | 163 (70.3%) | 0.6626 | 0.5217 | -4 to 3 |

Within sources having both categories, the own-collateral changed-minus-unchanged mean contrast ranges from -2.667 to +1.333 tricks for C (nine sources), and -1.667 to +0.571 for D (17 sources). These are descriptive differences, not isolated causal effects: permissible spot and shape changes accompany the shortness change. Complete effect distributions, histograms and all structural transitions are saved.

Changing matching priority to partner-first alters C in four of six sensitivity cases, by as much as 0.5 trick. Changing the reference seed alters C by up to 0.75 and D by up to 0.875; doubling the pool alters C by up to 0.5. Priority, finite pool and seed sensitivity remain material. B's lack of seed sensitivity is by deterministic definition, not proof that its structural intervention is uniquely correct.

The new targets remain defensible as explicit reallocation/reference contrasts. Their interpretation as pure shortness value is not defensible without further methodological choices.

## N. Uncertainty decomposition

Keep these components separate:

1. Hidden-hand sampling uncertainty: outer SD/SE/interval for the specified finite-control candidate under PT-A1B hard evidence.
2. Exchange-control ambiguity: multiple original invariant-preserving exchange outcomes.
3. Matched-control ambiguity: matching priority, distance, tie policy and permissible control population.
4. Finite reference-set uncertainty: D's IID control SE and seed/pool sensitivity; C's selected controls are dependent, so it receives no misleading IID SE.
5. Defender-spot-card variation: controlled shape-preserving neighborhood spreads above.
6. Collateral-shortness variation: structural transitions and descriptive effect distributions above.
7. Residual structural exclusions: absent legal reference, never a zero delta.

Structural model uncertainty also includes the choice among A/B/C/D. DDS itself is deterministic for fixed deal/declarer/strain; solver failures are separately counted. No combined omnibus SE is reported.

## O. Computational cost

The saved pilot was recovered, not rerun. It used 1,384 new DDS calls, 853 cache hits, 4,352 validated preloaded cache entries, zero failures and 46.37 seconds (24.71 solver seconds), below its 3,000-call cap.

Additional defender/collateral validation used 177 new calls, 31 cache hits, zero failures and 2.09 seconds, below its separate 2,000-call cap. Total recorded new benchmark calls: 1,561, excluding unit tests. Zero-DDS census work required no solver calls.

No larger main run was warranted before interpreting the pilot's target dependence. No full PT-1B dataset was regenerated.

## P. Exact test counts

Selections overlap and must not be added.

| Selection | Result |
| --- | --- |
| Affected PT-A2C tests immediately after resume | 24 passed, 2 DDS-only skips; exit 0 |
| Final PT-A2C tests within final combined selections | 28 cases: 26 passed + 2 DDS skips on Python 3.14; all 28 passed with DDS |
| PT-A2C/PT-A2B/PT-A2/PT-A1B/PT-A1/PT-A0, Python 3.14 | 199 passed, 6 expected DDS-only skips; exit 0 |
| PT-A2C/PT-A2B/PT-A2, Python 3.12/endplay | 84 passed; exit 0 |
| PT-1 family | 38 passed, 9 expected solver skips; exit 0 |
| Evaluation/probability/vacant-place selection | 111 passed; exit 0 |
| Auction/context/profile selection | 285 passed; exit 0 |
| Historical regression | 2673 passed, 9 skipped, 143 subtests passed in 919.83s (0:15:19); exit 0 |

Historical regression was recovered from the existing completed process, not restarted during resume. It excludes the six separately tested PT-A focused files. Python 3.14 handles the full non-DDS selections; Python 3.12 handles the DDS research tests. The previously documented unrelated Python 3.12 vacant-place compatibility issue was not modified or rerun.

Both new diagnostic guards are included in the final counts. Test filenames, source hashes and exit results are retained in test_selections.json and validation_summary.json. No production or historical audit test was weakened.

## Q. Production invariant

- production_changed = False
- routes before = 45
- routes after = 45

No bidding rule imports or consumes the new targets. The research core has no direct endplay import; DDS is injected through the existing research session. No system interpretation, likelihood calibration, distribution points, fixed singleton/void coefficients or score conversion was introduced.

## R. Recommendation

**PT-A2D TARGET METHODOLOGY REQUIRED.**

B is local and often closer to exchange, but can transfer shortness elsewhere and still has structural exclusions. C depends materially on matching priorities and finite pools. D has a precisely defined probability law, but averages large side-suit/defender changes and retains impossible-reference exclusions. None has yet shown the combination of interpretability, stability, minimal irrelevant-choice sensitivity, broad coherent support and meaningful exchange agreement needed for adoption.

The higher definition coverage does not resolve these issues. A future methodology phase should choose which collateral features may legitimately change for the intended total-trick question and validate that choice across more visible hands and reference realizations. Current exchange findings remain intact; its full hard-evidence ERV remains unavailable under its original definition.

No PT-A3 work, staging, PT-A2C commit or push was performed.
