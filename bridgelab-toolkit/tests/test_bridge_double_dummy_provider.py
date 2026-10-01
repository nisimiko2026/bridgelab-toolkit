import unittest

from bridge.capability_providers import (
    Capability,
    DoubleDummyProvider,
    ProviderDescriptor,
)
from bridge.double_dummy_provider import TrickSolverDoubleDummyProvider
from bridge.models import Seat, Suit
from bridge.trick_solver import (
    TrickSolverResult,
    TrickSolverStatus,
)


class FakeTrickSolver:
    def __init__(self, result: TrickSolverResult):
        self.result = result
        self.calls = []

    def solve(
        self,
        deal,
        declarer,
        strain,
        *,
        opening_lead=None,
    ) -> TrickSolverResult:
        self.calls.append(
            (deal, declarer, strain, opening_lead)
        )
        return self.result


class MissingSolve:
    pass


class DoubleDummyProviderTests(unittest.TestCase):

    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="test.double-dummy",
            capability=Capability.DOUBLE_DUMMY,
            implementation="fake-trick-solver",
            version="1",
        )

    def result(
        self,
        *,
        status: TrickSolverStatus = TrickSolverStatus.SUCCESS,
        tricks: int | None = 9,
        error: str | None = None,
    ) -> TrickSolverResult:
        return TrickSolverResult(
            implementation="fake-trick-solver",
            version="1",
            deal_id="deal-1",
            declarer=Seat.SOUTH,
            strain=Suit.SPADES,
            opening_lead=None,
            status=status,
            maximum_declarer_tricks=tricks,
            elapsed_seconds=0.01,
            error=error,
        )

    def test_adapter_satisfies_double_dummy_provider_protocol(self) -> None:
        solver = FakeTrickSolver(self.result())

        provider = TrickSolverDoubleDummyProvider(
            solver=solver,
            descriptor=self.descriptor(),
        )

        self.assertIsInstance(provider, DoubleDummyProvider)

    def test_descriptor_must_be_double_dummy_capability(self) -> None:
        descriptor = ProviderDescriptor(
            provider_id="wrong.capability",
            capability=Capability.BIDDING,
            implementation="fake-trick-solver",
        )

        with self.assertRaises(ValueError):
            TrickSolverDoubleDummyProvider(
                solver=FakeTrickSolver(self.result()),
                descriptor=descriptor,
            )

    def test_solver_must_expose_callable_solve(self) -> None:
        with self.assertRaises(TypeError):
            TrickSolverDoubleDummyProvider(
                solver=MissingSolve(),
                descriptor=self.descriptor(),
            )

    def test_success_result_is_returned_unchanged(self) -> None:
        expected = self.result()
        solver = FakeTrickSolver(expected)

        provider = TrickSolverDoubleDummyProvider(
            solver=solver,
            descriptor=self.descriptor(),
        )

        deal = object()

        actual = provider.solve(
            deal,
            Seat.SOUTH,
            Suit.SPADES,
        )

        self.assertIs(actual, expected)
        self.assertEqual(
            solver.calls,
            [(deal, Seat.SOUTH, Suit.SPADES, None)],
        )
        self.assertEqual(
            actual.status,
            TrickSolverStatus.SUCCESS,
        )
        self.assertEqual(
            actual.maximum_declarer_tricks,
            9,
        )

    def test_unavailable_result_is_not_replaced_by_heuristic(self) -> None:
        expected = self.result(
            status=TrickSolverStatus.UNAVAILABLE,
            tricks=None,
            error="solver unavailable",
        )
        solver = FakeTrickSolver(expected)

        provider = TrickSolverDoubleDummyProvider(
            solver=solver,
            descriptor=self.descriptor(),
        )

        actual = provider.solve(
            object(),
            Seat.SOUTH,
            Suit.SPADES,
        )

        self.assertIs(actual, expected)
        self.assertEqual(
            actual.status,
            TrickSolverStatus.UNAVAILABLE,
        )
        self.assertIsNone(actual.maximum_declarer_tricks)

    def test_failed_result_is_not_replaced_by_heuristic(self) -> None:
        expected = self.result(
            status=TrickSolverStatus.FAILED,
            tricks=None,
            error="solver failure",
        )
        solver = FakeTrickSolver(expected)

        provider = TrickSolverDoubleDummyProvider(
            solver=solver,
            descriptor=self.descriptor(),
        )

        actual = provider.solve(
            object(),
            Seat.SOUTH,
            Suit.SPADES,
        )

        self.assertIs(actual, expected)
        self.assertEqual(
            actual.status,
            TrickSolverStatus.FAILED,
        )
        self.assertIsNone(actual.maximum_declarer_tricks)


if __name__ == "__main__":
    unittest.main()
