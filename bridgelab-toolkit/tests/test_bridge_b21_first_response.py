"""B2.1 integration boundaries; existing rules remain the bidding authority."""
from dataclasses import FrozenInstanceError, dataclass, replace
from itertools import combinations, product

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_engine import BiddingEngine
from bridge.bidding_rules import KnowledgeSource, RuleDecision
from bridge.engine_router import BiddingEngineRouter, EngineRoute, auction_calls
from bridge.evaluation import evaluate_hand
from bridge.first_response import FirstResponseDisposition as D, assess_first_response
from bridge.models import Hand, Seat, Suit, Vulnerability
from bridge.nisim_nily_partnership_profile import NISIM_NILY_PROFILE
from bridge.partnership_profiles import (
    AgreementResolution as R, AgreementSelection, AgreementSourceScope as Scope,
    PartnershipProfile, ResolvedAgreement,
)
from bridge.policy_registry import PolicyRegistry
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.suit_quality_policy import SuitQualityAssessment
from bridge.system_profiles import SystemProfile

SAYC = PartnershipProfile('test-partnership','1',SystemProfile.SAYC,())


def hand(shape, hcp):
    """Exact objective fixtures, with no suit-quality assumptions."""
    patterns = [p for n in range(5) for p in combinations('AKQJ',n)]
    options = [[p for p in patterns if len(p)<=length] for length in shape]
    for suits in product(*options):
        if sum({'A':4,'K':3,'Q':2,'J':1}[r] for p in suits for r in p)==hcp:
            cards=Hand.parse('.'.join(''.join(p)+'T98765432'[:n-len(p)] or '-' for p,n in zip(suits,shape)))
            assert evaluate_hand(cards).hcp==hcp
            return cards
    raise AssertionError('invalid HCP/shape fixture')


def assess(opening,cards,*,profile=SAYC,calls=None,dealer=Seat.NORTH,**kwargs):
    return assess_first_response(cards,auction=Auction(dealer,calls or (opening,'P')),
        vulnerability=Vulnerability.NONE,profile=profile,**kwargs)


