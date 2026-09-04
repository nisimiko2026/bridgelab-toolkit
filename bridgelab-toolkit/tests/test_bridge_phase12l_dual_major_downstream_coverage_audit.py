import inspect

from benchmarks.stayman_dual_major_downstream_coverage_audit import (
    run_stayman_dual_major_downstream_coverage_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_exact_target_paths_and_coverage():
    audit = run_stayman_dual_major_downstream_coverage_audit()
    assert audit.target_total == 36
    assert audit.hearts_path["opener_calls"] == 36
    assert audit.hearts_path["terminal_calls"] == 5
    assert audit.hearts_path["residual_abstentions"] == 31
    assert audit.hearts_path["terminal_coverage_pct"] == 13.89
    assert audit.spades_path["opener_calls"] == 36
    assert audit.spades_path["terminal_calls"] == 7
    assert audit.spades_path["residual_abstentions"] == 29
    assert audit.spades_path["terminal_coverage_pct"] == 19.44


def test_cross_policy_identity_and_mutually_exclusive_classification():
    audit = run_stayman_dual_major_downstream_coverage_audit()
    assert audit.cross_policy_counts == {
        "BOTH_TERMINAL": 0,
        "HEARTS_ONLY_TERMINAL": 5,
        "SPADES_ONLY_TERMINAL": 7,
        "NEITHER_TERMINAL": 24,
    }
    assert sum(audit.cross_policy_counts.values()) == 36
    assert len(audit.positions) == 36
    assert len({row["seed"] for row in audit.positions}) == 36
    assert all(row["cross_policy_outcome"] in audit.cross_policy_counts for row in audit.positions)


def test_exact_responder_and_residual_primary_partitions():
    audit = run_stayman_dual_major_downstream_coverage_audit()
    assert audit.responder_primary_buckets == {
        "both_majors_four_plus": 0,
        "hearts_only_four_plus": 5,
        "spades_only_four_plus": 7,
        "neither_major_long_minor": 8,
        "neither_major_balanced_looking": 12,
        "neither_major_other_shape": 4,
    }
    assert sum(audit.responder_primary_buckets.values()) == 36
    assert audit.hearts_residual_primary_buckets == {
        "other_major_exactly_four": 7,
        "other_major_five_plus": 0,
        "no_four_card_major_long_minor": 8,
        "no_four_card_major_balanced_looking": 12,
        "no_four_card_major_other_shape": 4,
    }
    assert sum(audit.hearts_residual_primary_buckets.values()) == 31
    assert audit.spades_residual_primary_buckets == {
        "other_major_exactly_four": 5,
        "other_major_five_plus": 0,
        "no_four_card_major_long_minor": 8,
        "no_four_card_major_balanced_looking": 12,
        "no_four_card_major_other_shape": 4,
    }
    assert sum(audit.spades_residual_primary_buckets.values()) == 29


def test_source_rows_defer_without_policy_preference_or_new_candidate():
    audit = run_stayman_dual_major_downstream_coverage_audit()
    assert len(audit.source_certainty_matrix) == 10
    assert all(row["classification"] == "SOURCE_INSUFFICIENT" for row in audit.source_certainty_matrix)
    assert audit.source_safe_candidates == ()
    assert audit.source_interpretation.startswith("NO SOURCE-BACKED POLICY PREFERENCE")
    assert audit.decision == "D. DEFER DUAL-MAJOR DOWNSTREAM RESIDUALS"


def test_routes_defaults_prior_phases_and_jacoby_are_unchanged():
    audit = run_stayman_dual_major_downstream_coverage_audit()
    assert audit.route_count == 44
    assert len(create_standard_sayc_router().routes) == 44
    assert audit.default_dual_major_policy is None
    assert audit.default_continuation_policy is None
    assert PolicyRegistry().stayman_dual_major_response_policy_ids == ()
    assert PolicyRegistry().stayman_continuation_strength_policy_ids == ()
    assert audit.phase12g_calls == {"4H": 17, "4S": 21}
    assert audit.phase12h_residual_total == 197
    assert audit.jacoby_no_policy == {
        "heart_transfer": 62,
        "spade_transfer": 61,
        "total": 123,
    }


def test_phase12l_adds_no_production_rule_or_automatic_preference():
    module = __import__(
        "benchmarks.stayman_dual_major_downstream_coverage_audit",
        fromlist=["unused"],
    )
    source = inspect.getsource(module).casefold()
    assert "high_card_points" not in source
    assert "hcp" not in source
    assert "3nt" not in source.replace('"3nt",', "")
    assert "automatic policy" not in source
    audit = run_stayman_dual_major_downstream_coverage_audit()
    assert audit.production_defaults_changed is False
    assert audit.knowledge_markdown_changed == 0


def test_phase12l_is_structurally_deterministic():
    assert (
        run_stayman_dual_major_downstream_coverage_audit()
        == run_stayman_dual_major_downstream_coverage_audit()
    )
