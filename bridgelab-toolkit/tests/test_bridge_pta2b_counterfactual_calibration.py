"""PT-A2B focused mechanism, invariance, selection and isolation validation."""
from dataclasses import replace
from fractions import Fraction
import inspect
import random

import pytest

from bridge.auction_information import AuctionInformationState, Certainty
from bridge.counterfactual_calibration import (
    ControlFamily, FailureReason, diagnose, enumerate_controls, preservation_errors,
    representative_controls, control_distribution, evaluate_controls, estimate_multicontrol,
    missing_effect_bounds, target_statistics, pre_control_features,
)
from bridge.deals import Deal, full_deck
from bridge.expected_ruffing_research import ERVConfig, ResearchSolverSession
from bridge.hidden_hand_probability import SamplingConfig, WeightingStatus
from bridge.models import Hand, Seat, Suit
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus
from benchmarks.pta2_erv_validation import collapse_state, information_states, OWN_SINGLETON, OWN_VOID, length


def source(own, partner=None, seed=0):
    remaining=[c for c in full_deck() if c not in own.cards and (partner is None or c not in partner.cards)]
    random.Random(seed).shuffle(remaining)
    if partner is None:
        partner=Hand.from_cards(remaining[:13])
        remaining=remaining[13:]
    return Deal(seed,((Seat.SOUTH,own),(Seat.NORTH,partner),
                     (Seat.EAST,Hand.from_cards(remaining[:13])),(Seat.WEST,Hand.from_cards(remaining[13:]))))


def unique(void=False):
    return source(Hand.parse("AKQJT.AK32.-.AKQJ" if void else "AKQJT.AK2.3.AKQJ"),
                  Hand.parse("98765.QJT.AK32.2" if void else "98765.QJT.AK2.32"))


class FakeSolver:
    def solve(self,deal,declarer,strain):
        # Mechanism double only, not a research valuation formula.
        score=5+max(0,2-deal.hand(Seat.SOUTH).length(Suit.DIAMONDS))
        return TrickSolverResult("test","1",deal.serialize(),declarer,strain,None,
                                 TrickSolverStatus.SUCCESS,score,0.1)


def effect(deal, **kwargs):
    return evaluate_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,
                             ResearchSolverSession(FakeSolver()),**kwargs)


@pytest.mark.parametrize("own,partner,reason",[
    (OWN_SINGLETON,Hand.parse("JT9876.AKQJ.2.54"),FailureReason.PARTNER_LENGTH_FLOOR),
    (OWN_SINGLETON,Hand.parse("J9876.AKQ.AKQ.54"),FailureReason.PARTNER_HONOR_LOCK),
    (Hand.parse("AKQJT9876.32.A.2"),None,FailureReason.COMPENSATION_SHAPE),
    (Hand.parse("AKQJT.AKQ.2.AKQJ"),None,FailureReason.COMPENSATION_HONOR_LOCK),
])
def test_specific_structural_failure(own,partner,reason):
    deal=source(own,partner)
    d=diagnose(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    assert reason in d.reasons
    assert not d.evaluable and d.minimal_unique_controls==0
    for family in ControlFamily:
        assert not enumerate_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,family=family).controls


def test_trump_and_not_short_categories():
    d=unique()
    assert FailureReason.STUDIED_TRUMP in diagnose(d,Seat.SOUTH,Suit.SPADES,Suit.SPADES).reasons
    assert FailureReason.NOT_SHORT in diagnose(d,Seat.SOUTH,Suit.HEARTS,Suit.SPADES).reasons


def test_duplicate_cards_rejected_before_control_generation():
    deal=unique()
    with pytest.raises(ValueError):
        Deal(0,((Seat.SOUTH,deal.hand(Seat.SOUTH)),(Seat.NORTH,deal.hand(Seat.SOUTH)),
                (Seat.EAST,deal.hand(Seat.EAST)),(Seat.WEST,deal.hand(Seat.WEST))))


@pytest.mark.parametrize("void",(False,True))
def test_unique_control_collapse(void):
    e=effect(unique(void),control_limit=100)
    assert e.evaluable and e.legal_controls==1 and e.exhaustive
    assert e.original_path_count==(4 if void else 1)
    assert e.distribution.mean==e.distribution.median==e.pta2_selected_delta==(2 if void else 1)
    assert e.distribution.spread==e.distribution.standard_deviation==0


