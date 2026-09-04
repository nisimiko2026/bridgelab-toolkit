from benchmarks.stayman_gamegoing_audit import (
    StaymanGameGoingAuditFixture,
    run_stayman_gamegoing_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router


def test_phase12e_deterministic_endpoint_counts():
    audit = run_stayman_gamegoing_audit()
    assert audit.current_production_endpoint_counts == {"2D": 0, "2H": 0, "2S": 0}
    assert audit.fixture_supported_endpoint_counts == {"2D": 104, "2H": 70, "2S": 61}
    assert audit.opener_both_major_abstentions == 36
    assert audit.game_going_fixture_count_audited == 235


def test_gamegoing_fixture_is_explicit_deterministic_and_not_hand_based():
    fixture = StaymanGameGoingAuditFixture()
    assert not hasattr(fixture, "hcp")


def test_phase12e_source_classification_and_calls():
    audit = run_stayman_gamegoing_audit()
    assert audit.branch_classification_counts == {
        "SOURCE_EXECUTABLE": 0,
        "POLICY_REQUIRED": 0,
        "SOURCE_INSUFFICIENT": 3,
        "ARCHITECTURE_REQUIRED": 2,
        "TERMINAL": 0,
        "ALREADY_ROUTED": 0,
    }
    assert audit.source_safe_calls == {
        "3NT_after_2D": False,
        "4H_after_heart_fit": True,
        "4S_after_spade_fit": True,
    }
    assert audit.recommendation == "D. DEFER THIS FAMILY"


def test_phase12e_is_structurally_deterministic():
    assert run_stayman_gamegoing_audit() == run_stayman_gamegoing_audit()


def test_phase12e_does_not_leak_or_add_routes():
    audit = run_stayman_gamegoing_audit()
    assert not audit.default_registry_has_stayman_continuation_policy
    assert PolicyRegistry().stayman_continuation_strength_policy_ids == ()
    assert audit.production_route_count == len(create_standard_sayc_router().routes) == 44
    assert not audit.production_defaults_changed
    assert audit.knowledge_markdown_changed == 0
