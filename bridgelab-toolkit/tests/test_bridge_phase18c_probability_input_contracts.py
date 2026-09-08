from __future__ import annotations

import inspect

import pytest

from benchmarks.phase16_coverage_closure_audit import (
    run_phase16_coverage_closure_audit,
)
from bridge import (
    Card,
    DEFAULT_PROBABILITY_ENGINE_REGISTRY,
    FormulaIdentifier,
    PlayedCard,
    ProbabilityContext,
    ProbabilityEngineFailureCode,
    ProbabilityEngineStatus,
    PublicCardOwnership,
    PublicEvidence,
    PublicEvidenceKind,
    RestrictedChoiceObservationStatus,
    RestrictedChoiceQuestion,
    Seat,
    Suit,
    VacantPlacesQuestion,
    build_restricted_choice_question,
    build_vacant_places_question_from_play_history,
    create_standard_sayc_router,
    evaluate_probability,
    full_deck,
    generate_deal,
)


OBSERVED = PlayedCard(Seat.EAST, Card.parse("KC"))
BASIS = (PublicEvidence(PublicEvidenceKind.PLAYED_CARD, 0),)


def _restricted(
    choice_sets: tuple[frozenset[Card], ...] = (),
) -> RestrictedChoiceQuestion:
    return RestrictedChoiceQuestion(
        "restricted choice",
        Suit.CLUBS,
        Seat.EAST,
        OBSERVED,
        (),
        choice_sets,
        BASIS if choice_sets else (),
        Seat.NORTH,
    )


def _ownership(seat: Seat, card: str) -> PublicCardOwnership:
    return PublicCardOwnership(seat, Card.parse(card), BASIS[0])


def test_restricted_choice_forced_is_formula_neutral() -> None:
    question = _restricted((frozenset({OBSERVED.card}),))
    assert question.observation_status is RestrictedChoiceObservationStatus.FORCED
    assert not hasattr(question, "probability")
    assert not hasattr(question, "recommendation")


def test_restricted_choice_optional_requires_multiple_established_choices() -> None:
    question = _restricted((frozenset({OBSERVED.card, Card.parse("QC")}),))
    assert question.observation_status is RestrictedChoiceObservationStatus.OPTIONAL


def test_restricted_choice_ambiguous_preserves_incompatible_interpretations() -> None:
    question = _restricted(
        (
            frozenset({OBSERVED.card}),
            frozenset({OBSERVED.card, Card.parse("QC")}),
        )
    )
    assert question.observation_status is RestrictedChoiceObservationStatus.AMBIGUOUS


def test_restricted_choice_without_choice_evidence_is_insufficient() -> None:
    assert _restricted().observation_status is RestrictedChoiceObservationStatus.INSUFFICIENT


def test_restricted_choice_rejects_duplicate_physical_card() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        RestrictedChoiceQuestion(
            "duplicate", Suit.CLUBS, Seat.EAST, OBSERVED, (OBSERVED,)
        )


def test_restricted_choice_rejects_defender_seat_mismatch() -> None:
    with pytest.raises(ValueError, match="match observed defender"):
        RestrictedChoiceQuestion(
            "mismatch", Suit.CLUBS, Seat.WEST, OBSERVED
        )


def test_restricted_choice_rejects_target_suit_mismatch() -> None:
    with pytest.raises(ValueError, match="target suit"):
        RestrictedChoiceQuestion(
            "mismatch", Suit.HEARTS, Seat.EAST, OBSERVED
        )


def test_restricted_choice_rejects_inconsistent_public_history() -> None:
    with pytest.raises(ValueError, match="latest public play"):
        build_restricted_choice_question(
            subject="missing observation",
            target_suit=Suit.CLUBS,
            observed_defender=Seat.EAST,
            observed_play=OBSERVED,
            public_play_history=(PlayedCard(Seat.WEST, Card.parse("2D")),),
        )


def test_restricted_choice_rejects_hidden_or_untyped_evidence() -> None:
    with pytest.raises(TypeError, match="typed public evidence"):
        RestrictedChoiceQuestion(
            "hidden",
            Suit.CLUBS,
            Seat.EAST,
            OBSERVED,
            publicly_established_choice_sets=(frozenset({OBSERVED.card}),),
            choice_basis=(generate_deal(1),),  # type: ignore[arg-type]
        )


def test_restricted_choice_engine_remains_unregistered() -> None:
    result = evaluate_probability(_restricted(), context=ProbabilityContext(frozenset(), frozenset(), 52))
    assert result.status is ProbabilityEngineStatus.UNAVAILABLE
    assert result.failure_code is ProbabilityEngineFailureCode.ENGINE_NOT_REGISTERED