@pytest.mark.parametrize("own",(OWN_SINGLETON,OWN_VOID))
def test_expanded_family_preserves_invariants_and_same_coverage(own):
    added=0
    for seed in range(5):
        deal=source(own,seed=seed)
        base=enumerate_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,family=ControlFamily.BASE)
        expanded=enumerate_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
        assert bool(base.controls)==bool(expanded.controls)==base.diagnosis.evaluable
        assert {d.serialize() for d in base.controls}<={d.serialize() for d in expanded.controls}
        added+=len(expanded.controls)-len(base.controls)
        for control in expanded.controls:
            assert not preservation_errors(deal,control,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    assert added>0


def test_all_seat_orientations():
    original=unique()
    seats=(Seat.NORTH,Seat.EAST,Seat.SOUTH,Seat.WEST)
    for offset in range(4):
        mapping={s:seats[(i+offset)%4] for i,s in enumerate(seats)}
        rotated=Deal(0,tuple((mapping[s],h) for s,h in original.hands))
        p=mapping[Seat.SOUTH]
        family=enumerate_controls(rotated,p,Suit.DIAMONDS,Suit.SPADES)
        assert family.controls
        assert not any(preservation_errors(rotated,c,p,Suit.DIAMONDS,Suit.SPADES) for c in family.controls)


def test_enumeration_and_suit_order_do_not_change_target(monkeypatch):
    import bridge.counterfactual_calibration as module
    deal=source(OWN_SINGLETON,seed=4)
    original=module.paired_controls
    before=effect(deal,control_limit=7)
    monkeypatch.setattr(module,"paired_controls",lambda *args:tuple(reversed(original(*args))))
    after=effect(deal,control_limit=7)
    # Reversing paths may change the legacy seeded reference, never the uniform target.
    assert before.control_results==after.control_results and before.distribution==after.distribution
    monkeypatch.setattr(module,"Suit",tuple(reversed(tuple(Suit))))
    reversed_suits=effect(deal,control_limit=7)
    assert before.control_results==reversed_suits.control_results


def test_hash_selection_is_order_duplicate_and_seed_independent():
    family=enumerate_controls(source(OWN_SINGLETON,seed=4),Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
    assert len(family.controls)>5
    a=representative_controls(family.controls,5)
    assert a==representative_controls(tuple(reversed(family.controls))+family.controls,5)
    assert effect(source(OWN_SINGLETON,seed=4),control_seed=1).distribution==effect(source(OWN_SINGLETON,seed=4),control_seed=999).distribution


def test_equivalent_card_container_labeling_does_not_change_controls():
    deal=source(OWN_SINGLETON,seed=4)
    repacked=Deal(999,tuple(reversed(tuple((s,Hand.from_cards(reversed(sorted(h.cards)))) for s,h in deal.hands))))
    assert repacked.serialize()==deal.serialize()
    assert [d.serialize() for d in enumerate_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES).controls]==[
        d.serialize() for d in enumerate_controls(repacked,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES).controls]


def test_uniform_median_and_ambiguity_statistics():
    d=control_distribution((-2,0,1,5))
    assert d.mean==1 and d.median==0.5 and d.minimum==-2 and d.maximum==5 and d.spread==7
    assert d.standard_deviation==pytest.approx((6.5)**0.5)
    assert d==control_distribution((5,1,0,-2))
    assert control_distribution(()).mean is None


def test_weighted_outer_mean_and_sampling_uncertainty():
    d=target_statistics((Fraction(1,2),Fraction(5,2)),(Fraction(1,4),Fraction(3,4)))
    assert d["mean"]==2 and d["ess"]==pytest.approx(1.6)
    assert d["mc_95_ci"][0]<d["mean"]<d["mc_95_ci"][1]


def test_partial_coverage_and_bounds_are_not_zero_imputation():
    bounds=missing_effect_bounds(1,0.75)
    assert bounds["lower"]==-2.5 and bounds["upper"]==4
    assert missing_effect_bounds(None,0)["lower"]==-13
    assert missing_effect_bounds(2,1)["upper"]==2
    with pytest.raises(ValueError): missing_effect_bounds(None,0.5)


def test_solver_failure_does_not_renormalize_over_successful_controls():
    class Broken(FakeSolver):
        def solve(self,deal,*args):
            if deal.hand(Seat.SOUTH).length(Suit.DIAMONDS)==2:
                raise RuntimeError("failed control")
            return super().solve(deal,*args)
    e=evaluate_controls(unique(),Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,ResearchSolverSession(Broken()))
    assert e.failure_reasons==(FailureReason.SOLVER_FAILURE,) and e.distribution.mean is None


def test_budget_and_enumeration_limits_are_explicit():
    e=evaluate_controls(unique(),Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,ResearchSolverSession(FakeSolver(),max_calls=1))
    assert e.failure_reasons==(FailureReason.SOLVER_BUDGET,)
    e=effect(source(OWN_SINGLETON,seed=4),max_controls=1)
    assert e.failure_reasons==(FailureReason.ENUMERATION_LIMIT,)


def test_deterministic_partial_estimation_and_no_source_deal_parameter():
    a,b=source(OWN_SINGLETON,seed=3),source(OWN_SINGLETON,seed=9)
    assert a.serialize()!=b.serialize()
    states=[AuctionInformationState.start(Seat.SOUTH,d.hand(Seat.SOUTH),Seat.SOUTH) for d in (a,b)]
    cfg=ERVConfig(SamplingConfig(5,2000,93),3202)
    estimates=[estimate_multicontrol(s,Suit.DIAMONDS,Suit.SPADES,ResearchSolverSession(FakeSolver()),config=cfg,control_limit=2) for s in states]
    assert estimates[0]==estimates[1]
    assert "deal" not in inspect.signature(estimate_multicontrol).parameters
    with pytest.raises(TypeError):
        estimate_multicontrol(a,Suit.DIAMONDS,Suit.SPADES,ResearchSolverSession(FakeSolver()))


def test_soft_evidence_is_unresolved():
    base=AuctionInformationState.start(Seat.SOUTH,OWN_SINGLETON,Seat.SOUTH)
    update=length(Seat.NORTH,Suit.SPADES,4)
    update=replace(update,suit_lengths=((Suit.SPADES,replace(update.suit_lengths[0][1],certainty=Certainty.INFERRED)),))
    soft=base.with_updates((update,))
    cfg=ERVConfig(SamplingConfig(2,1000,92),3202)
    a,b=[estimate_multicontrol(s,Suit.DIAMONDS,Suit.SPADES,ResearchSolverSession(FakeSolver()),config=cfg,control_limit=2) for s in (base,soft)]
    assert b.weighting_status is WeightingStatus.INSUFFICIENT_WEIGHTING and a.effects==b.effects


def test_cohort_observables_precede_control_and_account_for_missing():
    rows=[(diagnose(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES),pre_control_features(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES))
          for d in (unique(),source(OWN_SINGLETON,Hand.parse("JT9876.AKQJ.2.54")))]
    assert [d.evaluable for d,f in rows]==[True,False]
    assert rows[0][1]["length_N_D"]==3 and rows[1][1]["length_N_D"]==1


@pytest.mark.parametrize("void",(False,True))
def test_real_dds_existing_collapse_reference_and_control_distribution(void):
    pytest.importorskip("endplay")
    from bridge.endplay_trick_solver import EndplayTrickSolver
    result=estimate_multicontrol(collapse_state(void),Suit.DIAMONDS,Suit.SPADES,
        ResearchSolverSession(EndplayTrickSolver()),config=ERVConfig(SamplingConfig(2,2,72000),3202),
        family=ControlFamily.BASE,control_limit=10000)
    e=result.effects[0]
    assert e.exhaustive and e.pta2_selected_delta==(2 if void else 1)
    assert dict(result.targets)["uniform_controls"]["mean"]==e.distribution.mean
    assert len(e.control_results)==e.legal_controls


def test_no_production_integration():
    from pathlib import Path
    from bridge.sayc_route_configuration import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes)==45
    for name in ("sayc.py","engine_router.py","sayc_route_configuration.py"):
        assert "counterfactual_calibration" not in (Path("bridge")/name).read_text()
