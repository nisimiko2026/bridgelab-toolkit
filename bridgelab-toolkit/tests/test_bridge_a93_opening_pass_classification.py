"""A9.3 opening-review population classification tests."""
from bridge.opening_pass_classification import (
    OpeningReviewClass,
    classify_opening_pass_population,
)


def test_empty():
    r = classify_opening_pass_population(count=0)
    assert r.population == 0
    assert r.cases == r.groups == r.hcp_counts == r.shape_counts == ()


def test_1000_population_matches_a8():
    r = classify_opening_pass_population(count=1000)
    assert r.population == 563


def test_every_case_classified_once():
    r = classify_opening_pass_population(count=1000)
    assert len(r.cases) == r.population
    assert sum(g.count for g in r.groups) == r.population


def test_group_shares_sum_to_one():
    r = classify_opening_pass_population(count=1000)
    assert abs(sum(g.share_of_population for g in r.groups) - 1.0) < 1e-12


def test_below_strength_cases_are_below_12():
    r = classify_opening_pass_population(count=1000)
    assert all(
        x.case.hcp < 12
        for x in r.cases
        if x.review_class is OpeningReviewClass.BELOW_NORMAL_OPENING_STRENGTH
    )


def test_normal_unresolved_cases_are_12_to_21():
    r = classify_opening_pass_population(count=1000)
    assert all(
        12 <= x.case.hcp <= 21
        for x in r.cases
        if x.review_class is OpeningReviewClass.NORMAL_OPENING_STRENGTH_UNRESOLVED
    )


def test_above_normal_unresolved_cases_are_22_plus():
    r = classify_opening_pass_population(count=1000)
    assert all(
        x.case.hcp >= 22
        for x in r.cases
        if x.review_class is OpeningReviewClass.ABOVE_NORMAL_OPENING_STRENGTH_UNRESOLVED
    )


def test_hcp_histogram_accounts_for_population():
    r = classify_opening_pass_population(count=1000)
    assert sum(n for _, n in r.hcp_counts) == r.population


def test_shape_histogram_accounts_for_population():
    r = classify_opening_pass_population(count=1000)
    assert sum(n for _, n in r.shape_counts) == r.population


def test_replay_and_rejection_evidence_preserved():
    r = classify_opening_pass_population(count=1000)
    assert all(x.case.replay_key and x.case.rejected_rules for x in r.cases)


def test_no_pass_or_policy_decision_surface():
    r = classify_opening_pass_population(count=100)
    for name in ("should_pass", "recommended_bid", "correct_bid", "policy_change", "priority", "rank"):
        assert not hasattr(r, name)


def test_deterministic():
    assert classify_opening_pass_population(count=100) == classify_opening_pass_population(count=100)
