# PT-A2B — Counterfactual Coverage and Control Calibration

Recommendation: **PT-A2C needed for further counterfactual methodology.**

PT-A2B quantifies structural missingness and compares multiple-control targets without changing production bidding. Broader controls preserve the existing invariants but cannot repair the missing-control set. Averaging controls changes the estimand and reduces some selected-control variability; it does not identify a full hard-evidence shortness value.

## A. PT-A2 checkpoint

Commit: c23cfc8f986c625f62248d6295e85641c9d43da4
Message: PT-A2: add expected ruffing value research oracle

Exactly eight files were committed:

- bridge/playing_trick_shortness_pairs.py
- bridge/expected_ruffing_research.py
- tests/test_bridge_pta2_expected_ruffing.py
- benchmarks/pta2_erv_validation.py
- benchmarks/PTA2_README.md
- output/pta2_erv/pilot/summary.json
- output/pta2_erv/main/summary.json
- output/pta2_erv/main/leakage.json

No environment, logs or hypothesis archives were included. Nothing was pushed.

## B. Repository state

Working directory: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit.
Git root: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree.
Branch: codex/phase18b. HEAD remains the PT-A2 checkpoint above.
PT-A2B files are untracked; there are no tracked modifications and the index is empty.
OneDrive was not touched. No PT-A3 work began.

## C. Files and API

New PT-A2B source/report files:

- bridge/counterfactual_calibration.py
- tests/test_bridge_pta2b_counterfactual_calibration.py
- benchmarks/pta2b_control_validation.py
- benchmarks/PTA2B_README.md

The module supplies FailureReason, Diagnosis, ControlFamily, ControlSet, ControlDistribution, MultiControlEffect and MultiControlEstimate; diagnose, enumerate_controls, representative_controls, evaluate_controls, estimate_multicontrol, pre_control_features, target_statistics and missing_effect_bounds.

estimate_multicontrol accepts PT-A0 state, studied/trump suits, an injected research solver session and hard-only ERVConfig. No source-deal parameter exists. Full source deals enter only the separate evaluation/validation API. PT-A1B remains the hidden-hand generator; explicit likelihoods are rejected by the existing configuration. Soft evidence remains INSUFFICIENT_WEIGHTING.

Durable generated results:

- output/pta2b_controls/coverage.json: classification of all 5,000 original hypotheses, stratified rates and missingness comparisons.
- output/pta2b_controls/pilot/summary.json
- output/pta2b_controls/main/summary.json
- output/pta2b_controls/main/control_cap_validation.json
- output/pta2b_controls/test_selections.json
- output/pta2b_controls/validation.json

Detailed new measurement archives: pilot/effects.jsonl.gz and main/effects.jsonl.gz under output/pta2b_controls/. These retain per-control deltas, complete control IDs, solver provenance, target statistics, evidence and weights. Do not stage them or execution logs automatically. The pre-existing PT research archives and PT-A2 hypothesis archives were not modified; PT-A2 outcome/weight digests were checked.

The existing ignored .pta2_env/ remains local. No environment files should be committed.

Execution logs and exit records, all under output/pta2b_controls/ and intended to remain untracked:

- auction_context_profile.log
- auction_context_profile_exit_code.txt
- control_cap.log
- control_cap_exit_code.txt
- dds_focused.log
- dds_focused_exit_code.txt
- evaluation_probability.log
- evaluation_probability_exit_code.txt
- focused.log
- focused_exit_code.txt
- focused_python314.log
- focused_python314_exit_code.txt
- historical.log
- historical_exit_code.txt
- main.log
- main_exit_code.txt
- pilot.log
- pilot_exit_code.txt
- pt1_family.log
- pt1_family_exit_code.txt
- python312_baseline_compatibility.log
- python312_baseline_compatibility_exit_code.txt

## D. Unevaluable taxonomy

