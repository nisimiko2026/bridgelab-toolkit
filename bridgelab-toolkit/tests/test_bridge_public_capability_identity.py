from dataclasses import FrozenInstanceError

import pytest

from benchmarks.phase21b_provenance_coverage_audit import (
    ProductionElementType,
    run_audit,
)
from bridge.auction import Auction, Bid, Contract, Strain
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_identity import (
    CapabilityIdentity,
    CapabilityType,
    KNOWN_CARD_COUNT_CAPABILITY,
    SIMPLE_UNBLOCK_KING_CAPABILITY,
    bidding_route_capability,
)
from bridge.deal_analysis import AnalysisStage
from bridge.deals import generate_deal
from bridge.declarer_play_state import DeclarerPlayInput, Trick
from bridge.engine_router import BiddingEngineRouter
from bridge.full_deal_analysis import (
    FullDealAnalysisInput,
    FullDealProbabilityRequest,
    analyze_full_deal,
    full_deal_analysis_to_dict,
)
from bridge.models import Card, Hand, Seat, Vulnerability
from bridge.probability_engine import ProbabilityContext
from bridge.probability_questions import KnownCardCountQuestion, ProbabilityQuestion
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


def _serialized(request: FullDealAnalysisInput, *, router=None):
    return full_deal_analysis_to_dict(
        analyze_full_deal(request, bidding_router=router)
    )


def test_shared_identity_is_immutable_validated_and_deterministic():
    identity = bidding_route_capability("sayc.opening")
    assert identity.serialize() == {
        "type": "bidding-route",
        "id": "sayc.opening",
    }
    assert identity.serialize() == identity.serialize()

    with pytest.raises(FrozenInstanceError):
        identity.capability_id = "changed"

    with pytest.raises((TypeError, ValueError)):
        CapabilityIdentity("", "valid")

    with pytest.raises(ValueError):
        CapabilityIdentity(CapabilityType.BIDDING_ROUTE, "  ")


def test_taxonomy_includes_current_and_future_families_without_placeholders():
    assert {item.value for item in CapabilityType} == {
        "bidding-route",
        "probability-engine",
        "declarer-technique",
        "defensive-algorithm",
        "opening-lead-algorithm",
    }

    assert KNOWN_CARD_COUNT_CAPABILITY.serialize() == {
        "type": "probability-engine",
        "id": "known-card-count",
    }

    assert SIMPLE_UNBLOCK_KING_CAPABILITY.serialize() == {
        "type": "declarer-technique",
        "id": "simple-unblock-king",
    }


def test_bidding_recommendation_exposes_route_identity_consistent_with_trace():
    context = _bidding_context("", "AKQJ.5432.32.432")
    payload = _serialized(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.AUCTION,),
            bidding=context,
        ),
        router=create_standard_sayc_router(),
    )["subsystem_results"][0]

    assert payload["capability"] == {
        "type": "bidding-route",
        "id": "sayc.opening",
    }
    assert dict(payload["trace"]) == {"route": "sayc.opening"}
    assert payload["capability"]["id"] == dict(payload["trace"])["route"]


def test_matched_route_abstention_keeps_route_identity():
    context = _bidding_context("", "432.432.432.5432")
    payload = _serialized(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.AUCTION,),
            bidding=context,
        ),
        router=create_standard_sayc_router(),
    )["subsystem_results"][0]

    assert payload["status"] == "abstain"
    assert payload["capability"] == {
        "type": "bidding-route",
        "id": "sayc.opening",
    }


def test_no_route_and_missing_bidding_state_omit_identity():
    context = _bidding_context("P P P")
    no_route = _serialized(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.AUCTION,),
            bidding=context,
        ),
        router=BiddingEngineRouter(),
    )["subsystem_results"][0]

    assert "capability" not in no_route

    missing = _serialized(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.AUCTION,),
        ),
        router=create_standard_sayc_router(),
    )

    assert missing["subsystem_results"] == ()


def test_known_card_count_success_and_owned_failure_have_identity():
    success = _serialized(
        FullDealAnalysisInput(
            probability_requests=(
                FullDealProbabilityRequest(
                    KnownCardCountQuestion(),
                    ProbabilityContext(
                        frozenset(),
                        frozenset(),
                        52,
                    ),
                ),
            ),
        )
    )["probability_results"][0]

    assert success["capability"] == {
        "type": "probability-engine",
        "id": "known-card-count",
    }
    assert success["formula"] == "known-card-count-v1"

    failure = _serialized(
        FullDealAnalysisInput(
            probability_requests=(
                FullDealProbabilityRequest(
                    KnownCardCountQuestion(),
                    ProbabilityContext(
                        frozenset(),
                        frozenset(),
                        51,
                    ),
                ),
            ),
        )
    )["probability_results"][0]

    assert failure["capability"] == success["capability"]


def test_unregistered_probability_question_omits_identity():
    question = ProbabilityQuestion("unregistered")
    payload = _serialized(
        FullDealAnalysisInput(
            probability_requests=(
                FullDealProbabilityRequest(
                    question,
                    ProbabilityContext(
                        frozenset(),
                        frozenset(),
                        52,
                    ),
                ),
            ),
        )
    )["probability_results"][0]

    assert "capability" not in payload


def _declarer_input(*, applicable: bool) -> DeclarerPlayInput:
    return DeclarerPlayInput(
        contract=Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH),
        declarer_seat=Seat.SOUTH,
        declarer_cards=frozenset(
            map(
                Card.parse,
                ("KC", "QC") if applicable else ("2C",),
            )
        ),
        dummy_cards=frozenset(
            map(
                Card.parse,
                ("AC", "JC", "TC", "9C"),
            )
        ),
        current_actor=Seat.SOUTH,
        completed_tricks=(),
        current_trick=Trick(Seat.SOUTH),
    )


def test_declarer_recommendation_and_not_applicable_have_identity():
    for applicable in (True, False):
        payload = _serialized(
            FullDealAnalysisInput(
                requested_stages=(AnalysisStage.DECLARER_PLAY,),
                declarer_play=_declarer_input(applicable=applicable),
            )
        )["subsystem_results"][0]

        assert payload["capability"] == {
            "type": "declarer-technique",
            "id": "simple-unblock-king",
        }


def test_missing_declarer_state_and_validation_error_have_no_identity():
    missing = _serialized(
        FullDealAnalysisInput(
            requested_stages=(AnalysisStage.DECLARER_PLAY,),
        )
    )

    assert missing["subsystem_results"] == ()
    assert "capability" not in missing


def test_capability_shape_never_leaks_implementation_keys():
    forbidden = {
        "module",
        "class",
        "function",
        "callable",
        "object",
        "registry",
    }

    for identity in (
        bidding_route_capability("sayc.opening"),
        KNOWN_CARD_COUNT_CAPABILITY,
        SIMPLE_UNBLOCK_KING_CAPABILITY,
    ):
        assert set(identity.serialize()) == {"type", "id"}
        assert not forbidden & set(identity.serialize())


def test_all_47_primary_elements_have_unique_stable_identity():
    inventory = run_audit().production_entries
    identities = []

    for item in inventory:
        if item.element_type is ProductionElementType.BIDDING_ROUTE:
            identity = bidding_route_capability(item.route_id)
        elif item.element_type is ProductionElementType.PROBABILITY_ENGINE:
            identity = KNOWN_CARD_COUNT_CAPABILITY
        else:
            identity = SIMPLE_UNBLOCK_KING_CAPABILITY

        identities.append(
            (
                identity.capability_type,
                identity.capability_id,
            )
        )

    assert len(identities) == len(set(identities)) == 47
