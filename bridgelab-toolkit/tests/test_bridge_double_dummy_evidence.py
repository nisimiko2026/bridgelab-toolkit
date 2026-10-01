import unittest

from bridge.capability_providers import Capability, ProviderDescriptor
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.models import Seat, Suit
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


def descriptor() -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id="dds.test",
        capability=Capability.DOUBLE_DUMMY,
        implementation="fake-dds",
        version="1",
    )


def result(
    status=TrickSolverStatus.SUCCESS,
    tricks=9,
) -> TrickSolverResult:
    if status is not TrickSolverStatus.SUCCESS:
        tricks = None

    return TrickSolverResult(
        implementation="fake-dds",
        version="1",
        deal_id="deal-1",
        declarer=Seat.SOUTH,
        strain=Suit.HEARTS,
        opening_lead=None,
        status=status,
        maximum_declarer_tricks=tricks,
        elapsed_seconds=0.01,
    )


class DoubleDummyEvidenceTests(unittest.TestCase):

    def test_records_successful_reference_measurement(self) -> None:
        evidence = DoubleDummyEvidence(
            provider=descriptor(),
            result=result(),
            source_ids=("board-1",),
            notes=("reference measurement",),
        )

        self.assertEqual(
            evidence.status,
            TrickSolverStatus.SUCCESS,
        )
        self.assertEqual(
            evidence.maximum_declarer_tricks,
            9,
        )

    def test_preserves_unavailable_without_fabricating_tricks(self) -> None:
        evidence = DoubleDummyEvidence(
            provider=descriptor(),
            result=result(TrickSolverStatus.UNAVAILABLE),
        )

        self.assertEqual(
            evidence.status,
            TrickSolverStatus.UNAVAILABLE,
        )
        self.assertIsNone(
            evidence.maximum_declarer_tricks,
        )

    def test_preserves_failed_without_fabricating_tricks(self) -> None:
        evidence = DoubleDummyEvidence(
            provider=descriptor(),
            result=result(TrickSolverStatus.FAILED),
        )

        self.assertEqual(
            evidence.status,
            TrickSolverStatus.FAILED,
        )
        self.assertIsNone(
            evidence.maximum_declarer_tricks,
        )

    def test_rejects_non_double_dummy_provider(self) -> None:
        bad = ProviderDescriptor(
            provider_id="bid.test",
            capability=Capability.BIDDING,
            implementation="fake-bidder",
        )

        with self.assertRaises(ValueError):
            DoubleDummyEvidence(
                provider=bad,
                result=result(),
            )

    def test_requires_trick_solver_result(self) -> None:
        with self.assertRaises(TypeError):
            DoubleDummyEvidence(
                provider=descriptor(),
                result=object(),
            )

    def test_rejects_non_tuple_provenance(self) -> None:
        with self.assertRaises(TypeError):
            DoubleDummyEvidence(
                provider=descriptor(),
                result=result(),
                source_ids=["board-1"],
            )

    def test_rejects_blank_provenance_entries(self) -> None:
        with self.assertRaises(ValueError):
            DoubleDummyEvidence(
                provider=descriptor(),
                result=result(),
                source_ids=("board-1", ""),
            )


if __name__ == "__main__":
    unittest.main()