Typed structural categories distinguish studied-suit-is-trump, own-hand-not-short, partner studied-length floor, partner honor lock, own compensation shape floor, and own compensation honor lock. Invalid physical transitions raise explicit invariant failures; duplicate cards are rejected by Deal. Enumeration limits, solver failure and solver-call budget exhaustion are separate computational categories.

Diagnosis records all violated constraints plus a deterministic primary cause. Primary causes partition the missing cases; all-reason counts overlap. No generic structural failure was used in this cohort. Solver and invalid-transition failures were zero.

| Shortness | Total | Evaluable | Missing | Missing rate | Primary partner floor | Primary honor lock | All honor-lock violations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| singleton | 2500 | 2102 | 398 | 15.92% | 380 | 18 | 78 |
| void | 2500 | 1717 | 783 | 31.32% | 742 | 41 | 292 |

Across both hands, 1,122 primary failures require partner to fall below a doubleton; the other 59 lack movable studied-suit spots because honors are fixed. There are 370 honor-lock violations including overlaps. Own-side compensation constraints are typed and tested but do not bind for these two visible hands. Full counts/rates are stratified by information state, singleton/void, own/partner trump structure, studied suit, short/equal/long trump role and ruffable-loser proxy in coverage.json.

## E. Missingness analysis

All observables were extracted from complete sampled hypotheses before constructing or solving controls. They are diagnostic latent features, never extra auction-time evidence. Seat HCP, every seat/suit length, defender split, partner trumps, total fit, own trumps, side-ace entry proxy and ruffable-loser proxy are retained.

Differences below are missing minus evaluable. Standardized differences divide by the square root of the mean of the two within-group population variances.

| Feature | Evaluable mean | Missing mean | Difference | Standardized difference |
| --- | --- | --- | --- | --- |
| partner_trumps | 3.6405 | 3.9204 | 0.2799 | 0.3257 |
| total_trumps | 8.6405 | 8.9204 | 0.2799 | 0.3257 |
| length_N_D | 4.4247 | 2.3709 | -2.0538 | -2.4112 |
| ruffable_loser_proxy | 3.3886 | 1.7714 | -1.6172 | -1.3415 |
| side_ace_entries | 0.8733 | 0.9712 | 0.0979 | 0.1260 |

The approximately two-card partner-diamond difference and large loser-proxy difference show material structural selection. This is not a missing-at-random claim. Per-state comparisons and categorical total-variation distances are supplied to avoid relying only on pooled means. Entries and losers here are explicitly simple proxies, not DDS-derived actual entry counts or a new Playing-Trick valuation.

## F. Expanded families and feasibility proof

Minimal family: reuse PT-A2/PT-1B one-step singleton or two-step void exchanges, deduplicating physical terminal deals. Expanded family: retain every minimal terminal and optionally apply one same-suit low-spot transposition between partners in any nontrump suit. This can replace the original singleton spot or rearrange side-suit spots without changing any hand shape. Duplicate terminal deals are removed.

Both preserve every seat's honors/HCP and exact trump cards, both defenders' complete hands, all hand sizes, legal 52-card partition, viewpoint studied length=2, partner studied length>=2, and no newly created shortness in the viewpoint compensation suits. The optional move preserves every hand's shape. Every optional exchange is reverse-replayed and all final controls pass preservation guards.

Why additional side-suit/multi-card paths cannot gain coverage under these invariants:

Let r=2 minus own studied length (one or two). Partner must have at least r+2 studied cards and at least r studied spots. For each other nontrump suit s, own removable capacity is min(number of spots in s, max(length(s)-2,0)). The capacities must sum to at least r. These conditions are necessary by card conservation, honor immobility and the length floors. They are sufficient: choose r incoming spots and r allowed outgoing spots and exchange them in any order. All intermediate floors hold. Hence the minimal family already reaches every structurally feasible source under these conditions.

