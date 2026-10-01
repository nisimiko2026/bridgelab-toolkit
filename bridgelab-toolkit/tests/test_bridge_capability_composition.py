import unittest

from bridge.capability_composition import register_trick_solver_provider
from bridge.capability_providers import Capability
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.double_dummy_provider import TrickSolverDoubleDummyProvider
from bridge.trick_solver import TrickSolverResult


class FakeTrickSolver:
    def solve(
        self,
        deal,
        declarer,
        strain,
        *,
        opening_lead=None,
    ) -> TrickSolverResult:
        raise AssertionError(
            "composition/registration must not invoke the solver"
        )


class CapabilityCompositionTests(unittest.TestCase):

    def test_registers_trick_solver_as_double_dummy_provider(self) -> None:
        registry = CapabilityProviderRegistry()
        solver = FakeTrickSolver()

        provider = register_trick_solver_provider(
            registry,
            solver,
            provider_id="dds.test",
            implementation="fake-dds",
            version="1",
        )

        self.assertIsInstance(
            provider,
            TrickSolverDoubleDummyProvider,
        )
        self.assertIs(
            registry.require(
                Capability.DOUBLE_DUMMY,
                "dds.test",
            ),
            provider,
        )

    def test_descriptor_is_constructed_explicitly(self) -> None:
        registry = CapabilityProviderRegistry()

        provider = register_trick_solver_provider(
            registry,
            FakeTrickSolver(),
            provider_id="dds.explicit",
            implementation="dds3",
            version="2.9",
        )

        self.assertEqual(
            provider.descriptor.provider_id,
            "dds.explicit",
        )
        self.assertEqual(
            provider.descriptor.capability,
            Capability.DOUBLE_DUMMY,
        )
        self.assertEqual(
            provider.descriptor.implementation,
            "dds3",
        )
        self.assertEqual(
            provider.descriptor.version,
            "2.9",
        )

    def test_multiple_double_dummy_providers_remain_available(self) -> None:
        registry = CapabilityProviderRegistry()

        first = register_trick_solver_provider(
            registry,
            FakeTrickSolver(),
            provider_id="dds.first",
            implementation="first-solver",
        )
        second = register_trick_solver_provider(
            registry,
            FakeTrickSolver(),
            provider_id="dds.second",
            implementation="second-solver",
        )

        self.assertEqual(
            registry.providers_for(Capability.DOUBLE_DUMMY),
            (first, second),
        )

        self.assertIs(
            registry.require(
                Capability.DOUBLE_DUMMY,
                "dds.first",
            ),
            first,
        )
        self.assertIs(
            registry.require(
                Capability.DOUBLE_DUMMY,
                "dds.second",
            ),
            second,
        )

    def test_duplicate_provider_id_is_rejected_by_registry(self) -> None:
        registry = CapabilityProviderRegistry()

        register_trick_solver_provider(
            registry,
            FakeTrickSolver(),
            provider_id="dds.same",
            implementation="solver-a",
        )

        with self.assertRaises(ValueError):
            register_trick_solver_provider(
                registry,
                FakeTrickSolver(),
                provider_id="DDS.SAME",
                implementation="solver-b",
            )

    def test_composition_does_not_invoke_solver(self) -> None:
        registry = CapabilityProviderRegistry()
        solver = FakeTrickSolver()

        register_trick_solver_provider(
            registry,
            solver,
            provider_id="dds.no-call",
            implementation="fake-dds",
        )

        self.assertEqual(
            len(registry.registrations),
            1,
        )

    def test_requires_real_registry(self) -> None:
        with self.assertRaises(TypeError):
            register_trick_solver_provider(
                object(),
                FakeTrickSolver(),
                provider_id="dds.test",
                implementation="fake-dds",
            )


if __name__ == "__main__":
    unittest.main()
