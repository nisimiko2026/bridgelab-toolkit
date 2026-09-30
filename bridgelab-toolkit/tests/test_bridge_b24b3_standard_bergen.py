"""Approved B2.4B3 Nisim-Nily card activation, not generic Bergen defaults."""
from dataclasses import replace
from itertools import combinations, product

import pytest

from bridge.auction import Auction
from bridge.bergen_raises import (
    BERGEN_FAMILY, BergenConfigurationError, BergenStatus,
    assess_bergen_response, resolve_bergen_agreement,
)
from bridge.evaluation import evaluate_hand
from bridge.first_response import FirstResponseDisposition, assess_first_response
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_jacoby_2nt import assess_jacoby_2nt_response
from bridge.nisim_nily_partnership_profile import (
    BERGEN_STANDARD_APPROVAL, JACOBY_2NT_PARAMETERS, NISIM_NILY_BERGEN_PROFILE,
    NISIM_NILY_BERGEN_PROFILE_B24B2, NISIM_NILY_PROFILE,
)
from bridge.opener_rebid import assess_opener_rebid
from bridge.partnership_profiles import (
    AgreementSourceScope, PartnershipProfile,
)
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile

PROFILE = NISIM_NILY_BERGEN_PROFILE


def hand(opening, hcp, support):
    shape = (support,3,3,7-support) if opening=='1S' else (3,support,3,7-support)
    patterns = [p for n in range(5) for p in combinations('AKQJ',n)]
    for suits in product(*[[p for p in patterns if len(p)<=n] for n in shape]):
        if sum({'A':4,'K':3,'Q':2,'J':1}[r] for p in suits for r in p)==hcp:
            result = Hand.parse('.'.join(''.join(p)+'T98765432'[:n-len(p)] or '-'
                                        for p,n in zip(suits,shape)))
            assert evaluate_hand(result).hcp==hcp
            return result
    raise AssertionError('Invalid fixture')


def assess(api, opening='1S', hcp=10, support=4, profile=PROFILE, calls=None, dealer=Seat.NORTH):
    return api(hand(opening,hcp,support),auction=Auction(dealer,calls or (opening,'P')),
               vulnerability=Vulnerability.NONE,profile=profile)


