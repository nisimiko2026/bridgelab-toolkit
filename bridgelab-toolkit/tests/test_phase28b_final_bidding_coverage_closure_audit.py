from benchmarks.phase28b_final_bidding_coverage_closure_audit import (
    build_audit,
)


def test_phase28b_closes_bidding_coverage():
    audit = build_audit()

    assert audit.phase == "28B"
    assert audit.phase28a_loaded
    assert audit.phase28a_closure_ready
    assert audit.production_route_count == 45
    assert audit.remaining_high_value_source_ready == 0
    assert audit.closure_gate
    assert audit.decision == "PHASE 28 BIDDING COVERAGE COMPLETE"


def test_phase28b_current_families_are_audited_without_blind_expansion():
    audit = build_audit()

    by_family = {row.family: row for row in audit.current_families}
    assert set(by_family) == {
        "response.one-level-existing-rule",
        "opener.one-level-rebid-existing-rule",
    }

    for row in by_family.values():
        assert row.classification == "CURRENT_SOURCE_GROUNDED_PARTIAL_COVERAGE"
        assert row.decision == "AUDITED_CURRENT_STATE_NO_BLIND_EXPANSION"
        assert not row.source_ready
        assert row.closure_safe


def test_phase28b_deferred_families_remain_closure_safe_and_not_source_ready():
    audit = build_audit()

    assert audit.deferred_families
    assert all(row.closure_safe for row in audit.deferred_families)
    assert all(not row.source_ready for row in audit.deferred_families)

    by_family = {row.family: row for row in audit.deferred_families}

    assert by_family["Stayman residuals"].classification == "SOURCE_PARTIAL"
    assert by_family["strong-2C residuals"].classification == "SOURCE_PARTIAL"
    assert by_family["natural 1NT responses"].classification == "SOURCE_PARTIAL"
    assert by_family["responder rebids"].classification == "SOURCE_PARTIAL"
    assert (
        by_family["three-level preempt responses"].classification
        == "SOURCE_PARTIAL"
    )
    assert (
        by_family["weak-two responses"].classification
        == "PARTNERSHIP_DEPENDENT"
    )
    assert by_family["weak-two responses"].decision == "DEFER_POLICY_REQUIRED"
    assert by_family["2NT response residuals"].classification == "SOURCE_PARTIAL"
    assert (
        by_family["Two-over-One unsupported opener rebids"].classification
        == "SOURCE_INSUFFICIENT"
    )


def test_phase28b_is_audit_only():
    audit = build_audit()

    assert audit.production_rules_added == 0
    assert audit.routes_added == 0
    assert audit.policies_added == 0
    assert not audit.production_defaults_changed
    assert audit.knowledge_markdown_changed == 0
