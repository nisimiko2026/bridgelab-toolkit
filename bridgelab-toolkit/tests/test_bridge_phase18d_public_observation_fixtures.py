from __future__ import annotations

import inspect

import pytest

from bridge import (
    Card,
    PlayedCard,
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
    full_deck,
)


OBSERVED = PlayedCard(Seat.EAST, Card.parse("KC"))
PLAYED_BASIS = PublicEvidence(PublicEvidenceKind.PLAYED_CARD, 1)
ChoiceCollection = frozenset[Card] | tuple[Card, ...]


def _restricted_choice_fixture(
    choice_sets: tuple[ChoiceCollection, ...] = (),
    *,
    choice_basis: tuple[PublicEvidence, ...] | None = None,
) -> RestrictedChoiceQuestion:
    history = (PlayedCard(Seat.WEST, Card.parse("2D")), OBSERVED)
    return build_restricted_choice_question(
        subject="public restricted-choice observation",
        target_suit=Suit.CLUBS,
        observed_defender=Seat.EAST,
        observed_play=OBSERVED,
        public_play_history=history,
        publicly_established_choice_sets=choice_sets,  # type: ignore[arg-type]
        choice_basis=(PLAYED_BASIS,) if choice_basis is None and choice_sets else choice_basis or (),
        declarer_seat=Seat.NORTH,
    )


@pytest.fixture
def restricted_choice_forced_fixture() -> RestrictedChoiceQuestion:
    return _restricted_choice_fixture((frozenset({OBSERVED.card}),))


@pytest.fixture
def restricted_choice_optional_fixture() -> RestrictedChoiceQuestion:
    return _restricted_choice_fixture(
        (frozenset({OBSERVED.card, Card.parse("QC")}),)
    )


@pytest.fixture
def restricted_choice_ambiguous_fixture() -> RestrictedChoiceQuestion:
    return _restricted_choice_fixture(
        (
            frozenset({OBSERVED.card}),
            frozenset({OBSERVED.card, Card.parse("QC")}),
        )
    )


@pytest.fixture
def restricted_choice_insufficient_fixture() -> RestrictedChoiceQuestion:
    return _restricted_choice_fixture()


def _ownership(seat: Seat, card: Card) -> PublicCardOwnership:
    return PublicCardOwnership(seat, card, PLAYED_BASIS)


@pytest.fixture
def vacant_places_zero_known_fixture() -> VacantPlacesQuestion:
    return VacantPlacesQuestion(
        "zero public cards", Suit.CLUBS, (Seat.EAST, Seat.WEST), declarer_seat=Seat.NORTH
    )


@pytest.fixture
def vacant_places_asymmetric_fixture() -> VacantPlacesQuestion:
    facts = (
        _ownership(Seat.EAST, Card.parse("KC")),
        _ownership(Seat.EAST, Card.parse("3D")),
        _ownership(Seat.EAST, Card.parse("4H")),
        _ownership(Seat.WEST, Card.parse("JC")),
    )
    return VacantPlacesQuestion(
        "asymmetric public cards",
        Suit.CLUBS,
        (Seat.EAST, Seat.WEST),
        facts,
        declarer_seat=Seat.NORTH,
    )


def test_restricted_choice_forced_fixture_is_status_only(
    restricted_choice_forced_fixture: RestrictedChoiceQuestion,
) -> None:
    assert restricted_choice_forced_fixture.observation_status is RestrictedChoiceObservationStatus.FORCED
    assert not hasattr(restricted_choice_forced_fixture, "probability")


def test_restricted_choice_optional_fixture_is_status_only(
    restricted_choice_optional_fixture: RestrictedChoiceQuestion,
) -> None:
    assert restricted_choice_optional_fixture.observation_status is RestrictedChoiceObservationStatus.OPTIONAL


def test_restricted_choice_ambiguous_fixture_is_status_only(
    restricted_choice_ambiguous_fixture: RestrictedChoiceQuestion,
) -> None:
    assert restricted_choice_ambiguous_fixture.observation_status is RestrictedChoiceObservationStatus.AMBIGUOUS


def test_restricted_choice_insufficient_fixture_is_status_only(
    restricted_choice_insufficient_fixture: RestrictedChoiceQuestion,
) -> None:
    assert restricted_choice_insufficient_fixture.observation_status is RestrictedChoiceObservationStatus.INSUFFICIENT


