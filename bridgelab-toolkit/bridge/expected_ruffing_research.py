"""PT-A2 research only: paired DDS contrast averaged over PT-A1B hypotheses.

No endplay import, production registration, bid interpretation or point conversion.
A paired contrast includes spot/length redistribution effects, not isolated ruffs.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, fields, is_dataclass, replace
from enum import Enum
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import json
from math import sqrt
import random
from time import perf_counter

from .auction_information import AuctionInformationState, ConstraintProvenance, EvidenceOrigin, FitInformation
from .conditional_hidden_hand import ConditionalSampler, ConditionalDiagnostics
from .deals import Deal
from .hidden_hand_probability import SamplingConfig, SamplingStatus, WeightingStatus
from .models import Card, Rank, Seat, Suit
from .playing_trick_shortness_pairs import (
    CardExchange, SelectedControl, apply_exchange, shortness_step_candidates, singleton_candidates,
)
from .trick_solver import TrickSolver, TrickSolverResult, TrickSolverStatus

METHOD = "PT-1B-uniform-spot-path-to-doubleton-v1"
SEATS = (Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST)


def jsonable(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted((jsonable(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    return value


def information_fingerprint(state: AuctionInformationState) -> str:
    return sha256(json.dumps(jsonable(state), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class PairStatus(str, Enum):
    EVALUABLE = "evaluable"
    NOT_EVALUABLE = "not_evaluable"
    SOLVER_FAILURE = "solver_failure"


class ERVStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NOT_EVALUABLE = "not_evaluable"


@dataclass(frozen=True, slots=True)
class ERVConfig:
    sampling: SamplingConfig = SamplingConfig()
    control_seed: int = 0
    solver_configuration: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        if not isinstance(self.sampling, SamplingConfig) or type(self.control_seed) is not int:
            raise TypeError("typed sampling config and integer control seed required")
        if self.sampling.likelihoods:
            raise ValueError("PT-A2 is hard-evidence-only; explicit soft likelihoods are out of scope")
        if not isinstance(self.solver_configuration, tuple) or any(
            not isinstance(p, tuple) or len(p) != 2 or any(not isinstance(x, str) for x in p)
            for p in self.solver_configuration):
            raise TypeError("solver configuration must be immutable string pairs")


@dataclass(frozen=True, slots=True)
class EffectDistribution:
    count: int
    weight_mass: float
    effective_sample_size: float
    mean: float | None
    variance: float | None
    standard_deviation: float | None
    standard_error: float | None
    confidence_interval_95: tuple[float, float] | None
    p_positive: float | None
    p_zero: float | None
    p_negative: float | None
    quantiles: tuple[tuple[float, int], ...]
    outcomes: tuple[tuple[int, float], ...]


def summarize_effects(values, weights) -> EffectDistribution:
    """Weighted distribution; CI describes Monte Carlo error, not model ambiguity."""
    values, weights = tuple(values), tuple(Fraction(w) for w in weights)
    if len(values) != len(weights) or any(type(x) is not int or not -13 <= x <= 13 for x in values):
        raise ValueError("paired integer trick effects and equal-length weights required")
    if any(w < 0 for w in weights):
        raise ValueError("weights must be nonnegative")
    total = sum(weights, Fraction())
    if not total:
        return EffectDistribution(len(values), 0.0, 0.0, None, None, None, None, None,
                                  None, None, None, (), ())
    normalized = tuple(w / total for w in weights)
    square_sum = sum((w*w for w in normalized), Fraction())
    ess = float(1 / square_sum)
    mean = sum((w*x for w, x in zip(normalized, values)), Fraction())
    variance = sum((w*(x-mean)**2 for w, x in zip(normalized, values)), Fraction())
    se = sqrt(float(variance / (1-square_sum)) / ess) if square_sum < 1 else None
    ci = (float(mean)-1.96*se, float(mean)+1.96*se) if se is not None else None
    histogram = Counter()
    for x, w in zip(values, normalized):
        histogram[x] += w
    quantiles = []
    for q in (0.05, 0.25, 0.5, 0.75, 0.95):
        cumulative = Fraction()
        for x, w in sorted(histogram.items()):
            cumulative += w
            if cumulative >= Fraction(str(q)):
                quantiles.append((q, x))
                break
    probability = lambda predicate: float(sum((w for x, w in histogram.items() if predicate(x)), Fraction()))
    return EffectDistribution(len(values), float(total), ess, float(mean), float(variance),
                              sqrt(float(variance)), se, ci, probability(lambda x:x>0),
                              probability(lambda x:x==0), probability(lambda x:x<0),
                              tuple(quantiles), tuple((x,float(w)) for x,w in sorted(histogram.items())))


def _rotate(deal, seat_map):
    return Deal(deal.seed, tuple((seat_map[s], hand) for s, hand in deal.hands))


@lru_cache(maxsize=4)
def paired_controls(deal: Deal, perspective: Seat, studied_suit: Suit,
                    trump: Suit) -> tuple[SelectedControl, ...]:
    """Uniform ordered legal paths to doubleton; voids require two exchanges.

    A clockwise seat rotation reuses PT-1B's N/S machinery without relabeling suits.
    Honors, all trump cards, defenders and declarer remain fixed in original seats.
    """
    if not isinstance(deal, Deal) or not isinstance(perspective, Seat):
        raise TypeError("physical research deal and perspective required")
    if not isinstance(studied_suit, Suit) or not isinstance(trump, Suit):
        raise TypeError("typed studied and trump suits required")
    length = deal.hand(perspective).length(studied_suit)
    if studied_suit is trump or length not in (0, 1):
        return ()
    offset = (2-SEATS.index(perspective)) % 4
    forward = {s:SEATS[(i+offset)%4] for i,s in enumerate(SEATS)}
    backward = {v:k for k,v in forward.items()}
    canonical = _rotate(deal, forward)
    first = shortness_step_candidates(canonical, Seat.SOUTH, studied_suit, trump)
    paths = ((d,(x,)) for d,x in first) if length == 1 else (
        (final,(x,y)) for intermediate,x in first
        for final,y in singleton_candidates(intermediate,Seat.SOUTH,studied_suit,trump))
    result=[]
    for control, exchanges in paths:
        restored = _rotate(control, backward)
        records = tuple(replace(x, added_from=backward[x.added_from], added_to=backward[x.added_to],
                                removed_from=backward[x.removed_from], removed_to=backward[x.removed_to])
                        for x in exchanges)
        result.append(SelectedControl(restored,records,0,0))
    return tuple(replace(x,candidate_exchange_count=len(result),selected_exchange_index=i)
                 for i,x in enumerate(result))


class ResearchSolverSession:
    """Bounded, single-threaded research cache. Runtime counters are not estimates."""
    def __init__(self, solver: TrickSolver, *, max_calls: int = 12000):
        if type(max_calls) is not int or max_calls < 1:
            raise ValueError("positive solver call budget required")
        self.solver, self.max_calls = solver, max_calls
        self.cache = {}
        self.calls = self.cache_hits = self.failures = 0
        self.wall_seconds = 0.0

    def solve(self, deal, declarer, strain):
        key=(deal.serialize(),declarer,strain)
        if key in self.cache:
            self.cache_hits+=1
            return self.cache[key]
        if self.calls >= self.max_calls:
            return TrickSolverResult("research-budget",None,key[0],declarer,strain,None,
                                     TrickSolverStatus.UNAVAILABLE,None,0.0,"solver_call_budget_exhausted")
        self.calls+=1
        start=perf_counter()
        try:
            result=self.solver.solve(deal,declarer,strain)
            if (result.deal_id,result.declarer,result.strain,result.opening_lead)!=(key[0],declarer,strain,None):
                raise ValueError("solver returned mismatched deal/contract provenance")
        except Exception as exc:
            result=TrickSolverResult(type(self.solver).__name__,None,key[0],declarer,strain,None,
                                     TrickSolverStatus.FAILED,None,0.0,f"{type(exc).__name__}: {exc}")
        self.wall_seconds+=perf_counter()-start
        self.failures += result.status is not TrickSolverStatus.SUCCESS
        stable=replace(result,elapsed_seconds=0.0)
        self.cache[key]=stable
        return stable


@dataclass(frozen=True, slots=True)
class PairedEffect:
    source_deal_id: str
    control_deal_id: str | None
    status: PairStatus
    reason: str | None
    candidate_count: int
    selected_index: int | None
    exchanges: tuple[CardExchange, ...]
    source_solver: TrickSolverResult | None
    control_solver: TrickSolverResult | None
    delta_tricks: int | None
    total_trumps: int
    trump_role: str
    ruffable_loser_proxy: int
    side_ace_entries: tuple[int, int]


def control_seed_for_deal(deal: Deal, seed: int) -> int:
    """Stable per-deal PT-1B selection: repeated hypotheses use the same control."""
    return int.from_bytes(sha256((str(seed)+":"+deal.serialize()).encode()).digest()[:8],"big")


def realized_shortness_effect(deal: Deal, perspective: Seat, studied_suit: Suit,
                             trump: Suit, declarer: Seat, session: ResearchSolverSession,
                             *, control_seed: int = 0, control_index: int | None = None) -> PairedEffect:
    """Full-information validation target; never an input to partial ERV."""
    if declarer not in (perspective,perspective.partner()):
        raise ValueError("declarer must be in the perspective partnership")
    own,other=deal.hand(perspective),deal.hand(perspective.partner())
    role="short" if own.length(trump)<other.length(trump) else "long" if own.length(trump)>other.length(trump) else "equal"
    ranks={c.rank for c in other.cards_in(studied_suit)}
    top=0
    for n in range(14,1,-1):
        if Rank(n) not in ranks: break
        top+=1
    losers=max(0,other.length(studied_suit)-top-own.length(studied_suit))
    entries=tuple(sum(c.rank is Rank.ACE and c.suit is not trump for c in h.cards) for h in (own,other))
    common=dict(source_deal_id=deal.serialize(),total_trumps=own.length(trump)+other.length(trump),
                trump_role=role,ruffable_loser_proxy=losers,side_ace_entries=entries)
    candidates=paired_controls(deal,perspective,studied_suit,trump)
    if not candidates:
        reason="own_shortness_required" if own.length(studied_suit) not in (0,1) else (
            "studied_suit_is_trump" if studied_suit is trump else "no_legal_doubleton_control")
        return PairedEffect(**common,control_deal_id=None,status=PairStatus.NOT_EVALUABLE,
                            reason=reason,candidate_count=0,selected_index=None,exchanges=(),
                            source_solver=None,control_solver=None,delta_tricks=None)
    index=random.Random(control_seed_for_deal(deal,control_seed)).randrange(len(candidates)) if control_index is None else control_index
    if type(index) is not int or not 0<=index<len(candidates):
        raise ValueError("invalid control index")
    control=candidates[index]
    replay=control.deal
    for exchange in reversed(control.exchanges):
        replay=apply_exchange(replay,exchange.inverse())
    if replay.serialize()!=deal.serialize() or control.deal.hand(perspective).length(studied_suit)!=2:
        raise AssertionError("counterfactual failed reversal or target length")
    source_result=session.solve(deal,declarer,trump)
    control_result=session.solve(control.deal,declarer,trump)
    successful=all(x.status is TrickSolverStatus.SUCCESS for x in (source_result,control_result))
    return PairedEffect(**common,control_deal_id=control.deal.serialize(),
                        status=PairStatus.EVALUABLE if successful else PairStatus.SOLVER_FAILURE,
                        reason=None if successful else ("solver_call_budget_exhausted" if
                            any(x.error=="solver_call_budget_exhausted" for x in (source_result,control_result))
                            else "solver_failure_or_unavailable"),
                        candidate_count=len(candidates),selected_index=index,exchanges=control.exchanges,
                        source_solver=source_result,control_solver=control_result,
                        delta_tricks=source_result.maximum_declarer_tricks-control_result.maximum_declarer_tricks if successful else None)


def control_support_guaranteed(state: AuctionInformationState, studied: Suit, trump: Suit,
                               proposal_allocations: int, observed_valid: bool) -> bool:
    """Conservative proof of legal controls throughout support, not sample coverage."""
    length=state.own_hand.length(studied)
    if studied is trump or length not in (0,1) or not observed_valid:
        return False
    if proposal_allocations==1:
        return True  # The sole physical proposal was observed to have a valid control.
    required=2-length
    compensation=sum(min(max(state.own_hand.length(suit)-2,0),
                         sum(c.rank<Rank.JACK for c in state.own_hand.cards_in(suit)))
                     for suit in Suit if suit not in (studied,trump))
    lower=state.for_seat(state.partner).suit_range(studied).minimum
    unseen_honors=4-sum(c.rank>=Rank.JACK for c in state.own_hand.cards_in(studied))
    return compensation>=required and lower-required>=2 and lower-unseen_honors>=required


@dataclass(frozen=True, slots=True)
class ERVResult:
    information_state_fingerprint: str
    visible_hand: str
    perspective: Seat
    studied_suit: Suit
    shortness_type: str
    trump: Suit
    declarer: Seat
    fit: FitInformation
    configuration: ERVConfig
    method: str
    estimand: str
    status: ERVStatus
    requested_hypotheses: int
    sampled_hypotheses: int
    evaluable_hypotheses: int
    control_rejections: int
    solver_failed_hypotheses: int
    dds_failure_count: int = field(compare=False)
    not_evaluable_reasons: tuple[tuple[str,int], ...]
    sampling_status: SamplingStatus
    hard_soft_status: WeightingStatus
    sampling_diagnostics: ConditionalDiagnostics
    sample_effective_size: float
    evaluable_probability_mass: float
    distribution: EffectDistribution
    full_hard_evidence_mean: float | None
    control_support_guaranteed: bool
    effects: tuple[PairedEffect, ...]
    weights: tuple[Fraction, ...]
    evidence: tuple
    provenance: tuple[ConstraintProvenance, ...]


def estimate_erv(state: AuctionInformationState, studied_suit: Suit, trump: Suit,
                 solver: TrickSolver | ResearchSolverSession, *, declarer: Seat | None = None,
                 config: ERVConfig = ERVConfig()) -> ERVResult:
    """Hard-evidence partial-information oracle: no source Deal parameter.

    Missing pairs are never zeroes. distribution is conditional on evaluable
    controls and successful solves. full_hard_evidence_mean additionally requires
    a sufficient support-wide legal-control proof; zero observed attrition is insufficient.
    """
    if not isinstance(state,AuctionInformationState) or not isinstance(config,ERVConfig):
        raise TypeError("requires information state and ERVConfig")
    if not isinstance(studied_suit,Suit) or not isinstance(trump,Suit):
        raise TypeError("typed suits required")
    declarer=state.partner if declarer is None else declarer
    if declarer not in (state.perspective,state.partner):
        raise ValueError("declarer must be in the perspective partnership")
    session=solver if isinstance(solver,ResearchSolverSession) else ResearchSolverSession(solver)
    initial_failures=session.failures
    sampled=ConditionalSampler(state).sample(config.sampling)
    model=sampled.model
    effects=[]
    for hypothesis in model.samples:
        mapping=dict(hypothesis.hands)
        mapping[state.perspective]=state.own_hand
        deal=Deal(config.sampling.seed,tuple((seat,mapping[seat]) for seat in SEATS))
        effects.append(realized_shortness_effect(deal,state.perspective,studied_suit,trump,
                        declarer,session,control_seed=config.control_seed))
    weights=tuple(w.as_fraction() for w in model.weights)
    valid=[(effect.delta_tricks,w) for effect,w in zip(effects,weights) if effect.status is PairStatus.EVALUABLE]
    distribution=summarize_effects([x for x,w in valid],[w for x,w in valid])
    reasons=Counter(x.reason for x in effects if x.reason)
    if not effects:
        reasons["contradictory_or_no_sampled_hypotheses"]+=1
    control_rejections=sum(x.status is PairStatus.NOT_EVALUABLE for x in effects)
    failures=sum(x.status is PairStatus.SOLVER_FAILURE for x in effects)
    failed_calls=session.failures-initial_failures
    status=ERVStatus.NOT_EVALUABLE if not valid else ERVStatus.PARTIAL if (
        len(valid)!=len(effects) or model.sampling_status is not SamplingStatus.COMPLETE) else ERVStatus.COMPLETE
    provenance=tuple(dict.fromkeys(p for update in state.updates for p in update.provenance))+(
        ConstraintProvenance(EvidenceOrigin.OWN_HAND,"exact visible shortness"),
        ConstraintProvenance(EvidenceOrigin.DERIVED_ARITHMETIC,METHOD),)
    length=state.own_hand.length(studied_suit)
    support_guaranteed=control_support_guaranteed(state,studied_suit,trump,
        sampled.diagnostics.proposal_allocation_count,bool(valid))
    return ERVResult(information_fingerprint(state),state.own_hand.serialize(),state.perspective,
        studied_suit,("void","singleton","doubleton")[length] if length<=2 else "not_short",
        trump,declarer,state.fit(trump),config,METHOD,
        "E[paired trick contrast | hard evidence, legal doubleton control, successful solves]",
        status,model.requested,model.accepted,len(valid),control_rejections,failures,failed_calls,
        tuple(sorted(reasons.items())),model.sampling_status,model.weighting_status,sampled.diagnostics,
        float(model.effective_sample_size),distribution.weight_mass,distribution,
        distribution.mean if status is ERVStatus.COMPLETE and support_guaranteed else None,
        support_guaranteed,tuple(effects),weights,
        state.updates,provenance)
