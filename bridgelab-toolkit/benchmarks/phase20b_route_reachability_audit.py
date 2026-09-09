"""Phase 20B audit of production SAYC route identity and reachability.

This module observes the current production router.  Structural witnesses prove
only exact-prefix dispatch; they do not claim rule applicability, recommendation
production, or semantic bridge correctness.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.models import Hand, Seat, Vulnerability
from bridge.sayc_route_configuration import create_standard_sayc_router


class OwnershipClassification(str, Enum):
    UNIQUE_OWNER = "UNIQUE_OWNER"
    SHARED_OWNER_EXPECTED = "SHARED_OWNER_EXPECTED"
    DUPLICATE_ROUTE_ID = "DUPLICATE_ROUTE_ID"
    MISSING_OWNER = "MISSING_OWNER"
    AMBIGUOUS_OWNER = "AMBIGUOUS_OWNER"


class PrefixCollisionClassification(str, Enum):
    UNIQUE_EXACT_PREFIX = "UNIQUE_EXACT_PREFIX"
    DUPLICATE_EXACT_PREFIX = "DUPLICATE_EXACT_PREFIX"


class ConfigurationReachability(str, Enum):
    REACHABLE = "REACHABLE"
    REACHABLE_POLICY_GATED = "REACHABLE_POLICY_GATED"
    SHADOWED = "SHADOWED"
    DUPLICATE_PREFIX = "DUPLICATE_PREFIX"
    INVALID_PREFIX = "INVALID_PREFIX"
    UNREACHABLE_CONFIGURATION = "UNREACHABLE_CONFIGURATION"
    UNKNOWN = "UNKNOWN"


class WitnessStatus(str, Enum):
    EXISTING_WITNESS = "EXISTING_WITNESS"
    DERIVABLE_WITHOUT_BRIDGE_THEORY = "DERIVABLE_WITHOUT_BRIDGE_THEORY"
    REQUIRES_SEMANTIC_HAND_FIXTURE = "REQUIRES_SEMANTIC_HAND_FIXTURE"
    NO_SAFE_WITNESS = "NO_SAFE_WITNESS"


class ObservedBenchmarkStatus(str, Enum):
    OBSERVED = "OBSERVED"
    NOT_OBSERVED = "NOT_OBSERVED"
    UNKNOWN = "UNKNOWN"


class PolicyState(str, Enum):
    NO_POLICY_REQUIRED = "NO_POLICY_REQUIRED"
    POLICY_PRESENT = "POLICY_PRESENT"
    POLICY_ABSENT_ABSTAIN = "POLICY_ABSENT_ABSTAIN"
    POLICY_PRESENT_ABSTAIN = "POLICY_PRESENT_ABSTAIN"
    POLICY_PRESENT_RECOMMEND = "POLICY_PRESENT_RECOMMEND"


@dataclass(frozen=True, slots=True)
class RouteInventoryEntry:
    registration_order: int
    route_id: str
    auction_prefix: tuple[str, ...]
    priority: int
    engine_type: str
    production_modules: tuple[str, ...]
    rule_ids: tuple[str, ...]
    subsystem: str
    policy_dependencies: tuple[str, ...]
    ownership: OwnershipClassification
    prefix_collision: PrefixCollisionClassification
    configuration_reachability: ConfigurationReachability
    witness_status: WitnessStatus
    observed_benchmark_status: ObservedBenchmarkStatus


@dataclass(frozen=True, slots=True)
class RouteReachabilityAudit:
    inventory: tuple[RouteInventoryEntry, ...]
    route_count: int
    unique_route_ids: int
    unique_exact_prefixes: int
    structurally_matched_routes: int
    policy_gated_routes: int
    invalid_prefixes: int
    shadowed_routes: int
    unreachable_routes: int
    missing_owners: int
    duplicate_route_ids: int
    ambiguous_owners: int
    duplicate_exact_prefixes: int
    historical_recommendation_baseline: int = 4
    ordinary_production_calls: int = 7_871
    ordinary_completed_auctions: int = 761
    ordinary_abstaining_deals: int = 9_239


_STRUCTURAL_HAND = Hand.parse("AKQJ9.KQ3.JT8.32")

# Existing production policy roles, derived from rule/module identity.  These
# names document dependencies only; this audit never supplies a policy.
_RULE_POLICY_MARKERS: tuple[tuple[str, str], ...] = (
    ("sayc.overcall.one_level.natural", "suit_quality"),
    ("sayc.overcall.one_level.natural", "playing_strength"),
    ("sayc.overcall.weak_jump", "offensive_hand"),
    ("sayc.double.takeout.direct", "opponent_suit_shortness"),
    ("sayc.overcall.direct.1nt", "stopper"),
    ("sayc.advancer.takeout.minimum.natural", "takeout_advancer_strength"),
    ("sayc.double.support.example_slice", "support_double_eligibility"),
    ("sayc.responder.1nt.jacoby.continuation", "jacoby_continuation_strength"),
    ("sayc.opener.1nt.stayman", "stayman_dual_major_response"),
    ("sayc.responder.1nt.stayman.major_fit.game", "stayman_continuation_strength"),
)


def _exact_prefix(matcher: object) -> tuple[str, ...]:
    """Read the immutable expected string captured by ``auction_calls``."""
    closure = getattr(matcher, "__closure__", None)
    captured = () if closure is None else tuple(cell.cell_contents for cell in closure)
    expected = tuple(value for value in captured if isinstance(value, str))
    if len(expected) != 1:
        raise ValueError("route matcher is not an inspectable exact-auction matcher")
    return tuple(expected[0].split())


def _rule_registry(engine: object) -> tuple[object, ...]:
    rules = getattr(engine, "rules", None)
    if rules is None:
        return ()
    return tuple(rules)


def _policy_dependencies(rule_ids: tuple[str, ...]) -> tuple[str, ...]:
    dependencies = {
        dependency
        for rule_id in rule_ids
        for marker, dependency in _RULE_POLICY_MARKERS
        if rule_id == marker
    }
    if any(rule_id.startswith("sayc.response.1") and ".2over1" in rule_id for rule_id in rule_ids):
        dependencies.add("suit_quality")
    return tuple(sorted(dependencies))


def structural_context(prefix: tuple[str, ...]) -> BiddingContext:
    """Build a public mechanics-only context for exact route dispatch."""
    auction = Auction(Seat.NORTH, prefix)
    return BiddingContext.create(
        hand=_STRUCTURAL_HAND,
        auction=auction,
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


def run_route_reachability_audit() -> RouteReachabilityAudit:
    router = create_standard_sayc_router()
    routes = router.routes
    route_id_counts = Counter(route.route_id.casefold() for route in routes)

    prefixes: list[tuple[str, ...] | None] = []
    rules_by_route: list[tuple[object, ...]] = []
    for route in routes:
        try:
            prefix: tuple[str, ...] | None = _exact_prefix(route.matcher)
        except (AttributeError, ValueError):
            prefix = None
        prefixes.append(prefix)
        rules_by_route.append(_rule_registry(route.engine))

    prefix_counts = Counter(prefix for prefix in prefixes if prefix is not None)
    owner_signatures = [
        tuple((type(rule).__module__, getattr(rule, "rule_id", "")) for rule in rules)
        for rules in rules_by_route
    ]
    owner_counts = Counter(owner_signatures)

    entries: list[RouteInventoryEntry] = []
    for order, (route, prefix, rules, owner_signature) in enumerate(
        zip(routes, prefixes, rules_by_route, owner_signatures, strict=True)
    ):
        rule_ids = tuple(str(getattr(rule, "rule_id", "")) for rule in rules)
        modules = tuple(sorted({type(rule).__module__ for rule in rules}))
        dependencies = _policy_dependencies(rule_ids)

        duplicate_id = route_id_counts[route.route_id.casefold()] > 1
        missing_owner = not rules
        duplicate_prefix = prefix is not None and prefix_counts[prefix] > 1
        if duplicate_id:
            ownership = OwnershipClassification.DUPLICATE_ROUTE_ID
        elif missing_owner:
            ownership = OwnershipClassification.MISSING_OWNER
        elif len(rules) == 1 and owner_counts[owner_signature] == 1:
            ownership = OwnershipClassification.UNIQUE_OWNER
        else:
            ownership = OwnershipClassification.SHARED_OWNER_EXPECTED

        collision = (
            PrefixCollisionClassification.DUPLICATE_EXACT_PREFIX
            if duplicate_prefix
            else PrefixCollisionClassification.UNIQUE_EXACT_PREFIX
        )

        if prefix is None:
            reachability = ConfigurationReachability.INVALID_PREFIX
            witness = WitnessStatus.NO_SAFE_WITNESS
        else:
            try:
                context = structural_context(prefix)
            except (TypeError, ValueError):
                reachability = ConfigurationReachability.INVALID_PREFIX
                witness = WitnessStatus.NO_SAFE_WITNESS
            else:
                match = router.match(context)
                witness = WitnessStatus.DERIVABLE_WITHOUT_BRIDGE_THEORY
                if duplicate_prefix:
                    reachability = ConfigurationReachability.DUPLICATE_PREFIX
                elif match is None:
                    reachability = ConfigurationReachability.UNREACHABLE_CONFIGURATION
                elif match.route_id != route.route_id:
                    reachability = ConfigurationReachability.SHADOWED
                elif dependencies:
                    reachability = ConfigurationReachability.REACHABLE_POLICY_GATED
                else:
                    reachability = ConfigurationReachability.REACHABLE

        entries.append(
            RouteInventoryEntry(
                registration_order=order,
                route_id=route.route_id,
                auction_prefix=() if prefix is None else prefix,
                priority=route.priority,
                engine_type=f"{type(route.engine).__module__}.{type(route.engine).__qualname__}",
                production_modules=modules,
                rule_ids=rule_ids,
                subsystem="BIDDING",
                policy_dependencies=dependencies,
                ownership=ownership,
                prefix_collision=collision,
                configuration_reachability=reachability,
                witness_status=witness,
                observed_benchmark_status=ObservedBenchmarkStatus.UNKNOWN,
            )
        )

    inventory = tuple(entries)
    return RouteReachabilityAudit(
        inventory=inventory,
        route_count=len(inventory),
        unique_route_ids=len(route_id_counts),
        unique_exact_prefixes=len(prefix_counts),
        structurally_matched_routes=sum(
            entry.configuration_reachability
            in {ConfigurationReachability.REACHABLE, ConfigurationReachability.REACHABLE_POLICY_GATED}
            for entry in inventory
        ),
        policy_gated_routes=sum(bool(entry.policy_dependencies) for entry in inventory),
        invalid_prefixes=sum(
            entry.configuration_reachability is ConfigurationReachability.INVALID_PREFIX
            for entry in inventory
        ),
        shadowed_routes=sum(
            entry.configuration_reachability is ConfigurationReachability.SHADOWED
            for entry in inventory
        ),
        unreachable_routes=sum(
            entry.configuration_reachability is ConfigurationReachability.UNREACHABLE_CONFIGURATION
            for entry in inventory
        ),
        missing_owners=sum(
            entry.ownership is OwnershipClassification.MISSING_OWNER for entry in inventory
        ),
        duplicate_route_ids=sum(count - 1 for count in route_id_counts.values() if count > 1),
        ambiguous_owners=sum(
            entry.ownership is OwnershipClassification.AMBIGUOUS_OWNER for entry in inventory
        ),
        duplicate_exact_prefixes=sum(count - 1 for count in prefix_counts.values() if count > 1),
    )


def _print_summary(audit: RouteReachabilityAudit) -> None:
    labels = (
        ("routes", audit.route_count),
        ("unique route IDs", audit.unique_route_ids),
        ("unique exact prefixes", audit.unique_exact_prefixes),
        ("structurally matched routes", audit.structurally_matched_routes),
        ("policy-gated routes", audit.policy_gated_routes),
        ("invalid prefixes", audit.invalid_prefixes),
        ("shadowed routes", audit.shadowed_routes),
        ("unreachable routes", audit.unreachable_routes),
        ("missing owners", audit.missing_owners),
        ("duplicate route IDs", audit.duplicate_route_ids),
        ("ambiguous owners", audit.ambiguous_owners),
        ("duplicate exact prefixes", audit.duplicate_exact_prefixes),
    )
    for label, value in labels:
        print(f"{label} = {value}")


if __name__ == "__main__":
    _print_summary(run_route_reachability_audit())
