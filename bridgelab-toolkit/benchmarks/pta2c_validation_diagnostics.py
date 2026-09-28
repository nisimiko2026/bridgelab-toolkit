"""PT-A2C validation-only defender and collateral-shortness diagnostics."""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import replace
import gzip,json
from pathlib import Path
from statistics import mean,median,pstdev
from time import perf_counter

from bridge.deals import Deal
from bridge.models import Hand,Rank,Seat,Suit
from bridge.counterfactual_calibration import diagnose
from bridge.expected_ruffing_research import ResearchSolverSession,jsonable
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.shortness_target_redesign import (
    TargetConfig,MatchingPriority,TargetKind,reference_support,structural_controls,
    fixed_feature_errors,matching_distance,evaluate_target_candidates,
)
from benchmarks.pta2c_target_validation import hydrate,cases,compact,paired_metrics


def defender_spot_variants(control,perspective,trump):
    """Same-suit E/W-or-N/S spot swaps; all partnership cards and all shapes fixed."""
    defenders=tuple(s for s in Seat if s not in (perspective,perspective.partner()))
    a,b=defenders
    results={control.serialize():control}
    for suit in Suit:
        if suit is trump:continue
        for x in sorted(c for c in control.hand(a).cards_in(suit) if c.rank<Rank.JACK):
            for y in sorted(c for c in control.hand(b).cards_in(suit) if c.rank<Rank.JACK):
                mapping=control.mapping
                mapping[a]=Hand.from_cards(mapping[a].cards-{x}|{y})
                mapping[b]=Hand.from_cards(mapping[b].cards-{y}|{x})
                result=Deal(0,tuple((s,mapping[s]) for s in Seat))
                assert all(result.hand(s).shape==control.hand(s).shape for s in Seat)
                assert all(result.hand(s)==control.hand(s) for s in (perspective,perspective.partner()))
                results[result.serialize()]=result
    return tuple(results[k] for k in sorted(results))


def shortness_changes(source,control,perspective,studied,trump):
    changes=[]
    for seat in Seat:
        for suit in Suit:
            if suit is trump or (seat is perspective and suit is studied):continue
            before,after=source.hand(seat).length(suit),control.hand(seat).length(suit)
            if min(before,2)!=min(after,2):
                changes.append({"seat":seat.value,"suit":suit.letter,"before":before,"after":after,
                                "own":seat is perspective})
    return changes


def distribution(values):
    return {"n":len(values),"mean":mean(values) if values else None,"median":median(values) if values else None,
        "minimum":min(values) if values else None,"maximum":max(values) if values else None,
        "sd":pstdev(values) if values else None,"histogram":dict(Counter(map(str,values)))}


