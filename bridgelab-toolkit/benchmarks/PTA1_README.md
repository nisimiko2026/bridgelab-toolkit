# PT-A1 ג€” Hidden-Hand Probability Model

## A. Repository state

Working directory: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit.
Repository root: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree.
Branch: codex/phase18b. Baseline HEAD: 4303c5520dfbf4472729ddc076237267c197eb51.
Root, branch and HEAD were verified before changes. Only the four existing compressed
PT research datasets were untracked at the start; they were not read, modified or staged.
No OneDrive work, DDS calls, large research reruns, commits, pushes or PT-A2 work.

## B. Existing components reused

- Canonical full_deck from bridge.deals, plus existing Hand/Card/Seat/Suit/Rank models.
- Existing Hand.from_cards, high_card_points and SUIT_ORDER.
- PT-A0 AuctionInformationState, hard range/shape projections, contradictions and provenance.
- Existing exact-rational ProbabilityValue for normalized empirical weights and marginals.
- Existing VacantPlacesQuestion and oriented_trump_break for defender-oriented exact references.

Inspected generate_deal/generate_deals, playing_trick_calibration generation, simulation
statistics, probability engine and vacant-place utilities before implementation.
generate_deal randomizes all 52 cards; PT-A1 must fix the visible hand, so it reuses its
canonical deck and uniform-shuffle approach on only the remaining 39 cards.
The PT-1 conditioned generator fixes research-specific partnership structures and would
introduce unwanted prior assumptions. ProbabilityContext is designed around declarer-play
visible/played-card input. Neither is a substitute for PT-A0-conditioned hidden allocation.
No existing generator, PT-A0 semantics or probability registry was modified.

## C. Files added

- bridge/hidden_hand_probability.py
- tests/test_bridge_pta1_hidden_hand_probability.py
- benchmarks/pta1_probability_validation.py
- benchmarks/PTA1_README.md
- output/pta1_probability/summary.json
- output/pta1_probability/historical.log
- output/pta1_probability/historical_exit_code.txt

No tracked baseline file is modified.

## D. Public API

Import directly from bridge.hidden_hand_probability.

sample_hidden_hands(state, config=SamplingConfig()) returns HiddenHandResult.
The exact viewpoint hand comes exclusively from the immutable state; there is no second,
potentially inconsistent hand argument and no source Deal input.

SamplingConfig: requested, max_proposals, seed, likelihoods.
LikelihoodRule: EvidenceKey(update_index, Feature), immutable outcome/factor pairs, explicit
default factor and typed provenance. Factors are ProbabilityValue values in [0,1].

HiddenHandResult contains:
- original information_state, perspective, configuration and versioned algorithm identity;
- sampling_status and weighting_status independently;
- proposal count, accepted/requested counts, first-failure rejection counts and rejection rate;
- generated HiddenSample holdings, normalized weights and exact rational effective sample size;
- HCP, suit-length and complete-shape marginals for each hidden seat;
- original updates, soft evidence, unresolved soft keys and contradiction sources.

marginal(seat, feature) selects a marginal. Timings are deliberately external to immutable
results so identical input/seed/configuration gives identical complete results.
The benchmark records runtime, proposals/sec and accepted samples/sec separately.

vacant_place_reference(state, trump, outstanding, defender_side_suit=None) delegates to
the existing oriented_trump_break utility for its explicitly limited conditional experiment.

## E. Legal-deal generation

Canonical unseen cards are shuffled using a local random.Random(seed), then dealt in three
13-card blocks to partner, LHO and RHO. Every proposal partitions the unseen deck exactly
once. Each allocation is equally likely: each physical partition has the same (13!)^3
permutations among 39! shuffles. There is no full-space enumeration or sampling without
replacement across proposals. Repeated sampled allocations are valid IID observations.

## F. Hard conditioning

