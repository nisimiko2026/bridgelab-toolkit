from bridge.missing_route_structural_classification import (
    MissingRouteStructuralFamily as F,
    _classify_auction,
    _calls,
    classify_missing_route_structure,
)


def test_parser_matches_observed_space_serialization():
    assert _calls("1D P 1H P 1S P") == ("1D","P","1H","P","1S","P")


def test_parser_tolerates_commas():
    assert _calls("2S,P") == ("2S","P")


def test_two_level_response_family():
    assert _classify_auction("2S P")[0] is F.RESPONSE_TO_TWO_LEVEL_OPENING


def test_three_level_response_family():
    assert _classify_auction("3H P")[0] is F.RESPONSE_TO_THREE_LEVEL_OPENING


def test_opener_rebid_family():
    assert _classify_auction("1D P 1H P")[0] is F.OPENER_REBID_AFTER_ONE_LEVEL_RESPONSE


def test_responder_rebid_family():
    assert _classify_auction("1D P 1H P 1S P")[0] is F.RESPONDER_REBID_AFTER_OPENER_REBID


def test_later_continuation_family():
    assert _classify_auction("1C P 1D P 1H P 2C P")[0] is F.LATER_CONTINUATION


def test_report_accounts_for_every_missing_route():
    r = classify_missing_route_structure(start_seed=1, count=100)
    assert len(r.cases) == r.missing_route_population
    assert sum(g.count for g in r.groups) == r.missing_route_population


def test_classification_is_diagnostic_only():
    r = classify_missing_route_structure(start_seed=1, count=25)
    assert all(not hasattr(x, "call") for x in r.cases)
    assert all(not hasattr(x, "recommendation") for x in r.cases)
