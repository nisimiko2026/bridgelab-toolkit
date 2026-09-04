from bridge import AbstentionReason,Auction,BiddingContext,PolicyRegistry,Seat,SystemContext,Vulnerability,create_standard_sayc_router,evaluate_with_abstention_diagnostic,generate_deal

def ctx(seed,calls=()):
    deal=generate_deal(seed); a=Auction(dealer=Seat.NORTH)
    for c in calls:a.add(c)
    return BiddingContext.create(hand=deal.hand(a.next_seat),auction=a,seat=a.next_seat,vulnerability=Vulnerability.NONE,system=SystemContext("SAYC"))

def test_no_route():
    d=evaluate_with_abstention_diagnostic(create_standard_sayc_router(PolicyRegistry()),ctx(1,("1C","P","1D","P","1H","P")))
    assert d.abstention.reason is AbstentionReason.NO_ROUTE and d.abstention.route_id is None

def test_routed_rejection_preserves_reasons():
    router=create_standard_sayc_router(PolicyRegistry())
    d=next(x for x in (evaluate_with_abstention_diagnostic(router,ctx(s)) for s in range(1,200)) if not x.result.has_recommendation)
    assert d.abstention.reason is AbstentionReason.ROUTED_NO_APPLICABLE_RULE
    assert d.abstention.route_id=="sayc.opening" and d.abstention.rejected_rules

def test_recommendation_has_no_abstention():
    router=create_standard_sayc_router(PolicyRegistry())
    d=next(x for x in (evaluate_with_abstention_diagnostic(router,ctx(s)) for s in range(1,200)) if x.result.has_recommendation)
    assert d.abstention is None
