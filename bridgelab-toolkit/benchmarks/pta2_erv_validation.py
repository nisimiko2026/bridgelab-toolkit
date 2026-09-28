"""Bounded PT-A2 DDS research, calibration, and exchange sensitivity.

All artifacts are new PT-A2 outputs. No prior corpus is regenerated.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import replace
import gzip
import json
from math import sqrt
from pathlib import Path
import random
from statistics import mean, stdev
from time import perf_counter

from bridge.auction_information import (
    AuctionInformationState, AuctionConstraintUpdate, Certainty, ConstraintProvenance,
    EvidenceOrigin, NumericRange, RangeEvidence, ShapeEvidence,
)
from bridge.conditional_hidden_hand import ConditionalSampler
from bridge.deals import Deal
from bridge.endplay_trick_solver import EndplayTrickSolver
from bridge.expected_ruffing_research import (
    ERVConfig, PairStatus, ResearchSolverSession, SEATS, estimate_erv, control_support_guaranteed, information_fingerprint,
    jsonable, paired_controls, realized_shortness_effect,
)
from bridge.hidden_hand_probability import SamplingConfig
from bridge.models import Hand, Seat, Suit
from bridge.playing_trick_calibration import ShortnessKind, generate_conditioned_case

SOURCE=ConstraintProvenance(EvidenceOrigin.PROFILE_INTERPRETATION,"PT-A2 synthetic general constraint")
OWN_SINGLETON=Hand.parse("AKQ42.9876.3.J76")
OWN_VOID=Hand.parse("AKQ42.98765.-.J76")
CONTROL_SEED=3202


def length(seat,suit,lo,hi=13):
    return AuctionConstraintUpdate(seat,suit_lengths=((suit,RangeEvidence(
        NumericRange(lo,hi),Certainty.GUARANTEED,SOURCE)),))


def information_states(own):
    base=AuctionInformationState.start(Seat.SOUTH,own,Seat.SOUTH)
    return (
        ("unknown_fit",base),
        ("support_ge3",base.with_updates((length(Seat.NORTH,Suit.SPADES,3),))),
        ("support_ge4",base.with_updates((length(Seat.NORTH,Suit.SPADES,4),))),
        ("support_eq4",base.with_updates((length(Seat.NORTH,Suit.SPADES,4,4),))),
        ("defender_diamonds_5_3",base.with_updates((length(Seat.NORTH,Suit.SPADES,4,4),
            length(Seat.WEST,Suit.DIAMONDS,5,5),length(Seat.EAST,Suit.DIAMONDS,3,3)))),
    )


def collapse_state(void):
    own=Hand.parse("AKQJT9876.5432.-.-" if void else "AKQJT9876.432.A.-")
    shapes=((Seat.NORTH,(4,0,9,0)),(Seat.WEST,(0,9 if void else 10,4 if void else 3,0)),
            (Seat.EAST,(0,0,0,13)))
    updates=tuple(AuctionConstraintUpdate(seat,shapes=ShapeEvidence((shape,),Certainty.GUARANTEED,SOURCE))
                  for seat,shape in shapes)
    updates+=(AuctionConstraintUpdate(Seat.NORTH,hcp=RangeEvidence(NumericRange(0,0),Certainty.GUARANTEED,SOURCE)),)
    return AuctionInformationState.start(Seat.SOUTH,own,Seat.SOUTH).with_updates(updates)


def compact(result):
    data=jsonable(result)
    del data["effects"],data["weights"]
    return data


def prediction_band(value):
    if value<0: return "negative"
    if value<0.5: return "0_to_0.5"
    if value<1: return "0.5_to_1"
    return "1_plus"


def calibration_summary(rows):
    valid=[r for r in rows if r["predicted"] is not None and r["realized"] is not None]
    if not valid:
        return {"attempted":len(rows),"n":0}
    predicted=[r["predicted"] for r in valid]
    realized=[r["realized"] for r in valid]
    errors=[p-y for p,y in zip(predicted,realized)]
    # Shared prediction Monte Carlo error must not be divided by holdout count.
    groups=defaultdict(list)
    for r in valid: groups[r["fingerprint"]].append(r)
    pred_mc_variance=sum((len(g)/len(valid))**2*(g[0]["prediction_se"] or 0)**2 for g in groups.values())
    empirical_variance=(stdev(errors)**2/len(errors)) if len(errors)>1 else None
    se=sqrt(empirical_variance+pred_mc_variance) if empirical_variance is not None else None
    bias=mean(errors)
    return {"attempted":len(rows),"n":len(valid),"information_states":len(groups),
            "mean_predicted":mean(predicted),"mean_realized":mean(realized),
            "prediction_minus_realization":bias,"rmse":sqrt(mean(e*e for e in errors)),
            "mae":mean(abs(e) for e in errors),
            "bias_se_approx":se,"bias_95_ci_approx":[bias-1.96*se,bias+1.96*se] if se is not None else None,
            "ci_note":"Descriptive normal interval plus shared prediction MC variance; small/selected strata are exploratory."}


def calibration_tables(rows):
    tables={}
    for field in ("cohort","shortness","state","predicted_band","trump_role","fit",
                  "ruffable_loser_proxy","side_ace_entries","defender_evidence"):
        groups=defaultdict(list)
        for row in rows: groups[str(row[field])].append(row)
        tables[field]={name:calibration_summary(group) for name,group in sorted(groups.items())}
    return tables


def target_row(target,prediction,*,cohort,state_name):
    p=prediction.distribution.mean
    return {"cohort":cohort,"shortness":prediction.shortness_type,"state":state_name,
            "fingerprint":prediction.information_state_fingerprint,"predicted":p,
            "prediction_se":prediction.distribution.standard_error,
            "prediction_coverage":prediction.evaluable_probability_mass,
            "realized":target.delta_tricks,"target_status":target.status.value,"target_reason":target.reason,
            "predicted_band":prediction_band(p) if p is not None else "unavailable",
            "trump_role":target.trump_role,"fit":target.total_trumps,
            "ruffable_loser_proxy":target.ruffable_loser_proxy,
            "side_ace_entries":sum(target.side_ace_entries),
            "defender_evidence":state_name=="defender_diamonds_5_3",
            "full_information_target":jsonable(target)}


def sensitivity_for(effect,perspective,studied,trump,declarer,session,max_alternatives=8):
    deal=Deal.parse(effect.source_deal_id)
    count=effect.candidate_count
    rng=random.Random(3203+count)
    indices=sorted({effect.selected_index}|set(rng.sample(range(count),min(count,max_alternatives))))
    alternatives=[]
    for index in indices:
        item=realized_shortness_effect(deal,perspective,studied,trump,declarer,session,
                                      control_seed=CONTROL_SEED,control_index=index)
        alternatives.append({"index":index,"delta":item.delta_tricks,"status":item.status.value,
                             "control_deal_id":item.control_deal_id,
                             "solver":jsonable(item.control_solver)})
    values=[item["delta"] for item in alternatives if item["delta"] is not None]
    return {"source_deal_id":deal.serialize(),"candidate_paths":count,"paths_examined":len(indices),
            "exhaustive":len(indices)==count,"original_delta":effect.delta_tricks,
            "mean_alternative_delta":mean(values) if values else None,
            "mean_shift":mean(values)-effect.delta_tricks if values else None,
            "spread":max(values)-min(values) if values else None,"alternatives":alternatives}


def run(output,*,samples=500,holdout=24,external=12,external_samples=64,sensitivity_sources=2,
        max_calls=16000):
    if output.exists() and (output/"summary.json").exists():
        raise ValueError("choose a fresh output directory; completed measurements are never overwritten")
    output.mkdir(parents=True,exist_ok=True)
    solver=EndplayTrickSolver()
    session=ResearchSolverSession(solver,max_calls=max_calls)
    started=perf_counter()
    summaries,calibration,sensitivity=[],[],[]
    metadata=(("implementation","endplay/DDS"),("endplay_version","0.5.12"),("opening_lead","optimal"))
    def persist_summary(partial=True):
        payload={"status":"in_progress" if partial else "complete",
                 "definition":"seed-selected PT-1B shortness-to-doubleton DDS contrast, in tricks",
                 "estimand_warning":"Means condition on legal controls and successful solves; missing hypotheses are not zero.",
                 "seed_policy":"independent prediction/holdout sampling seeds; stable per-deal hashed control seed",
                 "states":summaries,"calibration":calibration_summary(calibration),
                 "calibration_by":calibration_tables(calibration),
                 "calibration_records":calibration,"sensitivity_records":sensitivity,
                 "runtime":{"wall_seconds":perf_counter()-started,"dds_calls":session.calls,
                            "dds_wall_seconds":session.wall_seconds,"cache_hits":session.cache_hits,
                            "dds_failures":session.failures,"dds_call_budget":max_calls}}
        (output/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
        return payload
    with gzip.open(output/"hypotheses.jsonl.gz","wt",encoding="utf-8") as details:
        for hand_index,own in enumerate((OWN_SINGLETON,OWN_VOID)):
            for state_index,(name,state) in enumerate(information_states(own)):
                before_calls,before_seconds=session.calls,perf_counter()
                cfg=ERVConfig(SamplingConfig(samples,200000,32000+100*hand_index+state_index),
                              CONTROL_SEED,metadata)
                result=estimate_erv(state,Suit.DIAMONDS,Suit.SPADES,session,config=cfg)
                row={"label":result.shortness_type+"_"+name,"result":compact(result),
                     "wall_seconds":perf_counter()-before_seconds,"dds_calls":session.calls-before_calls}
                summaries.append(row)
                details.write(json.dumps(jsonable(result),separators=(",",":"))+"\n")
                details.flush()
                # Source cards enter only this later, independently seeded scoring stage.
                hidden=ConditionalSampler(state).sample(SamplingConfig(holdout,200000,42000+100*hand_index+state_index)).model
                for sample in hidden.samples:
                    mapping=dict(sample.hands)
                    mapping[state.perspective]=state.own_hand
                    source=Deal(0,tuple((seat,mapping[seat]) for seat in SEATS))
                    target=realized_shortness_effect(source,state.perspective,Suit.DIAMONDS,Suit.SPADES,
                                                     result.declarer,session,control_seed=CONTROL_SEED)
                    calibration.append(target_row(target,result,cohort="independent_conditional_holdout",state_name=name))
                for effect in [e for e in result.effects if e.status is PairStatus.EVALUABLE][:sensitivity_sources]:
                    item=sensitivity_for(effect,state.perspective,Suit.DIAMONDS,Suit.SPADES,result.declarer,session)
                    item["state"]=row["label"]
                    sensitivity.append(item)
                persist_summary()
                print(row["label"],"sampled",result.sampled_hypotheses,"valid",result.evaluable_hypotheses,
                      "mean",result.distribution.mean,"DDS",row["dds_calls"],"seconds",round(row["wall_seconds"],2),flush=True)
                if session.calls>=max_calls:
                    raise RuntimeError("bounded DDS budget exhausted; partial artifacts retained")
        # Small independent PT-1B-generated source cohort; its selection prior differs
        # from the hard-conditioned uniform baseline, so report it separately.
        for i in range(external):
            kind=ShortnessKind.SHORT_HAND_SINGLETON if i%2==0 else ShortnessKind.LONG_HAND_SINGLETON
            case=generate_conditioned_case(52000+i,(5,3) if i%3 else (6,4),kind)
            source=Deal.parse(case.deal_id,seed=case.deal_seed)
            item=case.short_suits[0]
            other=source.hand(item.hand.partner()).length(case.trump_suit)
            guarantee=3 if other==3 else 4
            state=AuctionInformationState.start(item.hand,source.hand(item.hand),item.hand).with_updates((
                length(item.hand.partner(),case.trump_suit,guarantee),))
            result=estimate_erv(state,item.suit,case.trump_suit,session,declarer=Seat.NORTH,
                config=ERVConfig(SamplingConfig(external_samples,200000,62000+i),CONTROL_SEED,metadata))
            target=realized_shortness_effect(source,item.hand,item.suit,case.trump_suit,Seat.NORTH,
                                            session,control_seed=CONTROL_SEED)
            calibration.append(target_row(target,result,cohort="PT1B_conditioned_sources",state_name="support_ge"+str(guarantee)))
            details.write(json.dumps(jsonable(result),separators=(",",":"))+"\n")
            details.flush()
            persist_summary()
            print("PT1B source",i,"prediction",result.distribution.mean,"realized",target.delta_tricks,flush=True)
        collapses=[]
        for void in (False,True):
            state=collapse_state(void)
            result=estimate_erv(state,Suit.DIAMONDS,Suit.SPADES,session,
                               config=ERVConfig(SamplingConfig(8,8,72000),CONTROL_SEED,metadata))
            first=result.effects[0]
            target=realized_shortness_effect(Deal.parse(first.source_deal_id),Seat.SOUTH,Suit.DIAMONDS,
                                            Suit.SPADES,Seat.NORTH,session,control_seed=CONTROL_SEED)
            assert result.sampling_diagnostics.proposal_allocation_count==1
            assert result.full_hard_evidence_mean==target.delta_tricks
            collapses.append({"shortness":result.shortness_type,"prediction":compact(result),
                              "target":jsonable(target),"identical_control":len({e.control_deal_id for e in result.effects})==1})
    payload=persist_summary(False)
    payload["full_information_collapse"]=collapses
    spreads=[r["spread"] for r in sensitivity if r["spread"] is not None]
    payload["sensitivity_summary"]={"sources":len(spreads),
        "fraction_sensitive":mean(s>0 for s in spreads) if spreads else None,
        "mean_spread":mean(spreads) if spreads else None,"max_observed_spread":max(spreads) if spreads else None,
        "mean_shift_from_selected":mean(r["mean_shift"] for r in sensitivity if r["mean_shift"] is not None) if spreads else None,
        "note":"Capped alternative-path sample; observed spreads lower-bound full control ambiguity."}
    payload["calibration_note"]="Holdouts assess internal expectation calibration. PT-1B-generated sources have a different selection prior; latent-feature strata are exploratory."
    reporting_metadata(payload)
    (output/"summary.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload


def reporting_metadata(payload):
    """Derive reporting fields only; no sampling, control construction or solves."""
    cohorts=sorted({row["cohort"] for row in payload["calibration_records"]})
    payload["calibration_strata_by_cohort"]={
        cohort:calibration_tables([row for row in payload["calibration_records"] if row["cohort"]==cohort])
        for cohort in cohorts}
    records=payload["sensitivity_records"]
    for record in records:
        record["delta_changed"]=any(
            item["delta"] is not None and item["delta"]!=record["original_delta"]
            for item in record["alternatives"])
    payload["sensitivity_summary"]["changed_sources"]=sum(r["delta_changed"] for r in records)
    shifts={}
    for state_row in payload["states"]:
        selected=[r for r in records if r["state"]==state_row["label"] and r["mean_shift"] is not None]
        if not selected:
            continue
        result=state_row["result"]
        n=result["evaluable_hypotheses"]
        # Baseline PT-A1B samples have equal weights. Replace only the tested
        # occurrences with their mean over the recorded alternative paths.
        assert abs(result["distribution"]["effective_sample_size"]-n)<1e-8
        change=sum(r["mean_shift"] for r in selected)/n
        shifts[state_row["label"]]={
            "tested_sources":len(selected),"evaluable_hypotheses":n,
            "subset_original_mean":mean(r["original_delta"] for r in selected),
            "subset_alternative_mean":mean(r["mean_alternative_delta"] for r in selected),
            "subset_mean_shift":mean(r["mean_shift"] for r in selected),
            "full_cohort_mean_shift_replacing_only_tested_controls":change,
            "full_cohort_mean_after_partial_replacement":result["distribution"]["mean"]+change}
    payload["sensitivity_mean_effects"]=shifts
    total_valid=sum(row["result"]["evaluable_hypotheses"] for row in payload["states"])
    payload["sensitivity_summary"]["pooled_evaluable_mean_shift_replacing_only_tested_controls"]=(
        sum(r["mean_shift"] for r in records if r["mean_shift"] is not None)/total_valid)
    payload["reporting_metadata_finalization"]={
        "additional_dds_calls":0,
        "note":"Separate calibration priors. Replacement uses the recorded alternative-path mean, including the original path, only for tested sample occurrences; it is not an extrapolation to untested controls."}
    return payload


def finalize_reporting_metadata(output):
    """Finish saved summaries while preserving measured outcomes and archives."""
    assert output.resolve().is_relative_to(Path("output/pta2_erv").resolve())
    path=output/"summary.json"
    payload=json.loads(path.read_text())
    assert payload["status"]=="complete"
    reporting_metadata(payload)
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload["sensitivity_mean_effects"]


def _restore_state(record):
    """Reconstruct only recorded visible state/general constraints, never source cards."""
    def provenance(data):
        return ConstraintProvenance(EvidenceOrigin(data["origin"]),data["reference"],
                                    data["call_index"],data["source_id"])
    def evidence(data):
        if data is None: return None
        assert data["distribution"] is None
        return RangeEvidence(NumericRange(**data["bounds"]),Certainty(data["certainty"]),
                             provenance(data["provenance"]))
    updates=[]
    for item in record["evidence"]:
        shape=item["shapes"]
        updates.append(AuctionConstraintUpdate(Seat(item["target"]),hcp=evidence(item["hcp"]),
            suit_lengths=tuple((Suit(suit),evidence(e)) for suit,e in item["suit_lengths"]),
            shapes=ShapeEvidence(tuple(tuple(row) for row in shape["allowed"]),Certainty(shape["certainty"]),
                                 provenance(shape["provenance"])) if shape else None))
    seat=Seat(record["perspective"])
    state=AuctionInformationState.start(seat,Hand.parse(record["visible_hand"]),seat).with_updates(tuple(updates))
    assert information_fingerprint(state)==record["information_state_fingerprint"]
    return state


def finalize_support_metadata(output):
    """Apply conservative support identification to saved measurements without DDS."""
    from hashlib import sha256
    assert output.resolve().is_relative_to(Path("output/pta2_erv").resolve())
    path=output/"summary.json"
    payload=json.loads(path.read_text())
    assert payload["status"]=="complete"
    def update(record):
        state=_restore_state(record)
        guaranteed=control_support_guaranteed(state,Suit(record["studied_suit"]),Suit(record["trump"]),
            record["sampling_diagnostics"]["proposal_allocation_count"],record["evaluable_hypotheses"]>0)
        record["control_support_guaranteed"]=guaranteed
        record["full_hard_evidence_mean"]=record["distribution"]["mean"] if record["status"]=="complete" and guaranteed else None
        return record
    for row in payload["states"]: update(row["result"])
    for row in payload["full_information_collapse"]: update(row["prediction"])
    source=output/"hypotheses.jsonl.gz"
    temporary=output/"hypotheses.support-finalized.tmp"
    digest=sha256()
    count=0
    with gzip.open(source,"rt",encoding="utf-8") as stream, gzip.open(temporary,"wt",encoding="utf-8") as target:
        for line in stream:
            record=json.loads(line)
            before=json.dumps((record["effects"],record["weights"]),sort_keys=True)
            update(record)
            assert before==json.dumps((record["effects"],record["weights"]),sort_keys=True)
            digest.update(before.encode())
            target.write(json.dumps(record,separators=(",",":"))+"\n")
            count+=1
    temporary.replace(source)
    payload["support_metadata_finalization"]={
        "records":count,"effects_and_weights_sha256":digest.hexdigest(),"additional_dds_calls":0,
        "note":"Conservative support-wide proof added after measurement; effects, weights and all statistics unchanged."}
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload["support_metadata_finalization"]


def validate_leakage(output):
    payload=json.loads((output/"summary.json").read_text())
    groups=defaultdict(list)
    for row in payload["calibration_records"]:
        if row["cohort"]=="independent_conditional_holdout" and row["realized"] is not None:
            groups[row["fingerprint"]].append(row)
    pair=None
    for rows in groups.values():
        for row in rows[1:]:
            if row["realized"]!=rows[0]["realized"]:
                pair=(rows[0],row)
                break
        if pair: break
    assert pair is not None
    worlds=[Deal.parse(row["full_information_target"]["source_deal_id"]) for row in pair]
    states=[dict(information_states(world.hand(Seat.SOUTH)))[pair[0]["state"]] for world in worlds]
    assert states[0]==states[1] and worlds[0].serialize()!=worlds[1].serialize()
    cfg=ERVConfig(SamplingConfig(32,200000,83000),CONTROL_SEED,(("implementation","endplay/DDS"),("endplay_version","0.5.12")))
    sessions=[ResearchSolverSession(EndplayTrickSolver(),max_calls=1000) for _ in range(2)]
    started=perf_counter()
    estimates=[estimate_erv(state,Suit.DIAMONDS,Suit.SPADES,session,config=cfg)
               for state,session in zip(states,sessions)]
    assert estimates[0]==estimates[1]
    # Full source worlds are passed to the scoring API only after both estimates.
    targets=[realized_shortness_effect(world,Seat.SOUTH,Suit.DIAMONDS,Suit.SPADES,Seat.NORTH,
                                      session,control_seed=CONTROL_SEED)
             for world,session in zip(worlds,sessions)]
    assert targets[0].delta_tricks!=targets[1].delta_tricks
    result={"identical_partial_information_results":True,"source_worlds":[w.serialize() for w in worlds],
            "state_fingerprint":information_fingerprint(states[0]),"config":jsonable(cfg),
            "partial_mean":estimates[0].distribution.mean,"sampled":estimates[0].sampled_hypotheses,
            "evaluable":estimates[0].evaluable_hypotheses,
            "later_realized_targets":[t.delta_tricks for t in targets],
            "dds_calls":sum(s.calls for s in sessions),"dds_failures":sum(s.failures for s in sessions),
            "wall_seconds":perf_counter()-started}
    (output/"leakage.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("output/pta2_erv/main"))
    parser.add_argument("--samples",type=int,default=500)
    parser.add_argument("--holdout",type=int,default=24)
    parser.add_argument("--external",type=int,default=12)
    parser.add_argument("--external-samples",type=int,default=64)
    parser.add_argument("--sensitivity-sources",type=int,default=2)
    parser.add_argument("--max-calls",type=int,default=16000)
    args=parser.parse_args()
    run(args.output,samples=args.samples,holdout=args.holdout,external=args.external,
        external_samples=args.external_samples,sensitivity_sources=args.sensitivity_sources,max_calls=args.max_calls)


if __name__=="__main__":
    main()
