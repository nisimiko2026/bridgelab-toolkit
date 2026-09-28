"""Bounded PT-A2C redesign comparisons, cached DDS and explicit target diagnostics."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import replace
import gzip
import json
from pathlib import Path
from statistics import mean, median
from time import perf_counter
import random

from bridge.counterfactual_calibration import diagnose
from bridge.deals import Deal, full_deck, generate_deal
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.expected_ruffing_research import ERVConfig, ResearchSolverSession, jsonable
from bridge.hidden_hand_probability import SamplingConfig
from bridge.models import Hand, Seat, Suit, Rank
from bridge.shortness_target_redesign import (
    TargetConfig, TargetKind, MatchingPriority, reference_support, evaluate_target_candidates,
    compare_candidate_expectations,
)
from bridge.trick_solver import TrickSolverResult, TrickSolverStatus
from benchmarks.pta2_erv_validation import information_states, collapse_state, OWN_SINGLETON, OWN_VOID


def hydrate(row):
    assert row["implementation"]=="endplay/DDS" and row["version"]=="0.5.12"
    assert row["opening_lead"] is None and row["status"]=="success"
    Deal.parse(row["deal_id"])
    return TrickSolverResult(row["implementation"],row["version"],row["deal_id"],Seat(row["declarer"]),
        Suit(row["strain"]),None,TrickSolverStatus.SUCCESS,row["maximum_declarer_tricks"],0.0)


def preload(session):
    before=len(session.cache)
    with gzip.open("output/pta2b_controls/main/effects.jsonl.gz","rt",encoding="utf-8") as stream:
        for line in stream:
            item=json.loads(line)
            effects=item["result"]["effects"] if item["kind"]=="prediction" else (item["result"],)
            for e in effects:
                for row in ([e["source_solver"]] if e["source_solver"] else [])+e["solver_records"]:
                    r=hydrate(row)
                    key=(r.deal_id,r.declarer,r.strain)
                    if key in session.cache:
                        assert session.cache[key]==r
                    session.cache[key]=r
    return len(session.cache)-before


def ranks(values):
    order=sorted(range(len(values)),key=values.__getitem__)
    result=[0.0]*len(values)
    i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]: j+=1
        for k in order[i:j]: result[k]=(i+j-1)/2
        i=j
    return result


def correlation(a,b):
    if len(a)<2: return None
    x,y=mean(a),mean(b)
    numerator=sum((v-x)*(w-y) for v,w in zip(a,b))
    denominator=(sum((v-x)**2 for v in a)*sum((w-y)**2 for w in b))**0.5
    return numerator/denominator if denominator else None


def paired_metrics(a,b):
    pairs=[(x,y) for x,y in zip(a,b) if x is not None and y is not None]
    if not pairs:return {"n":0}
    a,b=map(list,zip(*pairs))
    differences=[x-y for x,y in pairs]
    sign=lambda x:(x>0)-(x<0)
    return {"n":len(pairs),"mean_difference":mean(differences),"median_difference":median(differences),
        "pearson":correlation(a,b),"spearman":correlation(ranks(a),ranks(b)),
        "sign_disagreements":sum(sign(x)!=sign(y) for x,y in pairs),
        "large_disagreements_ge_1_5":sum(abs(x-y)>=1.5 for x,y in pairs)}


def census(output):
    rows=[]
    with gzip.open("output/pta2_erv/main/hypotheses.jsonl.gz","rt",encoding="utf-8") as stream:
        for index,line in enumerate(stream):
            if index>=10:break
            record=json.loads(line)
            for effect in record["effects"]:
                d=Deal.parse(effect["source_deal_id"])
                support=reference_support(d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES)
                own=d.hand(Seat.SOUTH)
                capacity=sum(min(max(own.length(s)-2,0),sum(c.rank<Rank.JACK for c in own.cards_in(s)))
                    for s in Suit if s not in (Suit.SPADES,Suit.DIAMONDS))
                rows.append({"kind":"singleton" if index<5 else "void","state_index":index%5,
                    "A":effect["status"]=="evaluable","B":not support.exclusions and capacity>=2-own.length(Suit.DIAMONDS),
                    "C":not support.exclusions,"D":not support.exclusions})
    summary={"n":len(rows),"coverage":{k:sum(r[k] for r in rows)/len(rows) for k in "ABCD"},
        "by_shortness":{kind:{k:sum(r[k] for r in rows if r["kind"]==kind)/sum(r["kind"]==kind for r in rows) for k in "ABCD"} for kind in ("singleton","void")},
        "warning":"Different targets/invariants, not recovered exchange outcomes. Fixed-card-capacity exclusions persist outside these two visible hands.",
        "dds_calls":0}
    (output/"coverage.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def cases(per_state, external, diverse):
    result=[]
    with gzip.open("output/pta2b_controls/main/effects.jsonl.gz","rt",encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line)
            if row["kind"]!="prediction" or row["result"]["family"]!="minimal_pt1b_distinct_terminal":continue
            for effect in row["result"]["effects"][:per_state]:
                result.append((row["state"],"PTA2B_conditional",Deal.parse(effect["source_deal_id"]),Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH))
    old=json.loads(Path("output/pta2_erv/main/summary.json").read_text(encoding="utf-8"))
    targets=[r for r in old["calibration_records"] if r["cohort"]=="PT1B_conditioned_sources"]
    with gzip.open("output/pta2_erv/main/hypotheses.jsonl.gz","rt",encoding="utf-8") as stream:
        predictions=[json.loads(line) for line in stream][10:]
    for p,t in list(zip(predictions,targets))[:external]:
        result.append((t["state"],"PT1B_conditioned",Deal.parse(t["full_information_target"]["source_deal_id"]),
            Seat(p["perspective"]),Suit(p["studied_suit"]),Suit(p["trump"]),Seat(p["declarer"])))
    count=0
    for seed in range(121000,122000):
        d=generate_deal(seed);own=d.hand(Seat.SOUTH)
        trump=max(Suit,key=lambda s:own.length(s))
        short=[s for s in Suit if s is not trump and own.length(s)<2]
        if not short:continue
        result.append(("diverse_"+str(count),"uniform_deal_diagnostic",d,Seat.SOUTH,short[0],trump,Seat.NORTH))
        count+=1
        if count>=diverse:break
    for text in ("AKQJT.AKQ.2.AKQJ","AKQJT9876543.2.-.-","AKQJ9876.543.-.T2"):
        own=Hand.parse(text)
        free=[c for c in full_deck() if c not in own.cards]
        random.Random(123001).shuffle(free)
        d=Deal(0,((Seat.SOUTH,own),(Seat.NORTH,Hand.from_cards(free[:13])),
                  (Seat.EAST,Hand.from_cards(free[13:26])),(Seat.WEST,Hand.from_cards(free[26:]))))
        result.append(("capacity_stress","structural_stress",d,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH))
    return result


def compact(comparison,label,cohort):
    result=jsonable(comparison)
    candidates=result["candidates"]
    source=Deal.parse(result["source_deal_id"])
    defenders=tuple(s for s in Seat if s not in (comparison.perspective,comparison.perspective.partner()))
    for candidate in candidates:
        records=candidate.pop("control_results")
        controls=[Deal.parse(r["deal_id"]) for r in records]
        candidate["representative_control"]=records[0]["deal_id"] if records else None
        candidate["mean_changed_defender_cards"]=mean(sum(len(source.hand(s).cards-d.hand(s).cards) for s in defenders) for d in controls) if controls else None
        candidate["partner_studied_lengths"]=sorted({d.hand(comparison.perspective.partner()).length(comparison.studied_suit) for d in controls})
    exchange=result.pop("exchange")
    result["exchange"]={k:exchange[k] for k in ("failure_reasons","distribution","first_valid_delta","pta2_selected_delta","legal_controls","exhaustive")}
    result["label"],result["cohort"]=label,cohort
    return result


def run(output, *, per_state=6,external=12,diverse=12,config=TargetConfig(),budget=7000):
    if (output/"summary.json").exists(): raise ValueError("fresh output required")
    output.mkdir(parents=True,exist_ok=True)
    session=ResearchSolverSession(EndplayTrickSolver(),max_calls=budget)
    cache_loaded=preload(session)
    started=perf_counter()
    rows=[]
    with gzip.open(output/"comparisons.jsonl.gz","wt",encoding="utf-8") as details:
        for i,(label,cohort,deal,p,studied,trump,declarer) in enumerate(cases(per_state,external,diverse)):
            comparison=evaluate_target_candidates(deal,p,studied,trump,declarer,session,config=config)
            rows.append(compact(comparison,label,cohort))
            details.write(json.dumps(jsonable(comparison))+"\n")
            details.flush()
            if (i+1)%10==0:print("sources",i+1,"new DDS",session.calls,"seconds",round(perf_counter()-started,2),flush=True)
            if session.calls>=budget:raise RuntimeError("DDS budget exhausted; partial detailed results retained")
        sensitivity=[]
        # Three representatives of each shortness, fixed before looking at contrasts.
        selected=[]
        for kind in ("singleton","void"):
            selected.extend([r for r in rows if dict(r["features"])["shortness"]==kind and all(not c["exclusions"] for c in r["candidates"])][:3])
        for row in selected:
            source=Deal.parse(row["source_deal_id"])
            variants=[]
            for name,variant in (("partner_first",replace(config,priority=MatchingPriority.PARTNER_FIRST)),
                                 ("independent_reference_seed",replace(config,control_seed=config.control_seed+1)),
                                 ("double_matching_pool",replace(config,matching_pool=config.matching_pool*2))):
                r=evaluate_target_candidates(source,Seat(row["perspective"]),Suit(row["studied_suit"]),Suit(row["trump"]),
                    Seat(row["declarer"]),session,config=variant)
                variants.append({"variant":name,"targets":{c.target.value:c.delta for c in r.candidates}})
            sensitivity.append({"source_deal_id":row["source_deal_id"],"shortness":dict(row["features"])["shortness"],
                "baseline":{c["target"]:c["delta"] for c in row["candidates"]},"variants":variants})
        # Experimental expectations stay separate; no candidate replaces PT-A2.
        expectations=[]
        for own in (OWN_SINGLETON,OWN_VOID):
            for label,state in information_states(own):
                r=compare_candidate_expectations(state,Suit.DIAMONDS,Suit.SPADES,session,
                    sampling=ERVConfig(SamplingConfig(4,2000,124000+len(expectations))),targets=config)
                data=jsonable(r)
                data["label"]=("singleton_" if own is OWN_SINGLETON else "void_")+label
                details.write(json.dumps({"experimental_expectation":data})+"\n")
                del data["comparisons"],data["weights"]
                expectations.append(data)
        collapse=[]
        for void in (False,True):
            r=compare_candidate_expectations(collapse_state(void),Suit.DIAMONDS,Suit.SPADES,session,
                sampling=ERVConfig(SamplingConfig(3,3,72000)),targets=config)
            first=r.comparisons[0]
            assert len({x.source_deal_id for x in r.comparisons})==1
            assert all(abs(stats["mean"]-next(c.delta for c in first.candidates if c.target is kind))<1e-10
                       for kind,stats in r.target_statistics)
            collapse.append({"shortness":"void" if void else "singleton","full_target":compact(first,"collapse","synthetic"),
                "outer_statistics":jsonable(r.target_statistics)})
        worlds=json.loads(Path("output/pta2_erv/main/leakage.json").read_text(encoding="utf-8"))["source_worlds"]
        states=[dict(information_states(Deal.parse(w).hand(Seat.SOUTH)))["unknown_fit"] for w in worlds]
        cfg=ERVConfig(SamplingConfig(3,2000,125000))
        estimates=[compare_candidate_expectations(s,Suit.DIAMONDS,Suit.SPADES,session,sampling=cfg,targets=config) for s in states]
        assert estimates[0]==estimates[1]
    comparisons={}
    for cohort in sorted({r["cohort"] for r in rows}):
        data=[r for r in rows if r["cohort"]==cohort]
        comparisons[cohort]={}
        for kind in TargetKind:
            values=[next(c["delta"] for c in r["candidates"] if c["target"]==kind.value) for r in data]
            comparisons[cohort][kind.value]={ref:paired_metrics(values,[
                r["exchange"]["distribution"][ref] if ref in ("mean","median") else r["exchange"]["first_valid_delta"] for r in data])
                for ref in ("first_valid","mean","median")}
    strata={}
    for field in ("shortness","trump_role","total_trumps","ruffable_loser_proxy","side_ace_entries","defender_split","label"):
        groups=defaultdict(list)
        for r in rows:
            groups[str(r["label"] if field=="label" else dict(r["features"])[field])].append(r)
        strata[field]={key:{"n":len(group),"targets":{kind.value:{
            "defined":sum(next(c["delta"] for c in r["candidates"] if c["target"]==kind.value) is not None for r in group),
            "mean":mean(v) if (v:=[next(c["delta"] for c in r["candidates"] if c["target"]==kind.value) for r in group
                if next(c["delta"] for c in r["candidates"] if c["target"]==kind.value) is not None]) else None}
            for kind in TargetKind}} for key,group in groups.items()}
    payload={"status":"complete","configuration":jsonable(config),"rows":rows,"comparisons":comparisons,
        "strata":strata,"sensitivity":sensitivity,"experimental_expectations":expectations,"collapse":collapse,
        "leakage":{"identical_partial_results":True,"worlds":worlds,"fingerprint":estimates[0].fingerprint},
        "runtime":{"new_dds_calls":session.calls,"cache_hits":session.cache_hits,"preloaded_cache_entries":cache_loaded,
                   "dds_failures":session.failures,"dds_seconds":session.wall_seconds,"wall_seconds":perf_counter()-started,"budget":budget},
        "adopted_target":None}
    (output/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(payload["runtime"],flush=True)
    return payload


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--pilot",action="store_true")
    parser.add_argument("--census",action="store_true")
    args=parser.parse_args()
    if args.census:
        args.output.mkdir(parents=True,exist_ok=True)
        print(census(args.output))
    elif args.pilot:
        run(args.output,per_state=2,external=4,diverse=4,
            config=TargetConfig(reference_draws=8,matching_pool=32,matched_controls=4),budget=3000)
    else:run(args.output)