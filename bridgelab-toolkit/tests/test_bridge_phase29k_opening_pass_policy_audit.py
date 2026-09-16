import json

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import BiddingContext, KnowledgeSource, RuleDecision, SystemContext
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.models import Hand, Seat, Vulnerability
from bridge.opening_pass_policy_audit import (
    OpeningPassSupport, audit_passed_out_auction, build_opening_pass_policy_report,
)
from bridge.sayc_route_configuration import create_standard_sayc_router


class _PassRule:
    rule_id = "fixture.explicit.pass"

    def evaluate(self, context):
        return RuleDecision.recommend(
            rule_id=self.rule_id, candidate=Call.parse("P"), priority=1,
            explanation="Explicit test-only Pass.",
            sources=(KnowledgeSource("bidding/systems/sayc", "Opening Bid Requirements"),),
        )


def test_canonical_pass_and_result_contract_support():
    assert Call.parse("P").serialize() == "P"
    auction = Auction(Seat.NORTH)
    assert Call.parse("P") in auction.legal_calls()
    auction.add("P")
    assert auction.next_seat is Seat.EAST
    context = BiddingContext.create(hand=Hand.parse("AKQ.JT9.8765.432"), auction=Auction(Seat.NORTH),
                                    vulnerability=Vulnerability.NONE, system=SystemContext("SAYC"))
    assert BiddingEngine((_PassRule(),)).evaluate(context).recommended_call == Call.parse("P")


def test_passed_out_auction_is_canonical():
    finding = audit_passed_out_auction()
    assert finding.calls == ("P", "P", "P", "P")
    assert finding.actors == ("N", "E", "S", "W")
    assert finding.complete_after_each == (False, False, False, True)
    assert finding.is_passed_out and finding.final_contract is None


def test_1000_deal_source_readiness_is_deterministic_and_bounded():
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    report = build_opening_pass_policy_report(batch)
    assert (report.depth0_abstains, report.diagnostic_screen_count,
            report.pass_supported_count, report.source_insufficient_count,
            report.coverage_boundary_count) == (616, 542, 0, 542, 3)
    assert len(report.representatives) <= 6
    assert all(case.support is not OpeningPassSupport.SOURCE_INSUFFICIENT or case.hcp <= 11
               for case in report.representatives)
    strong = [case for case in report.representatives if case.support is OpeningPassSupport.CURRENT_COVERAGE_BOUNDARY]
    assert [case.deal_index for case in strong] == [57, 184, 613]
    assert not any(hasattr(case, "deal") for case in report.representatives)
    assert json.loads(report.to_json()) == report.to_dict()
    assert report.to_json() == build_opening_pass_policy_report(batch).to_json()
    assert len(create_standard_sayc_router().routes) == 45
