import pytest
from bridge import (Auction,BiddingContext,Hand,KnowledgeSource,Seat,SystemContext,Vulnerability,
    JacobyContinuationStrengthAssessment,JacobyContinuationStrengthClass,
    assess_jacoby_continuation_strength,JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION,
    assess_configured_jacoby_continuation_strength)
from bridge.policy_registry import PolicyRegistry

SRC=KnowledgeSource("bidding/conventions/transfers/jacoby-transfers","Responder's Continuations")

def ctx(pid=None):
    opts={} if pid is None else {JACOBY_CONTINUATION_STRENGTH_POLICY_OPTION:pid}
    return BiddingContext.create(
        hand=Hand.parse("KJ974.842.63.Q63"),
        auction=Auction(Seat.NORTH,("1NT","P","2H","P","2S","P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping("SAYC",opts))

class P:
    policy_id="fixture.jacoby.weak"
    def assess(self,c):
        return JacobyContinuationStrengthAssessment(
            self.policy_id,JacobyContinuationStrengthClass.WEAK,
            "Explicit benchmark/partnership classification.",(SRC,))

def test_explicit_classification():
    r=assess_jacoby_continuation_strength(P(),ctx())
    assert r.strength_class is JacobyContinuationStrengthClass.WEAK

def test_known_requires_trace():
    with pytest.raises(ValueError):
        JacobyContinuationStrengthAssessment("x",JacobyContinuationStrengthClass.GAME_GOING)

def test_unknown_needs_no_source():
    r=JacobyContinuationStrengthAssessment("x",JacobyContinuationStrengthClass.UNKNOWN)
    assert r.strength_class is JacobyContinuationStrengthClass.UNKNOWN

def test_registry_has_no_default():
    reg=PolicyRegistry.from_jacoby_continuation_strength_policies([P()])
    assert assess_configured_jacoby_continuation_strength(ctx(),reg) is None

def test_registry_resolves_explicit_policy():
    reg=PolicyRegistry.from_jacoby_continuation_strength_policies([P()])
    r=assess_configured_jacoby_continuation_strength(ctx("fixture.jacoby.weak"),reg)
    assert r.strength_class is JacobyContinuationStrengthClass.WEAK

def test_from_policies_supports_role():
    reg=PolicyRegistry.from_policies(jacoby_continuation_strength_policies=[P()])
    assert reg.jacoby_continuation_strength_policy("FIXTURE.JACOBY.WEAK") is not None

def test_no_hcp_boundary_embedded():
    assert {x.name for x in JacobyContinuationStrengthClass} == {"WEAK","INVITATIONAL","GAME_GOING","SLAM_INTEREST","UNKNOWN"}
