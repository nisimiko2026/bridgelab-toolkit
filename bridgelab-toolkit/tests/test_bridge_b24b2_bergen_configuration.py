"""Synthetic cards exercise configuration mechanics, not approved Bergen variants."""
from dataclasses import FrozenInstanceError, replace
from itertools import combinations, product
from pathlib import Path

import pytest

from bridge.auction import Auction
from bridge.bergen_raises import (
    BERGEN_FAMILY, BERGEN_RAISES, BergenConfigurationError,
    BergenConfigurationIncomplete, BergenStatus as S,
    assess_bergen_response, resolve_bergen_agreement,
)
from bridge.evaluation import evaluate_hand
from bridge.models import Hand, Seat, Vulnerability
from bridge.nisim_nily_jacoby_2nt import assess_jacoby_2nt_response
from bridge.nisim_nily_partnership_profile import (
    NISIM_NILY_PROFILE, NISIM_NILY_BERGEN_PROFILE_B24B2, NISIM_NILY_JACOBY_2NT_PROFILE,
)
from bridge.partnership_profiles import (
    AgreementResolution as R, AgreementSelection, AgreementSourceScope as Scope,
    PartnershipProfile, ResolvedAgreement,
)
from bridge.profile_compiler import compile_profile_plan
from bridge.sayc_route_configuration import create_standard_sayc_router
from bridge.system_profiles import SystemProfile

CARD = 'bidding/convention-cards/test-bergen-a'
SLOTS = ('simple_raise', 'three_clubs', 'three_diamonds', 'three_major')


def parameters(*, swapped=False, relationship='disabled', policy='exclusive'):
    # These are arbitrary TEST ranges and labels. No partnership defaults.
    p = dict(card_source=CARD, strength_metric='hcp', branch_policy=policy,
             jacoby_relationship=relationship)
    for slot, call, meaning, lo, hi, support in (
        ('simple_raise', '2M', 'fixture simple', 6, 9, (3, 3)),
        ('three_clubs', '3C', 'fixture invitation', 10, 12, (4, 5)),
        ('three_diamonds', '3D', 'fixture constructive', 6, 9, (4, 5)),
        ('three_major', '3M', 'fixture weak', 0, 5, (4, 5)),
    ):
        if swapped and call in ('3C', '3D'):
            call = '3D' if call == '3C' else '3C'
        for key, value in dict(call=call, enabled='true', meaning=meaning,
            min_hcp=str(lo), max_hcp=str(hi), min_support=str(support[0]),
            max_support=str(support[1]), artificial=str(call in ('3C', '3D')).lower(),
            forcing='invitational' if meaning == 'fixture invitation' else 'nonforcing').items():
            p[f'{slot}.{key}'] = value
    if relationship != 'disabled':
        p['jacoby_treatment'] = 'fixture_jacoby'
    return p


def card(p=None, *, identity='test-a', base=SystemProfile.TWO_OVER_ONE_GF, jacoby=False):
    p = parameters() if p is None else p
    agreements = (AgreementSelection(BERGEN_FAMILY, R.ENABLE, BERGEN_RAISES, tuple(p.items())),)
    if jacoby:
        agreements += (AgreementSelection('response.major.2nt', R.ENABLE, 'fixture_jacoby',
                                         (('min_hcp', '13'), ('min_support', '4'))),)
    return PartnershipProfile(identity, 'fixture-1', base, agreements, (CARD,))


def hand(opening, hcp, support=4):
    shape = (support, 3, 3, 7-support) if opening == '1S' else (3, support, 3, 7-support)
    patterns = [p for n in range(5) for p in combinations('AKQJ', n)]
    for suits in product(*[[p for p in patterns if len(p) <= n] for n in shape]):
        if sum({'A': 4, 'K': 3, 'Q': 2, 'J': 1}[r] for p in suits for r in p) == hcp:
            result = Hand.parse('.'.join(''.join(p) + 'T98765432'[:n-len(p)] or '-'
                                        for p, n in zip(suits, shape)))
            assert evaluate_hand(result).hcp == hcp
            return result
    raise AssertionError('invalid fixture')


def assess(profile, opening='1S', hcp=10, support=4, *, calls=None, **kwargs):
    return assess_bergen_response(hand(opening, hcp, support),
        auction=Auction(Seat.NORTH, calls or (opening, 'P')),
        vulnerability=Vulnerability.NONE, profile=profile, **kwargs)


def selected(result):
    return None if result.recommended_call is None else result.recommended_call.serialize()


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('hcp,standard,swapped', [(6, '3D', '3C'), (9, '3D', '3C'),
                                               (10, '3C', '3D'), (12, '3C', '3D')])
