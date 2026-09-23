"""Policy audit on generated real hands; no fabricated sample or live rules."""
from dataclasses import FrozenInstanceError
import json

import pytest

from bridge.auction import Auction
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.deals import generate_deal
from bridge.models import Hand, Seat
from bridge.nisim_nily_opening_policy import build_nisim_nily_opening_policy
from bridge.opening_pass_nisim_nily_policy_audit import (
    Classification as C, classify_nisim_nily_hand, build_nisim_nily_policy_audit,
)


@pytest.fixture(scope="module")
def sample():
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    return batch, build_nisim_nily_policy_audit(batch)


def test_reproduction_and_every_real_record(sample):
    batch, report = sample
    assert len(report.cases) == report.opening_abstentions == 616
    assert report.simulation_errors == report.reproduction_errors == 0
    original = {a.deal_index: a for a in batch.auctions}
    for row in report.cases:
        a = original[row.deal_index]
        assert row.hand == generate_deal(100 + row.deal_index).hand(a.dealer).serialize()
        assert row.hand == a.steps[-1].hand
        assert row.dealer == row.acting_seat == a.dealer.value
        assert row.vulnerability == a.vulnerability.value
        assert row.opening_position == 1 and row.auction_before == ()
        assert row.production_status == "abstain"
        assert len(row.rule_trace) == 14
        assert all(t["candidate"] is None for t in row.rule_trace)
        assert row.rule20_total == row.hcp + sum(row.two_longest)


def test_full_counts_and_no_fallback(sample):
    _, r = sample
    assert dict(r.counts) == {
        "OPEN_KNOWN": 56, "WEAK_MULTI_CANDIDATE": 14, "PREEMPT_CANDIDATE": 6,
        "PASS_SUPPORTED": 17, "PARTNERSHIP_TREATMENT": 21,
        "PROTECTED_UNRESOLVED": 37, "UNKNOWN": 465,
    }
    assert r.positive_pass == 17 and r.known_open_not_pass == 77 and r.unresolved_not_pass == 522
    assert r.positive_pass + r.known_open_not_pass + r.unresolved_not_pass == 616
    assert any(x.hcp <= 3 and x.policy.classification is C.UNKNOWN for x in r.cases)
    assert all(x.policy.evidence and not x.policy.unresolved for x in r.cases if x.policy.classification is C.PASS_SUPPORTED)
    assert all(x.rule20_total < 20 and x.hcp < 11 and max(x.suit_lengths) <= 5
               for x in r.cases if x.policy.classification is C.PASS_SUPPORTED)


def test_approved_signatures_and_seat_boundaries(sample):
    _, r = sample
    rows = {x.deal_index: x for x in r.cases}
    assert rows[955].policy.classification is C.PASS_SUPPORTED  # 9 HCP 5S4H22
    assert rows[888].policy.classification is C.PASS_SUPPORTED  # 8 HCP 5S5H21
    case17 = rows[295]
    case18 = next(x for x in r.cases if x.hcp == 10 and x.suit_lengths[:2] == (4, 4)
                  and sorted(x.suit_lengths) == [2, 3, 4, 4])
    for row, call in ((case17, "1S"), (case18, None)):
        for passes in (0, 1, 2, 3):
            # Counterfactual context unit check on a real hand; never a sample row.
            p = classify_nisim_nily_hand(Hand.parse(row.hand), auction=Auction(Seat.NORTH, ("P",) * passes))
            assert p.classification is (C.PASS_SUPPORTED if passes < 2 else C.OPEN_KNOWN)
            assert p.supported_call == ("P" if passes < 2 else call)
    for index in (955, 888):
        p = classify_nisim_nily_hand(Hand.parse(rows[index].hand), auction=Auction(Seat.NORTH, ("P", "P")))
        assert p.classification is not C.PASS_SUPPORTED


def test_new_strength_evidence_does_not_change_historical_policy(sample):
    _, r = sample
    assert build_nisim_nily_opening_policy().version == "29M.1"
    for row in r.cases:
        if row.hcp >= 12 or row.rule20_total >= 20 or (row.hcp == 11 and max(row.suit_lengths[:2]) >= 5):
            assert row.policy.classification in (C.OPEN_KNOWN, C.PARTNERSHIP_TREATMENT)
    equal = [x for x in r.cases if x.hcp >= 12 and x.suit_lengths[:2] == (5, 5)]
    assert len(equal) == 3 and all(x.policy.supported_call == "1S" for x in equal)
    assert any(x.hcp <= 10 and x.rule20_total >= 20 for x in r.cases)
    assert any(x.hcp == 11 and x.rule20_total < 20 and x.policy.classification is C.OPEN_KNOWN for x in r.cases)
    assert all(x.policy.supported_call is None for x in r.cases if x.policy.classification is C.OPEN_KNOWN and x.hcp < 12)


def test_partnership_treatments_and_unidentified_minor_examples(sample):
    _, r = sample
    treatments = [x for x in r.cases if x.policy.classification is C.PARTNERSHIP_TREATMENT]
    assert {x.policy.supported_call for x in treatments} == {"2S", "2H", "2NT"}
    for row in treatments:
        s, h, d, c = row.suit_lengths
        assert row.hcp < 12
        assert row.policy.supported_call == ("2S" if s == 5 else "2H" if h == 5 else "2NT")
        assert sum(n == 5 for n in (s, h, d, c)) == 2
    for row in r.cases:
        if max(row.suit_lengths[2:]) == 6 and row.hcp < 10:
            assert row.policy.classification is not C.PASS_SUPPORTED
        if row.policy.classification in (C.WEAK_MULTI_CANDIDATE, C.PREEMPT_CANDIDATE):
            assert row.policy.supported_call is None and row.policy.unresolved


def test_selection_coverage_and_determinism(sample):
    batch, r = sample
    selected = [x for x in r.cases if x.deal_index in r.selected_indices]
    assert len(selected) >= 30 and len(selected) == len(set(r.selected_indices))
    covered = {tag for x in selected for tag in x.tags}
    assert all(n == 0 or tag in covered for tag, n in r.availability)
    assert dict(r.availability)["third-hand"] == dict(r.availability)["fourth-hand"] == 0
    assert sum(n for _, n in r.selected_counts) == len(selected)
    assert r.to_json() == build_nisim_nily_policy_audit(batch).to_json()
    assert json.loads(r.to_json()) == r.to_dict()
    assert r.route_count == 45 and not r.production_changed
    with pytest.raises(FrozenInstanceError):
        r.positive_pass = 616


def test_audit_api_rejects_invalid_context_and_production_status_override(sample):
    hand = Hand.parse(sample[1].cases[0].hand)
    for calls in (("P", "P", "P", "P"), ("1C",)):
        with pytest.raises(ValueError):
            classify_nisim_nily_hand(hand, auction=Auction(Seat.NORTH, calls))
    with pytest.raises(TypeError):
        classify_nisim_nily_hand(hand, auction=Auction(Seat.NORTH), production_status="abstain")
