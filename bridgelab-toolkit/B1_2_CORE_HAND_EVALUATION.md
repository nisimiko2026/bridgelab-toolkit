# B1.2 — Core Hand Evaluation v2

The single core evaluator remains `bridge.evaluation.evaluate_hand(Hand) -> HandEvaluation`.
There is no second evaluator or bidding-system/profile argument. No DDS or PT-A research
module is imported. No numeric natural, ruffing or adjusted playing-trick value is introduced.

## Existing API and facts retained

`HandEvaluation`, `SuitHonorEvidence` and `SuitQualityEvidence` remain frozen dataclasses.
Their constructor fields, positional order, equality and dataclass serialization are unchanged.
All existing functions and package exports remain available. New facts are derived properties,
so legacy `dataclasses.asdict()` output does not silently acquire new fields; callers exporting
new facts must select those properties explicitly.

Reused facts and conventions:

- `high_card_points`: A=4, K=3, Q=2, J=1.
- Legacy `controls`: A=2, K=1, including a singleton king. This remains a point count,
  distinct from suit-specific control patterns.
- `suit_lengths` and all suit-indexed tuples: S.H.D.C order.
- `distribution`: descending normalized lengths; no shape definition changes.
- Existing balanced shapes: 4333, 4432, 5332; semi-balanced: 5422, 6322.
- Existing raw honor evidence and rank/sequence evidence; no stopper/quality verdict.

## Added facts

On `HandEvaluation`:

- `hcp_by_suit`: per-suit HCP derived from the existing honor evidence and HCP weights.
- `rule_of_20`: frozen `RuleOf20Facts(hcp, longest_suit_length, second_longest_suit_length)`
  with derived `score`. There is no core `qualifies`, opening threshold or recommendation.
- `first_round_controls`, `second_round_controls`: tuples of suits with the patterns below.
- `losers_by_suit`, `losers`: the raw, documented LTC-style count below.
- `shortness_by_suit`: `Shortness.VOID`, `SINGLETON`, `DOUBLETON` or `NONE`.
- `natural_playing_trick_evidence`: the existing `suit_quality_evidence` tuple itself,
  containing lengths, ranks, honors and sequences. It is not a numeric trick estimate.

On `SuitHonorEvidence`:

- `hcp`, `shortness`, `has_guarded_king`, `first_round_control`,
  `second_round_control`, `losers`.

New types are importable from `bridge.evaluation`. A typical access is
`evaluate_hand(hand).honor_evidence(Suit.DIAMONDS).shortness`.

## Control semantics

First-round pattern means ace or void. Second-round pattern means guarded king (length
at least two) or singleton. These are independent categories: a void does not automatically
set the second-round flag, and an ace in a longer suit does not imply a second-round pattern.
A singleton ace has both patterns; a singleton king has the singleton pattern but is not a
guarded king. Honor and shortness bases remain separately inspectable.

Shortness-based patterns need a suitable trump context to be useful. They do not guarantee
tricks, assert a fit, classify a notrump stopper, authorize a cue-bid, or assign shortness value.
Legacy ace/king control points are unchanged by these new pattern facts.

## Loser convention and limitation

The raw count follows the repository table in
`../knowledge/bidding/principles/bidding-fundamentals/losing-trick-count.md`:
consider at most three cards; credit an ace, a king with at least two cards, and a queen with
at least three cards only when supported by ace or king. Thus singleton K has one loser,
Qx has two, Qxx has three, and KQx/AQx each have one. Extra length beyond three does not
add losers. No fractional corrections, fit adjustments or bidding recommendations are made.

This is one explicit LTC convention, not a claim that all LTC variants agree or that the
number predicts actual lost tricks. It is also not `13 - Natural Playing Tricks`.

## Consolidation and migration

General clients should use `evaluate_hand(hand).rule_of_20` for raw arithmetic.
The existing `nisim_nily_opening_policy.assess_rule_of_20` API remains available and now
reads those core facts instead of repeating the arithmetic. Its return schema, authority,
score>=20 qualification, 11-HCP intended-use flag, and no-opening/no-pass guards are unchanged.
This direction of dependency is policy -> core; the core knows nothing about Nisim–Nily.

No existing evaluator is superseded. The existing limited, approved playing-trick lookup
in `opening_policy_consolidation_audit.approved_playing_tricks` is partnership/audit policy,
not a universal formula. It remains outside the core, unchanged. PT-A2/PT-A2D experiments
and other PT-A research are not invoked or modified. Natural honor/sequence evidence,
ruffing values and adjusted values remain separate.

## Validation scope and production invariant

Focused selection: B1.2 core facts, existing hand evaluation, suit-quality evidence,
stopper evidence, and the existing Rule-of-20 policy tests. Final result: **106 passed**.
The first run exposed a mistaken test expectation (ace plus two kings is four control points);
the implementation's existing control count was retained and the expectation corrected.

`production_changed = False`; routes before = 45; routes after = 45.
No bidding-route files or rule semantics changed. No full historical regression, DDS run,
PT-A research run, commit or push is part of B1.2.