Sending cards through another partnership hand, adding cycles, or moving extra side cards cannot create studied spots or defeat these conservation bounds. Moving defenders, trumps or honors, or allowing partner's studied holding to become short, would change the invariants. Those options were not used to inflate coverage.

Expansion introduces additional spot-position/entry/promotion ambiguity. Uniform weighting across its larger terminal set is a different research target, not a claim that extra spot rearrangements are causally preferable.

## G. Coverage improvement

Original census: 3,819/5,000 = 76.38%.
Expanded coverage under unchanged invariants: 3,819/5,000 = 76.38%.
Incremental gain from shape-preserving spot relocation: zero.
Remaining missing: 1,181/5,000 = 23.62%.

The independent bounded calibration sample has 183/240 evaluable prediction hypotheses and 67/80 evaluable holdouts in each family. It is a different sample, not a revision of the 5,000-hypothesis result. All remaining structural missingness stays explicit; there is no acceptance threshold or zero imputation.

## H. Multiple-control target definitions

- PT-A2 reference: its original seeded selection over legal ordered minimal paths. It was never first-valid.
- FIRST-VALID: a separate deterministic comparator, the lexicographically first physical terminal in the chosen family.
- UNIFORM-CONTROLS: arithmetic mean delta over distinct physical terminal controls.
- MEDIAN-CONTROLS: median delta over distinct physical terminals; even populations average the two middle deltas.

The minimal family has one path per singleton terminal and four paths per void terminal. Census candidate counts verify this multiplicity throughout the original valid cohort. Consequently uniform minimal-path weighting and uniform minimal-terminal weighting describe the same population target. Expanded-path multiplicity is not used as a weight. No invented weighting model was added.

For the main cohort, at most eight terminals are solved per target using the eight smallest fixed SHA-256 priorities of canonical control IDs. This deterministic subset is independent of enumeration order and user control seed. It is an approximation to the uniform full-control mean/median when capped, not an exact exhaustive target. Reference and first-valid controls are solved separately and do not receive extra mass in the uniform target.

Every result preserves selected control IDs/deltas, counts enumerated/selected/solved, exhaustive flag, mean, median, min, max, spread and population SD across controls. A failed selected solve invalidates the multi-control target; successes are not silently renormalized.

## I. Invariance and reproducibility

Tests cover reversed candidate enumeration, reversed suit iteration, duplicate enumeration entries, canonical hand/seat/card container order, seed independence of the multi-control selection, all four seat orientations and exact deterministic results. The legacy selected-path comparator can depend on path ordering; the uniform target cannot.

Cards have physical suit/rank identity, not arbitrary external labels. Reordering their representation does not change controls. Swapping physical spot ranks across hands is not generally an irrelevant relabeling: recorded real-DDS counterexamples show different trick counts. For example, a legal same-suit swap of diamond ten and seven between partners changed a control from 9 to 10 declarer tricks. Requiring invariance to that physical change would erase meaningful card-play information.

Real DDS isolation also passed: two saved complete worlds with the same viewpoint hand, state, seed and configuration produce equal MultiControlEstimate results. Source hidden cards are never passed to the partial-information estimator.

## J. Ambiguity distribution

These are observed within-control spreads, separate from outer hidden-hand Monte Carlo standard errors. Bounded samples can underestimate the full control range.

| Family | Evaluable occurrences | Nonzero spread | Fraction | Mean spread | Max spread | Mean control SD | Exhaustive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimal | 250 | 139 | 55.6% | 0.676 | 2 | 0.310 | 13 |
| Expanded | 250 | 129 | 51.6% | 0.636 | 3 | 0.280 | 0 |

The main ambiguity cohort is 240 predictions plus 80 holdouts per family, 250 evaluable occurrences. Exhaustive collapse fixtures are reported separately. Lower observed expanded spread does not establish greater stability: eight controls cover a smaller fraction of its larger population.

A separate bounded cap check exhaustively solved one source per family/shortness cell with 9–150 terminals. These selected cases are not representative.

