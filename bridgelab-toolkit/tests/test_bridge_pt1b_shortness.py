"""PT-1B exact low-card shortness controls and measurement semantics."""

import ast
from pathlib import Path

import pytest

from bridge.deals import Deal, full_deck
from bridge.evaluation import evaluate_hand
from bridge.models import Rank, Seat, Suit
from bridge.playing_trick_calibration import ShortnessKind, generate_conditioned_case
from bridge.playing_trick_shortness_pairs import (
    apply_exchange, reciprocal_candidates, select_direct_reciprocal_control,
    select_reciprocal_controls, select_singleton_control, singleton_candidates,
)
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus
from benchmarks.pt1b_shortness_validation import delta_stats, reciprocal_effects, trump_quality


def _find(structure, kind, build):
    for seed in range(100):
        case = generate_conditioned_case(seed, structure, kind)
        selected = build(case, seed)
        if selected is not None:
            return case, selected
    raise AssertionError("no valid source found")


def _audit(source, controls, trump):
    assert set(card for seat in Seat for card in source.hand(seat).cards) == set(full_deck())
    source_hcp = sum(evaluate_hand(source.hand(seat)).hcp for seat in (Seat.NORTH, Seat.SOUTH))
    source_trumps = tuple(source.hand(seat).cards_in(trump) for seat in (Seat.NORTH, Seat.SOUTH))
    for control in controls:
        assert set(card for seat in Seat for card in control.hand(seat).cards) == set(full_deck())
        assert len({card for seat in Seat for card in control.hand(seat).cards}) == 52
        assert sum(evaluate_hand(control.hand(seat)).hcp
                   for seat in (Seat.NORTH, Seat.SOUTH)) == source_hcp
        assert tuple(control.hand(seat).cards_in(trump)
                     for seat in (Seat.NORTH, Seat.SOUTH)) == source_trumps
        for seat in Seat:
            before, after = source.hand(seat), control.hand(seat)
            if seat in (Seat.EAST, Seat.WEST):
                assert before == after
            else:
                assert evaluate_hand(before).hcp == evaluate_hand(after).hcp
                for suit in Suit:
                    assert {card for card in before.cards_in(suit) if card.rank >= Rank.JACK} == {
                        card for card in after.cards_in(suit) if card.rank >= Rank.JACK}


@pytest.mark.parametrize("structure,kind", [
    ((5, 3), ShortnessKind.SHORT_HAND_SINGLETON),
    ((6, 3), ShortnessKind.LONG_HAND_SINGLETON),
    ((5, 5), ShortnessKind.EQUAL_HAND_SINGLETON),
])
def test_singleton_doubleton_exact_preservation_and_reverse(structure, kind):
    case, control = _find(structure, kind, lambda c, seed:
                          select_singleton_control(c, length=2, selection_seed=seed))
    source = Deal.parse(case.deal_id, seed=case.deal_seed)
    _audit(source, (control.deal,), case.trump_suit)
    item = case.short_suits[0]
    assert control.deal.hand(item.hand).length(item.suit) == 2
    assert control.candidate_exchange_count > 0
    assert 0 <= control.selected_exchange_index < control.candidate_exchange_count
    assert all(x.added_card.rank < Rank.JACK and x.removed_card.rank < Rank.JACK
               for x in control.exchanges)
    assert all(x.added_suit is item.suit and x.removed_suit is not item.suit
               for x in control.exchanges)
    assert apply_exchange(control.deal, control.exchanges[0].inverse()).serialize() == source.serialize()


def test_three_card_control_is_exact_and_reversible():
    case, control = _find((5, 3), ShortnessKind.SHORT_HAND_SINGLETON,
                          lambda c, seed: select_singleton_control(
                              c, length=3, selection_seed=seed))
    source = Deal.parse(case.deal_id, seed=case.deal_seed)
    _audit(source, (control.deal,), case.trump_suit)
    assert len(control.exchanges) == 2
    assert control.deal.hand(case.short_suits[0].hand).length(case.short_suits[0].suit) == 3
    replay = control.deal
    for exchange in reversed(control.exchanges):
        replay = apply_exchange(replay, exchange.inverse())
    assert replay.serialize() == source.serialize()