def test_restricted_choice_rejects_nonlatest_observation() -> None:
    with pytest.raises(ValueError, match="latest public play"):
        build_restricted_choice_question(
            subject="invalid chronology",
            target_suit=Suit.CLUBS,
            observed_defender=Seat.EAST,
            observed_play=OBSERVED,
            public_play_history=(OBSERVED, PlayedCard(Seat.WEST, Card.parse("2D"))),
        )


def test_restricted_choice_rejects_duplicate_public_card() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        build_restricted_choice_question(
            subject="duplicate public card",
            target_suit=Suit.CLUBS,
            observed_defender=Seat.EAST,
            observed_play=OBSERVED,
            public_play_history=(OBSERVED, OBSERVED),
        )


def test_restricted_choice_rejects_off_suit_alternative() -> None:
    with pytest.raises(ValueError, match="target suit"):
        _restricted_choice_fixture(
            (frozenset({OBSERVED.card, Card.parse("QD")}),)
        )


def test_restricted_choice_rejects_choice_set_omitting_observed_card() -> None:
    with pytest.raises(ValueError, match="observed card"):
        _restricted_choice_fixture((frozenset({Card.parse("QC")}),))


@pytest.mark.parametrize(
    ("choice_sets", "expected_status"),
    (
        (
            ((OBSERVED.card,), (OBSERVED.card,)),
            RestrictedChoiceObservationStatus.FORCED,
        ),
        (
            (
                (OBSERVED.card, Card.parse("QC")),
                (Card.parse("QC"), OBSERVED.card),
            ),
            RestrictedChoiceObservationStatus.OPTIONAL,
        ),
        (
            (
                (OBSERVED.card,),
                (OBSERVED.card, Card.parse("QC")),
            ),
            RestrictedChoiceObservationStatus.AMBIGUOUS,
        ),
    ),
)
def test_restricted_choice_normalizes_equivalent_sets_without_losing_ambiguity(
    choice_sets: tuple[ChoiceCollection, ...],
    expected_status: RestrictedChoiceObservationStatus,
) -> None:
    assert _restricted_choice_fixture(choice_sets).observation_status is expected_status


def test_restricted_choice_normalizes_duplicate_card_within_choice_set() -> None:
    question = _restricted_choice_fixture(
        ((OBSERVED.card, OBSERVED.card),)  # type: ignore[arg-type]
    )
    assert question.observation_status is RestrictedChoiceObservationStatus.FORCED


def test_public_auction_is_context_only_and_cannot_establish_ownership() -> None:
    auction = PublicEvidence(PublicEvidenceKind.PUBLIC_AUCTION)
    question = _restricted_choice_fixture(
        (frozenset({OBSERVED.card, Card.parse("QC")}),),
        choice_basis=(auction,),
    )
    assert question.observation_status is RestrictedChoiceObservationStatus.OPTIONAL
    with pytest.raises(ValueError, match="cannot establish exact card ownership"):
        PublicCardOwnership(Seat.EAST, OBSERVED.card, auction)


def test_logically_established_is_direct_constructor_trust_boundary() -> None:
    logical = PublicEvidence(PublicEvidenceKind.LOGICALLY_ESTABLISHED)
    question = RestrictedChoiceQuestion(
        "trusted public deduction",
        Suit.CLUBS,
        Seat.EAST,
        OBSERVED,
        publicly_established_choice_sets=(frozenset({OBSERVED.card}),),
        choice_basis=(logical,),
        declarer_seat=Seat.NORTH,
    )
    assert question.observation_status is RestrictedChoiceObservationStatus.FORCED
    assert not hasattr(logical, "detail")


def test_vacant_places_zero_known_fixture_has_thirteen_slots_each(
    vacant_places_zero_known_fixture: VacantPlacesQuestion,
) -> None:
    assert vacant_places_zero_known_fixture.remaining_vacant_slots == (
        (Seat.EAST, 13),
        (Seat.WEST, 13),
    )


def test_vacant_places_asymmetric_fixture_has_ten_and_twelve_slots(
    vacant_places_asymmetric_fixture: VacantPlacesQuestion,
) -> None:
    assert vacant_places_asymmetric_fixture.remaining_vacant_slots == (
        (Seat.EAST, 10),
        (Seat.WEST, 12),
    )


def test_vacant_places_thirteen_known_cards_has_zero_slots() -> None:
    facts = tuple(_ownership(Seat.EAST, card) for card in full_deck()[:13])
    question = VacantPlacesQuestion(
        "complete public count", Suit.CLUBS, (Seat.EAST, Seat.WEST), facts
    )
    assert question.remaining_vacant_slots[0] == (Seat.EAST, 0)


