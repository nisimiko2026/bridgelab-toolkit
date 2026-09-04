from benchmarks.post_jacoby_endpoint_audit import run_post_jacoby_endpoint_audit
from bridge.policy_registry import PolicyRegistry


def test_phase12d_exact_endpoint_counts_and_classifications():
    audit = run_post_jacoby_endpoint_audit()
    assert audit.successful_phase12c_continuations == 75
    assert audit.weak == {
        "total": 25,
        "heart_pass": 17,
        "spade_pass": 8,
        "terminal_count": 25,
        "endpoint_classification": "TERMINAL",
        "current_production_route_attempts": 0,
    }
    assert audit.invitational == {
        "total": 25,
        "heart_2NT": 11,
        "spade_2NT": 14,
        "next_actor": "opener (after the benchmark opponent passes)",
        "endpoint_classification": "SOURCE_INSUFFICIENT",
        "current_production_route_attempts": 0,
    }
    assert audit.game_going == {
        "total": 25,
        "4H": 12,
        "4S": 13,
        "terminal_count": 25,
        "endpoint_classification": "TERMINAL",
        "current_production_route_attempts": 0,
    }


def test_phase12d_matrix_is_complete_and_consistent():
    audit = run_post_jacoby_endpoint_audit()
    assert len(audit.source_certainty_matrix) == 6
    assert sum(row["count"] for row in audit.source_certainty_matrix) == 75
    assert all(
        row["source_status"] == "TERMINAL"
        for row in audit.source_certainty_matrix
        if row["endpoint"].startswith(("WEAK", "GAME_GOING"))
    )
    assert all(
        row["source_status"] == "SOURCE_INSUFFICIENT"
        for row in audit.source_certainty_matrix
        if row["endpoint"].startswith("INVITATIONAL")
    )


def test_phase12d_is_structurally_deterministic():
    assert run_post_jacoby_endpoint_audit() == run_post_jacoby_endpoint_audit()


def test_phase12d_preserves_default_policy_and_baseline():
    audit = run_post_jacoby_endpoint_audit()
    assert PolicyRegistry().jacoby_continuation_strength_policy(
        "benchmark.fixture.jacoby.round-robin"
    ) is None
    assert audit.accepted_heart_transfer_positions == 62
    assert audit.accepted_spade_transfer_positions == 61
    assert audit.default_behavior_unchanged
    assert not audit.production_defaults_changed
    assert audit.knowledge_markdown_changed == 0
