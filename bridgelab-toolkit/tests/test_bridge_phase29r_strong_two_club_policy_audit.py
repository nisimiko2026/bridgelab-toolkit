"""Preparation-only evidence tests: no fitted strength formula or new bid rule."""
from dataclasses import FrozenInstanceError
import json

import pytest

from bridge.deal_simulator import SimulationConfig, run_full_auction_simulation
from bridge.deals import generate_deal
from bridge.evaluation import high_card_points
from bridge.models import Seat
from bridge.nisim_nily_opening_pass_contract import ContractResult as R, Family as F, FamilyState as S
from bridge.strong_two_club_policy_audit import (
    StrongPolicyConcept, ExpertAnswer, policy_probes, record_expert_answer,
    reference_comparisons, build_strong_two_club_audit, canonical_probe_hand,
)


@pytest.fixture(scope="module")
def sample():
    batch = run_full_auction_simulation(SimulationConfig(100, 1000))
    return batch, build_strong_two_club_audit(batch)


def test_canonical_probe_hcp_and_thirteen_cards():
    probes = policy_probes()
    assert [p.hand_number for p in probes] == list(range(1, 11))
    assert [p.hcp for p in probes] == [17, 16, 16, 15, 18, 19, 19, 20, 19, 15]
    assert [p.hand_number for p in probes if p.user_decision == "2C"] == [1, 3, 7, 8]
    assert [p.hand_number for p in probes if p.user_decision == "1S"] == [2, 4, 5, 6, 9, 10]
    for p in probes:
        hand = canonical_probe_hand(p.cards)
        assert len(hand.cards) == p.card_count == sum(p.suit_lengths) == sum(map(len, p.cards)) == 13
        assert high_card_points(hand) == p.hcp
        assert "stated_hcp" not in p.to_dict() and "named_honor_hcp" not in p.to_dict()
    assert all("x" in "".join(p.cards) for p in probes)
    assert all(p.expert_1.decision is p.expert_2.decision is None and p.additional_experts == () for p in probes)
    assert all(p.consensus == "AWAITING_EXPERTS" and p.evidence_status == "PROVISIONAL_USER_CLASSIFICATION" for p in probes)


def test_expert_answers_are_evidence_only_and_consensus_is_not_adoption():
    original = policy_probes()[0]
    one = record_expert_answer(original, ExpertAnswer("expert_1", "1S", "test evidence only"))
    assert one.consensus == "ONE_EXPERT_ONLY"
    two = record_expert_answer(one, ExpertAnswer("expert_2", "1S"))
    assert two.consensus == "EXPERT_AGREEMENT_DIFFERS_FROM_USER"
    three = record_expert_answer(two, ExpertAnswer("expert_3", "2C"))
    assert three.consensus == "EXPERT_DISAGREEMENT"
    assert three.user_decision == original.user_decision == "2C"
    assert original.expert_1.decision is None
    update = record_expert_answer(three, ExpertAnswer("expert_3", "1S"))
    assert len(update.additional_experts) == 1 and update.consensus == "EXPERT_AGREEMENT_DIFFERS_FROM_USER"
    assert update.evidence_status == "PROVISIONAL_USER_CLASSIFICATION"
    with pytest.raises(FrozenInstanceError):
        original.user_decision = "1S"


def test_forcing_property_is_not_a_hand_strength_test():
    concept = StrongPolicyConcept()
    assert concept.game_forcing_property and len(concept.eligibility_alternatives) == 3
    assert not concept.forcing_property_is_eligibility_test
    assert not concept.playing_tricks_calculation_approved
    assert not concept.independent_game_force_calculation_approved
    assert not concept.production_adopted


def test_partial_reference_values_are_not_filled_or_fitted():
    rows = reference_comparisons()
    assert len(rows) == 30
    illustrative = {r.hand_number: r for r in rows if r.definition_id == "playing-tricks-illustrative-table"}
    assert illustrative[1].calculated_value == illustrative[9].calculated_value == 8
    assert illustrative[1].at_least_nine is illustrative[9].at_least_nine is False
    assert illustrative[1].comparison_with_user == "PT_THRESHOLD_DIFFERS_FROM_USER_2C"
    assert all(r.calculated_value is None and r.at_least_nine is None for n, r in illustrative.items() if n not in (1, 9))
    assert "unapproved assumption" in illustrative[7].evidence
    assert all(not r.production_eligible for r in rows)
    assert all(r.calculated_value is None for r in rows if r.definition_id != "playing-tricks-illustrative-table")


def test_population_counts_distinguish_raw_unknown_from_pass_blockers(sample):
    _, r = sample
    assert r.opening_abstentions == 616 and r.simulation_errors == 0
    assert (r.raw_strong_unresolved, r.already_open_supported_with_strong_unresolved) == (599, 77)
    assert (r.blocker_count, r.sole_blocker_count, r.other_family_blocker_count) == (522, 465, 57)
    assert r.sole_blocker_count + r.other_family_blocker_count == r.blocker_count
    assert sum(n for _, n in r.phase29q_counts) == 616
    assert dict(r.phase29q_counts)["PASS_SUPPORTED"] == 17
    for row in r.blocker_cases:
        assert row.contract.result not in (R.PASS_SUPPORTED, R.OPEN_SUPPORTED, R.PARTNERSHIP_TREATMENT)
        assert any(c.family is F.STRONG_PLAYING_TRICKS and c.state is S.UNRESOLVED for c in row.contract.family_checks)
        assert row.contract.hand == generate_deal(100 + row.deal_index).hand(Seat(row.contract.dealer)).serialize()


def test_distributions_and_real_representatives(sample):
    _, r = sample
    for distribution in (r.hcp_distribution, r.sorted_shape_distribution, r.suit_order_shape_distribution, r.longest_suit_distribution):
        assert sum(n for _, n in distribution) == 522
    assert dict(r.longest_suit_distribution) == {4: 228, 5: 243, 6: 45, 7: 6}
    assert (r.six_plus, r.seven_plus, r.eight_plus) == (51, 6, 0)
    assert dict(r.other_family_counts) == {"PREEMPT": 6, "PROTECTED_DISTRIBUTION": 8, "SIX_MINOR": 35, "WEAK_MULTI": 16}
    assert len(r.selected_indices) >= 20 and len(r.selected_indices) == len(set(r.selected_indices))
    selected = [row for row in r.blocker_cases if row.deal_index in r.selected_indices]
    assert len(selected) == len(r.selected_indices)
    assert {row.contract.hcp for row in selected} == {hcp for hcp, _ in r.hcp_distribution}
    assert {max(row.contract.suit_lengths) for row in selected} == {length for length, _ in r.longest_suit_distribution}


def test_determinism_and_no_formula_or_production_change(sample):
    batch, r = sample
    assert r.to_json() == build_strong_two_club_audit(batch).to_json()
    assert json.loads(r.to_json()) == r.to_dict()
    assert r.production_route_count == 45
    assert not r.production_changed and not r.new_strength_predicate
    assert not r.existing_executable_pt_formula and not r.existing_executable_independent_gf_test
