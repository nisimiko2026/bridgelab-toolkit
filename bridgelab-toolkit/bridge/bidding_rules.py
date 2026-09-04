"""BridgeLab Bridge Engine — source-grounded bidding-rule contract.

This module defines *how* bidding knowledge is represented and evaluated.  It
intentionally contains no SAYC thresholds, convention meanings, or other
bidding theory.  Rule implementations belong to later phases and must cite the
canonical BridgeLab article from which each rule is derived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable

from .auction import Auction, Call
from .evaluation import HandEvaluation, evaluate_hand
from .models import Hand, Seat, Vulnerability


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    """Traceability pointer into the canonical BridgeLab knowledge corpus."""

    article_id: str
    heading: str | None = None

    def __post_init__(self) -> None:
        article_id = self.article_id.strip().replace("\\", "/").strip("/")
        if not article_id:
            raise ValueError("source article_id must not be blank")
        if article_id.casefold().endswith(".md"):
            article_id = article_id[:-3]
        if not article_id:
            raise ValueError("source article_id must not be blank")
        object.__setattr__(self, "article_id", article_id)

        if self.heading is not None:
            heading = self.heading.strip()
            object.__setattr__(self, "heading", heading or None)

    def serialize(self) -> str:
        if self.heading:
            return f"{self.article_id}#{self.heading}"
        return self.article_id


@dataclass(frozen=True, slots=True)
class SystemContext:
    """Bidding-system identity plus explicit configuration flags.

    ``options`` is deliberately opaque at this layer.  A convention interpreter
    may later define typed option schemas without changing the rule contract.
    """

    system: str
    options: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        system = self.system.strip()
        if not system:
            raise ValueError("system must not be blank")
        object.__setattr__(self, "system", system)

        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for key, value in self.options:
            k = str(key).strip()
            v = str(value).strip()
            if not k:
                raise ValueError("system option key must not be blank")
            folded = k.casefold()
            if folded in seen:
                raise ValueError(f"duplicate system option: {k}")
            seen.add(folded)
            normalized.append((k, v))
        object.__setattr__(self, "options", tuple(sorted(normalized, key=lambda x: x[0].casefold())))

    @classmethod
    def from_mapping(cls, system: str, options: Mapping[str, object] | None = None) -> "SystemContext":
        return cls(
            system=system,
            options=tuple((str(k), str(v)) for k, v in (options or {}).items()),
        )

    def option(self, key: str, default: str | None = None) -> str | None:
        folded = key.strip().casefold()
        for existing_key, value in self.options:
            if existing_key.casefold() == folded:
                return value
        return default


@dataclass(frozen=True, slots=True)
class BiddingContext:
    """Complete immutable input supplied to one bidding rule."""

    hand: Hand
    evaluation: HandEvaluation
    auction: Auction
    seat: Seat
    vulnerability: Vulnerability
    system: SystemContext

    def __post_init__(self) -> None:
        if not isinstance(self.hand, Hand):
            raise TypeError("hand must be Hand")
        if not isinstance(self.evaluation, HandEvaluation):
            raise TypeError("evaluation must be HandEvaluation")
        if not isinstance(self.auction, Auction):
            raise TypeError("auction must be Auction")
        if not isinstance(self.seat, Seat):
            raise TypeError("seat must be Seat")
        if not isinstance(self.vulnerability, Vulnerability):
            raise TypeError("vulnerability must be Vulnerability")
        if not isinstance(self.system, SystemContext):
            raise TypeError("system must be SystemContext")
        if self.auction.is_complete:
            raise ValueError("cannot create bidding context for a completed auction")
        if self.auction.next_seat is not self.seat:
            raise ValueError(
                f"context seat {self.seat.value} is not next to call; "
                f"expected {self.auction.next_seat.value}"
            )

    @classmethod
    def create(
        cls,
        *,
        hand: Hand,
        auction: Auction,
        vulnerability: Vulnerability,
        system: SystemContext,
        seat: Seat | None = None,
    ) -> "BiddingContext":
        actual_seat = auction.next_seat if seat is None else seat
        return cls(
            hand=hand,
            evaluation=evaluate_hand(hand),
            auction=auction,
            seat=actual_seat,
            vulnerability=vulnerability,
            system=system,
        )


@dataclass(frozen=True, slots=True)
class RuleDecision:
    """Result returned by a bidding rule.

    An applicable decision must provide a legal candidate call, a non-empty
    explanation, and at least one canonical source.  A non-applicable decision
    carries only an optional diagnostic reason.
    """

    rule_id: str
    applicable: bool
    candidate: Call | None = None
    explanation: str = ""
    sources: tuple[KnowledgeSource, ...] = ()
    priority: int = 0

    def __post_init__(self) -> None:
        rule_id = self.rule_id.strip()
        if not rule_id:
            raise ValueError("rule_id must not be blank")
        object.__setattr__(self, "rule_id", rule_id)

        explanation = self.explanation.strip()
        object.__setattr__(self, "explanation", explanation)

        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise TypeError("priority must be an integer")

        if self.applicable:
            if not isinstance(self.candidate, Call):
                raise ValueError("applicable decision requires a candidate Call")
            if not explanation:
                raise ValueError("applicable decision requires an explanation")
            if not self.sources:
                raise ValueError("applicable decision requires at least one source")
            if not all(isinstance(source, KnowledgeSource) for source in self.sources):
                raise TypeError("sources must contain KnowledgeSource values")
        else:
            if self.candidate is not None:
                raise ValueError("non-applicable decision cannot contain a candidate")
            if self.sources:
                raise ValueError("non-applicable decision cannot contain sources")

    @classmethod
    def not_applicable(cls, rule_id: str, reason: str = "") -> "RuleDecision":
        return cls(rule_id=rule_id, applicable=False, explanation=reason)

    @classmethod
    def recommend(
        cls,
        *,
        rule_id: str,
        candidate: Call,
        explanation: str,
        sources: tuple[KnowledgeSource, ...],
        priority: int = 0,
    ) -> "RuleDecision":
        return cls(
            rule_id=rule_id,
            applicable=True,
            candidate=candidate,
            explanation=explanation,
            sources=sources,
            priority=priority,
        )

    def validate_for(self, context: BiddingContext) -> None:
        """Check contextual invariants not knowable at construction time."""
        if not isinstance(context, BiddingContext):
            raise TypeError("context must be BiddingContext")
        if self.applicable:
            assert self.candidate is not None
            if not context.auction.is_legal(self.candidate):
                raise ValueError(
                    f"rule {self.rule_id!r} produced illegal call "
                    f"{self.candidate.serialize()}"
                )


@runtime_checkable
class BiddingRule(Protocol):
    """Structural contract implemented by all future bidding rules."""

    @property
    def rule_id(self) -> str: ...

    def evaluate(self, context: BiddingContext) -> RuleDecision: ...


def evaluate_rule(rule: BiddingRule, context: BiddingContext) -> RuleDecision:
    """Evaluate one rule and enforce the common decision contract."""
    if not isinstance(context, BiddingContext):
        raise TypeError("context must be BiddingContext")
    decision = rule.evaluate(context)
    if not isinstance(decision, RuleDecision):
        raise TypeError("bidding rule must return RuleDecision")
    if decision.rule_id != rule.rule_id:
        raise ValueError(
            f"decision rule_id {decision.rule_id!r} does not match rule {rule.rule_id!r}"
        )
    decision.validate_for(context)
    return decision