def test_two_partnerships_resolve_swapped_minor_mappings(opening, hcp, standard, swapped):
    a, b = card(), card(parameters(swapped=True), identity='test-b')
    first, second = assess(a, opening, hcp), assess(b, opening, hcp)
    assert selected(first) == standard and selected(second) == swapped
    assert first.meaning.meaning == second.meaning.meaning
    assert first.agreement.convention == second.agreement.convention == BERGEN_RAISES
    assert selected(assess(a, opening, hcp)) == standard


@pytest.mark.parametrize('opening', ('1H', '1S'))
@pytest.mark.parametrize('hcp,support,expected', [(0,4,'3M'), (5,4,'3M'), (6,3,'2M'),
    (9,3,'2M'), (10,3,None), (6,2,None), (10,5,'3C'), (10,6,None), (13,4,None)])
def test_card_boundaries_and_explicit_abstention(opening, hcp, support, expected):
    result = assess(card(), opening, hcp, support)
    assert selected(result) == (expected.replace('M', opening[-1]) if expected else None)
    if expected:
        assert result.meaning.forcing and result.selected.sources
    else:
        assert result.status is S.ABSTAIN


@pytest.mark.parametrize('slot', SLOTS)
def test_explicit_disabled_branches_do_not_gain_defaults(slot):
    p = {k:v for k,v in parameters().items() if not k.startswith(slot + '.')}
    p[slot+'.call'] = dict(zip(SLOTS, ('2M','3C','3D','3M')))[slot]
    p[slot+'.enabled'] = 'false'
    agreement = resolve_bergen_agreement(card(p))
    assert not agreement.branches[SLOTS.index(slot)].enabled
    hcp, support = {'simple_raise':(6,3), 'three_clubs':(10,4),
                    'three_diamonds':(6,4), 'three_major':(0,4)}[slot]
    assert selected(assess(card(p), hcp=hcp, support=support)) is None


@pytest.mark.parametrize('key', ['card_source','strength_metric','branch_policy','jacoby_relationship',
    'three_clubs.call','three_clubs.enabled','three_clubs.meaning','three_clubs.min_hcp',
    'three_clubs.max_hcp','three_clubs.min_support','three_clubs.max_support',
    'three_clubs.artificial','three_clubs.forcing'])
def test_missing_required_mapping_is_incomplete_and_never_executable(key):
    p=parameters(); del p[key]
    with pytest.raises(BergenConfigurationIncomplete):
        resolve_bergen_agreement(card(p))
    result=assess(card(p))
    assert result.status is S.CONFIGURATION_INCOMPLETE and selected(result) is None
    assert key in result.reason


@pytest.mark.parametrize('key,value', [('three_clubs.call','3D'),
    ('three_clubs.min_hcp','13'), ('three_clubs.max_hcp','38'),
    ('three_clubs.max_support','14'), ('three_clubs.min_support','6'),
    ('three_clubs.enabled','maybe'), ('three_clubs.artificial','yes'),
    ('three_clubs.forcing','undefined'), ('three_clubs.min_hcp','10.0'),
    ('strength_metric','support_points'), ('branch_policy','registration_order'),
    ('jacoby_relationship','guess'), ('unknown_parameter','true')])
def test_conflicting_impossible_or_unsupported_parameters_rejected(key,value):
    p=parameters(); p[key]=value
    with pytest.raises(BergenConfigurationError):
        assess(card(p))


def test_physically_impossible_hcp_support_rectangle_rejected():
    p=parameters(); p.update({'three_clubs.min_support':'13','three_clubs.max_support':'13',
                             'three_clubs.min_hcp':'11','three_clubs.max_hcp':'12'})
    with pytest.raises(BergenConfigurationError, match='Impossible HCP/support'):
        resolve_bergen_agreement(card(p))


def test_exclusive_overlap_rejected_but_nonexclusive_conflict_has_no_arbitrary_winner():
    p=parameters(); p['three_diamonds.max_hcp']='10'
    with pytest.raises(BergenConfigurationError, match='Overlapping exclusive'):
        resolve_bergen_agreement(card(p))
    p['branch_policy']='conflict'
    result=assess(card(p))
    assert result.status is S.CONFLICT and selected(result) is None


