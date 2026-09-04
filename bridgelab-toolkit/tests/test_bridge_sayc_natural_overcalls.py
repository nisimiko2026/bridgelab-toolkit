from bridge import Auction, BiddingContext, Hand, KnowledgeSource, PolicyRegistry, Seat, Suit, SuitQualityAssessment, SuitQualityStatus, PlayingStrengthAssessment, PlayingStrengthStatus, SystemContext, Vulnerability
from bridge.policy_registry import SUIT_QUALITY_POLICY_OPTION, PLAYING_STRENGTH_POLICY_OPTION
from bridge.sayc_natural_overcalls import SaycNaturalOneLevelOvercallRule, legal_one_level_overcall_suits
from bridge.auction import Strain

SOURCE=KnowledgeSource("bidding/systems/sayc","Natural Overcalls")

class Quality:
    policy_id="fixture-quality"
    def __init__(self,status=SuitQualityStatus.QUALIFIES): self.status=status
    def assess(self,context,suit):
        e=context.evaluation.quality_evidence(suit)
        if self.status is SuitQualityStatus.UNKNOWN:
            return SuitQualityAssessment.unknown(self.policy_id,suit,e)
        if self.status is SuitQualityStatus.DOES_NOT_QUALIFY:
            return SuitQualityAssessment.does_not_qualify(self.policy_id,suit,e,"fixture rejects",(SOURCE,))
        return SuitQualityAssessment.qualifies(self.policy_id,suit,e,"fixture qualifies",(SOURCE,))

class Strength:
    policy_id="fixture-strength"
    def __init__(self,status=PlayingStrengthStatus.QUALIFIES): self.status=status
    def assess(self,context):
        if self.status is PlayingStrengthStatus.UNKNOWN:
            return PlayingStrengthAssessment.unknown(self.policy_id)
        if self.status is PlayingStrengthStatus.DOES_NOT_QUALIFY:
            return PlayingStrengthAssessment.does_not_qualify(self.policy_id,"fixture rejects",(SOURCE,))
        return PlayingStrengthAssessment.qualifies(self.policy_id,"fixture qualifies",(SOURCE,))

def ctx(hand,opening="1D",quality=True,strength=True):
    opts={}
    if quality: opts[SUIT_QUALITY_POLICY_OPTION]="fixture-quality"
    if strength: opts[PLAYING_STRENGTH_POLICY_OPTION]="fixture-strength"
    return BiddingContext.create(hand=Hand.parse(hand),auction=Auction(Seat.NORTH,(opening,)),vulnerability=Vulnerability.NONE,system=SystemContext.from_mapping("SAYC",opts))

def rule(qstatus=SuitQualityStatus.QUALIFIES,sstatus=PlayingStrengthStatus.QUALIFIES):
    return SaycNaturalOneLevelOvercallRule(PolicyRegistry.from_policies(
        suit_quality_policies=[Quality(qstatus)],
        playing_strength_policies=[Strength(sstatus)],
    ))

def test_legal_one_level_suits_are_mechanical():
    assert legal_one_level_overcall_suits(Strain.CLUBS)==(Suit.DIAMONDS,Suit.HEARTS,Suit.SPADES)
    assert legal_one_level_overcall_suits(Strain.DIAMONDS)==(Suit.HEARTS,Suit.SPADES)
    assert legal_one_level_overcall_suits(Strain.HEARTS)==(Suit.SPADES,)
    assert legal_one_level_overcall_suits(Strain.SPADES)==()

def test_qualifying_1s_over_1d_is_recommended_when_both_policies_qualify():
    d=rule().evaluate(ctx("AKQ97.J82.64.532"))
    assert d.applicable
    assert d.candidate == __import__("bridge").Call.parse("1S")

def test_no_policy_abstains_before_playing_strength():
    d=rule().evaluate(ctx("AKQ97.J82.64.532",quality=False))
    assert not d.applicable
    assert "suit-quality" in d.explanation

def test_unknown_quality_abstains():
    d=rule(qstatus=SuitQualityStatus.UNKNOWN).evaluate(ctx("AKQ97.J82.64.532"))
    assert not d.applicable
    assert "suit-quality" in d.explanation

def test_outside_hcp_range_abstains():
    d=rule().evaluate(ctx("KQJ97.982.64.532"))
    assert not d.applicable
    assert "8–17" in d.explanation

def test_1s_opening_has_no_legal_one_level_suit_overcall():
    d=rule().evaluate(ctx("AKQ97.J82.64.532",opening="1S"))
    assert not d.applicable
    assert "No legally available" in d.explanation

def test_missing_playing_strength_policy_abstains():
    d=rule().evaluate(ctx("AKQ97.J82.64.532",strength=False))
    assert not d.applicable
    assert "playing-strength" in d.explanation

def test_unknown_playing_strength_abstains():
    d=rule(sstatus=PlayingStrengthStatus.UNKNOWN).evaluate(ctx("AKQ97.J82.64.532"))
    assert not d.applicable
    assert "playing-strength" in d.explanation

def test_rejected_playing_strength_abstains():
    d=rule(sstatus=PlayingStrengthStatus.DOES_NOT_QUALIFY).evaluate(ctx("AKQ97.J82.64.532"))
    assert not d.applicable
    assert "does not qualify" in d.explanation
