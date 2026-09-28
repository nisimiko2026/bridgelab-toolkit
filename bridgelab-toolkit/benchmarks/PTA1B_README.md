# PT-A1B: Exact Conditional Hidden-Hand Sampling

## A. PT-A1 checkpoint

Commit: e514de442af935e1dbd79922a50047aed2720ae4
Message: PT-A1: add hidden-hand probability model
Parent: 4303c5520dfbf4472729ddc076237267c197eb51

The staged set was verified to contain exactly these five files, and the
staged whitespace check passed before committing:

- benchmarks/PTA1_README.md
- benchmarks/pta1_probability_validation.py
- bridge/hidden_hand_probability.py
- output/pta1_probability/summary.json
- tests/test_bridge_pta1_hidden_hand_probability.py

No PT-A1B changes were included. No push occurred.

## B. Repository state

Working directory: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit
Git root: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree
Branch: codex/phase18b
HEAD remains e514de442af935e1dbd79922a50047aed2720ae4.

PT-A1B is uncommitted and unstaged. OneDrive was not accessed or modified.
At the PT-A1 checkpoint the tracked tree was clean and these six files remained
untracked; all remain outside the checkpoint:

- output/pt1_shortness/pt1_cases.jsonl.gz
- output/pt1a_solver_validation/pt1a_solver_cases.jsonl.gz
- output/pt1b_shortness_validation/pt1b_cases.jsonl.gz
- output/pt1b_shortness_validation/pt1b_exchange_sensitivity.jsonl.gz
- output/pta1_probability/historical.log
- output/pta1_probability/historical_exit_code.txt

The four research datasets were neither staged nor regenerated.

Final expanded short status (all ?? entries are untracked):

```text
 M bridge/hidden_hand_probability.py
 M tests/test_bridge_phase29l_opening_pass_source_policy_audit.py
?? benchmarks/PTA1B_README.md
?? benchmarks/pta1b_conditional_validation.py
?? bridge/conditional_hidden_hand.py
?? output/pt1_shortness/pt1_cases.jsonl.gz
?? output/pt1a_solver_validation/pt1a_solver_cases.jsonl.gz
?? output/pt1b_shortness_validation/pt1b_cases.jsonl.gz
?? output/pt1b_shortness_validation/pt1b_exchange_sensitivity.jsonl.gz
?? output/pta1_probability/historical.log
?? output/pta1_probability/historical_exit_code.txt
?? output/pta1b_conditional/historical.log
?? output/pta1b_conditional/historical_exit_code.txt
?? output/pta1b_conditional/historical_initial.log
?? output/pta1b_conditional/historical_initial_exit_code.txt
?? output/pta1b_conditional/summary.json
?? tests/test_bridge_pta1b_conditional_hidden_hand.py
```

The staging area is empty. Final runtime route count is 45.
Only this report was completed during finalization; implementation and tests
were not modified.

## C. PT-A1B files and API

Added implementation: bridge/conditional_hidden_hand.py
Added tests: tests/test_bridge_pta1b_conditional_hidden_hand.py
Added benchmark: benchmarks/pta1b_conditional_validation.py
Added report: benchmarks/PTA1B_README.md
Generated diagnostic summary: output/pta1b_conditional/summary.json
Generated validation logs: output/pta1b_conditional/historical.log and historical_exit_code.txt.
The first run is retained separately as historical_initial.log and historical_initial_exit_code.txt.

Modified bridge/hidden_hand_probability.py only to extract the common empirical
weighting/marginal summarizer. The PT-A1 shuffle/rejection generation law and
public API remain intact. Its original stress counts reproduce exactly.

Modified tests/test_bridge_phase29l_opening_pass_source_policy_audit.py to correct
a pre-existing regression guard that rejected any unrelated tracked work.
It now compares the complete tracked binary-capable diff before/after the audit,
rather than a path-only comparison plus an obsolete phase-specific allowlist.
This catches content mutations even when the affected file was already dirty.
The permanent invariant is that running this read-only audit leaves the tracked
working-tree diff against HEAD unchanged. The removed allowlist instead enforced
a temporary phase scope, unrelated to the audit's side effects. The replacement
is appropriate to keep permanently and does not weaken that read-only safeguard.
It does not claim to detect transient edits restored before the final snapshot,
untracked-file changes or index-only changes that leave the HEAD-to-working-tree
diff identical; the previous check did not detect those either.