| Family | Shortness | All controls | Eight-control mean error | 16-control mean error | 32-control mean error |
| --- | --- | --- | --- | --- | --- |
| Expanded | singleton | 132 | +0.068182 | +0.005682 | +0.036932 |
| Expanded | void | 135 | +0.000000 | +0.000000 | +0.000000 |
| Minimal | singleton | 18 | +0.208333 | +0.020833 | +0.000000 |
| Minimal | void | 120 | +0.000000 | +0.000000 | +0.000000 |

Maximum observed eight-control mean error in these four cases was 0.208333 tricks. A larger cap need not improve every deterministic prefix monotonically. Bounded-control approximation error is reported separately from both the physical spread and the hidden-hand SE.

## K. Full-information collapse

The established PT-A2 hidden-deal-collapse fixtures were exhaustively evaluated in both families.

| Shortness | Family | Distinct controls | Mean | Median | Min / max | Original selected delta |
| --- | --- | --- | --- | --- | --- | --- |
| singleton | Minimal | 27 | 1.0 | 1.0 | 1 / 1 | 1 |
| singleton | Expanded | 27 | 1.0 | 1.0 | 1 / 1 | 1 |
| void | Minimal | 216 | 2.0 | 2.0 | 2 / 2 | 2 |
| void | Expanded | 216 | 2.0 | 2.0 | 2 / 2 | 2 |

Thus singleton +1 and void +2 persist across their entire control distributions. The original fixtures have one hidden deal but multiple controls; the terms are not interchangeable. Separate focused fixtures test unique physical controls for singleton and void, including void path deduplication. These are mechanism checks, not representative calibration.

## L. Full hard-evidence ERV feasibility

Outcome C applies: missingness remains structurally important. **Full hard-evidence ERV unavailable.** In fact, for sources with no admissible control, the current target is undefined rather than merely an unobserved numerical value.

The benchmark supplies transparent hypothetical completion sensitivity. With empirical evaluable mass c, observed mean m and any proposed missing-case extension in [-13,13], the empirical completed mean lies in [c*m-13*(1-c), c*m+13*(1-c)]. This is not an identified posterior ERV or a confidence interval. Scenarios for missing deltas -2,-1,0,+1,+2 are recorded symmetrically; zero has no default or preferred status.

For expanded void/support>=3, c=0.5 and m=1.260417, giving hypothetical bounds [-5.869792,7.130208]. Their width illustrates nonidentification. A point interval from 100% coverage in a finite sample is only empirical; it does not prove support-wide coverage.

## M. Calibration comparison

Ten information states use the same two visible hands and general hard constraints as PT-A2. Each family uses the same 24 independent prediction hypotheses and eight independently seeded holdouts per state. Predictions use seeds 93000+100*hand_index+state_index; holdouts use 94000+100*hand_index+state_index. Control reference seed=3202. The new cohort is deliberately bounded; no full PT-1B corpus was rerun.

Across 80 attempted holdouts, 67 are evaluable for every comparator. Bias is predicted minus realized. Each target is assessed against its corresponding realized target.

| Family | Target | Predicted | Realized | Bias | RMSE | MAE |
| --- | --- | --- | --- | --- | --- | --- |
| Expanded | first_valid | 0.8193 | 0.7761 | 0.0431 | 0.9227 | 0.6975 |
| Expanded | median_controls | 1.0858 | 1.1716 | -0.0858 | 0.8622 | 0.6402 |
| Expanded | pta2_selected | 0.9658 | 1.0299 | -0.0640 | 0.9281 | 0.7156 |
| Expanded | uniform_controls | 1.0241 | 1.0504 | -0.0263 | 0.7675 | 0.5538 |
| Minimal | first_valid | 0.8141 | 0.7612 | 0.0529 | 0.9323 | 0.7098 |
| Minimal | median_controls | 1.0870 | 1.1269 | -0.0399 | 0.8807 | 0.6478 |
| Minimal | pta2_selected | 0.9658 | 1.0299 | -0.0640 | 0.9281 | 0.7156 |
| Minimal | uniform_controls | 1.0109 | 0.9994 | 0.0115 | 0.7649 | 0.5615 |

