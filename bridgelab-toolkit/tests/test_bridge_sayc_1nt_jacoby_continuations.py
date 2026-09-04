import pytest
from bridge import (
    Auction, BiddingContext, Hand, KnowledgeSource, Seat, SystemContext, Vulnerability,
    JacobyContinuationStrengthAssessment, JacobyContinuationStrengthClass,
    JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_1nt_jacoby import create_sayc_one_notrump_jacoby_continuation_engine
from bridge.sayc_route_configuration import create_standard_sayc_router

SRC=KnowledgeSource("bidding/conventions/transfers/jacoby-transfers","Responder's Continuations")

class Fixed:
    def __init__(self, cls):
        self.cls=cls
        self.policy_id=f"fixture.jacoby.{cls.value}"
    def assess(self, context):
        if self.cls is JacobyContinuationStrengthClass.UNKNOWN:
            return JacobyContinuationStrengthAssessment(self.policy_id,self.cls)
        return JacobyContinuationStrengthAssessment(
            self.policy_id,self.cls,"Explicit partnership classification.",(SRC,))

def ctx(calls,pid=None):
    opts={} if pid is None else {JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION:pid}
    return BiddingContext.create(
        hand=Hand.parse("KJ974.842.63.Q63"), auction=Auction(Seat.NORTH,calls),
        vulnerability=Vulnerability.NONE, system=SystemContext.from_mapping("SAYC",opts))

def call(engine,c):
    d=engine.evaluate(c)
    return None if d.recommended_call is None else d.recommended_call.serialize()

@pytest.mark.parametrize("cls,expected",[
    (JacobyContinuationStrengthClass.WEAK,"P"),
    (JacobyContinuationStrengthClass.INVITATIONAL,"2NT"),
    (JacobyContinuationStrengthClass.GAME_GOING,"4H"),
    (JacobyContinuationStrengthClass.SLAM_INTEREST,None),
    (JacobyContinuationStrengthClass.UNKNOWN,None),
])
def test_hearts_transfer_mapping(cls,expected):
    p=Fixed(cls); reg=PolicyRegistry.from_jacoby_continuation_strength_policies([p])
    e=create_sayc_one_notrump_jacoby_continuation_engine(reg)
    assert call(e,ctx(("1NT","P","2D","P","2H","P"),p.policy_id))==expected

def test_game_going_spades_maps_to_four_spades():
    p=Fixed(JacobyContinuationStrengthClass.GAME_GOING)
    reg=PolicyRegistry.from_jacoby_continuation_strength_policies([p])
    e=create_sayc_one_notrump_jacoby_continuation_engine(reg)
    assert call(e,ctx(("1NT","P","2H","P","2S","P"),p.policy_id))=="4S"

def test_missing_policy_abstains():
    e=create_sayc_one_notrump_jacoby_continuation_engine(PolicyRegistry())
    assert call(e,ctx(("1NT","P","2D","P","2H","P"))) is None

def test_unregistered_configured_policy_abstains():
    e=create_sayc_one_notrump_jacoby_continuation_engine(PolicyRegistry())
    assert call(e,ctx(("1NT","P","2D","P","2H","P"),"missing")) is None

def test_router_has_both_continuation_routes():
    r=create_standard_sayc_router()
    assert r.match(ctx(("1NT","P","2D","P","2H","P"))).route_id=="sayc.responder.1nt.jacoby.hearts.continuation"
    assert r.match(ctx(("1NT","P","2H","P","2S","P"))).route_id=="sayc.responder.1nt.jacoby.spades.continuation"
