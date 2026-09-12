from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from benchmarks.phase20b_route_reachability_audit import run_route_reachability_audit
from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.deal_analysis import AnalysisStage, PolicyVisibility
from bridge.engine_router import BiddingEngineRouter
from bridge.full_deal_analysis import (
    FullDealAnalysisInput,
    analyze_full_deal,
    full_deal_analysis_to_dict,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


def _bidding_context(
    auction: str,
    hand: str = "AKQJ.5432.32.432",
) -> BiddingContext:
    parsed = Hand.parse(hand)
    sequence = Auction(Seat.NORTH, auction.split())
    return BiddingContext.create(
        hand=parsed,
        auction=sequence,
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


def _serialized_bidding(auction: str, hand: str = "AKQJ.5432.32.432"):
    request = FullDealAnalysisInput(
        requested_stages=(AnalysisStage.AUCTION,),
        bidding=_bidding_context(auction, hand),
    )
    return full_deal_analysis_to_dict(
        analyze_full_deal(
            request,
            bidding_router=create_standard_sayc_router(),
        )
    )["subsystem_results"][0]


def test_policy_visibility_contract_is_immutable_and_narrow():
    policy = PolicyVisibility(
        "POLICY_GATED",
        ("stopper", "suit_quality"),
    )

    assert policy.serialize() == {
        "requirement": "POLICY_GATED",
        "dependencies": ("stopper", "suit_quality"),
    }

    with pytest.raises(FrozenInstanceError):
        policy.requirement = "changed"

    with pytest.raises(ValueError):
        PolicyVisibility("NOT_POLICY_GATED", ("stopper",))

    with pytest.raises(ValueError):
        PolicyVisibility("POLICY_GATED", ())

    with pytest.raises(ValueError):
        PolicyVisibility("POLICY_GATED", ("stopper", "STOPPER"))


def test_standard_router_policy_metadata_matches_phase20b_audited_dependencies():
    router = create_standard_sayc_router()
    structural = run_route_reachability_audit()

    router_dependencies = {
        route.route_id: route.policy_dependencies
        for route in router.routes
    }
    audited_dependencies = {
        entry.route_id: entry.policy_dependencies
        for entry in structural.inventory
    }

    assert len(router_dependencies) == 45
    assert router_dependencies.keys() == audited_dependencies.keys()

    for route_id in router_dependencies:
        assert set(router_dependencies[route_id]) == set(
            audited_dependencies[route_id]
        )

    gated = {
        route_id: dependencies
        for route_id, dependencies in router_dependencies.items()
        if dependencies
    }
    assert len(gated) == 19

    incidences = Counter(
        dependency
        for dependencies in gated.values()
        for dependency in dependencies
    )
    assert incidences == Counter(
        {
            "jacoby_continuation_strength": 2,
            "offensive_hand": 4,
            "opponent_suit_shortness": 4,
            "playing_strength": 4,
            "stayman_continuation_strength": 2,
            "stayman_dual_major_response": 1,
            "stopper": 4,
            "suit_quality": 6,
            "support_double_eligibility": 4,
            "takeout_advancer_strength": 4,
        }
    )


def test_policy_gated_matched_route_serializes_structural_dependencies():
    payload = _serialized_bidding(
        "1C",
        "AKQJ.5432.32.432",
    )

    assert payload["capability"] == {
        "type": "bidding-route",
        "id": "sayc.overcall.direct.after.1c",
    }
    assert payload["policy"] == {
        "requirement": "POLICY_GATED",
        "dependencies": (
            "suit_quality",
            "playing_strength",
            "offensive_hand",
            "opponent_suit_shortness",
            "stopper",
        ),
    }

    assert set(payload["policy"]) == {"requirement", "dependencies"}
    assert "consulted" not in payload["policy"]
    assert "applied" not in payload["policy"]
    assert "satisfied" not in payload["policy"]
    assert "selected" not in payload["policy"]


def test_non_policy_route_omits_policy_field():
    payload = _serialized_bidding(
        "",
        "AKQJ.5432.32.432",
    )

    assert payload["capability"] == {
        "type": "bidding-route",
        "id": "sayc.opening",
    }
    assert "policy" not in payload


def test_no_route_omits_policy_field():
    context = _bidding_context("P P P")
    payload = full_deal_analysis_to_dict(
        analyze_full_deal(
            FullDealAnalysisInput(
                requested_stages=(AnalysisStage.AUCTION,),
                bidding=context,
            ),
            bidding_router=BiddingEngineRouter(),
        )
    )["subsystem_results"][0]

    assert "capability" not in payload
    assert "policy" not in payload


def test_two_over_one_major_response_routes_expose_suit_quality_dependency():
    heart = _serialized_bidding("1H P")
    spade = _serialized_bidding("1S P")

    assert heart["policy"] == {
        "requirement": "POLICY_GATED",
        "dependencies": ("suit_quality",),
    }
    assert spade["policy"] == {
        "requirement": "POLICY_GATED",
        "dependencies": ("suit_quality",),
    }