def test_vacant_places_rejects_fourteen_known_cards() -> None:
    facts = tuple(_ownership(Seat.EAST, card) for card in full_deck()[:14])
    with pytest.raises(ValueError, match="exceed legal hand size"):
        VacantPlacesQuestion(
            "impossible public count", Suit.CLUBS, (Seat.EAST, Seat.WEST), facts
        )


def test_vacant_places_rejects_duplicate_card_for_same_defender() -> None:
    duplicate = Card.parse("KC")
    with pytest.raises(ValueError, match="duplicate physical card"):
        VacantPlacesQuestion(
            "duplicate public card",
            Suit.CLUBS,
            (Seat.EAST, Seat.WEST),
            (_ownership(Seat.EAST, duplicate), _ownership(Seat.EAST, duplicate)),
        )


def test_vacant_places_rejects_cross_assigned_card() -> None:
    duplicate = Card.parse("KC")
    with pytest.raises(ValueError, match="duplicate physical card"):
        VacantPlacesQuestion(
            "cross-assigned public card",
            Suit.CLUBS,
            (Seat.EAST, Seat.WEST),
            (_ownership(Seat.EAST, duplicate), _ownership(Seat.WEST, duplicate)),
        )


def test_vacant_places_rejects_unrelated_ownership_seat() -> None:
    with pytest.raises(ValueError, match="compared defender"):
        VacantPlacesQuestion(
            "unrelated public seat",
            Suit.CLUBS,
            (Seat.EAST, Seat.WEST),
            (_ownership(Seat.NORTH, Card.parse("AC")),),
        )


def test_vacant_places_rejects_same_defender_twice() -> None:
    with pytest.raises(ValueError, match="distinct"):
        VacantPlacesQuestion("same defender", Suit.CLUBS, (Seat.EAST, Seat.EAST))


def test_vacant_places_rejects_declarer_or_dummy() -> None:
    for defenders in ((Seat.NORTH, Seat.EAST), (Seat.SOUTH, Seat.EAST)):
        with pytest.raises(ValueError, match="two defenders"):
            VacantPlacesQuestion(
                "declarer partnership",
                Suit.CLUBS,
                defenders,
                declarer_seat=Seat.NORTH,
            )


def test_vacant_places_adapter_derives_only_public_defender_plays() -> None:
    history = (
        PlayedCard(Seat.NORTH, Card.parse("AC")),
        PlayedCard(Seat.EAST, Card.parse("KC")),
        PlayedCard(Seat.SOUTH, Card.parse("QC")),
        PlayedCard(Seat.WEST, Card.parse("JC")),
    )
    question = build_vacant_places_question_from_play_history(
        subject="public play ownership",
        target_suit=Suit.CLUBS,
        defenders=(Seat.EAST, Seat.WEST),
        public_play_history=history,
        declarer_seat=Seat.NORTH,
    )
    assert tuple((fact.seat, fact.card) for fact in question.public_card_ownership) == (
        (Seat.EAST, Card.parse("KC")),
        (Seat.WEST, Card.parse("JC")),
    )
    assert all(
        fact.evidence.kind is PublicEvidenceKind.PLAYED_CARD
        for fact in question.public_card_ownership
    )


def test_public_auction_cannot_create_vacant_places_ownership() -> None:
    with pytest.raises(ValueError, match="cannot establish exact card ownership"):
        PublicCardOwnership(
            Seat.EAST,
            Card.parse("KC"),
            PublicEvidence(PublicEvidenceKind.PUBLIC_AUCTION),
        )


def test_phase18d_fixture_apis_exclude_hidden_information_channels() -> None:
    expected_parameters = {
        build_restricted_choice_question: {
            "subject",
            "target_suit",
            "observed_defender",
            "observed_play",
            "public_play_history",
            "publicly_established_choice_sets",
            "choice_basis",
            "declarer_seat",
        },
        build_vacant_places_question_from_play_history: {
            "subject",
            "target_suit",
            "defenders",
            "public_play_history",
            "declarer_seat",
        },
    }
    for adapter, expected in expected_parameters.items():
        signature = inspect.signature(adapter)
        assert set(signature.parameters) == expected
        annotations = " ".join(str(value.annotation) for value in signature.parameters.values())
        for forbidden in (
            "Any",
            "Mapping",
            "Deal",
            "Hand",
            "object",
            "double-dummy",
        ):
            assert forbidden not in annotations
