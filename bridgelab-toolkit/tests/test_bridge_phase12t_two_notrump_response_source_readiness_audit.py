# ruff: noqa: E701, E702
import inspect
from benchmarks.two_notrump_response_source_readiness_audit import run_two_notrump_response_source_readiness_audit
from bridge.sayc_route_configuration import create_standard_sayc_router
A=run_two_notrump_response_source_readiness_audit()
def test_population():assert (A.start_seed,A.deal_count,A.expected_population,A.population)==(1,10_000,33,33);assert {x["auction_prefix"] for x in A.positions}=={"2NT P"};assert {x["current_action"] for x in A.positions}=={"ABSTAIN"}
def test_partition():assert A.primary_partitions=={"exactly-one-four-card-major":15,"balanced-no-four-major":8,"both-majors-four-plus":4,"long-minor":3,"game-looking":1,"slam-interest-looking":1,"five-plus-hearts":1};assert sum(x["observed_count"] for x in A.source_matrix)==33
def test_methods():assert A.opening_semantics=={"natural":True,"hcp_range":"20-21","balanced_required":True};assert A.method_findings["stayman"]["source_defined"];assert A.method_findings["transfers"]["3D"]=="hearts";assert not A.method_findings["natural"]["3NT_complete"]
def test_routes():assert A.route_count==len(create_standard_sayc_router().routes)==45;assert {x["route_name"] for x in A.positions}=={"sayc.response.2nt.jacoby"};assert (A.production_rules_added,A.routes_added,A.policies_added)==(0,0,0);assert "EngineRoute(" not in inspect.getsource(__import__("benchmarks.two_notrump_response_source_readiness_audit",fromlist=["x"]))
def test_decision():assert A.source_safe_candidates==();assert A.decision=="E. DEFER 2NT RESPONSES";assert A.phase12u_recommendation["phase12m_population"]==693
def test_unchanged():assert not A.production_defaults_changed;assert A.knowledge_markdown_changed==0
def test_deterministic():assert A==run_two_notrump_response_source_readiness_audit()
