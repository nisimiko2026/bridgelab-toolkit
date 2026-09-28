# PT-A2 ג€” Expected Ruffing Value research oracle: final Aג€“R report

Recommendation: **PT-A2B METHODOLOGICAL CALIBRATION REQUIRED**.

Completed DDS measurements are preserved. Finalization recovered the successful historical result, added summary-only sensitivity/calibration metadata, and wrote this report. No research implementation changed during finalization; no DDS cohort or completed test suite was rerun.

## A. Repository state

Mandatory working directory: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit.
Git root: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree.
Branch: codex/phase18b. HEAD: 3069453f6e4555f3872ff3fbc75cb28e337140c4.
The index is empty. Nothing staged, committed or pushed. OneDrive was not touched.
The four pre-existing PT research archives and earlier historical logs remain untouched.

## B. PT-1B components reused

Reused physical CardExchange records, inverse replay, preservation checks, SelectedControl, singleton candidate enumeration and the TrickSolver/endplay adapter. The only tracked modification is bridge/playing_trick_shortness_pairs.py: extract shortness_step_candidates to allow the first void exchange, retaining the original singleton_candidates admissibility and API. A clockwise seat rotation allows all four perspectives to reuse the N/S machinery; cards and evidence return to their physical seats.

## C. Files and public API

New source/report files:

- bridge/expected_ruffing_research.py
- tests/test_bridge_pta2_expected_ruffing.py
- benchmarks/pta2_erv_validation.py
- benchmarks/PTA2_README.md

Modified tracked file: bridge/playing_trick_shortness_pairs.py.

New measurement artifacts:

- output/pta2_erv/pilot/summary.json
- output/pta2_erv/pilot/hypotheses.jsonl.gz
- output/pta2_erv/main/summary.json
- output/pta2_erv/main/hypotheses.jsonl.gz
- output/pta2_erv/main/leakage.json

Execution records to leave untracked:

- output/pta2_erv/historical.log
- output/pta2_erv/historical_exit_code.txt
- output/pta2_erv/main_run.log
- output/pta2_erv/main_exit_code.txt

The local .pta2_env/ Python 3.12.13/endplay 0.5.12 environment is ignored and must not be committed. It includes pyvenv.cfg, Scripts/, Lib/, installed packages and its local ignore file. No environment files belong in the deliverable.

Research API: estimate_erv(state, studied_suit, trump, solver, *, declarer=None, config=ERVConfig()) -> ERVResult.
Supporting API: ERVConfig, ResearchSolverSession, PairedEffect, PairStatus, ERVStatus, EffectDistribution, paired_controls, realized_shortness_effect, control_seed_for_deal, information_fingerprint, control_support_guaranteed and summarize_effects.
The partial-information API accepts an AuctionInformationState, never a complete source deal. realized_shortness_effect is a separate full-information scoring API. Benchmark finalize_reporting_metadata derives fields from saved summaries without solving.

## D. Exact realized-effect definition

For a complete hypothesis D and selected legal control C(D), delta = DDS(D, declarer, trump) - DDS(C(D), declarer, trump), in tricks, with optimal opening lead in both solves. Control selection uses a reproducible hash of the complete *sampled hypothesis* and base control seed. This stabilizes repeated hypotheses and single-deal collapse.

The reported evaluable-pair ERV estimates E[delta | hard evidence, legal doubleton control, successful solves]. It is a paired trick contrast, not a direct count of ruffs. No HCP conversion or fixed singleton/void value is defined.

## E. Counterfactual construction and limitations

A singleton needs one exchange; a void needs two ordered legal exchanges to reach a doubleton. Low spots (2ג€“10) move from partner's studied suit to the viewpoint hand; compensating low spots move back from a different nontrump side suit. The compensating holding and partner's studied holding remain at least doubletons.

All four hands remain legal. Every honor stays in its original hand; HCP, each seat's exact trump cards, defender hands, strain and declarer remain fixed. Exchanges are reversible and recorded. Side-suit lengths and spot locations change, so natural winners, promotions and entries may change alongside ruffing opportunities. Alternative ordered paths can reach the same final control; selection is uniform over legal paths, not unique terminal deals.

No legal path produces a typed NOT_EVALUABLE result with a reason. No fabricated fallback or zero is supplied. Controls are research interventions and need not satisfy all original auction constraints.

