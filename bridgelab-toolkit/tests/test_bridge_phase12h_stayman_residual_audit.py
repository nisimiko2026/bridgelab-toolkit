import inspect

from benchmarks.stayman_residual_coverage_audit import (
    run_stayman_residual_coverage_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_exact_residual_totals_and_phase12g_calls():
    audit = run_stayman_residual_coverage_audit()
    assert audit.residual_by_family == {
        "after_2D": 104,
        "after_2H_no_fit": 53,
        "after_2S_no_fit": 40,
    }
    assert audit.residual_total == 197
    assert audit.phase12g_calls == {"4H": 17, "4S": 21}
    assert audit.dual_major_abstentions == 36


def test_every_position_has_exactly_one_primary_bucket_and_matrix_row():
    audit = run_stayman_residual_coverage_audit()
    assert audit.primary_shape_buckets == {
        "after_2D": {
            "both_majors_four_plus": 9,
            "exactly_one_four_card_major": 52,
            "five_four_major_pattern": 2,
            "no_four_card_major_balanced_looking": 30,
            "no_four_card_major_long_minor": 9,
            "no_four_card_major_other_shape": 2,
        },
        "after_2H_no_fit": {
            "no_four_card_major_balanced_looking": 23,
            "no_four_card_major_long_minor": 7,
            "no_four_card_major_other_shape": 8,
            "other_major_exactly_four": 15,
        },
        "after_2S_no_fit": {
            "no_four_card_major_balanced_looking": 14,
            "no_four_card_major_long_minor": 6,
            "no_four_card_major_other_shape": 1,
            "other_major_exactly_four": 19,
        },
    }
    for family, expected in audit.residual_by_family.items():
        assert sum(audit.primary_shape_buckets[family].values()) == expected
    assert sum(row["exact_count"] for row in audit.source_certainty_matrix) == 197
    assert all(
        row["classification"] == "SOURCE_INSUFFICIENT"
        for row in audit.source_certainty_matrix
    )


def test_route_attempts_are_measured_but_no_production_action_occurs():
    audit = run_stayman_residual_coverage_audit()
    assert audit.existing_route_matches == {
        "after_2D": 0,
        "after_2H_no_fit": 53,
        "after_2S_no_fit": 40,
    }
    assert audit.existing_production_actions == {
        "after_2D": 0,
        "after_2H_no_fit": 0,
        "after_2S_no_fit": 0,
    }


def test_phase12h_is_structurally_deterministic():
    assert (
        run_stayman_residual_coverage_audit()
        == run_stayman_residual_coverage_audit()
    )


def test_phase12h_adds_no_hcp_classifier_route_or_default_policy():
    module = __import__(
        "benchmarks.stayman_residual_coverage_audit", fromlist=["unused"]
    )
    source = inspect.getsource(module).casefold()
    assert "high_card_points" not in source
    assert "hcp" not in source
    assert len(create_standard_sayc_router().routes) == 44
    assert PolicyRegistry().stayman_continuation_strength_policy_ids == ()
    audit = run_stayman_residual_coverage_audit()
    assert audit.route_count == 44
    assert audit.source_safe_subset_candidates == ()
    assert audit.recommendation == "D. DEFER STAYMAN RESIDUALS"
