"""B2.2 checks the existing second-call meanings and composition boundary."""
from dataclasses import FrozenInstanceError, dataclass, replace
from itertools import combinations, product

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import KnowledgeSource, RuleDecision
from bridge.engine_router import BiddingEngineRouter, EngineRoute, auction_calls
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.opener_rebid import OpenerRebidDisposition as D, assess_opener_rebid
from bridge.partnership_profiles import (
    AgreementResolution as R, AgreementSelection, AgreementSourceScope as Scope,
    PartnershipProfile, ResolvedAgreement,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.stayman_dual_major_response_policy import (
    StaymanDualMajorResponse as Choice, StaymanDualMajorResponseAssessment,
)
from bridge.system_profiles import SystemProfile

SAYC=PartnershipProfile('rebid-test','1',SystemProfile.SAYC,())


def hand(shape,hcp):
    patterns=[p for n in range(5) for p in combinations('AKQJ',n)]
    for suits in product(*[[p for p in patterns if len(p)<=n] for n in shape]):
        if sum({'A':4,'K':3,'Q':2,'J':1}[r] for p in suits for r in p)==hcp:
            cards=Hand.parse('.'.join(''.join(p)+'T98765432'[:n-len(p)] or '-' for p,n in zip(suits,shape)))
            assert evaluate_hand(cards).hcp==hcp
            return cards
    raise AssertionError('invalid fixture')


def assess(opening,response,cards,*,profile=SAYC,calls=None,dealer=Seat.NORTH,**kwargs):
    return assess_opener_rebid(cards,auction=Auction(dealer,calls or (opening,'P',response,'P')),
        vulnerability=Vulnerability.NONE,profile=profile,**kwargs)


def call(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('opening,response,shape',[
    ('1C','1D',(3,3,2,5)),('1C','1H',(3,3,2,5)),
    ('1C','1S',(3,3,2,5)),('1D','1H',(3,3,5,2)),
    ('1D','1S',(3,3,5,2)),('1H','1S',(3,5,3,2)),
])
@pytest.mark.parametrize('hcp,expected',[(11,None),(12,'1NT'),(14,'1NT'),(15,None)])
def test_minimum_notrump_boundaries(opening,response,shape,hcp,expected):
    assert call(assess(opening,response,hand(shape,hcp)))==expected


@pytest.mark.parametrize('opening,shape',[('1C',(3,3,2,5)),('1D',(3,3,5,2)),('1H',(3,5,3,2))])
@pytest.mark.parametrize('hcp,expected',[(17,None),(18,'2NT'),(19,'2NT'),(20,None)])
def test_existing_jump_notrump_range(opening,shape,hcp,expected):
    result=assess(opening,'1S',hand(shape,hcp))
    assert call(result)==expected
    if expected:
        assert '18-19' in result.selected.explanation and result.selected.sources


@pytest.mark.parametrize('opening,response,shape,expected',[
    ('1C','1H',(2,4,2,5),'2H'),('1C','1S',(4,2,2,5),'2S'),
    ('1D','1H',(2,4,5,2),'2H'),('1D','1S',(4,2,5,2),'2S'),
    ('1C','1H',(4,4,1,4),'2H'), # support beats other major
    ('1H','1S',(4,5,2,2),None), # known support branch is not executable here
])
def test_support_responder_existing_lengths_and_priority(opening,response,shape,expected):
    assert call(assess(opening,response,hand(shape,13)))==expected


@pytest.mark.parametrize('opening,response,shape,expected',[
    ('1C','1D',(3,2,2,6),'2C'),('1C','1H',(3,2,2,6),'2C'),
    ('1C','1S',(3,2,2,6),'2C'),('1D','1H',(3,2,6,2),'2D'),
    ('1D','1S',(3,2,6,2),'2D'),('1H','1S',(3,6,2,2),'2H'),
    ('1C','1S',(3,3,2,5),None),('1D','1S',(3,3,5,2),None),
    ('1H','1S',(3,5,3,2),None),
])
def test_own_suit_six_card_boundary(opening,response,shape,expected):
    assert call(assess(opening,response,hand(shape,15)))==expected


@pytest.mark.parametrize('opening,response,shape,expected',[
    ('1C','1D',(4,4,1,4),'1H'), ('1C','1D',(4,3,1,5),'1S'),
    ('1C','1H',(4,3,1,5),'1S'), ('1C','1S',(2,2,4,5),'2D'),
    ('1D','1H',(4,2,5,2),'1S'), ('1D','1H',(2,2,5,4),'2C'),
    ('1D','1S',(2,2,5,4),'2C'), ('1H','1S',(2,5,4,2),'2D'),
    ('1H','1S',(1,4,4,4),None), # unknown multiple second-suit choice
    ('1H','1S',(2,5,2,4),None), # unimplemented club branch blocks a fallback
])
def test_existing_second_suit_and_overlap_gaps(opening,response,shape,expected):
    assert call(assess(opening,response,hand(shape,13)))==expected


@pytest.mark.parametrize('opening,shape',[('1C',(2,4,2,5)),('1D',(2,4,5,2))])
@pytest.mark.parametrize('hcp,expected',[(15,None),(16,'2H'),(20,'2H')])
def test_reverse_strength_boundary_and_original_meaning(opening,shape,hcp,expected):
    result=assess(opening,'1S',hand(shape,hcp))
    assert call(result)==expected
    if expected:
        assert 'reverse' in result.selected.explanation.lower()
        assert any('Reverse' in (s.heading or '') for s in result.selected.sources)


@pytest.mark.parametrize('opening,shape',[('1C',(2,4,3,4)),('1D',(2,4,4,3))])
def test_reverse_requires_opening_minor_strictly_longer(opening,shape):
    assert call(assess(opening,'1S',hand(shape,16))) is None


@pytest.mark.parametrize('opening,shape',[('1H',(3,5,3,2)),('1S',(5,3,3,2))])
@pytest.mark.parametrize('hcp,expected',[(11,None),(12,'P'),(14,'P'),(15,None),(18,None)])
def test_simple_raise_minimum_pass_and_invitational_gap(opening,shape,hcp,expected):
    result=assess(opening,'2'+opening[1],hand(shape,hcp))
    assert call(result)==expected
    if expected:
        assert '6-9' in result.selected.explanation and 'minimum' in result.selected.explanation


@pytest.mark.parametrize('opening,response,shape,expected',[
    ('1S','2C',(5,2,4,2),'2D'),('1H','2D',(4,5,2,2),'2S'),
    ('1S','2C',(5,2,2,4),'3C'),('1S','2C',(6,2,3,2),'2S'),
    ('1S','2C',(6,1,4,2),'2D'), # second suit before own suit
    ('1S','2C',(6,1,2,4),'3C'), # support before own suit
    ('1S','2C',(5,3,3,2),None),('1H','2D',(3,5,3,2),None), # no numeric balanced-GF rule
    ('1S','2C',(5,4,4,0),None),('1H','2C',(3,5,3,2),None),('1S','2D',(5,3,3,2),None),
])
def test_established_nisim_nily_gf_shape_priorities(opening,response,shape,expected):
    result=assess(opening,response,hand(shape,13),profile=NISIM_NILY_PROFILE)
    assert call(result)==expected
    assert result.context.system.system=='TWO_OVER_ONE_GF'
    if expected:
        assert result.selected.sources
        assert result.profile.agreement('response.major.two_over_one').source_scope is Scope.PARTNERSHIP


@pytest.mark.parametrize('opening,response,expected',[
    ('1NT','2D','2H'),('1NT','2H','2S'),('2NT','3D','3H'),
    ('2NT','3H','3S'),('2NT','4D','4H'),('2NT','4H','4S'),
])
def test_existing_transfer_and_texas_acceptance(opening,response,expected):
    result=assess(opening,response,hand((3,3,4,3),16))
    assert call(result)==expected and result.selected.sources


@pytest.mark.parametrize('opening,response,level',[('1NT','2C','2'),('2NT','3C','3')])
@pytest.mark.parametrize('shape,suit', [((3,3,4,3),'D'),((3,4,3,3),'H'),((4,3,3,3),'S'),((4,4,3,2),None)])
def test_existing_stayman_length_boundaries(opening,response,level,shape,suit):
    assert call(assess(opening,response,hand(shape,16)))==(level+suit if suit else None)


@dataclass(frozen=True)
class StaymanFixture:
    response: Choice
    policy_id: str='test.b22.stayman'
    def assess(self,context):
        return StaymanDualMajorResponseAssessment(self.policy_id,self.response,'Explicit test preference.',
            (KnowledgeSource('test-only/stayman'),))


@pytest.mark.parametrize('choice,expected',[(Choice.HEARTS,'2H'),(Choice.SPADES,'2S'),(Choice.UNKNOWN,None)])
def test_existing_explicit_stayman_policy(choice,expected):
    policy=StaymanFixture(choice)
    registry=PolicyRegistry.from_stayman_dual_major_response_policies((policy,))
    result=assess('1NT','2C',hand((4,4,3,2),16),registry=registry,
        stayman_dual_major_response_policy_id=policy.policy_id)
    assert call(result)==expected
    if expected:
        assert any(s.article_id=='test-only/stayman' for s in result.selected.sources)
    # The 1NT preference is not a new 2NT convention.
    assert call(assess('2NT','3C',hand((4,4,3,2),20),registry=registry,
        stayman_dual_major_response_policy_id=policy.policy_id)) is None


@pytest.mark.parametrize('hcp,expected',[(21,None),(22,'2NT'),(24,'2NT'),(25,None)])
def test_strong_two_club_balanced_rebid_boundaries(hcp,expected):
    assert call(assess('2C','2D',hand((4,3,3,3),hcp)))==expected


def test_strong_two_club_unbalanced_gap():
    assert call(assess('2C','2D',hand((6,3,2,2),23))) is None


@pytest.mark.parametrize('opening,response',[('2D','2H'),('2H','2NT'),('2S','3S'),('3C','3H'),('3D','3NT'),('1S','1NT')])
def test_no_new_multi_preempt_or_missing_continuations(opening,response):
    result=assess(opening,response,hand((4,3,3,3),13))
    assert result.disposition is D.ABSTAIN and result.route_id is None


@pytest.mark.parametrize('calls',[
    ('1C','P'), ('1C','P','1H','P','2H','P'),
    ('1C','1D','1H','P'), ('1C','P','1H','1S'),
    ('1C','X','1H','P'), ('1C','P','1H','X'),
])
def test_reject_responder_and_competitive_positions(calls):
    with pytest.raises(ValueError):
        assess('1C','1H',hand((3,4,2,4),13),calls=calls)


@pytest.mark.parametrize('passes',(1,2,3))
def test_passed_auction_not_normalized_into_a_route(passes):
    result=assess('1C','1H',hand((3,4,2,4),13),calls=('P',)*passes+('1C','P','1H','P'))
    assert result.disposition is D.ABSTAIN and result.route_id is None


@pytest.mark.parametrize('opening,response',[('1C','1H'),('1D','1S'),('1NT','2D'),('2C','2D'),('2NT','3D')])
def test_nisim_nily_never_impersonates_sayc(opening,response):
    assert call(assess(opening,response,hand((3,4,3,3),23),profile=NISIM_NILY_PROFILE)) is None


@pytest.mark.parametrize('family,treatment', [
    ('response.major.raises','bergen'),('opener.rebid.1h','unknown'),
    ('opening.1h','artificial'),('rebid.1h','new-meaning'),
])
def test_partnership_overrides_block_unimplemented_meanings(family,treatment):
    profile=replace(SAYC,agreements=(AgreementSelection(family,R.ENABLE,treatment),))
    assert call(assess('1H','2H',hand((3,5,3,2),13),profile=profile)) is None
    assert call(assess('1H','2H',hand((3,5,3,2),13)))=='P'


@pytest.mark.parametrize('family',('response.major.raises','response.major.two_over_one'))
def test_disabled_treatment_does_not_reappear(family):
    profile=replace(SAYC,agreements=(AgreementSelection(family,R.DISABLE),))
    opening,response,shape=('1H','2H',(3,5,3,2)) if family.endswith('raises') else ('1S','2C',(5,2,4,2))
    assert call(assess(opening,response,hand(shape,13),profile=profile)) is None


def test_base_resolution_override_and_parameter_provenance():
    base=ResolvedAgreement('response.major.two_over_one','game_force',R.INHERIT,Scope.SYSTEM)
    cards=hand((5,2,4,2),13)
    inherited=assess('1S','2C',cards,base_agreements=(base,))
    assert call(inherited)=='2D'
    assert inherited.profile.agreement(base.family).source_scope is Scope.SYSTEM
    profile=replace(SAYC,agreements=(AgreementSelection(base.family,R.REPLACE,'natural'),))
    assert call(assess('1S','2C',cards,profile=profile,base_agreements=(base,))) is None
    profile=replace(profile,agreements=(AgreementSelection(base.family,R.REPLACE,'game_force',(('min_hcp','16'),)),))
    blocked=assess('1S','2C',cards,profile=profile,base_agreements=(base,))
    assert call(blocked) is None
    assert blocked.profile.agreement(base.family).parameters==(('min_hcp','16'),)


@pytest.mark.parametrize('dealer',tuple(Seat))
def test_deterministic_immutable_and_core_evaluation(dealer):
    cards=hand((3,2,2,6),13)
    first=assess('1C','1H',cards,dealer=dealer)
    second=assess('1C','1H',cards,dealer=dealer)
    assert first.selected==second.selected and first.engine_result==second.engine_result
    assert first.reason==second.reason and call(first)=='2C'
    assert first.context.seat is dealer and first.context.evaluation==evaluate_hand(cards)
    with pytest.raises(FrozenInstanceError):
        first.selected=None


@dataclass(frozen=True)
class FixtureRule:
    rule_id: str
    bid: str
    priority: int
    def evaluate(self,context):
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse(self.bid),
            explanation='Fixture rule.',sources=(KnowledgeSource('test-only'),),priority=self.priority)


@pytest.mark.parametrize('bid,priority,expected',[('2H',100,None),('2H',90,'2C'),('2C',100,'2C')])
def test_single_result_and_explicit_conflict(monkeypatch,bid,priority,expected):
    import bridge.opener_rebid as module
    engine=BiddingEngine((FixtureRule('a','2C',100),FixtureRule('b',bid,priority)))
    router=BiddingEngineRouter((EngineRoute('sayc.opener.fixture',auction_calls('1C','P','1H','P'),engine),))
    monkeypatch.setattr(module,'create_standard_sayc_router',lambda registry:router)
    result=assess('1C','1H',hand((3,2,2,6),13))
    assert call(result)==expected
    assert len(result.engine_result.decisions)==2
    if expected is None:
        assert result.disposition is D.CONFLICT


def test_all_existing_opener_routes_preserve_engine_evidence_and_production_count():
    router=create_standard_sayc_router()
    before=tuple((r.route_id,r.priority,r.policy_dependencies) for r in router.routes)
    assert len(before)==47
    pairs=[('1C','1D'),('1C','1H'),('1C','1S'),('1D','1H'),('1D','1S'),
           ('1H','1S'),('1H','2H'),('1S','2S'),('1H','2C'),('1H','2D'),('1S','2C'),('1S','2D'),
           ('1NT','2D'),('1NT','2H'),('1NT','2C'),('2NT','3D'),('2NT','3H'),('2NT','3C'),
           ('2NT','4D'),('2NT','4H'),('2C','2D')]
    covered=set()
    for opening,response in pairs:
        for shape in ((3,3,4,3),(5,2,4,2),(2,4,2,5)):
            result=assess(opening,response,hand(shape,13))
            original=router.evaluate(result.context)
            assert result.engine_result==original
            assert result.recommended_call==original.recommended_call
            covered.add(result.route_id)
    assert covered=={r.route_id for r in router.routes if r.route_id.startswith(('sayc.opener.','sayc.2over1.opener.'))}
    assert before==tuple((r.route_id,r.priority,r.policy_dependencies) for r in create_standard_sayc_router().routes)