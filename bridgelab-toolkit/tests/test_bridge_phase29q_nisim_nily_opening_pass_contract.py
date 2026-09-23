"""Family algebra and policy boundaries, validated against real generated hands."""
from dataclasses import FrozenInstanceError, replace
import json

import pytest

from bridge.auction import Auction
from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.deals import generate_deal
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_opening_pass_contract import (
    Family as F, FamilyState as S, FamilyCheck, ContractResult as R,
    assess_opening_pass_contract, resolve_families, build_opening_pass_contract_audit,
)


@pytest.fixture(scope="module")
def sample():
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    return batch, build_opening_pass_contract_audit(batch)


def test_complete_negative_proof_and_each_unknown_blocks_pass():
    # Abstract algebra only; these fixtures are not authorized real-hand evidence.
    negative = tuple(FamilyCheck(f, S.NEGATIVE, "test-only exclusion", ("TEST_ONLY",)) for f in F)
    assert resolve_families(negative) is R.PASS_SUPPORTED
    assert resolve_families(()) is R.OTHER_UNRESOLVED
    assert resolve_families(negative[:-1]) is R.OTHER_UNRESOLVED
    assert resolve_families(negative + negative[:1]) is R.OTHER_UNRESOLVED
    assert resolve_families(negative[:-1] + negative[:1]) is R.OTHER_UNRESOLVED
    for index, check in enumerate(negative):
        changed = negative[:index] + (replace(check, state=S.UNRESOLVED),) + negative[index+1:]
        assert resolve_families(changed) is not R.PASS_SUPPORTED
    mixed = tuple(replace(c, state=S.UNRESOLVED) for c in negative)
    for family in (F.NORMAL_HCP, F.RULE20, F.MAJOR11, F.STRONG_HCP):
        with_open = tuple(replace(c, state=S.POSITIVE) if c.family is family else c for c in mixed)
        assert resolve_families(with_open) is R.OPEN_SUPPORTED
    with_treatment = tuple(replace(c, state=S.POSITIVE, supported_call="2S") if c.family is F.WEAK_TWO_SUITED else c for c in mixed)
    assert resolve_families(with_treatment) is R.PARTNERSHIP_TREATMENT


def test_family_evidence_required_and_no_positive_pass_family():
    with pytest.raises(TypeError):
        FamilyCheck(F.STRONG_PLAYING_TRICKS, False, "false is not negative", ("test",))
    with pytest.raises(ValueError):
        FamilyCheck(F.STRONG_PLAYING_TRICKS, S.NEGATIVE, "unsupported", ())
    with pytest.raises(ValueError):
        FamilyCheck(F.STRONG_PLAYING_TRICKS, S.NEGATIVE, "", ("test",))
    with pytest.raises(ValueError):
        FamilyCheck(F.NORMAL_HCP, S.POSITIVE, "wrong family", ("test",), "P")


def test_reproduce_every_record_and_counts(sample):
    batch, report = sample
    assert report.seed == 100 and report.total_deals == 1000
    assert report.depth0_abstain == len(report.cases) == 616
    assert report.simulation_errors == 0
    original = {a.deal_index: a for a in batch.auctions}
    for row in report.cases:
        a, c = original[row.deal_index], row.contract
        assert c.hand == generate_deal(100 + row.deal_index).hand(a.dealer).serialize() == a.steps[-1].hand
        assert c.acting_seat == c.dealer == a.dealer.value
        assert c.vulnerability == a.vulnerability.value
        assert c.opening_position == 1 and not a.steps[-1].auction_before
        assert row.production_status == "abstain" and row.production_route == "sayc.opening"
        assert len(c.family_checks) == len(F) and {x.family for x in c.family_checks} == set(F)
        assert c.result is resolve_families(c.family_checks)
    assert dict(report.counts) == {
        "OPEN_SUPPORTED": 61, "PARTNERSHIP_TREATMENT": 16,
        "WEAK_MULTI_UNRESOLVED": 13, "PREEMPT_UNRESOLVED": 6,
        "PROTECTED_UNRESOLVED": 38, "OTHER_UNRESOLVED": 465, "PASS_SUPPORTED": 17,
    }
    assert (report.pass_count, report.known_opening_count, report.unresolved_count) == (17, 77, 522)
    assert sum(n for _, n in report.counts) == 616


def test_all_pass_rows_have_every_negative_exclusion(sample):
    _, report = sample
    passes = [r for r in report.cases if r.contract.result is R.PASS_SUPPORTED]
    assert tuple(r.deal_index for r in passes) == report.pass_review_indices
    for row in passes:
        c = row.contract
        assert c.supported_call == "P" and c.approved_negative_signature
        assert all(x.state is S.NEGATIVE and x.reason and x.evidence for x in c.family_checks)
        assert c.hcp < 11 and c.rule20_total < 20 and max(c.suit_lengths) <= 5
        assert "no production no-match inference" in c.reason
        for passes_before in (0, 1):
            # Same real hand, counterfactual context: never relabeled as a real sample row.
            assessed = assess_opening_pass_contract(Hand.parse(c.hand), auction=Auction(Seat.NORTH, ("P",) * passes_before), vulnerability=Vulnerability(c.vulnerability))
            assert assessed.result is R.PASS_SUPPORTED


