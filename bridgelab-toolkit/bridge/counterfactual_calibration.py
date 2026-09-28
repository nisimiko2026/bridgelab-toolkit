"""PT-A2B research: structural coverage and distinct-terminal-control targets.

No bidding or endplay dependency. Hard evidence enters only through PT-A1B.
Failure diagnosis is necessary/sufficient for the preserved PT-1B length floors.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import comb, sqrt
from statistics import median

from .auction_information import AuctionInformationState
from .conditional_hidden_hand import ConditionalSampler
from .deals import Deal
from .evaluation import high_card_points
from .expected_ruffing_research import (
    ERVConfig, ResearchSolverSession, SEATS, control_seed_for_deal,
    information_fingerprint, paired_controls,
)
from .models import Hand, Rank, Seat, Suit
from .playing_trick_shortness_pairs import _exchange, apply_exchange
from .trick_solver import TrickSolverStatus
import random


class FailureReason(str, Enum):
    STUDIED_TRUMP = "studied_suit_is_trump"
    NOT_SHORT = "own_singleton_or_void_required"
    PARTNER_LENGTH_FLOOR = "partner_studied_doubleton_floor"
    PARTNER_HONOR_LOCK = "partner_studied_spots_insufficient_honors_locked"
    COMPENSATION_SHAPE = "own_side_suit_doubleton_floor"
    COMPENSATION_HONOR_LOCK = "own_compensation_spots_insufficient_honors_locked"
    INVALID_TRANSITION = "invalid_physical_transition"
    ENUMERATION_LIMIT = "control_enumeration_limit"
    SOLVER_FAILURE = "solver_failure"
    SOLVER_BUDGET = "solver_call_budget_exhausted"


class ControlFamily(str, Enum):
    BASE = "minimal_pt1b_distinct_terminal"
    SPOT_RELOCATION = "minimal_plus_one_same_suit_spot_swap"


@dataclass(frozen=True, slots=True)
class Diagnosis:
    reasons: tuple[FailureReason, ...]
    required_transfers: int
    partner_studied_length: int
    partner_studied_spots: int
    compensation_shape_capacity: int
    compensation_spot_capacity: int
    minimal_unique_controls: int

    @property
    def evaluable(self):
        return not self.reasons


def diagnose(deal: Deal, perspective: Seat, studied: Suit, trump: Suit) -> Diagnosis:
    own, partner = deal.hand(perspective), deal.hand(perspective.partner())
    required = 2-own.length(studied)
    spots = sum(c.rank < Rank.JACK for c in partner.cards_in(studied))
    sides = tuple(s for s in Suit if s not in (studied, trump))
    capacities = {s:max(0,own.length(s)-2) for s in sides}
    shape_capacity = sum(capacities.values())
    spot_capacity = sum(min(capacities[s],sum(c.rank < Rank.JACK for c in own.cards_in(s))) for s in sides)
    reasons = []
    if studied is trump:
        reasons.append(FailureReason.STUDIED_TRUMP)
    if own.length(studied) not in (0,1):
        reasons.append(FailureReason.NOT_SHORT)
    if not reasons:
        if partner.length(studied)-required < 2:
            reasons.append(FailureReason.PARTNER_LENGTH_FLOOR)
        if spots < required:
            reasons.append(FailureReason.PARTNER_HONOR_LOCK)
        if shape_capacity < required:
            reasons.append(FailureReason.COMPENSATION_SHAPE)
        elif spot_capacity < required:
            reasons.append(FailureReason.COMPENSATION_HONOR_LOCK)
    unique = 0
    if not reasons:
        outgoing = tuple(c for c in own.cards if c.suit in sides and c.rank < Rank.JACK)
        choices = sum(all(sum(c.suit is s for c in group)<=capacities[s] for s in sides)
                      for group in combinations(outgoing,required))
        unique = comb(spots,required)*choices
        assert unique > 0
    return Diagnosis(tuple(reasons),required,partner.length(studied),spots,
                     shape_capacity,spot_capacity,unique)


def pre_control_features(deal, perspective, studied, trump):
    """Full-hypothesis diagnostics only; never additional auction-time evidence."""
    own, partner = deal.hand(perspective),deal.hand(perspective.partner())
    others = tuple(s for s in SEATS if s not in (perspective,perspective.partner()))
    top = 0
    for rank in range(14,1,-1):
        if not any(int(c.rank)==rank for c in partner.cards_in(studied)):
            break
        top += 1
    a,b = own.length(trump),partner.length(trump)
    data = {
        "shortness": "singleton" if own.length(studied)==1 else "void" if own.length(studied)==0 else "other",
        "studied_suit":studied.letter,
        "own_trumps":a,"partner_trumps":b,"total_trumps":a+b,
        "trump_structure":f"{a}-{b}","trump_role":"short" if a<b else "long" if a>b else "equal",
        "defender_split":"-".join(str(deal.hand(s).length(studied)) for s in others),
        "ruffable_loser_proxy":max(0,partner.length(studied)-top-own.length(studied)),
        "side_ace_entries":sum(c.rank is Rank.ACE and c.suit is not trump for h in (own,partner) for c in h.cards),
    }
    for seat in SEATS:
        hand=deal.hand(seat)
        data["hcp_"+seat.value]=high_card_points(hand)
        for suit in Suit:
            data["length_"+seat.value+"_"+suit.letter]=hand.length(suit)
    return data


def preservation_errors(source, control, perspective, studied, trump):
    errors=[]
    for seat in SEATS:
        before,after=source.hand(seat),control.hand(seat)
        if {c for c in before.cards if c.rank>=Rank.JACK}!={c for c in after.cards if c.rank>=Rank.JACK}:
            errors.append("honors")
        if before.cards_in(trump)!=after.cards_in(trump):
            errors.append("trumps")
        if seat not in (perspective,perspective.partner()) and before!=after:
            errors.append("defenders")
    if control.hand(perspective).length(studied)!=2:
        errors.append("shortness_transition")
    if control.hand(perspective.partner()).length(studied)<2:
        errors.append("partner_floor")
    for suit in Suit:
        if suit not in (studied,trump):
            before=source.hand(perspective).length(suit)
            if control.hand(perspective).length(suit)<min(before,2):
                errors.append("compensation_floor")
    return tuple(sorted(set(errors)))


@dataclass(frozen=True, slots=True)
class ControlSet:
    family: ControlFamily
    diagnosis: Diagnosis
    controls: tuple[Deal, ...]
    original_path_count: int
    minimal_unique_count: int


def enumerate_controls(deal, perspective, studied, trump, *,
                       family=ControlFamily.SPOT_RELOCATION, max_controls=100000):
    if not isinstance(family,ControlFamily):
        raise TypeError("typed control family required")
    if type(max_controls) is not int or max_controls<1:
        raise ValueError("positive enumeration limit required")
    diagnosis=diagnose(deal,perspective,studied,trump)
    if not diagnosis.evaluable:
        return ControlSet(family,diagnosis,(),0,0)
    paths=paired_controls(deal,perspective,studied,trump)
    base={x.deal.serialize():x.deal for x in paths}
    assert len(base)==diagnosis.minimal_unique_controls
    if len(base)>max_controls:
        raise OverflowError(FailureReason.ENUMERATION_LIMIT.value)
    controls=dict(base)
    if family is ControlFamily.SPOT_RELOCATION:
        for source in base.values():
            # One optional same-suit spot transposition changes no hand's shape.
            # It may include the studied suit. Every honor/trump/defender is fixed.
            for suit in Suit:
                if suit is trump:
                    continue
                own_spots=sorted(c for c in source.hand(perspective).cards_in(suit) if c.rank<Rank.JACK)
                partner_spots=sorted(c for c in source.hand(perspective.partner()).cards_in(suit) if c.rank<Rank.JACK)
                for a in own_spots:
                    for b in partner_spots:
                        variant,exchange=_exchange(source,b,perspective.partner(),a,perspective)
                        if apply_exchange(variant,exchange.inverse()).serialize()!=source.serialize():
                            raise AssertionError(FailureReason.INVALID_TRANSITION.value)
                        controls[variant.serialize()]=variant
                        if len(controls)>max_controls:
                            raise OverflowError(FailureReason.ENUMERATION_LIMIT.value)
    ordered=tuple(controls[key] for key in sorted(controls))
    for control in ordered:
        errors=preservation_errors(deal,control,perspective,studied,trump)
        if errors:
            raise AssertionError((FailureReason.INVALID_TRANSITION.value,errors))
    return ControlSet(family,diagnosis,ordered,len(paths),len(base))


def representative_controls(controls, limit):
    """Bottom-k fixed hashes of canonical physical deals; order/seed independent.

    Exhaustive if k>=population; otherwise a deterministic pseudo-random subset.
    This approximates the uniform distinct-terminal target, not an exact mean.
    """
    if type(limit) is not int or limit<1:
        raise ValueError("positive control limit required")
    unique={d.serialize():d for d in controls}
    selected=sorted(unique,key=lambda key:(sha256(("PTA2B-controls-v1:"+key).encode()).digest(),key))[:limit]
    return tuple(unique[key] for key in selected)


@dataclass(frozen=True, slots=True)
class ControlDistribution:
    count: int
    mean: float | None
    median: float | None
    minimum: int | None
    maximum: int | None
    spread: int | None
    standard_deviation: float | None


def control_distribution(deltas):
    values=tuple(deltas)
    if any(type(v) is not int or not -13<=v<=13 for v in values):
        raise ValueError("integer DDS deltas required")
    if not values:
        return ControlDistribution(0,None,None,None,None,None,None)
    center=Fraction(sum(values),len(values))
    variance=sum((Fraction(v)-center)**2 for v in values)/len(values)
    return ControlDistribution(len(values),float(center),float(median(values)),min(values),max(values),
                               max(values)-min(values),sqrt(float(variance)))


@dataclass(frozen=True, slots=True)
class MultiControlEffect:
    source_deal_id: str
    family: ControlFamily
    diagnosis: Diagnosis
    failure_reasons: tuple[FailureReason, ...]
    minimal_unique_controls: int
    original_path_count: int
    legal_controls: int
    selected_controls: int
    controls_solved: int
    exhaustive: bool
    control_results: tuple[tuple[str, int | None], ...]
    distribution: ControlDistribution
    first_valid_delta: int | None
    pta2_selected_delta: int | None
    source_solver: object
    solver_records: tuple
    features: tuple

    @property
    def evaluable(self):
        return not self.failure_reasons and self.distribution.mean is not None


def evaluate_controls(deal, perspective, studied, trump, declarer, session, *,
                      family=ControlFamily.SPOT_RELOCATION, control_limit=8,
                      control_seed=3202, max_controls=100000):
    if declarer not in (perspective,perspective.partner()):
        raise ValueError("declarer must belong to perspective partnership")
    diagnostic=diagnose(deal,perspective,studied,trump)
    features=tuple(sorted(pre_control_features(deal,perspective,studied,trump).items()))
    try:
        candidates=enumerate_controls(deal,perspective,studied,trump,family=family,max_controls=max_controls)
    except OverflowError:
        return MultiControlEffect(deal.serialize(),family,diagnostic,(FailureReason.ENUMERATION_LIMIT,),
            diagnostic.minimal_unique_controls,0,0,0,0,False,(),control_distribution(()),None,None,None,(),features)
    if not candidates.controls:
        return MultiControlEffect(deal.serialize(),family,diagnostic,diagnostic.reasons,
            0,0,0,0,0,True,(),control_distribution(()),None,None,None,(),features)
    selected=representative_controls(candidates.controls,control_limit)
    source=session.solve(deal,declarer,trump)
    paths=paired_controls(deal,perspective,studied,trump)
    original=paths[random.Random(control_seed_for_deal(deal,control_seed)).randrange(len(paths))].deal
    first=candidates.controls[0]  # Explicit lexicographic first, NOT the PT-A2 policy.
    solved={d.serialize():session.solve(d,declarer,trump) for d in (*selected,first,original)}
    def delta(control):
        result=solved[control.serialize()]
        if source.status is TrickSolverStatus.SUCCESS and result.status is TrickSolverStatus.SUCCESS:
            return source.maximum_declarer_tricks-result.maximum_declarer_tricks
        return None
    values=tuple((d.serialize(),delta(d)) for d in selected)
    failed=any(value is None for _,value in values)
    reasons=()
    if failed:
        reasons=(FailureReason.SOLVER_BUDGET if any(r.error=="solver_call_budget_exhausted" for r in (source,*solved.values()))
                 else FailureReason.SOLVER_FAILURE,)
    # A failed selected solve invalidates this target, never a valid-only control mean.
    distribution=control_distribution(()) if failed else control_distribution(value for _,value in values)
    return MultiControlEffect(deal.serialize(),family,diagnostic,reasons,len({x.deal.serialize() for x in paths}),
        len(paths),len(candidates.controls),len(selected),sum(value is not None for _,value in values),
        len(selected)==len(candidates.controls),values,distribution,delta(first),delta(original),source,
        tuple(solved[key] for key in sorted(solved)),features)


def target_statistics(values, weights):
    values,weights=tuple(values),tuple(Fraction(w) for w in weights)
    if len(values)!=len(weights) or any(w<0 for w in weights):
        raise ValueError("matching nonnegative weights required")
    mass=sum(weights,Fraction())
    if not mass:
        return {"count":len(values),"mass":0.0,"ess":0.0,"mean":None,"sd":None,"se":None,"mc_95_ci":None}
    normalized=tuple(w/mass for w in weights)
    center=sum((Fraction(str(v))*w for v,w in zip(values,normalized)),Fraction())
    variance=sum((w*(Fraction(str(v))-center)**2 for v,w in zip(values,normalized)),Fraction())
    square=sum(w*w for w in normalized)
    se=sqrt(float(variance*square/(1-square))) if square<1 else None
    return {"count":len(values),"mass":float(mass),"ess":float(1/square),"mean":float(center),
            "sd":sqrt(float(variance)),"se":se,
            "mc_95_ci":(float(center)-1.96*se,float(center)+1.96*se) if se is not None else None}


def missing_effect_bounds(observed_mean, coverage, *, lower=-13, upper=13):
    """Empirical completion sensitivity, NOT identified ERV or a confidence bound.

    Where no control exists the target is undefined. These bounds apply only to
    a hypothetical extension assigning missing deltas within [lower, upper].
    """
    if not 0<=coverage<=1 or not -13<=lower<=upper<=13:
        raise ValueError("invalid coverage/delta bounds")
    if coverage>0 and (observed_mean is None or not -13<=observed_mean<=13):
        raise ValueError("observed mean required for positive coverage")
    known=coverage*observed_mean if coverage else 0
    return {"lower":known+(1-coverage)*lower,"upper":known+(1-coverage)*upper,
            "missing_fraction":1-coverage,
            "interpretation":"hypothetical completion of empirical sample, not identified full ERV"}


@dataclass(frozen=True, slots=True)
class MultiControlEstimate:
    fingerprint: str
    configuration: ERVConfig
    family: ControlFamily
    control_limit: int
    requested: int
    sampled: int
    evaluable: int
    coverage: float
    sampling_status: object
    weighting_status: object
    evidence: tuple
    effects: tuple[MultiControlEffect, ...]
    weights: tuple
    targets: tuple
    completion_bounds: object
    full_hard_evidence_erv: None = None


def estimate_multicontrol(state: AuctionInformationState, studied: Suit, trump: Suit, session, *,
                          config=ERVConfig(), family=ControlFamily.SPOT_RELOCATION,
                          control_limit=8, declarer=None):
    if not isinstance(state,AuctionInformationState):
        raise TypeError("AuctionInformationState required; source deals are not accepted")
    if not isinstance(config,ERVConfig):
        raise TypeError("ERVConfig required")
    declarer=state.partner if declarer is None else declarer
    sampled=ConditionalSampler(state).sample(config.sampling).model
    effects=[]
    for hypothesis in sampled.samples:
        mapping=dict(hypothesis.hands)
        mapping[state.perspective]=state.own_hand
        deal=Deal(config.sampling.seed,tuple((s,mapping[s]) for s in SEATS))
        effects.append(evaluate_controls(deal,state.perspective,studied,trump,declarer,session,
            family=family,control_limit=control_limit,control_seed=config.control_seed))
    weights=tuple(w.as_fraction() for w in sampled.weights)
    targets=[]
    for name in ("pta2_selected","first_valid","uniform_controls","median_controls"):
        def value(effect):
            if not effect.evaluable:
                return None
            return {"pta2_selected":effect.pta2_selected_delta,"first_valid":effect.first_valid_delta,
                    "uniform_controls":effect.distribution.mean,"median_controls":effect.distribution.median}[name]
        valid=[(value(e),w) for e,w in zip(effects,weights) if value(e) is not None]
        targets.append((name,target_statistics([v for v,w in valid],[w for v,w in valid])))
    stats=dict(targets)["uniform_controls"]
    bounds=missing_effect_bounds(stats["mean"],stats["mass"]) if sampled.accepted else None
    return MultiControlEstimate(information_fingerprint(state),config,family,control_limit,sampled.requested,
        sampled.accepted,stats["count"],stats["mass"],sampled.sampling_status,sampled.weighting_status,
        state.updates,tuple(effects),weights,tuple(targets),bounds)