## F. PT-A1B integration

ConditionalSampler supplies legal hidden-card hypotheses and exact model weights. Its combinatorial count-matrix allocation and whole-proposal residual-HCP rejection remain unchanged; the PT-A1 rejection reference also remains available. Seeds distinguish predictions, holdouts and external sources.

Only EXACT/GUARANTEED information constrains this baseline. INFERRED/PROBABILISTIC evidence is retained with INSUFFICIENT_WEIGHTING; it is not silently calibrated or promoted. ERVConfig rejects explicit soft likelihoods in this phase. No system/profile interpretation is added.

## G. DDS boundary

Endplay is instantiated only by benchmark/validation code and injected through TrickSolver. The research oracle has no endplay import. Production router import inspection loads neither the oracle nor the DDS adapter. No production route or bidding rule uses ERV. No distribution points, fixed coefficients, bid recommendations, NPT/SRV/CRV/RCC/OR/APT calculation, or Nisimג€“Nily/SAYC/2-1/Precision interpretation was introduced.

## H. Output and three distinct limitations

ERVResult retains the information fingerprint, visible hand, evidence/provenance, fit, configuration, requested/sample/evaluable counts, control rejections, solver-failed hypotheses, actual DDS failure count, sampling/weighting statuses, ESS, coverage, distribution, full pair records and weights.

1. Hidden-hand sampling uncertainty: SD describes the sampled effect distribution; SE and approximate normal 95% CI describe Monte Carlo error for the evaluable-pair mean under the specified sampler and control policy.
2. Counterfactual-control ambiguity: alternative legal exchanges change the estimand. Report spreads and replacement shifts separately; they are not included in the Monte Carlo CI.
3. Incomplete evaluability: some hypotheses have no admissible control. Coverage is empirical sampled probability mass, not proof of support-wide evaluability. Missing hypotheses receive no value.

**Full hard-evidence ERV unavailable under incomplete counterfactual coverage.** This applies to all ten main states. Even 100% sampled coverage does not establish full-support coverage: full_hard_evidence_mean additionally requires a conservative support proof. COMPLETE refers to sampled processing, not automatically to identification over the entire support.

## I. Fit-information progression

Own singleton hand: AKQ42.9876.3.J76. Own void hand: AKQ42.98765.-.J76.
Viewpoint South, partner/declarer North, spades trump, diamonds studied. The successive synthetic general constraints are partner spades unknown, >=3, >=4, exactly 4, then exactly 4 plus West diamonds=5 and East diamonds=3. No calls are interpreted.

Each main state requested and sampled 500 hypotheses (sample ESS=500). DDS failures and solver-failed hypotheses were zero in every state. Missing counts below are control-construction failures. Evaluable ESS equals the evaluable count.

| State | Evaluable / 500 | Missing | Coverage | Pair mean | SD | SE | MC 95% CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| singleton_unknown_fit | 437 | 63 | 87.4% | 0.4851 | 0.7760 | 0.0372 | 0.4123 to 0.5580 |
| singleton_support_ge3 | 402 | 98 | 80.4% | 0.6294 | 0.7258 | 0.0362 | 0.5583 to 0.7004 |
| singleton_support_ge4 | 382 | 118 | 76.4% | 0.7775 | 0.7659 | 0.0392 | 0.7006 to 0.8544 |
| singleton_support_eq4 | 382 | 118 | 76.4% | 0.7801 | 0.7984 | 0.0409 | 0.6999 to 0.8603 |
| singleton_defender_diamonds_5_3 | 499 | 1 | 99.8% | 0.7996 | 0.8351 | 0.0374 | 0.7263 to 0.8729 |
| void_unknown_fit | 355 | 145 | 71.0% | 0.9042 | 1.0219 | 0.0543 | 0.7978 to 1.0107 |
| void_support_ge3 | 313 | 187 | 62.6% | 1.2077 | 0.9314 | 0.0527 | 1.1043 to 1.3110 |
| void_support_ge4 | 276 | 224 | 55.2% | 1.7681 | 1.0093 | 0.0609 | 1.6488 to 1.8874 |
| void_support_eq4 | 277 | 223 | 55.4% | 1.5848 | 0.9486 | 0.0571 | 1.4729 to 1.6968 |
| void_defender_diamonds_5_3 | 496 | 4 | 99.2% | 1.5343 | 0.9218 | 0.0414 | 1.4531 to 1.6155 |

