"""PT-A2C target construction and research isolation tests."""
from dataclasses import replace
import inspect
from collections import Counter
import random
import pytest

from bridge.auction_information import AuctionInformationState, Certainty
from bridge.counterfactual_calibration import diagnose
from bridge.deals import Deal, full_deck
from bridge.expected_ruffing_research import ERVConfig, ResearchSolverSession
from bridge.hidden_hand_probability import SamplingConfig, WeightingStatus
from bridge.models import Hand, Seat, Suit, Rank
from bridge.shortness_target_redesign import (
    TargetConfig, TargetKind, Exclusion, MatchingPriority, reference_support, reference_controls,
    structural_controls, matching_distance, select_matched, fixed_feature_errors,
    evaluate_target_candidates, compare_candidate_expectations,
)
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus
from benchmarks.pta2_erv_validation import OWN_SINGLETON, OWN_VOID, collapse_state, length


def source(own=OWN_SINGLETON,partner=None,seed=0):
    cards=[c for c in full_deck() if c not in own.cards and (partner is None or c not in partner.cards)]
    random.Random(seed).shuffle(cards)
    if partner is None:
        partner=Hand.from_cards(cards[:13])
        cards=cards[13:]
    return Deal(seed,((Seat.SOUTH,own),(Seat.NORTH,partner),
                     (Seat.EAST,Hand.from_cards(cards[:13])),(Seat.WEST,Hand.from_cards(cards[13:]))))


class FakeSolver:
    def solve(self,deal,declarer,strain):
        # Test-only varying outcomes to exercise nested means and exclusions.
        score=sum(int(c.rank) for c in deal.hand(declarer).cards)%8+3
        return TrickSolverResult("test","1",deal.serialize(),declarer,strain,None,
                                 TrickSolverStatus.SUCCESS,score,random.random())


CFG=TargetConfig(reference_draws=4,matching_pool=12,matched_controls=3,exchange_controls=2)


def evaluate(deal,config=CFG,solver=None):
    return evaluate_target_candidates(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,
                                     ResearchSolverSession(solver or FakeSolver()),config=config)