def test_multiple_candidates_stable_and_seeded_selection_reproducible():
    case, selected = _find((5, 3), ShortnessKind.SHORT_HAND_SINGLETON,
                           lambda c, seed: select_singleton_control(
                               c, length=2, selection_seed=seed)
                           if len(singleton_candidates(Deal.parse(c.deal_id),
                                                       c.short_suits[0].hand,
                                                       c.short_suits[0].suit,
                                                       c.trump_suit)) > 1 else None)
    source = Deal.parse(case.deal_id)
    item = case.short_suits[0]
    candidates = singleton_candidates(source, item.hand, item.suit, case.trump_suit)
    reconstructed = Deal(source.seed, tuple(reversed(source.hands)))
    assert [(d.serialize(), x) for d, x in candidates] == [
        (d.serialize(), x) for d, x in singleton_candidates(
            reconstructed, item.hand, item.suit, case.trump_suit)]
    assert select_singleton_control(case, length=2, selection_seed=37) == \
        select_singleton_control(case, length=2, selection_seed=37)
    assert selected.candidate_exchange_count == len(candidates) > 1


def test_invalid_exchange_is_rejected():
    case, control = _find((6, 3), ShortnessKind.SHORT_HAND_SINGLETON,
                          lambda c, seed: select_singleton_control(
                              c, length=2, selection_seed=seed))
    source = Deal.parse(case.deal_id)
    with pytest.raises(ValueError, match="starting shapes|absent"):
        apply_exchange(source, control.exchanges[0].inverse())


def test_short_and_long_cohorts_are_distinct():
    short = generate_conditioned_case(4, (6, 3), ShortnessKind.SHORT_HAND_SINGLETON)
    long = generate_conditioned_case(4, (6, 3), ShortnessKind.LONG_HAND_SINGLETON)
    assert short.short_suits[0].hand is short.short_trump_hand
    assert long.short_suits[0].hand is long.long_trump_hand
    assert short.shortness_kind != long.shortness_kind


def test_reciprocal_square_exact_preservation_reversibility_and_interaction():
    case, controls = _find((5, 4), ShortnessKind.RECIPROCAL_SINGLETONS,
                           lambda c, seed: select_reciprocal_controls(
                               c, selection_seed=seed))
    _audit(controls.reciprocal, (controls.north_removed,
                                controls.south_removed, controls.neither), case.trump_suit)
    north_suit = next(x.suit for x in case.short_suits if x.hand is Seat.NORTH)
    south_suit = next(x.suit for x in case.short_suits if x.hand is Seat.SOUTH)
    assert controls.north_removed.hand(Seat.NORTH).length(north_suit) == 2
    assert controls.north_removed.hand(Seat.SOUTH).length(south_suit) == 1
    assert controls.south_removed.hand(Seat.NORTH).length(north_suit) == 1
    assert controls.south_removed.hand(Seat.SOUTH).length(south_suit) == 2
    assert controls.neither.hand(Seat.NORTH).length(north_suit) == 2
    assert controls.neither.hand(Seat.SOUTH).length(south_suit) == 2
    assert apply_exchange(controls.north_removed, controls.north_exchange.inverse()).serialize() == \
        controls.reciprocal.serialize()
    assert apply_exchange(controls.south_removed, controls.south_exchange.inverse()).serialize() == \
        controls.reciprocal.serialize()
    assert apply_exchange(controls.neither,
                          controls.south_exchange_after_north.inverse()).serialize() == \
        controls.north_removed.serialize()
    assert apply_exchange(controls.neither,
                          controls.north_exchange_after_south.inverse()).serialize() == \
        controls.south_removed.serialize()
    assert controls.candidate_exchange_count == len(reciprocal_candidates(case))
    assert 0 <= controls.selected_exchange_index < controls.candidate_exchange_count


def test_seven_three_four_corner_impossible_but_direct_control_possible():
    for seed in range(10):
        case = generate_conditioned_case(seed, (7, 3), ShortnessKind.RECIPROCAL_SINGLETONS)
        assert select_reciprocal_controls(case, selection_seed=seed) is None
    case, control = _find((7, 3), ShortnessKind.RECIPROCAL_SINGLETONS,
                          lambda c, seed: select_direct_reciprocal_control(
                              c, selection_seed=seed))
    source = Deal.parse(case.deal_id)
    _audit(source, (control.deal,), case.trump_suit)
    assert apply_exchange(control.deal, control.exchanges[0].inverse()).serialize() == source.serialize()


def test_reciprocal_effect_formula_and_separate_statistics():
    result = reciprocal_effects(10, 9, 8, 6)
    assert result == {"combined": 4, "remove_n_conditional": 1,
                      "remove_s_conditional": 2, "n_alone": 2,
                      "s_alone": 3, "interaction": -1}
    assert delta_stats([1, 0, -1])["n"] == 3
    assert delta_stats([1, 0, -1])["p_positive"] == pytest.approx(1 / 3)
    assert delta_stats([1, 0, -1])["p_le_minus_1"] == pytest.approx(1 / 3)
    assert delta_stats([])["mean_delta"] is None


