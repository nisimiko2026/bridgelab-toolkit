"""A9.2 opening-Pass review tests."""
from bridge.opening_pass_review import review_opening_pass_cases


REPRESENTATIVE = (2, 6, 9, 10, 11)


def test_empty():
    r = review_opening_pass_cases(count=0)
    assert r.population == 0
    assert r.cases == ()


def test_1000_population_matches_a8():
    r = review_opening_pass_cases(count=1000, seeds=())
    assert r.population == 563


def test_representative_seeds_found():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    assert tuple(x.seed for x in r.cases) == REPRESENTATIVE


def test_replay_keys_preserved():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    assert all(x.replay_key == f"sayc-production@1:seed:{x.seed}" for x in r.cases)


def test_hands_preserved():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    assert all(x.hand and x.deal for x in r.cases)


def test_shape_is_four_suits_and_thirteen_cards():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    assert all(len(x.shape) == 4 and sum(x.shape) == 13 for x in r.cases)


def test_rejection_trace_present():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    assert all(x.rejected_rules for x in r.cases)


def test_rejection_trace_contains_opening_rules():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    assert all(all(rule.startswith("sayc.opening.") for rule, _ in x.rejected_rules) for x in r.cases)


def test_no_pass_or_correct_bid_decision_surface():
    r = review_opening_pass_cases(count=1000, seeds=REPRESENTATIVE)
    for x in r.cases:
        for name in ("recommended_bid", "correct_bid", "should_pass", "classification", "disposition"):
            assert not hasattr(x, name)


def test_unknown_seed_is_not_invented():
    r = review_opening_pass_cases(count=100, seeds=(999999,))
    assert r.cases == ()


def test_deterministic():
    assert review_opening_pass_cases(count=100, seeds=(2, 6)) == review_opening_pass_cases(count=100, seeds=(2, 6))