@pytest.mark.parametrize("own",(OWN_SINGLETON,OWN_VOID))
def test_candidates_preserve_formal_fixed_variables(own):
    deal=source(own)
    controls=reference_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,draws=20,seed=22)
    assert len(controls)==20
    for c in controls:
        assert not fixed_feature_errors(deal,c,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
        assert c.hand(Seat.SOUTH).length(Suit.DIAMONDS)==2
        assert all(len(c.hand(s).cards)==13 for s in Seat)
    assert any(deal.hand(Seat.WEST)!=c.hand(Seat.WEST) for c in controls)


@pytest.mark.parametrize("own",(OWN_SINGLETON,OWN_VOID))
def test_structural_minimum_swap_size_and_no_hidden_relaxation(own):
    deal=source(own)
    controls,reasons=structural_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    assert not reasons and controls
    expected=2-own.length(Suit.DIAMONDS)
    for c in controls:
        assert not fixed_feature_errors(deal,c,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
        assert sum(len(deal.hand(s).cards-c.hand(s).cards) for s in Seat)==2*expected
        assert all(c.hand(Seat.SOUTH).length(s)>=min(2,own.length(s)) for s in (Suit.HEARTS,Suit.CLUBS))


@pytest.mark.parametrize("partner",("JT9876.AKQJ.2.54","J9876.AKQ.AKQ.54"))
def test_old_structural_exclusion_has_new_defined_targets(partner):
    d=source(partner=Hand.parse(partner))
    assert not diagnose(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES).evaluable
    r=evaluate(d)
    assert not r.exchange.evaluable
    assert all(not c.exclusions and c.delta is not None for c in r.candidates)


@pytest.mark.parametrize("own",("AKQJT.AKQ.2.AKQJ","AKQJT9876543.2.-.-"))
def test_coverage_not_forced_when_fixed_cards_make_reference_impossible(own):
    r=evaluate(source(Hand.parse(own)))
    assert r.support.exclusions==(Exclusion.FIXED_CARD_CAPACITY,)
    assert all(c.delta is None and c.exclusions for c in r.candidates)


def test_uniform_reference_marginals_and_deterministic_replay():
    d=source()
    a=reference_controls(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,draws=900,seed=72)
    b=reference_controls(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,draws=900,seed=72)
    assert a==b
    counts=Counter(c for control in a for c in control.hand(Seat.SOUTH).cards_in(Suit.DIAMONDS))
    assert len(counts)==9
    assert all(abs(n/len(a)-2/9)<0.055 for n in counts.values())
    assert reference_support(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES).physical_assignments>len(a)


def test_matching_distance_and_exposed_priority():
    d=source()
    controls,_=structural_controls(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    x=controls[0]
    a=matching_distance(d,x,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    b=matching_distance(d,x,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,priority=MatchingPriority.PARTNER_FIRST)
    assert a[:2]==tuple(reversed(b[:2])) and a[2:]==b[2:]
    # Exact HCP/honors/trumps are hard constraints, not hidden scalar penalties.
    bad=source(seed=99)
    with pytest.raises(ValueError): matching_distance(d,bad,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)


def test_matching_order_and_duplicate_invariance():
    d=source()
    pool=reference_controls(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,draws=30,seed=55)
    a=select_matched(d,pool,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,count=5,priority=MatchingPriority.DEFENDERS_FIRST)
    b=select_matched(d,tuple(reversed(pool))+pool,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,count=5,priority=MatchingPriority.DEFENDERS_FIRST)
    assert a==b


def test_candidate_arithmetic_and_separation_of_uncertainty():
    r=evaluate(source())
    for candidate in r.candidates:
        values=[x.maximum_declarer_tricks for x in candidate.control_results]
        assert candidate.delta==pytest.approx(r.source_solver.maximum_declarer_tricks-sum(values)/len(values))
        if candidate.target is TargetKind.BASELINE:
            assert candidate.finite_reference_se is not None
        else:
            assert candidate.finite_reference_se is None
    assert r.exchange.distribution.mean is not None


def test_failed_solve_is_not_silently_dropped():
    class Broken(FakeSolver):
        def solve(self,*args): raise RuntimeError("solver broke")
    r=evaluate(source(),solver=Broken())
    assert all(c.delta is None and Exclusion.SOLVER_FAILURE in c.exclusions for c in r.candidates)


def test_deterministic_results_ignore_timing():
    assert evaluate(source())==evaluate(source())


def test_hidden_source_isolation_and_no_deal_argument():
    a,b=source(seed=10),source(seed=11)
    assert a.serialize()!=b.serialize()
    states=[AuctionInformationState.start(Seat.SOUTH,d.hand(Seat.SOUTH),Seat.SOUTH) for d in (a,b)]
    cfg=ERVConfig(SamplingConfig(3,1000,88))
    results=[compare_candidate_expectations(s,Suit.DIAMONDS,Suit.SPADES,ResearchSolverSession(FakeSolver()),
               sampling=cfg,targets=CFG) for s in states]
    assert results[0]==results[1]
    assert results[0].adopted_target is None
    assert "deal" not in inspect.signature(compare_candidate_expectations).parameters
    with pytest.raises(TypeError):
        compare_candidate_expectations(a,Suit.DIAMONDS,Suit.SPADES,ResearchSolverSession(FakeSolver()))


@pytest.mark.parametrize("void",(False,True))
def test_single_hidden_deal_collapse_equals_each_new_full_information_target(void):
    r=compare_candidate_expectations(collapse_state(void),Suit.DIAMONDS,Suit.SPADES,
        ResearchSolverSession(FakeSolver()),sampling=ERVConfig(SamplingConfig(3,3,72000)),targets=CFG)
    assert len({c.source_deal_id for c in r.comparisons})==1
    for kind,stats in r.target_statistics:
        target=next(c for c in r.comparisons[0].candidates if c.target is kind)
        assert stats["mean"]==pytest.approx(target.delta)
        assert stats["se"]==0
        # Zero outer sampling error does not erase the finite-control uncertainty.
        if kind is TargetKind.BASELINE: assert target.finite_reference_se is not None


def test_soft_evidence_preserves_hard_only_status():
    base=AuctionInformationState.start(Seat.SOUTH,OWN_SINGLETON,Seat.SOUTH)
    update=length(Seat.NORTH,Suit.SPADES,4)
    e=replace(update.suit_lengths[0][1],certainty=Certainty.INFERRED)
    soft=base.with_updates((replace(update,suit_lengths=((Suit.SPADES,e),)),))
    cfg=ERVConfig(SamplingConfig(1,1000,88))
    a,b=[compare_candidate_expectations(s,Suit.DIAMONDS,Suit.SPADES,ResearchSolverSession(FakeSolver()),
                                        sampling=cfg,targets=CFG) for s in (base,soft)]
    assert b.weighting_status is WeightingStatus.INSUFFICIENT_WEIGHTING
    assert a.comparisons==b.comparisons


@pytest.mark.parametrize("perspective",tuple(Seat))
def test_all_viewpoint_orientations(perspective):
    original=source()
    seats=(Seat.NORTH,Seat.EAST,Seat.SOUTH,Seat.WEST)
    offset=(seats.index(perspective)-2)%4
    d=Deal(0,tuple((seats[(i+offset)%4],original.hand(s)) for i,s in enumerate(seats)))
    controls=reference_controls(d,perspective,Suit.DIAMONDS,Suit.SPADES,draws=3,seed=33)
    assert controls
    assert all(not fixed_feature_errors(d,c,perspective,Suit.DIAMONDS,Suit.SPADES) for c in controls)


@pytest.mark.parametrize("void",(False,True))
def test_real_dds_new_target_collapse(void):
    pytest.importorskip("endplay")
    from bridge.endplay_trick_solver import EndplayTrickSolver
    r=compare_candidate_expectations(collapse_state(void),Suit.DIAMONDS,Suit.SPADES,
        ResearchSolverSession(EndplayTrickSolver()),sampling=ERVConfig(SamplingConfig(2,2,72000)),targets=CFG)
    assert all(stats["mean"]==pytest.approx(next(c.delta for c in r.comparisons[0].candidates if c.target is kind))
               for kind,stats in r.target_statistics)
    assert r.comparisons[0].exchange.pta2_selected_delta==(2 if void else 1)


def test_no_production_imports():
    import ast
    from pathlib import Path
    from bridge.sayc_route_configuration import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes)==45
    tree=ast.parse(Path("bridge/shortness_target_redesign.py").read_text(encoding="utf-8"))
    assert not any(isinstance(n,ast.ImportFrom) and n.module and "endplay" in n.module for n in ast.walk(tree))
    for name in ("sayc.py","engine_router.py","sayc_route_configuration.py"):
        assert "shortness_target_redesign" not in (Path("bridge")/name).read_text(encoding="utf-8")

def test_reference_can_require_different_own_shortness_elsewhere():
    r=evaluate(source(Hand.parse("AKQJ9876.543.-.T2")))
    targets={c.target:c for c in r.candidates}
    assert targets[TargetKind.STRUCTURAL].exclusions==(Exclusion.COMPENSATION_FLOOR,)
    assert targets[TargetKind.MATCHED].delta is not None
    assert targets[TargetKind.BASELINE].delta is not None


def test_defender_diagnostic_holds_matching_and_partnership_features_fixed():
    from benchmarks.pta2c_validation_diagnostics import defender_spot_variants
    d=source()
    control=reference_controls(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,draws=1,seed=44)[0]
    variants=defender_spot_variants(control,Seat.SOUTH,Suit.SPADES)
    assert len(variants)>1
    for candidate in variants:
        assert candidate.hand(Seat.SOUTH)==control.hand(Seat.SOUTH)
        assert candidate.hand(Seat.NORTH)==control.hand(Seat.NORTH)
        assert all(candidate.hand(seat).shape==control.hand(seat).shape for seat in Seat)
        assert not fixed_feature_errors(d,candidate,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
        assert matching_distance(d,candidate,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)==matching_distance(
            d,control,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)


def test_collateral_shortness_diagnostic_excludes_studied_change():
    from benchmarks.pta2c_validation_diagnostics import shortness_changes
    d=source(Hand.parse("AKQJ9876.543.-.T2"))
    controls=reference_controls(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,draws=5,seed=88)
    for c in controls:
        changes=shortness_changes(d,c,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
        assert any(item["own"] for item in changes)
        assert not any(item["own"] and item["suit"]=="D" for item in changes)