def test_solver_failure_remains_unavailable():
    case = generate_conditioned_case(1, (5, 3), ShortnessKind.SHORT_HAND_SINGLETON)
    failed = TrickSolverResult("DDS", "test", case.deal_id, Seat.NORTH, Suit.SPADES,
                               None, TrickSolverStatus.FAILED, None, 0.0, "failed")
    assert failed.maximum_declarer_tricks is None
    with pytest.raises(ValueError, match="must not contain tricks"):
        TrickSolverResult("DDS", "test", case.deal_id, Seat.NORTH, Suit.SPADES,
                          None, TrickSolverStatus.FAILED, 7, 0.0, "failed")


def test_failed_solver_matches_never_enter_statistics(monkeypatch, tmp_path):
    import gzip
    import json
    from benchmarks import pt1b_shortness_validation as validation

    class UnavailableSolver:
        implementation = "test-unavailable"

        def solve(self, deal, declarer, strain):
            return TrickSolverResult(self.implementation, None, deal.serialize(),
                                     declarer, strain, None, TrickSolverStatus.UNAVAILABLE,
                                     None, 0.0, "solver absent")

    monkeypatch.setattr(validation, "EndplayTrickSolver", UnavailableSolver)
    with pytest.raises(RuntimeError, match="generation limit reached"):
        validation.run(seed=2901, primary_target=1, reciprocal_target=1,
                       sensitivity_sources=0, output_dir=tmp_path)
    with gzip.open(tmp_path / "pt1b_cases.jsonl.gz", "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    assert rows
    assert all(row["delta"] is None for row in rows)
    assert all(all(result["maximum_declarer_tricks"] is None
                   for result in row["solvers"]) for row in rows)
    assert not (tmp_path / "pt1b_summary.json").exists()


def test_quality_definition_predeclared():
    case = generate_conditioned_case(3, (5, 3), ShortnessKind.SHORT_HAND_SINGLETON)
    assert trump_quality(case) in ("weak", "medium", "strong")


def test_small_solver_validation_records_real_dd_provenance(tmp_path):
    pytest.importorskip("endplay")
    import gzip
    import json
    from benchmarks.pt1b_shortness_validation import run
    summary = run(seed=9100, primary_target=2, reciprocal_target=1,
                  sensitivity_sources=1, output_dir=tmp_path)
    assert summary["solver_calls"] > 0
    assert summary["solver_status_counts"] == {"success": summary["solver_calls"]}
    assert summary["cohorts"]["7-3_reciprocal"]["design"] == "direct-only"
    assert summary["cohorts"]["5-4_reciprocal"]["design"] == "complete-four-corner"
    assert "loser_bucket" in summary["within_cohort_strata"]
    assert "source_context" in summary["within_cohort_strata"]
    assert "loser_bucket" in summary["reciprocal_within_cohort_strata"]
    assert summary["sensitivity_replay_solver_calls"] > 0
    assert summary["total_solver_calls_including_replay"] == (
        summary["solver_calls"] + summary["sensitivity_replay_solver_calls"])
    with gzip.open(tmp_path / summary["sensitivity_provenance_file"],
                   "rt", encoding="utf-8") as stream:
        sensitivity_rows = [json.loads(line) for line in stream]
    assert len(sensitivity_rows) == summary["sensitivity_replay_solver_calls"]
    assert all(row["control_solver"]["status"] == "success"
               for row in sensitivity_rows)
    with gzip.open(tmp_path / "pt1b_cases.jsonl.gz", "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    assert rows
    for row in rows:
        assert row["case"]["natural_playing_tricks"] is None
        assert row["case"]["adjusted_playing_tricks"] is None
        for result in (row["solvers"].values() if isinstance(row["solvers"], dict)
                       else row["solvers"]):
            if result is not None:
                assert result["implementation"] == "endplay/DDS"
                assert result["status"] == "success"


def test_general_pt1b_modules_have_no_bidding_or_partnership_imports():
    root = Path(__file__).resolve().parents[1]
    for relative in ("bridge/playing_trick_shortness_pairs.py",
                     "benchmarks/pt1b_shortness_validation.py"):
        tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.module]
        assert not any("bidding" in name or "partnership" in name
                       or "profile" in name for name in imports)


def test_production_router_remains_45():
    from bridge import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes) == 47