def selected(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


def option(family,treatment):
    return replace(SAYC,agreements=(AgreementSelection(family,R.ENABLE,treatment),))


@pytest.mark.parametrize('opening',('1C','1D','1H','1S'))
@pytest.mark.parametrize('hcp',(0,5))
def test_weak_pass_boundaries(opening,hcp):
    result=assess(opening,hand((3,3,3,4),hcp))
    assert selected(result)=='P' and result.disposition is D.RECOMMENDED
    assert result.selected.sources


@pytest.mark.parametrize('opening',('1C','1D'))
@pytest.mark.parametrize('hcp',(6,12,25))
def test_six_plus_major_response_has_no_invented_upper_limit(opening,hcp):
    assert selected(assess(opening,hand((3,4,3,3),hcp)))=='1H'


@pytest.mark.parametrize('opening,shape,expected',[
    ('1C',(4,4,3,2),None), ('1D',(4,4,3,2),'1H'),
    ('1C',(4,5,2,2),'1H'), ('1C',(5,4,2,2),'1S'),
    ('1C',(2,2,5,4),'1D'), ('1C',(2,2,4,5),None),
    ('1C',(3,3,4,3),'1D'), ('1C',(3,3,3,4),'1NT'),
    ('1D',(4,3,3,3),'1S'), ('1D',(3,3,4,3),None),
])
def test_major_minor_length_and_choice_boundaries(opening,shape,expected):
    assert selected(assess(opening,hand(shape,6)))==expected


@pytest.mark.parametrize('hcp,expected',[(5,'P'),(6,'1NT'),(10,'1NT'),(11,None)])
def test_club_notrump_strength_boundaries(hcp,expected):
    assert selected(assess('1C',hand((3,3,3,4),hcp)))==expected


@pytest.mark.parametrize('hcp,expected',[(9,None),(10,'2NT'),(12,'2NT'),(13,'3NT'),(15,'3NT'),(16,None)])
def test_diamond_notrump_strength_and_meaning(hcp,expected):
    result=assess('1D',hand((3,3,3,4),hcp))
    assert selected(result)==expected
    if expected=='2NT':
        assert 'invit' in result.selected.explanation.lower()
    if expected=='3NT':
        assert 'game' in result.selected.explanation.lower()


@pytest.mark.parametrize('opening,shape', [('1H',(2,4,3,4)),('1S',(4,2,3,4))])
@pytest.mark.parametrize('hcp,level',[(5,'P'),(6,'2'),(9,'2'),(10,'3'),(12,'3'),(13,None)])
def test_major_raise_hcp_boundaries_and_limit_meaning(opening,shape,hcp,level):
    result=assess(opening,hand(shape,hcp))
    expected=level+opening[1] if level in ('2','3') else level
    assert selected(result)==expected
    if level=='3':
        assert 'limit' in result.selected.explanation.lower()


@pytest.mark.parametrize('opening,shape,expected',[
    ('1H',(4,3,3,3),'2H'), ('1H',(4,2,3,4),'1S'),
    ('1H',(3,2,4,4),None), ('1S',(3,4,3,3),'2S'),
    ('1S',(2,4,3,4),None),
])
def test_support_length_and_support_before_other_major(opening,shape,expected):
    assert selected(assess(opening,hand(shape,6)))==expected


@pytest.mark.parametrize('opening,shape',[('1H',(3,2,4,4)),('1S',(2,3,4,4))])
@pytest.mark.parametrize('treatment',('forcing','nonforcing'))
@pytest.mark.parametrize('hcp,expected',[(5,'P'),(6,'1NT'),(9,'1NT'),(10,None)])
def test_major_nt_treatment_and_strength(opening,shape,treatment,hcp,expected):
    result=assess(opening,hand(shape,hcp),profile=option('response.major.1nt',treatment))
    assert selected(result)==expected
    if expected=='1NT':
        assert f'as {treatment}' in result.selected.explanation


@pytest.mark.parametrize('opening,bid_h,bid_s',[('1NT','2D','2H'),('2NT','3D','3H')])
@pytest.mark.parametrize('shape,target',[((3,4,3,3),None),((3,5,3,2),'H'),((5,3,3,2),'S'),((2,6,3,2),'H'),((5,5,2,1),None)])
@pytest.mark.parametrize('hcp',(0,15))
def test_nt_first_transfer_lengths_any_strength(opening,bid_h,bid_s,shape,target,hcp):
    assert selected(assess(opening,hand(shape,hcp)))==({'H':bid_h,'S':bid_s}.get(target))


@pytest.mark.parametrize('hcp',(0,5,12,25))
def test_strong_two_club_waiting_meaning_is_preserved(hcp):
    result=assess('2C',hand((4,3,3,3),hcp))
    assert selected(result)=='2D'
    assert 'waiting' in result.selected.explanation


@pytest.mark.parametrize('opening',('2D','2H','2S','3C','3D','3H','3S','4C','4D'))
def test_unimplemented_multi_weak_two_preempt_responses_abstain(opening):
    result=assess(opening,hand((4,3,3,3),12))
    assert result.disposition is D.ABSTAIN and result.route_id is None
    assert selected(result) is None


@pytest.mark.parametrize('opening',('2D','2NT'))
def test_nisim_nily_artificial_openings_do_not_borrow_natural_sayc(opening):
    result=assess(opening,hand((5,3,3,2),10),profile=NISIM_NILY_PROFILE)
    assert result.disposition is D.ABSTAIN and result.engine_result is None
    assert any('opening.'+opening.lower() in b for b in result.blockers)


class FixtureQuality:
    policy_id='fixture.b21.quality'
    def assess(self,context,suit):
        return SuitQualityAssessment.qualifies(self.policy_id,suit,context.evaluation.quality_evidence(suit),
            'Fixture only: explicitly qualified.',(KnowledgeSource('bidding/systems/2-over-1'),))


@pytest.mark.parametrize('opening,shape,expected',[
    ('1H',(3,2,3,5),'2C'),('1H',(3,2,5,3),'2D'),
    ('1S',(2,3,3,5),'2C'),('1S',(2,3,5,3),'2D'),
    ('1H',(4,2,2,5),None),('1H',(2,3,3,5),None),
    ('1H',(3,2,4,4),None),('1H',(2,1,5,5),None),
])
@pytest.mark.parametrize('hcp',(11,12))
def test_nisim_nily_existing_gf_slice_requires_all_gates(opening,shape,expected,hcp):
    result=assess(opening,hand(shape,hcp),profile=NISIM_NILY_PROFILE,
        registry=PolicyRegistry.from_suit_quality_policies([FixtureQuality()]),
        suit_quality_policy_id=FixtureQuality.policy_id)
    assert selected(result)==(expected if hcp==12 else None)
    assert result.context.system.system=='TWO_OVER_ONE_GF'
    if result.selected:
        assert 'Game Force' in result.selected.explanation and result.selected.sources


def test_missing_quality_policy_remains_abstention():
    result=assess('1H',hand((3,2,3,5),12),profile=NISIM_NILY_PROFILE)
    assert result.disposition is D.ABSTAIN
    assert any('quality' in x.explanation for x in result.engine_result.decisions)


@pytest.mark.parametrize('opening',('1C','1D','1H','1S','1NT','2C','2NT'))
def test_system_identity_alone_does_not_enable_sayc_or_gf(opening):
    profile=replace(SAYC,base_system=SystemProfile.TWO_OVER_ONE_GF)
    result=assess(opening,hand((3,5,3,2),6),profile=profile)
    assert selected(result) is None


def test_resolver_override_parameters_provenance_and_isolation():
    default=ResolvedAgreement('response.major.1nt','nonforcing',R.INHERIT,Scope.SYSTEM)
    profile=replace(option('response.major.1nt','forcing'),sources=('test-source',))
    result=assess('1H',hand((3,2,4,4),7),profile=profile,base_agreements=(default,))
    assert selected(result)=='1NT' and result.context.system.option('forcing_one_notrump')=='forcing'
    assert result.profile.agreement('response.major.1nt').source_scope is Scope.PARTNERSHIP
    assert result.profile.sources==('test-source',)
    other=assess('1H',hand((3,2,4,4),7),base_agreements=(default,))
    assert other.context.system.option('forcing_one_notrump')=='nonforcing'
    altered=replace(profile,agreements=(replace(profile.agreements[0],parameters=(('hcp_min','8'),)),))
    blocked=assess('1H',hand((3,2,4,4),7),profile=altered,base_agreements=(default,))
    assert selected(blocked) is None
    assert blocked.profile.agreement('response.major.1nt').parameters==(('hcp_min','8'),)


@pytest.mark.parametrize('resolution',(R.ENABLE,R.DISABLE))
def test_bergen_or_disabled_raise_never_restores_traditional_raise(resolution):
    treatment='bergen' if resolution is R.ENABLE else None
    profile=replace(SAYC,agreements=(AgreementSelection('response.major.raises',resolution,treatment),))
    result=assess('1H',hand((2,4,3,4),10),profile=profile)
    assert selected(result) is None


def test_unknown_relevant_treatment_blocks_but_other_opening_does_not():
    unknown=option('response.minor.raises','inverted')
    assert selected(assess('1C',hand((3,4,3,3),6),profile=unknown)) is None
    unrelated=option('opening.2d','multi_2d')
    assert selected(assess('1C',hand((3,4,3,3),6),profile=unrelated))=='1H'


@pytest.mark.parametrize('calls', [('1C',),('1C','P','1H','P'),('1NT','P','2D','P','2H','P')])
def test_only_first_responder_call_is_accepted(calls):
    with pytest.raises(ValueError,match='first call'):
        assess('1C',hand((4,3,3,3),6),calls=calls)


@pytest.mark.parametrize('calls',[('P','1C','P'),('1C','X'),('1C','1H')])
def test_passed_hand_or_interference_remains_unsupported(calls):
    result=assess('1C',hand((4,3,3,3),6),calls=calls)
    assert result.disposition is D.ABSTAIN and result.route_id is None


@pytest.mark.parametrize('dealer',tuple(Seat))
def test_seat_orientation_determinism_immutability_and_core_facts(dealer):
    cards=hand((3,4,3,3),6)
    first=assess('1C',cards,dealer=dealer)
    second=assess('1C',cards,dealer=dealer)
    assert first.selected==second.selected and selected(first)=='1H'
    assert first.engine_result==second.engine_result
    assert first.profile==second.profile and first.blockers==second.blockers
    assert first.disposition is second.disposition and first.reason==second.reason
    assert first.context.auction.serialize()==second.context.auction.serialize()
    assert first.context.evaluation==evaluate_hand(cards)
    assert first.context.seat is dealer.partner()
    with pytest.raises(FrozenInstanceError):
        first.opening='2C'


@dataclass(frozen=True)
class FixtureRule:
    rule_id: str
    call: str
    priority: int
    def evaluate(self,context):
        return RuleDecision.recommend(rule_id=self.rule_id,candidate=Call.parse(self.call),
            explanation='Test conflict.',sources=(KnowledgeSource('test-only'),),priority=self.priority)


@pytest.mark.parametrize('priority,call,expected',[(100,'1S',None),(90,'1S','1H'),(100,'1H','1H')])
def test_single_response_or_explicit_equal_priority_conflict(monkeypatch,priority,call,expected):
    import bridge.first_response as module
    engine=BiddingEngine((FixtureRule('a','1H',100),FixtureRule('b',call,priority)))
    router=BiddingEngineRouter((EngineRoute('sayc.response.1c',auction_calls('1C','P'),engine),))
    monkeypatch.setattr(module,'create_standard_sayc_router',lambda registry:router)
    result=assess('1C',hand((3,4,3,3),6))
    assert selected(result)==expected
    if expected is None:
        assert result.disposition is D.CONFLICT and result.blockers==('a','b')
    assert len(result.engine_result.decisions)==2


def test_existing_router_outcome_and_priorities_are_preserved():
    router=create_standard_sayc_router()
    before=tuple((r.route_id,r.priority,r.policy_dependencies) for r in router.routes)
    assert len(before)==47
    for opening in ('1C','1D','1H','1S','1NT','2C','2D','2NT','3D'):
        for hcp in (0,5,6,9,10,12,13,15):
            result=assess(opening,hand((3,3,4,3),hcp))
            original=router.evaluate(result.context)
            assert result.recommended_call==original.recommended_call
            if result.engine_result is not None:
                assert result.engine_result==original
    assert before==tuple((r.route_id,r.priority,r.policy_dependencies) for r in create_standard_sayc_router().routes)