def test_vacant_places_derives_only_public_slot_counts() -> None:
    question = VacantPlacesQuestion(
        "vacant places",
        Suit.CLUBS,
        (Seat.EAST, Seat.WEST),
        (_ownership(Seat.EAST, "KC"), _ownership(Seat.WEST, "2D")),
        declarer_seat=Seat.NORTH,
    )
    assert question.known_card_counts == ((Seat.EAST, 1), (Seat.WEST, 1))
    assert question.remaining_vacant_slots == ((Seat.EAST, 12), (Seat.WEST, 12))
    assert question.known_target_suit_counts == ((Seat.EAST, 1), (Seat.WEST, 0))
    assert not hasattr(question, "probability")


def test_vacant_places_rejects_duplicate_card() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        VacantPlacesQuestion(
            "duplicate",
            Suit.CLUBS,
            (Seat.EAST, Seat.WEST),
            (_ownership(Seat.EAST, "KC"), _ownership(Seat.WEST, "KC")),
        )


def test_vacant_places_rejects_more_than_thirteen_owned_cards() -> None:
    facts = tuple(PublicCardOwnership(Seat.EAST, card, BASIS[0]) for card in full_deck()[:14])
    with pytest.raises(ValueError, match="exceed legal hand size"):
        VacantPlacesQuestion(
            "overflow", Suit.CLUBS, (Seat.EAST, Seat.WEST), facts
        )


def test_vacant_places_rejects_identical_defenders() -> None:
    with pytest.raises(ValueError, match="distinct"):
        VacantPlacesQuestion(
            "same seat", Suit.CLUBS, (Seat.EAST, Seat.EAST)
        )


def test_vacant_places_rejects_declarer_or_dummy_as_defender() -> None:
    with pytest.raises(ValueError, match="two defenders"):
        VacantPlacesQuestion(
            "invalid partnership",
            Suit.CLUBS,
            (Seat.NORTH, Seat.EAST),
            declarer_seat=Seat.NORTH,
        )


def test_vacant_places_rejects_hidden_ownership_map() -> None:
    with pytest.raises(TypeError, match="typed public ownership"):
        VacantPlacesQuestion(
            "hidden map",
            Suit.CLUBS,
            (Seat.EAST, Seat.WEST),
            ({Seat.EAST: generate_deal(1).hand(Seat.EAST)},),  # type: ignore[arg-type]
        )


def test_vacant_places_engine_remains_unregistered() -> None:
    question = VacantPlacesQuestion(
        "vacant", Suit.CLUBS, (Seat.EAST, Seat.WEST)
    )
    result = evaluate_probability(question, context=ProbabilityContext(frozenset(), frozenset(), 52))
    assert result.failure_code is ProbabilityEngineFailureCode.ENGINE_NOT_REGISTERED


def test_restricted_choice_adapter_accepts_public_history_only() -> None:
    history = (PlayedCard(Seat.WEST, Card.parse("2D")), OBSERVED)
    question = build_restricted_choice_question(
        subject="public observation",
        target_suit=Suit.CLUBS,
        observed_defender=Seat.EAST,
        observed_play=OBSERVED,
        public_play_history=history,
        declarer_seat=Seat.NORTH,
    )
    assert question.prior_public_plays == history[:-1]
    assert question.observation_status is RestrictedChoiceObservationStatus.INSUFFICIENT


def test_vacant_places_adapter_uses_only_cards_played_by_defenders() -> None:
    history = (
        PlayedCard(Seat.NORTH, Card.parse("AC")),
        PlayedCard(Seat.EAST, Card.parse("KC")),
        PlayedCard(Seat.SOUTH, Card.parse("QC")),
        PlayedCard(Seat.WEST, Card.parse("JC")),
    )
    question = build_vacant_places_question_from_play_history(
        subject="public ownership",
        target_suit=Suit.CLUBS,
        defenders=(Seat.EAST, Seat.WEST),
        public_play_history=history,
        declarer_seat=Seat.NORTH,
    )
    assert {fact.card for fact in question.public_card_ownership} == {
        Card.parse("KC"),
        Card.parse("JC"),
    }


def test_public_adapters_have_no_deal_or_hand_parameter() -> None:
    for adapter in (
        build_restricted_choice_question,
        build_vacant_places_question_from_play_history,
    ):
        parameters = inspect.signature(adapter).parameters
        assert "deal" not in parameters
        assert "hand" not in parameters
        assert all("Deal" not in str(item.annotation) for item in parameters.values())


def test_probability_production_guards_remain_unchanged() -> None:
    audit = run_phase16_coverage_closure_audit()
    assert DEFAULT_PROBABILITY_ENGINE_REGISTRY.registered_question_types == (
        "KnownCardCountQuestion",
    )
    assert audit.cumulative["production_recommendations"] == 4
    assert len(create_standard_sayc_router().routes) == 45
    assert tuple(FormulaIdentifier) == (FormulaIdentifier.KNOWN_CARD_COUNT_V1,)
