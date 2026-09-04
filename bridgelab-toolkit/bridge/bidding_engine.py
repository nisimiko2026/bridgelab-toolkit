"""BridgeLab Bridge Engine — deterministic bidding-rule orchestration.

The engine in this module does not contain bidding theory.  It executes
registered :class:`BiddingRule` implementations, applies the Phase 5D contract,
ranks applicable source-grounded decisions deterministically, and returns a
recommendation plus alternatives and the complete evaluation trace.

Actual SAYC/convention rules are intentionally deferred to later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .auction import Call
from .bidding_rules import BiddingContext, BiddingRule, RuleDecision, evaluate_rule


@dataclass(frozen=True, slots=True)
class BiddingEngineResult:
    """Immutable result of evaluating one bidding position.

    ``recommended`` is the highest-ranked unique candidate call, or ``None``
    when no registered rule applies. ``alternatives`` contains the remaining
    unique candidate calls in rank order. ``decisions`` contains every rule
    decision, including non-applicable rules, preserving the audit trail.
    """

    recommended: RuleDecision | None
    alternatives: tuple[RuleDecision, ...]
    decisions: tuple[RuleDecision, ...]

    @property
    def has_recommendation(self) -> bool:
        return self.recommended is not None

    @property
    def candidates(self) -> tuple[RuleDecision, ...]:
        if self.recommended is None:
            return ()
        return (self.recommended, *self.alternatives)

    @property
    def recommended_call(self) -> Call | None:
        return None if self.recommended is None else self.recommended.candidate


class BiddingEngine:
    """Evaluate and rank a fixed registry of source-grounded bidding rules.

    Ranking is deliberately simple and explainable at this architectural
    stage:

    1. higher ``RuleDecision.priority`` first;
    2. lower registration order first;
    3. lexical ``rule_id`` as a final stable tie-breaker.

    If several rules recommend the same call, only the highest-ranked decision
    for that call appears in ``candidates``.  Every rule's decision remains
    available in ``decisions`` for diagnostics and source auditing.
    """

    def __init__(self, rules: Iterable[BiddingRule] = ()) -> None:
        collected = tuple(rules)
        seen: set[str] = set()
        for rule in collected:
            rule_id = _validated_rule_id(rule)
            folded = rule_id.casefold()
            if folded in seen:
                raise ValueError(f"duplicate bidding rule_id: {rule_id}")
            seen.add(folded)
        self._rules = collected

    @property
    def rules(self) -> tuple[BiddingRule, ...]:
        return self._rules

    def evaluate(self, context: BiddingContext) -> BiddingEngineResult:
        if not isinstance(context, BiddingContext):
            raise TypeError("context must be BiddingContext")

        evaluated: list[tuple[int, RuleDecision]] = []
        decisions: list[RuleDecision] = []

        for registration_order, rule in enumerate(self._rules):
            decision = evaluate_rule(rule, context)
            decisions.append(decision)
            if decision.applicable:
                evaluated.append((registration_order, decision))

        evaluated.sort(
            key=lambda item: (
                -item[1].priority,
                item[0],
                item[1].rule_id.casefold(),
            )
        )

        unique_candidates: list[RuleDecision] = []
        seen_calls: set[str] = set()
        for _, decision in evaluated:
            assert decision.candidate is not None
            call_key = decision.candidate.serialize()
            if call_key in seen_calls:
                continue
            seen_calls.add(call_key)
            unique_candidates.append(decision)

        recommended = unique_candidates[0] if unique_candidates else None
        alternatives = tuple(unique_candidates[1:])

        return BiddingEngineResult(
            recommended=recommended,
            alternatives=alternatives,
            decisions=tuple(decisions),
        )


def _validated_rule_id(rule: BiddingRule) -> str:
    try:
        rule_id = rule.rule_id
    except AttributeError as exc:
        raise TypeError("bidding rule must expose rule_id") from exc
    if not isinstance(rule_id, str):
        raise TypeError("bidding rule rule_id must be a string")
    normalized = rule_id.strip()
    if not normalized:
        raise ValueError("bidding rule rule_id must not be blank")
    return normalized
