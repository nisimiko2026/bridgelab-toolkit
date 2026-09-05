"""Formula-neutral probability execution architecture and registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .declarer_play_state import DeclarerPlayState
from .models import Card
from .probability_evidence import ProbabilityEvidence, ProbabilityEvidenceType
from .probability_questions import KnownCardCountQuestion, ProbabilityQuestion


class ProbabilityEngineStatus(str, Enum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    INVALID_INPUT = "invalid-input"
    ERROR = "error"


class ProbabilityEngineFailureCode(str, Enum):
    ENGINE_NOT_REGISTERED = "engine-not-registered"
    INSUFFICIENT_STATE = "insufficient-state"
    INVALID_CARD_ACCOUNTING = "invalid-card-accounting"
    UNSUPPORTED_QUESTION = "unsupported-question"
    MISSING_SEED = "missing-seed"
    MISSING_TRIAL_COUNT = "missing-trial-count"


class CalculationMode(str, Enum):
    EXACT = "exact"
    SIMULATED = "simulated"


class FormulaIdentifier(str, Enum):
    KNOWN_CARD_COUNT_V1 = "known-card-count-v1"


@dataclass(frozen=True, slots=True)
class ProbabilityContext:
    visible_cards: frozenset[Card]
    played_cards: frozenset[Card]
    unknown_card_count: int


@dataclass(frozen=True, slots=True)
class ProbabilityEngineResult:
    status: ProbabilityEngineStatus
    evidence: tuple[ProbabilityEvidence, ...] = ()
    mode: CalculationMode | None = None
    formula_id: FormulaIdentifier | None = None
    failure_code: ProbabilityEngineFailureCode | None = None
    explanation: str = ""
    trace: tuple[tuple[str, str], ...] = ()

    @property
    def is_success(self) -> bool:
        return self.status is ProbabilityEngineStatus.SUCCESS


ProbabilityCalculator = Callable[[ProbabilityQuestion, ProbabilityContext], ProbabilityEngineResult]


@dataclass(frozen=True, slots=True)
class ProbabilityEngineRegistry:
    registrations: tuple[tuple[type[ProbabilityQuestion], ProbabilityCalculator], ...] = ()

    def calculator_for(self, question: ProbabilityQuestion) -> ProbabilityCalculator | None:
        return next((calculator for question_type, calculator in self.registrations if isinstance(question, question_type)), None)

    @property
    def registered_question_types(self) -> tuple[str, ...]:
        return tuple(question_type.__name__ for question_type, _ in self.registrations)


def build_probability_context(state: DeclarerPlayState) -> ProbabilityContext:
    return ProbabilityContext(state.visible_cards, state.played_cards, state.unknown_card_count)


def _known_card_count(
    question: ProbabilityQuestion,
    context: ProbabilityContext,
) -> ProbabilityEngineResult:
    if not isinstance(question, KnownCardCountQuestion):
        return ProbabilityEngineResult(
            ProbabilityEngineStatus.UNAVAILABLE,
            failure_code=ProbabilityEngineFailureCode.UNSUPPORTED_QUESTION,
        )
    visible = len(context.visible_cards)
    played = len(context.played_cards)
    unknown = context.unknown_card_count
    trace = (("deck-size", "52"), ("known-unique", str(visible + played)), ("unknown", str(unknown)))
    if context.visible_cards.intersection(context.played_cards) or visible + played + unknown != 52:
        return ProbabilityEngineResult(
            ProbabilityEngineStatus.INVALID_INPUT,
            failure_code=ProbabilityEngineFailureCode.INVALID_CARD_ACCOUNTING,
            explanation="Known-card accounting does not reconcile to the 52-card deck.",
            trace=trace,
        )
    evidence = ProbabilityEvidence(
        ProbabilityEvidenceType.KNOWN_CARD_COUNT, question.subject.strip(),
        ("Only declarer-visible holdings and cards in validated play history are known.",
         "Hidden defender cards and distributions remain unknown."),
        (("visible-cards", str(visible)), ("played-cards", str(played))), str(unknown),
        trace=trace,
    )
    return ProbabilityEngineResult(
        ProbabilityEngineStatus.SUCCESS, (evidence,), CalculationMode.EXACT,
        FormulaIdentifier.KNOWN_CARD_COUNT_V1, trace=trace,
    )


DEFAULT_PROBABILITY_ENGINE_REGISTRY = ProbabilityEngineRegistry(((KnownCardCountQuestion, _known_card_count),))


def evaluate_probability(
    question: ProbabilityQuestion,
    state: DeclarerPlayState | None = None,
    *,
    context: ProbabilityContext | None = None,
    registry: ProbabilityEngineRegistry = DEFAULT_PROBABILITY_ENGINE_REGISTRY,
) -> ProbabilityEngineResult:
    calculator = registry.calculator_for(question)
    if calculator is None:
        return ProbabilityEngineResult(
            ProbabilityEngineStatus.UNAVAILABLE,
            failure_code=ProbabilityEngineFailureCode.ENGINE_NOT_REGISTERED,
            explanation=f"No probability engine is registered for {type(question).__name__}.",
            trace=(("question-type", type(question).__name__),),
        )
    supplied_context = context if context is not None else (None if state is None else build_probability_context(state))
    if supplied_context is None:
        return ProbabilityEngineResult(
            ProbabilityEngineStatus.UNAVAILABLE,
            failure_code=ProbabilityEngineFailureCode.INSUFFICIENT_STATE,
            explanation="A validated declarer state or explicit probability context is required.",
        )
    try:
        return calculator(question, supplied_context)
    except (TypeError, ValueError) as exc:
        return ProbabilityEngineResult(ProbabilityEngineStatus.ERROR, explanation=str(exc))
