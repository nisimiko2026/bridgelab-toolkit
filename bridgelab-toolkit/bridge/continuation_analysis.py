"""Exact-auction breakdown of continuation abstentions."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from .sayc_coverage_benchmark import SaycCoverageBenchmarkReport

@dataclass(frozen=True,slots=True)
class ContinuationAuctionCount:
    auction:str
    count:int

@dataclass(frozen=True,slots=True)
class ContinuationBreakdown:
    total:int
    auctions:tuple[ContinuationAuctionCount,...]

def continuation_breakdown(report:SaycCoverageBenchmarkReport)->ContinuationBreakdown:
    counts=Counter()
    for case in report.batch.cases:
        r=case.result
        if r.stop_reason.value=="no-recommendation" and len(r.steps)>=4:
            counts[r.final_auction]+=1
    ordered=tuple(
        ContinuationAuctionCount(auction,count)
        for auction,count in sorted(counts.items(),key=lambda item:(-item[1],item[0]))
    )
    return ContinuationBreakdown(sum(counts.values()),ordered)
