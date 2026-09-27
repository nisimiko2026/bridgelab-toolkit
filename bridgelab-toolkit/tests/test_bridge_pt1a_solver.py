"""PT-1A DDS orientation, provenance, paired controls, and validation tests."""

import ast
import gzip
import json
from pathlib import Path

import pytest

from bridge.deals import Deal
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.models import Card, Hand, Rank, Seat, Suit
from bridge.playing_trick_calibration import ShortnessKind
from bridge.playing_trick_pairs import build_matched_set, generate_matched_sets
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus


def suit_block_deal() -> Deal:
    return Deal(1, (
        (Seat.NORTH, Hand.parse("AKQJT98765432.-.-.-")),
        (Seat.EAST, Hand.parse("-.AKQJT98765432.-.-")),
        (Seat.SOUTH, Hand.parse("-.-.AKQJT98765432.-")),
        (Seat.WEST, Hand.parse("-.-.-.AKQJT98765432")),
    ))


def dummy_ruff_deal() -> Deal:
    # On a heart opening lead, dummy South can ruff with 2S while North follows 2H.
    # NS own all spades; consuming that trump need not create a 14th trick.
    return Deal(2, (
        (Seat.NORTH, Hand.parse("AKQJT9876543.2.-.-")),
        (Seat.EAST, Hand.parse("-.AKQJT9876543.2.-")),
        (Seat.SOUTH, Hand.parse("2.-.AKQJT9876543.-")),
        (Seat.WEST, Hand.parse("-.-.-.AKQJT98765432")),
    ))


def test_solver_result_contract_rejects_fake_success_and_failure_tricks():
    deal = suit_block_deal()
    with pytest.raises(ValueError, match="0..13"):
        TrickSolverResult("test", "1", deal.serialize(), Seat.NORTH, Suit.SPADES,
                          None, TrickSolverStatus.SUCCESS, 14, 0.0)
    with pytest.raises(ValueError, match="must not contain tricks"):
        TrickSolverResult("test", "1", deal.serialize(), Seat.NORTH, Suit.SPADES,
                          None, TrickSolverStatus.FAILED, 7, 0.0)


@pytest.mark.parametrize("source,kind", [
    ((6, 3), ShortnessKind.SHORT_HAND_SINGLETON),
    ((7, 3), ShortnessKind.SHORT_HAND_SINGLETON),
    ((6, 3), ShortnessKind.RECIPROCAL_SINGLETONS),
    ((7, 3), ShortnessKind.RECIPROCAL_SINGLETONS),
])
def test_targeted_pairs_keep_all_exact_controls(source, kind):
    matched = build_matched_set(42, source, kind)
    assert matched is not None
    assert tuple(case.trump_structure for case in matched.cases) == (
        ((6, 3), (5, 4)) if source == (6, 3) else ((7, 3), (6, 4), (5, 5)))
    first = matched.cases[0]
    for case in matched.cases[1:]:
        assert case.partnership_hcp == first.partnership_hcp
        assert (case.trump_honors_north, case.trump_honors_south) == (
            first.trump_honors_north, first.trump_honors_south)
        assert (case.side_honors_north, case.side_honors_south) == (
            first.side_honors_north, first.side_honors_south)
        assert case.side_ace_entries == first.side_ace_entries
        assert case.defender_trump_split == first.defender_trump_split
        assert case.short_suits == first.short_suits
        assert Deal.parse(case.deal_id).hand(Seat.EAST) == Deal.parse(first.deal_id).hand(Seat.EAST)
        assert Deal.parse(case.deal_id).hand(Seat.WEST) == Deal.parse(first.deal_id).hand(Seat.WEST)


def test_targeted_reciprocal_sampler_reaches_accepted_target():
    batch = generate_matched_sets((7, 3), ShortnessKind.RECIPROCAL_SINGLETONS,
                                  seed=50, accepted_target=100)
    assert batch.accepted == len(batch.sets) == 100
    assert batch.generated >= batch.accepted
    assert len({matched.pair_id for matched in batch.sets}) == 100


def test_unsupported_fixed_lead_is_explicitly_unavailable():
    result = EndplayTrickSolver().solve(
        suit_block_deal(), Seat.NORTH, Suit.SPADES,
        opening_lead=Card(Suit.HEARTS, Rank.ACE))
    assert result.status is TrickSolverStatus.UNAVAILABLE
    assert result.maximum_declarer_tricks is None
    assert result.deal_id == suit_block_deal().serialize()


def test_suit_block_orientation_top_winners_and_nt():
    pytest.importorskip("endplay")
    solver = EndplayTrickSolver()
    deal = suit_block_deal()
    assert solver.solve(deal, Seat.NORTH, Suit.SPADES).maximum_declarer_tricks == 13
    assert solver.solve(deal, Seat.NORTH, None).maximum_declarer_tricks == 0
    assert solver.solve(deal, Seat.EAST, Suit.SPADES).maximum_declarer_tricks == 0