Relative to the selected-path reference, the minimal uniform target shifts mean prediction by +0.045081, RMSE by -0.163199 and MAE by -0.154155. Expanded uniform shifts mean prediction by +0.058247, RMSE by -0.160547 and MAE by -0.161876.

This is internal calibration under the hard-conditioned baseline. Lower error partly reflects a changed, averaged target; it does not establish superior causal validity or calibration for real bidding systems. Approximate bias intervals account for shared prediction Monte Carlo error; they do not include missingness, physical-control ambiguity or bounded-control approximation bias.

Expanded-family predictions by state are below. Means remain conditioned on evaluable hypotheses.

| State | Evaluable / 24 | Reference | Uniform approximation | Median approximation | Uniform MC SE |
| --- | --- | --- | --- | --- | --- |
| singleton_unknown_fit | 23 | 0.4348 | 0.5109 | 0.5217 | 0.1054 |
| singleton_support_ge3 | 18 | 0.6667 | 0.6181 | 0.7222 | 0.1656 |
| singleton_support_ge4 | 18 | 0.9444 | 1.0208 | 1.1389 | 0.1592 |
| singleton_support_eq4 | 20 | 0.6000 | 0.8438 | 0.9250 | 0.1357 |
| singleton_defender_diamonds_5_3 | 24 | 0.6667 | 0.7552 | 0.9792 | 0.1276 |
| void_unknown_fit | 17 | 1.1176 | 1.1324 | 1.0882 | 0.1566 |
| void_support_ge3 | 12 | 1.2500 | 1.2604 | 1.2500 | 0.2129 |
| void_support_ge4 | 14 | 1.5000 | 1.6339 | 1.6786 | 0.1623 |
| void_support_eq4 | 13 | 1.3077 | 1.5481 | 1.6154 | 0.2121 |
| void_defender_diamonds_5_3 | 24 | 1.4167 | 1.2865 | 1.3333 | 0.1409 |

There are four strict pairwise ranking reversals for minimal controls and three for expanded controls versus the original reference (ties excluded). For example, singleton exact-four support moves above singleton minimum-three support under both uniform targets. These small-sample ranking changes are descriptive; no monotonic-fit rule is imposed.

Per-target bands, fixed reference bands (to preserve band membership when comparing targets), singleton/void strata and every information/fit state are included in main/summary.json, with counts, prediction/realization means, biases, RMSE/MAE and intervals. Separate comparison_to_pta2_reference fields expose the shifts. Singleton and void error profiles remain materially different.

## N. Computational cost

| Run | DDS calls | Call cap | Failures | Wall seconds |
| --- | --- | --- | --- | --- |
| Pilot | 727 | 4000 | 0 | 35.83 |
| Main | 4640 | 12000 | 0 | 141.79 |
| Cap validation | 390 | 1000 | 0 | 2.63 |

Total recorded benchmark DDS calls: 5,757, excluding unit tests. Census/final comparison metadata used zero DDS calls. Main DDS wall time was 30.34 seconds of 141.79 total seconds, with 1,918 cache hits.

Across 320 sources per family, minimal controls enumerated 12,946 terminals (maximum 300), selected 1,974, and incurred 2,542 new DDS calls including reference comparisons. Expanded controls enumerated 64,790 terminals (maximum 1,350), selected 2,000, and incurred 1,810 additional DDS calls after cache reuse. This is 7.94 and 5.66 incremental calls per attempted source respectively; expanded cost is order-dependent because minimal ran first. Structural misses need no solves.

Enumeration and validation wall times were 39.02 seconds minimal and 93.89 expanded, including each family's sampling/evaluation work. Collapse and leakage account for the remaining main calls. Cache keys use complete physical deal, declarer and strain. Reusing source/overlapping control solves saves substantial work; no production cache or bidding dependency was added.

