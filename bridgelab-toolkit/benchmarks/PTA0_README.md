# PT-A0 — Auction Information State

## A. Repository state

Working directory: C:/Users/nisim/Documents/BridgeLab-phase18b-worktree/bridgelab-toolkit.
Branch: codex/phase18b. Starting and ending HEAD: e6f15575fdde8cf9ec43b66cb8b41fa7731fc9f5.
PT-1/PT-1A/PT-1B source, benchmarks, tests and small reports are tracked.
The four pre-existing compressed research datasets remain untracked and untouched.
No OneDrive work, commit, push, PT-A1 implementation, DDS call, or dataset rerun.

## B. Assessment of the existing files

Compared both files with the approved PT-A0 specification recovered from the earlier
“Bridge Void Playing Value” task, including its original detailed architectural requirements.
Retained the immutable evidence history, range intersection, shape restrictions, certainty,
provenance, snapshots, own shortness and hidden-information boundary. Retained all 33 tests.

Corrected these assumptions:

- Defender maxima cannot simply be added without the remaining suit-card limit and partner constraints.
- A contradictory state cannot establish a fit or activate shortness relevance.
- An eight-card own suit already guarantees an eight-card partnership total.
- A total maximum below eight means no possible fit, rather than a possible fit.
- Individually feasible shape alternatives need not be jointly feasible across three seats.
- In the snapshot fixture starting with South, the fourth caller is East, not West.

Extended the tests to 47 cases, including four-state progression, every seat orientation,
probability-one evidence staying probabilistic, joint-shape contradictions and stronger isolation.

## C. Files

Revised the two pre-existing untracked files:

- bridge/auction_information.py
- tests/test_bridge_pta0_auction_information.py

Added this report: benchmarks/PTA0_README.md. No tracked production file changed.

## D. Public API and architecture reuse

Import directly from bridge.auction_information:

- AuctionInformationState.start(perspective, own_hand, dealer)
- AuctionInformationState.from_auction(perspective, own_hand, auction, updates=())
- state.after_call(call, updates=()) and state.with_updates(updates): new cumulative snapshots
- state.for_seat(seat): hard HCP/suit ranges, possible shapes, original evidence and conflicts
- state.fit(suit), state.opponent_fit(suit), state.own_shortness(): information only
- state.status, state.conflicts, state.partner, state.opponents
- snapshots(initial, steps): one immutable state after each call

Inputs: AuctionConstraintUpdate, NumericRange, RangeEvidence, ShapeEvidence,
DiscreteDistribution, ConstraintProvenance, Certainty, EvidenceOrigin.
Outputs: SeatInformation, ConstraintConflict, FitInformation, OpponentFitInformation,
ShortnessInformation, InformationStatus, FitStatus, ShortnessKind.

Reuses Auction, AuctionEntry, Call, Hand, Seat, Suit, high_card_points, SUIT_ORDER and
ProbabilityValue. BiddingContext is a rule-evaluation input requiring system/evaluation
context and a next-to-call player. It does not supply arbitrary-perspective evidence histories.
PT-A0 reuses existing auction mechanics without introducing another router or interpreter.
Existing vacant_places mathematics is neither duplicated nor invoked: a promised length
must not be converted into an observed card identity or exact vacant-place allocation.

## E. Constraints, certainty and provenance

Updates name an absolute target seat, with optional HCP range, suit ranges or allowed
13-card shapes in S.H.D.C order. Every evidence item retains certainty and provenance:
typed origin, reference, optional zero-based call index and optional opaque source/profile ID.
Call indices are checked against the snapshot and partner/opponent origins against the actor.
The target can differ from the source actor for externally derived indirect evidence.

Own Hand is exact. Unknown-seat EXACT updates are rejected; a logically forced single
length remains a GUARANTEED constraint rather than knowledge of unseen card identities.
UNKNOWN is represented by absence of evidence, with public card-count bounds only.
INFERRED and PROBABILISTIC inputs remain inspectable but never narrow guaranteed bounds,
even when a supplied distribution assigns probability one to a single outcome.

Hard ranges intersect and allowed shapes filter per-seat 13-card possibilities. Updates
append rather than overwrite. Soft evidence is not fused, renormalized or promoted.
SeatInformation exposes hcp_evidence(), suit_evidence(), hcp_provenance() and suit_provenance().
Arithmetic provenance accompanies derived bounds. Earlier snapshots stay unchanged.

## F. Contradiction handling

