"""Demand-driven normalization of existing declarer counting evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bidding_rules import KnowledgeSource
from .declarer_play_state import DeclarerPlayState
from .probability_questions import KnownCardCountQuestion as KnownCardCountQuestion, ProbabilityQuestion


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
    UNSUPPORTED_EVIDENCE_TYPE = "unsupported-evidence-type"


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
    question: ProbabilityQuestion | None,
) -> ProbabilityEvidenceResult:
    """Backward-compatible evidence adapter over the probability engine."""
    if question is None:
        return ProbabilityEvidenceResult(
            ProbabilityEvidenceStatus.UNAVAILABLE,
            failure_code=ProbabilityEvidenceFailureCode.MISSING_QUESTION,
            explanation="An explicit supported evidence question is required.",
        )
    from .probability_engine import ProbabilityEngineFailureCode, ProbabilityEngineStatus, evaluate_probability

    result = evaluate_probability(question, state)
    if result.status is ProbabilityEngineStatus.SUCCESS:
        return ProbabilityEvidenceResult(ProbabilityEvidenceStatus.AVAILABLE, result.evidence)
    failure = {
        ProbabilityEngineFailureCode.INSUFFICIENT_STATE: ProbabilityEvidenceFailureCode.INSUFFICIENT_KNOWN_CARDS,
        ProbabilityEngineFailureCode.INVALID_CARD_ACCOUNTING: ProbabilityEvidenceFailureCode.INVALID_CARD_ACCOUNTING,
        ProbabilityEngineFailureCode.ENGINE_NOT_REGISTERED: ProbabilityEvidenceFailureCode.UNSUPPORTED_EVIDENCE_TYPE,
    }.get(result.failure_code)
    return ProbabilityEvidenceResult(
        ProbabilityEvidenceStatus.ERROR if result.status is ProbabilityEngineStatus.ERROR else ProbabilityEvidenceStatus.UNAVAILABLE,
        failure_code=failure,
        explanation=result.explanation,
    )
