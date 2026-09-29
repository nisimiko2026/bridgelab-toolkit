# PT-A2D — Mechanism-Based Shortness Attribution

**Recommendation: PT-A2E mechanism methodology required. No full-information target is adopted; no auction-time expectation is computed.**

Same-deal play diagnostics avoid defender-card substitution and collateral shape changes, but do not yet identify a general scalar shortness value. Actual ruffs, the value of keeping a ruff option, and changed scoring rules differ even in exact endgames. Full-deal searches remain unresolved within the bounded pilot.

This report was completed during finalization from the saved pilot, supplemental two-ruff results and completed validation logs. No tests, DDS benchmarks or result generation were repeated during finalization.

## A. PT-A2C checkpoint

Commit: `51393c3d8d0770be123d016af8edd4127d7aafaf`.
Message: `PT-A2C: compare alternative shortness counterfactual targets`.

That checkpoint contains five PT-A2C source/test/report files and eight small JSON artifacts. Environments, logs and large datasets were excluded. Nothing was pushed.

## B. Repository state and API

Working directory: `C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit`.
Git root: `C:/Users/nisim/Documents/BridgeLab-phase18b-worktree`.
Branch: `codex/phase18b`. Starting HEAD for finalization is the PT-A2C checkpoint above.

PT-A2D files selected for its own checkpoint:

- `bridge/shortness_mechanism.py`
- `tests/test_bridge_pta2d_mechanism.py`
- `benchmarks/pta2d_mechanism_validation.py`
- `benchmarks/PTA2D_DDS_CAPABILITIES.md`
- `benchmarks/PTA2D_README.md`
- `output/pta2d_mechanism/pilot.json`
- `output/pta2d_mechanism/two_ruff_validation.json`
- `output/pta2d_mechanism/test_selections.json`

Execution logs remain untracked. No production file was modified. Earlier datasets and environments are excluded. OneDrive was not touched.

Public research API:

- `PlayPosition.from_deal(deal, declarer, trump)` preserves every physical card and starts with declarer's left-hand opponent on lead. Balanced small endgames use existing Card, Seat and Suit types without weakening the exactly-13-card Hand abstraction.
- `MechanismOracle.analyze(position)` computes exact minimax trick potential and joint winning-ruff profiles over all locally optimal lines, or returns a typed budget result.
- `MechanismOracle.restricted(position, policy, unrestricted=...)` solves an explicitly changed action/reward game.
- `DDSOptimalMoves` exposes tied optimal moves; `bounded_studied_paths` retains conservative envelopes when exhaustive analysis cannot finish.

These are full-information research interfaces, not bidding-time estimators.

## C. DDS/play-path capabilities

The installed endplay 0.5.12 source was inspected and documented before implementation in `PTA2D_DDS_CAPABILITIES.md`.

BridgeLab's existing adapter returns trick totals through `analyse_start`. Endplay also exposes per-card continuation values and all tied optimal next cards through `solve_board` and `OptimalAll`, including expanded equivalent-rank cards. `OptimalOne` is one tied move, not a unique principal variation. `analyse_play` evaluates a supplied sequence rather than generating all complete optimal lines.

Repeated queries and physical transitions can traverse the optimal-action graph. These wrappers do not expose a persistent no-ruff restriction. Filtering a first move and accepting its ordinary DDS continuation would incorrectly allow later ruffs. Restricted games therefore use independent minimax. Ruff events come from card plays and trick winners, never from a DDS total alone.

Independent minimax and DDS agree on root values and tied first actions. Complete tied-path profiles were also cross-checked on the five smaller fixtures. The saved five-trick supplemental fixture checks the root value and all optimal first actions.

## D. Candidate targets