Public additions:

- ConditionalSampler(state): prepare exact proposal weights once.
- sampler.sample(SamplingConfig(...)): reproducible ConditionalResult.
- sampler.count_matrix_masses(): exact integer proposal mass for each count matrix.
- sample_conditional_hidden_hands(state, config): convenience entry point.
- ConditionalResult.model: existing HiddenHandResult with samples, marginals,
  evidence, weights, ESS, statuses, rejection counts and original information state.
- ConditionalResult.diagnostics: typed ConditionalDiagnostics with status,
  matrix count, proposal allocation count, primary HCP seat, residual HCP seats
  and explanation.
- ConditionalStatus: READY, CONTRADICTORY, INFEASIBLE.

READY means the proposal space has positive mass. It does not prove that all
residual HCP restrictions are jointly feasible.

## D. Algorithm

The target is uniform over physical allocations of the 39 unseen cards to the
three labeled hidden seats satisfying every PT-A0 hard constraint, before any
explicit likelihood weighting. Only the perspective hand and the general
information state enter the sampler.

Setup chooses a primary hidden seat by the narrowest hard HCP range, with a
deterministic partner/LHO/RHO tie break. Per suit, at most 16 available honor
subsets are enumerated. Each receives the exact number of spot-card subsets.
A four-suit suffix dynamic program counts primary hands by shape and HCP total.

Setup then enumerates feasible seat-by-suit count matrices, using two small
shape domains and deriving the third row from outstanding suit capacities.
Matrices receive exact integer weights. Sampling uses integer random tickets,
uniform spot subsets and uniform allocations of remaining suit cards.
Additional HCP restrictions at other seats use explicit whole-proposal rejection.

## E. Target-distribution argument

For feasible matrix M, let p be the primary seat and q either other seat.
Let n_s be the unseen count of suit s. Define

    A(M_p) = number of primary holdings with shape M_p and permitted primary HCP
    B(M) = product_s C(n_s - M_ps, M_qs)
    W(M) = A(M_p) * B(M)
    Z = sum_M W(M)

The matrix is drawn with probability W(M)/Z. The honor/spot suffix DP draws each
permitted primary holding with probability 1/A(M_p). Each remaining allocation
has probability 1/B(M). Therefore every physical proposal has probability

    W(M)/Z * 1/A(M_p) * 1/B(M) = 1/Z.

Rejecting a whole proposal for secondary HCP constraints and drawing a new
matrix conditions this uniform law onto the full hard-evidence target. Keeping
the matrix fixed while retrying secondary HCP would bias it; this implementation
does not do that. No importance correction is needed for accepted baseline draws.

Z is the proposal allocation count. It equals the full target count only when
there are no residual HCP restrictions. With residual HCP restrictions it is
not advertised as the full target count. Integer cumulative selection avoids
floating-point rounding of combinatorial probabilities.

## F. Suit-count and shape conditioning

Every generated matrix has three rows summing to 13, columns summing to unseen
suit capacities, each hard suit interval respected, and allowed shape alternatives
respected seat by seat. Invalid matrices never enter the sampling table.

For the unconstrained benchmark hand, all 88,695 matrices have individually
checked multinomial weights, whose sum is exactly

    C(39,13) * C(26,13) = 84,478,098,072,866,400.

For partner shapes (4,4,4,1) or (5,3,3,2), exact marginal matrix masses also match
independent products of suit combinations, multiplied by C(26,13).

## G. HCP conditioning and infeasibility

The primary HCP band is conditioned exactly within the combinatorial weights.
An exact HCP count of 11 at any of the three hidden seats is tested without
rejection. Combined partner length/HCP constraints also incur no rejection
when there are no restrictive secondary HCP bands.

Secondary HCP checks remain rejection based and are counted by labeled seat,
for example W:residual_hcp. There is no full three-seat joint-HCP DP.
Budget exhaustion returns BUDGET_EXHAUSTED, never a claim of impossibility.

Existing PT-A0 contradictions are returned before RNG construction. Zero
shape/primary-HCP combinatorial mass returns INFEASIBLE before sampling, with
hard-evidence, own-hand and derived-arithmetic provenance. For example a hidden
13-diamond hand cannot have 20 HCP. Unresolved soft evidence is retained but
is not blamed as a cause of hard infeasibility. Some contradictions involving
both secondary HCP bands may still require exhausting the proposal budget.

