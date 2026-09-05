from dataclasses import FrozenInstanceError

import pytest

from bridge import (
    AbstentionCode, ActionKind, AnalysisStage, AnalysisStatus, Bid, Card, Contract,
    DealAnalysisContext, DeclarerHandRole, DeclarerPlayInput, DeclarerPlayState,
    DeclarerStateFailureCode, PlayedCard, Seat, Strain, Suit, Trick, Vulnerability,
    analyze_deal_decision, build_declarer_play_state, create_standard_sayc_router,
)
from benchmarks.end_to_end_analysis_architecture import _bidding


ROUTER = create_standard_sayc_router()


def cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def complete_input(**changes) -> DeclarerPlayInput:
    values = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH),
        "declarer_seat": Seat.SOUTH,
        "declarer_cards": cards("AS", "KH", "2C"),
        "dummy_cards": cards("QS", "QH", "3C"),
        "current_actor": Seat.NORTH,
        "completed_tricks": (),
        "current_trick": Trick(Seat.WEST, (PlayedCard(Seat.WEST, Card.parse("2H")),)),
        "vulnerability": Vulnerability.NS,
        "opening_leader": Seat.WEST,
    }
    values.update(changes)
    return DeclarerPlayInput(**values)


def test_state_is_immutable_and_reuses_canonical_types():
    state = build_declarer_play_state(complete_input()).state
    assert state is not None and isinstance(next(iter(state.declarer_cards)), Card)
    assert isinstance(state.current_actor, Seat) and state.current_trick.led_suit is Suit.HEARTS
    with pytest.raises(FrozenInstanceError):
        state.current_actor = Seat.SOUTH


def test_declarer_and_dummy_are_distinct_and_actor_has_authority():
    with pytest.raises(ValueError, match="declarer or dummy"):
        DeclarerPlayState(
            complete_input().contract, cards("AS"), cards("KS"), Seat.EAST, (), Trick(Seat.EAST)
        )


def test_duplicate_visible_card_is_rejected():
    result = build_declarer_play_state(complete_input(dummy_cards=cards("AS", "QH")))
    assert result.failure_code is DeclarerStateFailureCode.INVALID_CARD_STATE


def test_played_card_cannot_remain_in_holding():
    result = build_declarer_play_state(complete_input(dummy_cards=cards("QS", "QH", "2H")))
    assert result.failure_code is DeclarerStateFailureCode.INVALID_CARD_STATE


def test_trick_length_and_clockwise_order_are_validated():
    with pytest.raises(ValueError, match="clockwise"):
        Trick(Seat.WEST, (PlayedCard(Seat.NORTH, Card.parse("2H")),))
    plays = tuple(PlayedCard(seat, Card.parse(card)) for seat, card in zip(Seat, ("2C", "3C", "4C", "5C")))
    with pytest.raises(ValueError, match="more than four"):
        Trick(Seat.NORTH, (*plays, PlayedCard(Seat.NORTH, Card.parse("6C"))))


def test_follow_suit_legal_actions_are_exact():
    state = build_declarer_play_state(complete_input()).state
    assert state is not None and state.legal_actions == (Card.parse("QH"),)
    assert state.follow_suit_required


def test_void_in_led_suit_allows_every_acting_card():
    state = build_declarer_play_state(complete_input(dummy_cards=cards("QS", "3C"))).state
    assert state is not None and set(state.legal_actions) == cards("QS", "3C")
    assert not state.follow_suit_required


def test_declarer_hand_and_dummy_hand_roles_generate_from_correct_holding():
    dummy = build_declarer_play_state(complete_input()).state
    declarer = build_declarer_play_state(complete_input(
        current_actor=Seat.SOUTH, current_trick=Trick(Seat.SOUTH)
    )).state
    assert dummy is not None and dummy.acting_role is DeclarerHandRole.DUMMY_HAND
    assert declarer is not None and declarer.acting_role is DeclarerHandRole.DECLARER_HAND
    assert set(declarer.legal_actions) == cards("AS", "KH", "2C")


def test_complete_context_builds_valid_state():
    result = build_declarer_play_state(complete_input())
    assert result.is_ready and result.failure_code is None


@pytest.mark.parametrize(("change", "code"), [
    ({"dummy_cards": None}, DeclarerStateFailureCode.MISSING_DUMMY_HAND),
    ({"contract": None}, DeclarerStateFailureCode.MISSING_CONTRACT),
    ({"declarer_seat": None}, DeclarerStateFailureCode.MISSING_DECLARER_SEAT),
    ({"declarer_cards": None}, DeclarerStateFailureCode.MISSING_DECLARER_HAND),
    ({"current_actor": None}, DeclarerStateFailureCode.MISSING_CURRENT_ACTOR),
    ({"completed_tricks": None}, DeclarerStateFailureCode.MISSING_PLAY_HISTORY),
])
def test_missing_fields_produce_structured_failures(change, code):
    assert build_declarer_play_state(complete_input(**change)).failure_code is code


def test_valid_state_does_not_report_missing_state():
    actual = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=complete_input()),
        bidding_router=ROUTER,
    )
    assert actual.status is AnalysisStatus.NO_DECISION
    assert actual.abstention_code is not AbstentionCode.MISSING_STATE
    assert actual.action.kind is ActionKind.NONE and actual.action.card is None


def test_incomplete_state_preserves_precise_reason():
    actual = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=complete_input(dummy_cards=None)),
        bidding_router=ROUTER,
    )
    assert actual.abstention_code is AbstentionCode.MISSING_STATE
    assert actual.debug_metadata == (("declarer-state", "missing-dummy-hand"),)


def test_known_card_accounting_and_trick_number_are_derived():
    state = build_declarer_play_state(complete_input()).state
    assert state is not None
    assert len(state.visible_cards) == 6 and len(state.played_cards) == 1
    assert state.unknown_card_count == 45 and state.trick_number == 1


def test_trick_winner_supports_notrump_and_trump():
    trick = Trick(Seat.NORTH, (
        PlayedCard(Seat.NORTH, Card.parse("AH")), PlayedCard(Seat.EAST, Card.parse("2S")),
        PlayedCard(Seat.SOUTH, Card.parse("KH")), PlayedCard(Seat.WEST, Card.parse("3H")),
    ))
    assert trick.winner(None) is Seat.NORTH
    assert trick.winner(Suit.SPADES) is Seat.EAST


def test_repeated_build_is_structurally_identical():
    assert build_declarer_play_state(complete_input()) == build_declarer_play_state(complete_input())


def test_bidding_pipeline_and_route_count_are_unchanged():
    actual = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    assert actual.action.bid.serialize() == "2S"
    assert len(ROUTER.routes) == 45
