from pathlib import Path

from benchmarks.end_to_end_analysis_architecture import _bidding
from bridge import (
    AbstentionCode, ActionKind, AnalysisStage, AnalysisStatus, Bid, Card, Contract,
    DealAnalysisContext, DeclarerPlayInput, DeclarerRecommendationReason,
    DeclarerRecommendationStatus, DeclarerTechnique, PlayedCard, Seat, Strain,
    Trick, UNBLOCK_SOURCE, analyze_deal_decision, build_declarer_play_state,
    create_standard_sayc_router, evaluate_declarer_play,
)


ROUTER = create_standard_sayc_router()


def cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def source_input(**changes) -> DeclarerPlayInput:
    values = {
        "contract": Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH),
        "declarer_seat": Seat.SOUTH,
        "declarer_cards": cards("KC", "QC", "2S"),
        "dummy_cards": cards("AC", "JC", "TC", "9C", "3S"),
        "current_actor": Seat.SOUTH,
        "completed_tricks": (),
        "current_trick": Trick(Seat.SOUTH),
    }
    values.update(changes)
    return DeclarerPlayInput(**values)


def direct(**changes):
    state = build_declarer_play_state(source_input(**changes)).state
    assert state is not None
    return state, evaluate_declarer_play(state)


def top(**changes):
    return analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=source_input(**changes)),
        bidding_router=ROUTER,
    )


def test_selected_technique_has_exact_frozen_source():
    root = Path(__file__).parents[2]
    text = (root / "knowledge/play/declarer-play/general-techniques/unblock.md").read_text(encoding="utf-8")
    assert "Cash the ♣K." in text and "Cash the ♣Q." in text
    assert UNBLOCK_SOURCE.article_id == "play/declarer-play/general-techniques/unblock"
    assert UNBLOCK_SOURCE.heading == "Example 1 – Simple Unblock"


def test_source_classification_is_executable_and_exact_card_is_king():
    state, result = direct()
    assert result.status is DeclarerRecommendationStatus.RECOMMENDATION
    assert result.technique is DeclarerTechnique.SIMPLE_UNBLOCK_KING
    assert result.card == Card.parse("KC") and result.card in state.legal_actions


def test_top_level_normalizes_card_play_and_source_evidence():
    result = top()
    assert result.status is AnalysisStatus.RECOMMENDATION
    assert result.action.kind is ActionKind.CARD_PLAY and result.action.card == Card.parse("KC")
    assert result.evidence[0].source == UNBLOCK_SOURCE


def test_same_geometry_from_dummy_is_outside_exact_source_scope():
    _, result = direct(
        declarer_cards=cards("AC", "JC", "TC", "9C", "2S"),
        dummy_cards=cards("KC", "QC", "3S"), current_actor=Seat.NORTH,
        current_trick=Trick(Seat.NORTH),
    )
    assert result.reason is DeclarerRecommendationReason.TECHNIQUE_NOT_APPLICABLE


def test_one_rank_near_miss_abstains():
    _, result = direct(declarer_cards=cards("KC", "8C", "2S"))
    assert not result.has_recommendation


def test_missing_required_king_abstains():
    _, result = direct(declarer_cards=cards("QC", "2S"))
    assert result.reason is DeclarerRecommendationReason.TECHNIQUE_NOT_APPLICABLE


def test_extra_suit_card_breaks_exact_geometry():
    _, result = direct(declarer_cards=cards("KC", "QC", "2C", "2S"))
    assert not result.has_recommendation


def test_two_matching_suits_are_ambiguous():
    _, result = direct(
        declarer_cards=cards("KC", "QC", "KD", "QD"),
        dummy_cards=cards("AC", "JC", "TC", "9C", "AD", "JD", "TD", "9D"),
    )
    assert result.reason is DeclarerRecommendationReason.AMBIGUOUS_ACTION


def test_nonempty_trick_and_follow_suit_constraint_abstain():
    trick = Trick(Seat.WEST, (
        PlayedCard(Seat.WEST, Card.parse("2H")), PlayedCard(Seat.NORTH, Card.parse("3H")),
        PlayedCard(Seat.EAST, Card.parse("4H")),
    ))
    _, result = direct(current_trick=trick)
    assert not result.has_recommendation


def test_suit_contract_is_outside_notrump_source_boundary():
    _, result = direct(contract=Contract(Bid(3, Strain.HEARTS), Seat.SOUTH))
    assert not result.has_recommendation


def test_unrelated_position_has_no_fallback_heuristic():
    result = top(declarer_cards=cards("AS", "KH", "2C"), dummy_cards=cards("QS", "QH", "3C"))
    assert result.status is AnalysisStatus.NO_DECISION
    assert result.action.card is None
    assert result.abstention_code is AbstentionCode.TECHNIQUE_NOT_APPLICABLE


def test_incomplete_state_preserves_phase13c_diagnostic():
    result = top(dummy_cards=None)
    assert result.status is AnalysisStatus.NO_DECISION
    assert result.abstention_code is AbstentionCode.MISSING_STATE
    assert result.debug_metadata == (("declarer-state", "missing-dummy-hand"),)


def test_explanation_trace_and_repeated_analysis_are_deterministic():
    first, second = top(), top()
    assert first == second
    assert "Simple Unblock" in first.explanation and "KC" in first.explanation
    assert first.debug_metadata == (("technique", "simple-unblock-king"), ("card", "KC"))
    assert not hasattr(first, "confidence")


def test_phase12n_and_auction_behavior_are_unchanged():
    opening = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    strong = analyze_deal_decision(_bidding("AKQ.AKQ.Q74.Q843", ("2C", "P", "2D", "P")), bidding_router=ROUTER)
    assert opening.action.bid.serialize() == "2S"
    assert strong.action.bid.serialize() == "2NT"
    assert len(ROUTER.routes) == 45