Every proposal is checked against each seat's PT-A0 hard HCP range, suit ranges and allowed
shape set. The physical partition enforces global suit capacity automatically. Accepted
samples therefore follow the uniform prior conditional on all hard evidence.

A contradictory PT-A0 state returns CONTRADICTORY and zero proposals, no samples or
marginals, and the original conflicts. A proposal budget shortfall returns BUDGET_EXHAUSTED
with any accepted samples and full accounting. It does not relax constraints or claim that
zero acceptance proves impossibility. Card-rank/HCP combinations not ruled out by PT-A0
arithmetic can still be unrealizable; bounded rejection remains safe in that case.

Rejection categories record the first failing seat/feature in deterministic order, not all
simultaneous failures. Accepted plus rejected always equals proposals.

## G. Soft evidence

INFERRED and PROBABILISTIC evidence never filters legal proposals. Supplied PT-A0 marginal
beliefs are not automatically interpreted as likelihoods: multiplying by a desired marginal
would generally count the prior twice.

No numeric rule: preserve evidence and return INSUFFICIENT_WEIGHTING. Equal-weight
marginals then describe the hard-conditioned prior, not an all-evidence posterior.
Partial rules: apply those explicit factors and retain unresolved soft keys/status.
Full rules: multiply configured likelihoods and normalize; return WEIGHTED.
All weights zero: return ZERO_TOTAL_WEIGHT with no normalized weights or marginals.

Multiple rules explicitly assert a product likelihood model; conditional independence and
factor calibration are caller responsibilities. PT-A1 invents no coefficient. A zero-weight
sample remains in the legal sample set. Probability-one soft assertions remain soft even
when a configured likelihood concentrates all weight. Rational ProbabilityValue represents
empirical mass exactly, not epistemically exact knowledge of the underlying distribution.
Every generated Marginal also carries explicit PROBABILISTIC certainty, including probability-one
empirical outcomes; any underlying hard guarantee remains separately available in PT-A0.

ESS = 1 / sum(normalized_weight^2). Uniform samples have ESS=N. No probability generation,
normalization or provenance mutation occurs inside PT-A0.

## H. Baseline prior

Uniform random physical allocations of all unseen cards. No balanced-shape, even-split,
honor-concentration, shortness-usefulness or bidding-system prior is present. Conditioning
comes only from PT-A0 hard constraints and explicitly configured soft likelihood factors.

## I. Hidden-information isolation

Tests build two valid complete source deals with identical viewpoint hand but different
cards at all three hidden seats. With identical auction/updates and seed/configuration, the
entire PT-A1 results compare equal. Source deals exist only in the test. The core accepts
only AuctionInformationState and SamplingConfig and imports no Deal or solver.
Upstream interpreters remain responsible for supplying legitimate public evidence.

## J. Reproducibility

All randomness comes from a local seeded RNG; deck and seat order are canonical.
Exact repeated-result and replay tests pass. Different seeds produce different samples.
Two independently seeded baseline runs are checked against the same exact reference.
Reproducibility is scoped to the documented algorithm and Python implementation; timings
are not part of result equality.

## K. Exact versus sampled validation

The benchmark counts 13-card subsets of the 39 unseen cards by (spades,HCP) using integer
dynamic programming, without enumerating full deals. Its total equals C(39,13). Focused
tests check that the suit marginal equals the hypergeometric formula and mean HCP equals
one third of unseen HCP. Hard-condition probabilities are computed by exact restriction
and renormalization of this joint distribution.

Each benchmark marginal bin records expected rational/decimal probability, observed
probability, absolute error, N, theoretical binomial standard error sqrt(p(1-p)/N), and
standardized error. Tests use a prespecified six-standard-error stochastic guard rather
than an arbitrary fixed tolerance. This is not a blanket calibration claim, especially
for rare bins, weighted posteriors or untested correlated constraints.

Representative rows (all bins are available in summary.json):

