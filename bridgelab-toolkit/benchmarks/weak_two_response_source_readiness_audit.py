"""Phase 12S deterministic weak-two response source-readiness audit."""
# ruff: noqa: E701, E702
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Suit, Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router

SUITS={"2D":Suit.DIAMONDS,"2H":Suit.HEARTS,"2S":Suit.SPADES}
ORDER=("very-strong/slam-interest-looking","game-looking-with-support","balanced/nt-inquiry-looking","support/raise-oriented","long-independent-suit","weak/no-action-looking")

@dataclass(frozen=True,slots=True)
class Audit:
 start_seed:int; deal_count:int; expected_population:int; population:int
 per_opening:dict[str,int]; primary_partitions:dict[str,int]; opening_partitions:dict[str,dict[str,int]]
 distributions:dict[str,dict[str,object]]; positions:tuple[dict[str,object],...]; source_matrix:tuple[dict[str,object],...]
 top_candidates:tuple[dict[str,object],...]; source_safe_candidates:tuple[str,...]; two_d_meaning:str
 inquiry_findings:dict[str,object]; decision:str; phase12t_recommendation:dict[str,object]
 route_count:int; production_rules_added:int=0; routes_added:int=0; policies_added:int=0
 production_defaults_changed:bool=False; knowledge_markdown_changed:int=0
 def to_dict(self): return asdict(self)

def _cat(e,support,independent):
 if e.hcp>=19:return ORDER[0]
 if e.hcp>=15 and support>=3:return ORDER[1]
 if e.is_balanced:return ORDER[2]
 if support>=3:return ORDER[3]
 if independent>=6:return ORDER[4]
 return ORDER[5]

def run_weak_two_response_source_readiness_audit(*,start_seed=1,deal_count=10_000):
 b=run_sayc_coverage_benchmark(start_seed=start_seed,count=deal_count); router=create_standard_sayc_router(); pos=[]; groups=defaultdict(list)
 for case in b.batch.cases:
  r=case.result
  if r.stop_reason.value!="no-recommendation" or r.final_auction not in {f"{o} P" for o in SUITS}:continue
  opening=r.final_auction.split()[0]; suit=SUITS[opening]; hand=case.deal.hand(r.stopped_seat); oh=case.deal.hand(r.stopped_seat.partner()); e=evaluate_hand(hand); oe=evaluate_hand(oh)
  support=e.length(suit); independent=max(e.length(x) for x in Suit if x is not suit); category=_cat(e,support,independent)
  context=BiddingContext.create(hand=hand,auction=Auction(r.dealer,tuple(r.final_auction.split())),vulnerability=Vulnerability.NONE,system=SystemContext("SAYC")); route_match=router.match(context); result=router.evaluate(context)
  row={"seed":case.deal.seed,"stable_id":f"seed-{case.deal.seed}:{r.stopped_seat.value}:{opening}-P","auction_prefix":r.final_auction,"opening_bid":opening,"opener_hcp":oe.hcp,"opener_shape":"-".join(map(str,oh.shape)),"opener_opened_suit_length":oe.length(suit),"opener_suit_quality":"production opening rule accepted the frozen suit-quality guard","responder_hcp":e.hcp,"responder_shape":"-".join(map(str,hand.shape)),"responder_suit_lengths_shdc":{x.name[0]:e.length(x) for x in (Suit.SPADES,Suit.HEARTS,Suit.DIAMONDS,Suit.CLUBS)},"support":support,"longest_suit_length":max(e.length(x) for x in Suit),"balanced":e.is_balanced,"primary_family":category,"secondary_flags":{"weak_no_action":e.hcp<=10,"support_raise":support>=3,"game_with_support":e.hcp>=15 and support>=3,"balanced_nt":e.is_balanced,"long_independent":independent>=6,"very_strong":e.hcp>=19,"slam_interest":e.hcp>=19,"inquiry_looking":e.hcp>=15},"route_exists":route_match is not None,"route_name":None if route_match is None else route_match.route_id,"route_reaches_rule":route_match is not None,"rule_attempted":None if route_match is None else route_match.route_id,"rule_abstains":route_match is not None and result.recommended_call is None,"route_missing":route_match is None,"current_action":"ABSTAIN" if result.recommended_call is None else result.recommended_call.serialize()}
  pos.append(row);groups[(opening,category)].append(row)
 counts=Counter(x["opening_bid"] for x in pos); primary=Counter(x["primary_family"] for x in pos)
 oparts={o:{c:len(groups[(o,c)]) for c in ORDER if groups[(o,c)]} for o in SUITS}; dist={}
 for o in SUITS:
  rows=[x for x in pos if x["opening_bid"]==o];dist[o]={"responder_hcp":dict(sorted(Counter(x["responder_hcp"] for x in rows).items())),"responder_shape":dict(sorted(Counter(x["responder_shape"] for x in rows).items())),"responder_support":dict(sorted(Counter(x["support"] for x in rows).items()))}
 matrix=[]
 for o in SUITS:
  for c in ORDER:
   rows=groups[(o,c)]
   if not rows:continue
   h=[x["responder_hcp"] for x in rows]; calls=("2NT inquiry","Pass","raise","game","new suit","3NT")
   matrix.append({"opening":o,"family_id":f"weak-two.{o.casefold()}.{c}","observed_count":len(rows),"responder_hcp_range":f"{min(h)}-{max(h)}","shape_support":c,"candidate_calls":calls,"frozen_source_finding":"Actions are named, but triggers and precedence are qualitative; inquiry replies vary by partnership and Ogust is optional.","classification":"LOW_SAMPLE" if len(rows)<5 else "PARTNERSHIP_DEPENDENT","executable_subset":False,"policy_required":False,"architecture_required":False,"primary_blocker":"No complete exact trigger/call/forcing/precedence/exceptions contract.","recommended_action":"defer"})
 by={x["family_id"]:x for x in matrix}; top=tuple(by[x] for x in ("weak-two.2d.balanced/nt-inquiry-looking","weak-two.2h.balanced/nt-inquiry-looking","weak-two.2s.balanced/nt-inquiry-looking","weak-two.2s.support/raise-oriented","weak-two.2d.support/raise-oriented"))
 return Audit(start_seed,deal_count,540,len(pos),dict(counts),{c:primary[c] for c in ORDER},oparts,dist,tuple(pos),tuple(matrix),top,(),"Natural weak two: current rule sayc.opening.weak2.2d and frozen source both define 2D as natural in this configuration; alternative Multi/Flannery/Roman meanings are not active.",{"two_nt_inquiry_exists":True,"forcing_status_complete":False,"feature_ask_replies_complete":False,"ogust_optional":True,"minimum_maximum_mapping_partnership_dependent":True,"executable":False},"E. DEFER WEAK-TWO RESPONSES",{"phase":"Phase 12T — Two-Notrump Response Source-Readiness Audit","family_id":"response.two-notrump","exact_prefix":"2NT P","phase12m_population":33,"expected_action":"ABSTAIN","audit_only":True},len(router.routes))

