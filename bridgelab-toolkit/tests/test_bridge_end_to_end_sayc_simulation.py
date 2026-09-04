"""End-to-end Phase 6D tests use complete, physically valid 52-card deals.

Opponent engines are intentionally explicit-pass fixture engines so the test
isolates the production SAYC chain under audit.  North/South use the real
standard SAYC router and real production bidding rules.
"""

from dataclasses import dataclass

from bridge import (
    Auction, BiddingEngine, Call, ControlledAuctionSimulator, Hand, KnowledgeSource,
    PolicyRegistry, RuleDecision, Seat, SimulationStopReason, Suit,
    SuitQualityAssessment, SystemContext, create_standard_sayc_router,
)


FIXTURE_SOURCE=KnowledgeSource("bidding/systems/sayc","Opening Bid Requirements")
QUALITY_SOURCE=KnowledgeSource("bidding/systems/2-over-1","Hands Suitable for a 2/1 Response")


@dataclass(frozen=True)
class PassRule:
    rule_id:str
    def evaluate(self,context):
        return RuleDecision.recommend(
            rule_id=self.rule_id,candidate=Call.pass_(),
            explanation="Phase 6D opponent-pass fixture",
            sources=(FIXTURE_SOURCE,),priority=1,
        )


@dataclass(frozen=True)
class FixtureQualityPolicy:
    policy_id:str="phase6d-fixture-quality"
    def assess(self,context,suit):
        evidence=context.evaluation.quality_evidence(suit)
        return SuitQualityAssessment.qualifies(
            self.policy_id,suit,evidence,
            "Phase 6D fixture explicitly accepts the selected suit so the test can exercise the already-existing policy-aware 2/1 rule.",
            (QUALITY_SOURCE,),
        )


def pass_engine(side):
    return BiddingEngine((PassRule(f"phase6d.fixture.pass.{side}"),))


def systems(options=None):
    system=SystemContext.from_mapping("SAYC",options or {})
    return {seat:system for seat in Seat}


def simulator(hands,options=None,registry=None):
    router=create_standard_sayc_router(registry)
    return ControlledAuctionSimulator(
        hands=hands,
        engines={
            Seat.NORTH:router,
            Seat.EAST:pass_engine("east"),
            Seat.SOUTH:router,
            Seat.WEST:pass_engine("west"),
        },
        systems=systems(options),
    )


def test_real_deal_opening_response_then_exact_unsupported_rebid_stop():
    # N: 1H production opening. S: 2H production raise. After W passes,
    # N faces 1H-P-2H-P, which Phase 6C deliberately does not route.
    hands={
        Seat.NORTH:Hand.parse("AK2.AKJ98.Q32.76"),
        Seat.EAST:Hand.parse("QJ97.432.AJ8.J98"),
        Seat.SOUTH:Hand.parse("T86.QT7.9764.KQ3"),
        Seat.WEST:Hand.parse("543.65.KT5.AT542"),
    }
    result=simulator(hands).simulate(Auction(Seat.NORTH))
    assert result.final_auction=="1H P 2H P"
    assert result.stop_reason is SimulationStopReason.NO_RECOMMENDATION
    assert result.stopped_seat is Seat.NORTH
    assert [s.rule_id for s in result.steps[:3]]==[
        "sayc.opening.1h",
        "phase6d.fixture.pass.east",
        "sayc.response.1h.2h",
    ]


def test_real_deal_two_over_one_chain_reaches_production_opener_rebid():
    # N opens 1S. S has 12+ HCP, <3 spades, 5+ clubs strictly longer than
    # diamonds, and an explicit quality policy, so the existing 2/1 rule bids
    # 2C. N then has 4 diamonds and <4 hearts, so the existing opener-rebid
    # rule bids 2D. The next unsupported position is East after that call.
    hands={
        Seat.NORTH:Hand.parse("AKQJ9.82.KQJ8.76"),
        Seat.EAST:Hand.parse("T7653.QJT9.32.98"),
        Seat.SOUTH:Hand.parse("82.AK7.AT4.KQJ54"),
        Seat.WEST:Hand.parse("4.6543.9765.AT32"),
    }
    policy=FixtureQualityPolicy()
    registry=PolicyRegistry.from_suit_quality_policies((policy,))
    options={"two_over_one":"game_force","suit_quality_policy":policy.policy_id}
    result=simulator(hands,options,registry).simulate(Auction(Seat.NORTH))
    assert result.final_auction=="1S P 2C P 2D P"
    assert result.stop_reason is SimulationStopReason.NO_RECOMMENDATION
    assert result.stopped_seat is Seat.SOUTH
    ids=[step.rule_id for step in result.steps]
    assert ids[0]=="sayc.opening.1s"
    assert "sayc.response.1s.2c.2over1" in ids
    assert "sayc.2over1.opener.1s.2c.2d" in ids


def test_same_two_over_one_deal_stops_at_responder_without_explicit_quality_policy():
    hands={
        Seat.NORTH:Hand.parse("AKQJ9.82.KQJ8.76"),
        Seat.EAST:Hand.parse("T7653.QJT9.32.98"),
        Seat.SOUTH:Hand.parse("82.AK7.AT4.KQJ54"),
        Seat.WEST:Hand.parse("4.6543.9765.AT32"),
    }
    options={"two_over_one":"game_force"}
    result=simulator(hands,options,PolicyRegistry()).simulate(Auction(Seat.NORTH))
    assert result.final_auction=="1S P"
    assert result.stop_reason is SimulationStopReason.NO_RECOMMENDATION
    assert result.stopped_seat is Seat.SOUTH


def test_trace_preserves_canonical_sources_across_production_steps():
    hands={
        Seat.NORTH:Hand.parse("AK2.AKJ98.Q32.76"),
        Seat.EAST:Hand.parse("QJ97.432.AJ8.J98"),
        Seat.SOUTH:Hand.parse("T86.QT7.9764.KQ3"),
        Seat.WEST:Hand.parse("543.65.KT5.AT542"),
    }
    result=simulator(hands).simulate(Auction(Seat.NORTH))
    north_open=result.steps[0]
    south_response=result.steps[2]
    assert north_open.sources
    assert south_response.sources
    assert any(source.article_id=="bidding/systems/sayc" for source in north_open.sources)
    assert any(source.article_id for source in south_response.sources)
