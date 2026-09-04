from __future__ import annotations

import unittest

from bridge import Auction, BiddingContext, Hand, KnowledgeSource, Seat, Suit, SystemContext, Vulnerability
from bridge.policy_registry import (
    PolicyRegistry,
    assess_configured_stopper,
    configured_stopper_policy_id,
    resolve_stopper_policy,
)
from bridge.stopper_policy import StopperAssessment, StopperStatus


SOURCE = (
    KnowledgeSource("bidding/natural-bids/responses/response-to-1-diamond", "Notrump Responses"),
)


def context(*, policy: str | None = None) -> BiddingContext:
    options = {} if policy is None else {"stopper_policy": policy}
    return BiddingContext.create(
        hand=Hand.parse("AQ84.KJ6.T75.932"),
        auction=Auction(Seat.NORTH, ("1D", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC", options),
    )


class _FixturePolicy:
    def __init__(self, policy_id: str, status: StopperStatus) -> None:
        self.policy_id = policy_id
        self.status = status

    def assess(self, ctx: BiddingContext, suit: Suit) -> StopperAssessment:
        evidence = ctx.evaluation.honor_evidence(suit)
        if self.status is StopperStatus.UNKNOWN:
            return StopperAssessment.unknown(
                policy_id=self.policy_id,
                evidence=evidence,
                explanation="Fixture unknown.",
            )
        if self.status is StopperStatus.STOPPED:
            return StopperAssessment.stopped(
                policy_id=self.policy_id,
                evidence=evidence,
                explanation="Fixture stopped.",
                sources=SOURCE,
            )
        return StopperAssessment.not_stopped(
            policy_id=self.policy_id,
            evidence=evidence,
            explanation="Fixture not stopped.",
            sources=SOURCE,
        )


class PolicyRegistryTests(unittest.TestCase):
    def test_empty_registry(self) -> None:
        self.assertEqual(PolicyRegistry().stopper_policy_ids, ())

    def test_deterministic_id_order(self) -> None:
        registry = PolicyRegistry.from_stopper_policies([
            _FixturePolicy("zeta", StopperStatus.UNKNOWN),
            _FixturePolicy("Alpha", StopperStatus.UNKNOWN),
        ])
        self.assertEqual(registry.stopper_policy_ids, ("Alpha", "zeta"))

    def test_duplicate_ids_case_insensitive(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            PolicyRegistry.from_stopper_policies([
                _FixturePolicy("One", StopperStatus.UNKNOWN),
                _FixturePolicy("one", StopperStatus.UNKNOWN),
            ])

    def test_lookup_case_insensitive(self) -> None:
        policy = _FixturePolicy("Partnership.Stopper", StopperStatus.UNKNOWN)
        registry = PolicyRegistry.from_stopper_policies([policy])
        self.assertIs(registry.stopper_policy("partnership.stopper"), policy)

    def test_missing_lookup_returns_none(self) -> None:
        self.assertIsNone(PolicyRegistry().stopper_policy("missing"))

    def test_configured_id_reads_system_option(self) -> None:
        self.assertEqual(
            configured_stopper_policy_id(context(policy="fixture").system),
            "fixture",
        )

    def test_missing_configuration_returns_none(self) -> None:
        self.assertIsNone(configured_stopper_policy_id(context().system))

    def test_resolver_returns_selected_policy(self) -> None:
        policy = _FixturePolicy("fixture", StopperStatus.UNKNOWN)
        registry = PolicyRegistry.from_stopper_policies([policy])
        self.assertIs(
            resolve_stopper_policy(context(policy="fixture").system, registry),
            policy,
        )

    def test_resolver_missing_registry_entry_returns_none(self) -> None:
        self.assertIsNone(
            resolve_stopper_policy(context(policy="fixture").system, PolicyRegistry())
        )

    def test_assessment_without_configuration_returns_none(self) -> None:
        registry = PolicyRegistry.from_stopper_policies([
            _FixturePolicy("fixture", StopperStatus.STOPPED)
        ])
        self.assertIsNone(
            assess_configured_stopper(context(), registry, Suit.DIAMONDS)
        )

    def test_assessment_missing_named_policy_returns_none(self) -> None:
        self.assertIsNone(
            assess_configured_stopper(
                context(policy="fixture"),
                PolicyRegistry(),
                Suit.DIAMONDS,
            )
        )

    def test_assessment_uses_resolved_policy(self) -> None:
        registry = PolicyRegistry.from_stopper_policies([
            _FixturePolicy("fixture", StopperStatus.STOPPED)
        ])
        result = assess_configured_stopper(
            context(policy="fixture"),
            registry,
            Suit.DIAMONDS,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.status, StopperStatus.STOPPED)
        self.assertEqual(result.sources, SOURCE)

    def test_unknown_policy_result_is_preserved(self) -> None:
        registry = PolicyRegistry.from_stopper_policies([
            _FixturePolicy("fixture", StopperStatus.UNKNOWN)
        ])
        result = assess_configured_stopper(
            context(policy="fixture"),
            registry,
            Suit.DIAMONDS,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.status, StopperStatus.UNKNOWN)

    def test_registry_snapshots_input(self) -> None:
        policies = [_FixturePolicy("a", StopperStatus.UNKNOWN)]
        registry = PolicyRegistry.from_stopper_policies(policies)
        policies.append(_FixturePolicy("b", StopperStatus.UNKNOWN))
        self.assertEqual(registry.stopper_policy_ids, ("a",))

    def test_blank_policy_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PolicyRegistry.from_stopper_policies([
                _FixturePolicy("   ", StopperStatus.UNKNOWN)
            ])

    def test_lookup_requires_string(self) -> None:
        with self.assertRaises(TypeError):
            PolicyRegistry().stopper_policy(123)  # type: ignore[arg-type]

    def test_assess_requires_types(self) -> None:
        with self.assertRaises(TypeError):
            assess_configured_stopper(None, PolicyRegistry(), Suit.DIAMONDS)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            assess_configured_stopper(context(), None, Suit.DIAMONDS)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            assess_configured_stopper(context(), PolicyRegistry(), "D")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