## H. Reference and statistical comparisons

The benchmark retains the independent PT-A1 rejection generator. For every
scenario it compares all four suit marginals, HCP and shape for N, W and E.
Numeric bins are all stored. Shape metrics cover the full union of bins; five
representative shape events per seat are stored individually to limit output.

The JSON records exact probability where available, reference estimate,
conditional estimate, difference, sample sizes, ESS, exact-bin standard error
sqrt(p(1-p)/N), and pooled two-sample standard error of the difference.
Unavailable exact values are null, never fabricated. Exact oracles cover the
baseline all-seat suit/HCP marginals, partner HCP/spade conditioning, defender
spade mixtures, shape alternatives and the vacant-place comparison.

The following examples have conditional N=ESS=4000. Reference ESS equals its
accepted count. SE is against the exact event probability unless stated otherwise.

| Scenario / event | Exact | Conditional | Reference | Difference from exact | SE |
|---|---:|---:|---:|---:|---:|
| unconstrained: N hcp=11 | 0.094389 | 0.086500 | 0.093750 | -0.007889 | 0.004623 |
| combined: N spades=4 | 0.761581 | 0.766250 | 0.765250 | +0.004669 | 0.006737 |
| combined: N hcp=11 | 0.337530 | 0.333250 | 0.336250 | -0.004280 | 0.007477 |
| defender_diamonds_5_3: W spades=2 | 0.411765 | 0.422000 | 0.415419 | +0.010235 | 0.007782 |
| shape_alternatives: N shape=[4, 4, 4, 1] | 0.483871 | 0.491000 | 0.484297 | +0.007129 | 0.007902 |

For the tighter three-seat case, partner HCP=11 is 0.381000 conditional versus
0.380128 reference; difference +0.000872, two-sample SE 0.016550,
conditional ESS 4000 and reference ESS 1097. A full exact oracle is not claimed
for that case.

These are supporting diagnostics, not a proof based on an arbitrary tolerance.
Rare-bin normal approximations can be poor: conditional on partner HCP=11,
partner spades=8 has exact probability 0.00000634435417 (expected count 0.02538).
One occurrence in 4000 gives a normal z of 6.118, but the exact probability of
at least one occurrence is about 2.506%. This is retained in the summary.
Multiple-bin extrema are descriptive and are not a global hypothesis test.
The correctness basis is the integer-mass argument plus independent counting
oracles, supported by seeded sampling checks.

## I. Exact combinatorial checks

Tests enumerate a tiny complete conditional space independently: perspective
holds all spades, partner all hearts, W has 12 diamonds/1 club, E 1 diamond/12 clubs.
There are 13*13=169 physical allocations. Requiring W HCP=10 leaves 9*9+4=85.
Exact primary-HCP setup counts 85. With a primary-seat tie selecting partner,
the proposal count is 169 and explicit secondary rejection yields the same
85-allocation target. The event E holds the diamond ace has exact probability
1/85. Fixed-count allocation without the HCP restriction gives each diamond
rank probability 1/13. Tests check integer counts and empirical errors using
sample-size-dependent standard errors.

## J. Stress results

Every conditional scenario requested and obtained 4000 accepted draws, ESS=4000.
All reference runs requested 4000; budget exhaustion is shown by smaller totals.

| Scenario | Conditional accepted/proposals | Reference accepted/proposals | Residual rejection |
|---|---:|---:|---:|
| unconstrained | 4000/4000 | 4000/4000 | 0.00% |
| partner_spades_ge3 | 4000/4000 | 4000/7459 | 0.00% |
| partner_spades_eq4 | 4000/4000 | 4000/23077 | 0.00% |
| partner_hcp_10_12 | 4000/4000 | 4000/14340 | 0.00% |
| partner_hcp_eq11 | 4000/4000 | 4000/42936 | 0.00% |
| combined | 4000/4000 | 4000/65101 | 0.00% |
| defender_diamonds_5_3 | 4000/4000 | 2270/200000 | 0.00% |
| shape_alternatives | 4000/4000 | 2197/200000 | 0.00% |
| tight_three_seat_evidence | 4000/9231 | 1097/200000 | 56.67% |
| rare_partner_all_remaining_spades | 4000/4000 | 0/20000 | 0.00% |

