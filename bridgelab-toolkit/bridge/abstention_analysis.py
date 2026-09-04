"""Objective classification of benchmark abstentions.

This module classifies hand/auction evidence only.  Labels are descriptive
mechanics, not bidding recommendations.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from .evaluation import evaluate_hand
from .models import Hand, Seat, Suit
from .sayc_coverage_benchmark import SaycCoverageBenchmarkReport


@dataclass(frozen=True,slots=True)
class AbstentionClassification:
    stage:str
    label:str
    seed:int
    auction:str
    seat:Seat
    hcp:int
    shape:tuple[int,int,int,int]


@dataclass(frozen=True,slots=True)
class AbstentionAnalysis:
    classifications:tuple[AbstentionClassification,...]
    stage_counts:tuple[tuple[str,int],...]
    label_counts:tuple[tuple[str,int],...]


def _opening_label(hand:Hand)->str:
    e=evaluate_hand(hand)
    h=e.hcp
    hearts=e.length(Suit.HEARTS); spades=e.length(Suit.SPADES)
    clubs=e.length(Suit.CLUBS); diamonds=e.length(Suit.DIAMONDS)
    if h < 12: return "opening.hcp-below-12"
    if h > 21: return "opening.hcp-above-21"
    if hearts>=5 and spades>=5 and hearts==spades: return "opening.equal-length-majors"
    if clubs==diamonds: return "opening.equal-length-minors"
    return "opening.other-unresolved"


def _response_label(opening:str,hand:Hand)->str:
    e=evaluate_hand(hand); h=e.hcp
    if opening=="1NT": return "response.after-1nt-unrouted"
    if opening=="1C":
        if 6<=h<=10 and e.is_balanced: return "response.1c.notrump-range-or-shape"
        if h>=6 and e.length(Suit.HEARTS)>=4 and e.length(Suit.SPADES)>=4:
            return "response.1c.both-four-card-majors"
        return "response.1c.other-unresolved"
    if opening=="1D":
        if 6<=h<=9 and e.is_balanced: return "response.1d.one-notrump-unresolved"
        return "response.1d.other-unresolved"
    if opening in ("1H","1S"):
        major=Suit.HEARTS if opening=="1H" else Suit.SPADES
        if 6<=h<=9 and e.length(major)<3: return f"response.{opening.lower()}.possible-one-notrump-no-treatment"
        if h>=12: return f"response.{opening.lower()}.high-values-or-policy-gated"
        return f"response.{opening.lower()}.other-unresolved"
    return "response.other-unresolved"


def analyze_benchmark_abstentions(report:SaycCoverageBenchmarkReport)->AbstentionAnalysis:
    rows=[]
    for case in report.batch.cases:
        result=case.result
        if result.stop_reason.value!="no-recommendation" or result.stopped_seat is None:
            continue
        seat=result.stopped_seat
        hand=case.deal.hand(seat)
        e=evaluate_hand(hand)
        depth=len(result.steps)
        if depth==0:
            stage="opening"; label=_opening_label(hand)
        elif depth==2:
            stage="response"
            opening=result.steps[0].call.serialize()
            label=_response_label(opening,hand)
        else:
            stage="continuation"
            label="continuation.unrouted-after-response"
        rows.append(AbstentionClassification(stage,label,case.deal.seed,result.final_auction,seat,e.hcp,hand.shape))
    stage=Counter(r.stage for r in rows); labels=Counter(r.label for r in rows)
    return AbstentionAnalysis(tuple(rows),tuple(sorted(stage.items())),tuple(sorted(labels.items())))
