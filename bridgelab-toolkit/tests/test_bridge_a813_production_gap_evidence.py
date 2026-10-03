from bridge.production_gap_evidence import EvidenceClass,classify_production_gap_evidence

def test_empty():
    r=classify_production_gap_evidence(count=0)
    assert r.abstained==0 and r.cases==() and r.groups==()

def test_accounting():
    r=classify_production_gap_evidence(count=1000)
    assert r.completed+r.abstained==r.runs==1000
    assert sum(g.count for g in r.groups)==r.abstained

def test_every_abstention_classified_once():
    r=classify_production_gap_evidence(count=100)
    assert len(r.cases)==r.abstained

def test_no_route_means_missing_route():
    r=classify_production_gap_evidence(count=1000)
    xs=[x for x in r.cases if x.case.diagnostic.reason.value=="no-route"]
    assert xs and all(x.evidence_class is EvidenceClass.MISSING_ROUTE for x in xs)

def test_opening_route_is_review_not_policy_gap():
    r=classify_production_gap_evidence(count=1000)
    xs=[x for x in r.cases if x.case.depth==0]
    assert xs and all(x.evidence_class is EvidenceClass.OPENING_PASS_REVIEW for x in xs)

def test_other_routed_rejections():
    r=classify_production_gap_evidence(count=1000)
    xs=[x for x in r.cases if x.case.depth>0 and x.case.diagnostic.reason.value=="routed-no-applicable-rule"]
    assert xs and all(x.evidence_class is EvidenceClass.ROUTED_RULE_REJECTION for x in xs)

def test_seed_provenance():
    r=classify_production_gap_evidence(count=100)
    assert all(g.count==len(g.seeds) for g in r.groups)

def test_shares():
    r=classify_production_gap_evidence(count=100)
    assert abs(sum(g.share_of_abstentions for g in r.groups)-1)<1e-12

def test_deterministic():
    assert classify_production_gap_evidence(count=100)==classify_production_gap_evidence(count=100)

def test_no_policy_gap_or_engine_defect_claim():
    r=classify_production_gap_evidence(count=0)
    assert all(x not in EvidenceClass.__members__ for x in ("POLICY_GAP","ENGINE_DEFECT"))

def test_no_priority_surface():
    r=classify_production_gap_evidence(count=0)
    for n in ("priority","rank","winner","score","correct","accuracy"):
        assert not hasattr(r,n)

def test_1000_case_gate():
    r=classify_production_gap_evidence(count=1000)
    assert r.abstained==925