def test_known_published_dd_table_orients_declarer_and_strain():
    endplay = pytest.importorskip("endplay")
    # The endplay documentation publishes N=13 clubs and N=9 hearts here.
    pbn = "QJ8.AJ965.K82.AQ 43.QT87.QT64.754 AKT9..A97.J98632 7652.K432.J53.KT"
    hands = [Hand.parse(text) for text in pbn.split()]
    deal = Deal(1975, tuple(zip((Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST), hands)))
    solver = EndplayTrickSolver()
    clubs = solver.solve(deal, Seat.NORTH, Suit.CLUBS)
    hearts = solver.solve(deal, Seat.NORTH, Suit.HEARTS)
    assert (clubs.status, clubs.maximum_declarer_tricks) == (TrickSolverStatus.SUCCESS, 13)
    assert (hearts.status, hearts.maximum_declarer_tricks) == (TrickSolverStatus.SUCCESS, 9)
    assert clubs.version == endplay.__version__
    assert clubs.implementation == "endplay/DDS"
    assert clubs.deal_id == deal.serialize()


def test_dummy_ruff_opportunity_does_not_force_extra_trick_credit():
    pytest.importorskip("endplay")
    from endplay.types import Deal as EndplayDeal, Denom, Player
    deal = dummy_ruff_deal()
    solver = EndplayTrickSolver()
    assert deal.hand(Seat.SOUTH).length(Suit.HEARTS) == 0
    assert deal.hand(Seat.SOUTH).length(Suit.SPADES) == 1
    pbn = "N:" + " ".join(deal.hand(seat).serialize().replace("-", "")
                          for seat in (Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST))
    play = EndplayDeal(pbn, first=Player.east, trump=Denom.spades)
    for card in ("HA", "S2", "C2", "H2"):
        play.play(card)
    assert play.curplayer == Player.south  # South's 2S won the opening heart trick.
    assert solver.solve(deal, Seat.NORTH, Suit.SPADES).maximum_declarer_tricks == 13
    assert solver.solve(deal, Seat.NORTH, None).maximum_declarer_tricks == 1


@pytest.mark.parametrize("seed,expected", [(4, (11, 12)), (0, (7, 7)), (9, (10, 9))])
def test_fixed_paired_deals_show_gain_zero_and_loss(seed, expected):
    pytest.importorskip("endplay")
    matched = build_matched_set(seed, (6, 3), ShortnessKind.SHORT_HAND_SINGLETON)
    assert matched is not None
    solver = EndplayTrickSolver()
    results = tuple(solver.solve(Deal.parse(case.deal_id), Seat.NORTH, Suit.SPADES)
                    for case in matched.cases)
    assert tuple(result.maximum_declarer_tricks for result in results) == expected
    assert all(case.natural_playing_tricks is None and case.adjusted_playing_tricks is None
               and case.marginal_ruff_value is None for case in matched.cases)


def test_solver_failure_never_gets_heuristic_tricks(monkeypatch):
    dds = pytest.importorskip("endplay.dds")
    def broken(_deal):
        raise RuntimeError("synthetic DDS failure")
    monkeypatch.setattr(dds, "analyse_start", broken)
    result = EndplayTrickSolver().solve(suit_block_deal(), Seat.NORTH, Suit.SPADES)
    assert result.status is TrickSolverStatus.FAILED
    assert result.maximum_declarer_tricks is None
    assert "synthetic DDS failure" in result.error


def test_small_solver_validation_records_provenance_and_measured_deltas(tmp_path):
    pytest.importorskip("endplay")
    from benchmarks.pt1a_solver_validation import run
    summary = run(seed=9000, primary_target=3, reciprocal_target=2,
                  output_dir=tmp_path)
    assert summary["solver_status_counts"] == {"success": 34}
    assert summary["solver_calls"] == 34
    assert all(row["solver_complete"] == 3 for row in summary["primary_solver_tricks"].values())
    assert summary["primary_paired_deltas"]["5-4_minus_6-3"]["matched_pairs"] == 3
    assert summary["reciprocal_paired_deltas"]["5-4_minus_6-3"]["matched_pairs"] == 2
    with gzip.open(tmp_path / "pt1a_solver_cases.jsonl.gz", "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == 34
    assert all(row["solver"]["status"] == "success" for row in rows)
    assert all(row["solver"]["deal_id"] == row["case"]["deal_id"] for row in rows)
    assert all(row["case"]["natural_playing_tricks"] is None for row in rows)
    assert all(row["case"]["adjusted_playing_tricks"] is None for row in rows)


def test_general_solver_modules_have_no_bidding_or_profile_imports():
    bridge_dir = Path(__file__).resolve().parents[1] / "bridge"
    allowed = {"deals", "models", "trick_solver", "playing_trick_calibration"}
    for filename in ("trick_solver.py", "endplay_trick_solver.py", "playing_trick_pairs.py"):
        tree = ast.parse((bridge_dir / filename).read_text(encoding="utf-8"))
        imports = {node.module for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.level == 1}
        assert imports <= allowed


def test_production_router_remains_45():
    from bridge import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes) == 45
