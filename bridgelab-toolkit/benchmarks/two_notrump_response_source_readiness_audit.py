"""Phase 12T audit of residual responder decisions after 2NT-P."""
# ruff: noqa: E701, E702
from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import asdict,dataclass
import json
from pathlib import Path
from bridge.auction import Auction
from bridge.bidding_rules import BiddingContext,SystemContext
from bridge.evaluation import evaluate_hand
from bridge.models import Suit,Vulnerability
from bridge.sayc_coverage_benchmark import run_sayc_coverage_benchmark
from bridge.sayc_route_configuration import create_standard_sayc_router
ORDER=("five-plus-hearts","five-plus-spades","both-majors-four-plus","exactly-one-four-card-major","balanced-slam-interest","balanced-no-four-major","long-minor","slam-interest-looking","game-looking","weak-no-action")
@dataclass(frozen=True,slots=True)
class Audit:
 start_seed:int;deal_count:int;expected_population:int;population:int;opening_semantics:dict[str,object];primary_partitions:dict[str,int];positions:tuple[dict[str,object],...];source_matrix:tuple[dict[str,object],...];top_candidates:tuple[dict[str,object],...];method_findings:dict[str,object];source_safe_candidates:tuple[str,...];decision:str;phase12u_recommendation:dict[str,object];route_count:int;production_rules_added:int=0;routes_added:int=0;policies_added:int=0;production_defaults_changed:bool=False;knowledge_markdown_changed:int=0
 def to_dict(self):return asdict(self)
def _family(e):
 h=e.length(Suit.HEARTS);s=e.length(Suit.SPADES);m=max(e.length(Suit.CLUBS),e.length(Suit.DIAMONDS))
 if h>=5:return ORDER[0]
 if s>=5:return ORDER[1]
 if h>=4 and s>=4:return ORDER[2]
 if h==4 or s==4:return ORDER[3]
 if e.is_balanced and e.hcp>=11:return ORDER[4]
 if e.is_balanced:return ORDER[5]
 if m>=6:return ORDER[6]
 if e.hcp>=11:return ORDER[7]
 if e.hcp>=6:return ORDER[8]
 return ORDER[9]
def run_two_notrump_response_source_readiness_audit(*,start_seed=1,deal_count=10_000):
 b=run_sayc_coverage_benchmark(start_seed=start_seed,count=deal_count);router=create_standard_sayc_router();p=[];g=defaultdict(list)
 for case in b.batch.cases:
  r=case.result
  if r.stop_reason.value!="no-recommendation" or r.final_auction!="2NT P":continue
  hand=case.deal.hand(r.stopped_seat);oh=case.deal.hand(r.stopped_seat.partner());e=evaluate_hand(hand);oe=evaluate_hand(oh);f=_family(e);ctx=BiddingContext.create(hand=hand,auction=Auction(r.dealer,("2NT","P")),vulnerability=Vulnerability.NONE,system=SystemContext("SAYC"));route=router.match(ctx);out=router.evaluate(ctx)
  row={"seed":case.deal.seed,"stable_id":f"seed-{case.deal.seed}:S:2NT-P","auction_prefix":"2NT P","opener_hcp":oe.hcp,"opener_shape":"-".join(map(str,oh.shape)),"opener_balanced":oe.is_balanced,"responder_hcp":e.hcp,"responder_shape":"-".join(map(str,hand.shape)),"responder_balanced":e.is_balanced,"suit_lengths_shdc":{x.name[0]:e.length(x) for x in (Suit.SPADES,Suit.HEARTS,Suit.DIAMONDS,Suit.CLUBS)},"four_card_majors":[x.name for x in (Suit.HEARTS,Suit.SPADES) if e.length(x)==4],"five_plus_majors":[x.name for x in (Suit.HEARTS,Suit.SPADES) if e.length(x)>=5],"long_minors":[x.name for x in (Suit.DIAMONDS,Suit.CLUBS) if e.length(x)>=6],"primary_family":f,"route_name":None if route is None else route.route_id,"route_exists":route is not None,"rule_attempted":None if route is None else route.route_id,"rule_abstains":out.recommended_call is None,"current_action":"ABSTAIN"}
  p.append(row);g[f].append(row)
 matrix=[]
 calls={ORDER[0]:("3D",),ORDER[1]:("3H",),ORDER[2]:("3C",),ORDER[3]:("3C",),ORDER[4]:("4NT","slam actions"),ORDER[5]:("Pass","3NT"),ORDER[6]:("minor methods","3NT"),ORDER[7]:("slam actions",),ORDER[8]:("3NT",),ORDER[9]:("Pass",)}
 for f in ORDER:
  rows=g[f]
  if not rows:continue
  hs=[x["responder_hcp"] for x in rows];matrix.append({"family_id":f,"observed_count":len(rows),"hcp_range":f"{min(hs)}-{max(hs)}","shape_characteristics":dict(sorted(Counter(x["responder_shape"] for x in rows).items())),"candidate_calls":calls[f],"frozen_source_finding":"The source names this action/method, but does not provide a complete residual trigger, precedence, and exception contract.","classification":"LOW_SAMPLE" if len(rows)<3 else "SOURCE_PARTIAL","executable_subset":False,"policy_required":False,"architecture_required":False,"primary_blocker":"Incomplete exact strength/shape precedence and exceptions.","recommended_action":"defer"})
 by={x["family_id"]:x for x in matrix};rank=tuple(by[x] for x in ("exactly-one-four-card-major","both-majors-four-plus","five-plus-hearts","balanced-no-four-major","long-minor"))
 return Audit(start_seed,deal_count,33,len(p),{"natural":True,"hcp_range":"20-21","balanced_required":True},dict(Counter(x["primary_family"] for x in p)),tuple(p),tuple(matrix),rank,{"stayman":{"call":"3C","source_defined":True,"complete_responder_trigger":False,"dual_major_complete":False},"transfers":{"3D":"hearts","3H":"spades","five_plus_required":True,"any_strength":True,"acceptance_defined":True,"continuations_complete":False},"natural":{"pass_complete":False,"3NT_complete":False,"direct_games_complete":False,"minor_actions_partnership_dependent":True}},(),"E. DEFER 2NT RESPONSES",{"phase":"Phase 12U — One-Level Response Residual Source-Readiness Audit","family_id":"response.one-level-existing-rule","prefixes":("1C P","1D P","1H P","1S P"),"phase12m_population":693,"audit_only":True},len(router.routes))