| Candidate | Measurement | Limitation |
| --- | --- | --- |
| Realized ruff count | Min/max own studied-suit winning ruffs over optimal lines | Event count is not extra tricks |
| Essential ruff value | Ordinary optimum minus strict restricted optimum, when feasible | Prohibition can leave no permitted play |
| Short-hand contribution | Joint own studied, own all-suit, partner all-suit ruff profiles and policy contrasts | Side-suit shortness is distinct from having fewer trumps; no additive causal value is claimed |
| Crossruff contribution | Joint presence of winning ruffs in both partnership hands | Reciprocal ruffs do not identify an isolated increment |
| Trump-control contribution | Option-sensitive examples distinguished from observed ruffs | No validated scalar for control, threats, entries or dummy reversal |
| Non-credit diagnostic | Ordinary optimum minus optimum with own studied winning ruffs uncredited | Changes the reward game, not the legal-action game |

Natural Playing Tricks and distribution points remain separate and unchanged.

## E. Restricted-play methodology

Follow suit, card ownership, turn order and trick winners are explicit. The declaring partnership maximizes and defense minimizes. Identical remaining-card/current-trick positions share memoized results.

Three policies remain distinct:

1. **Strict:** remove the viewpoint's trump actions when the studied suit is led. If defense can force a state with no permitted viewpoint action, return `strict_rule_can_force_no_permitted_play`. The internal infeasibility sentinel is never exposed as a trick count or zero. Declarer may avoid infeasible branches when a feasible strategy exists.
2. **Discard if possible:** prohibit these actions only when another legal card exists. Forced ruffs remain allowed. This is not strict prohibition.
3. **No credit:** retain legal play but award no partnership point for a studied-suit trick won by the viewpoint's trump. Both sides optimize the changed payoff; this is not counting ruffs in an originally optimal line.

Restricted searches do not reuse unrestricted DDS continuation values as if they solved the modified game. Node budgets and feasibility statuses are explicit.

## F. Optimal-line ambiguity

Exact joint profiles are `(own studied winning ruffs, own all winning ruffs, partner all winning ruffs)`. Both sides' tied locally minimax-optimal actions are retained. Joint profiles prevent asserting reciprocal ruffs merely because two marginal maxima occur on different lines.

Path counts are accumulated through the memoized graph, not separately materialized principal variations. Exact bounds concern locally optimal perfect-information lines; they do not specify a probability distribution over lines or prove existence of one strategy achieving a secondary objective against every response.

Incomplete searches return a lower bound on the minimum and an upper bound on the maximum. Endpoints need not be attained. No midpoint or zero imputation is used. An unresolved every-line requirement remains unknown. No remaining viewpoint trump or studied-suit card can prove an exact zero future studied-ruff count.

The option-threat fixture includes zero-ruff optimal lines, yet restricting the ruff option loses a trick. Existence of such a line does not show that removing the option preserves the minimax value.

## G. Mechanism taxonomy

Verified descriptors include studied winning ruff, viewpoint ruff in another suit, reciprocal partnership ruffs, optimal-line ambiguity, and sensitivity to action/reward policy. Overruffs lost to defense are not credited as viewpoint winning ruffs.

Immediate/delayed timing, dummy reversal, trump preservation and entry creation are not inferred automatically from counts. No isolated value is assigned to them. Zero studied ruffs is not called zero total shortness value; the zero fixture supports the narrower conclusion that all three tested policies leave its optimum unchanged.

## H. Singleton validation

The zero fixture has these N/E/S/W hands, with East leading and spades trump:

`4C 5S AS | 5C 6C QS | 8C 3D 8S | 4D TD JD`

South has an exact diamond singleton. Optimum three, studied-ruff bounds `[0,0]`, and all three policy losses zero. Winning trump play supports the optimum without a studied ruff.

The ambiguous singleton fixture is:

`6C 9D KD | 5C 4D 5D | JD 3S JS | 3C 4C TD`, South leads.

Its 608 optimal lines have optimum three, ruff bounds `[0,1]`, and strict loss zero. No arbitrary line becomes a scalar target.

## I. Void and one-/two-ruff validation

The three-trick one-ruff fixture has optimum two and exactly one studied winning ruff on every optimal line. Discard-if-possible and non-credit each lose one trick; strict prohibition is infeasible. The crossruff fixture below supplies a feasible strict one-trick-loss oracle.

Five-trick two-ruff-capacity fixture, North leads:

`2D 3D AC KC QC | AD KD AS KS 4C | 2S 3S 2C 3C 8C | QD JD 5C 6C 9C`

