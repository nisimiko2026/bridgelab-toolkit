from dataclasses import FrozenInstanceError

import pytest

from benchmarks.end_to_end_analysis_architecture import _bidding
from bridge import (
    CalculationMode, Card, DEFAULT_PROBABILITY_ENGINE_REGISTRY, FormulaIdentifier,
    KnownCardCountQuestion, MonteCarloQuestion, ProbabilityContext,
    ProbabilityEngineFailureCode, ProbabilityEngineStatus, ProbabilityEvidenceStatus,
    RestrictedChoiceQuestion, Suit, SuitDistributionQuestion, TrumpBreakQuestion,
    VacantPlacesQuestion, analyze_deal_decision, collect_declarer_probability_evidence,
    create_standard_sayc_router, evaluate_declarer_play, evaluate_probability,
)
from tests.test_bridge_phase13e_probability_evidence_adapter import state


ROUTER = create_standard_sayc_router()


def test_question_models_are_immutable():
    question = KnownCardCountQuestion()
    with pytest.raises(FrozenInstanceError):
        question.subject = "changed"


def test_question_variants_capture_only_explicit_inputs():
    assert RestrictedChoiceQuestion("honor choice", Suit.CLUBS).observed_play == ()
    assert VacantPlacesQuestion("seat capacity", Suit.HEARTS).known_seat_constraints == ()
    assert SuitDistributionQuestion("club split", Suit.CLUBS, 5).cards_outstanding == 5
    assert TrumpBreakQuestion("trump split", Suit.SPADES, 5).candidate_distributions == ()
    assert MonteCarloQuestion("line simulation", seed=7, trials=100).seed == 7


def test_registry_contains_only_existing_known_card_engine():
    assert DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types == ("KnownCardCountQuestion",)


def test_known_card_engine_preserves_8_0_44_result():
    result = evaluate_probability(KnownCardCountQuestion(), state())
    assert result.status is ProbabilityEngineStatus.SUCCESS
    assert result.evidence[0].result == "44"
    assert result.evidence[0].known_facts == (("visible-cards", "8"), ("played-cards", "0"))


def test_known_card_engine_is_exact_with_real_formula_identifier():
    result = evaluate_probability(KnownCardCountQuestion(), state())
    assert result.mode is CalculationMode.EXACT
    assert result.formula_id is FormulaIdentifier.KNOWN_CARD_COUNT_V1
    assert result.evidence[0].probability is None and not result.evidence[0].simulated


def test_trace_is_compact_deterministic_metadata():
    first = evaluate_probability(KnownCardCountQuestion(), state())
    second = evaluate_probability(KnownCardCountQuestion(), state())
    assert first == second
    assert first.trace == (("deck-size", "52"), ("known-unique", "8"), ("unknown", "44"))


def test_probability_context_uses_no_hidden_defender_hands():
    result = evaluate_probability(KnownCardCountQuestion(), state())
    assert "Hidden defender cards and distributions remain unknown." in result.evidence[0].assumptions
    assert not hasattr(result, "defender_hands")


def test_invalid_accounting_is_structured_invalid_input():
    context = ProbabilityContext(frozenset({Card.parse("AS")}), frozenset(), 49)
    result = evaluate_probability(KnownCardCountQuestion(), context=context)
    assert result.status is ProbabilityEngineStatus.INVALID_INPUT
    assert result.failure_code is ProbabilityEngineFailureCode.INVALID_CARD_ACCOUNTING
    assert result.evidence == ()


def test_missing_state_is_structured_unavailable():
    result = evaluate_probability(KnownCardCountQuestion())
    assert result.status is ProbabilityEngineStatus.UNAVAILABLE
    assert result.failure_code is ProbabilityEngineFailureCode.INSUFFICIENT_STATE


@pytest.mark.parametrize("question", [
    RestrictedChoiceQuestion("restricted choice", Suit.CLUBS),
    VacantPlacesQuestion("vacant places", Suit.CLUBS),
    SuitDistributionQuestion("suit distribution", Suit.CLUBS, 5),
    TrumpBreakQuestion("trump break", Suit.SPADES, 5),
    MonteCarloQuestion("simulation", seed=1, trials=100),
])
def test_unimplemented_families_are_structured_unavailable(question):
    result = evaluate_probability(question, state())
    assert result.status is ProbabilityEngineStatus.UNAVAILABLE
    assert result.failure_code is ProbabilityEngineFailureCode.ENGINE_NOT_REGISTERED
    assert result.evidence == () and result.mode is None and result.formula_id is None
    assert "probability" not in result.explanation.casefold() or "%" not in result.explanation


def test_backward_compatible_evidence_adapter_uses_engine():
    result = collect_declarer_probability_evidence(state(), KnownCardCountQuestion())
    assert result.status is ProbabilityEvidenceStatus.AVAILABLE
    assert result.evidence[0].result == "44"


def test_adapter_returns_structured_unavailable_for_future_question():
    result = collect_declarer_probability_evidence(
        state(), RestrictedChoiceQuestion("restricted choice", Suit.CLUBS)
    )
    assert result.status is ProbabilityEvidenceStatus.UNAVAILABLE
    assert result.failure_code.value == "unsupported-evidence-type"
    assert result.evidence == ()


def test_simple_unblock_and_top_level_bidding_are_unchanged():
    recommendation = evaluate_declarer_play(state())
    assert recommendation.card == Card.parse("KC") and recommendation.probability_evidence == ()
    opening = analyze_deal_decision(_bidding("KQJ876.32.43.543"), bidding_router=ROUTER)
    assert opening.action.bid.serialize() == "2S" and len(ROUTER.routes) == 45


def test_no_speculative_formula_identifiers_exist():
    assert tuple(FormulaIdentifier) == (FormulaIdentifier.KNOWN_CARD_COUNT_V1,)
