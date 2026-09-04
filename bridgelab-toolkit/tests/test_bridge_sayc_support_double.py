import pytest

from bridge import Auction, BiddingContext, Hand, KnowledgeSource, Seat, SystemContext, Vulnerability
from bridge.bidding_rules import evaluate_rule
from bridge.policy_registry import PolicyRegistry, SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION
from bridge.sayc_support_double import SaycSupportDoubleExampleRule
from bridge.support_double_eligibility_policy import (
    SupportDoubleEligibilityAssessment,
    SupportDoubleEligibilityStatus,
)

SRC = KnowledgeSource("bidding/conventions/doubles/support-double", "Requirements")

class Qualifies:
    policy_id = "fixture.support.ok"
    def assess(self, context):
        return SupportDoubleEligibilityAssessment(
            self.policy_id, SupportDoubleEligibilityStatus.QUALIFIES,
            "fixture qualifies unresolved Support Double conditions", (SRC,)
        )

class Rejects:
    policy_id = "fixture.support.no"
    def assess(self, context):
        return SupportDoubleEligibilityAssessment(
            self.policy_id, SupportDoubleEligibilityStatus.DOES_NOT_QUALIFY,
            "fixture rejects unresolved Support Double conditions", (SRC,)
        )

def ctx(calls, hand, policy_id="fixture.support.ok", system="SAYC"):
    return BiddingContext.create(
        hand=Hand.parse(hand),
        auction=Auction(Seat.NORTH, calls),
        vulnerability=Vulnerability.NONE,
        system=SystemContext.from_mapping(
            system, {SUPPORT_DOUBLE_ELIGIBILITY_POLICY_OPTION: policy_id}
        ),
    )

@pytest.mark.parametrize(
    "calls,hand",
    [
        (("1D","P","1H","1S"), "AK94.Q73.J62.843"),
        (("1C","P","1H","1S"), "AK94.Q73.J62.843"),
        (("1D","P","1S","2C"), "AQ7.K843.J62.943"),
        (("1H","P","1S","2D"), "AQ7.K843.J62.943"),
    ],
)
def test_frozen_example_slices_double(calls, hand):
    reg=PolicyRegistry.from_support_double_eligibility_policies([Qualifies()])
    d=evaluate_rule(SaycSupportDoubleExampleRule(reg),ctx(calls,hand))
    assert d.applicable and d.candidate.serialize()=="X"

def test_requires_exactly_three_support():
    reg=PolicyRegistry.from_support_double_eligibility_policies([Qualifies()])
    d=evaluate_rule(
        SaycSupportDoubleExampleRule(reg),
        ctx(("1D","P","1H","1S"),"AK94.Q873.J6.843")
    )
    assert not d.applicable

def test_no_configured_policy_abstains():
    reg=PolicyRegistry()
    d=evaluate_rule(
        SaycSupportDoubleExampleRule(reg),
        ctx(("1D","P","1H","1S"),"AK94.Q73.J62.843","missing")
    )
    assert not d.applicable

def test_rejected_policy_abstains():
    reg=PolicyRegistry.from_support_double_eligibility_policies([Rejects()])
    d=evaluate_rule(
        SaycSupportDoubleExampleRule(reg),
        ctx(("1D","P","1H","1S"),"AK94.Q73.J62.843","fixture.support.no")
    )
    assert not d.applicable

def test_non_source_example_abstains_even_with_three_support():
    reg=PolicyRegistry.from_support_double_eligibility_policies([Qualifies()])
    d=evaluate_rule(
        SaycSupportDoubleExampleRule(reg),
        ctx(("1C","P","1S","2H"),"AQ7.K843.J62.943")
    )
    assert not d.applicable

def test_non_sayc_abstains():
    reg=PolicyRegistry.from_support_double_eligibility_policies([Qualifies()])
    d=evaluate_rule(
        SaycSupportDoubleExampleRule(reg),
        ctx(("1D","P","1H","1S"),"AK94.Q73.J62.843",system="Other")
    )
    assert not d.applicable