Optimum three; strict value one, loss two. Non-credit also loses two, while discard-if-possible loses one. The exact ruff range is `[0,2]` over 98,304 optimal lines. Two independent studied ruffs can occur, but **two actual ruffs are not unavoidable**. This validates two-trick option loss under a specified restriction, not a universal equation between observed ruffs and gained tricks.

All six synthetic fixtures are full-information 3–5-trick endgames, not exhaustive 52-card attribution claims.

## J. Crossruff validation

`3D 3S TS | 7C AC KD | 4C JC 7S | 5C 9C 6D`, North leads, spades trump.

All 16 optimal lines have profile `(1,1,1)` and three tricks. South takes one studied diamond ruff and North one other-suit ruff. Strict prohibition reduces the optimum to two. Reciprocal ruff presence is exact; its separate additive contribution is not isolated from entries and trump winners.

## K. Extreme-trump validation

The actual PT-A2C 12-trump source, viewpoint `AKQJT9876543.2.-.-`, is accepted unchanged. No doubleton reference is manufactured. Its bounded full-deal ruff envelope is `[0,12]`, with endpoints not claimed attained. Restricted searches remain unresolved; no zero is imputed.

The eight-trump void `AKQJ9876.543.-.T2` retains `[0,8]`; the honor-locked five-trump hand retains `[0,5]`. A complete no-own-trump singleton case has exact ruff count zero. Its rule changes are analytically inert because their triggering action cannot occur, although the generic restricted minimax still reaches its computational cap.

## L. Exchange-unevaluable coverage

The saved zero-DDS census accepts all 5,000 physical positions: 3,819 exchange-available and 1,181 exchange-undefined (23.62%). **Physical domain validity is not exact attribution coverage or evidence of a preferable target.**

The bounded pilot selects three exchange-available and three exchange-unavailable deals, three extreme deals and one no-own-trump deal. All six comparison-cohort cases retain `[0,5]`; exact extrema coverage is 0/3 in each exchange stratum. Overall exact count coverage is 1/10, solely the no-own-trump case. All 30 generic full-deal restricted runs reach their 1,500-node caps.

The event definition needs no replacement hand on formerly excluded deals, but their distribution and material differences between strata remain unidentified. These are not recovered exchange effects.

## M. Prior-target comparisons

The original exchange preserves defender cards and its original invariants; coverage remains 76.38%. PT-A2C may change defender spots and collateral shortness. PT-A2D preserves the physical deal but changes the measured event or game rule. These are different estimands.

No overlapping full-deal mechanism scalar is exactly resolved. Pearson and Spearman correlations remain null with explicit reasons. The saved results retain the following certified difference envelopes, not estimated mean or median effects:

| Prior target | n | Mean difference envelope | Median difference envelope | Sign disagreement count bounds |
| --- | --- | --- | --- | --- |
| Exchange first-valid | 3 | [0.3333, 5.3333] | [0, 5] | 1–3 |
| Exchange multi-control mean | 3 | [-0.1806, 4.8194] | [0, 5] | 1–3 |
| Structural | 6 | [-0.1667, 4.8333] | [-0.5, 4.5] | 2–6 |
| Matched | 6 | [-0.3750, 4.6250] | [-0.3750, 4.6250] | 1–6 |
| Conditional baseline | 6 | [-0.1875, 4.8125] | [-0.5, 4.5] | 2–6 |

All compared cases permit, but none certifies, absolute disagreement of at least 1.5 tricks. Full identities and per-case envelopes are saved in `pilot.json`. Zero versus nonzero is a sign disagreement.

For partner `93.A432.AJ2.AK32` and viewpoint `AKQ42.9876.3.J76`, the saved targets are exchange first -1, mean -1/3, structural -1, matched -1 and baseline -0.875. A nonnegative ruff count cannot agree with those signs. An exchange-undefined case with partner `9876.AK3.J7.KQ32` has structural -1, matched +1.25 and baseline +0.625, while the mechanism count remains `[0,5]`. Neither example identifies the correct target by agreement.

## N. Full-information target decision

