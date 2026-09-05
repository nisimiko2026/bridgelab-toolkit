from dataclasses import FrozenInstanceError

import pytest

from benchmarks.end_to_end_analysis_architecture import _bidding
from bridge import (
    AbstentionCode, ActionKind, AnalysisStage, AnalysisStatus, Bid, Card, Contract,
    DealAnalysisContext, DefensivePlayInput, DefensivePlayState, DefensiveStateFailureCode,
    PlayedCard, Seat, Strain, Trick, analyze_deal_decision,
    build_defensive_play_state, build_defensive_probability_context,
    create_standard_sayc_router, evaluate_declarer_play, evaluate_probability,
    KnownCardCountQuestion,
)
from tests.test_bridge_phase13e_probability_evidence_adapter import state as declarer_state


ROUTER = create_standard_sayc_router()


def cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def defensive_input(**changes) -> DefensivePlayInput:
    values = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), "declarer_seat": Seat.SOUTH,
        "defender_cards": cards("AH", "5H", "2C"), "dummy_cards": cards("KH", "QS", "3C"),
        "current_actor": Seat.EAST, "completed_tricks": (),
        "current_trick": Trick(Seat.NORTH, (PlayedCard(Seat.NORTH, Card.parse("2H")),)),
        "opening_leader": Seat.WEST,
    }
    values.update(changes)
    return DefensivePlayInput(**values)


def build(**changes):
    return build_defensive_play_state(defensive_input(**changes))


def test_defensive_state_is_immutable_and_reuses_canonical_types():
    actual = build().state
    assert actual is not None and isinstance(actual, DefensivePlayState)
    assert isinstance(next(iter(actual.defender_cards)), Card)
    assert isinstance(actual.current_actor, Seat) and isinstance(actual.contract, Contract)
    assert isinstance(actual.current_trick, Trick) and isinstance(actual.current_trick.plays[0], PlayedCard)
    with pytest.raises(FrozenInstanceError):
        actual.current_actor = Seat.WEST


def test_actor_cannot_be_declarer_or_dummy():
    assert build(current_actor=Seat.SOUTH).failure_code is DefensiveStateFailureCode.ACTOR_IS_DECLARER
    assert build(current_actor=Seat.NORTH).failure_code is DefensiveStateFailureCode.ACTOR_IS_DUMMY


def test_partner_and_seats_are_derived():
    actual = build().state
    assert actual is not None
    assert actual.declarer is Seat.SOUTH and actual.dummy is Seat.NORTH
    assert actual.current_actor is Seat.EAST and actual.partner is Seat.WEST


def test_dummy_visibility_and_information_boundary_are_explicit():
    actual = build().state
    assert actual is not None and actual.dummy_cards == cards("KH", "QS", "3C")
    assert not hasattr(actual, "partner_cards") and not hasattr(actual, "declarer_cards")


def test_duplicate_and_played_card_conflicts_are_rejected():
    assert build(dummy_cards=cards("AH", "QS")).failure_code is DefensiveStateFailureCode.INVALID_CARD_STATE
    assert build(defender_cards=cards("AH", "5H", "2H")).failure_code is DefensiveStateFailureCode.INVALID_CARD_STATE


def test_current_trick_order_is_structured_invalid():
    result = build(current_actor=Seat.WEST)
    assert result.failure_code is DefensiveStateFailureCode.INCONSISTENT_TRICK_ORDER


def test_follow_suit_legal_cards_are_exact():
    actual = build().state
    assert actual is not None
    assert actual.legal_actions == (Card.parse("AH"), Card.parse("5H"))
    assert actual.follow_suit_required


def test_void_defender_may_play_every_held_card():
    actual = build(defender_cards=cards("AS", "2C")).state
    assert actual is not None and set(actual.legal_actions) == cards("AS", "2C")
    assert not actual.follow_suit_required


