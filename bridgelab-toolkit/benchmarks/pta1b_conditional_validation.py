"""PT-A1B exact/reference comparisons, stress cases and separate setup timing."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import json
from math import comb, sqrt
from pathlib import Path
from time import perf_counter
import tracemalloc

from bridge.auction_information import AuctionConstraintUpdate, Certainty, ShapeEvidence
from bridge.conditional_hidden_hand import ConditionalSampler
from bridge.hidden_hand_probability import Feature, SamplingConfig, sample_hidden_hands, vacant_place_reference
from bridge.models import Seat, Suit
from benchmarks.pta1_probability_validation import OWN, SOURCE, exact_partner_joint, update
from bridge.auction_information import AuctionInformationState


def _mass_from_model(model, seat, feature):
    if not model.accepted:
        return {}
    return {value: float(p.as_fraction()) for value, p in model.marginal(seat, feature).outcomes}


def _diagnostics(model):
    return {"accepted": model.accepted, "requested": model.requested, "proposals": model.proposals,
            "rejections": dict(model.rejections), "rejection_rate": model.rejection_rate,
            "effective_sample_size": float(model.effective_sample_size),
            "sampling_status": model.sampling_status.value,
            "weighting_status": model.weighting_status.value, "seed": model.config.seed}


def _compare(conditional, reference, exacts):
    records, summaries = [], []
    for seat in (Seat.NORTH, Seat.WEST, Seat.EAST):
        for feature in Feature:
            c = _mass_from_model(conditional, seat, feature)
            r = _mass_from_model(reference, seat, feature)
            exact = exacts.get((seat, feature))
            values = sorted(set(c) | set(r) | (set(exact) if exact is not None else set()))
            if not values:
                continue
            events = []
            for value in values:
                pc, pr = c.get(value, 0), r.get(value, 0)
                pe = float(exact.get(value, 0)) if exact is not None else None
                n, nr = conditional.accepted, reference.accepted
                se = sqrt(pe * (1-pe) / n) if pe is not None and n else None
                pooled = (pc * n + pr * nr) / (n + nr) if n + nr else 0
                se_diff = sqrt(pooled * (1-pooled) * (1/n + 1/nr)) if n and nr else None
                events.append({
                    "outcome": value, "conditional": pc, "reference": pr if nr else None,
                    "exact": pe, "difference_from_exact": pc-pe if pe is not None else None,
                    "standard_error_vs_exact": se,
                    "z_vs_exact": (pc-pe)/se if se else None,
                    "difference_from_reference": pc-pr if nr else None,
                    "standard_error_of_difference": se_diff,
                    "z_vs_reference": (pc-pr)/se_diff if se_diff else None,
                    "conditional_n": n, "reference_n": nr,
                    "conditional_ess": float(conditional.effective_sample_size),
                    "reference_ess": float(reference.effective_sample_size),
                })
            max_exact = max((abs(e["z_vs_exact"]) for e in events if e["z_vs_exact"] is not None), default=None)
            max_ref = max((abs(e["z_vs_reference"]) for e in events if e["z_vs_reference"] is not None), default=None)
            summaries.append({
                "seat": seat.value, "feature": feature.value, "bins_compared": len(values),
                "total_variation_vs_exact": sum(abs(c.get(v,0)-float(exact.get(v,0))) for v in values)/2 if exact is not None else None,
                "total_variation_vs_reference": sum(abs(c.get(v,0)-r.get(v,0)) for v in values)/2 if reference.accepted else None,
                "max_abs_z_vs_exact": max_exact, "max_abs_z_vs_reference": max_ref,
            })
            # Retain every numeric bin and representative shape bins; aggregate
            # shape metrics above always use the full observed/expected union.
            if feature is Feature.SHAPE:
                events = sorted(events, key=lambda e: -(e["exact"] if e["exact"] is not None
                                                         else e["conditional"] + (e["reference"] or 0)))[:5]
            records.extend({"seat": seat.value, "feature": feature.value, **e} for e in events)
    return records, summaries


def _partner_exact(joint, predicate):
    subset = {key: p for key, p in joint.items() if predicate(*key)}
    total = sum(subset.values(), Fraction())
    result = {}
    for feature, index in ((Feature.SPADES, 0), (Feature.HCP, 1)):
        counts = Counter()
        for key, p in subset.items():
            counts[key[index]] += p / total
        result[Seat.NORTH, feature] = counts
    # No defender-specific evidence in these experiments. Given partner spades,
    # each defender gets a uniform 13-card subset of the remaining 26 cards.
    defenders = Counter()
    for (spades, _), p in subset.items():
        outstanding = 8 - spades
        for k in range(outstanding + 1):
            defenders[k] += p / total * Fraction(comb(outstanding, k) * comb(26-outstanding, 13-k), comb(26,13))
    result[Seat.WEST, Feature.SPADES] = defenders
    result[Seat.EAST, Feature.SPADES] = defenders
    return result


def run(samples=4000, max_proposals=200000):
    base = AuctionInformationState.start(Seat.SOUTH, OWN, Seat.SOUTH)
    joint = exact_partner_joint(OWN)
    alternatives = ((4,4,4,1),(5,3,3,2))
    cases = [
        ("unconstrained", (), 731, lambda s,h: True),
        ("partner_spades_ge3", (update(Seat.NORTH,suit=Suit.SPADES,low=3),), 733, lambda s,h:s>=3),
        ("partner_spades_eq4", (update(Seat.NORTH,suit=Suit.SPADES,low=4,high=4),), 735, lambda s,h:s==4),
        ("partner_hcp_10_12", (update(Seat.NORTH,low=10,high=12),), 736, lambda s,h:10<=h<=12),
        ("partner_hcp_eq11", (update(Seat.NORTH,low=11,high=11),), 737, lambda s,h:h==11),
        ("combined", (update(Seat.NORTH,suit=Suit.SPADES,low=4), update(Seat.NORTH,low=10,high=12)), 738,
         lambda s,h:s>=4 and 10<=h<=12),
        ("defender_diamonds_5_3", (
            update(Seat.NORTH,suit=Suit.SPADES,low=4,high=4),
            update(Seat.WEST,suit=Suit.DIAMONDS,low=5,high=5),
            update(Seat.EAST,suit=Suit.DIAMONDS,low=3,high=3)), 740, None),
        ("shape_alternatives", (AuctionConstraintUpdate(Seat.NORTH,shapes=ShapeEvidence(
            alternatives,Certainty.GUARANTEED,SOURCE)),), 742, None),
        ("tight_three_seat_evidence", (
            update(Seat.NORTH,suit=Suit.SPADES,low=4,high=5),update(Seat.NORTH,low=10,high=12),
            update(Seat.WEST,suit=Suit.DIAMONDS,low=5,high=6),update(Seat.WEST,low=9,high=13),
            update(Seat.EAST,suit=Suit.CLUBS,low=4,high=6),update(Seat.EAST,low=6,high=10)),743,None),
        ("rare_partner_all_remaining_spades", (update(Seat.NORTH,suit=Suit.SPADES,low=8,high=8),),741,
         lambda s,h:s==8),
    ]
    rows=[]
    for name, updates, seed, predicate in cases:
        s=base.with_updates(updates)
        start=perf_counter()
        sampler=ConditionalSampler(s)
        setup_seconds=perf_counter()-start
        start=perf_counter()
        result=sampler.sample(SamplingConfig(samples,max_proposals,seed+10000))
        sampling_seconds=perf_counter()-start
        start=perf_counter()
        reference=sample_hidden_hands(s,SamplingConfig(samples,
                                     min(max_proposals,20000) if name.startswith("rare") else max_proposals,seed))
        reference_seconds=perf_counter()-start
        exacts=_partner_exact(joint,predicate) if predicate else {}
        if name=="unconstrained":
            for seat in (Seat.NORTH,Seat.WEST,Seat.EAST):
                exacts[seat,Feature.HCP]=exacts[Seat.NORTH,Feature.HCP]
                for suit,feature in ((Suit.SPADES,Feature.SPADES),(Suit.HEARTS,Feature.HEARTS),
                                     (Suit.DIAMONDS,Feature.DIAMONDS),(Suit.CLUBS,Feature.CLUBS)):
                    outstanding=13-OWN.length(suit)
                    exacts[seat,feature]={k:Fraction(comb(outstanding,k)*comb(39-outstanding,13-k),comb(39,13))
                                          for k in range(outstanding+1)}
        if name=="defender_diamonds_5_3":
            v=vacant_place_reference(s,Suit.SPADES,4,defender_side_suit=Suit.DIAMONDS)
            exacts[Seat.WEST,Feature.SPADES]={item.first_trumps:item.probability.as_fraction() for item in v}
            exacts[Seat.EAST,Feature.SPADES]={item.second_trumps:item.probability.as_fraction() for item in v}
        if name=="shape_alternatives":
            masses={}
            for shape in alternatives:
                n=1
                for suit,count in zip((Suit.SPADES,Suit.HEARTS,Suit.DIAMONDS,Suit.CLUBS),shape):
                    n*=comb(13-OWN.length(suit),count)
                masses[shape]=n
            exacts[Seat.NORTH,Feature.SHAPE]={key:Fraction(n,sum(masses.values())) for key,n in masses.items()}
        comparisons,metrics=_compare(result.model,reference,exacts)
        row={"scenario":name,"setup_seconds":setup_seconds,"sampling_and_summary_seconds":sampling_seconds,
             "conditional_total_seconds":setup_seconds+sampling_seconds,
             "conditional_proposals_per_second":result.model.proposals/sampling_seconds,
             "conditional_accepted_per_second":result.model.accepted/sampling_seconds,
             "reference_total_seconds":reference_seconds,
             "reference_proposals_per_second":reference.proposals/reference_seconds,
             "reference_accepted_per_second":reference.accepted/reference_seconds,
             "conditional":_diagnostics(result.model),"reference":_diagnostics(reference),
             "matrix_count":sampler.diagnostics.matrix_count,
             "proposal_allocation_count":sampler.diagnostics.proposal_allocation_count,
             "primary_hcp_seat":sampler.diagnostics.primary_hcp_seat.value,
             "residual_hcp_seats":[seat.value for seat in sampler.diagnostics.residual_hcp_seats],
             "marginal_comparisons":comparisons,"marginal_metrics":metrics}
        rows.append(row)
        print(name,"conditional",result.model.accepted,"/",result.model.proposals,
              "reference",reference.accepted,"/",reference.proposals,flush=True)
    # Separate memory pass: tracing overhead is excluded from the timing table.
    tracemalloc.start()
    memory_sampler=ConditionalSampler(base)
    current,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert memory_sampler.diagnostics.matrix_count==rows[0]["matrix_count"]
    return {"target":"uniform physical assignments satisfying all hard PT-A0 evidence",
            "algorithm":"exact-shape-primary-hcp-conditional-v1","scenarios":rows,
            "setup_memory":{"scenario":"unconstrained","retained_python_bytes":current,"peak_python_bytes":peak},
            "statistical_note":"Independent seeded draws; exact-bin SE uses sqrt(p(1-p)/N). "
             "Reference differences use pooled two-sample binomial SE. Shape metrics use all bins; "
             "only five representative shape bins are stored individually. Rare-bin normal SE and "
             "multiple-bin extrema are descriptive, not a global equivalence test."}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--samples",type=int,default=4000)
    parser.add_argument("--max-proposals",type=int,default=200000)
    parser.add_argument("--output",type=Path,default=Path("output/pta1b_conditional/summary.json"))
    args=parser.parse_args()
    payload=run(args.samples,args.max_proposals)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
