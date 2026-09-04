from dataclasses import dataclass

import pytest

from bridge import (
    Auction, BiddingContext, BiddingEngine, BiddingEngineRouter, Call, EngineRoute,
    Hand, KnowledgeSource, RuleDecision, Seat, SystemContext, Vulnerability,
    auction_calls,
)


SRC=KnowledgeSource("bidding/systems/sayc","Opening Bid Requirements")


@dataclass(frozen=True)
class FixedRule:
    rule_id:str
    call:str
    def evaluate(self,context):
        candidate=Call.parse(self.call)
        if not context.auction.is_legal(candidate):
            return RuleDecision.not_applicable(self.rule_id,"illegal here")
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=candidate,
            explanation="fixture",sources=(SRC,),priority=1
        )


def engine(call):
    return BiddingEngine((FixedRule(f"fixture.{call}",call),))


def ctx(calls=()):
    return BiddingContext.create(
        hand=Hand.parse("AKQJ9.KQ3.JT8.32"),
        auction=Auction(Seat.NORTH,calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("SAYC"),
    )


def test_exact_auction_route_selects_existing_engine():
    router=BiddingEngineRouter((
        EngineRoute("opening",auction_calls(),engine("1S"),10),
    ))
    assert router.evaluate(ctx()).recommended_call.serialize()=="1S"


def test_different_auction_routes_to_different_existing_engine():
    router=BiddingEngineRouter((
        EngineRoute("opening",auction_calls(),engine("1S"),10),
        EngineRoute("after-pass",auction_calls("P"),engine("1H"),10),
    ))
    assert router.evaluate(ctx(("P",))).recommended_call.serialize()=="1H"


def test_no_match_and_no_fallback_abstains():
    router=BiddingEngineRouter(())
    assert not router.evaluate(ctx()).has_recommendation


def test_fallback_is_used_only_when_no_route_matches():
    router=BiddingEngineRouter((),fallback=engine("1C"))
    assert router.evaluate(ctx()).recommended_call.serialize()=="1C"


def test_higher_route_priority_wins():
    router=BiddingEngineRouter((
        EngineRoute("low",lambda c: True,engine("1C"),1),
        EngineRoute("high",lambda c: True,engine("1S"),5),
    ))
    match=router.match(ctx())
    assert match.route_id=="high"
    assert router.evaluate(ctx()).recommended_call.serialize()=="1S"


def test_equal_priority_uses_registration_order():
    router=BiddingEngineRouter((
        EngineRoute("first",lambda c: True,engine("1D"),5),
        EngineRoute("second",lambda c: True,engine("1S"),5),
    ))
    assert router.match(ctx()).route_id=="first"


def test_duplicate_route_ids_are_case_insensitive():
    with pytest.raises(ValueError):
        BiddingEngineRouter((
            EngineRoute("Opening",lambda c: True,engine("1C")),
            EngineRoute("opening",lambda c: True,engine("1D")),
        ))


def test_matcher_must_return_bool():
    router=BiddingEngineRouter((
        EngineRoute("bad",lambda c: 1,engine("1C")),
    ))
    with pytest.raises(TypeError):
        router.evaluate(ctx())


def test_auction_calls_is_mechanics_only_exact_match():
    matcher=auction_calls("1S","P")
    assert matcher(ctx(("1S","P")))
    assert not matcher(ctx(("1S","P","2C")))


def test_route_registry_snapshot_is_immutable():
    routes=[EngineRoute("opening",lambda c: True,engine("1C"))]
    router=BiddingEngineRouter(routes)
    routes.clear()
    assert len(router.routes)==1