Across the ten states: 5,000 requested and sampled, 3,819 evaluable, 1,181 control failures, zero DDS failures; aggregate coverage 76.38%. Void means are not monotonic as information narrows. Comparisons reflect both changed hard-conditioned distributions and changed evaluable subsets; they do not establish a causal fit increment.

## J. Distribution of outcomes

Probabilities below condition on evaluable pairs. Full discrete histograms and variance are retained in each summary. Quantiles are 5%, 25%, 50%, 75%, 95%.

| State | P(positive) | P(zero) | P(negative) | Quantiles |
| --- | --- | --- | --- | --- |
| singleton_unknown_fit | 0.4691 | 0.4622 | 0.0686 | -1, 0, 0, 1, 2 |
| singleton_support_ge3 | 0.5547 | 0.4129 | 0.0323 | 0, 0, 1, 1, 2 |
| singleton_support_ge4 | 0.6702 | 0.2801 | 0.0497 | 0, 0, 1, 1, 2 |
| singleton_support_eq4 | 0.6257 | 0.3403 | 0.0340 | 0, 0, 1, 1, 2 |
| singleton_defender_diamonds_5_3 | 0.6373 | 0.3106 | 0.0521 | -1, 0, 1, 1, 2 |
| void_unknown_fit | 0.6535 | 0.2845 | 0.0620 | -1, 0, 1, 1, 3 |
| void_support_ge3 | 0.8211 | 0.1438 | 0.0351 | 0, 1, 1, 2, 3 |
| void_support_ge4 | 0.8913 | 0.1051 | 0.0036 | 0, 1, 2, 2, 3 |
| void_support_eq4 | 0.8845 | 0.1119 | 0.0036 | 0, 1, 2, 2, 3 |
| void_defender_diamonds_5_3 | 0.8710 | 0.1230 | 0.0060 | 0, 1, 2, 2, 3 |

## K. Full-information collapse with real DDS

Both synthetic states have exactly one physical proposal allocation. General guaranteed shape/HCP constraints force the remaining cards; hidden hands are not supplied through an EXACT-hand back door. Eight hypotheses were requested, sampled and evaluable per case, all repeating the same source/control. The sufficient support check succeeds.

| Case | PT-A2 mean | Realized paired delta | Variance / SE | Identical control |
| --- | --- | --- | --- | --- |
| singleton | 1.0 | 1 | 0 / 0 | True |
| void | 2.0 | 2 | 0 / 0 | True |

These are deliberately degenerate 13-trump correctness cases. They validate collapse and the shared construction, not representative auction calibration. Singleton uses the original PT-1B one-step machinery; void uses the documented two-step extension.

## L. Partial-information calibration

The priors differ, so assess the cohorts separately. The summary retains legacy pooled descriptive fields for traceability; calibration_strata_by_cohort provides the appropriate separate analyses by prediction band, shortness, information state, realized fit/role, loser proxy, side-ace entry proxy and defender evidence. Latent-feature strata are exploratory, not additional information supplied to predictions.

| Cohort | Attempted | Valid | Predicted | Realized | Bias | RMSE | MAE | Approx bias 95% CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PT1B_conditioned_sources | 12 | 8 | 0.5705 | 0.7500 | -0.1795 | 0.9551 | 0.8308 | -0.8782, 0.5191 |
| independent_conditional_holdout | 240 | 180 | 1.0028 | 1.0000 | 0.0028 | 0.9242 | 0.7292 | -0.1354, 0.1410 |

Independent conditional holdouts use 24 fresh source hypotheses per state, with independent seeds; 60/240 lacked controls. This checks internal expectation consistency. PT-1B-conditioned sources use 12 newly generated cases with 64-hypothesis predictions; 4/12 lacked controls. Their selection prior differs from the hard-conditioned baseline and eight valid cases give low power.

Bias intervals add shared prediction Monte Carlo variance rather than dividing it by the number of holdouts sharing that prediction. They are descriptive normal approximations; selection, control ambiguity and unevaluable outcomes are not covered by them. No coefficients were fitted.

## M. Real-DDS leakage/isolation validation

