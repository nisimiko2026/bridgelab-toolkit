"""PT-A2 mechanism/isolation tests; real DDS checks are separately optional."""
from dataclasses import replace
from fractions import Fraction
import ast
import inspect
import random
from pathlib import Path

import pytest

from bridge.auction_information import (
    AuctionInformationState, AuctionConstraintUpdate, Certainty, ConstraintProvenance,
    EvidenceOrigin, NumericRange, RangeEvidence, ShapeEvidence,
)
from bridge.conditional_hidden_hand import ConditionalSampler
from bridge.deals import Deal, full_deck
from bridge.expected_ruffing_research import (
    ERVConfig, ERVStatus, PairStatus, ResearchSolverSession, control_seed_for_deal,
    estimate_erv, information_fingerprint, paired_controls, control_support_guaranteed, realized_shortness_effect, summarize_effects,
)
from bridge.hidden_hand_probability import SamplingConfig, WeightingStatus
from bridge.models import Hand, Rank, Seat, Suit
from bridge.playing_trick_calibration import ShortnessKind, generate_conditioned_case
from bridge.playing_trick_shortness_pairs import apply_exchange, select_singleton_control, singleton_candidates
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus

OWN=Hand.parse("AKQ42.9876.3.J76")
VOID=Hand.parse("AKQ42.98765.-.J76")
SOURCE=ConstraintProvenance(EvidenceOrigin.PROFILE_INTERPRETATION,"synthetic general hard evidence")


def state(own=OWN,updates=(),seat=Seat.SOUTH):
    return AuctionInformationState.start(seat,own,seat).with_updates(updates)


def length(seat,suit,lo,hi=13,certainty=Certainty.GUARANTEED):
    return AuctionConstraintUpdate(seat,suit_lengths=((suit,RangeEvidence(NumericRange(lo,hi),certainty,SOURCE)),))


def collapse_state(void=False):
    own=Hand.parse("AKQJT9876.5432.-.-" if void else "AKQJT9876.432.A.-")
    shapes=((Seat.NORTH,(4,0,9,0)),(Seat.WEST,(0,9 if void else 10,4 if void else 3,0)),
            (Seat.EAST,(0,0,0,13)))
    updates=tuple(AuctionConstraintUpdate(seat,shapes=ShapeEvidence((shape,),Certainty.GUARANTEED,SOURCE))
                  for seat,shape in shapes)
    updates+=(AuctionConstraintUpdate(Seat.NORTH,hcp=RangeEvidence(NumericRange(0,0),Certainty.GUARANTEED,SOURCE)),)
    return state(own,updates)


class DeterministicSolver:
    def solve(self,deal,declarer,strain):
        # Test double only; no heuristic is used by the research oracle.
        score=sum((int(c.rank)*int(c.suit)) for c in deal.hand(declarer).cards)%8+3
        return TrickSolverResult("test-only","1",deal.serialize(),declarer,strain,None,
                                 TrickSolverStatus.SUCCESS,score,random.random())


def estimate(s=None,n=12,solver=None,seed=92):
    return estimate_erv(s or state(),Suit.DIAMONDS,Suit.SPADES,solver or DeterministicSolver(),
                       config=ERVConfig(SamplingConfig(n,500,seed),17,(("test","1"),)))


def test_deterministic_result_excludes_solver_timing():
    assert estimate()==estimate()
    assert all(x.source_solver is None or x.source_solver.elapsed_seconds==0 for x in estimate().effects)


def test_partial_api_and_full_source_leakage_isolation():
    assert "deal" not in inspect.signature(estimate_erv).parameters
    cards=[c for c in full_deck() if c not in OWN.cards]
    def source(seed):
        random.Random(seed).shuffle(cards)
        return Deal(seed,((Seat.SOUTH,OWN),(Seat.NORTH,Hand.from_cards(cards[:13])),
                         (Seat.WEST,Hand.from_cards(cards[13:26])),(Seat.EAST,Hand.from_cards(cards[26:]))))
    a,b=source(5),source(6)
    assert a.serialize()!=b.serialize() and a.hand(Seat.SOUTH)==b.hand(Seat.SOUTH)
    sa,sb=state(a.hand(Seat.SOUTH)),state(b.hand(Seat.SOUTH))
    assert information_fingerprint(sa)==information_fingerprint(sb)
    assert estimate(sa)==estimate(sb)
    with pytest.raises(TypeError):
        estimate_erv(a,Suit.DIAMONDS,Suit.SPADES,DeterministicSolver())


