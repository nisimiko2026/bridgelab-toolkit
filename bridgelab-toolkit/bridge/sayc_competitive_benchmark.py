"""Deterministic benchmark foundation for direct SAYC competition.

This benchmark contains no competitive bidding theory.  North is a scripted
opponent that opens one selected natural one-level suit; South and subsequent
opponent turns use explicit Pass fixtures. East/West use the production SAYC
router.  The harness therefore exposes direct-overcall positions without
changing the semantics of the existing uncontested coverage benchmark.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .auction import Call
from .batch_simulation import BatchSimulationReport, run_seeded_batch
from .bidding_engine import BiddingEngine
from .bidding_rules import KnowledgeSource, RuleDecision, SystemContext
from .models import Seat
from .sayc_route_configuration import create_standard_sayc_router
from .policy_registry import PolicyRegistry

_FIXTURE_SOURCE = KnowledgeSource("bidding/systems/sayc", "Natural Overcalls")
_ALLOWED_OPENINGS = ("1C", "1D", "1H", "1S")


@dataclass(frozen=True, slots=True)
class _ScriptedOpponentRule:
    rule_id: str
    opening: str | None = None

    def evaluate(self, context):
        if self.opening is not None and len(context.auction) == 0:
            call = Call.parse(self.opening)
            return RuleDecision.recommend(
                rule_id=self.rule_id,
                candidate=call,
                explanation="Scripted opponent opening for competitive benchmark; not a production SAYC recommendation.",
                sources=(_FIXTURE_SOURCE,),
                priority=1,
            )
        return RuleDecision.recommend(
            rule_id=self.rule_id,
            candidate=Call.pass_(),
            explanation="Explicit passive-opponent competitive benchmark fixture; not production SAYC coverage.",
            sources=(_FIXTURE_SOURCE,),
            priority=1,
        )


@dataclass(frozen=True, slots=True)
class SaycCompetitiveMetrics:
    runs: int
    opening: str
    direct_positions_reached: int
    direct_actions: int
    direct_abstentions: int
    production_rule_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class SaycCompetitiveBenchmarkReport:
    batch: BatchSimulationReport
    metrics: SaycCompetitiveMetrics


def run_sayc_direct_overcall_benchmark(
    *,
    start_seed: int = 1,
    count: int = 1000,
    opening: str = "1D",
    registry: PolicyRegistry | None = None,
    system_options: dict[str, str] | None = None,
) -> SaycCompetitiveBenchmarkReport:
    opening = opening.strip().upper()
    if opening not in _ALLOWED_OPENINGS:
        raise ValueError("opening must be one of 1C, 1D, 1H, 1S")
    if registry is None:
        registry = PolicyRegistry()
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    options = {} if system_options is None else dict(system_options)

    def engines(deal):
        router = create_standard_sayc_router(registry)
        return {
            Seat.NORTH: BiddingEngine((_ScriptedOpponentRule("benchmark.fixture.opponent.north", opening),)),
            Seat.EAST: router,
            Seat.SOUTH: BiddingEngine((_ScriptedOpponentRule("benchmark.fixture.opponent.south"),)),
            Seat.WEST: router,
        }

    def systems(deal):
        return {
            seat: SystemContext.from_mapping("SAYC", options) for seat in Seat
        }

    batch = run_seeded_batch(
        start_seed=start_seed,
        count=count,
        engine_factory=engines,
        system_factory=systems,
        dealer=Seat.NORTH,
    )

    prod = Counter()
    reached = actions = abstentions = 0
    for case in batch.cases:
        steps = case.result.steps
        if steps and steps[0].rule_id == "benchmark.fixture.opponent.north":
            reached += 1
            if len(steps) >= 2 and not steps[1].rule_id.startswith("benchmark.fixture."):
                actions += 1
                prod[steps[1].rule_id] += 1
            elif case.result.stopped_seat is Seat.EAST:
                abstentions += 1

    metrics = SaycCompetitiveMetrics(
        runs=count,
        opening=opening,
        direct_positions_reached=reached,
        direct_actions=actions,
        direct_abstentions=abstentions,
        production_rule_counts=tuple(sorted(prod.items())),
    )
    return SaycCompetitiveBenchmarkReport(batch, metrics)


@dataclass(frozen=True, slots=True)
class SaycTakeoutAdvancerMetrics:
    runs: int
    opening: str
    advancer_positions_reached: int
    advancer_actions: int
    advancer_abstentions: int
    response_call_counts: tuple[tuple[str, int], ...]
    production_rule_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class SaycTakeoutAdvancerBenchmarkReport:
    batch: BatchSimulationReport
    metrics: SaycTakeoutAdvancerMetrics


def run_sayc_takeout_advancer_benchmark(
    *,
    start_seed: int = 1,
    count: int = 1000,
    opening: str = "1D",
    registry: PolicyRegistry | None = None,
    system_options: dict[str, str] | None = None,
) -> SaycTakeoutAdvancerBenchmarkReport:
    """Benchmark the production Advancer route after a scripted 1x-X-P start.

    The opponent opening, partner Double, and intervening Pass are explicit
    benchmark fixtures. Only the Advancer call is produced by the production
    SAYC router. The harness therefore measures route reachability without
    asserting that the scripted Double was a production Takeout Double.
    """
    opening = opening.strip().upper()
    if opening not in _ALLOWED_OPENINGS:
        raise ValueError("opening must be one of 1C, 1D, 1H, 1S")
    if registry is None:
        registry = PolicyRegistry()
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    options = {} if system_options is None else dict(system_options)

    @dataclass(frozen=True, slots=True)
    class _ScriptedTakeoutRule:
        rule_id: str
        call_text: str
        def evaluate(self, context):
            return RuleDecision.recommend(
                rule_id=self.rule_id,
                candidate=Call.parse(self.call_text),
                explanation="Scripted Takeout-Double benchmark fixture; not a production SAYC recommendation.",
                sources=(_FIXTURE_SOURCE,),
                priority=1,
            )

    def engines(deal):
        router = create_standard_sayc_router(registry)
        return {
            Seat.NORTH: BiddingEngine((_ScriptedOpponentRule("benchmark.fixture.opponent.north", opening),)),
            Seat.EAST: BiddingEngine((_ScriptedTakeoutRule("benchmark.fixture.partner.double", "X"),)),
            Seat.SOUTH: BiddingEngine((_ScriptedTakeoutRule("benchmark.fixture.opponent.pass", "P"),)),
            Seat.WEST: router,
        }

    def systems(deal):
        return {seat: SystemContext.from_mapping("SAYC", options) for seat in Seat}

    batch = run_seeded_batch(
        start_seed=start_seed, count=count, engine_factory=engines,
        system_factory=systems, dealer=Seat.NORTH, max_steps=4,
    )

    calls=Counter(); rules=Counter(); reached=actions=abstentions=0
    for case in batch.cases:
        steps=case.result.steps
        if len(steps)>=3 and tuple(step.call.serialize() for step in steps[:3]) == (opening,"X","P"):
            reached += 1
            if len(steps)>=4 and not steps[3].rule_id.startswith("benchmark.fixture."):
                actions += 1
                calls[steps[3].call.serialize()] += 1
                rules[steps[3].rule_id] += 1
            elif case.result.stopped_seat is Seat.WEST:
                abstentions += 1

    return SaycTakeoutAdvancerBenchmarkReport(
        batch,
        SaycTakeoutAdvancerMetrics(
            runs=count, opening=opening, advancer_positions_reached=reached,
            advancer_actions=actions, advancer_abstentions=abstentions,
            response_call_counts=tuple(sorted(calls.items())),
            production_rule_counts=tuple(sorted(rules.items())),
        ),
    )


@dataclass(frozen=True, slots=True)
class SaycSupportDoubleMetrics:
    runs: int
    auction_prefix: tuple[str, ...]
    positions_reached: int
    exactly_three_support: int
    support_double_actions: int
    abstentions: int
    production_rule_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class SaycSupportDoubleBenchmarkReport:
    batch: BatchSimulationReport
    metrics: SaycSupportDoubleMetrics


_SUPPORT_DOUBLE_PREFIXES = {
    "1D-P-1H-1S": ("1D", "P", "1H", "1S"),
    "1C-P-1H-1S": ("1C", "P", "1H", "1S"),
    "1D-P-1S-2C": ("1D", "P", "1S", "2C"),
    "1H-P-1S-2D": ("1H", "P", "1S", "2D"),
}


def run_sayc_support_double_benchmark(
    *,
    start_seed: int = 1,
    count: int = 1000,
    route: str = "1D-P-1H-1S",
    registry: PolicyRegistry | None = None,
    system_options: dict[str, str] | None = None,
) -> SaycSupportDoubleBenchmarkReport:
    """Benchmark the Phase 9R production Support Double example slice.

    The four-call auction prefix is entirely scripted. Only opener's fifth call
    is produced by the production SAYC router. An eligibility policy, if used,
    is supplied explicitly by the caller and is never installed as a default.
    """
    key = route.strip().upper()
    try:
        prefix = _SUPPORT_DOUBLE_PREFIXES[key]
    except KeyError as exc:
        raise ValueError(
            "route must be one of " + ", ".join(_SUPPORT_DOUBLE_PREFIXES)
        ) from exc
    if registry is None:
        registry = PolicyRegistry()
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    options = {} if system_options is None else dict(system_options)

    @dataclass(frozen=True, slots=True)
    class _ScriptedCallRule:
        rule_id: str
        call_text: str
        def evaluate(self, context):
            return RuleDecision.recommend(
                rule_id=self.rule_id,
                candidate=Call.parse(self.call_text),
                explanation="Scripted Support-Double benchmark prefix; not a production recommendation.",
                sources=(_FIXTURE_SOURCE,),
                priority=1,
            )

    # With North dealer, seats act N,E,S,W,N. Script the first four calls;
    # North then uses the production router as opener.
    def engines(deal):
        router = create_standard_sayc_router(registry)
        return {
            Seat.NORTH: BiddingEngine((
                _ScriptedCallRule("benchmark.fixture.support.opening", prefix[0]),
                # BiddingEngine may see both rules at turn 1, so a single
                # state-aware rule is supplied below by wrapper construction.
            )),
            Seat.EAST: BiddingEngine((_ScriptedCallRule("benchmark.fixture.support.pass", prefix[1]),)),
            Seat.SOUTH: BiddingEngine((_ScriptedCallRule("benchmark.fixture.support.response", prefix[2]),)),
            Seat.WEST: BiddingEngine((_ScriptedCallRule("benchmark.fixture.support.overcall", prefix[3]),)),
        }

    @dataclass(frozen=True, slots=True)
    class _NorthFixtureThenProduction:
        fixture: object
        router: object
        def evaluate(self, context):
            if len(context.auction) == 0:
                return BiddingEngine((self.fixture,)).evaluate(context)
            return self.router.evaluate(context)

    def actual_engines(deal):
        router=create_standard_sayc_router(registry)
        return {
            Seat.NORTH: _NorthFixtureThenProduction(
                _ScriptedCallRule("benchmark.fixture.support.opening", prefix[0]), router
            ),
            Seat.EAST: BiddingEngine((_ScriptedCallRule("benchmark.fixture.support.pass", prefix[1]),)),
            Seat.SOUTH: BiddingEngine((_ScriptedCallRule("benchmark.fixture.support.response", prefix[2]),)),
            Seat.WEST: BiddingEngine((_ScriptedCallRule("benchmark.fixture.support.overcall", prefix[3]),)),
        }

    def systems(deal):
        return {seat: SystemContext.from_mapping("SAYC", options) for seat in Seat}

    batch=run_seeded_batch(
        start_seed=start_seed, count=count, engine_factory=actual_engines,
        system_factory=systems, dealer=Seat.NORTH, max_steps=5,
    )

    responder_suit = "H" if prefix[2] == "1H" else "S"
    from .models import Suit
    suit = Suit.HEARTS if responder_suit == "H" else Suit.SPADES

    reached=three=actions=abstentions=0
    rules=Counter()
    for case in batch.cases:
        steps=case.result.steps
        if len(steps)>=4 and tuple(x.call.serialize() for x in steps[:4]) == prefix:
            reached += 1
            # Opener is North in this controlled benchmark.
            if case.deal.mapping[Seat.NORTH].length(suit) == 3:
                three += 1
            if len(steps)>=5 and steps[4].rule_id == "sayc.double.support.example_slice":
                actions += 1
                rules[steps[4].rule_id] += 1
            elif case.result.stopped_seat is Seat.NORTH:
                abstentions += 1

    return SaycSupportDoubleBenchmarkReport(
        batch,
        SaycSupportDoubleMetrics(
            runs=count, auction_prefix=prefix, positions_reached=reached,
            exactly_three_support=three, support_double_actions=actions,
            abstentions=abstentions, production_rule_counts=tuple(sorted(rules.items())),
        ),
    )


@dataclass(frozen=True, slots=True)
class SaycDirectOneNotrumpMetrics:
    runs: int
    opening: str
    direct_positions_reached: int
    hcp_15_18_balanced: int
    one_notrump_actions: int
    abstentions: int
    production_rule_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class SaycDirectOneNotrumpBenchmarkReport:
    batch: BatchSimulationReport
    metrics: SaycDirectOneNotrumpMetrics


def run_sayc_direct_one_notrump_benchmark(
    *,
    start_seed: int = 1,
    count: int = 1000,
    opening: str = "1H",
    registry: PolicyRegistry | None = None,
    system_options: dict[str, str] | None = None,
) -> SaycDirectOneNotrumpBenchmarkReport:
    """Benchmark the production Phase 9U direct 1NT route.

    North's one-level suit opening is scripted. East alone uses the production
    SAYC router. A stopper policy, if desired, must be explicitly supplied by
    the caller; this harness never installs a production default.
    """
    opening = opening.strip().upper()
    if opening not in _ALLOWED_OPENINGS:
        raise ValueError("opening must be one of 1C, 1D, 1H, 1S")
    if registry is None:
        registry = PolicyRegistry()
    if not isinstance(registry, PolicyRegistry):
        raise TypeError("registry must be PolicyRegistry")
    options = {} if system_options is None else dict(system_options)

    def engines(deal):
        router = create_standard_sayc_router(registry)
        return {
            Seat.NORTH: BiddingEngine((_ScriptedOpponentRule(
                "benchmark.fixture.opponent.north", opening
            ),)),
            Seat.EAST: router,
            Seat.SOUTH: BiddingEngine((_ScriptedOpponentRule(
                "benchmark.fixture.opponent.south"
            ),)),
            Seat.WEST: router,
        }

    def systems(deal):
        return {seat: SystemContext.from_mapping("SAYC", options) for seat in Seat}

    batch = run_seeded_batch(
        start_seed=start_seed,
        count=count,
        engine_factory=engines,
        system_factory=systems,
        dealer=Seat.NORTH,
        max_steps=2,
    )

    reached = objective = actions = abstentions = 0
    rules = Counter()
    for case in batch.cases:
        steps = case.result.steps
        if steps and steps[0].rule_id == "benchmark.fixture.opponent.north":
            reached += 1
            east = case.deal.mapping[Seat.EAST]
            from .evaluation import evaluate_hand
            ev = evaluate_hand(east)
            if 15 <= ev.hcp <= 18 and ev.is_balanced:
                objective += 1

            if len(steps) >= 2 and steps[1].rule_id == "sayc.overcall.direct.1nt":
                actions += 1
                rules[steps[1].rule_id] += 1
            elif case.result.stopped_seat is Seat.EAST:
                abstentions += 1

    return SaycDirectOneNotrumpBenchmarkReport(
        batch,
        SaycDirectOneNotrumpMetrics(
            runs=count,
            opening=opening,
            direct_positions_reached=reached,
            hcp_15_18_balanced=objective,
            one_notrump_actions=actions,
            abstentions=abstentions,
            production_rule_counts=tuple(sorted(rules.items())),
        ),
    )