The saved main/leakage.json was completed before interruption and recovered during finalization. Two different complete worlds have the same South hand, hard information state, seed 83000, 32 requested hypotheses, control seed 3202 and endplay/DDS 0.5.12 configuration. Both partial-information results are identical: 32 sampled, 27 evaluable, mean 1/3 trick. Only afterward were source worlds scored: realized targets 0 and -1 tricks.

The benchmark asserts equality of the complete deterministic results; solver timing/runtime counts are handled separately. The saved source IDs and configuration make this check reproducible. It used 112 DDS calls, zero failures, 4.57 seconds. No repeat was needed.

## N. Counterfactual sensitivity

Pilot: 4/10 changed (40%), mean observed spread 0.7 tricks, maximum 2; tested-subset mean shift +0.177778.
Main: 8/20 changed (40%), mean observed spread 0.7 tricks, maximum 3; tested-subset mean shift +0.125.

Main records below preserve original delta, all sampled alternative deltas (including the original path), observed spread and mean shift. At most eight sampled indices plus the original were checked; these spreads are lower bounds on full control ambiguity. The first two evaluable occurrences per state were selected, so this is a small bounded diagnostic, not a precise population sensitivity estimate.

| State / source index | Original | Recorded alternatives | Spread | Subset item shift |
| --- | --- | --- | --- | --- |
| singleton_unknown_fit / 1 | 0 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| singleton_unknown_fit / 2 | 0 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| singleton_support_ge3 / 3 | 0 | 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| singleton_support_ge3 / 4 | 0 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| singleton_support_ge4 / 5 | -1 | 1, 1, -1, 1, 1, -1, -1, -1 | 2 | +1.000000 |
| singleton_support_ge4 / 6 | 0 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| singleton_support_eq4 / 7 | 0 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| singleton_support_eq4 / 8 | 0 | 0, 0, 1, 1, 0, 1, 0, 1 | 1 | +0.500000 |
| singleton_defender_diamonds_5_3 / 9 | 1 | 1, 1, 1, 1, 1, 1, 1, 1 | 0 | +0.000000 |
| singleton_defender_diamonds_5_3 / 10 | 0 | 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| void_unknown_fit / 11 | 2 | 3, 2, 3, 3, 2, 2, 2, 3, 3 | 1 | +0.555556 |
| void_unknown_fit / 12 | 0 | 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| void_support_ge3 / 13 | 0 | 0, 0, 0, 0, 0, 0, 0, 0, 0 | 0 | +0.000000 |
| void_support_ge3 / 14 | -2 | -2, -2, -2, -2, -2, -2, -2, -2, -2 | 0 | +0.000000 |
| void_support_ge4 / 15 | 3 | 1, 3, 3, 3, 1, 1, 1, 3, 3 | 2 | -0.888889 |
| void_support_ge4 / 16 | 2 | 2, 2, 2, 1, 1, 2, 2, 2, 1 | 1 | -0.333333 |
| void_support_eq4 / 17 | -1 | 1, -1, -1, 1, 1, -1, -1, 1, 1 | 2 | +1.111111 |
| void_support_eq4 / 18 | 0 | 3, 0, 3, 3, 0, 0, 0, 3, 3 | 3 | +1.666667 |
| void_defender_diamonds_5_3 / 19 | 1 | 1, 1, 1, 1, 1, 1, 1, 1, 1 | 0 | +0.000000 |
| void_defender_diamonds_5_3 / 20 | 3 | 1, 1, 1, 3, 3, 3, 1, 1, 3 | 2 | -1.111111 |

Replacement calculation: replace each tested occurrence's selected delta with its recorded alternative-path mean, leaving every untested occurrence unchanged. For equal-weight valid samples, cohort shift = sum(tested item shifts) / evaluable count. It neither extrapolates the tested shifts nor estimates full control averaging.

| State | Tested subset shift | Cohort shift | Mean after partial replacement |
| --- | --- | --- | --- |
| singleton_unknown_fit | +0.000000 | +0.000000 | 0.485126 |
| singleton_support_ge3 | +0.000000 | +0.000000 | 0.629353 |
| singleton_support_ge4 | +0.500000 | +0.002618 | 0.780105 |
| singleton_support_eq4 | +0.250000 | +0.001309 | 0.781414 |
| singleton_defender_diamonds_5_3 | +0.000000 | +0.000000 | 0.799599 |
| void_unknown_fit | +0.277778 | +0.001565 | 0.905790 |
| void_support_ge3 | +0.000000 | +0.000000 | 1.207668 |
| void_support_ge4 | -0.611111 | -0.004428 | 1.763688 |
| void_support_eq4 | +1.388889 | +0.010028 | 1.594866 |
| void_defender_diamonds_5_3 | -0.555556 | -0.002240 | 1.532034 |