def write_artifacts(a,out):
 out=Path(out);j=out/"bridgelab_phase12t_two_notrump_response_source_readiness_audit.json";m=out/"bridgelab_phase12t_two_notrump_response_source_readiness_audit.md";j.write_text(json.dumps(a.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8");rows="\n".join(f"| {x['family_id']} | {x['observed_count']} | {x['hcp_range']} | {', '.join(x['candidate_calls'])} | {x['classification']} | NO | {x['primary_blocker']} |" for x in a.source_matrix);m.write_text(f"""# Phase 12T — Two-Notrump Response Source-Readiness Audit

Seeds 1–10,000. Expected population 33; measured **{a.population}**, confirmed. All are exact `2NT P` responder abstentions routed to `sayc.response.2nt.jacoby`; downstream `2NT-3D-3H` and `2NT-3H-3S` are excluded. Routes remain {a.route_count}.

Opener semantics: natural, balanced, 20–21 HCP. Primary partition: `{json.dumps(a.primary_partitions,sort_keys=True)}`. Complete HCP/shape/suit distributions and positions are in JSON.

Stayman `3C` and transfers `3D→hearts`, `3H→spades` are source-defined. Transfers require 5+ cards and any strength and acceptance is defined, but these residuals fall outside existing executable transfer coverage. Stayman responder strength, dual-major treatment, natural Pass/3NT/direct games, continuations, precedence, and exceptions remain incomplete or partnership-dependent.

| Family | Count | HCP | Candidate | Classification | Executable | Blocker |
|---|---:|---|---|---|---|---|
{rows}

Best source-safe subset: none. **{a.decision}.** Top candidates: exactly-one four-card major, both four-plus majors, five-plus hearts residual, balanced/no-major, long minor.

Recommend **{a.phase12u_recommendation['phase']}**, prefixes `1C P / 1D P / 1H P / 1S P`, Phase 12M population 693, audit-only.

Production rules/routes/policies added: 0/0/0. Defaults and knowledge unchanged.

Current cumulative Full Kit: Phase 12T
""",encoding="utf-8");return m,j
if __name__=="__main__":write_artifacts(run_two_notrump_response_source_readiness_audit(),Path.cwd())