def selected(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('opening',('1H','1S'))
@pytest.mark.parametrize('hcp',(0,5,6,7,9,10,12,13,16))
@pytest.mark.parametrize('support',(2,3,4,5,6))
def test_approved_partition_boundaries_have_one_or_no_outcome(opening,hcp,support):
    # Explicit user-approved partition; especially HCP 6 separates by support.
    expected = None
    if 0<=hcp<=6 and support>=4: expected='3D'
    elif 6<=hcp<=9 and support==3: expected='2'+opening[-1]
    elif 7<=hcp<=9 and support==4: expected='3'+opening[-1]
    elif 10<=hcp<=12 and support>=4: expected='3C'
    elif hcp>=13 and support>=4: expected='2NT'
    bergen=assess(assess_bergen_response,opening,hcp,support)
    jacoby=assess(assess_jacoby_2nt_response,opening,hcp,support)
    candidates=[c for c in (selected(bergen),selected(jacoby)) if c is not None]
    assert candidates == ([expected] if expected else [])
    first=assess(assess_first_response,opening,hcp,support)
    assert selected(first)==expected and first.route_id is None
    assert first.disposition is (FirstResponseDisposition.RECOMMENDED if expected
                                 else FirstResponseDisposition.ABSTAIN)
    if expected=='2NT':
        assert bergen.status is BergenStatus.DEFER_TO_JACOBY
        assert jacoby.meaning.artificial and jacoby.meaning.game_forcing
    if expected:
        assert first.selected.sources and not first.blockers


@pytest.mark.parametrize('call,meaning,hcp,support,artificial,forcing',[
    ('2M','simple natural raise',(6,9),(3,3),False,'nonforcing'),
    ('3C','Bergen limit raise',(10,12),(4,13),True,'invitational'),
    ('3D','Bergen preemptive raise',(0,6),(4,13),True,'nonforcing'),
    ('3M','mixed natural raise',(7,9),(4,4),False,'nonforcing'),
])
def test_exact_card_meanings_and_provenance(call,meaning,hcp,support,artificial,forcing):
    agreement=resolve_bergen_agreement(PROFILE)
    branch=next(b for b in agreement.branches if b.call==call)
    assert branch.enabled and branch.meaning==meaning
    assert branch.hcp==hcp and branch.support==support
    assert branch.artificial is artificial and branch.forcing==forcing
    assert agreement.source.source_scope is AgreementSourceScope.PARTNERSHIP
    own=next(a for a in PROFILE.agreements if a.family==BERGEN_FAMILY)
    assert agreement.source.parameters==own.parameters
    assert agreement.profile.sources==PROFILE.sources
    assert BERGEN_STANDARD_APPROVAL in PROFILE.sources
    assert own.option('variant')=='STANDARD'
    assert own.option('competition')=='UNCONTESTED_ONLY'
    assert agreement.jacoby_source.parameters==JACOBY_2NT_PARAMETERS


@pytest.mark.parametrize('calls', [('1H','1S'),('1S','X'),('1H','2C'),('P','1S','P')])
@pytest.mark.parametrize('hcp',(6,10,13))
def test_intervention_or_unsupported_passed_hand_prefix_abstains(calls,hcp):
    opening=next(c for c in calls if c in ('1H','1S'))
    for api in (assess_bergen_response,assess_first_response,assess_jacoby_2nt_response):
        assert selected(assess(api,opening,hcp,4,calls=calls)) is None


@pytest.mark.parametrize('opening',('1H','1S'))
@pytest.mark.parametrize('response',('2M','3C','3D','3M'))
def test_no_bergen_opener_continuation_is_added(opening,response):
    result=assess(assess_opener_rebid,opening,12,4,
        calls=(opening,'P',response.replace('M',opening[-1]),'P'))
    assert selected(result) is None


@pytest.mark.parametrize('opening',('1H','1S'))
def test_sayc_and_other_partnerships_are_unchanged(opening):
    sayc=PartnershipProfile('unchanged-sayc','1',SystemProfile.SAYC,())
    other=PartnershipProfile('unconfigured-pair','1',SystemProfile.TWO_OVER_ONE_GF,())
    assert selected(assess(assess_first_response,opening,10,4,profile=sayc))=='3'+opening[-1]
    for profile in (sayc,other,NISIM_NILY_PROFILE):
        assert selected(assess(assess_bergen_response,opening,10,4,profile=profile)) is None
    assert selected(assess(assess_first_response,opening,10,4,profile=other)) is None
    # Sharing a system, or a name without the agreement, cannot activate Bergen.
    same_name=replace(other,profile_id=PROFILE.profile_id)
    assert selected(assess(assess_first_response,opening,10,4,profile=same_name)) is None


@pytest.mark.parametrize('dealer',tuple(Seat))
@pytest.mark.parametrize('hcp',(6,8,11,13))
def test_deterministic_selection_and_seat_orientation(dealer,hcp):
    a=assess(assess_first_response,hcp=hcp,dealer=dealer)
    b=assess(assess_first_response,hcp=hcp,dealer=dealer)
    assert a.selected==b.selected and a.reason==b.reason and a.profile==b.profile
    assert a.context.seat is dealer.partner()
    assert a.context.evaluation==evaluate_hand(a.context.hand)
    assert a.production_adopted is False


def test_standard_label_does_not_override_explicit_card_mapping():
    own=next(a for a in PROFILE.agreements if a.family==BERGEN_FAMILY)
    p=dict(own.parameters)
    p['three_clubs.call'],p['three_diamonds.call']='3D','3C'
    different=replace(PROFILE,profile_id='explicit-other-card',agreements=tuple(
        replace(a,parameters=tuple(p.items())) if a.family==BERGEN_FAMILY else a
        for a in PROFILE.agreements))
    assert selected(assess(assess_bergen_response,hcp=11,profile=different))=='3D'
    assert selected(assess(assess_bergen_response,hcp=11))=='3C'


def test_competitive_card_request_is_rejected_not_silently_ignored():
    own=next(a for a in PROFILE.agreements if a.family==BERGEN_FAMILY)
    p=dict(own.parameters); p['competition']='COMPETITIVE'
    invalid=replace(PROFILE,agreements=tuple(replace(a,parameters=tuple(p.items()))
        if a.family==BERGEN_FAMILY else a for a in PROFILE.agreements))
    with pytest.raises(BergenConfigurationError,match='UNCONTESTED_ONLY'):
        resolve_bergen_agreement(invalid)


def test_incomplete_historical_card_and_production_inventory_preserved():
    assert NISIM_NILY_BERGEN_PROFILE_B24B2.version=='B2.4B2'
    assert assess(assess_bergen_response,profile=NISIM_NILY_BERGEN_PROFILE_B24B2).status is BergenStatus.CONFIGURATION_INCOMPLETE
    assert len(create_standard_sayc_router().routes)==45
