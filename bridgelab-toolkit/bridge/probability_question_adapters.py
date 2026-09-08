"""Public-play-only builders for formula-neutral probability questions."""

from __future__ import annotations

from .declarer_play_state import PlayedCard
from .models import Card, Seat, Suit
from .probability_questions import (
    PublicCardOwnership,
    PublicEvidence,
    PublicEvidenceKind,
    RestrictedChoiceQuestion,
    VacantPlacesQuestion,
)


def build_restricted_choice_question(
    *,
    subject: str,
    target_suit: Suit,
    observed_defender: Seat,
    observed_play: PlayedCard,
    public_play_history: tuple[PlayedCard, ...],
    publicly_established_choice_sets: tuple[frozenset[Card], ...] = (),
    choice_basis: tuple[PublicEvidence, ...] = (),
    declarer_seat: Seat | None = None,
) -> RestrictedChoiceQuestion:
    """Build from public history; the observation must be its latest play."""

    history = tuple(public_play_history)
    if any(not isinstance(play, PlayedCard) for play in history):
        raise TypeError("public play history requires PlayedCard values")
    if not history or history[-1] != observed_play:
        raise ValueError("observed play must be the latest public play")
    return RestrictedChoiceQuestion(
        subject,
        target_suit,
        observed_defender,
        observed_play,
        history[:-1],
        publicly_established_choice_sets,
        choice_basis,
        declarer_seat,
    )


def build_vacant_places_question_from_play_history(
    *,
    subject: str,
    target_suit: Suit,
    defenders: tuple[Seat, Seat],
    public_play_history: tuple[PlayedCard, ...],
    declarer_seat: Seat | None = None,
) -> VacantPlacesQuestion:
    """Derive original-hand ownership only from cards publicly played by defenders."""

    history = tuple(public_play_history)
    if any(not isinstance(play, PlayedCard) for play in history):
        raise TypeError("public play history requires PlayedCard values")
    cards = tuple(play.card for play in history)
    if len(cards) != len(set(cards)):
        raise ValueError("public play history contains a duplicate physical card")
    ownership = tuple(
        PublicCardOwnership(
            play.seat,
            play.card,
            PublicEvidence(PublicEvidenceKind.PLAYED_CARD, index),
        )
        for index, play in enumerate(history)
        if play.seat in defenders
    )
    return VacantPlacesQuestion(
        subject,
        target_suit,
        defenders,
        ownership,
        13,
        declarer_seat,
    )
