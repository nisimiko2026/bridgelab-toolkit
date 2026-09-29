"""PT-A2D research: physical play states, exact small-game minimax and bounds.

This is a full-information diagnostic, never an auction-time valuation API.
A winning ruff is a trump winner on a nontrump lead. Studied ruffs additionally
require that the winning seat is the viewpoint and the lead is the studied suit.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from .models import Card, Rank, Seat, Suit
from .deals import Deal

SEATS = tuple(Seat)


@dataclass(frozen=True, slots=True)
class PlayPosition:
    """Remaining cards, clockwise trick prefix, and leader. No cards are replaced."""
    hands: tuple[frozenset[Card], ...]
    leader: Seat
    trump: Suit
    trick: tuple[Card, ...] = ()

    def __post_init__(self):
        if not isinstance(self.leader, Seat) or not isinstance(self.trump, Suit):
            raise TypeError('typed leader and trump required')
        if len(self.hands) != 4 or len(self.trick) > 3:
            raise ValueError('four hands and at most three played cards required')
        if any(not isinstance(h, frozenset) for h in self.hands):
            raise TypeError('immutable card sets required')
        cards = [c for h in self.hands for c in h] + list(self.trick)
        if any(not isinstance(c, Card) for c in cards) or len(set(cards)) != len(cards):
            raise ValueError('unique physical cards required')
        sizes = [len(h) for h in self.hands]
        for i in range(len(self.trick)):
            sizes[(SEATS.index(self.leader)+i)%4] += 1
        if len(set(sizes)) != 1 or max(sizes) > 13:
            raise ValueError('remaining hands plus current trick must balance')
        for i,c in enumerate(self.trick[1:],1):
            hand=self.hands[(SEATS.index(self.leader)+i)%4]
            if c.suit != self.trick[0].suit and any(x.suit == self.trick[0].suit for x in hand):
                raise ValueError('trick prefix contains a revoke')

    @classmethod
    def from_deal(cls, deal, declarer, trump):
        if not isinstance(deal, Deal):
            raise TypeError('complete physical Deal required')
        return cls(tuple(deal.hand(s).cards for s in SEATS), declarer.next(), trump)

    @property
    def player(self):
        return SEATS[(SEATS.index(self.leader)+len(self.trick))%4]

    @property
    def remaining_tricks(self):
        return (sum(map(len,self.hands))+len(self.trick))//4

    def legal(self):
        hand=self.hands[SEATS.index(self.player)]
        follow=tuple(c for c in hand if self.trick and c.suit == self.trick[0].suit)
        return tuple(sorted(follow or hand))

    def advance(self, card):
        if card not in self.legal():
            raise ValueError('illegal play')
        hands=list(self.hands)
        hands[SEATS.index(self.player)] = hands[SEATS.index(self.player)]-{card}
        trick=self.trick+(card,)
        if len(trick)<4:
            return PlayPosition(tuple(hands),self.leader,self.trump,trick),None,None
        lead=trick[0].suit
        best=max(range(4),key=lambda i:(2 if trick[i].suit==self.trump else 1 if trick[i].suit==lead else 0,int(trick[i].rank)))
        winner=SEATS[(SEATS.index(self.leader)+best)%4]
        ruff=winner if lead!=self.trump and trick[best].suit==self.trump else None
        return PlayPosition(tuple(hands),winner,self.trump),winner,ruff


class Restriction(str,Enum):
    STRICT = 'ban_studied_ruff_actions'
    DISCARD_IF_POSSIBLE = 'ban_when_nonruff_legal_card_exists'
    NO_CREDIT = 'do_not_credit_studied_winning_ruffs'


class Status(str,Enum):
    EXACT = 'exact'
    BUDGET = 'budget_exhausted'
    INFEASIBLE = 'strict_rule_can_force_no_permitted_play'


class BudgetExceeded(Exception):
    pass


@dataclass(frozen=True,slots=True)
class PathResult:
    status: Status
    optimum: int | None
    # Joint outcomes over ALL locally minimax-optimal lines, both sides' ties.
    # (own studied winning ruffs, own all winning ruffs, partner all winning ruffs)
    profiles: tuple[tuple[int,int,int], ...]
    studied_ruff_bounds: tuple[int,int]
    every_optimal_line_requires_studied_ruff: bool | None
    reciprocal_ruff_presence: tuple[bool,bool] | None
    optimal_line_count: int | None


@dataclass(frozen=True,slots=True)
class RestrictedResult:
    policy: Restriction
    status: Status
    value: int | None
    loss: int | None


class MechanismOracle:
    """Memoized exact minimax; optional DDS ONLY for unrestricted optimal moves.

    Path bounds quantify observed mechanisms, not causal gained tricks. Strict
    infeasibility is propagated adversarially; it is never scored as zero.
    Non-credit is a different payoff game. Forced-discard policy allows forced
    ruffs and therefore is not a strict no-ruff essential-value estimate.
    """
    def __init__(self, perspective, studied, trump, *, max_nodes=100000, dds=None):
        if not isinstance(perspective,Seat) or not isinstance(studied,Suit) or not isinstance(trump,Suit):
            raise TypeError('typed seat and suits required')
        if studied==trump or type(max_nodes) is not int or max_nodes<1:
            raise ValueError('nontrump studied suit and positive integer budget required')
        self.perspective,self.studied,self.trump=perspective,studied,trump
        self.max_nodes,self.dds=max_nodes,dds
        self.values,self.paths={},{}
        self.nodes=self.cache_hits=self.edges=self.restricted_calls=0

    def _visit(self):
        if self.nodes>=self.max_nodes: raise BudgetExceeded()
        self.nodes+=1

    def _own_side(self,seat):
        return seat in (self.perspective,self.perspective.partner())

    def _attempt(self,p,c):
        return bool(p.trick and p.player==self.perspective and
                    p.trick[0].suit==self.studied and c.suit==self.trump)

    def _actions(self,p,policy):
        cards=p.legal()
        if policy in (Restriction.STRICT,Restriction.DISCARD_IF_POSSIBLE):
            permitted=tuple(c for c in cards if not self._attempt(p,c))
            if permitted or policy==Restriction.STRICT: return permitted
        return cards

    def _value(self,p,policy=None):
        key=(p,policy)
        if key in self.values:
            self.cache_hits+=1
            return self.values[key]
        self._visit()
        if not p.remaining_tricks: return 0
        choices=[]
        for card in self._actions(p,policy):
            child,winner,ruff=p.advance(card)
            reward=int(winner is not None and self._own_side(winner))
            if policy==Restriction.NO_CREDIT and ruff==self.perspective and p.trick[0].suit==self.studied:
                reward=0
            continuation=self._value(child,policy)
            choices.append(-100 if continuation==-100 else reward+continuation)
        value=(max(choices) if self._own_side(p.player) else min(choices)) if choices else -100
        self.values[key]=value
        return value

    def _optimal(self,p):
        if self.dds is not None:
            return self.dds.optimal(p,self.perspective)
        value=self._value(p)
        cards=[]
        for c in p.legal():
            child,winner,_=p.advance(c)
            if int(winner is not None and self._own_side(winner))+self._value(child)==value:
                cards.append(c)
        return value,tuple(cards)

    def _profiles(self,p):
        if p in self.paths:
            self.cache_hits+=1
            return self.paths[p]
        self._visit()
        if not p.remaining_tricks: return {(0,0,0)},1
        _,cards=self._optimal(p)
        profiles=set(); count=0
        for c in cards:
            self.edges+=1
            child,_,ruff=p.advance(c)
            future,n=self._profiles(child)
            event=(int(ruff==self.perspective and p.trick[0].suit==self.studied),
                   int(ruff==self.perspective),int(ruff==self.perspective.partner())) if ruff else (0,0,0)
            profiles.update(tuple(a+b for a,b in zip(row,event)) for row in future)
            count+=n
        self.paths[p]=(profiles,count)
        return profiles,count

    def analyze(self,p):
        self._validate(p)
        optimum=None
        try:
            optimum,_=self._optimal(p) if p.remaining_tricks else (0,())
            profiles,count=self._profiles(p)
        except BudgetExceeded:
            cap=sum(c.suit==self.trump for c in p.hands[SEATS.index(self.perspective)])
            # Public entry requires an empty trick, so no in-flight own trump is lost.
            return PathResult(Status.BUDGET,optimum,(),(0,min(cap,p.remaining_tricks)),None,None,None)
        values=[row[0] for row in profiles]
        reciprocal=[bool(row[1] and row[2]) for row in profiles]
        return PathResult(Status.EXACT,optimum,tuple(sorted(profiles)),(min(values),max(values)),
                          min(values)>0,(all(reciprocal),any(reciprocal)),count)

    def restricted(self,p,policy,*,unrestricted=None):
        self._validate(p)
        if not isinstance(policy,Restriction): raise TypeError('typed restriction required')
        self.restricted_calls+=1
        try:
            value=self._value(p,policy)
        except BudgetExceeded:
            return RestrictedResult(policy,Status.BUDGET,None,None)
        if value==-100:
            return RestrictedResult(policy,Status.INFEASIBLE,None,None)
        return RestrictedResult(policy,Status.EXACT,value,None if unrestricted is None else unrestricted-value)

    def _validate(self,p):
        if not isinstance(p,PlayPosition) or p.trump!=self.trump or p.trick:
            raise ValueError('matching physical position at a trick boundary required')
        if sum(c.suit==self.studied for c in p.hands[SEATS.index(self.perspective)])>1:
            raise ValueError('exact own singleton or void required')

    def statistics(self):
        return {'nodes':self.nodes,'cache_hits':self.cache_hits,'optimal_edges':self.edges,
                'restricted_solver_calls':self.restricted_calls,'cached_positions':len(self.values)+len(self.paths)}


class DDSOptimalMoves:
    """Lazy endplay adapter; per-card values orient to the side currently playing."""
    def __init__(self,max_calls=200):
        if type(max_calls) is not int or max_calls<1: raise ValueError('positive DDS budget required')
        self.max_calls=max_calls
        self.calls=self.cache_hits=0
        self.cache={}
        self.seconds=0.0

    def optimal(self,p,perspective):
        if not p.remaining_tricks: return 0,()
        if p in self.cache:
            self.cache_hits+=1
            score,cards=self.cache[p]
        else:
            if self.calls>=self.max_calls: raise BudgetExceeded()
            from endplay.types import Deal as EDeal,Player,Denom,Card as ECard
            from endplay.dds import solve_board
            from endplay.dds.solve import SolveMode
            def hand_text(hand):
                return '.'.join(''.join(c.rank.symbol for c in sorted(hand,reverse=True) if c.suit==s)
                                for s in (Suit.SPADES,Suit.HEARTS,Suit.DIAMONDS,Suit.CLUBS))
            d=EDeal('N:'+' '.join(hand_text(h) for h in p.hands),
                    first=Player[p.leader.name.lower()],trump=Denom[p.trump.name.lower()])
            for c in p.trick:
                d.play(ECard(c.suit.letter+c.rank.symbol),from_hand=False)
            started=perf_counter(); self.calls+=1
            results=list(solve_board(d,SolveMode.OptimalAll))
            self.seconds+=perf_counter()-started
            if not results: raise RuntimeError('DDS returned no optimal cards for a nonterminal position')
            scores={s for _,s in results}
            if len(scores)!=1: raise RuntimeError('OptimalAll returned unequal scores')
            score=scores.pop()
            cards=tuple(sorted(Card(Suit.parse(c.suit.name),Rank(int(c.rank.to_alternate()))) for c,_ in results))
            if any(c not in p.legal() for c in cards): raise RuntimeError('DDS returned an illegal card')
            self.cache[p]=score,cards
        value=score if p.player in (perspective,perspective.partner()) else p.remaining_tricks-score
        return value,cards
@dataclass(frozen=True,slots=True)
class StudiedBounds:
    """Certified envelope; unresolved endpoints are NOT attained extrema."""
    status: Status
    optimum: int | None
    minimum_lower_bound: int
    maximum_upper_bound: int
    extrema_exact: bool
    every_optimal_line_requires_ruff: bool | None
    resolved_subpositions: int


def bounded_studied_paths(position, perspective, studied, adapter, *, max_nodes=2000):
    """Full-deal, same-card optimal-DAG analysis with safe incomplete bounds.

    Zero future own trump or zero remaining studied cards proves zero studied
    winning ruffs without enumerating irrelevant continuations. No arbitrary PV.
    """
    validator=MechanismOracle(perspective,studied,position.trump,max_nodes=max_nodes)
    validator._validate(position)
    cache={}; nodes=0; resolved=0
    def visit(p):
        nonlocal nodes,resolved
        if p in cache: return cache[p]
        own_trumps=sum(c.suit==p.trump for c in p.hands[SEATS.index(perspective)])
        own_trumps+=sum(c.suit==p.trump and SEATS[(SEATS.index(p.leader)+i)%4]==perspective for i,c in enumerate(p.trick))
        studied_cards=sum(c.suit==studied for h in p.hands for c in h)+sum(c.suit==studied for c in p.trick)
        cap=min(own_trumps,studied_cards,p.remaining_tricks)
        if cap==0:
            resolved+=1
            return 0,0,True
        if nodes>=max_nodes: return 0,cap,False
        nodes+=1
        try: _,cards=adapter.optimal(p,perspective)
        except BudgetExceeded: return 0,cap,False
        lows=[]; highs=[]; exact=[]
        for c in cards:
            child,_,ruff=p.advance(c)
            event=int(ruff==perspective and p.trick[0].suit==studied) if ruff else 0
            lo,hi,done=visit(child)
            lows.append(event+lo);highs.append(event+hi);exact.append(done)
        lo,hi=min(lows),max(highs)
        done=all(exact) or lo==hi
        cache[p]=(lo,hi,done)
        if done: resolved+=1
        return cache[p]
    try: optimum,_=adapter.optimal(position,perspective)
    except BudgetExceeded: optimum=None
    lo,hi,done=visit(position)
    required=True if lo>0 else False if done else None
    result=StudiedBounds(Status.EXACT if done else Status.BUDGET,optimum,lo,hi,done,required,resolved)
    return result,{'path_nodes':nodes,'cached_path_positions':len(cache)}