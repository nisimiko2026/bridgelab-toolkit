from bridge.evidence_review_contract import ReviewClassification
from bridge.missing_route_classification import (
    MissingRouteFamily,
    _later_seat_opening_prefix,
    classify_missing_routes,
)


def test_later_seat_prefix_two_passes():
    assert _later_seat_opening_prefix("P,P")


def test_later_seat_prefix_three_passes():
    assert _later_seat_opening_prefix("P,P,P")


def test_empty_is_not_later_seat():
    assert not _later_seat_opening_prefix("")


def test_one_pass_is_not_later_seat():
    assert not _later_seat_opening_prefix("P")


def test_nonpass_auction_is_not_later_seat():
    assert not _later_seat_opening_prefix("1C,P")


def test_report_accounts_for_all_missing_routes():
    r = classify_missing_routes(start_seed=1, count=100)
    assert r.missing_route_population == len(r.cases)
    assert sum(g.count for g in r.groups) == r.missing_route_population


def test_only_reviewed_later_seat_family_is_core_gap():
    r = classify_missing_routes(start_seed=1, count=100)
    for x in r.cases:
        if x.family is MissingRouteFamily.LATER_SEAT_OPENING:
            assert x.classification is ReviewClassification.CORE_GAP
        else:
            assert x.classification is ReviewClassification.INSUFFICIENT_EVIDENCE


def test_a96_is_classification_only():
    r = classify_missing_routes(start_seed=1, count=25)
    # A9.6 records no recommended call and exposes no "correct bid" field.
    assert all(not hasattr(x, "call") for x in r.cases)
    assert all(not hasattr(x, "recommendation") for x in r.cases)