@pytest.mark.parametrize("void",(False,True))
def test_single_physical_deal_collapse_matches_selected_pt1b_target(void):
    s=collapse_state(void)
    sampler=ConditionalSampler(s)
    assert sampler.diagnostics.proposal_allocation_count==1
    assert not sampler.diagnostics.residual_hcp_seats
    result=estimate(s,n=4)
    assert result.evaluable_hypotheses==4
    assert len({x.source_deal_id for x in result.effects})==1
    assert len({x.control_deal_id for x in result.effects})==1
    target=realized_shortness_effect(Deal.parse(result.effects[0].source_deal_id),Seat.SOUTH,
           Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,ResearchSolverSession(DeterministicSolver()),control_seed=17)
    assert result.distribution.mean==target.delta_tricks==result.full_hard_evidence_mean
    assert result.distribution.variance==result.distribution.standard_error==0
    assert result.distribution.confidence_interval_95==(target.delta_tricks,target.delta_tricks)


@pytest.mark.parametrize("own,kind,steps",((OWN,"singleton",1),(VOID,"void",2)))
@pytest.mark.parametrize("perspective",tuple(Seat))
def test_own_shortness_all_orientations_preserve_pt1b_invariants(own,kind,steps,perspective):
    r=estimate(state(own,seat=perspective),n=4)
    assert r.shortness_type==kind and r.evaluable_hypotheses
    for effect in r.effects:
        if effect.status is not PairStatus.EVALUABLE: continue
        source,control=Deal.parse(effect.source_deal_id),Deal.parse(effect.control_deal_id)
        assert control.hand(perspective).length(Suit.DIAMONDS)==2
        assert len(effect.exchanges)==steps
        for seat in Seat:
            before,after=source.hand(seat),control.hand(seat)
            assert before.cards_in(Suit.SPADES)==after.cards_in(Suit.SPADES)
            assert {c for c in before.cards if c.rank>=Rank.JACK}=={c for c in after.cards if c.rank>=Rank.JACK}
            if seat not in (perspective,perspective.partner()):
                assert before==after
        for move in reversed(effect.exchanges):
            control=apply_exchange(control,move.inverse())
        assert control.serialize()==source.serialize()


def test_original_pt1b_singleton_controls_and_selection_reused():
    for seed in range(50):
        case=generate_conditioned_case(seed,(5,3),ShortnessKind.SHORT_HAND_SINGLETON)
        source=Deal.parse(case.deal_id,seed=case.deal_seed)
        item=case.short_suits[0]
        expected=select_singleton_control(case,length=2,selection_seed=control_seed_for_deal(source,17))
        if expected: break
    assert expected is not None
    actual=realized_shortness_effect(source,item.hand,item.suit,case.trump_suit,Seat.NORTH,
                                    ResearchSolverSession(DeterministicSolver()),control_seed=17)
    assert actual.control_deal_id==expected.deal.serialize()
    assert actual.selected_index==expected.selected_exchange_index


@pytest.mark.parametrize("minimum", (0,3,4))
def test_unknown_eight_and_nine_fit_states(minimum):
    updates=() if minimum==0 else (length(Seat.NORTH,Suit.SPADES,minimum),)
    r=estimate(state(updates=updates),n=4)
    assert r.fit.total.minimum==5+minimum
    assert r.sampled_hypotheses==4
    assert all(Deal.parse(x.source_deal_id).hand(Seat.NORTH).length(Suit.SPADES)>=minimum for x in r.effects)


def test_defender_evidence_and_provenance():
    s=state(updates=(length(Seat.WEST,Suit.DIAMONDS,5,5),length(Seat.EAST,Suit.DIAMONDS,3,3)))
    r=estimate(s,n=4)
    assert SOURCE in r.provenance and r.evidence==s.updates
    assert all(Deal.parse(x.source_deal_id).hand(Seat.WEST).length(Suit.DIAMONDS)==5 for x in r.effects)
    assert all(Deal.parse(x.source_deal_id).hand(Seat.EAST).length(Suit.DIAMONDS)==3 for x in r.effects)


def test_missing_controls_are_not_zero_effects():
    s=state(Hand.parse("AKQJT9876543.-.2.-"))
    r=estimate(s,n=5)
    assert r.status is ERVStatus.NOT_EVALUABLE
    assert r.control_rejections==r.sampled_hypotheses==5
    assert r.distribution.mean is r.full_hard_evidence_mean is None
    assert r.distribution.outcomes==()
    assert dict(r.not_evaluable_reasons)=={"no_legal_doubleton_control":5}
    assert all(x.source_solver is None for x in r.effects)


