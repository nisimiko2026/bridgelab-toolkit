"""Theory-neutral routing between existing bidding engines.

Routing decides *which* already-configured engine owns a position.  It does not
contain bidding rules and does not manufacture recommendations.

Routes are explicit predicates over ``BiddingContext``.  More specific routes
may be assigned higher priority.  Equal-priority matches are resolved by
registration order, making routing deterministic and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable

from .bidding_engine import BiddingEngine, BiddingEngineResult
from .bidding_rules import BiddingContext


ContextMatcher = Callable[[BiddingContext], bool]


@runtime_checkable
class RecommendationEngine(Protocol):
    """Minimal engine contract required by simulation and routing."""

    def evaluate(self, context: BiddingContext) -> BiddingEngineResult: ...


@dataclass(frozen=True, slots=True)
class EngineRoute:
    route_id: str
    matcher: ContextMatcher
    engine: RecommendationEngine
    priority: int = 0

    def __post_init__(self) -> None:
        route_id = self.route_id.strip()
        if not route_id:
            raise ValueError("route_id must not be blank")
        object.__setattr__(self, "route_id", route_id)
        if not callable(self.matcher):
            raise TypeError("matcher must be callable")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise TypeError("priority must be an integer")
        if not isinstance(self.engine, RecommendationEngine):
            raise TypeError("engine must satisfy RecommendationEngine")


@dataclass(frozen=True, slots=True)
class EngineRouteMatch:
    route_id: str
    priority: int
    registration_order: int
    engine: RecommendationEngine


class BiddingEngineRouter:
    """Select one existing engine for the current bidding context."""

    def __init__(
        self,
        routes=(),
        *,
        fallback: RecommendationEngine | None = None,
    ) -> None:
        collected=tuple(routes)
        seen=set()
        for route in collected:
            if not isinstance(route, EngineRoute):
                raise TypeError("routes must contain EngineRoute values")
            key=route.route_id.casefold()
            if key in seen:
                raise ValueError(f"duplicate route_id: {route.route_id}")
            seen.add(key)
        if fallback is not None and not isinstance(fallback, RecommendationEngine):
            raise TypeError("fallback must satisfy RecommendationEngine")
        self._routes=collected
        self._fallback=fallback

    @property
    def routes(self) -> tuple[EngineRoute, ...]:
        return self._routes

    def match(self, context: BiddingContext) -> EngineRouteMatch | None:
        if not isinstance(context, BiddingContext):
            raise TypeError("context must be BiddingContext")

        matches=[]
        for order,route in enumerate(self._routes):
            result=route.matcher(context)
            if not isinstance(result,bool):
                raise TypeError(f"route matcher {route.route_id!r} must return bool")
            if result:
                matches.append((order,route))

        if not matches:
            return None

        matches.sort(key=lambda item:(-item[1].priority,item[0],item[1].route_id.casefold()))
        order,route=matches[0]
        return EngineRouteMatch(route.route_id,route.priority,order,route.engine)

    def resolve(self, context: BiddingContext) -> RecommendationEngine | None:
        matched=self.match(context)
        if matched is not None:
            return matched.engine
        return self._fallback

    def evaluate(self, context: BiddingContext) -> BiddingEngineResult:
        engine=self.resolve(context)
        if engine is None:
            # Same abstention shape as an empty BiddingEngine, without guessing.
            return BiddingEngine(()).evaluate(context)
        return engine.evaluate(context)


def auction_calls(*calls: str) -> ContextMatcher:
    """Create an exact-auction matcher from serialized call tokens.

    This helper is mechanics-only.  The caller chooses which auction belongs
    to which engine; no system meaning is embedded here.
    """
    expected=" ".join(c.strip().upper() for c in calls)

    def matches(context: BiddingContext) -> bool:
        return context.auction.serialize().upper() == expected

    return matches
