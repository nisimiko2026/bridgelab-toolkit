import inspect
from benchmarks.weak_two_response_source_readiness_audit import (
    run_weak_two_response_source_readiness_audit,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router

A = run_weak_two_response_source_readiness_audit()


def test_population():
    assert (A.start_seed, A.deal_count, A.expected_population, A.population) == (
        1,
        10_000,
        540,
        540,
    )
    assert A.per_opening == {"2D": 167, "2H": 179, "2S": 194}
    assert {x["auction_prefix"] for x in A.positions} == {"2D P", "2H P", "2S P"}
    assert {x["current_action"] for x in A.positions} == {"ABSTAIN"}


def test_partitions():
    assert A.primary_partitions == {
        "very-strong/slam-interest-looking": 12,
        "game-looking-with-support": 27,
        "balanced/nt-inquiry-looking": 196,
        "support/raise-oriented": 65,
        "long-independent-suit": 120,
        "weak/no-action-looking": 120,
    }
    assert sum(A.primary_partitions.values()) == 540
    assert sum(x["observed_count"] for x in A.source_matrix) == 540


def test_source():
    assert "Natural weak two" in A.two_d_meaning
    assert A.inquiry_findings == {
        "two_nt_inquiry_exists": True,
        "forcing_status_complete": False,
        "feature_ask_replies_complete": False,
        "ogust_optional": True,
        "minimum_maximum_mapping_partnership_dependent": True,
        "executable": False,
    }
    assert all(not x["executable_subset"] for x in A.source_matrix)
    assert len({x["opening"] for x in A.source_matrix}) == 3


def test_selection():
    assert A.decision == "E. DEFER WEAK-TWO RESPONSES"
    assert A.phase12t_recommendation["family_id"] == "response.two-notrump"
    assert A.phase12t_recommendation["phase12m_population"] == 33


def test_no_production_changes():
    assert A.route_count == len(create_standard_sayc_router().routes) == 45
    assert all(x["route_missing"] for x in A.positions)
    assert (A.production_rules_added, A.routes_added, A.policies_added) == (0, 0, 0)
    assert PolicyRegistry().stayman_dual_major_response_policy_ids == ()
    assert "EngineRoute(" not in inspect.getsource(
        __import__(
            "benchmarks.weak_two_response_source_readiness_audit", fromlist=["x"]
        )
    )


def test_defaults_and_knowledge():
    assert A.production_defaults_changed is False
    assert A.knowledge_markdown_changed == 0


def test_deterministic():
    assert A == run_weak_two_response_source_readiness_audit()