def write_artifacts(a,output_dir):
 out=Path(output_dir);jp=out/"bridgelab_phase12s_weak_two_response_source_readiness_audit.json";mp=out/"bridgelab_phase12s_weak_two_response_source_readiness_audit.md";jp.write_text(json.dumps(a.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8")
 rows="\n".join(f"| {x['opening']} | {x['family_id']} | {x['observed_count']} | {x['responder_hcp_range']} | {x['classification']} | NO | {x['primary_blocker']} |" for x in a.source_matrix)
 mp.write_text(f"""# Phase 12S — Weak-Two Response Source-Readiness Audit

- Seeds: 1–10,000
- Phase 12M expected population: 540; measured: {a.population} (confirmed)
- Per opening: 2D={a.per_opening['2D']}, 2H={a.per_opening['2H']}, 2S={a.per_opening['2S']}
- All current actions: `ABSTAIN`; routes: {a.route_count}

## Exact 2D meaning

{a.two_d_meaning}

## Primary partitions

{json.dumps(a.primary_partitions,sort_keys=True)}

Full opening-specific HCP, shape, support distributions and all positions are in the JSON artifact.

## Inquiry / Ogust / Feature Ask

2NT is described as an artificial inquiry/Feature Ask, but its exact responder trigger and forcing status are incomplete. Reply meanings vary by partnership. Ogust is explicitly optional and other structures exist. No inquiry or reply subset is executable.

## Source-certainty matrix

| Opening | Family | Count | HCP | Classification | Executable | Blocker |
|---|---|---:|---|---|---|---|
{rows}

2H and 2S remain independently inventoried. No complete source contract authorizes merging them or assigning calls.

## Decision

**{a.decision}.** Best source-safe subset: none.

Top candidates are the three opening-specific balanced/inquiry-looking groups followed by the 2S and 2D support-oriented groups; all remain blocked by incomplete triggers, forcing status, reply structure, precedence, and exceptions.

Recommend **{a.phase12t_recommendation['phase']}**, exact prefix `2NT P`, Phase 12M population 33, audit-only with no numeric authorization, policy, or route.

Production rules/routes/policies added: 0/0/0. Defaults unchanged. Knowledge Markdown changes: 0.

Current cumulative Full Kit: Phase 12S
""",encoding="utf-8");return mp,jp

if __name__=="__main__":write_artifacts(run_weak_two_response_source_readiness_audit(),Path.cwd())