Pooling all 3,819 evaluable occurrences yields a +0.000654622 mean shift when replacing only the 20 tested controls. This small diluted shift does not negate the observed source-level ambiguity of up to three tricks. Pilot pooled replacement shift is +0.029143898 across 61 evaluable occurrences.

## O. Computational performance

| Run | DDS calls | Budget | Wall seconds | DDS seconds | Cache hits | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| pilot | 262 | 1000 | 9.76 | 3.67 | 128 | 0 |
| main | 9359 | 16000 | 449.70 | 165.47 | 223 | 0 |

Main exit code: 0. Pilot + main + leakage recorded 9,733 DDS calls. Preliminary smoke checks and solver unit tests are separate from that total. The main run stayed below its 16,000-call cap; no large historical PT-1/PT-1B DDS dataset was regenerated.

Finalization made zero DDS calls. Both hypotheses archives remained byte-for-byte unchanged while reporting metadata was added. Support metadata had already been finalized before the interruption. Recorded outcome/weight digests were rechecked:

- pilot: 11e3093ad08374284a6d0df171f99b146e5b4725df7d779f6e201fa0ccb4cddc
- main: d01c2ecf774a07c04dbab9c0b2cf5e205fdf5ad5fcddc26aaeb84e516acd45f7

## P. Exact validation counts

These are completed runs, not newly repeated totals; selections overlap and must not be added.

| Selection | Result |
| --- | --- |
| Final PT-A2 / Python 3.14 | 29 passed, 2 DDS-only skips |
| Final PT-A2 / Python 3.12 + endplay | 31 passed |
| Combined PT-A0/PT-A1/PT-A1B/PT-A2 | 145 passed, 2 DDS skips; before five final support-proof cases were added |
| PT-A0 / PT-A1 / PT-A1B within combined selection | 47 / 43 / 31 passed |
| Earlier real-DDS PT-A2 + PT-1A/PT-1B selection | 59 passed |
| Evaluation/probability/vacant-place selection | 106 passed |
| Auction/context/profile selection | 429 passed |
| PT-1 family / Python 3.14 | 38 passed, 9 expected solver skips |
| Historical regression | 2673 passed, 9 skipped, 143 subtests passed; exit 0; 1066.64 s (17:46) |

Historical totals were recovered from output/pta2_erv/historical.log plus historical_exit_code.txt. The historical selection excludes the four PT-A0/A1/A1B/A2 focused files. Expected solver skips reflect missing endplay in Python 3.14. The five added support-proof cases passed in both final focused runs; the older combined run is not represented as a rerun of the final 31-case file.

Finalization checks: Python AST syntax, JSON/archive integrity, unchanged effect/weight digests, count partition identities, absent full-support means under incomplete coverage, separate collapse equality, router count/import boundary and git whitespace checks. No new implementation change required test-suite or DDS repetition.

## Q. Production invariant

- production_changed = False
- routes before = 45
- routes after = 45

Production entry point, router and route-configuration sources match HEAD. The sole tracked source diff is the research shortness-pair refactor. The index remains empty. No production import of the research oracle or DDS adapter was acquired; no bidding rules use ERV.

## R. Recommendation

**PT-A2B METHODOLOGICAL CALIBRATION REQUIRED.**

The mechanism, physical controls, deterministic isolation and singleton/void collapse are validated. However, control construction leaves 23.62% of main hypotheses unevaluable, alternative controls materially change selected source effects, and external calibration is small and prior-dependent. Full hard-evidence ERV remains unidentified for all ten main states.

Before decision integration, calibrate the choice of control/estimand, investigate missing-control selection, expand diverse visible-hand and independently generated source cohorts, and evaluate coverage-aware reporting. Keep sampling uncertainty, control ambiguity and missing evaluability separate. Do not translate these results into bidding points or fixed coefficients.

No PT-A3 work, staging, commit or push was performed.
