import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,Seat,SystemContext,Vulnerability
from bridge.support_double_eligibility_policy import *
from bridge.policy_registry import *
SRC=KnowledgeSource("bidding/conventions/doubles/support-double","Requirements")
def ctx(pid=None):
 opts={} if pid is None else {SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION:pid}
 return BiddingContext.create(hand=Hand.parse("KJ9.A74.KQ63.763"),auction=Auction(Seat.NORTH,("1D","P","1H","1S")),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))
class P:
 policy_id="fixture.support-double"
 def assess(self,c): return SupportDoubleEligibilityAssessment(self.policy_id,SupportDoubleEligibilityStatus.QUALIFIES,"fixture eligibility",(SRC,))
def test_explicit_qualification():
 assert assess_support_double_eligibility(P(),ctx()).status is SupportDoubleEligibilityStatus.QUALIFIES
def test_known_requires_trace():
 with pytest.raises(ValueError): SupportDoubleEligibilityAssessment("x",SupportDoubleEligibilityStatus.QUALIFIES)
def test_unknown_needs_no_invented_threshold():
 a=SupportDoubleEligibilityAssessment("x",SupportDoubleEligibilityStatus.UNKNOWN)
 assert a.status is SupportDoubleEligibilityStatus.UNKNOWN
def test_registry_has_no_default():
 reg=PolicyRegistry.from_support_double_eligibility_policies([P()])
 assert assess_configured_support_double_eligibility(ctx(),reg) is None
def test_registry_resolves_explicit_policy():
 reg=PolicyRegistry.from_support_double_eligibility_policies([P()])
 assert assess_configured_support_double_eligibility(ctx("fixture.support-double"),reg).status is SupportDoubleEligibilityStatus.QUALIFIES
def test_duplicate_policy_id_rejected():
 with pytest.raises(ValueError): PolicyRegistry.from_support_double_eligibility_policies([P(),P()])
def test_from_policies_combines_role():
 reg=PolicyRegistry.from_policies(support_double_eligibility_policies=[P()])
 assert reg.support_double_eligibility_policy("FIXTURE.SUPPORT-DOUBLE") is not None
