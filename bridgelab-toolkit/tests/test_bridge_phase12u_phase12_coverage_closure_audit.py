# ruff: noqa: E701, E702
from benchmarks.phase12_coverage_closure_audit import run_phase12_coverage_closure_audit
A=run_phase12_coverage_closure_audit()
def test_inventory():assert len(A.inventory)==9;assert len({x["family_id"] for x in A.inventory})==9;assert all(x["final_status"] for x in A.inventory)
def test_populations():assert {x["family_id"]:x["phase12m_population"] for x in A.inventory}["response.two-notrump"]==33;assert next(x for x in A.inventory if x["family_id"]=="opener.strong-two-club-after-waiting")["production_calls_added"]==24
def test_untouched():assert len(A.untouched)==3;assert all(x["classification"]=="SOURCE_PARTIAL" and not x["obvious_complete_contract"] for x in A.untouched)
def test_routes_benchmark():assert A.routes["current"]==45;assert A.routes["audit_only_growth"]==0;assert A.benchmark=={"seeds":10000,"production_calls":7871,"completed":761,"abstained":9239,"phase12_default_calls_added":62,"policy_gated_available":123}
def test_deferred():assert len(A.deferred)==7;assert all(x["blocker"] for x in A.deferred)
def test_closure():assert not A.closure_gate;assert "PHASE 12 COMPLETE" in A.decision;assert A.phase13_recommendation.startswith("Phase 13")
def test_unchanged_deterministic():assert not A.production_defaults_changed;assert A.production_changes==A.knowledge_markdown_changed==0;assert A==run_phase12_coverage_closure_audit()