The tighter synthetic auction-information state is partner S=4..5/HCP=10..12,
LHO D=5..6/HCP=9..13, RHO C=4..6/HCP=6..10. These are general constraints;
no bid or bidding-system interpretation was implemented.

The old combined 4000/65101 and defender 2270/200000 reference counts reproduce
exactly. The latter remains BUDGET_EXHAUSTED in the reference but completes
with zero rejection conditionally. The tighter conditional run has 5231
residual HCP rejections; that cost is not hidden.

## K. Vacant-place consistency

All four perspective orientations preserve partner/LHO/RHO as distinct seats.
For own five spades and partner four spades, the unconditional 2-2 defender
split reference is 0.4069565217. Conditioning LHO diamonds=5 and RHO diamonds=3
changes that exact probability to 0.4117647059. The corresponding conditional
estimate is 0.422000 with SE 0.007782.

Tests also vary partnership side-suit shortness with the same known trump total;
this alone does not alter the unconditional defender split reference. HCP or
defender-specific evidence may legitimately condition those probabilities.
No shortness or Playing-Trick value is assigned.

## L. Reproducibility, provenance and isolation

The same immutable state/configuration/seed produces equal complete results,
including when setup is reused. Timing and memory fields are deliberately kept
outside the reproducible model. Bitstream compatibility across Python versions
is not promised.

Tests build different complete source deals with identical perspective cards.
Only the visible hand enters the state, and conditional results are identical.
The public API rejects a Deal argument. Generated hidden hands are hypotheses,
not source information.

Original state, constraints, certainty, provenance and explicit likelihood rules
remain available in HiddenHandResult. Empirical marginals remain PROBABILISTIC,
even when frequency is one. Unknown likelihoods retain INSUFFICIENT_WEIGHTING.
Explicit zero weights retain legal baseline samples and never become hard
constraints. No empirical bidding-likelihood calibration is supplied.

## M. Performance

One local run, Python 3.14; these are measurements, not timing assertions.
Sampling time includes constructing samples and summary marginals. Setup can
be amortized by reusing ConditionalSampler. Reference time includes its setup.

| Scenario | Setup s | Sampling+summary s | Conditional cold total s | Reference total s | Conditional proposals/s | Conditional accepted/s | Reference accepted/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| unconstrained | 0.2162 | 0.5382 | 0.7544 | 0.5239 | 7433 | 7433 | 7636 |
| partner_spades_ge3 | 0.1110 | 0.5417 | 0.6527 | 0.5722 | 7385 | 7385 | 6991 |
| partner_spades_eq4 | 0.0275 | 0.5345 | 0.5620 | 0.7741 | 7484 | 7484 | 5167 |
| partner_hcp_10_12 | 0.2093 | 0.5360 | 0.7453 | 0.6461 | 7463 | 7463 | 6191 |
| partner_hcp_eq11 | 0.2179 | 0.5354 | 0.7533 | 0.9916 | 7471 | 7471 | 4034 |
| combined | 0.0827 | 0.5237 | 0.6063 | 1.2826 | 7638 | 7638 | 3119 |
| defender_diamonds_5_3 | 0.0063 | 0.5296 | 0.5359 | 3.3106 | 7553 | 7553 | 686 |
| shape_alternatives | 0.0055 | 0.5298 | 0.5353 | 3.0048 | 7550 | 7550 | 731 |
| tight_three_seat_evidence | 0.0109 | 0.7005 | 0.7114 | 2.7203 | 13178 | 5710 | 403 |
| rare_partner_all_remaining_spades | 0.0100 | 0.5068 | 0.5168 | 0.2643 | 7893 | 7893 | 0 |

Unconstrained and some weakly constrained cold runs are slower than the reference
because setup must enumerate matrices. Narrow constraints give the intended
efficiency improvement; universal speedup is not claimed.

A separate tracemalloc pass for unconstrained setup measured 19,986,168 retained
Python bytes and 21,448,792 peak bytes (about 19.06/20.46 MiB). Tracing was excluded
from timing measurements. These are Python allocation counts, not process RSS.
Returned samples consume additional memory linear in accepted sample count.
The JSON summary is about 1.11 MiB and contains no generated full-deal dataset.

## N. Validation

