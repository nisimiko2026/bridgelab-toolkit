"""A9.4 opening decision coverage audit tests."""
from bridge.opening_decision_coverage_audit import (
    OpeningCoverageFamily,
    audit_opening_decision_coverage,
)


def test_empty():
    r = audit_opening_decision_coverage(count=0)
    assert r.population == 0
    assert r.cases == r.groups == r.normal_strength_shape_counts == ()


def test_1000_population_preserved():
    assert audit_opening_decision_coverage(count=1000).population == 563


def test_every_case_has_exactly_one_family():
    r = audit_opening_decision_coverage(count=1000)
    assert len(r.cases) == r.population
    assert sum(g.count for g in r.groups) == r.population


def test_below_strength_family_is_below_12():
    r = audit_opening_decision_coverage(count=1000)
    assert all(
        x.source.case.hcp < 12
        for x in r.cases
        if x.family is OpeningCoverageFamily.BELOW_NORMAL_STRENGTH_REVIEW
    )


def test_equal_major_family_has_equal_five_plus_majors():
    r = audit_opening_decision_coverage(count=10000)
    xs = [x for x in r.cases if x.family is OpeningCoverageFamily.EQUAL_FIVE_PLUS_MAJORS]
    assert xs
    assert all(x.source.case.shape[0] == x.source.case.shape[1] >= 5 for x in xs)


def test_equal_minor_family_is_exactly_five_five_minors():
    r = audit_opening_decision_coverage(count=10000)
    xs = [x for x in r.cases if x.family is OpeningCoverageFamily.EQUAL_FIVE_MINORS]
    assert xs
    assert all(x.source.case.shape[2:] == (5, 5) for x in xs)


def test_10k_known_normal_strength_split():
    r = audit_opening_decision_coverage(count=10000)
    assert r.count(OpeningCoverageFamily.EQUAL_FIVE_PLUS_MAJORS) == 20
    assert r.count(OpeningCoverageFamily.EQUAL_FIVE_MINORS) == 25
    assert r.count(OpeningCoverageFamily.OTHER_NORMAL_STRENGTH_UNRESOLVED) == 0
    assert r.count(OpeningCoverageFamily.ABOVE_NORMAL_STRENGTH_UNRESOLVED) == 0


def test_10k_below_strength_count():
    r = audit_opening_decision_coverage(count=10000)
    assert r.count(OpeningCoverageFamily.BELOW_NORMAL_STRENGTH_REVIEW) == 5844


def test_normal_shape_histogram_accounts_for_45():
    r = audit_opening_decision_coverage(count=10000)
    assert sum(n for _, n in r.normal_strength_shape_counts) == 45


def test_shares_sum_to_one():
    r = audit_opening_decision_coverage(count=1000)
    assert abs(sum(g.share_of_population for g in r.groups) - 1.0) < 1e-12


def test_no_policy_or_pass_decision_surface():
    r = audit_opening_decision_coverage(count=100)
    for name in ("should_pass", "recommended_bid", "policy_change", "winner", "rank", "priority"):
        assert not hasattr(r, name)


def test_deterministic():
    assert audit_opening_decision_coverage(count=100) == audit_opening_decision_coverage(count=100)