| Scenario | Event | Expected | Observed | Absolute error | Standard error | N |
|---|---|---:|---:|---:|---:|---:|
| unconstrained | spades=4 | 0.173742 | 0.172000 | 0.001742 | 0.005991 | 4000 |
| unconstrained_second_seed | spades=4 | 0.173742 | 0.179000 | 0.005258 | 0.005991 | 4000 |
| partner_spades_ge3 | spades=4 | 0.319539 | 0.310500 | 0.009039 | 0.007373 | 4000 |
| partner_spades_ge4 | spades=4 | 0.730187 | 0.739000 | 0.008813 | 0.007018 | 4000 |
| partner_spades_eq4 | spades=4 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 4000 |
| partner_hcp_10_12 | spades=4 | 0.161732 | 0.157250 | 0.004482 | 0.005822 | 4000 |
| partner_hcp_eq11 | spades=4 | 0.161710 | 0.159750 | 0.001960 | 0.005822 | 4000 |
| combined | spades=4 | 0.761581 | 0.765250 | 0.003669 | 0.006737 | 4000 |
| defender_baseline | LHO spades=2 | 0.406957 | 0.413250 | 0.006293 | 0.007768 | 4000 |
| defender_diamonds_5_3 | LHO spades=2 | 0.411765 | 0.415419 | 0.003654 | 0.010330 | 2270 |

The largest absolute standardized marginal error in the completed benchmark was about
2.93. Bins within a run are dependent and multiple bins/seeds were inspected; this statistic
is descriptive, not proof of calibrated tails or a formal global goodness-of-fit result.
Weighted-factor algebra and ESS are tested, but realistic external likelihood calibration
is not claimed.

## L. Vacant-place integration

Unconditional reference uses only defender orientation and the explicitly supplied
outstanding trump total. Partnership shortness does not alter it. Tests vary own and
partner shortness while preserving that total and obtain identical exact references.

Conditional reference accepts only a specified side suit with fixed hard lengths at BOTH
defender seats. A ranged/inferred/probabilistic length is rejected rather than coerced to
an exact number. LHO and RHO remain distinct. With West diamonds=5, East diamonds=3 and
four outstanding spades, the reference uses 8 versus 10 available slots. The benchmark
compares accepted physical deals under exactly these constraints with that formula.

This reference is not the complete posterior for additional HCP/shape constraints. The
general sampler handles those jointly; no universal vacant-place shortcut is claimed.
Partnership information can change the distribution of total outstanding trumps; the
invariance statement is conditional on a fixed total, not about mixing different totals.

## M. Performance and rejection diagnostics

Measured in the existing Documents Python 3.14 environment; times are machine-dependent.
Rates use end-to-end wall time, including constraint preparation and marginal aggregation.

| Scenario | Accepted/requested | Proposals | Rejected | Proposals/sec | Accepted/sec |
|---|---:|---:|---:|---:|---:|
| unconstrained | 4000/4000 | 4000 | 0.00% | 8066 | 8066 |
| unconstrained_second_seed | 4000/4000 | 4000 | 0.00% | 7990 | 7990 |
| partner_spades_ge3 | 4000/4000 | 7459 | 46.37% | 13237 | 7099 |
| partner_spades_ge4 | 4000/4000 | 16817 | 76.21% | 25057 | 5960 |
| partner_spades_eq4 | 4000/4000 | 23077 | 82.67% | 17683 | 3065 |
| partner_hcp_10_12 | 4000/4000 | 14340 | 72.11% | 7085 | 1976 |
| partner_hcp_eq11 | 4000/4000 | 42936 | 90.68% | 13995 | 1304 |
| combined | 4000/4000 | 65101 | 93.86% | 16937 | 1041 |
| defender_baseline | 4000/4000 | 23499 | 82.98% | 10144 | 1727 |
| defender_diamonds_5_3 | 2270/4000 | 200000 | 98.87% | 18786 | 213 |
| rare_partner_all_remaining_spades | 0/4000 | 20000 | 100.00% | 24587 | 0 |