@pytest.mark.parametrize('profile', (NISIM_NILY_PROFILE,NISIM_NILY_JACOBY_2NT_PROFILE,NISIM_NILY_BERGEN_PROFILE_B24B2))
def test_nisim_nily_uses_only_its_incomplete_card_not_generic_or_base_defaults(profile):
    base=(ResolvedAgreement(BERGEN_FAMILY,BERGEN_RAISES,R.ENABLE,Scope.SYSTEM,tuple(parameters().items())),)
    result=assess(profile,base_agreements=base)
    assert result.status is S.CONFIGURATION_INCOMPLETE and selected(result) is None
    effective=result.profile.agreement(BERGEN_FAMILY)
    own=next(a for a in profile.agreements if a.family == BERGEN_FAMILY)
    assert effective.parameters == own.parameters and effective.source_scope is Scope.PARTNERSHIP


def test_new_nisim_card_records_source_fragments_without_filling_in_ranges():
    agreement=next(a for a in NISIM_NILY_BERGEN_PROFILE_B24B2.agreements if a.family == BERGEN_FAMILY)
    p=dict(agreement.parameters)
    assert agreement.treatment_id == BERGEN_RAISES
    assert (p['simple_raise.min_hcp'],p['simple_raise.max_hcp']) == ('8','10')
    assert p['three_major.meaning'] == 'weak raise' and p['three_major.min_support'] == '4'
    assert 'three_clubs.min_hcp' not in p and 'three_diamonds.meaning' not in p
    assert 'three_major.max_hcp' not in p


@pytest.mark.parametrize('relationship', ('disjoint','defer_to_jacoby'))
def test_separate_jacoby_eligibility_is_resolved_and_preserved(relationship):
    p=parameters(relationship=relationship)
    result=assess(card(p,jacoby=True),hcp=13)
    assert selected(result) is None
    assert result.status is (S.DEFER_TO_JACOBY if relationship == 'defer_to_jacoby' else S.ABSTAIN)
    assert result.agreement.jacoby_source.parameters == (('min_hcp','13'),('min_support','4'))
    assert selected(assess(card(p,jacoby=True),hcp=12)) == '3C'


def test_explicit_jacoby_precedence_suppresses_overlapping_bergen():
    p=parameters(relationship='disjoint'); p['three_clubs.max_hcp']='15'
    with pytest.raises(BergenConfigurationError,match='Bergen/Jacoby overlap'):
        resolve_bergen_agreement(card(p,jacoby=True))
    p['jacoby_relationship']='defer_to_jacoby'
    assert assess(card(p,jacoby=True),hcp=14).status is S.DEFER_TO_JACOBY


@pytest.mark.parametrize('case', ('missing','mismatch','disabled'))
def test_jacoby_relationship_must_match_separate_treatment(case):
    p=parameters(relationship='disjoint')
    if case=='mismatch': p['jacoby_treatment']='different'
    if case=='disabled':
        p['jacoby_relationship']='disabled'; del p['jacoby_treatment']
    with pytest.raises(BergenConfigurationError):
        resolve_bergen_agreement(card(p,jacoby=case!='missing'))


@pytest.mark.parametrize('opening', ('1H','1S'))
def test_complete_synthetic_nisim_card_coexists_with_existing_jacoby_assessor(opening):
    # A test-only completion, never a new Nisim-Nily production agreement.
    p=parameters(relationship='defer_to_jacoby')
    p['jacoby_treatment']='nisim_nily_jacoby_2nt'
    p['card_source']='bidding/convention-cards/cc-nily-nisim'
    profile=replace(NISIM_NILY_JACOBY_2NT_PROFILE,agreements=tuple(
        replace(a,treatment_id=BERGEN_RAISES,parameters=tuple(p.items()))
        if a.family==BERGEN_FAMILY else a for a in NISIM_NILY_JACOBY_2NT_PROFILE.agreements))
    assert selected(assess(profile,opening,hcp=12))=='3C'
    assert assess(profile,opening,hcp=13).status is S.DEFER_TO_JACOBY
    result=assess_jacoby_2nt_response(hand(opening,13),auction=Auction(Seat.NORTH,(opening,'P')),
                                   vulnerability=Vulnerability.NONE,profile=profile)
    assert selected(result)=='2NT' and result.meaning.game_forcing and result.meaning.artificial


@pytest.mark.parametrize('base', (SystemProfile.SAYC,SystemProfile.TWO_OVER_ONE_GF))
def test_no_implicit_system_or_other_partnership_activation(base):
    other=PartnershipProfile('other','1',base,(),(CARD,))
    assert resolve_bergen_agreement(other) is None
    assert assess(other).status is S.ABSTAIN
    defaults=(ResolvedAgreement(BERGEN_FAMILY,BERGEN_RAISES,R.ENABLE,Scope.SYSTEM,tuple(parameters().items())),)
    assert assess(other,base_agreements=defaults).status is S.CONFIGURATION_INCOMPLETE
    assert selected(assess(card(base=base)))=='3C'  # explicitly selected card, either base