No target is adopted. Strict prohibition has feasibility gaps; allowing forced ruffs changes the question; non-credit changes the reward. Counts do not isolate gain, reciprocal ruffs do not isolate a crossruff increment, and control attribution remains unmeasured. Full-deal precision is inadequate within this pilot.

## O. Auction-time expectation and leakage

Not run because the adoption gate failed. No PT-A1B averaging, soft likelihood or expectation statistics are introduced. There is no mixed visible-state/actual-hidden-source estimator.

The full-information interface rejects AuctionInformationState, and boundary tests verify that no partial-information sampler is imported. Existing earlier-phase leakage tests passed within the combined selections. A new PT-A2D bidding-time leakage experiment is not claimed: no such expectation API exists yet.

## P. Computational cost

Saved pilot plus supplemental two-ruff benchmark, excluding pytest and exploratory probes:

- DDS calls: 5,534 (4,381 synthetic, 1,153 full-deal); DDS cache hits: 14.
- Restricted solver invocations: 48; 18 small-game runs (16 exact, two infeasible), 30 full-deal runs (all budget-limited).
- Independent exact small-game analysis: 206,665 nodes, 202,820 cache hits, 28,297 optimal graph edges, 101,692 optimal lines counted by memoization.
- Small restricted games: 364,928 nodes and 269,185 cache hits.
- Full-deal path search: 2,308 nodes. Full restricted search: 45,000 nodes and 25,355 cache hits.
- DDS time approximately 1.327 seconds. Pilot wall time 7.684 seconds; supplemental wall time 15.899 seconds.

Full-deal caps were 128 DDS calls and 2,500 path nodes per case, plus 1,500 nodes per restricted policy. The saved five-trick independent analysis cap is 500,000 nodes. These are feasibility budgets, not an optimized performance ceiling. No large full-deal cohort, full PT-1B dataset or auction expectation was launched.

The saved pilot contains the original five synthetic cases; `two_ruff_validation.json` adds the sixth without rerunning that pilot. The final benchmark source includes all six for a future explicitly authorized fresh run. No such run occurred during finalization.

## Q. Exact completed validation

Selections overlap and must not be added. These are the already completed commands; none was rerun during finalization.

| Selection | Result |
| --- | --- |
| Initial PT-A2D, Python 3.14 | 23 passed, 8 expected DDS-only skips |
| PT-A2D/C/B/A2/A1B/A1/A0, Python 3.14 | 222 passed, 14 expected DDS-only skips |
| PT-A2D/C/B/A2, Python 3.12/endplay | 115 passed |
| Added interval-comparison guard | 1 passed, 31 deselected |
| Final PT-A2D focused set, Python 3.12/endplay | **32 passed** |
| PT-1 family | 38 passed, 9 expected solver skips |
| Evaluation/probability/vacant-place selection | 111 passed |
| Auction/context/profile selection | 285 passed |
| Historical regression | **2673 passed, 9 skipped, 143 subtests passed; exit 0; 977.59s (16:17)** |

All recorded runs exited zero. The final focused set includes the interval guard added after the combined selections; earlier totals are retained as executed, not inflated retroactively. Historical regression excludes the seven separately tested PT-A files. No historical safeguard was edited. The existing Python 3.14 baseline avoids the previously documented unrelated Python 3.12 vacant-place compatibility issue; DDS checks use the existing endplay environment.

## R. Production invariant

- `production_changed = False`
- `routes before = 45`
- `routes after = 45`

The saved production-isolation test passed and no production files changed afterward. No production route, bidding-system interpretation, NPT/SRV/CRV/RCC/OR/APT calculation or distribution-point bonus was introduced. DDS queries exist only in the requested research adapter. No OneDrive work occurred.

## S. Recommendation

**PT-A2E mechanism methodology required.**

A later methodology phase must resolve policy semantics, distinguish strategy dependence from tied-line counts, isolate crossruff/control effects if possible, and obtain useful full-deal precision before selecting an auction-time target. Broader definition coverage or a chosen principal variation would not satisfy this requirement.

This checkpoint finalizes PT-A2D only. No PT-A2E or PT-A3 work and no push are authorized or performed as part of finalization.