import unittest

from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case import DecisionCase
from bridge.decision_evidence import (
    DecisionEvidence,
    Disagreement,
    DisagreementKind,
)
from bridge.double_dummy_evidence import DoubleDummyEvidence
from bridge.models import Seat, Suit
from bridge.simulation_statistics import SimulationStatistics
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


def bidding_evidence(provider_id: str) -> DecisionEvidence:
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation="test-bidder",
    )
    result = CapabilityResult(
        provider=descriptor,
        status=ProviderStatus.SUCCESS,
        recommendation="1NT",
    )
    return DecisionEvidence(result=result)


def dd_evidence() -> DoubleDummyEvidence:
    descriptor = ProviderDescriptor(
        provider_id="dds.test",
        capability=Capability.DOUBLE_DUMMY,
        implementation="test-dds",
    )
    result = TrickSolverResult(
        implementation="test-dds",
        version=None,
        deal_id="deal-1",
        declarer=Seat.SOUTH,
        strain=Suit.HEARTS,
        opening_lead=None,
        status=TrickSolverStatus.SUCCESS,
        maximum_declarer_tricks=9,
        elapsed_seconds=0.01,
    )
    return DoubleDummyEvidence(
        provider=descriptor,
        result=result,
    )


def simulation_statistics() -> SimulationStatistics:
    return SimulationStatistics(
        runs=10,
        completed=8,
        abstained=2,
        max_steps=0,
        total_calls_added=30,
        max_calls_added=5,
        stop_reason_counts=(
            ("auction-complete", 8),
            ("no-recommendation", 2),
        ),
        stopped_seat_counts=(),
    )


class DecisionCaseTests(unittest.TestCase):

    def test_minimal_case(self) -> None:
        case = DecisionCase(case_id="case-1")

        self.assertEqual(case.case_id, "case-1")
        self.assertIsNone(case.bridgelab)
        self.assertEqual(case.external, ())
        self.assertEqual(case.corpus, ())
        self.assertEqual(case.simulations, ())
        self.assertEqual(case.double_dummy, ())
        self.assertEqual(case.disagreements, ())

    def test_collects_heterogeneous_evidence(self) -> None:
        bridgelab = bidding_evidence("bridgelab")
        external = bidding_evidence("external")
        dd = dd_evidence()
        simulations = simulation_statistics()

        disagreement = Disagreement(
            kind=DisagreementKind.JUDGMENT_DIFFERENCE,
            left_provider_id="bridgelab",
            right_provider_id="external",
            explanation="Different recommendations.",
        )

        case = DecisionCase(
            case_id="board-17:south:opening",
            bridgelab=bridgelab,
            external=(external,),
            simulations=(simulations,),
            double_dummy=(dd,),
            disagreements=(disagreement,),
            notes=("Evidence retained without voting.",),
        )

        self.assertIs(case.bridgelab, bridgelab)
        self.assertEqual(case.external, (external,))
        self.assertEqual(case.simulations, (simulations,))
        self.assertEqual(case.double_dummy, (dd,))
        self.assertEqual(case.disagreements, (disagreement,))

    def test_preserves_multiple_external_observations(self) -> None:
        first = bidding_evidence("ben")
        second = bidding_evidence("brl")

        case = DecisionCase(
            case_id="case-multi",
            external=(first, second),
        )

        self.assertEqual(
            case.external,
            (first, second),
        )

    def test_preserves_multiple_double_dummy_observations(self) -> None:
        first = dd_evidence()
        second = dd_evidence()

        case = DecisionCase(
            case_id="case-dd",
            double_dummy=(first, second),
        )

        self.assertEqual(
            case.double_dummy,
            (first, second),
        )

    def test_rejects_blank_case_id(self) -> None:
        with self.assertRaises(ValueError):
            DecisionCase(case_id="   ")

    def test_rejects_non_tuple_evidence_collection(self) -> None:
        with self.assertRaises(TypeError):
            DecisionCase(
                case_id="case-1",
                external=[bidding_evidence("external")],
            )

    def test_rejects_wrong_evidence_type(self) -> None:
        with self.assertRaises(TypeError):
            DecisionCase(
                case_id="case-1",
                double_dummy=(bidding_evidence("wrong"),),
            )

    def test_rejects_blank_note(self) -> None:
        with self.assertRaises(ValueError):
            DecisionCase(
                case_id="case-1",
                notes=("valid", ""),
            )


if __name__ == "__main__":
    unittest.main()
