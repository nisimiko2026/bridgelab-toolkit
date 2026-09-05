"""Demand-driven normalization of existing declarer counting evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bidding_rules import KnowledgeSource
from .declarer_play_state import DeclarerPlayState


class ProbabilityEvidenceType(str, Enum):
    KNOWN_CARD_COUNT = "known-card-count"


class ProbabilityEvidenceStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ProbabilityEvidenceFailureCode(str, Enum):
    MISSING_QUESTION = "missing-question"
    INSUFFICIENT_KNOWN_CARDS = "insufficient-known-cards"
    INVALID_CARD_ACCOUNTING = "invalid-card-accounting"


@dataclass(frozen=True, slots=True)
class KnownCardCountQuestion:
    subject: str = "declarer-visible card accounting"

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("evidence subject must not be blank")


@dataclass(frozen=True, slots=True)
class ProbabilityEvidence:
    evidence_type: ProbabilityEvidenceType
    subject: str
    assumptions: tuple[str, ...]
    known_facts: tuple[tuple[str, str], ...]
    result: str
    probability: str | None = None
    alternatives: tuple[tuple[str, str], ...] = ()
    sample_size: int | None = None
    deterministic: bool = True
    simulated: bool = False
    source: KnowledgeSource | None = None
    trace: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ProbabilityEvidenceResult:
    status: ProbabilityEvidenceStatus
    evidence: tuple[ProbabilityEvidence, ...] = ()
    failure_code: ProbabilityEvidenceFailureCode | None = None
    explanation: str = ""

    @property
    def is_available(self) -> bool:
        return self.status is ProbabilityEvidenceStatus.AVAILABLE


def collect_declarer_probability_evidence(
    state: DeclarerPlayState | None,
    question: KnownCardCountQuestion | None,
) -> ProbabilityEvidenceResult:
    """Normalize existing state accounting; perform no probability calculation."""
    if question is None:
        return ProbabilityEvidenceResult(
            ProbabilityEvidenceStatus.UNAVAILABLE,
            failure_code=ProbabilityEvidenceFailureCode.MISSING_QUESTION,
            explanation="An explicit supported evidence question is required.",
        )
    if state is None:
        return ProbabilityEvidenceResult(
            ProbabilityEvidenceStatus.UNAVAILABLE,
            failure_code=ProbabilityEvidenceFailureCode.INSUFFICIENT_KNOWN_CARDS,
            explanation="A validated declarer state is required for known-card accounting.",
        )
    visible = len(state.visible_cards)
    played = len(state.played_cards)
    unknown = state.unknown_card_count
    if visible + played + unknown != 52:
        return ProbabilityEvidenceResult(
            ProbabilityEvidenceStatus.ERROR,
            failure_code=ProbabilityEvidenceFailureCode.INVALID_CARD_ACCOUNTING,
            explanation="Known-card accounting does not reconcile to the 52-card deck.",
        )
    evidence = ProbabilityEvidence(
        ProbabilityEvidenceType.KNOWN_CARD_COUNT,
        question.subject.strip(),
        ("Only declarer-visible holdings and cards in validated play history are known.",
         "Hidden defender cards and distributions remain unknown."),
        (("visible-cards", str(visible)), ("played-cards", str(played))),
        str(unknown),
        trace=(("deck-size", "52"), ("known-unique", str(visible + played)), ("unknown", str(unknown))),
    )
    return ProbabilityEvidenceResult(ProbabilityEvidenceStatus.AVAILABLE, (evidence,))