def test_low_hcp_no_match_is_not_a_trick_bound(sample):
    rows = {r.deal_index: r for r in sample[1].cases}
    c = rows[1].contract
    assert c.hcp == 2 and c.result is R.OTHER_UNRESOLVED
    check = next(x for x in c.family_checks if x.family is F.STRONG_PLAYING_TRICKS)
    assert check.state is S.UNRESOLVED and c.supported_call is None
    assert all(x.state is S.NEGATIVE for x in c.family_checks if x.family is not F.STRONG_PLAYING_TRICKS)
    assert dict((f, n) for f, n, _ in sample[1].unresolved_blockers)["STRONG_PLAYING_TRICKS"] == 522


def test_activation_and_later_seat_fail_closed(sample):
    c = next(r.contract for r in sample[1].cases if r.deal_index == 955)
    hand = Hand.parse(c.hand)
    extra = assess_opening_pass_contract(hand, auction=Auction(Seat.NORTH), vulnerability=Vulnerability.NONE,
        additional_activated_families=("unresolved-extra-opening",))
    assert extra.result is R.OTHER_UNRESOLVED
    assert next(x for x in extra.family_checks if x.family is F.OTHER_ACTIVATED).state is S.UNRESOLVED
    for passes in (2, 3):
        later = assess_opening_pass_contract(hand, auction=Auction(Seat.NORTH, ("P",)*passes), vulnerability=Vulnerability.NONE)
        assert later.result is R.OTHER_UNRESOLVED and later.supported_call is None
    case17 = next(r.contract for r in sample[1].cases if r.deal_index == 295)
    for passes in (2, 3):
        later = assess_opening_pass_contract(Hand.parse(case17.hand), auction=Auction(Seat.NORTH, ("P",)*passes), vulnerability=Vulnerability.NONE)
        assert later.result is R.OPEN_SUPPORTED and later.supported_call == "1S"


def test_current_full_normal_strength_precedes_weak_treatment(sample):
    rows = {r.deal_index: r for r in sample[1].cases}
    for index in (292, 626, 736, 922, 988):
        row = rows[index]
        assert row.phase29p_classification == "PARTNERSHIP_TREATMENT"
        assert row.contract.result is R.OPEN_SUPPORTED and row.contract.supported_call is None
        assert row.contract.rule20_total >= 20
        assert next(c for c in row.contract.family_checks if c.family is F.WEAK_TWO_SUITED).state is S.NEGATIVE
    assert rows[634].contract.result is R.OPEN_SUPPORTED and rows[634].contract.supported_call == "1S"
    for row in rows.values():
        c = row.contract
        if c.result is R.PARTNERSHIP_TREATMENT:
            assert c.hcp < 12 and c.rule20_total < 20
            assert not (c.hcp == 11 and max(c.suit_lengths[:2]) >= 5)
            assert c.supported_call in ("2S", "2H", "2NT")
        if c.result is R.OPEN_SUPPORTED and c.supported_call:
            assert c.supported_call == "1S" and c.suit_lengths[:2] == (5, 5)


def test_multi_preempt_minor_and_protected_checks_are_not_guessed(sample):
    for row in sample[1].cases:
        c = row.contract
        checks = {x.family: x for x in c.family_checks}
        if max(c.suit_lengths[:2]) >= 6:
            assert checks[F.WEAK_MULTI].state is S.UNRESOLVED
        if max(c.suit_lengths) >= 7:
            assert checks[F.PREEMPT].state is S.UNRESOLVED
        if max(c.suit_lengths[2:]) >= 6:
            assert checks[F.SIX_MINOR].state is S.UNRESOLVED
        if c.result in (R.WEAK_MULTI_UNRESOLVED, R.PREEMPT_UNRESOLVED, R.PROTECTED_UNRESOLVED, R.OTHER_UNRESOLVED):
            assert c.supported_call is None
    assert not any(r.contract.supported_call == "2D" for r in sample[1].cases)


def test_positive_strong_branch_on_real_hand_outside_abstention_population():
    hand = next(h for seed in range(100, 1100) if (h := generate_deal(seed).hand(Seat.NORTH)) and evaluate_hand(h).hcp >= 22)
    c = assess_opening_pass_contract(hand, auction=Auction(Seat.NORTH), vulnerability=Vulnerability.NONE)
    assert c.result is R.OPEN_SUPPORTED
    assert next(x for x in c.family_checks if x.family is F.STRONG_HCP).state is S.POSITIVE


def test_transitions_serialization_and_routes(sample):
    batch, r = sample
    assert sum(len(ids) for _, _, ids in r.transitions) == 616
    assert sum(n for _, n, _ in r.affirmative_overlaps) == 77
    assert r.to_json() == build_opening_pass_contract_audit(batch).to_json()
    assert json.loads(r.to_json()) == r.to_dict()
    assert r.production_route_count == 45 and not r.production_changed and not r.production_ready
    with pytest.raises(FrozenInstanceError):
        r.pass_count = 616


def test_invalid_auctions_and_status_overrides_rejected(sample):
    hand = Hand.parse(sample[1].cases[0].contract.hand)
    for calls in (("P",)*4, ("1C",)):
        with pytest.raises(ValueError):
            assess_opening_pass_contract(hand, auction=Auction(Seat.NORTH, calls), vulnerability=Vulnerability.NONE)
    with pytest.raises(TypeError):
        assess_opening_pass_contract(hand, auction=Auction(Seat.NORTH), vulnerability=Vulnerability.NONE, no_rule_match=True)