def test_second_third_and_fourth_hand_states_build():
    second = build().state
    third = build(current_trick=Trick(Seat.WEST, (
        PlayedCard(Seat.WEST, Card.parse("2H")), PlayedCard(Seat.NORTH, Card.parse("3H")),
    )), dummy_cards=cards("KH", "QS", "3C")).state
    fourth = build(current_actor=Seat.WEST, current_trick=Trick(Seat.NORTH, (
        PlayedCard(Seat.NORTH, Card.parse("2H")), PlayedCard(Seat.EAST, Card.parse("3H")),
        PlayedCard(Seat.SOUTH, Card.parse("4H")),
    )), defender_cards=cards("AH", "5H", "2C"), dummy_cards=cards("KH", "QS", "3C")).state
    assert second is not None and third is not None and fourth is not None


def test_later_trick_history_and_counts_are_derived():
    completed = Trick(Seat.NORTH, (
        PlayedCard(Seat.NORTH, Card.parse("2S")), PlayedCard(Seat.EAST, Card.parse("AS")),
        PlayedCard(Seat.SOUTH, Card.parse("3S")), PlayedCard(Seat.WEST, Card.parse("4S")),
    ))
    actual = build(completed_tricks=(completed,)).state
    assert actual is not None and actual.trick_number == 2
    assert (actual.declarer_tricks, actual.defender_tricks) == (0, 1)


@pytest.mark.parametrize(("change", "code"), [
    ({"contract": None}, DefensiveStateFailureCode.MISSING_CONTRACT),
    ({"declarer_seat": None}, DefensiveStateFailureCode.MISSING_DECLARER_SEAT),
    ({"defender_cards": None}, DefensiveStateFailureCode.MISSING_DEFENDER_HAND),
    ({"dummy_cards": None}, DefensiveStateFailureCode.MISSING_DUMMY_HAND),
    ({"current_actor": None}, DefensiveStateFailureCode.MISSING_CURRENT_ACTOR),
    ({"completed_tricks": None}, DefensiveStateFailureCode.MISSING_PLAY_HISTORY),
])
def test_missing_fields_have_structured_reasons(change, code):
    assert build(**change).failure_code is code


def test_valid_top_level_state_has_no_engine_not_missing_state():
    result = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DEFENSIVE_PLAY, defensive_play=defensive_input()),
        bidding_router=ROUTER,
    )
    assert result.status is AnalysisStatus.NO_DECISION and result.action.kind is ActionKind.NONE
    assert result.action.card is None and result.abstention_code is AbstentionCode.ENGINE_UNAVAILABLE
    assert result.debug_metadata == (("defensive-state", "ready"),)


def test_incomplete_top_level_state_preserves_precise_missing_reason():
    result = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DEFENSIVE_PLAY, defensive_play=defensive_input(dummy_cards=None)),
        bidding_router=ROUTER,
    )
    assert result.abstention_code is AbstentionCode.MISSING_STATE
    assert result.debug_metadata == (("defensive-state", "missing-dummy-hand"),)


def test_probability_context_contains_only_defender_known_facts():
    actual = build().state
    assert actual is not None
    context = build_defensive_probability_context(actual)
    assert len(context.visible_cards) == 6 and len(context.played_cards) == 1
    assert context.unknown_card_count == 45 and not hasattr(context, "defender_hands")
    assert evaluate_probability(KnownCardCountQuestion(), context=context).evidence[0].result == "45"


def test_construction_is_deterministic():
    assert build() == build()


def test_declarer_probability_and_auction_guards_are_unchanged():
    assert evaluate_declarer_play(declarer_state()).card == Card.parse("KC")
    assert evaluate_probability(KnownCardCountQuestion(), declarer_state()).evidence[0].result == "44"
    opening = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    assert opening.action.bid.serialize() == "2S" and len(ROUTER.routes) == 45


def test_opening_lead_remains_distinct_with_its_own_missing_state():
    result = analyze_deal_decision(DealAnalysisContext(AnalysisStage.OPENING_LEAD), bidding_router=ROUTER)
    assert result.stage is AnalysisStage.OPENING_LEAD and result.action.kind is ActionKind.NONE
    assert result.abstention_code is AbstentionCode.MISSING_STATE
