"""PT-A2C experimental target comparison; no target is adopted for bidding.

B: minimal physical relocation with fixed honors/trumps, defenders may change.
C: finite nearest matched set from the explicitly defined D reference.
D: uniform physical nontrump-spot assignments given all honor/trump ownership
   and viewpoint studied length exactly two. Not a causal ruff count.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from itertools import combinations, permutations
from math import comb, factorial, sqrt
import random
from statistics import mean, stdev

from .auction_information import AuctionInformationState
from .conditional_hidden_hand import ConditionalSampler
from .counterfactual_calibration import (
    ControlFamily, evaluate_controls, pre_control_features, target_statistics,
)
from .deals import Deal
from .expected_ruffing_research import ERVConfig, ResearchSolverSession, SEATS, information_fingerprint
from .models import Hand, Rank, Seat, Suit
from .trick_solver import TrickSolverStatus


class TargetKind(str, Enum):
    STRUCTURAL = "B_structural_relocation"
    MATCHED = "C_finite_matched_expectation"
    BASELINE = "D_uniform_conditional_baseline"


class Exclusion(str, Enum):
    NOT_OWN_SHORTNESS = "own_singleton_or_void_required"
    STUDIED_TRUMP = "studied_suit_is_trump"
    FIXED_CARD_CAPACITY = "fixed_honors_and_trumps_leave_no_doubleton_capacity"
    SPOT_SUPPLY = "insufficient_free_studied_or_compensation_spots"
    COMPENSATION_FLOOR = "structural_own_compensation_floor"
    SOLVER_FAILURE = "solver_failure_or_budget_exhausted"


class MatchingPriority(str, Enum):
    DEFENDERS_FIRST = "defenders_then_partner"
    PARTNER_FIRST = "partner_then_defenders"


@dataclass(frozen=True, slots=True)
class TargetConfig:
    reference_draws: int = 16
    matching_pool: int = 64
    matched_controls: int = 8
    control_seed: int = 12002
    priority: MatchingPriority = MatchingPriority.DEFENDERS_FIRST
    exchange_controls: int = 8

    def __post_init__(self):
        if any(type(x) is not int or x<1 for x in
               (self.reference_draws,self.matching_pool,self.matched_controls,self.exchange_controls)):
            raise ValueError("positive integer budgets required")
        if self.matching_pool<self.reference_draws or self.matched_controls>self.matching_pool:
            raise ValueError("pool must contain reference and matched draw budgets")
        if type(self.control_seed) is not int or not isinstance(self.priority,MatchingPriority):
            raise TypeError("integer seed and typed matching priority required")


def _fixed(hand, trump):
    return frozenset(c for c in hand.cards if c.rank>=Rank.JACK or c.suit is trump)


def fixed_feature_errors(source, control, perspective, studied, trump):
    errors=[]
    for seat in SEATS:
        if _fixed(source.hand(seat),trump)!=_fixed(control.hand(seat),trump):
            errors.append("honor_or_trump_ownership_"+seat.value)
    if control.hand(perspective).length(studied)!=2:
        errors.append("viewpoint_studied_length_not_two")
    return tuple(errors)


@dataclass(frozen=True, slots=True)
class ReferenceSupport:
    exclusions: tuple[Exclusion, ...]
    physical_assignments: int
    own_free_slots: int
    own_required_studied_spots: int


def reference_support(source, perspective, studied, trump):
    own=source.hand(perspective)
    if studied is trump:
        return ReferenceSupport((Exclusion.STUDIED_TRUMP,),0,0,0)
    if own.length(studied) not in (0,1):
        return ReferenceSupport((Exclusion.NOT_OWN_SHORTNESS,),0,0,0)
    fixed={s:_fixed(source.hand(s),trump) for s in SEATS}
    free=sorted(c for s in SEATS for c in source.hand(s).cards-fixed[s])
    slots={s:13-len(fixed[s]) for s in SEATS}
    need=2-sum(c.suit is studied for c in fixed[perspective])
    own_rest=slots[perspective]-need
    if own_rest<0:
        return ReferenceSupport((Exclusion.FIXED_CARD_CAPACITY,),0,slots[perspective],need)
    a=sum(c.suit is studied for c in free)
    b=len(free)-a
    if need>a or own_rest>b:
        return ReferenceSupport((Exclusion.SPOT_SUPPLY,),0,slots[perspective],need)
    remaining=len(free)-slots[perspective]
    assignments=comb(a,need)*comb(b,own_rest)*factorial(remaining)
    for seat in SEATS:
        if seat is not perspective:
            assignments//=factorial(slots[seat])
    return ReferenceSupport((),assignments,slots[perspective],need)


def reference_controls(source, perspective, studied, trump, *, draws, seed):
    """IID uniform exact-card assignments, with replacement; no rejection.

    Choose own studied spots, then own other spots, then uniformly partition the
    remaining spots into fixed seat vacancies. Every legal assignment has the
    same product probability. Source spot locations do not set the reference.
    """
    if type(draws) is not int or draws<1:
        raise ValueError("positive draws required")
    support=reference_support(source,perspective,studied,trump)
    if support.exclusions:
        return ()
    fixed={s:_fixed(source.hand(s),trump) for s in SEATS}
    free=sorted(c for s in SEATS for c in source.hand(s).cards-fixed[s])
    studied_cards=[c for c in free if c.suit is studied]
    other_cards=[c for c in free if c.suit is not studied]
    rng=random.Random(seed)
    controls=[]
    for _ in range(draws):
        own_spots=set(rng.sample(studied_cards,support.own_required_studied_spots))
        own_spots.update(rng.sample(other_cards,support.own_free_slots-len(own_spots)))
        rest=[c for c in free if c not in own_spots]
        rng.shuffle(rest)
        mapping={perspective:Hand.from_cards(fixed[perspective]|own_spots)}
        offset=0
        for seat in SEATS:
            if seat is perspective:
                continue
            n=13-len(fixed[seat])
            mapping[seat]=Hand.from_cards(fixed[seat]|set(rest[offset:offset+n]))
            offset+=n
        control=Deal(0,tuple((s,mapping[s]) for s in SEATS))
        assert not fixed_feature_errors(source,control,perspective,studied,trump)
        controls.append(control)
    return tuple(controls)


def matching_distance(source, control, perspective, studied, trump, *,
                      priority=MatchingPriority.DEFENDERS_FIRST):
    """Lexicographic shape distance, not hidden weighted scalar 'similarity'.

    Defender/partner nontrump L1 length differences, own other-side L1 lengths,
    then change in the published ruffable-loser proxy. All HCP/honors/trumps exact.
    """
    if fixed_feature_errors(source,control,perspective,studied,trump):
        raise ValueError("candidate violates hard matching features")
    if not isinstance(priority,MatchingPriority):
        raise TypeError("typed matching priority required")
    partner=perspective.partner()
    defenders=tuple(s for s in SEATS if s not in (perspective,partner))
    def distance(seats,suits):
        return sum(abs(source.hand(s).length(t)-control.hand(s).length(t)) for s in seats for t in suits)
    nontrumps=tuple(s for s in Suit if s is not trump)
    defender=distance(defenders,nontrumps)
    partner_diff=distance((partner,),nontrumps)
    own=distance((perspective,),tuple(s for s in nontrumps if s is not studied))
    before=pre_control_features(source,perspective,studied,trump)["ruffable_loser_proxy"]
    after=pre_control_features(control,perspective,studied,trump)["ruffable_loser_proxy"]
    leading=(defender,partner_diff) if priority is MatchingPriority.DEFENDERS_FIRST else (partner_diff,defender)
    return (*leading,own,abs(before-after))


def select_matched(source, controls, perspective, studied, trump, *, count, priority):
    if type(count) is not int or count<1:
        raise ValueError("positive match count required")
    unique={d.serialize():d for d in controls}
    ordered=sorted(unique,key=lambda key:(
        matching_distance(source,unique[key],perspective,studied,trump,priority=priority),
        sha256(("PTA2C-match:"+key).encode()).digest(),key))
    return tuple(unique[key] for key in ordered[:count])


def structural_controls(source, perspective, studied, trump):
    """Minimum r spot swaps; donors may be partner OR defenders, no donor floor.

    Own compensation suits retain their old PT-1B floors. First minimize number
    of changed defender cards, then match distance. No DDS outcome selects a control.
    """
    support=reference_support(source,perspective,studied,trump)
    if support.exclusions:
        return (),support.exclusions
    own=source.hand(perspective)
    required=2-own.length(studied)
    incoming=sorted((c,s) for s in SEATS if s is not perspective
                    for c in source.hand(s).cards_in(studied) if c.rank<Rank.JACK)
    outgoing=sorted(c for c in own.cards if c.rank<Rank.JACK and c.suit not in (studied,trump))
    unique={}
    for take in combinations(incoming,required):
        for give in combinations(outgoing,required):
            if any(own.length(s)-sum(c.suit is s for c in give)<min(own.length(s),2)
                   for s in Suit if s not in (studied,trump)):
                continue
            for ordered in permutations(give):
                hands={s:set(source.hand(s).cards) for s in SEATS}
                for (card,donor),compensation in zip(take,ordered):
                    hands[donor].remove(card)
                    hands[perspective].remove(compensation)
                    hands[perspective].add(card)
                    hands[donor].add(compensation)
                control=Deal(0,tuple((s,Hand.from_cards(hands[s])) for s in SEATS))
                assert not fixed_feature_errors(source,control,perspective,studied,trump)
                unique[control.serialize()]=control
    if not unique:
        return (), (Exclusion.COMPENSATION_FLOOR,)
    defenders=tuple(s for s in SEATS if s not in (perspective,perspective.partner()))
    def key(control):
        changed=sum(len(source.hand(s).cards-control.hand(s).cards) for s in defenders)
        return (changed,matching_distance(source,control,perspective,studied,trump),
                sha256(("PTA2C-structural:"+control.serialize()).encode()).digest())
    return tuple(sorted(unique.values(),key=key)),()


@dataclass(frozen=True, slots=True)
class CandidateResult:
    target: TargetKind
    exclusions: tuple[Exclusion, ...]
    delta: float | None
    source_tricks: int | None
    control_mean_tricks: float | None
    control_count: int
    distinct_controls: int
    candidate_population: int
    control_trick_sd: float | None
    finite_reference_se: float | None
    delta_range: tuple[int,int] | None
    distances: tuple
    control_results: tuple
    note: str


def _score(kind, source_result, controls, population, exclusions, source, perspective, studied, trump,
           declarer, session, config):
    results=tuple(session.solve(d,declarer,trump) for d in controls)
    if not exclusions and (source_result.status is not TrickSolverStatus.SUCCESS or
                           any(r.status is not TrickSolverStatus.SUCCESS for r in results)):
        exclusions=(Exclusion.SOLVER_FAILURE,)
    values=[r.maximum_declarer_tricks for r in results]
    if exclusions or not values:
        return CandidateResult(kind,exclusions,None,source_result.maximum_declarer_tricks,None,len(results),
            len({d.serialize() for d in controls}),population,None,None,None,(),results,"not evaluable; never zero")
    center=mean(values)
    sd=stdev(values) if len(values)>1 else None
    iid_se=sd/sqrt(len(values)) if kind is TargetKind.BASELINE and sd is not None else None
    deltas=[source_result.maximum_declarer_tricks-v for v in values]
    return CandidateResult(kind,(),source_result.maximum_declarer_tricks-center,source_result.maximum_declarer_tricks,
        center,len(values),len({d.serialize() for d in controls}),population,sd,iid_se,(min(deltas),max(deltas)),
        tuple(matching_distance(source,d,perspective,studied,trump,priority=config.priority) for d in controls),
        results,"IID reference SE only for D; matched C controls are selected/dependent; B is one specified relocation")


@dataclass(frozen=True, slots=True)
class TargetComparison:
    source_deal_id: str
    perspective: Seat
    studied_suit: Suit
    trump: Suit
    declarer: Seat
    configuration: TargetConfig
    source_solver: object
    exchange: object
    candidates: tuple[CandidateResult,...]
    support: ReferenceSupport
    features: tuple


def evaluate_target_candidates(source, perspective, studied, trump, declarer, session, *, config=TargetConfig()):
    if not isinstance(source,Deal) or not isinstance(config,TargetConfig):
        raise TypeError("physical source deal and typed target configuration required")
    if declarer not in (perspective,perspective.partner()):
        raise ValueError("declarer must be in viewpoint partnership")
    source_result=session.solve(source,declarer,trump)
    exchange=evaluate_controls(source,perspective,studied,trump,declarer,session,
        family=ControlFamily.BASE,control_limit=config.exchange_controls)
    support=reference_support(source,perspective,studied,trump)
    seed=int.from_bytes(sha256((str(config.control_seed)+":"+source.serialize()).encode()).digest()[:8],"big")
    pool=reference_controls(source,perspective,studied,trump,draws=config.matching_pool,seed=seed)
    matched=select_matched(source,pool,perspective,studied,trump,count=config.matched_controls,priority=config.priority)
    structural,reasons=structural_controls(source,perspective,studied,trump)
    specifications=(
        (TargetKind.STRUCTURAL,structural[:1],len(structural),reasons),
        (TargetKind.MATCHED,matched,len({d.serialize() for d in pool}),support.exclusions),
        (TargetKind.BASELINE,pool[:config.reference_draws],support.physical_assignments,support.exclusions))
    results=tuple(_score(kind,source_result,controls,n,reasons,source,perspective,studied,trump,declarer,session,config)
                  for kind,controls,n,reasons in specifications)
    return TargetComparison(source.serialize(),perspective,studied,trump,declarer,config,source_result,exchange,
        results,support,tuple(sorted(pre_control_features(source,perspective,studied,trump).items())))


@dataclass(frozen=True, slots=True)
class ExperimentalExpectation:
    fingerprint: str
    sampling_configuration: ERVConfig
    target_configuration: TargetConfig
    requested: int
    sampled: int
    weighting_status: object
    sampling_status: object
    target_statistics: tuple
    comparisons: tuple
    weights: tuple
    evidence: tuple
    adopted_target: None = None


def compare_candidate_expectations(state, studied, trump, session, *, sampling=ERVConfig(),
                                   targets=TargetConfig(), declarer=None):
    """Experimental comparison only: does not replace the existing PT-A2 target."""
    if not isinstance(state,AuctionInformationState) or not isinstance(sampling,ERVConfig):
        raise TypeError("visible AuctionInformationState and hard-only ERVConfig required")
    declarer=state.partner if declarer is None else declarer
    model=ConditionalSampler(state).sample(sampling.sampling).model
    rows=[]
    for hypothesis in model.samples:
        mapping=dict(hypothesis.hands)
        mapping[state.perspective]=state.own_hand
        deal=Deal(0,tuple((s,mapping[s]) for s in SEATS))
        rows.append(evaluate_target_candidates(deal,state.perspective,studied,trump,declarer,session,config=targets))
    weights=tuple(w.as_fraction() for w in model.weights)
    summaries=[]
    for kind in TargetKind:
        valid=[(next(c.delta for c in row.candidates if c.target is kind),w) for row,w in zip(rows,weights)
               if not next(c.exclusions for c in row.candidates if c.target is kind)]
        summaries.append((kind,target_statistics([v for v,w in valid],[w for v,w in valid])))
    return ExperimentalExpectation(information_fingerprint(state),sampling,targets,model.requested,model.accepted,
        model.weighting_status,model.sampling_status,tuple(summaries),tuple(rows),weights,state.updates)