Detects empty HCP/suit intersections, impossible per-seat 13-card shapes, unavailable unseen
suit/HCP totals, and incompatible combinations of the three unseen seats' shape alternatives.
ConstraintConflict retains its subject and sources. Contradictions are not silently repaired.
Inconsistent projections use None; fit results use CONTRADICTORY with no total and cannot
activate shortness relevance. Locally feasible seat projections may remain available when
the global state is contradictory; consumers must consult state.status.

## G. Fit derivation

Own exact length plus the partner hard range gives the partnership total. Opponent totals
intersect summed defender bounds with 13 minus the partnership holding. Numeric totals
drive labels, including NO_POSSIBLE_FIT and CONTRADICTORY. There are no value coefficients.
The ranges are conservative bounds, not probability distributions.

## H. Shortness progression

Exact South hand: AKQ42.9876.3.J76.

| Snapshot | General update | Minimum spade total | Diamond information |
|---|---|---:|---|
| 1 | None | 5 | Exact singleton; no established fit |
| 2 | North spades >= 3 | 8 | Same singleton; fit established |
| 3 | North spades >= 4 | 9 | Same singleton; stronger fit |
| 4 | West diamonds >= 5 | 9 | Same singleton; defender evidence available |

Own void/singleton/doubleton remains recorded independently of fit. No NPT/SRV/CRV/ERV/APT,
shortness bonus, distribution points or other playing value is exposed or calculated.

## I. Hidden-information isolation

The test creates two valid full deals with an identical perspective hand and different
holdings at all three unseen seats. Identical visible auction and updates produce identical
states, seat projections, conflicts, shortness and fit outputs. Only the perspective hand is
passed into PT-A0. There is no Deal/DDS input or import. Import-boundary tests also exclude
system and partnership code from the module.

## J. Opponent example

After the visible calls 1S, 2D from South, an externally supplied West diamonds >= 5 update
retains OPPONENT_CALL provenance, call index 1 and its reference. East does not acquire West's
direct evidence. PT-A0 never infers this meaning from 2D. All perspectives have orientation tests.

## K. Tests

Existing Documents project Python 3.14 environment; commands execute in Phase18B with
PYTHONDONTWRITEBYTECODE=1 and pytest cache disabled.

| Group | Passed | Skipped | Failed |
|---|---:|---:|---:|
| Pre-edit PT-A0 baseline | 33 | 0 | 0 |
| Final PT-A0 | 47 | 0 | 0 |
| Auction/context/profile | 428 | 0 | 0 |
| PT-1/PT-1A/PT-1B | 38 | 9 | 0 |
| Evaluation/probability | 106 | 0 | 0 |
| Historical regression (excluding separately validated PT-A0) | 2673 | 9 | 0 |

Historical regression also passed 143 subtests. The original pytest process completed
with exit code 0 in 2588.72 seconds (43:08); its final output was recovered reliably
from the existing execution session during validation resumption. No test rerun was needed.
No implementation or test code was changed during validation resumption.

The nine solver-dependent skips are due to absent endplay. No OneDrive solver environment
was used. Groups overlap the historical suite; do not add them as unique test counts.

Focused command: python -m pytest tests/test_bridge_pta0_auction_information.py -q -p no:cacheprovider
Historical command: python -m pytest -q -p no:cacheprovider --ignore=tests/test_bridge_pta0_auction_information.py
Auction/context/profile selection: tests/test_bridge*.py names matching
auction|bidding_rules|profile|partnership|treatment_binding|base_system|two_over_one_opening.
Evaluation/probability selection: tests/test_bridge*.py names matching evaluation|probability.
PT tests: test_bridge_pt1_playing_trick_calibration.py, test_bridge_pt1a_solver.py,
test_bridge_pt1b_shortness.py.

## L. Production result

production_changed = False. Runtime create_standard_sayc_router().routes count:
45 before / 45 after. No tracked production diff, registration or integration changes.

## M. Limitations

No call interpretation, probability generation/fusion, evidence retraction, deal sampling,
rank-allocation solver or playing-value calculation. Consistency covers the represented
range/shape arithmetic; it does not prove physical realizability of arbitrary HCP/shape
combinations at the card-rank level. Seat/fit ranges are conservative projections rather
than exhaustive globally tightened domains. Disagreeing soft evidence remains inspectable
without making hard knowledge contradictory. Provenance identifies asserted sources but
cannot authenticate the external interpreter's assertions.

## N. Recommendation

Ready for PT-A1 against this information contract. The historical regression completed
successfully with zero failures. PT-A1 itself was not started. No commit or push was made.
