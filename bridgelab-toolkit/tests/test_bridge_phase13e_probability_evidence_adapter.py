from dataclasses import FrozenInstanceError

import pytest

from benchmarks.end_to_end_analysis_architecture import _bidding
from bridge import (
    ActionKind, AnalysisStage, Bid, Card, Contract, DealAnalysisContext,
    DeclarerPlayInput, DeclarerRecommendation, DeclarerRecommendationStatus,
    DeclarerTechnique, KnownCardCountQuestion, ProbabilityEvidenceFailureCode,
    ProbabilityEvidenceStatus, ProbabilityEvidenceType, Seat, Strain, Trick,
    analyze_deal_decision, build_declarer_play_state,
    collect_declarer_probability_evidence, create_standard_sayc_router,
    evaluate_declarer_play,
)


ROUTER = create_standard_sayc_router()


def cards(*values: str) -> frozenset[Card]:
    return frozenset(Card.parse(value) for value in values)


def play_input() -> DeclarerPlayInput:
    return DeclarerPlayInput(
        contract=Contract(Bid(3, Strain.NOTRUMP), Seat.SOUTH), declarer_seat=Seat.SOUTH,
        declarer_cards=cards("KC", "QC", "2S"), dummy_cards=cards("AC", "JC", "TC", "9C", "3S"),
        current_actor=Seat.SOUTH, completed_tricks=(), current_trick=Trick(Seat.SOUTH),
    )


def state():
    actual = build_declarer_play_state(play_input()).state
    assert actual is not None
    return actual


def evidence_result():
    return collect_declarer_probability_evidence(state(), KnownCardCountQuestion())


def test_probability_evidence_model_is_immutable():
    item = evidence_result().evidence[0]
    with pytest.raises(FrozenInstanceError):
        item.result = "0"


def test_only_existing_known_card_count_type_is_defined():
    assert tuple(ProbabilityEvidenceType) == (ProbabilityEvidenceType.KNOWN_CARD_COUNT,)


def test_existing_state_accounting_is_reused_without_new_math():
    actual_state = state()
    item = evidence_result().evidence[0]
    assert item.result == str(actual_state.unknown_card_count) == "44"
    assert item.known_facts == (("visible-cards", "8"), ("played-cards", "0"))


def test_exact_not_simulated_and_no_fake_precision():
    item = evidence_result().evidence[0]
    assert item.deterministic and not item.simulated
    assert item.probability is None and item.alternatives == () and item.sample_size is None
    assert not hasattr(item, "confidence") and not hasattr(item, "confidence_interval")


def test_assumptions_preserve_partial_information_boundary():
    item = evidence_result().evidence[0]
    assert "Hidden defender cards and distributions remain unknown." in item.assumptions
    assert all("defender-hand" not in key for key, _ in item.known_facts)


def test_computational_count_does_not_fabricate_source():
    assert evidence_result().evidence[0].source is None


def test_missing_question_is_structured_unavailable():
    result = collect_declarer_probability_evidence(state(), None)
    assert result.status is ProbabilityEvidenceStatus.UNAVAILABLE
    assert result.failure_code is ProbabilityEvidenceFailureCode.MISSING_QUESTION
    assert result.evidence == ()


def test_missing_state_is_structured_unavailable_not_zero_probability():
    result = collect_declarer_probability_evidence(None, KnownCardCountQuestion())
    assert result.failure_code is ProbabilityEvidenceFailureCode.INSUFFICIENT_KNOWN_CARDS
    assert result.evidence == () and "0%" not in result.explanation


def test_blank_question_is_rejected():
    with pytest.raises(ValueError, match="must not be blank"):
        KnownCardCountQuestion(" ")


def test_repeated_exact_evidence_is_structurally_identical():
    assert evidence_result() == evidence_result()


def test_simple_unblock_behavior_and_empty_probability_evidence_are_unchanged():
    recommendation = evaluate_declarer_play(state())
    assert recommendation.card == Card.parse("KC")
    assert recommendation.technique is DeclarerTechnique.SIMPLE_UNBLOCK_KING
    assert recommendation.probability_evidence == ()


def test_recommendation_result_can_carry_probability_evidence():
    item = evidence_result().evidence[0]
    result = DeclarerRecommendation(
        DeclarerRecommendationStatus.RECOMMENDATION, Card.parse("KC"), "fixture",
        DeclarerTechnique.SIMPLE_UNBLOCK_KING, probability_evidence=(item,),
    )
    assert result.probability_evidence == (item,)


def test_top_level_preserves_demand_driven_attached_probability_evidence():
    item = evidence_result().evidence[0]

    def evaluator(_state):
        return DeclarerRecommendation(
            DeclarerRecommendationStatus.RECOMMENDATION, Card.parse("KC"), "fixture",
            DeclarerTechnique.SIMPLE_UNBLOCK_KING, probability_evidence=(item,),
        )

    result = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=play_input()),
        bidding_router=ROUTER, declarer_evaluator=evaluator,
    )
    assert result.action.kind is ActionKind.CARD_PLAY
    assert result.probability_evidence == (item,)


def test_default_top_level_does_not_run_probability_adapter_automatically():
    result = analyze_deal_decision(
        DealAnalysisContext(AnalysisStage.DECLARER_PLAY, declarer_play=play_input()), bidding_router=ROUTER
    )
    assert result.probability_evidence == ()


def test_bidding_and_phase12n_are_unchanged():
    ordinary = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    strong = analyze_deal_decision(
        _bidding("AKQ.AKQ.Q74.Q843", ("2C", "P", "2D", "P")), bidding_router=ROUTER
    )
    assert ordinary.action.bid.serialize() == "2S" and strong.action.bid.serialize() == "2NT"
    assert len(ROUTER.routes) == 45