| Selection | Result |
|---|---:|
| PT-A1B focused, final diagnostic revision | 31 passed |
| PT-A1 | 43 passed |
| PT-A0 | 47 passed |
| Evaluation/probability/vacant-place selection | 106 passed |
| Auction/context/profile selection | 429 passed |
| PT-1/PT-1A/PT-1B | 38 passed, 9 skipped |
| Corrected historical audit module | 9 passed |
| Historical regression | 2673 passed, 9 skipped |
| Historical subtests | 143 passed |
| Historical exit code | 0 |

The initial historical run was 1 failed, 2672 passed, 9 skipped, 143 subtests
passed in 1064.33s; exit code 1. Its only failure was the obsolete phase-specific
tracked-file allowlist described above. The audit itself preserved the tracked
state. After strengthening that guard, its full module passed 9 tests, and the
historical suite was rerun in full. Both historical logs are retained.

Final historical result: 2673 passed, 9 skipped, 143 subtests passed in 907.49s (0:15:07); exit code 0.
No tests were rerun during finalization. A previously completed controlled
guard check also verified that unchanged existing edits are accepted and
same-path tracked-content mutations are rejected.

The first combined phase run passed 120 tests (30+43+47). After correcting only
the new sampler's infeasibility provenance, the final 31 PT-A1B tests passed.
Other already completed focused selections were not unnecessarily repeated.
Selections overlap; their counts must not be added as disjoint coverage.
The nine solver skips are expected because endplay/endplay.dds is unavailable.
No large DDS dataset was rerun.

Commands (use the project Python interpreter and PYTHONDONTWRITEBYTECODE=1):

    python -m pytest tests/test_bridge_pta1b_conditional_hidden_hand.py tests/test_bridge_pta1_hidden_hand_probability.py tests/test_bridge_pta0_auction_information.py -q -p no:cacheprovider
    python -m pytest tests/test_bridge_pta1b_conditional_hidden_hand.py -q -p no:cacheprovider
    python -m benchmarks.pta1b_conditional_validation
    python -m pytest tests/test_bridge_pt1_playing_trick_calibration.py tests/test_bridge_pt1a_solver.py tests/test_bridge_pt1b_shortness.py -q -rs -p no:cacheprovider
    python -m pytest -q -p no:cacheprovider --ignore=tests/test_bridge_pta0_auction_information.py --ignore=tests/test_bridge_pta1_hidden_hand_probability.py --ignore=tests/test_bridge_pta1b_conditional_hidden_hand.py

Evaluation/probability selection: tests/test_bridge*.py matching evaluation|probability,
excluding pta1. Auction/context/profile selection: tests/test_bridge*.py matching
auction|bidding_rules|profile|partnership|treatment_binding|base_system|two_over_one_opening.
Historical stdout/stderr and the actual exit code are saved alongside the summary.
Five changed/new Python files also passed syntax compilation without writing pyc files.

## O. Production invariant

production_changed = False
routes before = 45
routes after = 45

Runtime create_standard_sayc_router().routes was checked. No production bidding
route, registration, profile interpretation or integration changed. Tracked changes are the shared research probability-result summarizer and
the historical test's repository-state guard.
There is no DDS dependency or call, no bidding recommendation, and no
ERV/NPT/SRV/CRV/RCC/OR/APT, distribution-point or singleton-value calculation.
No PT-A2 work was started. No push occurred.

## P. Remaining limitations

Exact direct HCP conditioning covers one chosen seat. Other HCP bands use
whole-proposal rejection, which can still be expensive for extreme joint evidence.
Setup does not prove every residual-HCP infeasibility. Matrix memory/setup cost
is measurable, and weak constraints may favor the original reference sampler.
The public proposal allocation count must not be read as full-target cardinality
when residual bands exist.

Marginals are finite-sample estimates. Rare events need an adequate sample budget;
empirical zero is not impossibility. Unweighted binomial SEs in this benchmark
do not automatically apply to self-normalized weighted estimates. Soft likelihoods
need external justification, calibration and care with correlated evidence.
The hard-conditioned baseline must not be advertised as an all-evidence posterior
when unresolved soft evidence remains.

## Q. Recommendation

READY FOR PT-A2 using the validated hard-conditioned baseline. Exact
combinatorial construction preserves the target law, the original combined
and defender stress cases complete, and focused plus historical regression
pass. PT-A2 has not been started.

This does not validate empirical bidding likelihoods. PT-A1C calibration is
needed before treating uncalibrated soft evidence as a trustworthy all-evidence
posterior; it is not a prerequisite for explicitly hard-evidence-only work.
