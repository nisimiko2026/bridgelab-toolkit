"""Focused Phase 29J root-cause evidence and production guards."""

import json

from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation, run_simulation
from bridge.deals import generate_deal
from bridge.evaluation import evaluate_hand
from bridge.full_auction_abstention_audit import build_abstention_audit
from bridge.full_auction_coverage import build_full_auction_coverage_report
from bridge.opening_abstention_root_cause_audit import (
    OpeningRootCause, build_opening_root_cause_report,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.sayc import create_sayc_opening_engine
from bridge.models import Hand, Seat, Vulnerability


def test_deal_184_reproduction_and_ordered_decision_trace():
    config = SimulationConfig(seed=100, deal_count=185)
    batch = run_full_auction_simulation(config)
    report = build_opening_root_cause_report(batch)
    case = next(item for item in report.strong_cases if item.deal_index == 184)
    production = batch.auctions[184]
    assert case.hand == production.steps[-1].hand
    assert case.hand == generate_deal(284).hand(production.dealer).serialize()
    assert (case.dealer, case.hcp, case.suit_lengths, case.shape_class) == (
        "N", 20, (5, 5, 3, 0), "unbalanced")
    assert case.hcp == evaluate_hand(generate_deal(284).hand(production.dealer)).hcp
    assert case.root_cause is OpeningRootCause.CONTROLLED_EQUAL_MAJOR_BOUNDARY
    assert case.route_id == "sayc.opening"
    assert case.production_abstention_code == "rule-abstained"
    ids = tuple(trace.rule_id for trace in case.rule_trace)
    assert ids[:7] == ("sayc.opening.2c", "sayc.opening.1nt", "sayc.opening.2nt",
                       "sayc.opening.1h", "sayc.opening.1s",
                       "sayc.opening.1c", "sayc.opening.1d")
    assert "strictly longer" in case.rule_trace[3].explanation
    assert "strictly longer" in case.rule_trace[4].explanation
    assert all(trace.status == "not-applicable" and trace.candidate is None
               for trace in case.rule_trace)
    assert all(trace.sources == () for trace in case.rule_trace)
    assert not hasattr(case, "deal")
    assert json.loads(report.to_json()) == report.to_dict()
    assert build_opening_root_cause_report(batch).to_json() == report.to_json()


def test_12_hcp_discovery_and_other_case_separation():
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    report = build_opening_root_cause_report(batch)
    assert report.depth0_abstains == sum(
        a.outcome.value == "abstain" and not a.final_calls for a in batch.auctions)
    twelve = tuple(case for case in report.strong_cases if case.hcp == 12)
    assert len(twelve) == 2
    assert all(case.hand == batch.auctions[case.deal_index].steps[-1].hand for case in twelve)
    assert all(case.root_cause is OpeningRootCause.CONTROLLED_EQUAL_MAJOR_BOUNDARY
               for case in twelve)
    assert report.strong_depth0_count == len(report.strong_cases)
    assert all(case.hcp >= 12 for case in report.strong_cases)
    assert len(create_standard_sayc_router().routes) == 45


def test_related_reports_and_simulators_remain_available():
    config = SimulationConfig(100, 3)
    batch = run_full_auction_simulation(config)
    assert batch == run_full_auction_simulation(config)
    assert build_abstention_audit(batch).total_abstains == batch.abstain
    assert build_full_auction_coverage_report(batch).abstain == batch.abstain
    assert run_simulation(config).completed_deals == 3


def test_existing_five_five_suit_boundaries_are_deterministic():
    expected = {
        "AKJT7.AKJ74.A54.-": None,  # equal majors
        "AKJT7.A54.AKJ74.-": "1S",
        "A54.AKJT7.AKJ74.-": "1H",
        "AKJT7.A54.-.AKJ74": "1S",
        "A54.AKJT7.-.AKJ74": "1H",
        "A54.-.AKJT7.AKJ74": None,  # equal minors
    }
    engine = create_sayc_opening_engine()
    for hand_text, call in expected.items():
        context = BiddingContext.create(
            hand=Hand.parse(hand_text), auction=Auction(Seat.NORTH),
            vulnerability=Vulnerability.NONE, system=SystemContext("SAYC"),
        )
        result = engine.evaluate(context)
        assert context.evaluation.hcp == 20
        assert (None if result.recommended_call is None else
                result.recommended_call.serialize()) == call