The defender-specific case stopped at 2,270/4,000 after 200,000 proposals. The rare but
feasible all-eight-remaining-spades case obtained zero acceptances in 20,000 proposals.
Both report BUDGET_EXHAUSTED. The rare event has exact acceptance probability
C(31,5)/C(39,13) = 0.00002091875, or only 0.418 expected acceptances in 20,000
proposals; its observed zero is unsurprising and does not establish impossibility.
These results expose the rejection sampler's limitations.
No hidden optimization changes the prior and no failed proposal is counted as an accepted
sample. Partial output remains visibly partial.

## N. Exact test counts

| Group | Passed | Skipped | Failed |
|---|---:|---:|---:|
| Final PT-A1 focused | 43 | 0 | 0 |
| PT-A0 focused | 47 | 0 | 0 |
| Evaluation/probability | 106 | 0 | 0 |
| Auction/context/profile selection | 429 | 0 | 0 |
| PT-1/PT-1A/PT-1B | 38 | 9 | 0 |
| Historical (excluding separately validated PT-A0/PT-A1) | 2673 | 9 | 0 |

Nine endplay-dependent tests skip in the project Python 3.14 environment. No DDS was called.
The auction selection includes PT-A0, so these groups overlap; counts are not additive.
Historical regression also passed 143 subtests, with exit code 0 in 918.88 seconds
(15:18). Its complete output and exit code are saved in output/pta1_probability/.

Commands, from the mandatory work directory with PYTHONDONTWRITEBYTECODE=1:

    python -m pytest tests/test_bridge_pta1_hidden_hand_probability.py -q -p no:cacheprovider
    python -m pytest tests/test_bridge_pta0_auction_information.py -q -p no:cacheprovider
    python -m pytest tests/test_bridge_pt1_playing_trick_calibration.py tests/test_bridge_pt1a_solver.py tests/test_bridge_pt1b_shortness.py -q -rs -p no:cacheprovider
    python -m benchmarks.pta1_probability_validation
    python -m pytest -q -p no:cacheprovider --ignore=tests/test_bridge_pta0_auction_information.py --ignore=tests/test_bridge_pta1_hidden_hand_probability.py

Evaluation/probability selection: tests/test_bridge*.py matching evaluation|probability,
excluding pta1. Auction/context/profile selection: tests/test_bridge*.py matching
auction|bidding_rules|profile|partnership|treatment_binding|base_system|two_over_one_opening.

## O. Production

production_changed = False. routes before = 45. routes after = 45.
No new registration, bidding recommendation or production integration.
Final route count, unchanged baseline HEAD, and empty tracked/staged diffs were verified
at completion. No commit, push or PT-A2 work occurred.

## P. Limitations

Rejection sampling can be inefficient for narrow joint constraints. There is no exhaustive
satisfiability solver, probability of every possible full hidden deal, adaptive proposal,
MCMC mixing claim or rare-event accuracy guarantee. Empirical zero frequency does not prove
impossibility. Unweighted standard errors do not automatically apply to weighted ratios.
Explicit product likelihood factors need external justification and calibration; correlated
soft evidence cannot safely be multiplied without that assumption. No concealed coefficient
or bidding interpretation is supplied. No ERV/NPT/SRV/CRV/RCC/OR/APT, distribution points,
shortness bonus, bidding recommendation or DDS call is implemented.

## Q. Recommendation

An intermediate PT-A1B calibration phase is required before treating constrained or weighted
expectations as broadly trustworthy for PT-A2. The baseline architecture is correct and
transparent, but narrow defender evidence already exhausts the proposal budget and realistic
soft likelihoods have not been calibrated. PT-A1B should establish acceptance/ESS requirements,
evaluate a correctness-preserving constrained proposal strategy and validate explicit weighting
on representative constraints. PT-A2 and all playing-value calculations remain unstarted.
