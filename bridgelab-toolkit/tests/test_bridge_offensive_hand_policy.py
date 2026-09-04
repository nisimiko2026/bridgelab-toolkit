import pytest
from bridge import Auction,BiddingContext,Hand,KnowledgeSource,OffensiveHandAssessment,OffensiveHandStatus,Seat,SystemContext,Vulnerability,assess_offensive_hand
SOURCE=KnowledgeSource("bidding/systems/sayc","Weak Jump Overcalls")
def context():
    return BiddingContext.create(hand=Hand.parse("KQJ983.7.J82.Q63"),auction=Auction(Seat.NORTH,("1D",)),vulnerability=Vulnerability.NONE,system=SystemContext("SAYC"))
class Policy:
    policy_id="fixture.offense"
    def __init__(self,status=OffensiveHandStatus.QUALIFIES): self.status=status
    def assess(self,c):
        if self.status is OffensiveHandStatus.UNKNOWN:return OffensiveHandAssessment.unknown(self.policy_id)
        if self.status is OffensiveHandStatus.QUALIFIES:return OffensiveHandAssessment.qualifies(self.policy_id,"fixture qualifies",(SOURCE,))
        return OffensiveHandAssessment.does_not_qualify(self.policy_id,"fixture rejects",(SOURCE,))
def test_three_outcomes():
    assert assess_offensive_hand(Policy(),context()).qualifies_offense is True
    assert assess_offensive_hand(Policy(OffensiveHandStatus.DOES_NOT_QUALIFY),context()).qualifies_offense is False
    assert assess_offensive_hand(Policy(OffensiveHandStatus.UNKNOWN),context()).qualifies_offense is None
def test_known_requires_source_and_explanation():
    with pytest.raises(ValueError): OffensiveHandAssessment.qualifies("x","", (SOURCE,))
    with pytest.raises(ValueError): OffensiveHandAssessment.qualifies("x","yes", ())
def test_wrong_result_rejected():
    class Bad:
        policy_id="bad"
        def assess(self,c): return True
    with pytest.raises(TypeError): assess_offensive_hand(Bad(),context())