def run(root=Path("output/pta2c_targets"),budget=2000):
    output=root/"diagnostics"
    if (output/"summary.json").exists():raise ValueError("completed diagnostics already exist")
    output.mkdir(parents=True,exist_ok=True)
    pilot=json.loads((root/"pilot/summary.json").read_text(encoding="utf-8"))
    config=TargetConfig(**{**pilot["configuration"],"priority":MatchingPriority(pilot["configuration"]["priority"])})
    raw=[]
    with gzip.open(root/"pilot/comparisons.jsonl.gz","rt",encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            if "experimental_expectation" not in row:raw.append(row)
    session=ResearchSolverSession(EndplayTrickSolver(),max_calls=budget)
    for row in raw:
        for data in [row["source_solver"],*row["exchange"]["solver_records"],*[r for c in row["candidates"] for r in c["control_results"]]]:
            result=hydrate(data)
            session.cache[result.deal_id,result.declarer,result.strain]=result
    preloaded=len(session.cache)
    started=perf_counter()
    stress=[]
    for label,cohort,source,p,studied,trump,declarer in cases(1,0,0):
        if cohort!="structural_stress":continue
        support=reference_support(source,p,studied,trump)
        controls,reasons=structural_controls(source,p,studied,trump)
        stress.append({"hand":source.hand(p).serialize(),"source":source.serialize(),
            "A_exclusions":[r.value for r in diagnose(source,p,studied,trump).reasons],
            "B_exclusions":[r.value for r in reasons],"C_exclusions":[r.value for r in support.exclusions],
            "D_exclusions":[r.value for r in support.exclusions]})
        # Measure newly added compensation-floor stress case only, retain pilot others.
        if source.hand(p).serialize()=="AKQJ9876.543.-.T2":
            result=evaluate_target_candidates(source,p,studied,trump,declarer,session,config=config)
            raw.append(jsonable(result))
            (output/"collateral_stress_case.json").write_text(json.dumps(jsonable(result),indent=2)+"\n",encoding="utf-8")
    (root/"impossible_reference_census.json").write_text(json.dumps({
        "dds_calls_for_classification":0,"cases":stress,
        "exclusion_counts":{k:sum(bool(r[k+"_exclusions"]) for r in stress) for k in "ABCD"}},indent=2)+"\n",encoding="utf-8")
    # First three complete singleton and void sources, selected before DDS variation.
    selected=[]
    for kind in ("singleton","void"):
        selected.extend([r for r in raw if dict(r["features"])["shortness"]==kind
                         and all(not c["exclusions"] for c in r["candidates"])][:3])
    defender_rows=[]
    for row in selected:
        source=Deal.parse(row["source_deal_id"])
        perspective,studied,trump,declarer=Seat(row["perspective"]),Suit(row["studied_suit"]),Suit(row["trump"]),Seat(row["declarer"])
        for candidate in row["candidates"]:
            if candidate["target"]==TargetKind.STRUCTURAL.value:continue
            base_record=candidate["control_results"][0]
            base=Deal.parse(base_record["deal_id"])
            variants=defender_spot_variants(base,perspective,trump)
            # All one-swap variants, no arbitrary chosen DDS-favorable subset.
            values=[]
            for variant in variants:
                assert not fixed_feature_errors(source,variant,perspective,studied,trump)
                assert matching_distance(source,variant,perspective,studied,trump,priority=config.priority)==matching_distance(
                    source,base,perspective,studied,trump,priority=config.priority)
                result=session.solve(variant,declarer,trump)
                assert result.maximum_declarer_tricks is not None
                values.append({"control":variant.serialize(),"tricks":result.maximum_declarer_tricks,
                               "delta":row["source_solver"]["maximum_declarer_tricks"]-result.maximum_declarer_tricks})
            deltas=[v["delta"] for v in values]
            count=candidate["control_count"]
            original=row["source_solver"]["maximum_declarer_tricks"]-base_record["maximum_declarer_tricks"]
            defender_rows.append({"source":row["source_deal_id"],"shortness":dict(row["features"])["shortness"],
                "target":candidate["target"],"matching_distance":candidate["distances"][0],"variants":values,
                "delta_distribution":distribution(deltas),"delta_spread":max(deltas)-min(deltas),
                "original_target":candidate["delta"],"original_first_control_delta":original,
                "one_control_replacement_target_range":[candidate["delta"]+(min(deltas)-original)/count,
                                                        candidate["delta"]+(max(deltas)-original)/count],
                "control_count":count})
    collateral=defaultdict(list)
    within_source=[]
    for row in raw:
        source=Deal.parse(row["source_deal_id"])
        p,s,t=Seat(row["perspective"]),Suit(row["studied_suit"]),Suit(row["trump"])
        for candidate in row["candidates"]:
            if candidate["exclusions"]:continue
            local=[]
            for record in candidate["control_results"]:
                control=Deal.parse(record["deal_id"])
                changes=shortness_changes(source,control,p,s,t)
                datum={"source":row["source_deal_id"],"delta":row["source_solver"]["maximum_declarer_tricks"]-record["maximum_declarer_tricks"],
                       "own_collateral":any(c["own"] for c in changes),"any_collateral":bool(changes),"changes":changes}
                collateral[candidate["target"]].append(datum)
                local.append(datum)
            for scope in ("own_collateral","any_collateral"):
                changed=[v["delta"] for v in local if v[scope]]
                unchanged=[v["delta"] for v in local if not v[scope]]
                if changed and unchanged:
                    within_source.append({"source":row["source_deal_id"],"target":candidate["target"],"scope":scope,
                        "changed_mean_minus_unchanged":mean(changed)-mean(unchanged),
                        "changed_n":len(changed),"unchanged_n":len(unchanged)})
    collateral_summary={}
    for target,rows in collateral.items():
        collateral_summary[target]={"controls":len(rows)}
        for scope in ("own_collateral","any_collateral"):
            changed=[r["delta"] for r in rows if r[scope]]
            unchanged=[r["delta"] for r in rows if not r[scope]]
            collateral_summary[target][scope]={"changed":len(changed),"fraction":len(changed)/len(rows),
                "changed_effect_distribution":distribution(changed),"unchanged_effect_distribution":distribution(unchanged)}
    with gzip.open(output/"collateral_controls.jsonl.gz","wt",encoding="utf-8") as stream:
        for target,rows in collateral.items():
            for row in rows:stream.write(json.dumps({"target":target,**row})+"\n")
    summary={"defender_variation":defender_rows,
        "defender_variation_summary":{target:{
            "sources":len(rows),"nonzero_spread":sum(r["delta_spread"]>0 for r in rows),
            "mean_spread":mean(r["delta_spread"] for r in rows),"max_spread":max(r["delta_spread"] for r in rows)}
            for target in (TargetKind.MATCHED.value,TargetKind.BASELINE.value)
            if (rows:=[r for r in defender_rows if r["target"]==target])},
        "collateral_summary":collateral_summary,"within_source_collateral_comparisons":within_source,
        "limitations":[
            "Controlled perturbation of one selected control inside the SAME conditional/matching stratum; not a fresh random control sample or a causal effect estimate.",
            "C distances and hard features stay fixed. Its finite candidate realization changes; the sampled-pool algorithm is not claimed to have reselected this neighborhood.",
            "For D all variants remain in the same reference support. Population expectation is unchanged; displayed ranges concern finite-control realizations.",
            "Only C/D receive this conditional defender-neighborhood diagnostic. B's selected minimum-relocation policy is held fixed; no general defender-invariance claim is made for B.",
            "Collateral subgroup differences are descriptive and confounded by other permissible card/shape changes; not an isolated causal shortness effect."],
        "runtime":{"new_dds_calls":session.calls,"cache_hits":session.cache_hits,"preloaded_entries":preloaded,
                   "dds_failures":session.failures,"wall_seconds":perf_counter()-started,"budget":budget}}
    (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    p=run()
    print(p["runtime"])
    print(p["defender_variation_summary"])
    print(p["collateral_summary"])