## O. Exact test results

Selections overlap and must not be summed.

| Run | Result |
| --- | --- |
| PT-A2B focused / Python 3.14 | 23 passed, 2 DDS-only skips |
| PT-A2B + PT-A2 + PT-A1B + PT-A1 + PT-A0 / Python 3.14 | 173 passed, 4 DDS-only skips; exit 0 |
| PT-A2B + PT-A2 / Python 3.12 + endplay | 56 passed (25 PT-A2B + 31 PT-A2); exit 0 |
| Evaluation/probability selection | 111 passed; exit 0 |
| Auction/context/profile filename selection | 285 passed; exit 0 |
| PT-1 family / Python 3.14 | 38 passed, 9 expected solver skips; exit 0 |
| Historical regression / Python 3.14 | 2673 passed, 9 skipped, 143 subtests passed in 1189.17s (0:19:49); exit 0 |

The initial combined run on Python 3.12 had 170 passed and seven failures in unchanged bridge/probability_questions.py:149 (zero-argument super in a slotted dataclass). One failure was independently reproduced by running the old PT-A1 test alone, without PT-A2B imports. The involved tracked files match the checkpoint. It is a pre-existing runtime compatibility limitation, not hidden as an expected skip and not fixed by changing production code. The full phase selection passes on the established Python 3.14 runtime; real DDS checks pass separately on Python 3.12.

Exact nonhistorical filename selections are recorded in test_selections.json. Their scope differs from earlier PT-A2 selections, so 111 and 285 are the current authoritative subset counts. Historical regression covers the remaining old tests and excludes the five separately tested PT-A phase files.

Additional checks: saved per-control means/spreads recomputed, hypothesis accounting verified, JSON/AST syntax checked, original PT-A2 effect/weight digests unchanged, whitespace checks clean, route count verified.

## P. Production invariant

- production_changed = False
- routes before = 45
- routes after = 45

PT-A2B creates only new research/test/benchmark/report files. No tracked production file changed after the checkpoint. No bidding rule consumes PT-A2/PT-A2B output. DDS remains injected research/validation infrastructure; no direct endplay import exists in the new core module. No points, fixed shortness coefficients, system interpretation or soft-evidence calibration were introduced.

## Q. Remaining limitations

Four distinct issues stay separate:

1. Hidden-hand Monte Carlo uncertainty: the outer SE/CI for the specified evaluable and bounded-control target.
2. DDS deterministic result: fixed-deal trick counts, with failures separately accounted for; no statistical solver noise is assumed.
3. Control-choice ambiguity: within-source spread/SD and different target definitions. Capped-control approximation adds its own numerical uncertainty, calibrated only on four small cases here.
4. Missing-control coverage: structural nonidentification; hypothetical completion sensitivity is not an ordinary confidence interval.

Only two visible hands, spade contracts and diamond shortness are benchmarked. The bounded holdouts share the sampler prior, not an empirical bidding prior. Entries/losers are proxies. Eight controls are usually not exhaustive, and expanded controls add incidental spot-play effects without a causal preference. Physical-rank substitution is not generally an irrelevant symmetry. The historical Python 3.12 compatibility issue remains outside this phase.

## R. Recommendation

**PT-A2C needed for further counterfactual methodology.**

PT-A2B completes the requested methodological diagnosis and controlled target comparison. It does not justify decision integration: invariant-preserving transformations cannot repair the materially selected missing set, and multiple-control averaging remains a choice of research target with bounded approximation error.

A next methodology phase should define a defensible target on currently excluded sources (or explicitly restrict the estimand), justify the control population rather than choose it for coverage, and evaluate more visible hands and control-cap convergence. No bid-point mapping, production integration or PT-A3 work was undertaken. PT-A2B remains uncommitted; nothing was pushed.
