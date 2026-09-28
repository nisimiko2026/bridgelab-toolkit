"""PT-A2B bounded coverage census and matched-target DDS calibration."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import gzip
import json
from math import sqrt
from pathlib import Path
from statistics import mean, pvariance
from time import perf_counter

from bridge.counterfactual_calibration import (
    ControlFamily, diagnose, pre_control_features, evaluate_controls, estimate_multicontrol,
)
from bridge.deals import Deal
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.expected_ruffing_research import ERVConfig, ResearchSolverSession, SEATS, jsonable
from bridge.hidden_hand_probability import SamplingConfig
from bridge.conditional_hidden_hand import ConditionalSampler
from bridge.models import Seat, Suit
from benchmarks.pta2_erv_validation import (
    information_states, OWN_SINGLETON, OWN_VOID, collapse_state, calibration_summary, prediction_band,
)


def coverage_census(source, output):
    started=perf_counter()
    rows=[]
    with gzip.open(source,"rt",encoding="utf-8") as stream:
        for index,line in enumerate(stream):
            record=json.loads(line)
            if index>=10:
                break
            label=("singleton" if index<5 else "void")+"_"+(
                "unknown_fit","support_ge3","support_ge4","support_eq4","defender_diamonds_5_3")[index%5]
            for effect in record["effects"]:
                deal=Deal.parse(effect["source_deal_id"])
                d=diagnose(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
                assert d.evaluable==(effect["status"]=="evaluable")
                if d.evaluable:
                    multiplicity=1 if index<5 else 4
                    assert d.minimal_unique_controls*multiplicity==effect["candidate_count"]
                features=pre_control_features(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
                rows.append({"state":label,"evaluable":d.evaluable,"reasons":[r.value for r in d.reasons],
                             "diagnosis":jsonable(d),"features":features})
    strata={}
    for key in ("state","shortness","trump_structure","studied_suit","trump_role","ruffable_loser_proxy"):
        groups=defaultdict(list)
        for row in rows:
            value=row["state"] if key=="state" else row["features"][key]
            groups[str(value)].append(row)
        strata[key]={}
        for label,group in sorted(groups.items()):
            missing=[r for r in group if not r["evaluable"]]
            strata[key][label]={"total":len(group),"evaluable":len(group)-len(missing),
                "missing":len(missing),"missing_rate":len(missing)/len(group),
                "primary_reasons":dict(Counter(r["reasons"][0] for r in missing)),
                "all_reasons_nonexclusive":dict(Counter(reason for r in missing for reason in r["reasons"]))}
    differences={}
    for label,group in [("all",rows)]+[(name,[r for r in rows if r["state"]==name]) for name in strata["state"]]:
        valid=[r["features"] for r in group if r["evaluable"]]
        missing=[r["features"] for r in group if not r["evaluable"]]
        numeric={}
        categorical={}
        if valid and missing:
            for key in valid[0]:
                if isinstance(valid[0][key],(int,float)):
                    a,b=[r[key] for r in valid],[r[key] for r in missing]
                    scale=sqrt((pvariance(a)+pvariance(b))/2)
                    numeric[key]={"evaluable_mean":mean(a),"missing_mean":mean(b),
                        "missing_minus_evaluable":mean(b)-mean(a),
                        "standardized_difference":(mean(b)-mean(a))/scale if scale else None,
                        "evaluable_n":len(a),"missing_n":len(b)}
                else:
                    a,b=Counter(r[key] for r in valid),Counter(r[key] for r in missing)
                    categorical[key]={"evaluable_counts":dict(a),"missing_counts":dict(b),
                        "total_variation":sum(abs(a[x]/len(valid)-b[x]/len(missing)) for x in a.keys()|b.keys())/2}
        differences[label]={"numeric":numeric,"categorical":categorical}
    payload={"hypotheses":len(rows),"original_evaluable":sum(r["evaluable"] for r in rows),
        "expanded_evaluable":sum(r["evaluable"] for r in rows),"incremental_coverage":0,
        "strata":strata,"pre_control_differences":differences,"wall_seconds":perf_counter()-started,
        "dds_calls":0,
        "proof":"Required studied spots, partner terminal length >=2, and summed own removable side spots are necessary and sufficient under fixed honors/trumps/defenders and own side-length floors. Nonminimal same-suit transpositions cannot repair their violation.",
        "missingness_conclusion":"Structural deterministic selection. Not a missing-at-random assertion."}
    output.mkdir(parents=True,exist_ok=True)
    (output/"coverage.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload


def target_value(effect, name):
    if not effect.evaluable:
        return None
    return {"pta2_selected":effect.pta2_selected_delta,"first_valid":effect.first_valid_delta,
            "uniform_controls":effect.distribution.mean,"median_controls":effect.distribution.median}[name]


def run(output, *, samples=24, holdout=8, control_limit=8, budget=12000):
    if (output/"summary.json").exists():
        raise ValueError("fresh output required; do not overwrite measurements")
    output.mkdir(parents=True,exist_ok=True)
    session=ResearchSolverSession(EndplayTrickSolver(),max_calls=budget)
    started=perf_counter()
    state_rows=[]
    records=[]
    costs=[]
    artifacts=output/"effects.jsonl.gz"
    with gzip.open(artifacts,"wt",encoding="utf-8") as details:
        for hand_index,own in enumerate((OWN_SINGLETON,OWN_VOID)):
            for index,(name,state) in enumerate(information_states(own)):
                label=("singleton" if hand_index==0 else "void")+"_"+name
                holdouts=ConditionalSampler(state).sample(SamplingConfig(holdout,200000,94000+100*hand_index+index)).model
                for family in ControlFamily:
                    before=session.calls
                    time=perf_counter()
                    cfg=ERVConfig(SamplingConfig(samples,200000,93000+100*hand_index+index),3202,
                                  (("implementation","endplay/DDS"),("version","0.5.12")))
                    prediction=estimate_multicontrol(state,Suit.DIAMONDS,Suit.SPADES,session,
                        config=cfg,family=family,control_limit=control_limit)
                    compact=jsonable(prediction)
                    del compact["effects"],compact["weights"]
                    state_rows.append({"state":label,"family":family.value,"prediction":compact})
                    details.write(json.dumps({"kind":"prediction","state":label,"result":jsonable(prediction)})+"\n")
                    outcomes=list(prediction.effects)
                    for h in holdouts.samples:
                        mapping=dict(h.hands)
                        mapping[state.perspective]=state.own_hand
                        deal=Deal(0,tuple((seat,mapping[seat]) for seat in SEATS))
                        target=evaluate_controls(deal,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,
                            session,family=family,control_limit=control_limit)
                        outcomes.append(target)
                        details.write(json.dumps({"kind":"holdout","state":label,"result":jsonable(target)})+"\n")
                        for target_name,stats in prediction.targets:
                            records.append({"state":label,"family":family.value,"target":target_name,
                                "predicted":stats["mean"],"realized":target_value(target,target_name),
                                "prediction_se":stats["se"],"fingerprint":prediction.fingerprint,
                                "predicted_band":prediction_band(stats["mean"]) if stats["mean"] is not None else "unavailable",
                                "shortness":dict(target.features)["shortness"],
                                "target_missing_reasons":[r.value for r in target.failure_reasons]})
                    valid=[e for e in outcomes if e.evaluable]
                    costs.append({"state":label,"family":family.value,"hypotheses":len(outcomes),
                        "evaluable":len(valid),"controls_enumerated_total":sum(e.legal_controls for e in outcomes),
                        "controls_enumerated_max":max(e.legal_controls for e in outcomes),
                        "controls_selected_total":sum(e.selected_controls for e in outcomes),
                        "exhaustive_sources":sum(e.exhaustive for e in valid),
                        "nonzero_spread_sources":sum(e.distribution.spread>0 for e in valid),
                        "mean_spread":mean(e.distribution.spread for e in valid) if valid else None,
                        "max_spread":max((e.distribution.spread for e in valid),default=None),
                        "dds_calls":session.calls-before,"wall_seconds":perf_counter()-time})
                    details.flush()
                    print(label,family.value,"valid",prediction.evaluable,"calls",session.calls,"elapsed",round(perf_counter()-started,2),flush=True)
                    if session.calls>=budget:
                        raise RuntimeError("DDS budget exhausted; detailed partial measurements retained")
        collapses=[]
        for void in (False,True):
            state=collapse_state(void)
            for family in ControlFamily:
                result=estimate_multicontrol(state,Suit.DIAMONDS,Suit.SPADES,session,
                    config=ERVConfig(SamplingConfig(2,2,72000),3202),family=family,control_limit=10000)
                assert len({x.source_deal_id for x in result.effects})==1
                first=result.effects[0]
                assert first.pta2_selected_delta==(2 if void else 1)
                collapses.append({"shortness":"void" if void else "singleton","family":family.value,
                    "target":jsonable(first),"prediction_targets":jsonable(result.targets)})
        # Real DDS isolation: source worlds never enter estimate_multicontrol.
        leakage_worlds=json.loads(Path("output/pta2_erv/main/leakage.json").read_text())["source_worlds"]
        states=[dict(information_states(Deal.parse(w).hand(Seat.SOUTH)))["unknown_fit"] for w in leakage_worlds]
        cfg=ERVConfig(SamplingConfig(4,200000,95000),3202)
        estimates=[estimate_multicontrol(s,Suit.DIAMONDS,Suit.SPADES,session,config=cfg,control_limit=control_limit) for s in states]
        assert estimates[0]==estimates[1]
        leakage={"identical_results":True,"source_worlds":leakage_worlds,
                 "fingerprint":estimates[0].fingerprint,"targets":jsonable(estimates[0].targets)}
    grouped={}
    for field in ("all","shortness","state","predicted_band"):
        groups=defaultdict(list)
        for row in records:
            group="all" if field=="all" else str(row[field])
            groups[(row["family"],row["target"],group)].append(row)
        grouped[field]=[{"family":f,"target":t,"group":g,"statistics":calibration_summary(rows)}
                        for (f,t,g),rows in sorted(groups.items())]
    ranking={}
    for family in ControlFamily:
        selected=[r for r in state_rows if r["family"]==family.value]
        for target_name in ("pta2_selected","first_valid","uniform_controls","median_controls"):
            ranking[family.value+"/"+target_name]=[r["state"] for r in sorted(selected,
                key=lambda row:(dict(row["prediction"]["targets"])[target_name]["mean"] is None,
                    dict(row["prediction"]["targets"])[target_name]["mean"] or 0))]
    payload={"status":"complete","samples_per_state":samples,"holdouts_per_state":holdout,
             "control_limit":control_limit,"states":state_rows,"calibration_records":records,
             "calibration":grouped,"rankings":ranking,"costs":costs,"collapse":collapses,"leakage":leakage,
             "runtime":{"dds_calls":session.calls,"dds_failures":session.failures,"cache_hits":session.cache_hits,
                        "dds_seconds":session.wall_seconds,"wall_seconds":perf_counter()-started,"budget":budget},
             "target_note":"Distinct physical terminal controls. Fixed hash subset approximates uniform mean and median when capped. PT-A2 reference is seeded path selection; first-valid is a separate lexicographic comparator.",
             "bounds_note":"Hypothetical empirical completion only; absent controls leave the full target undefined."}
    (output/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload


def finalize_comparisons(output):
    """Add transparent paired summaries from saved measurements; zero DDS calls."""
    path=output/"summary.json"
    payload=json.loads(path.read_text())
    records=payload["calibration_records"]
    reference={(row["family"],row["state"]):row["predicted"] for row in records if row["target"]=="pta2_selected"}
    by_reference_band=defaultdict(list)
    for row in records:
        p=reference[row["family"],row["state"]]
        band=prediction_band(p) if p is not None else "unavailable"
        by_reference_band[row["family"],row["target"],band].append(row)
    payload["calibration_fixed_reference_bands"]=[
        {"family":f,"target":t,"reference_band":b,"statistics":calibration_summary(rows)}
        for (f,t,b),rows in sorted(by_reference_band.items())]
    comparisons=[]
    for field in ("all","shortness","state","predicted_band"):
        rows=payload["calibration"][field]
        refs={(r["family"],r["group"]):r["statistics"] for r in rows if r["target"]=="pta2_selected"}
        for row in rows:
            ref=refs.get((row["family"],row["group"]))
            value=row["statistics"]
            if not ref or not ref.get("n") or not value.get("n"):
                continue
            comparisons.append({"stratum":field,"family":row["family"],"target":row["target"],
                "group":row["group"],"reference_n":ref["n"],"target_n":value["n"],
                **{key+"_shift":value[key]-ref[key] for key in
                   ("mean_predicted","mean_realized","prediction_minus_realization","rmse","mae")},
                "note":"Target-specific bands can change membership; fixed_reference_bands is the matched-band comparison."})
    payload["comparison_to_pta2_reference"]=comparisons
    groups=defaultdict(list)
    witnesses=[]
    with gzip.open(output/"effects.jsonl.gz","rt",encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            effects=row["result"]["effects"] if row["kind"]=="prediction" else [row["result"]]
            for e in effects:
                if not e["failure_reasons"]:
                    groups[e["family"]].append(e)
                if len(witnesses)>=3:
                    continue
                solved=[r for r in e["solver_records"] if r["status"]=="success"]
                for i,a in enumerate(solved):
                    for b in solved[i+1:]:
                        if a["maximum_declarer_tricks"]==b["maximum_declarer_tricks"]:
                            continue
                        da,db=Deal.parse(a["deal_id"]),Deal.parse(b["deal_id"])
                        left=da.hand(Seat.SOUTH).cards-db.hand(Seat.SOUTH).cards
                        right=db.hand(Seat.SOUTH).cards-da.hand(Seat.SOUTH).cards
                        if len(left)!=1 or len(right)!=1:
                            continue
                        x,y=next(iter(left)),next(iter(right))
                        if x.suit is not y.suit or x.suit is Suit.SPADES or max(int(x.rank),int(y.rank))>=11:
                            continue
                        if any(da.hand(seat)!=db.hand(seat) for seat in (Seat.EAST,Seat.WEST)):
                            continue
                        witnesses.append({"state":row["state"],"control_a":a["deal_id"],"control_b":b["deal_id"],
                            "tricks_a":a["maximum_declarer_tricks"],"tricks_b":b["maximum_declarer_tricks"],
                            "swapped_spots":[x.serialize(),y.serialize()],
                            "interpretation":"Physical spot ranks are not irrelevant labels; this legal same-suit ownership swap changes DDS."})
                        break
                    if len(witnesses)>=3:
                        break
    payload["spot_rank_counterexamples"]=witnesses
    payload["ambiguity_by_family"]={}
    for family,effects in groups.items():
        payload["ambiguity_by_family"][family]={
            "evaluable_occurrences":len(effects),
            "nonzero_spread":sum(e["distribution"]["spread"]>0 for e in effects),
            "fraction_nonzero_spread":mean(e["distribution"]["spread"]>0 for e in effects),
            "mean_spread":mean(e["distribution"]["spread"] for e in effects),
            "max_observed_spread":max(e["distribution"]["spread"] for e in effects),
            "mean_within_control_sd":mean(e["distribution"]["standard_deviation"] for e in effects),
            "mean_uniform_minus_selected":mean(e["distribution"]["mean"]-e["pta2_selected_delta"] for e in effects),
            "max_absolute_uniform_minus_selected":max(abs(e["distribution"]["mean"]-e["pta2_selected_delta"]) for e in effects),
            "exhaustive":sum(e["exhaustive"] for e in effects)}
    prediction_lookup={(r["family"],r["state"]):dict(r["prediction"]["targets"]) for r in payload["states"]}
    changes=[]
    for family in ControlFamily:
        names=sorted(s for f,s in prediction_lookup if f==family.value)
        for i,a in enumerate(names):
            for b in names[i+1:]:
                x,y=prediction_lookup[family.value,a],prediction_lookup[family.value,b]
                if all(v["mean"] is not None for v in (x["pta2_selected"],y["pta2_selected"],x["uniform_controls"],y["uniform_controls"])):
                    old=x["pta2_selected"]["mean"]-y["pta2_selected"]["mean"]
                    new=x["uniform_controls"]["mean"]-y["uniform_controls"]["mean"]
                    if old*new<0:
                        changes.append({"family":family.value,"state_a":a,"state_b":b,
                                        "reference_difference":old,"uniform_difference":new})
    payload["strict_ranking_reversals"]=changes
    payload["missing_delta_scenarios"]=[
        {"state":r["state"],"family":r["family"],"scenarios":[
            {"assumed_missing_delta":v,"hypothetical_empirical_mean":
             r["prediction"]["coverage"]*dict(r["prediction"]["targets"])["uniform_controls"]["mean"]+
             (1-r["prediction"]["coverage"])*v} for v in (-2,-1,0,1,2)]}
        for r in payload["states"] if dict(r["prediction"]["targets"])["uniform_controls"]["mean"] is not None]
    payload["comparison_finalization"]={"additional_dds_calls":0,
        "warning":"Bounded-control approximation, Monte Carlo error, model ambiguity and missing coverage remain separate."}
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload


def validate_control_cap(output, budget=1000):
    """Small exhaustive comparison of the deterministic bounded control target."""
    selected={}
    with gzip.open(output/"effects.jsonl.gz","rt",encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            effects=row["result"]["effects"] if row["kind"]=="prediction" else [row["result"]]
            for e in effects:
                kind=dict(e["features"])["shortness"]
                key=(e["family"],kind)
                if key not in selected and not e["failure_reasons"] and 8<e["legal_controls"]<=150:
                    selected[key]=e
    session=ResearchSolverSession(EndplayTrickSolver(),max_calls=budget)
    started=perf_counter()
    rows=[]
    for (family,kind),original in sorted(selected.items()):
        source=Deal.parse(original["source_deal_id"])
        values=[]
        for limit in (8,16,32,original["legal_controls"]):
            e=evaluate_controls(source,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,session,
                family=ControlFamily(family),control_limit=limit)
            assert e.evaluable
            if limit==8:
                assert e.control_results==tuple(tuple(x) for x in original["control_results"])
            values.append({"cap":limit,"distribution":jsonable(e.distribution),"exhaustive":e.exhaustive})
        exact=values[-1]["distribution"]
        for value in values:
            value["mean_error_vs_exhaustive"]=value["distribution"]["mean"]-exact["mean"]
            value["median_error_vs_exhaustive"]=value["distribution"]["median"]-exact["median"]
        rows.append({"family":family,"shortness":kind,"source_deal_id":source.serialize(),
                     "legal_controls":original["legal_controls"],"comparisons":values})
    result={"rows":rows,"dds_calls":session.calls,"dds_failures":session.failures,
            "wall_seconds":perf_counter()-started,"budget":budget,
            "selection":"First source in each family/shortness cell with 9..150 legal controls; deliberately bounded, not representative."}
    (output/"control_cap_validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--samples",type=int,default=24)
    parser.add_argument("--holdout",type=int,default=8)
    parser.add_argument("--control-limit",type=int,default=8)
    parser.add_argument("--budget",type=int,default=12000)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument("--census-only",action="store_true")
    modes.add_argument("--finalize-only",action="store_true")
    modes.add_argument("--cap-validation",action="store_true")
    args=parser.parse_args()
    if args.finalize_only:
        result=finalize_comparisons(args.output)
        print(result["comparison_finalization"])
    elif args.cap_validation:
        result=validate_control_cap(args.output)
        print(result)
    elif args.census_only:
        result=coverage_census(Path("output/pta2_erv/main/hypotheses.jsonl.gz"),args.output)
        print("Census",result["hypotheses"],result["original_evaluable"],"seconds",result["wall_seconds"])
    else:
        result=run(args.output,samples=args.samples,holdout=args.holdout,control_limit=args.control_limit,budget=args.budget)
        print(result["runtime"])