def test_partial_coverage_marks_unconditional_mean_unidentified():
    r=estimate(n=50)
    assert 0<r.evaluable_hypotheses<r.sampled_hypotheses
    assert r.status is ERVStatus.PARTIAL and r.full_hard_evidence_mean is None
    assert r.evaluable_hypotheses+r.control_rejections+r.solver_failed_hypotheses==r.sampled_hypotheses
    valid=[(e,w) for e,w in zip(r.effects,r.weights) if e.delta_tricks is not None]
    mass=sum(w for _,w in valid)
    assert r.evaluable_probability_mass==pytest.approx(float(mass))
    assert r.distribution.mean==pytest.approx(float(sum(e.delta_tricks*w for e,w in valid)/mass))


def test_solver_failures_and_budget_accounted():
    class Broken:
        def solve(self,*args): raise RuntimeError("DDS failed")
    r=estimate(collapse_state(),n=3,solver=Broken())
    assert r.solver_failed_hypotheses==3 and r.dds_failure_count==2
    assert r.distribution.mean is None
    session=ResearchSolverSession(DeterministicSolver(),max_calls=1)
    limited=estimate(collapse_state(),n=3,solver=session)
    assert session.calls==1 and limited.solver_failed_hypotheses==3
    assert all(e.control_solver.error=="solver_call_budget_exhausted" for e in limited.effects)


def test_wrong_solver_provenance_fails_explicitly():
    class Wrong(DeterministicSolver):
        def solve(self,*args):
            return replace(super().solve(*args),deal_id="wrong source")
    r=estimate(collapse_state(),n=2,solver=Wrong())
    assert r.dds_failure_count==2 and r.distribution.mean is None


def test_weighted_distribution_signs_moments_and_quantiles():
    r=summarize_effects((-2,0,4),(Fraction(1,4),Fraction(1,2),Fraction(1,4)))
    assert r.mean==0.5 and r.variance==4.75
    assert r.effective_sample_size==pytest.approx(8/3)
    assert (r.p_positive,r.p_zero,r.p_negative)==(0.25,0.5,0.25)
    assert dict(r.quantiles)[0.5]==0
    assert r.confidence_interval_95[0]<r.mean<r.confidence_interval_95[1]
    assert summarize_effects((1,),(1,)).standard_error is None
    assert summarize_effects((),()).mean is None
    with pytest.raises(ValueError): summarize_effects((1,),(-1,))


def test_soft_status_is_preserved_without_likelihood_calibration():
    s=state(updates=(length(Seat.NORTH,Suit.SPADES,4,4,Certainty.INFERRED),))
    a,b=estimate(s,n=4),estimate(n=4)
    assert a.hard_soft_status is WeightingStatus.INSUFFICIENT_WEIGHTING
    assert a.effects==b.effects and a.distribution==b.distribution
    assert a.information_state_fingerprint!=b.information_state_fingerprint


def test_research_only_dependency_boundary():
    root=Path(__file__).resolve().parents[1]
    body=(root/"bridge/expected_ruffing_research.py").read_text()
    tree=ast.parse(body)
    names=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any(name and any(x in name for x in ("endplay","bidding","profile","sayc")) for name in names)
    for name in ("bridge/sayc.py","bridge/sayc_route_configuration.py","bridge/engine_router.py"):
        assert "expected_ruffing" not in (root/name).read_text()
    from bridge.sayc_route_configuration import create_standard_sayc_router
    assert len(create_standard_sayc_router().routes)==47


@pytest.mark.parametrize("void",(False,True))
def test_real_dds_full_information_collapse(void):
    pytest.importorskip("endplay")
    from bridge.endplay_trick_solver import EndplayTrickSolver
    r=estimate(collapse_state(void),n=3,solver=EndplayTrickSolver())
    assert r.evaluable_hypotheses==3
    first=r.effects[0]
    solver=EndplayTrickSolver()
    source=solver.solve(Deal.parse(first.source_deal_id),r.declarer,r.trump)
    control=solver.solve(Deal.parse(first.control_deal_id),r.declarer,r.trump)
    assert r.full_hard_evidence_mean==source.maximum_declarer_tricks-control.maximum_declarer_tricks


def test_zero_observed_attrition_is_not_a_support_wide_control_proof():
    r=estimate(n=1)
    assert r.evaluable_hypotheses==1
    assert not r.control_support_guaranteed
    assert r.full_hard_evidence_mean is None
    assert r.distribution.mean is not None


@pytest.mark.parametrize("own,lower,expected",((OWN,5,True),(OWN,4,False),(VOID,6,True),(VOID,5,False)))
def test_control_support_sufficient_card_count_proof(own,lower,expected):
    s=state(own,updates=(length(Seat.NORTH,Suit.DIAMONDS,lower),))
    assert control_support_guaranteed(s,Suit.DIAMONDS,Suit.SPADES,100,True) is expected
