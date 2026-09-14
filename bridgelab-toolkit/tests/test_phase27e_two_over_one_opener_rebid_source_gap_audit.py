from benchmarks.phase27e_two_over_one_opener_rebid_source_gap_audit import (
    run_two_over_one_opener_rebid_source_gap_audit,
)


def test_phase27e_maps_all_four_canonical_two_over_one_routes():
    audit = run_two_over_one_opener_rebid_source_gap_audit()
    assert audit.canonical_family_count == 4
    assert audit.route_count == 45
    assert audit.all_routes_reachable

    by_auction = {row["auction"]: row for row in audit.cases}
    assert by_auction["1H-P-2C-P"]["expected_route"] == "sayc.2over1.opener.1h.2c"
    assert by_auction["1H-P-2D-P"]["expected_route"] == "sayc.2over1.opener.1h.2d"
    assert by_auction["1S-P-2C-P"]["expected_route"] == "sayc.2over1.opener.1s.2c"
    assert by_auction["1S-P-2D-P"]["expected_route"] == "sayc.2over1.opener.1s.2d"


def test_phase27e_unsupported_canonical_routes_are_source_insufficient_and_abstain():
    audit = run_two_over_one_opener_rebid_source_gap_audit()
    by_auction = {row["auction"]: row for row in audit.cases}

    for auction in ("1H-P-2C-P", "1S-P-2D-P"):
        row = by_auction[auction]
        assert row["production_coverage"] == "NONE"
        assert row["source_status"] == "SOURCE_INSUFFICIENT"
        assert row["current_probe_action"] == "ABSTAIN"
        assert row["decision"] == "DEFER"

    assert audit.unsupported_all_abstain


def test_phase27e_supported_canonical_routes_remain_partial_not_generalized():
    audit = run_two_over_one_opener_rebid_source_gap_audit()
    by_auction = {row["auction"]: row for row in audit.cases}

    for auction in ("1H-P-2D-P", "1S-P-2C-P"):
        row = by_auction[auction]
        assert row["production_coverage"] == "PARTIAL"
        assert row["source_status"] == "SOURCE_PARTIAL"
        assert row["decision"] == "KEEP_EXISTING_RULES"


def test_phase27e_is_audit_only():
    audit = run_two_over_one_opener_rebid_source_gap_audit()
    assert audit.production_rules_added == 0
    assert audit.routes_added == 0
    assert audit.policies_added == 0
    assert not audit.production_defaults_changed
    assert audit.knowledge_markdown_changed == 0