def test_card_override_parameters_compiler_provenance_and_determinism():
    profile=card(parameters(swapped=True))
    defaults=(ResolvedAgreement(BERGEN_FAMILY,BERGEN_RAISES,R.ENABLE,Scope.SYSTEM,tuple(parameters().items())),)
    a=resolve_bergen_agreement(profile,base_agreements=defaults)
    b=resolve_bergen_agreement(profile,base_agreements=defaults)
    assert a==b and a.source.parameters==profile.agreements[0].parameters
    assert a.source.source_scope is Scope.PARTNERSHIP and a.profile.sources==(CARD,)
    directive=compile_profile_plan(a.profile,base_agreements=defaults).directive(BERGEN_FAMILY)
    assert directive.effective_parameters==a.source.parameters
    assert directive.effective_source_scope is Scope.PARTNERSHIP
    assert assess(profile)==assess(profile)
    with pytest.raises(FrozenInstanceError): a.branch_policy='conflict'


def test_disable_cannot_resurrect_base_bergen():
    profile=replace(card(),agreements=(AgreementSelection(BERGEN_FAMILY,R.DISABLE),))
    defaults=(ResolvedAgreement(BERGEN_FAMILY,BERGEN_RAISES,R.ENABLE,Scope.SYSTEM,tuple(parameters().items())),)
    assert resolve_bergen_agreement(profile,base_agreements=defaults) is None
    assert selected(assess(profile,base_agreements=defaults)) is None


def test_case_insensitive_duplicate_family_and_parameter_keys_rejected():
    with pytest.raises(ValueError,match='duplicate agreement family'):
        replace(card(),agreements=card().agreements+(AgreementSelection(BERGEN_FAMILY.upper(),R.ENABLE,'bergen'),))
    with pytest.raises(ValueError,match='duplicate parameter key'):
        AgreementSelection(BERGEN_FAMILY,R.ENABLE,BERGEN_RAISES,(('three_clubs.call','3C'),('THREE_CLUBS.CALL','3D')))


def test_generic_reference_is_never_loaded_or_accepted_as_card(monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('reference file must not be loaded')
    monkeypatch.setattr(Path,'read_text',forbidden)
    assert selected(assess(card()))=='3C'
    article='bidding/conventions/responses/bergen-raises'
    profile=replace(card(),sources=(article,))
    result=assess(replace(profile,agreements=(AgreementSelection(BERGEN_FAMILY,R.ENABLE,'bergen'),)))
    assert result.status is S.CONFIGURATION_INCOMPLETE
    p=parameters(); p['card_source']=article
    with pytest.raises(BergenConfigurationError,match='explicit convention card'):
        resolve_bergen_agreement(replace(card(p),sources=(article,)))


@pytest.mark.parametrize('calls', [('P','1H','P'),('1H','X'),('1H','1S'),
    ('1S','P','3C','P'),('1S','P','3C','P','3S','P')])
def test_no_interference_passed_hand_or_continuations(calls):
    result=assess(card(),calls=calls)
    assert result.status is S.ABSTAIN and selected(result) is None


def test_unbound_relevant_profile_meaning_blocks_bergen_fallback():
    profile=replace(card(),agreements=card().agreements+(
        AgreementSelection('response.1s',R.ENABLE,'unknown_response'),))
    result=assess(profile)
    assert result.status is S.ABSTAIN and 'Unsupported' in result.reason


def test_no_production_route_adoption():
    assert len(create_standard_sayc_router().routes)==47
    assert assess(card()).production_adopted is False


def test_explicit_jacoby_disable_is_consumed_without_blocking_bergen():
    profile=replace(card(),agreements=card().agreements+(
        AgreementSelection('response.major.2nt',R.DISABLE),))
    defaults=(ResolvedAgreement('response.major.2nt','fixture_jacoby',R.ENABLE,Scope.SYSTEM,
                               (('min_hcp','13'),('min_support','4'))),)
    assert selected(assess(profile,base_agreements=defaults))=='3C'


def test_incomplete_parameterized_bergen_does_not_bypass_jacoby_guards():
    result=assess_jacoby_2nt_response(hand('1S',13),auction=Auction(Seat.NORTH,('1S','P')),
        vulnerability=Vulnerability.NONE,profile=NISIM_NILY_BERGEN_PROFILE_B24B2)
    assert selected(result) is None and result.blockers
