from dataclasses import FrozenInstanceError

import pytest

from benchmarks.end_to_end_analysis_architecture import _bidding
from bridge import (
    AbstentionCode, ActionKind, AnalysisStage, AnalysisStatus, Auction, Bid, Card,
    Contract, DealAnalysisContext, Doubling, Hand, KnownCardCountQuestion,
    OpeningLeadInput, OpeningLeadState, OpeningLeadStateFailureCode, Seat, Strain,
    Suit, Vulnerability, analyze_deal_decision, build_defensive_play_state,
    build_opening_lead_probability_context, build_opening_lead_state,
    create_standard_sayc_router, evaluate_declarer_play, evaluate_probability,
)
from tests.test_bridge_phase13e_probability_evidence_adapter import state as declarer_state
from tests.test_bridge_phase13g_defensive_state_architecture import defensive_input


ROUTER = create_standard_sayc_router()
BALANCED = Hand.parse("KJ72.Q83.T94.762")


def lead_input(**changes) -> OpeningLeadInput:
    values = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH),
        "declarer_seat": Seat.SOUTH, "opening_leader_seat": Seat.WEST,
        "opening_leader_hand": BALANCED, "vulnerability": Vulnerability.NS,
    }
    values.update(changes)
    return OpeningLeadInput(**values)


def build(**changes):
    return build_opening_lead_state(lead_input(**changes))


def test_opening_lead_state_is_immutable_and_reuses_canonical_types():
    actual = build().state
    assert actual is not None and isinstance(actual, OpeningLeadState)
    assert isinstance(actual.contract, Contract) and isinstance(actual.opening_leader_hand, Hand)
    assert isinstance(actual.legal_leads[0], Card) and isinstance(actual.suit_lengths[0][0], Suit)
    with pytest.raises(FrozenInstanceError):
        actual.opening_leader = Seat.EAST


def test_leader_and_partner_are_derived_and_validated():
    actual = build().state
    assert actual is not None
    assert actual.declarer is Seat.SOUTH and actual.opening_leader is Seat.WEST
    assert actual.partner is Seat.EAST
    assert build(opening_leader_seat=Seat.EAST).failure_code is OpeningLeadStateFailureCode.INVALID_LEADER_SEAT


def test_no_hidden_hand_is_required_or_represented():
    actual = build().state
    assert actual is not None
    assert not hasattr(actual, "dummy_cards")
    assert not hasattr(actual, "declarer_cards")
    assert not hasattr(actual, "partner_cards")


def test_legal_leads_are_all_thirteen_cards_without_follow_suit_filter():
    actual = build().state
    assert actual is not None
    assert set(actual.legal_leads) == BALANCED.cards and len(actual.legal_leads) == 13
    assert not hasattr(actual, "current_trick") and not hasattr(actual, "follow_suit_required")


def test_canonical_hand_rejects_duplicate_or_empty_card_state():
    with pytest.raises(ValueError):
        Hand.from_cards((Card.parse("AS"), Card.parse("AS")))
    with pytest.raises(ValueError):
        Hand.from_cards(())


def test_auction_is_snapshotted_without_interpretation():
    auction = Auction(Seat.SOUTH, ("3NT", "P", "P", "P"))
    actual = build(auction=auction).state
    assert actual is not None and actual.auction_entries == auction.entries
    assert not hasattr(actual, "implied_shape") and not hasattr(actual, "lead_preference")


def test_inconsistent_auction_contract_is_structured_invalid():
    auction = Auction(Seat.SOUTH, ("3NT", "P", "P", "P"))
    result = build(contract=Contract(Bid(4, Strain.HEARTS), Seat.SOUTH), auction=auction)
    assert result.failure_code is OpeningLeadStateFailureCode.INCONSISTENT_CONTRACT_AUCTION


def test_contract_doubling_vulnerability_and_hand_features_are_preserved():
    contract = Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH, Doubling.DOUBLED)
    actual = build(contract=contract).state
    assert actual is not None
    assert actual.contract.doubling is Doubling.DOUBLED and actual.vulnerability is Vulnerability.NS
    assert dict(actual.suit_lengths)[Suit.SPADES] == 4
    assert Card.parse("KS") in dict(actual.honor_holdings)[Suit.SPADES]


def test_known_card_accounting_excludes_dummy_and_other_hidden_hands():
    actual = build().state
    assert actual is not None
    assert actual.known_cards == BALANCED.cards and actual.unknown_card_count == 39


def test_probability_context_contains_only_pre_dummy_facts():
    actual = build().state
    assert actual is not None
    context = build_opening_lead_probability_context(actual)
    assert context.visible_cards == BALANCED.cards and context.played_cards == frozenset()
    assert context.unknown_card_count == 39
    assert evaluate_probability(KnownCardCountQuestion(), context=context).evidence[0].result == "39"


@pytest.mark.parametrize(("change", "code"), [
    ({"contract": None}, OpeningLeadStateFailureCode.MISSING_CONTRACT),
    ({"declarer_seat": None}, OpeningLeadStateFailureCode.MISSING_DECLARER),
    ({"opening_leader_seat": None}, OpeningLeadStateFailureCode.MISSING_LEADER_SEAT),
    ({"opening_leader_hand": None}, OpeningLeadStateFailureCode.MISSING_LEADER_HAND),
    ({"require_auction": True}, OpeningLeadStateFailureCode.MISSING_REQUIRED_AUCTION),
])
def test_missing_inputs_have_precise_structured_reasons(change, code):
    assert build(**change).failure_code is code


def test_valid_top_level_state_has_no_engine_and_no_card():
    result = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.OPENING_LEAD, opening_lead=lead_input()), bidding_router=ROUTER
    )
    assert result.status is AnalysisStatus.NO_DECISION and result.action.kind is ActionKind.NONE
    assert result.action.card is None and result.abstention_code is AbstentionCode.ENGINE_UNAVAILABLE
    assert result.debug_metadata == (("opening-lead-state", "ready"),)


def test_incomplete_top_level_state_is_precise_missing_state():
    result = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.OPENING_LEAD, opening_lead=lead_input(opening_leader_hand=None)),
        bidding_router=ROUTER,
    )
    assert result.abstention_code is AbstentionCode.MISSING_STATE
    assert result.debug_metadata == (("opening-lead-state", "missing-leader-hand"),)


def test_opening_lead_and_defensive_play_remain_distinct():
    lead = build().state
    defense = build_defensive_play_state(defensive_input()).state
    assert lead is not None and defense is not None
    assert not hasattr(lead, "dummy_cards") and hasattr(defense, "dummy_cards")
    assert not hasattr(lead, "current_trick") and defense.current_trick.plays


def test_repeated_construction_is_structurally_identical():
    assert build() == build()


def test_declarer_probability_defense_and_auction_guards_are_unchanged():
    assert evaluate_declarer_play(declarer_state()).card == Card.parse("KC")
    assert evaluate_probability(KnownCardCountQuestion(), declarer_state()).evidence[0].result == "44"
    defense = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DEFENSIVE_PLAY, defensive_play=defensive_input()), bidding_router=ROUTER
    )
    assert defense.abstention_code is AbstentionCode.ENGINE_UNAVAILABLE
    opening = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    assert opening.action.bid.serialize() == "2S" and len(ROUTER.routes) == 45
